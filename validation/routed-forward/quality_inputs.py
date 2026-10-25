#!/usr/bin/env python3
"""Normalize raw native packages for arm-blind quality review, without editing bytes."""
import secrets,shutil,time,hashlib
from pathlib import Path
import study as s
import design_contract as d,review_contract as review,native_checks
from source_self import catalog as source_catalog
R=s.R;s.gate.authorize(R/'gates','hidden',R);s.tool_verify()
assignment=s.read(R/'private/assignment.json');versions=['initial']+list(assignment['units']);secrets.SystemRandom().shuffle(versions)
index={};root=R/'quality-inputs';root.mkdir(parents=True,exist_ok=False)
for version in versions:
 key='candidate-'+secrets.token_hex(4);out=root/key;out.mkdir();index[key]={'version':version}
 capsule=R/'submissions'/('initial'if version=='initial'else version+'/final')
 shutil.copytree(capsule/'source',out/'source');shutil.copytree(capsule/'licenses',out/'licenses');shutil.copy2(capsule/'seal.json',out/'source-seal.json')
 for phase in ['public','private']:
  scope=R/'design'/phase
  for pl in ['ios','android']:
   for case in sorted((scope/'cases').iterdir()):
    if version=='initial':capture=(R/s.read(R/'operators/active-D0.json')['path']if phase=='public'else R/'corpora/initial/private')/pl/case.name
    else:
     capture=R/'corpora'/version/('final-public'if phase=='public'else'private')/pl/case.name
     if phase=='public'and assignment['units'][version]['mode']in {'default','baseline'}:capture=capture/'capture'
    dest=out/'native'/phase/pl/case.name;dest.mkdir(parents=True)
    for name in ['automatic.json','parent-plan.json','source-before.json','source-after.json','environment-check.json','execution.json','execution-coverage.json']:
     if(capture/name).is_file():shutil.copy2(capture/name,dest/name)
    native=capture/'native';target=dest/'native';target.mkdir()
    if native.exists():
     for source in sorted(native.rglob('*')):
      if source.is_file()and(source.name=='observation.json'or source.suffix.lower()=='.png'):
       destination=target/source.relative_to(native);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
    if (target/'observation.json').is_file():
     approval=s.read(scope/'approval.json');plan=s.read(scope/'compiled'/case.name/pl/'plan.json')
     cat=review.catalog(plan,s.read(scope/'design-lock.json'),approval['design_lock_sha256'],s.read(scope/'policy.json'),approval['policy_sha256'],pl)
     s.save(dest/'review-catalog.json',cat)
     s.save(dest/'review-template.json',{'version':1,'catalog_sha256':d.digest(cat),'observation_sha256':s.sha(target/'observation.json'),'decisions':[{'review_id':row['review_id'],'actual':None,'reason':'REPLACE WITH ORIGINAL OBSERVATION OR HONEST UNKNOWN','snapshot_indices':[]}for row in cat['rows']if row['method']=='visual']})
     obs=s.read(target/'observation.json');s.save(dest/'state-image-index.json',{state['id']:{'indices':[i for i,_ in native_checks.bound_state_evidence(obs,state)[0]],'complete':native_checks.bound_state_evidence(obs,state)[1]}for state in plan['states']})
    s.save(dest/'originals.json',{'rawCaptureRelativePath':str(capture.relative_to(R)),'rawFiles':s.table(capture),'scope':'Review copy only; original raw capture/receipt/source/inputs verified independently. No derived replacement image or verdict.'})
 # Original API compiler records; raw workspace names are opaque and arm names
 # are withheld. Reviewers must judge evidence rather than infer quality by age.
 api=R/'corpora'/version/'minimum-api'
 if api.exists():shutil.copytree(api,out/'minimum-api')
 s.seal_dir(out)
for phase in ['public','private']:
 catalogs={key:source_catalog(R/'design'/phase,root/key/'source')for key in index}
 first=next(iter(catalogs.values()));same=all(value==first for value in catalogs.values())
 for key,value in ({'shared-identical-sources':first}if same else catalogs).items():
  dest=root/'source-review'/phase/key;dest.mkdir(parents=True,exist_ok=True);s.save(dest/'catalog.json',value)
  s.save(dest/'template.json',{'version':1,'catalog_sha256':d.digest(value),'decisions':[{'review_id':row['review_id'],'actual':None,'reason':'REPLACE WITH ORIGINAL SOURCE OBSERVATION OR HONEST UNKNOWN','evidence':[]}for row in value['rows']]})
 s.save(root/'source-review'/phase/'identity.json',{'shared':same,'candidate_files':{key:value['files']for key,value in catalogs.items()},'scope':'Reuse source judgment only for exactly identical approved source file bytes; runtime evidence remains separate.'})
images={}
for path in root.rglob('*.png'):
 images.setdefault(s.sha(path),[]).append(str(path.relative_to(root)))
s.save(root/'image-sha-index.json',{'images':images,'scope':'Exact original-image deduplication only, never assume equal images from equal source.'})
s.save(R/'private/quality-map.json',{'createdAtUnix':time.time(),'candidates':index,'scope':'Reveal only after both quality panels seal.'})
s.save(root/'requirements-index.json',{'version':1,'native':{phase:{pl:[o['id']for o in s.read(R/'design'/phase/'reference.json')['obligations']]for pl in ['ios','android']}for phase in ['public','private']},
 'source_items':s.read(R/'design/public/audit-index.json')['items'],'scope':'Use scope:platform:obligation_id and source:item_id; inspect complete original prose and explicit source-review ledger too.'})
s.seal_dir(root);s.cohort('quality-inputs',{'anonymous-inputs':[root]});print(root)
