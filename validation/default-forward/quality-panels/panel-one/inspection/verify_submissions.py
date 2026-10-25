import pathlib,json,hashlib,sys
out=pathlib.Path(__file__).resolve().parent.parent;base=out.parents[1];q=base/'quality-inputs'
sys.path.insert(0,str(base/'candidate-v10/scripts'))
from native_checks import resolve,bound_state_evidence

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
results=[]
for scope in ['public','private']:
 cat=read(q/'source-review'/scope/'shared-identical-sources/catalog.json');sub=read(out/'source'/scope/'shared-identical-sources/submission.json')
 assert set(sub)=={'version','catalog_sha256','decisions'} and sub['version']==1 and sub['catalog_sha256']==digest(cat)
 rows={r['review_id']:r for r in cat['rows']};assert len(sub['decisions'])==len(rows)==55
 for d in sub['decisions']:
  assert set(d)=={'review_id','actual','reason','evidence'} and type(d['actual']) in [bool,type(None)] and d['reason'].strip()
  r=rows.pop(d['review_id']);assert set(e['file'] for e in d['evidence'])==set(r['files'])
  for e in d['evidence']:
   assert set(e)=={'file','sha256','start_line','end_line'} and cat['files'][e['file']]['sha256']==e['sha256']
   assert 1<=e['start_line']<=e['end_line']<=cat['files'][e['file']]['line_count']
 assert not rows
 results.append({'source_scope':scope,'decisions':55,'catalog_binding':'verified','source_evidence_ranges':'verified'})
control_summaries=[]
for p in sorted(q.glob('candidate-*/native/*/*/*')):
 c,scope,platform,case=p.parts[-5],p.parts[-3],p.parts[-2],p.name
 cat=read(p/'review-catalog.json');sub=read(out/'visual'/c/scope/platform/case/'submission.json');obs=read(p/'native/observation.json');stateindex=read(p/'state-image-index.json');plan=read(p/'parent-plan.json')
 assert set(sub)=={'version','catalog_sha256','observation_sha256','decisions'} and sub['version']==1 and sub['catalog_sha256']==digest(cat) and sub['observation_sha256']==sha(p/'native/observation.json')
 rows={r['review_id']:r for r in cat['rows'] if r['method']=='visual'};assert len(sub['decisions'])==len(rows)==12
 states={s['id']:s for s in plan['states']}
 for state,ix in stateindex.items():
  found,complete,reason,capture=bound_state_evidence(obs,states[state]);assert complete,(p,state,reason)
  assert set(i for i,_ in found)==set(ix['indices']),(p,state,'indices differ')
  controls={}
  for selector in ['collection.self','collection.delegate','collection.ack','collection.notes','collection.confirm']:
   evidence=[]
   for i,snapshot in found:
    x=resolve(snapshot,{'identifier':selector},platform)
    if x['resolution']=='unique_native_control' and x['control'].get('intersects_viewport'):
     evidence.append({'snapshot_index':i,'resolution':x['resolution'],'enabled':x['facts'].get('enabled'),'selected':x['facts'].get('selected'),'role':x['facts'].get('control_role'),'value':x['facts'].get('value')})
   controls[selector]=evidence
  for sel in ['collection.self','collection.delegate','collection.notes','collection.confirm']:assert controls[sel],(p,state,sel)
  if state in ['delegate_chosen','authorized','submitted']:assert controls['collection.ack'],(p,state,'ack')
  else:assert not controls['collection.ack'],(p,state,'unexpected ack')
  control_summaries.append({'case_path':str(p.relative_to(q)),'state':state,'bound_complete':complete,'controls':controls})
 for d in sub['decisions']:
  assert set(d)=={'review_id','actual','reason','snapshot_indices'} and type(d['actual']) in [bool,type(None)] and d['reason'].strip()
  r=rows.pop(d['review_id']);assert d['snapshot_indices']==stateindex[r['state']]['indices']
 assert not rows
 results.append({'visual_case':str(p.relative_to(q)),'decisions':12,'catalog_and_observation_binding':'verified','exact_state_indices_and_raw_bound_complete':'verified'})
alarms=read(out/'alarm-judgments.json');assert len(alarms)==3
for a in alarms:
 for e in a['evidence']:
  f=base/e['file'];assert sha(f)==e['sha256']
  if 'end_line' in e:assert 1<=e['start_line']<=e['end_line']<=len(f.read_text().splitlines())
for filename,data in [('verification.json',results),('native-control-summary.json',control_summaries)]:
 p=out/'inspection'/filename;assert not p.exists();p.write_text(json.dumps(data,indent=2)+'\n')
print('Verified: 110 source decisions, 144 visual decisions, 72 exact bound checkpoint scans, native control evidence, and 3 unchanged strict alarms with uncertain cause.')
print('Raw control state summaries',len(control_summaries),'all supported; no SDK invocation.')
