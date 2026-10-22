#!/usr/bin/env python3
"""Transport independent semantic claim/cause-group judgments; frozen metrics decide."""
import argparse,json,subprocess,sys,time
from pathlib import Path
import experiment as ex
import metrics
R=Path(__file__).resolve().parent

def truths(task,alias,phase,cases=None):
 rows=[]
 for p in sorted((R/'evaluation'/phase/task/alias).glob('*/*/acceptance.json')):
  platform,case=p.parts[-3:-1]
  if cases and case not in cases:continue
  report=ex.read(p)
  for row in report['rows']:rows.append(dict(row,key=case+'/'+platform+'/'+row['id'],platform=platform,case=case))
  for cell in report['matrix_contract']['cells']:
   if cell['disposition']=='not_applicable':rows.append(dict(cell,key=case+'/'+platform+'/'+cell['id'],platform=platform,case=case,status='not_applicable',cause_category=None))
 return rows

def prepare(panel):
 required='grade-final'if panel=='one'else'grade-claims-one';receipt=ex.gate.authorize(R/'gates',required,R)
 for task in ['T1','T2','T3']:
  out=R/'claim-judgments'/panel/task;inputs=R/'evaluation-inputs/claims'/task
  prompt=f'''You are a fresh independent reviewer of ORIGINAL failure claims and confirmed defect cause membership in an anonymous native UI blind study. Write ONLY {out}. Read ONLY {inputs}, original review/plan/own raw files explicitly referenced by that transport, approved independent task design referred by evaluation-inputs/d0/{task}, common D0 and FINAL anonymous evidence and evaluation/d0/{task} plus evaluation/final/{task}, frozen candidate-v8 generic tools, METRIC-POLICY.md and metrics.py. Do NOT read private assignment, other claim judges, previous studies, builder messages or desired outcomes. Do not change any source, original claim/expectation, grade, original input or tool. No SDK/commits/other agents.
Record actual phase start/end in phase.json. For each anonymous source read claims.json, verify ORIGINAL artifacts and SHA, and inspect actual original evidence for every original failed claim. Later repair success or a shared bug is NOT proof that an earlier claim detected it. Native own-D0 facts and screenshots are original evidence; common D0 acceptance establishes the independent consensus-relative product-defect universe. Original_scope is merely an upper bound from pre-existing original case/platform/state/rule IDs, not detection credit. Never extend a vague finding to new states/aspects by using a later grader. A malformed expected/unit/descriptor is an engineering issue; it is NOT automatically a false product alarm. Recognize semantically explicit original supported findings despite formatting only when the original evidence actually supports the claimed issue. Preserve unknown/disagreement.
For each source write judgment.json {{claims:[{{claim_id,status:'TP'|'FP'|'U',supported_rows:[],reason,false_alarm_supported:bool}}],clusters:[{{id,rows:[],reason,certainty:'confirmed'|'uncertain'}}]}}. Judge ALL original_status=failed claims except explicit machine duplicates (retain a note); do not judge nonfailure observations as failure alarms. TP needs direct original support for at least one original_scope key that is common D0 status=failed AND cause_category=product. FP requires explicit original evidence that the claimed product issue is absent or misattributed; a common P alone or a schema rejection alone is insufficient. Otherwise U. supported_rows is nonempty only for TP and must stay within original_scope. A broad original sentence earns only the explicitly supported manifestations, not all matching bugs. Keep exact original expected/unit fields unchanged.
Independently group ALL common D0 confirmed product rows for this source into a disjoint complete partition, using keys <case>/<platform>/<assertion_id> with P1/P2 only. Use source/root-cause evidence to group correlated states/platforms; names do not matter, exact membership must agree across independent panels. Do not inflate repeated manifestations into independent bugs. If grouping cannot be established use certainty=uncertain with explicit reason. An empty product universe needs clusters:[]. Do not inspect another grouping. Cluster certainty and semantic claim support are separate.
Include input integrity, original screenshot inspection coverage, schema/descriptor limitations and preserved uncertainties. Finish SEAL.json {{files:{{relative_path:SHA256}}}} containing ALL output files except SEAL.json/__pycache__. No output edits after seal. AI consensus is not human gold; retain disputed cases and no invented TN/FPR universe.'''
  path=R/'prompts'/('claims-'+panel+'-'+task+'.txt');path.write_text(prompt)
 ex.save(R/'operators'/('claims-'+panel+'-delivery.json'),{'atUnix':time.time(),'authorization':receipt,'promptHashes':{t:ex.sha(R/'prompts'/('claims-'+panel+'-'+t+'.txt'))for t in ['T1','T2','T3']}})
 print('Prepared fresh independent claim panel',panel)

def close(panel):
 ex.gate.authorize(R/'gates','grade-final'if panel=='one'else'grade-claims-one',R);members={}
 for task in ['T1','T2','T3']:
  dest=R/'claim-judgments'/panel/task;seal=ex.read(dest/'SEAL.json');actual={str(p.relative_to(dest)):ex.sha(p)for p in dest.rglob('*')if p.is_file()and p.name!='SEAL.json'and'__pycache__'not in p.parts};assert seal['files']==actual
  for alias in ['source-a','source-b']:
   transport=ex.read(R/'evaluation-inputs/claims'/task/alias/'claims.json')
   for rel,h in transport['original_files'].items():assert ex.sha(R/rel)==h
   data=ex.read(dest/alias/'judgment.json');claims={c['claim_id']:c for c in transport['claims']};want={k for k,c in claims.items()if c['original_status']=='failed'and not c.get('duplicate_of')};received={c['claim_id']:c for c in data['claims']};assert len(received)==len(data['claims'])and want<=set(received)<=set(claims)
   truth=truths(task,alias,'d0');product={r['key']for r in truth if r['status']=='failed'and r['cause_category']=='product'}
   metrics.agreed_clusters(data['clusters'],data['clusters'],product)
   for cid in want:
    c=received[cid];assert c['status']in{'TP','FP','U'}and c.get('reason');assert set(c['supported_rows'])<=set(claims[cid]['original_scope'])
    if c['status']=='TP':assert c['supported_rows']and set(c['supported_rows'])<=product
    else:assert not c['supported_rows']
    if c['status']=='FP':assert c['false_alarm_supported']is True
  members[task]=[str(dest.relative_to(R))]
 path=R/'operators'/('claims-'+panel+'-members.json');ex.save(path,members);subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),'grade-claims-'+panel,'--members',str(path)],check=True,stdout=subprocess.DEVNULL);print('Closed complete claims panel',panel)

def merge():
 ex.gate.authorize(R/'gates','grade-claims-two',R);out=R/'evaluation/claims';assert not out.exists();members={}
 for task in ['T1','T2','T3']:
  for alias in ['source-a','source-b']:
   transports=ex.read(R/'evaluation-inputs/claims'/task/alias/'claims.json');panels=[ex.read(R/'claim-judgments'/p/task/alias/'judgment.json')for p in ['one','two']];maps=[{c['claim_id']:c for c in p['claims']}for p in panels];claims=[]
   for original in transports['claims']:
    row=dict(original)
    for p,m in zip(['judge_one','judge_two'],maps):row[p]=m.get(row['claim_id'],{'status':'U','supported_rows':[],'reason':'Non-alarm or duplicate does not require a semantic alarm judgment.','false_alarm_supported':False})
    claims.append(row)
   payload={'D0':truths(task,alias,'d0'),'FINAL':truths(task,alias,'final',['P1','P2']),'claims':claims,'clusters_one':panels[0]['clusters'],'clusters_two':panels[1]['clusters']}
   ex.save(out/task/alias/'metric-input.json',payload);ex.save(out/task/alias/'metrics.json',metrics.summarize(payload))
  members[task]=[str((out/task).relative_to(R))]
 path=R/'operators/grade-selfreview-members.json';ex.save(path,members);subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),'grade-selfreview','--members',str(path)],check=True,stdout=subprocess.DEVNULL);print('Frozen original semantic metrics closed')

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','close','merge']);p.add_argument('--panel',choices=['one','two']);a=p.parse_args()
 if a.command=='prepare':assert a.panel;prepare(a.panel)
 elif a.command=='close':assert a.panel;close(a.panel)
 else:merge()
if __name__=='__main__':main()
