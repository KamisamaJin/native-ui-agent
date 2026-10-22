from pathlib import Path
import json,shutil,datetime
R=Path(__file__).resolve().parent;A=R/'authoring-attempts'/'attempt-02-route';A.mkdir(parents=True)
for t in ['T1','T2','T3']:
 for scope in ['public','private']:
  base=R/t/scope
  for p in [base/'contract.json',*base.glob('cases/*/actions.*.json')]:
   q=A/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
   obj=json.loads(p.read_text())
   def fix(v):
    if isinstance(v,dict):
     if v.get('type')=='sweep' and 'max_scrolls' in v:v['max_steps']=v.pop('max_scrolls')
     for z in v.values():fix(z)
    if isinstance(v,list):
     for z in v:fix(z)
   fix(obj);p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
shutil.copy2(R/'generate_design.py',A/'generate_design.py')
p=R/'generate_design.py';s=p.read_text().replace("state_id='baseline',max_scrolls=24","state_id='baseline',max_steps=24").replace("state_id='expanded',max_scrolls=24","state_id='expanded',max_steps=24").replace("state_id='submitted',max_scrolls=24","state_id='submitted',max_steps=24");p.write_text(s)
(R/'revision-03-record.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Frozen observer API inspection established that explicit sweep bounds use max_steps. Correct original independent routes before locking; preserve prior route originals. No runtime invocation.'},indent=2)+'\n')
