#!/usr/bin/env python3
"""Original evidence claim judgments; no expected values or verdict overrides."""
import argparse
import study as s
import metrics
R=s.R

def truth(phase,task,alias):
 rows=[]
 for path in sorted((R/'evaluation'/phase/task/alias).glob('*/*/acceptance.json')):
  pl,case=path.parts[-3:-1]
  for row in s.read(path)['rows']:rows.append(dict(row,key=pl+'/'+case+'/'+row['id'],case=case,platform=pl))
 return rows

def prepare():
 s.gate.authorize(R/'gates','grade-final-two',R);assignment=s.read(R/'private/assignment.json')
 for task in ['T1','T2']:
  initial=truth('d0',task,'initial');out=R/'claim-inputs'/task;units={}
  for alias,unit in assignment['gradeAliases'][task].items():
   claims=[]
   for path in sorted((R/'corpora'/task/'d0').glob('*/*/automatic.json')):
    pl,case=path.parts[-3:-1]
    for row in s.read(path)['assertions']:
     if row['status']=='failed':claims.append({'claim_id':'machine/'+pl+'/'+case+'/'+row['id'],'origin':'machine','original_status':'failed','original_scope':[pl+'/'+case+'/'+row['id']],'original':row,'raw':str(path.relative_to(R))})
   original=R/'submissions'/unit/'agent-output/claims.json'
   for index,item in enumerate(s.read(original)['findings']):
    proposed=[item['platform']+'/'+item['case']+'/'+rid for rid in item.get('assertion_ids',[])]
    valid=[v for v in proposed if v in{r['key']for r in initial}]
    claims.append({'claim_id':'manual/'+str(index),'origin':'manual','original_status':item.get('status','failed'),'original_scope':valid,'unmapped_scope':sorted(set(proposed)-set(valid)),'original':item,'raw':str(original.relative_to(R))})
   units[alias]={'unit':unit,'claims':claims,'final':truth('final',task,alias),'source':str((R/'submissions'/unit/'final/source').relative_to(R)),'original_report':str((R/'submissions'/unit/'agent-output/repair.json').relative_to(R))}
  s.save(out/'inputs.json',{'task':task,'initial':initial,'units':units,'scope':'D0 product failures shared by identical initial PR; original finding scope cannot expand to other states after repair. Grade classifications before reveal.'})
  s.seal_dir(out)

def close(panel):
 s.gate.authorize(R/'gates','grade-final-two'if panel=='one'else'claims-one',R);members={}
 for task in ['T1','T2']:
  root=R/'claim-judgments'/panel/task;s.verify_dir(root);value=s.read(root/'judgment.json');data=s.read(R/'claim-inputs'/task/'inputs.json')
  product=[r['key']for r in data['initial']if r['status']=='failed'and r.get('cause_category')=='product']
  metrics.agreed_clusters(value['clusters'],value['clusters'],product)
  assert set(value['claims'])==set(data['units'])
  for alias,unit in data['units'].items():
   judgments=value['claims'][alias];assert set(judgments)=={c['claim_id']for c in unit['claims']}
   rows=[dict(c,judge_one=judgments[c['claim_id']],judge_two=judgments[c['claim_id']])for c in unit['claims']]
   metrics.detection(data['initial'],rows,[],rows)
  members[task]=[root]
 s.cohort('claims-'+panel,members)
 if panel=='two':
  for task in ['T1','T2']:
   data=s.read(R/'claim-inputs'/task/'inputs.json');panels=[s.read(R/'claim-judgments'/p/task/'judgment.json')for p in ['one','two']]
   for alias,unit in data['units'].items():
    claims=[dict(c,judge_one=panels[0]['claims'][alias][c['claim_id']],judge_two=panels[1]['claims'][alias][c['claim_id']])for c in unit['claims']]
    value={'D0':data['initial'],'FINAL':unit['final'],'claims':claims,'clusters_one':panels[0]['clusters'],'clusters_two':panels[1]['clusters']}
    out=R/'evaluation/claims'/task/alias;s.save(out/'metric-input.json',value);s.save(out/'metrics.json',metrics.summarize(value))

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','close']);p.add_argument('--panel',choices=['one','two']);a=p.parse_args()
 prepare()if a.command=='prepare'else close(a.panel)
if __name__=='__main__':main()
