#!/usr/bin/env python3
"""Shared anonymous source-only panel delivery and conservative dual consensus."""
import argparse,sys
import study as s
sys.path.insert(0,str(s.REPO/'tools'))
import implementation_audit as audit
import design_contract as d
R=s.R
import shared_amendment

def prepare(phase):
 shared_amendment.verify()
 s.gate.authorize(R/'gates','hidden'if phase=='d0'else'grade-d0-two',R);assignment=s.read(R/'private/assignment.json');out=R/'source-evaluation-inputs'/phase;assert not out.exists()
 for task in ['T1','T2']:
  scope=R/'design'/task/'public';approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');policy=s.read(scope/'implementation-audit.json')
  aliases={'initial':None}if phase=='d0'else assignment['gradeAliases'][task]
  for alias,unit in aliases.items():
   capsule=R/'submissions'/(task if phase=='d0'else unit)/('d0'if phase=='d0'else'final')
   cat=audit.catalog(lock,approval['design_lock_sha256'],policy,approval['implementation_audit_sha256'],capsule/'source',scope)
   base=out/task/alias;s.save(base/'catalog.json',cat);s.save(base/'template.json',{'review':{'version':1,'catalog_sha256':d.digest(cat),'decisions':[]},'attributions':[]})
   s.save(base/'inputs.json',{'source':alias,'task':task,'phase':phase,'capsule':str(capsule.relative_to(R)),'design_root':str(scope.relative_to(R)),'catalog_sha256':d.digest(cat),'source_seal_sha256':s.sha(capsule/'seal.json'),'original_files':{str(p.relative_to(R)):s.sha(p)for folder in [capsule,scope]for p in folder.rglob('*')if p.is_file()and'__pycache__'not in p.parts}})
 s.seal_dir(out)

def judge(phase,task,alias,panel):
 base=R/'source-evaluation-inputs'/phase/task/alias;cat=s.read(base/'catalog.json');path=R/'judgments'/phase/panel/task/alias/'source-judge.json';value=s.read(path)
 if set(value)!={'review','attributions'}:raise ValueError('Source-only panel needs original review and separate cause assessments')
 report=audit.bind(cat,value['review']);by={r['id']:r for r in report['rows']};causes={}
 for item in value['attributions']:
  if set(item)!={'id','cause','reason'}or item['id']not in by or item['id']in causes or item['cause']not in{'product','infrastructure','observation','uncertain'}or not item['reason'].strip():raise ValueError('Unique supported source-cause assessment required')
  causes[item['id']]=item
 return report,causes

def validate(phase,panel):
 shared_amendment.verify()
 s.verify_dir(R/'source-evaluation-inputs'/phase)
 for task in ['T1','T2']:
  for base in (R/'source-evaluation-inputs'/phase/task).iterdir():judge(phase,task,base.name,panel)

def merge(phase):
 for task in ['T1','T2']:
  for base in (R/'source-evaluation-inputs'/phase/task).iterdir():
   alias=base.name;reports=[judge(phase,task,alias,p)for p in ['one','two']];second={r['id']:r for r in reports[1][0]['rows']};rows=[]
   for a in reports[0][0]['rows']:
    b=second[a['id']];status=a['status']if a['status']==b['status']and a['status']in{'passed','failed'}else'unassessed';causes=[v[1].get(a['id'])for v in reports]
    cause=(causes[0]['cause']if all(causes)and causes[0]['cause']==causes[1]['cause']else'uncertain')if status=='failed'else None
    rows.append({'id':a['id'],'key':'source/'+a['id'],'expected':a['expected'],'unit':a['unit'],'priority':a['priority'],'status':status,'cause_category':cause,'judges':[a,b],'cause_assessments':causes,'method':'independent_source_review_consensus','reason':'Agreed original source judgment'if status!='unassessed'else'Disagreement/unknown retained'})
   s.save(R/'evaluation/source'/phase/task/alias/'acceptance.json',{'rows':rows,'counts':{v:sum(r['status']==v for r in rows)for v in ['passed','failed','unassessed']},'accepted':all(r['status']=='passed'for r in rows if r['priority']=='must'),'scope':'Independent dual-AI source-only consensus; not native evidence, AST proof or human gold.'})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','validate','merge']);p.add_argument('phase',choices=['d0','final']);p.add_argument('--panel',choices=['one','two']);a=p.parse_args()
 prepare(a.phase)if a.command=='prepare'else validate(a.phase,a.panel)if a.command=='validate'else merge(a.phase)
