#!/usr/bin/env python3
"""Complete source AND runtime gate; original intermediate endpoints remain intact."""
import argparse,time
from pathlib import Path
import study as s
R=s.R
import shared_amendment
shared_amendment.verify()
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);a=p.parse_args();w=a.workspace.resolve();unit=w.name;cfg=s.read(R/'private/assignment.json')['units'][unit];assert w==R/'cache'/unit
s.gate.authorize(R/'gates','d0-raw',R);s.tool_verify();s.verify_dir(R/'self-final'/unit)
for phase in ['original','final']:s.verify_dir(R/'source-self'/unit/phase)
final=s.read(R/'submissions'/unit/'final/seal.json')['files'];assert s.fingerprint(w)==final and s.read(R/'source-self'/unit/'final/receipt.json')['source']==final
runtime=s.read(R/'self-final'/unit/'endpoint.json');source=s.read(R/'source-self'/unit/'final/report.json')
import check_minimum_api
api_cache=R/'cache/source-api'/unit/'final'
api=check_minimum_api.run(w,R/'design'/cfg['task']/'public/Bridge.swift',api_cache,'14.0')
api_out=R/'source-api'/unit/'final';api_out.mkdir(parents=True,exist_ok=False)
for path in api_cache.glob('*.log'):s.shutil.copy2(path,api_out/path.name)
s.shutil.copy2(api_cache/'record.json',api_out/'record.json')
s.save(R/'self-complete'/unit/'endpoint.json',{'finishedAtUnix':time.time(),'handoffAtUnix':runtime['handoffAtUnix'],'accepted':runtime['accepted']and source['status']=='accepted'and api['status']=='source_api_typechecked','runtimeAccepted':runtime['accepted'],'sourceAccepted':source['status']=='accepted','runtimeEndpointSHA256':s.sha(R/'self-final'/unit/'endpoint.json'),'sourceReceiptSHA256':s.sha(R/'source-self'/unit/'final/receipt.json'),'sourceCounts':source['counts'],'minimumSourceAPIAccepted':api['status']=='source_api_typechecked','minimumSourceAPIRecordSHA256':s.sha(api_out/'record.json'),'scope':'Complete AI self-verification, source-only judgment AND unchanged native/visual gate; not independent quality gold.'})
s.seal_dir(R/'self-complete'/unit);print(R/'self-complete'/unit/'endpoint.json')
