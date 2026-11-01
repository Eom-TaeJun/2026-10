"""Synthetic administrative review and exposure selection; no payment decisions."""
import sqlite3
from datetime import date
from collections import Counter

HANDOFF = {
 'missing_field':'필수 입력값을 확인하세요', 'invalid_date':'사건일 형식을 확인하세요',
 'unreadable':'원문을 다시 확보하세요', 'target_mismatch':'청구와 증빙의 대상을 확인하세요',
 'rule_mismatch':'사건일 기준 합성 규칙을 확인하세요', 'no_rule':'해당 기간의 규칙을 확보하세요',
 'amount_mismatch':'청구액과 증빙액 차이를 확인하세요', 'missing_documents':'필수 증빙을 보완하세요'}
FIELDS={'missing_field':['event_date','selected_rule','target','evidence_target','amount_claimed','amount_evidence'],
'invalid_date':['event_date'],'unreadable':['readable'],'target_mismatch':['target','evidence_target'],
'rule_mismatch':['event_date','selected_rule'],'no_rule':['event_date'],
'amount_mismatch':['amount_claimed','amount_evidence'],'missing_documents':['documents']}

def a_baseline(row, rules):
    # All input available; this SQL implements only a basic intake completeness check.
    with sqlite3.connect(':memory:') as db:
        ok=db.execute('SELECT ? IS NOT NULL AND ? IS NOT NULL AND ? IS NOT NULL AND ?',
          (row.get('event_date'),row.get('amount_claimed'),row.get('amount_evidence'),'application' in row.get('documents',[]))).fetchone()[0]
    return a_output(row,[] if ok else ['missing_field'],None)

def a_output(row,flags,rule):
    flags=sorted(set(flags))
    return dict(id=row['id'],status='needs_review' if flags else 'administratively_consistent',flags=flags,
      applied_synthetic_rule=rule,review_required=True,payment_authorized=False,
      handoff=[dict(reason=f,request=HANDOFF[f],evidence={k:row.get(k) for k in FIELDS[f]}) for f in flags])

def a_review(row,rules):
    flags=[]; rule=None
    if any(row.get(k) is None for k in FIELDS['missing_field']): flags.append('missing_field')
    if row.get('readable') is not True: flags.append('unreadable')
    if row.get('target') is not None and row.get('evidence_target') is not None and row['target']!=row['evidence_target']: flags.append('target_mismatch')
    if row.get('event_date') is not None:
        try: day=date.fromisoformat(row['event_date'])
        except (ValueError,TypeError): flags.append('invalid_date')
        else:
            matches=[r for r in rules if date.fromisoformat(r['start'])<=day<date.fromisoformat(r['end'])]
            if len(matches)!=1: flags.append('no_rule')
            else:
                rule=matches[0]
                if row.get('selected_rule')!=rule['id']: flags.append('rule_mismatch')
                if not set(rule['documents'])<=set(row.get('documents',[])):flags.append('missing_documents')
    if row.get('amount_claimed') is not None and row.get('amount_evidence') is not None and row['amount_claimed']!=row['amount_evidence']:flags.append('amount_mismatch')
    return a_output(row,flags,rule['id'] if rule else None)

def database(data):
    db=sqlite3.connect(':memory:'); db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE contracts (id,asset,right,start,end,lim)')
    db.executemany('INSERT INTO contracts VALUES (:id,:asset,:right,:start,:end,:limit)',data['contracts'])
    db.execute('CREATE TABLE dependencies (asset,dependency)')
    db.executemany('INSERT INTO dependencies VALUES (:asset,:dependency)',data['dependencies'])
    return db

def summarize(rows, unknown=()):
    counts=Counter(r['id'] for r in rows)
    unique={r['id']:r for r in rows}
    missing=sorted(k for k,r in unique.items() if r['limit'] is None)
    return dict(ids=sorted(unique),known_limit=sum(r['limit'] for r in unique.values() if r['limit'] is not None),
       missing_limit=missing,unknown_right=sorted(set(unknown)),duplicates=sorted(k for k,n in counts.items() if n>1),
       complete=not (missing or unknown),unit='synthetic_limit_units',payment_authorized=False)

def b_asset_sql(data,event):
    with database(data) as db:
        rows=[dict(r) for r in db.execute('SELECT id,asset,right,start,end,lim AS "limit" FROM contracts WHERE asset=?',(event['asset_hint'],))]
    # Naive row aggregation intentionally exposes its different business semantics.
    result=summarize(rows)
    result['known_limit']=sum(r['limit'] for r in rows if r['limit'] is not None)
    result['raw_rows']=len(rows)
    return result

def b_review(data,event):
    assets={event['target']} if event['kind']=='asset' else {d['asset'] for d in data['dependencies'] if d['dependency']==event['target']}
    active=[r for r in data['contracts'] if r['asset'] in assets and r['start']<=event['at']<r['end']]
    unknown=[r['id'] for r in active if r['right'] not in ('service','capacity','revenue')]
    return summarize([r for r in active if r['right'] in event['rights']],unknown)

def b_dependency_sql(data,event):
    with database(data) as db:
        db.execute('CREATE TABLE wanted (right)')
        db.executemany('INSERT INTO wanted VALUES (?)',[(v,) for v in event['rights']])
        # EXISTS avoids multiplying contracts when dependency rows repeat.
        clause="""start <= :at AND :at < end AND
         ((:kind='asset' AND asset=:target) OR (:kind='dependency' AND EXISTS
          (SELECT 1 FROM dependencies d WHERE d.asset=contracts.asset AND d.dependency=:target)))"""
        rows=[dict(r) for r in db.execute('SELECT id,asset,right,start,end,lim AS "limit" FROM contracts WHERE '+clause+' AND right IN (SELECT right FROM wanted)',event)]
        unknown=[r[0] for r in db.execute('SELECT id FROM contracts WHERE '+clause+" AND right NOT IN ('service','capacity','revenue')",event)]
    return summarize(rows,unknown)
