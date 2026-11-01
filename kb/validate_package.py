"""Read-only artifact and public-suitability checks; does not rerun holdout."""
import hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parent
problems=[]
for manifest,base in [('fixture_freeze.json',ROOT),('code_freeze.json',ROOT/'experiments')]:
    m=json.loads((ROOT/'results'/manifest).read_text())
    for n,h in m['sha256'].items():
        if hashlib.sha256((base/n).read_bytes()).hexdigest()!=h:problems.append('freeze mismatch '+n)
r=json.loads((ROOT/'results/eval.json').read_text())
for n,h in r['code_sha256'].items():
    if hashlib.sha256((ROOT/'experiments'/n).read_bytes()).hexdigest()!=h:problems.append('run code mismatch '+n)
assert len(r['records'])==44
# Check every Markdown local destination and common credential/private-transfer markers.
patterns=[r'-----BEGIN [A-Z ]*PRIVATE KEY-----',r'gh[pousr]_[A-Za-z0-9]{30,}',r'AKIA[A-Z0-9]{16}',r'(?i)(?:x-amz-signature|x-goog-signature|access_token)=',r'libfile_[a-zA-Z0-9]+']
checked=0
for f in sorted(ROOT.rglob('*')):
    if not f.is_file() or '__pycache__' in f.parts or f.name=='public_check.json':continue
    checked+=1;text=f.read_text()
    if f.name!='validate_package.py':
        for pattern in patterns:
            if re.search(pattern,text):problems.append('sensitive marker '+str(f.relative_to(ROOT)))
    if f.suffix=='.md':
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if '://' in link or link.startswith('#'):continue
            path=link.split('#')[0]
            if path and not (f.parent/path).exists():problems.append('missing link '+str(f.relative_to(ROOT))+' -> '+path)
print(json.dumps(dict(files_checked=checked,freeze_checks='pass' if not problems else 'see_problems',problems=problems,scope='kb/ only; heuristic marker/link checks plus AI content inspection; not a complete secret/PII detector',evaluation_rerun=False),ensure_ascii=False,indent=2))
raise SystemExit(bool(problems))
