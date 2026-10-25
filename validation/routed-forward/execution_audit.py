#!/usr/bin/env python3
"""Portable actual dispatch adoption/selection chronology; not a product grade."""
import json
from pathlib import Path
import study as s
import design_contract as d,retest_plan,requirement_routes as routes
R=s.R

def namespace(files):return{str(i)+'/'+k[len(prefix)+1:]:h for i,prefix in enumerate(s.ROOTS)for k,h in files.items()if k.startswith(prefix+'/')}
def main():
 s.tool_verify();assignment=s.read(R/'private/assignment.json')['units'];out=[]
 for unit,cfg in assignment.items():
  previous=s.read(R/'handoff'/unit/'SESSION-original.json')['previous'];cycles=[];runs=[]
  phases=[('intake',R/'handoff'/unit,R/'submissions'/unit/'initial/seal.json')]
  phases += [(p.name,p/'evidence',R/'submissions'/unit/('feedback-'+p.name.split('-')[-1])/'seal.json')for p in sorted((R/'feedback'/unit).glob('request-*'))]
  phases += [('final',R/'corpora'/unit/'final-public',R/'submissions'/unit/'final/seal.json')]
  for phase,root,seal in phases:
   now=namespace(s.read(seal)['files'])
   for path in sorted(root.rglob('cycle.json')):
    cycle=s.read(path);base=path.parent;pl=next(v for v in path.parts if v in ['ios','android']);case=base.parent.name if base.name=='intake'else base.name
    scope=R/'design/public';approval=s.read(scope/'approval.json');plan=s.read(scope/'compiled'/case/pl/'plan.json');lock=s.read(scope/'design-lock.json')
    prior=previous[pl][case];matches=[p for p in(R/'corpora').rglob('result.json')if(p.parent/'source-before.json').is_file()and s.sha(p)==prior['sha256']]
    matches += [p for p in(R/'feedback'/unit).rglob('result.json')if(p.parent/'source-before.json').is_file()and s.sha(p)==prior['sha256']]
    assert matches,'Missing original preceding capture';original=matches[0].parent;before=s.read(original/'source-before.json');obs=s.read(original/'native/observation.json');execution=s.read(original/'execution.json')
    report=s.read(base/'before-evaluated.json')if cycle['version']==2 else s.read(original/'automatic.json')
    coverage=routes.audit(lock,approval['design_lock_sha256'],plan,s.read(scope/'routes.json'),approval['routes_sha256'])
    routed=routes.route_findings(coverage,plan,report,obs,execution=execution);assert routed==s.read(base/'before-routes.json')
    kwargs={'changed_files':sorted(k for k in set(before)|set(now)if before.get(k)!=now.get(k)),'source_before':d.digest(before),'source_after':d.digest(now),'final':cycle['final'],'selected_states':execution['selected_states']}
    if cycle['version']==2:
     import review_contract
     cat=review_contract.catalog(plan,lock,approval['design_lock_sha256'],s.read(scope/'policy.json'),approval['policy_sha256'],pl)
     expected=retest_plan.dispatch(coverage,plan,report,routed,visual_ids={v['id']for v in cat['rows']if v['method']=='visual'},capture_available=True,**kwargs)
     assert cycle['source_sha256']==d.digest(now)
    else:expected=retest_plan.unresolved(coverage,plan,report,**kwargs)
    assert s.read(base/'retest-plan.json')==expected,str(path)
    if cycle['native_executed']:
     actual=s.read(base/'capture/execution.json');assert actual['selected_states']==expected['states']
     assert d.digest(s.read(base/'capture/source-before.json'))==d.digest(now)
    cycles.append({'path':str(path.relative_to(R)),'phase':phase,'platform':pl,'native_executed':cycle['native_executed'],'states':expected['states'],'review_imported':'reconstruct_bound_review'in cycle['trace'],'source_changed':bool(kwargs['changed_files']),'trace':cycle['trace']})
   if phase.startswith('request-'):previous=s.read(root.parent/'next-previous.json')['previous']
  for root in [R/'feedback'/unit,R/'corpora'/unit/'final-public']:
   for p in sorted(root.rglob('result.json')):
    if not(p.parent/'source-before.json').is_file():continue
    packet=s.read(p);runs.append({'path':str(p.relative_to(R)),'scope':packet['scope'],'status':packet['status'],'wall_seconds':packet['finishedAtUnix']-packet['startedAtUnix'],'startedAtUnix':packet['startedAtUnix'],'source_sha256':packet['source_sha256']})
  out.append({'unit':unit,'condition':cfg['mode'],'cycles':cycles,'planner_calls':len(cycles),'native_runs':runs,'default_image_completions':len(list((R/'self-review'/unit).rglob('completion.json'))),'scope':'Original actuals import and exact selection replay, no product success or cost attribution inferred.'})
 return {'arms':out,'scope':'Same initial capsules, immutable latest-capture pointers, actual source-delta maps and full-final selections replayed; no SDK.'}
if __name__=='__main__':print(json.dumps(main(),indent=2))
