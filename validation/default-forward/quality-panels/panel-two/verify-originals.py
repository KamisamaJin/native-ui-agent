from pathlib import Path
import hashlib,json,collections
B=Path('validation/default-forward');Q=B/'quality-inputs';O=B/'quality-panels/panel-two'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(p):return hashlib.sha256(json.dumps(read(p),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
source_count=visual_count=0
for scope in ['public','private']:
 p=Q/'source-review'/scope/'shared-identical-sources';cat=read(p/'catalog.json');sub=read(O/'source'/scope/'shared-identical-sources/submission.json');assert sub['catalog_sha256']==canonical(p/'catalog.json')
 assert {d['review_id'] for d in sub['decisions']}=={r['review_id'] for r in cat['rows']}
 rows={r['review_id']:r for r in cat['rows']}
 for d in sub['decisions']:
  assert isinstance(d['actual'],bool) and d['reason'] and {e['file'] for e in d['evidence']}==set(rows[d['review_id']]['files'])
  for e in d['evidence']:assert e['sha256']==cat['files'][e['file']]['sha256'] and 1<=e['start_line']<=e['end_line']<=cat['files'][e['file']]['line_count']
 source_count+=len(sub['decisions'])
summaries=[];all_alarms=set()
for p in sorted(Q.glob('candidate-*/native/*/*/*')):
 candidate=p.parts[-5];scope=p.parts[-3];platform=p.parts[-2];case=p.name
 sub=read(O/'visual'/candidate/scope/platform/case/'submission.json');cat=read(p/'review-catalog.json');si=read(p/'state-image-index.json');obs=read(p/'native/observation.json');auto=read(p/'automatic.json');plan=read(p/'parent-plan.json');env=read(p/'environment-check.json');cv=read(p/'execution-coverage.json')
 assert sub['catalog_sha256']==canonical(p/'review-catalog.json') and sub['observation_sha256']==sha(p/'native/observation.json')
 rows={r['review_id']:r for r in cat['rows'] if r['method']=='visual'};assert {d['review_id'] for d in sub['decisions']}==set(rows)
 for d in sub['decisions']:
  r=rows[d['review_id']];assert isinstance(d['actual'],bool) and d['snapshot_indices']==si[r['state']]['indices']
 visual_count+=len(sub['decisions']);assert env['status']=='P' and cv['satisfied']
 states=[]
 for state,v in si.items():
  cap=next(c for c in obs['state_captures'] if c['state_id']==state)
  assert v['complete'] and cap['complete'] and cap['top_reached'] and cap['bottom_reached'] and cap['stable_binding'] and cap['stable_height'] and cap['max_gap']==0
  assert v['indices']==cap['snapshot_indices']
  specs=next(s for s in plan['states'] if s['id']==state)
  for i in v['indices']:
   snap=obs['snapshots'][i];assert snap['state_id']==state and snap['capture_consistent'] and snap['binding']==snap['binding_after_capture']
   assert snap['binding']['fixture_index']==specs['input_index'] and snap['binding']['event_revision']==min(specs['after_action'],4)
  states.append({'state':state,'indices':v['indices'],'complete':True,'max_gap':cap['max_gap'],'stable_binding':True,'input_index':specs['input_index'],'event_revision':min(specs['after_action'],4),'intervals':cap['intervals']})
 dispatches=[]
 for step in obs['steps']:
  a=step.get('action',step);typ=a['type']
  if typ not in ['tap','apply_next_fixture']:continue
  d=step['dispatch'];assert d['attempted'] and d['succeeded']
  assert d['method']==('caller_fixture_update' if typ=='apply_next_fixture' else 'xcui_tap' if platform=='ios' else 'compose_onclick')
  if typ=='tap':assert d['matches']==1 and d['native_controls']==1 and d['enabled'] and d['event_end']==d['event_start']+1
  else:assert d['event_end']==d['event_start']
  before=d['binding_before'];after=step['binding_after'];assert before['instance']==after['instance']
  if 'pid' in before:assert before['pid']==after['pid']
  dispatches.append({'state':step.get('state_id',a.get('state_id')),'method':d['method'],'interval':[d['event_start'],d['event_end']],'one_enabled_control':typ=='tap','instance_preserved':True})
 failures=[a['id'] for a in auto['assertions'] if a['status']=='failed']
 for aid in failures:all_alarms.add((candidate,scope,platform,case,aid))
 summaries.append({'candidate':candidate,'scope':scope,'platform':platform,'case':case,'observation_sha256':sha(p/'native/observation.json'),'states':states,'dispatches':dispatches,'automatic_counts':dict(collections.Counter(a['status'] for a in auto['assertions'])),'original_failed_ids':failures,'environment_status':env['status'],'coverage_satisfied':cv['satisfied']})
alarms=read(O/'alarm-judgments.json');assert {(a['candidate'],a['scope'],a['platform'],a['case'],a['assertion_id']) for a in alarms}==all_alarms
assert read(O/'extra-findings.json')==[]
assert source_count==110 and visual_count==144 and len(summaries)==12
out=O/'inspection/binding-review.json';assert not out.exists();out.write_text(json.dumps({'source_decisions':source_count,'visual_decisions':visual_count,'cases':summaries,'limitations':'Structural binding/coverage/dispatch audit only. The manual image judgments are in the original submissions; automatic F values are unchanged.'},indent=2)+'\n')
print('Verified',source_count,'source decisions;',visual_count,'visual decisions;',len(summaries),'cases;',len(all_alarms),'original alarms. Exact catalog hashes, complete state indices, epoch bindings, successful native dispatch intervals, and source citations verified.')
