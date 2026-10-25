#!/usr/bin/env python3
"""Read-only portable replay of original independent actuals and all bindings."""
import study as s
import design_contract as d,review_contract as review,native_checks,requirement_routes as rr,acceptance
from source_self import audit,catalog as source_catalog
R=s.R

def main():
 s.gate.authorize(R/'gates','quality-panels',R);counts={'source_submissions':0,'visual_submissions':0}
 candidates=sorted(p for p in(R/'quality-inputs').iterdir()if p.name.startswith('candidate-'))
 for phase in ['public','private']:
  identity=s.read(R/'quality-inputs/source-review'/phase/'identity.json')
  for candidate in candidates:
   cat=source_catalog(R/'design'/phase,candidate/'source');group='shared-identical-sources'if identity['shared']else candidate.name
   assert cat==s.read(R/'quality-inputs/source-review'/phase/group/'catalog.json')
  for group in sorted((R/'quality-inputs/source-review'/phase).iterdir()):
   if not group.is_dir():continue
   cat=s.read(group/'catalog.json')
   for panel in ['panel-one','panel-two']:
    assert audit.bind(cat,s.read(R/'quality-panels'/panel/'source'/phase/group.name/'submission.json'))==s.read(R/'quality-evaluation'/panel/'source'/phase/(group.name+'.json'))
    counts['source_submissions']+=1
 for candidate in candidates:
  for phase in ['public','private']:
   scope=R/'design'/phase;approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');policy=s.read(scope/'policy.json')
   for pl in ['ios','android']:
    for case in sorted((scope/'cases').iterdir()):
     base=candidate/'native'/phase/pl/case.name;op=base/'native/observation.json';plan=s.read(base/'parent-plan.json');observation=s.read(op)
     for panel in ['panel-one','panel-two']:
      original=R/'quality-panels'/panel/'visual'/candidate.name/phase/pl/case.name/'submission.json';dest=R/'quality-evaluation'/panel/'runtime'/candidate.name/phase/pl/case.name
      manual=review.bind(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],observation,s.sha(op),op.parent,s.read(original),pl)
      assert manual==s.read(dest/'manual.json')
      evaluated=native_checks.evaluate(plan,observation,pl,manual,op.parent,s.sha(op),lock,approval['design_lock_sha256'],policy,approval['policy_sha256']);assert evaluated==s.read(dest/'evaluated.json')
      cov=rr.audit(lock,approval['design_lock_sha256'],plan,s.read(scope/'routes.json'),approval['routes_sha256'])
      assert rr.admission(cov,plan,evaluated)['obligations']==s.read(dest/'obligations.json')
      counts['visual_submissions']+=1
 print({'status':'PASS',**counts,'scope':'Original independent Boolean actuals and source/native/image binding replay; no human-gold or SDK rerender claim.'})
if __name__=='__main__':main()
