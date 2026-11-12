from pathlib import Path
source=(Path(__file__).resolve().parents[2]/'review-8/checks/run_query_scope.py').read_text().split("for platform in['ios','android']:")[0].replace("a.arm/'query';base.mkdir", "a.arm/'wire-delta';base.mkdir")
exec(compile(source,str(Path(__file__).resolve().parents[2]/'review-8/checks/run_query_scope.py'),'exec'))
# Complete explicit query formats need no claim that a partial parent graph is a
# whole snapshot. Preserve full native tree or use only the explicit query body.
def group_only(o,s,n,t,resolution='no_native_control'):
 explicit(o,s,n,t,resolution)
 for snap in o['snapshots']:snap['nodes']=[];snap.pop('performance',None)
def legacy_flat(o,s,n,t):
 for snap in o['snapshots']:
  matched=[dict(node)for node in snap['nodes']if node.get('identifier')==t['identifier']]
  for node in matched:node.pop('index',None);node.pop('parent_index',None)
  snap['nodes']=matched;snap.pop('performance',None)
 explicit(o,s,n,t)
evaluate('ios-explicit-query-only-valid','ios',True,'unique',True,'passed',group_only,False)
evaluate('ios-explicit-legacy-flat-valid','ios',True,'unique',True,'passed',legacy_flat,False)
evaluate('ios-explicit-plus-full-native-tree-valid','ios',True,'unique',True,'passed',explicit,False)
evaluate('ios-unsupported-query-only-resolution','ios',True,'unique',True,'unassessed',lambda o,s,n,t:group_only(o,s,n,t,'singleton_only_not_enumerated'),False)
evaluate('ios-header-identity-conflict','ios',True,'unique',True,'unassessed',lambda o,s,n,t:(explicit(o,s,n,t),o['snapshots'][0]['control_groups'][0]['semantic'].update(index=999)),False)
evaluate('ios-header-visibility-conflict','ios',True,'present',True,'unassessed',lambda o,s,n,t:(explicit(o,s,n,t),o['snapshots'][0]['control_groups'][0]['semantic'].update(intersects_viewport=False)),False)
evaluate('ios-nonapplication-native-root','ios',True,'unique',True,'unassessed',lambda o,s,n,t:o['snapshots'][0]['nodes'][0].update(role_raw=49),False)
evaluate('android-geometry-version-bool','android',True,'unique',True,'unassessed',lambda o,s,n,t:o['snapshots'][0]['nodes'][1]['native_geometry'].update(version=True),False)
evaluate('android-geometry-unit-unknown','android',True,'unique',True,'unassessed',lambda o,s,n,t:o['snapshots'][0]['nodes'][1]['native_geometry'].update(coordinate_unit='dp'),False)
evaluate('android-size-float','android',True,'unique',True,'unassessed',lambda o,s,n,t:o['snapshots'][0]['nodes'][1]['native_geometry']['size_px'].__setitem__(0,30.0),False)
evaluate('android-geometry-density-mismatch','android',True,'unique',True,'unassessed',lambda o,s,n,t:o['snapshots'][0]['nodes'][1]['native_geometry'].update(density=2),False)

# Formal native M is known even when its one entity lies outside the rendered
# viewport: existing emitted offscreen_not_resolved is a complete count1 query.
def offscreen(o,s,n,t,query_only=False,duplicate_entity=False):
 snap=o['snapshots'][0];matches=[node for node in snap['nodes']if node.get('identifier')==t['identifier']]
 for node in matches:
  node['intersects_viewport']=False
  if'frame'in node:node['frame']['y']=700;node['fully_within_viewport']=False
  else:
   node['fully_visible']=False;node['native_geometry']['position_px'][1]=700;node['unclipped_bounds_dp']=[20,700,50,740];node['bounds_dp']=[20,600,50,600];node['touch_bounds_dp']=[20,700,50,740]
 if query_only:
  explicit(o,s,n,t,'offscreen_not_resolved')
  for sample in o['snapshots']:sample['nodes']=[];sample.pop('performance',None)
 if duplicate_entity:
  other=copy.deepcopy(matches[0]);key='index'if'index'in other else'node_id';other[key]=max(node[key]for node in snap['nodes'])+1;snap['nodes'].append(other)
for platform in['ios','android']:
 evaluate(platform+'-offscreen-count1-presence',platform,True,'present',True,'passed',offscreen,False)
 evaluate(platform+'-offscreen-count1-local-cardinality',platform,True,'unique',True,'passed',offscreen,False)
 evaluate(platform+'-offscreen-count2-presence-control',platform,True,'present',True,'passed',lambda o,s,n,t:offscreen(o,s,n,t,duplicate_entity=True),False)
evaluate('ios-explicit-offscreen-count1-presence','ios',True,'present',True,'passed',lambda o,s,n,t:offscreen(o,s,n,t,True),False)
save(ROOT/'raw'/(a.arm+'-wire-delta-results.json'),rows)
