from pathlib import Path
import json,hashlib,datetime,sys,struct
R=Path(__file__).resolve().parent;T=R.parent/'candidate-v8'/'scripts';sys.path.insert(0,str(T));import design_contract as d,review_contract as rc
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for tid in ['T1','T2','T3']:
 for scope,cases in [('public',['P1','P2']),('private',['H1'])]:
  b=R/tid/scope;app=d.load(b/'approval.json');lock=d.load(b/'design-lock.json');pol=d.load(b/'policy.json');d.validate_lock(lock,app['design_lock_sha256']);assert d.digest(pol)==app['policy_sha256'];assert pol['atoms'][0]['sampling']['region']==[.02,.05,.03,.95]
  for cid in cases:
   cs=b/'cases'/cid;comp=b/'compiled'/cid;fixtures=d.load(cs/'fixtures.json');li={'T1':'slots','T2':'incidents','T3':'services'}[tid]
   for model in [fixtures['initial'],*fixtures['updates']]:
    assert isinstance(model['guidance'],str) and model['guidance']
    for item in model[li]:assert bool(item['unavailableReason'])==not item['available']
   meta=d.load(b/f'reference-{cid}-expanded.meta.json')
   for ext in ['svg','png']:assert sha(b/f'reference-{cid}-expanded.{ext}')==meta[ext+'_sha256']
   for platform in ['ios','android']:
    plan=d.load(comp/platform/'plan.json');acts=d.verify_generated(plan,lock,app['design_lock_sha256'],platform);assert acts==d.load(comp/platform/'actions.json');cat=rc.catalog(plan,lock,app['design_lock_sha256'],pol,app['policy_sha256'],platform);assert d.digest(cat)==d.load(comp/platform/'catalog.json')['catalog_sha256'];assert d.digest(d.load(cs/f'environment.{platform}.json'))==app['environment_sha256'][cid][platform]
    for p in cs.iterdir():assert p.read_bytes()==(comp/p.name).read_bytes()
    for state in plan['states']:
     ix=state['after_action'];assert sum(a['type']=='apply_next_fixture' for a in acts[:ix+1])==state['input_index'];assert acts[ix]['state_id']==state['id']
     if 'stimulus_action' in state:assert acts[state['stimulus_action']]['type']=='tap' and acts[ix]['type']=='sweep'
    rows.append({'task':tid,'case':cid,'platform':platform,'actions':len(acts),'states':len(plan['states']),'rules':len(plan['matrix_contract']['selected_requirements']),'assertions':len(plan['assertions']),'lock_route_plan_catalog_environment_copies':True,'input_action_checkpoints':True})
  if scope=='private':assert lock['contract']['rules']==d.load(R/tid/'public'/'design-lock.json')['contract']['rules']
# Check v1 only against its own sealed inventory. Never traverse tool-gate other members.
v1=R.parent/'design-v1';old=d.load(v1/'seal.json');mismatches=[n for n,h in old['files_sha256'].items() if not (v1/n).is_file() or sha(v1/n)!=h];assert not mismatches
f32=lambda n:struct.unpack('!f',struct.pack('!f',n))[0];gutter=[]
for w in range(160,403):
 for platform in ['ios','android']:
  child=w-32 if platform=='ios' else f32(int(f32(f32(w)*f32(2.75)))/2.75)-32
  edge=child*.03;assert edge<12;gutter.append(edge)
gate=d.load(R.parent/'gates'/'tools.json');files={n:h for n,h in gate['members']['candidate-v8'].items() if n.startswith('candidate-v8/')};assert len(files)==54;assert all(sha(R.parent/n)==h for n,h in files.items())
assert not d.load(R/'REFERENCE-QA.json')['violations']
out={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':rows,'v1_preserved_sha256':sha(v1/'seal.json'),'v1_sealed_files_verified':len(old['files_sha256']),'v1_mismatches':mismatches,'frozen_skill_files_verified':len(files),'gutter_proof':{'offered_native_widths':[160,402],'platforms':['ios','android-pinned-float32'],'maximum_sample_outer_edge_native':max(gutter),'guaranteed_empty_gutter_native':12,'all_fit':True},'reference_svg_glyph_bounds':'9/9 all within12-unit canvas gutter','new_unavailable_reason_and_guidance_input_consistency':True,'native_sdk_invocations':0,'design_quality_approval':False}
(R/'delivery-integrity.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'integrity_runs':len(rows),'v1_unchanged':True,'max_canvas_sample_edge':max(gutter),'frozen_files':len(files)}))
