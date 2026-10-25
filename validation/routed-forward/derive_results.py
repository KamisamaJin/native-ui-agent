#!/usr/bin/env python3
"""Closed blind panel consensus, platform common causes and conservative costs."""
import json
import study as s
from metrics import summarize
R=s.R

def consensus(values):return values[0]if len(set(values))==1 else'unassessed'
def derive():
 s.gate.authorize(R/'gates','revealed',R)
 mapping=s.read(R/'private/quality-map.json')['candidates'];reverse={v['version']:k for k,v in mapping.items()};panels=['panel-one','panel-two'];native={};source={};alarms={}
 for candidate in mapping:
  native[candidate]={};source[candidate]={}
  for phase in ['public','private']:
   rows=[]
   for pl in ['ios','android']:
    for case in sorted((R/'design'/phase/'cases').iterdir()):
     docs=[s.read(R/'quality-evaluation'/p/'runtime'/candidate/phase/pl/case.name/'evaluated.json')for p in panels];ids=[r['id']for r in docs[0]['assertions']]
     assert all([r['id']for r in doc['assertions']]==ids for doc in docs)
     rows.extend({'id':pl+':'+case.name+':'+key,'status':consensus([doc['assertions'][i]['status']for doc in docs])}for i,key in enumerate(ids))
   native[candidate][phase]={'rows':rows,'counts':{k:sum(v['status']==k for v in rows)for k in ['passed','failed','unassessed']}}
   identity=s.read(R/'quality-inputs/source-review'/phase/'identity.json');group='shared-identical-sources'if identity['shared']else candidate
   docs=[s.read(R/'quality-evaluation'/p/'source'/phase/(group+'.json'))for p in panels];ids=[r['id']for r in docs[0]['rows']]
   rows=[{'id':key,'status':consensus([doc['rows'][i]['status']for doc in docs])}for i,key in enumerate(ids)]
   source[candidate][phase]={'rows':rows,'counts':{k:sum(v['status']==k for v in rows)for k in ['passed','failed','unassessed']}}
  by=[{(v['candidate'],v['scope'],v['platform'],v['case'],v['assertion_id']):v for v in s.read(R/'quality-panels'/p/'alarm-judgments.json')}for p in panels]
  assert set(by[0])==set(by[1]);alarms[candidate]=[]
  for key in sorted(by[0]):
   if key[0]!=candidate:continue
   causes=[v[key]['cause']for v in by];cause=causes[0]if len(set(causes))==1 else'uncertain'
   alarms[candidate].append({'scope':key[1],'platform':key[2],'case':key[3],'id':key[4],'cause':cause})
 adjudication=s.read(R/'adjudication/causes.json');assert set(adjudication['candidates'])==set(mapping)
 causes=adjudication['causes'];assert len({v['id']for v in causes})==len(causes)
 for cause in causes:
  assert type(cause['initial_present'])is bool and set(cause['present_by_candidate'])==set(mapping)
  assert all(v is None or type(v)is bool for v in cause['present_by_candidate'].values())
  assert cause['evidence']and cause['reason']and cause['panel_consensus']is True
 initial={v['id']for v in causes if v['initial_present']};cost=s.read(R/'costs.json');assignment=s.read(R/'private/assignment.json')['units'];inputs={'initial_confirmed_defects':sorted(initial),'arms':[]};rows=[];unknowns={}
 for unit,cfg in assignment.items():
  candidate=reverse[unit];counts={k:sum(native[candidate][phase]['counts'][k]for phase in ['public','private'])for k in ['passed','failed','unassessed']};scounts={k:sum(source[candidate][phase]['counts'][k]for phase in ['public','private'])for k in ['passed','failed','unassessed']}
  residual={v['id']for v in causes if v['initial_present']and v['present_by_candidate'][candidate]is True};unknown={v['id']for v in causes if v['initial_present']and v['present_by_candidate'][candidate]is None};regressions={v['id']for v in causes if not v['initial_present']and v['present_by_candidate'][candidate]is True};unknowns[unit]=unknown
  selfcheck=s.read(R/'self-endpoints'/(unit+'.json'));selfsource=s.read(R/'self-review'/unit/'source-only/bound.json');c=next(v for v in cost['arms']if v['unit']==unit)
  sourcecomplete=scounts['failed']==scounts['unassessed']==0 and selfsource['status']=='accepted';nativecomplete=selfcheck['status']=='accepted_within_public_self_scope'and counts['failed']==counts['unassessed']==0
  unresolved=adjudication.get('unresolved_by_candidate',{}).get(candidate,[])
  inputs['arms'].append({'unit':unit,'residual_initial_defects':sorted(residual|unknown),'new_regressions':sorted(regressions),'alarm_causes':[v['cause']for v in alarms[reverse['initial']]if v['scope']=='public'],
    'native_complete':nativecomplete,'source_audit_complete':sourcecomplete,'independent_quality_complete':sourcecomplete and counts['failed']==counts['unassessed']==0 and not unknown and not unresolved,
    'failed':counts['failed'],'unassessed':counts['unassessed'],'applicable':sum(counts.values()),'author_seconds':c['source_authoring_seconds'],'d0_seconds':c['shared_D0_acquisition_seconds'],'repair_endpoint_seconds':c['handoff_to_full_self_endpoint_seconds']})
  rows.append({'unit':unit,'condition':cfg['mode'],'candidate':candidate,'public':native[candidate]['public']['counts'],'private':native[candidate]['private']['counts'],'all':counts,'source_all_scope_counts':scounts,'confirmed_residuals':sorted(residual),'unknown_initial_mappings':sorted(unknown),'regressions':sorted(regressions),'strict_alarm_causes':alarms[candidate],'final_alarm_attribution':{'product':sum(v['cause']=='product'for v in alarms[candidate]),'false_alarm':sum(v['cause']=='false_alarm'for v in alarms[candidate]),'uncertain':sum(v['cause']=='uncertain'for v in alarms[candidate])},'unresolved_independent_findings':unresolved})
 metrics=summarize(inputs)
 for row in metrics['arms']:
  unknown=unknowns[row['unit']]
  if unknown:
   n=len(initial);upper=row['final_initial_defect_miss_rate'];lower=upper-len(unknown)/n
   row.update(final_initial_defect_miss_rate=None,repair_rate=None,final_miss_bounds=[lower,upper],repair_rate_bounds=[1-upper,1-lower],rate_limitation='Unknown final cause mappings prevent a point estimate; original raw records retained.')
 return {'summary':{'arms':rows,'initial_candidate':reverse['initial'],'initial_counts':{p:native[reverse['initial']][p]['counts']for p in ['public','private']},'confirmed_initial_causes':sorted(initial),'scope':'One naturally authored initial PR; two independent anonymous AI panels, no human gold. Testability/accessibility causes and business causes remain tagged in original adjudication; unknown is not repaired or a false alarm.'},'metric_input':inputs,'metrics':metrics,'causes':causes}
if __name__=='__main__':print(json.dumps(derive(),indent=2))
