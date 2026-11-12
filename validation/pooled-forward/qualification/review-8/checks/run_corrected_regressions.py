from pathlib import Path
query=Path(__file__).with_name('run_query_scope.py').read_text().split("for platform in['ios','android']:")[0].replace("a.arm/'query';base.mkdir", "a.arm/'corrected-regressions';base.mkdir")
exec(compile(query,str(Path(__file__).with_name('run_query_scope.py')),'exec'))
prior=ROOT.parent/'review-7'
typed=Path(__file__).with_name('run_typed_and_regressions.py').read_text();body=typed.split('def regression(name,o,s,n,t):',1)[1].split("for name in['original-PNG16-rejected'",1)[0];exec(compile('def regression(name,o,s,n,t):'+body,str(Path(__file__).with_name('run_typed_and_regressions.py')),'exec'))
for name in['original-PNG16-rejected','runtime-shape-rejected','stable-runtime-domain-rejected','actual-compiled-host-rejected','original-joint-chain-rejected']:
 def change(o,s,n,t,name=name):t['identifier']='absent-regression-target';regression(name,o,s,n,t)
 evaluate(name,'ios',False,'present',False,'unassessed',change,False)
save(ROOT/'raw'/(a.arm+'-corrected-regression-results.json'),rows)
