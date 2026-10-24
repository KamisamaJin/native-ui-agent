#!/usr/bin/env python3
"""Index original unsuccessful/unknown records without changing their verdicts."""
import argparse
import study as s
R=s.R

def build():
 s.gate.authorize(R/'gates','reveal',R)
 result=[]
 for folder in ['corpora','feedback']:
  for path in sorted((R/folder).rglob('*.json')):
   if '__pycache__'in path.parts:continue
   name=path.name
   if name not in{'wrapper-failure.json','result.json','automatic.json'}:continue
   value=s.read(path)
   if name=='automatic.json':
    rows=[{'id':r['id'],'status':r['status'],'reason':r.get('reason')}for r in value['assertions']if r['status']in{'failed','unassessed'}]
    if rows:result.append({'kind':'original-automatic-rows','path':str(path.relative_to(R)),'sha256':s.sha(path),'rows':rows})
   elif name=='wrapper-failure.json'or value.get('status')not in{'verified_capture','captured_partial'}:
    result.append({'kind':'native-request-failure','path':str(path.relative_to(R)),'sha256':s.sha(path),'status':value.get('status'),'error':value.get('error')})
 for folder in ['evaluation','source-self']:
  for path in sorted((R/folder).rglob('*.json')):
   if path.name not in{'acceptance.json','report.json'}:continue
   value=s.read(path);rows=value.get('rows',[])
   bad=[{'id':r['id'],'status':r['status'],'cause':r.get('cause_category'),'reason':r.get('reason')}for r in rows if r['status']in{'failed','unassessed'}]
   if bad:result.append({'kind':folder,'path':str(path.relative_to(R)),'sha256':s.sha(path),'rows':bad})
 for folder in ['self-final','self-complete']:
  for path in sorted((R/folder).rglob('endpoint.json')):
   value=s.read(path)
   if not value['accepted']:result.append({'kind':'self-gate-blocked','path':str(path.relative_to(R)),'sha256':s.sha(path),'original':value})
 for path in sorted((R/'source-api').rglob('record.json')):
  value=s.read(path)
  if value['status']!='source_api_typechecked':result.append({'kind':'minimum-api-check','path':str(path.relative_to(R)),'sha256':s.sha(path),'original':value})
 return {'records':result,'engineeringEvidence':{'index':'ENGINEERING.md','development':'development/','designProposals':'design-proposals/','neutralReviews':'neutral-review/','sourceControls':['source-neutral-forward/','source-neutral-cli-check/','source-neutral-minimum-api/']},'scope':'Index only; original records/seals are authoritative. F/U rows may share one cause, are not independent defect counts. Failed compile/operator attempts remain in initial/final agent outputs and original logs; no UI failure is repaired by this report.'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=build();path=R/'failure-index.json'
 if a.check:assert s.read(path)==value
 else:s.save(path,value)
 print('PASS original failures and unknowns indexed')
