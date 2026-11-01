"""One evaluation pass; gold is only used here, never by engine.py."""
import argparse,csv,json,pathlib,hashlib,datetime,platform
from engine import a_baseline,a_review,b_asset_sql,b_review,b_dependency_sql
P=pathlib.Path(__file__).resolve().parent; ROOT=P.parent
load=lambda n:json.loads((P/n).read_text())
def run(split,out):
    freeze=json.loads((ROOT/'results/fixture_freeze.json').read_text())
    for n,h in freeze['sha256'].items(): assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
    rules=load('rules.json'); ag=load('a_gold.json'); bd=load('b_data.json');bg=load('b_gold.json')
    records=[];summary={}
    for method,fn in [('intake_sql',a_baseline),('review_rules',a_review)]:
        rows=[]
        for c in load('a_cases.json'):
            if c['split']!=split:continue
            result=fn(c,rules);gold=ag[c['id']];f=result['flags']
            rows.append((gold,f));records.append(dict(experiment='A',id=c['id'],method=method,output=result,gold=gold))
        summary['A_'+method]=dict(total=len(rows),normal=sum(not g for g,f in rows),exceptions=sum(bool(g) for g,f in rows),tp=sum(bool(g) and bool(f) for g,f in rows),fp=sum(not g and bool(f) for g,f in rows),fn=sum(bool(g) and not f for g,f in rows),exact_reasons=sum(g==f for g,f in rows),handoff_missing=sum(len(set(g)-set(f)) for g,f in rows),handoff_required=sum(len(g) for g,f in rows))
    for method,fn in [('asset_sql',b_asset_sql),('dependency_python',b_review),('dependency_sql',b_dependency_sql)]:
        m=dict(events=0,tp=0,fp=0,fn=0,exact_ids=0,exact_subtotal=0,exact_exception_fields=0)
        for event in bd['events']:
            if event['split']!=split:continue
            r=fn(bd,event);g=bg[event['id']];pred=set(r['ids']);truth=set(g['ids'])
            m['events']+=1;m['tp']+=len(pred&truth);m['fp']+=len(pred-truth);m['fn']+=len(truth-pred)
            m['exact_ids']+=pred==truth;m['exact_subtotal']+=r['known_limit']==g['known_limit']
            m['exact_exception_fields']+=all(r[k]==g[k] for k in ['missing_limit','unknown_right','duplicates'])
            records.append(dict(experiment='B',id=event['id'],method=method,output=r,gold=g))
        summary['B_'+method]=m
    py=[r['output'] for r in records if r['method']=='dependency_python'];sq=[r['output'] for r in records if r['method']=='dependency_sql']
    summary['B_sql_python_parity']=dict(matches=sum(a==b for a,b in zip(py,sq)),total=len(py))
    # Repeatability within the same frozen execution, not a second tuned holdout.
    evs=[e for e in bd['events'] if e['split']==split]
    summary['B_reprocessing']=dict(matches=sum(b_review(bd,e)==r for e,r in zip(evs,py)),total=len(evs))
    report=dict(run_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),split=split,seed=20261101,code_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(P.glob('*.py'))},summary=summary,records=records)
    out.mkdir(parents=True,exist_ok=True);target=out/(split+'.json')
    if target.exists():raise SystemExit('Refusing overwrite: choose a separate reproduction output directory')
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with (out/(split+'.csv')).open('w') as f:
        w=csv.writer(f);w.writerow(['experiment','id','method','output_json','gold_json'])
        for r in records:w.writerow([r['experiment'],r['id'],r['method'],json.dumps(r['output'],ensure_ascii=False),json.dumps(r['gold'],ensure_ascii=False)])
    print(json.dumps(dict(split=split,summary=summary),ensure_ascii=False,indent=2))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--split',choices=['dev','eval'],required=True);a.add_argument('--out',type=pathlib.Path,required=True);args=a.parse_args();run(args.split,args.out)
