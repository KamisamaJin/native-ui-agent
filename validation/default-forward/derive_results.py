#!/usr/bin/env python3
"""Conservative closed-panel consensus. Nonempty defect cases require cause matching."""
import json
import study as s
from metrics import summarize
R=s.R

def verdict(values):
 return values[0]if len(set(values))==1 else'unassessed'

def derive():
 s.gate.authorize(R/'gates','revealed',R)
 mapping=s.read(R/'private/quality-map.json')['candidates'];reverse={v['version']:k for k,v in mapping.items()};panels=['panel-one','panel-two'];source={};native={};causes={};product=[];extras=[]
 for panel in panels:extras.extend(s.read(R/'quality-panels'/panel/'extra-findings.json'))
 for phase in ['public','private']:
  for group in sorted((R/'quality-inputs/source-review'/phase).iterdir()):
   if not group.is_dir():continue
   reports=[s.read(R/'quality-evaluation'/panel/'source'/phase/(group.name+'.json'))for panel in panels]
   ids=[v['id']for v in reports[0]['rows']];assert all([v['id']for v in doc['rows']]==ids for doc in reports)
   rows=[{'id':key,'status':verdict([doc['rows'][i]['status']for doc in reports])}for i,key in enumerate(ids)]
   source[phase+':'+group.name]={'rows':rows,'counts':{k:sum(v['status']==k for v in rows)for k in ['passed','failed','unassessed']}}
   product.extend('source:'+phase+':'+r['id']for r in rows if r['status']=='failed')
 for candidate in mapping:
  native[candidate]={}
  for phase in ['public','private']:
   rows=[]
   for pl in ['ios','android']:
    for case in sorted((R/'design'/phase/'cases').iterdir()):
     docs=[s.read(R/'quality-evaluation'/panel/'runtime'/candidate/phase/pl/case.name/'evaluated.json')for panel in panels]
     ids=[r['id']for r in docs[0]['assertions']];assert all([r['id']for r in v['assertions']]==ids for v in docs)
     rows.extend({'id':pl+':'+case.name+':'+key,'status':verdict([doc['assertions'][i]['status']for doc in docs])}for i,key in enumerate(ids))
   native[candidate][phase]={'counts':{k:sum(r['status']==k for r in rows)for k in ['passed','failed','unassessed']},'rows':rows}
  docs=[s.read(R/'quality-panels'/panel/'alarm-judgments.json')for panel in panels];by=[{(r['candidate'],r['scope'],r['platform'],r['case'],r['assertion_id']):r for r in doc}for doc in docs]
  alarms=[]
  for key in sorted(set(by[0])|set(by[1])):
   if key[0]!=candidate:continue
   assert all(key in doc for doc in by);values=[doc[key]['cause']for doc in by];cause=values[0]if len(set(values))==1 else'uncertain'
   alarms.append({'scope':key[1],'platform':key[2],'case':key[3],'id':key[4],'cause':cause})
   if cause=='product':product.append(':'.join(key))
  causes[candidate]=alarms
 # Prevent nontrivial defects from being silently turned into zero or counted
 # repeatedly without the independently required common-cause comparison.
 if product or extras:raise ValueError('Independent cross-version common-cause adjudication required before metric export: '+json.dumps({'product_manifestations':product,'extra_findings':extras}))
 costs=s.read(R/'costs.json');assignment=s.read(R/'private/assignment.json');initial=reverse['initial'];inputs={'initial_confirmed_defects':[],'arms':[]};rows=[]
 for unit,cfg in assignment['units'].items():
  candidate=reverse[unit];counts={k:sum(native[candidate][phase]['counts'][k]for phase in ['public','private'])for k in ['passed','failed','unassessed']};cost=next(v for v in costs['arms']if v['unit']==unit)
  self_check=s.read(R/'self-endpoints'/(unit+'.json'));self_source=s.read(R/'self-review'/unit/'source-only/bound.json')
  source_complete=all(v['counts']['failed']==0 and v['counts']['unassessed']==0 for v in source.values())and self_source['status']=='accepted'
  native_complete=self_check['status']=='accepted_within_public_self_scope'and counts['failed']==counts['unassessed']==0
  inputs['arms'].append({'unit':unit,'residual_initial_defects':[],'new_regressions':[],'alarm_causes':[v['cause']for v in causes[initial]if v['scope']=='public'],
                        'native_complete':native_complete,'source_audit_complete':source_complete,'independent_quality_complete':source_complete and counts['failed']==counts['unassessed']==0,
                        'failed':counts['failed'],'unassessed':counts['unassessed'],'applicable':sum(counts.values()),'author_seconds':cost['source_authoring_seconds'],'d0_seconds':cost['shared_D0_acquisition_seconds'],'repair_endpoint_seconds':cost['handoff_to_full_self_endpoint_seconds']})
  claims=s.read(R/'submissions'/unit/'agent-output/claims.json')['findings'];assert not any(v.get('classification')=='product'for v in claims),'Independent product-claim attribution required'
  rows.append({'unit':unit,'condition':cfg['mode'],'candidate':candidate,'public':native[candidate]['public']['counts'],'private':native[candidate]['private']['counts'],'all':counts,'source_all_scope_counts':{k:sum(v['counts'][k]for v in source.values())for k in ['passed','failed','unassessed']},'participant_product_claims':0,'participant_original_records':len(claims),'strict_alarm_causes':causes[candidate]})
 return {'summary':{'arms':rows,'initial_candidate':initial,'initial_counts':{phase:native[initial][phase]['counts']for phase in ['public','private']},'confirmed_product_defects':0,'source_bytes_identical':all(s.read(R/'submissions'/unit/'final/seal.json')['files']==s.read(R/'submissions/initial/seal.json')['files']for unit in assignment['units']),'scope':'One natural shared initial PR; two independent AI panels, no human gold. Native strict F remains F with unresolved cause. Declared source-only and unexecuted runtime limits remain outside native proof.'},'metric_input':inputs,'metrics':summarize(inputs)}
if __name__=='__main__':print(json.dumps(derive(),indent=2))
