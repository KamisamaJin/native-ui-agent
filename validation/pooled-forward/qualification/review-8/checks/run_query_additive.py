from pathlib import Path
source=Path(__file__).with_name('run_query_scope.py').read_text().split("for platform in['ios','android']:")[0]
source=source.replace("a.arm/'query';base.mkdir", "a.arm/'query-additive';base.mkdir")
exec(compile(source,str(Path(__file__).with_name('run_query_scope.py')),'exec'))
for platform in['ios','android']:
 prefix=platform+'-'
 # Avoid removing a registration anchor when testing no-matches. This is a new
 # independent exact selector absent from the preserved native tree.
 def absent_selector(o,s,n,t):t['identifier']='never-native-target'
 evaluate(prefix+'corrected-full-complete-absence',platform,False,'present',False,'passed',absent_selector,True)
 evaluate(prefix+'local-complete-query-absence',platform,True,'present',False,'passed',absent_selector,False)
 evaluate(prefix+'local-complete-query-zero-unique',platform,True,'unique',False,'passed',absent_selector,False)
 evaluate(prefix+'same-identity-record-does-not-prove-nonunique',platform,True,'unique',False,'unassessed',lambda o,s,n,t:duplicate(o,s,n,t,True),False)

# Existing structured explicit iOS zero-result query, independently bound to the
# current native checkpoint, is a complete LOCAL empty matching domain.
evaluate('ios-explicit-empty-local-query','ios',True,'present',False,'passed',lambda o,s,n,t:(t.update(identifier='never-native-target'),no_tree(o,s,n,t),explicit(o,s,n,t,'missing',0)),False)
save(ROOT/'raw'/(a.arm+'-query-additive-results.json'),rows)
