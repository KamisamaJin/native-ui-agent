#!/usr/bin/env python3
"""Create original actuals tasks for the shared initial PR; no expected overrides."""
import time
import study as s
import review_contract as review,design_contract as d,native_checks as checks
R=s.R;s.gate.authorize(R/'gates','d0-raw',R);scope=R/'design/public';approval=s.read(scope/'approval.json');capture_root=R/s.read(R/'operators/active-D0.json')['path']
for pl in ['ios','android']:
 for case in sorted((scope/'cases').iterdir()):
  base=capture_root/pl/case.name;op=base/'native/observation.json';out=R/'d0-review'/pl/case.name;out.mkdir(parents=True,exist_ok=False)
  if not op.is_file():s.save(out/'unavailable.json',{'reason':'No original observation; no actual may be invented'});continue
  plan=s.read(scope/'compiled'/case.name/pl/'plan.json');obs=s.read(op);cat=review.catalog(plan,s.read(scope/'design-lock.json'),approval['design_lock_sha256'],s.read(scope/'policy.json'),approval['policy_sha256'],pl)
  s.save(out/'catalog.json',cat);s.save(out/'request.json',{'capture':str(base),'capture_sha256':s.sha(base/'result.json'),'sourceSHA256':s.read(base/'result.json')['source_sha256'],'observationSHA256':s.sha(op)})
  s.save(out/'state-image-index.json',{state['id']:{'indices':[i for i,_ in checks.bound_state_evidence(obs,state)[0]],'complete':checks.bound_state_evidence(obs,state)[1],'reason':checks.bound_state_evidence(obs,state)[2]}for state in plan['states']})
  s.save(out/'template.json',{'version':1,'catalog_sha256':d.digest(cat),'observation_sha256':s.sha(op),'decisions':[{'review_id':row['review_id'],'actual':None,'reason':'Original observed proposition or honest unknown required','snapshot_indices':[]}for row in cat['rows']if row['method']=='visual']})
s.save(R/'operators/d0-review-start.json',{'startedAtUnix':time.time(),'scope':'Common original image review; both arms receive same actuals before handoff.'})
print(R/'d0-review')
