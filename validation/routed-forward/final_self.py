#!/usr/bin/env python3
"""Existing approved qualitative actuals -> bound evaluation -> full-self endpoint."""
import argparse,time
from pathlib import Path
import study as s
import design_contract as d,review_contract as review,native_checks,requirement_routes as rr,acceptance
R=s.R
p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','close']);p.add_argument('--unit',required=True);a=p.parse_args()
cfg=s.read(R/'private/assignment.json')['units'][a.unit];scope=R/'design/public';approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');policy=s.read(scope/'policy.json')
root=R/'self-review'/a.unit
if a.command=='prepare':root.mkdir(parents=True,exist_ok=False)
rows=[]
for case in sorted((scope/'cases').iterdir()):
 for pl in ['ios','android']:
  capture=R/'corpora'/a.unit/'final-public'/pl/case.name
  if cfg['mode']in {'default','baseline'}:capture=capture/'capture'
  plan=s.read(scope/'compiled'/case.name/pl/'plan.json');op=capture/'native/observation.json';out=root/pl/case.name
  if a.command=='prepare':
   out.mkdir(parents=True,exist_ok=False)
   if not op.is_file():s.save(out/'unavailable.json',{'reason':'No final native observation; no visual pass can be submitted'});continue
   catalog=review.catalog(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],pl)
   s.save(out/'catalog.json',catalog)
   s.save(out/'request.json',{'capture':str(capture),'observation_sha256':s.sha(op),'sourceSealSHA256':s.sha(R/'submissions'/a.unit/'final/seal.json'),'catalog_sha256':d.digest(catalog)})
   s.save(out/'template.json',{'version':1,'catalog_sha256':d.digest(catalog),'observation_sha256':s.sha(op),
      'decisions':[{'review_id':r['review_id'],'actual':None,'reason':'REPLACE WITH ORIGINAL OBSERVATION OR HONEST UNKNOWN','snapshot_indices':[]}for r in catalog['rows']if r['method']=='visual']})
  else:
   if not op.is_file():rows.append({'platform':pl,'case':case.name,'status':'not_accepted','reason':'No final observation'});continue
   submission=out/'submission.json';assert submission.is_file(),'Original final image actuals required'
   request=s.read(out/'request.json');assert request['observation_sha256']==s.sha(op)
   receipt=s.read(capture/'result.json');s.xp.verify_capture_images(receipt,op.parent)
   config=s.configuration(R/'cache'/a.unit,scope,case.name,pl,cfg['simulator'])
   if cfg['mode']=='default':
    import evidence_review,feedback_loop
    reference=evidence_review.bind(config,capture/'result.json',s.sha(capture/'result.json'),submission,s.sha(submission),Path(config['review_store'])/('final-'+s.sha(submission)))
    cycle=capture.parent/'cycle.json';feedback_loop.complete_review(config,cycle,s.sha(cycle),None,out/'completion')
   manual=review.bind(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],s.read(op),s.sha(op),op.parent,s.read(submission),pl)
   evaluated=native_checks.evaluate(plan,s.read(op),pl,manual,op.parent,s.sha(op),lock,approval['design_lock_sha256'],policy,approval['policy_sha256'])
   cov=rr.audit(lock,approval['design_lock_sha256'],plan,s.read(scope/'routes.json'),approval['routes_sha256'])
   env=acceptance.environment(s.read(op),s.read(case/('environment.'+pl+'.json')),pl)
   admission=rr.admission(cov,plan,evaluated,capture=receipt,environment=env)
   s.save(out/'bound-manual.json',manual);s.save(out/'evaluated.json',evaluated);s.save(out/'admission.json',admission)
   rows.append({'platform':pl,'case':case.name,'status':admission['status'],'counts':evaluated['counts'],'submissionSHA256':s.sha(submission)})
if a.command=='close':
 w=R/'cache'/a.unit;assert s.fingerprint(w)==s.read(R/'submissions'/a.unit/'final/seal.json')['files'],'Source changed during source-closed review'
 api=s.read(R/'corpora'/a.unit/'minimum-api/record.json');assert api['source']==s.fingerprint(w)
 endpoint={'finishedAtUnix':time.time(),'handoffAtUnix':s.read(w/'SESSION.json')['handoffAtUnix'],'rows':rows,'source_api':api['status'],
           'status':'accepted_within_public_self_scope'if rows and all(v['status']=='accepted'for v in rows)and api['status']=='source_api_typechecked'else'not_accepted',
           'scope':'Fresh full-public self evidence and original actuals; independent hidden/quality acceptance remains required.'}
 s.save(R/'self-endpoints'/(a.unit+'.json'),endpoint)
print(root)
