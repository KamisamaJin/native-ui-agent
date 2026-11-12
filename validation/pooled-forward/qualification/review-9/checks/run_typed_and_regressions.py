from pathlib import Path
source=Path(__file__).with_name('run_query_scope.py').read_text().split("for platform in['ios','android']:")[0].replace("a.arm/'query';base.mkdir", "a.arm/'typed-regressions';base.mkdir")
exec(compile(source,str(Path(__file__).with_name('run_query_scope.py')),'exec'))

# Exact raw old SC11 references are read unchanged; assert reference rejection
# specifically rather than relying on newly required query metadata being absent.
prior=ROOT.parent/'review-7';old_names=['capture-index-bool','M01-full-after-action-bool','M02-full-after-action-float','M03-legacy-action-snapshot-bool']
for name in old_names:
 group='metadata-scope'if name.startswith('M')else'delta';folder=prior/'work'/oldarm/group/name;o=load(folder/'observation.json');s=load(folder/'state.json');ev=native_checks.bound_state_evidence(o,s,folder/'packet/native');record('raw-old-'+name,not ev[0]and not ev[1],{'observation_sha256':sha(folder/'observation.json'),'actual_found':len(ev[0]),'complete':ev[1],'reason':ev[2],'original_bytes_unchanged':True})

def mutate(name,o,s,n,t):
 if name=='full-snapshot-bool':o['state_captures'][0]['snapshot_indices'][0]=False
 elif name=='full-snapshot-float':o['state_captures'][0]['snapshot_indices'][0]=0.0
 elif name=='full-snapshot-negative':o['state_captures'][0]['snapshot_indices'][0]=-1
 elif name=='full-snapshot-duplicate':o['state_captures'][0]['snapshot_indices']=[0,0,2]
 elif name=='full-action-bool':o['state_captures'][0]['after_action']=False
 elif name=='full-action-float':o['state_captures'][0]['after_action']=0.0
 elif name=='state-action-bool':s['after_action']=False
 elif name=='bundle-action-bool':o['steps'][0]['observation_set']['after_action']=False
 elif name=='bundle-snapshot-bool':o['steps'][0]['observation_set']['snapshot_indices'][0]=False
 elif name=='bundle-immediate-float':o['steps'][0]['immediate_after']=0.0
 elif name=='bundle-last-bool':o['steps'][0]['after']=False
 elif name=='legacy-last-bool':o['steps'][0].pop('observation_set');o['steps'][0]['after']=False
 elif name=='legacy-last-float':o['steps'][0].pop('observation_set');o['steps'][0]['after']=0.0
 elif name in{'full-input-bool','target-input-bool'}:
  def visit(v):
   if isinstance(v,dict):
    for k in list(v):
     if k=='fixture_index':v[k]=False
     else:visit(v[k])
   elif isinstance(v,list):
    for item in v:visit(item)
  visit(o)
 else:raise AssertionError(name)
for name in['full-snapshot-bool','full-snapshot-float','full-snapshot-negative','full-snapshot-duplicate','full-action-bool','full-action-float','state-action-bool','full-input-bool','bundle-action-bool','bundle-snapshot-bool','bundle-immediate-float','bundle-last-bool','legacy-last-bool','legacy-last-float','target-input-bool']:
 local=name.startswith(('bundle','legacy','target'));prop='present';expected=True if local else False
 evaluate(name,'ios',local,prop,expected,'unassessed',lambda o,s,n,t,name=name:mutate(name,o,s,n,t),False)

# Relevant prior certificate/domain regressions, under current complete-query ABI.
def regression(name,o,s,n,t):
 if name=='original-PNG16-rejected':
  old_6=ROOT.parent/'review-6/work'/('candidate-v13.5'if a.arm.startswith('candidate')else'baseline-v12.6-common-2')/('admitted-runtime-retry-1'if a.arm.startswith('candidate')else'admitted-runtime')/'A07-raster16-lowbit-admitted-host/packet/native'
  for file in old_6.glob('frame-*.png'):shutil.copyfile(file,n/file.name)
 elif name=='native-width-stays-strict':
  for snap in o['snapshots']:snap['nodes'][2]['frame']['width']=30.000000000000007
 elif name=='runtime-shape-rejected':
  for snap in o['snapshots']:snap['runtime']['offered_width']=389
 elif name=='stable-runtime-domain-rejected':
  for snap in o['snapshots']:snap['runtime']['content_frame']['height']=1100;snap['runtime']['offered_width']=389
 elif name=='actual-compiled-host-rejected':(n/'compiled-project/ObserverApp.swift').write_text('// different compiledhost\n')
 elif name=='original-joint-chain-rejected':
  source=prior/'work'/oldarm/'delta/ABI-A08-joint-witness-admitted-host';replacement=load(source/'observation.json');o.clear();o.update(replacement)
  for snap in o['snapshots']:
   for node in snap['nodes']:node['index']+=1;node['parent_index']=node['parent_index']+1 if node['parent_index']>=0 else 0
   snap['nodes'].insert(0,{'index':0,'parent_index':-1,'identifier':'','role_raw':2,'frame':copy.deepcopy(snap['app_frame'])});snap['performance']={'native_query_mode':'single_public_snapshot'}
  for file in(source/'packet/native').glob('frame-*.png'):shutil.copyfile(file,n/file.name)
 else:raise AssertionError(name)
for name in['original-PNG16-rejected','runtime-shape-rejected','stable-runtime-domain-rejected','actual-compiled-host-rejected','original-joint-chain-rejected']:
 evaluate(name,'ios',False,'present',False,'unassessed',lambda o,s,n,t,name=name:regression(name,o,s,n,t),False)
folder=base/'native-width-stays-strict';folder.mkdir();o,s,n=ios(folder);regression('native-width-stays-strict',o,s,n,{})
plan={'version':1,'states':[s],'required_assertion_ids':['raw'],'assertions':[{'id':'raw','state':'start','kind':'geometry','target':{'identifier':'anchor-a'},'property':'width','basis':'semantic','op':'eq','expected':30}]};report=native_checks.evaluate(plan,o,'ios',root=n);save(folder/'observation.json',o);save(folder/'state.json',s);save(folder/'evaluated.json',report);record('native-width-stays-strict',report['states']['start']['complete']and report['assertions'][0]['status']=='failed',{'report':report})

# The shared solver bytes did not change. Replay only its pertinent alternatives
# and closed default budget, using independent old finite-domain oracles.
for name in['C01-nonminimum-choice','C03-odd-cycle-unsat','C04-alternative-link-pairs']:
 data=load(prior/'work'/oldarm/'csp'/(name+'.json'));domains={k:{tuple(rect)for rect in values}for k,values in data['domains'].items()};links=[{'witness_pairs':[tuple(v)for v in clause]}for clause in data['link_clauses']];orders={tuple(v[:2]):v[2]for v in data['orders']};result=scroll_coverage.joint_assignment({k:{'rectangles':v}for k,v in domains.items()},links,orders);record(name,(result['assignment']is not None)==(data['oracle_assignment']is not None),{'original_independent_oracle':data['oracle_assignment'],'actual':result})
import itertools
keys=list('ABCDEFGHI');positions={(0,2*i,1,2*i+1)for i in range(8)};result=scroll_coverage.joint_assignment({k:{'rectangles':positions}for k in keys},[{'witness_pairs':[(x,y)]}for x,y in itertools.combinations(keys,2)],{});record('C65-10000-bound-still-closed',result['assignment']is None and result['visited_nodes']==10000 and result['status']=='search_budget_exhausted',{'actual':result,'oracle':'Pigeonhole UNSAT,9 identities8 pairwise-distinct positions. HOST helper only, not physical ABI/timing credit.'})
save(ROOT/'raw'/(a.arm+'-typed-regression-results.json'),rows)
