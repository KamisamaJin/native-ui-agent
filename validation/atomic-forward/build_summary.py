#!/usr/bin/env python3
"""Project frozen metrics by task/arm/platform without changing judgment or expectations."""
import argparse,copy,json
from pathlib import Path
import experiment as ex
import metrics as m
from claim_panels import truths
R=Path(__file__).resolve().parent

def namespace(data,prefix):
 result=copy.deepcopy(data)
 for phase in ['D0','FINAL']:
  for row in result[phase]:row['key']=prefix+'/'+row['key']
 for panel in ['clusters_one','clusters_two']:
  for group in result[panel]:group['rows']=[prefix+'/'+k for k in group['rows']]
 for claim in result['claims']:
  claim['claim_id']=prefix+'/'+claim['claim_id'];claim['original_scope']=[prefix+'/'+k for k in claim['original_scope']]
  if claim.get('duplicate_of'):claim['duplicate_of']=prefix+'/'+claim['duplicate_of']
  for panel in ['judge_one','judge_two']:claim[panel]['supported_rows']=[prefix+'/'+k for k in claim[panel].get('supported_rows',[])]
 return result

def project(data,platform):
 result=copy.deepcopy(data)
 for phase in ['D0','FINAL']:result[phase]=[r for r in result[phase]if r['platform']==platform]
 wanted={r['key']for r in result['D0']};claims=[]
 for c in result['claims']:
  c['original_scope']=[k for k in c['original_scope']if k in wanted]
  for panel in ['judge_one','judge_two']:c[panel]['supported_rows']=[k for k in c[panel].get('supported_rows',[])if k in wanted]
  if c.get('platform')==platform:claims.append(c)
 result['claims']=claims
 for panel in ['clusters_one','clusters_two']:
  groups=[]
  for group in result[panel]:
   group['rows']=[k for k in group['rows']if k in wanted]
   if group['rows']:groups.append(group)
  result[panel]=groups
 return result

def compute():
 ex.gate.authorize(R/'gates','reveal',R);assignment=ex.read(R/'private/assignment.json');groups={};tasks={};allparts={};diagnostic=[]
 for task,aliases in assignment['gradeAliases'].items():
  tasks[task]={}
  for alias,unit in aliases.items():
   config=assignment['units'][unit];payload=ex.read(R/'evaluation/claims'/task/alias/'metric-input.json');tool=config['tool'];part=namespace(payload,task);allparts.setdefault(tool,[]).append(part);tasks[task][tool]={'alias':alias,'unit':unit,'public':m.summarize(payload),'hiddenFinal':m.coverage(truths(task,alias,'final',['H1'])),'allFinal':m.coverage(truths(task,alias,'final'))}
 for tool,parts in allparts.items():
  data={key:[row for part in parts for row in part[key]]for key in ['D0','FINAL','claims','clusters_one','clusters_two']};public=m.summarize(data)
  hidden=[r for task,v in tasks.items()for r in truths(task,v[tool]['alias'],'final',['H1'])];full=[r for task,v in tasks.items()for r in truths(task,v[tool]['alias'],'final')]
  values=[v[tool]['public']['detection']['combined']['rowRecall']for v in tasks.values()];known=[v for v in values if v is not None]
  groups[tool]={'public':public,'hiddenFinal':m.coverage(hidden),'allFinal':m.coverage(full),'macroTaskCombinedRowRecall':sum(known)/len(known)if known else None,'macroRecallDefinedTasks':len(known),'platforms':{pl:m.summarize(project(data,pl))for pl in ['ios','android']}}
  by={r['key']:r for r in data['D0']};compliance={'exactTypedDescriptor':0,'otherOrUnresolvedDescriptor':0,'uniqueOriginalAlarms':0}
  for claim in data['claims']:
   if claim['original_status']!='failed'or claim.get('duplicate_of'):continue
   compliance['uniqueOriginalAlarms']+=1;spec=claim.get('original_plan')or claim['original'];scope=claim['original_scope'];exact=len(scope)==1 and spec.get('expected')==by[scope[0]].get('expected')and spec.get('unit')==by[scope[0]].get('unit')
   compliance['exactTypedDescriptor'if exact else'otherOrUnresolvedDescriptor']+=1
  groups[tool]['descriptorCompliance']=compliance
  groups[tool]['causeCounts']={stage:{cause:sum(r['status']=='failed'and r.get('cause_category')==cause for r in rows)for cause in ['product','infrastructure','system','observation','uncertain']}for stage,rows in [('D0',data['D0']),('FINAL',full)]}
 for path in sorted((R/'evaluation/pair').glob('*/*/*/*/comparison.json')):
  value=ex.read(path);diagnostic.append({'path':str(path.relative_to(R)),**value})
 return {'groups':groups,'tasks':tasks,'offlineSameEvidence':{'configurations':len(diagnostic),'newSDKCommands':0,'comparisons':diagnostic,'counts':{tool:{status:sum((r['counts'][tool]or{}).get(status,0)for r in diagnostic)for status in ['passed','failed','unassessed']}for tool in ['v7','v8']}},'scope':'Three task pairs with repeated state/platform manifestations; consensus-relative original semantic detection. No seeded product defect. Shared evaluator and design clarity are not exclusive treatment gains. Descriptor compliance is separate, and AI consensus is not human gold.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=compute();path=R/'summary.json'
 if a.check:assert ex.read(path)==value
 else:assert not path.exists();ex.save(path,value)
 print('PASS grouped frozen metrics')
if __name__=='__main__':main()
