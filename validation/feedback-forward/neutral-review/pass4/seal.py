from pathlib import Path
import json,hashlib,time,shlex,sys
out=Path(__file__).resolve().parent
started=time.time()
load=lambda p:json.loads(p.read_text())
before=load(out/'input-shas.json')['files']
changed=[key for key,v in before.items() if hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()!=v['sha256']]
if changed:raise RuntimeError('Original inputs changed: '+repr(changed))
review_end=time.time()
start=load(out/'START.json')['startedAtUnix']
end={'endedAtUnix':review_end,'endedAtUtc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(review_end)),'startedAtUnix':start,'reviewWallSeconds':review_end-start,'reviewWallScope':'Includes agent reading/reasoning, tool operations and evidence packaging; no isolated model compute or queue timing is claimed.','nativeExecutionPerformedByReviewer':False,'sourceOrExpectationEditsPerformed':False,'originalInputFileCountRechecked':len(before),'allOriginalInputsUnchanged':True,'release':'not_accepted','nativeOriginalTiming':{'startedAtUnix':1792851852.161227,'nativeFinishedAtUnix':1792851898.346504,'finishedAtUnix':1792851898.365859,'reportedNestedSeconds':{'boot_seconds':0.25974549999999996,'build_or_validate_seconds':7.031751375,'native_test_command_seconds':38.679963791,'export_seconds':0.042859333999999194},'scope':'Original permitted producer record only; no SDK/device command executed in this review.'}}
(out/'END.json').write_text(json.dumps(end,indent=2)+'\n')
label='seal'
record={'label':label,'argv':['python3','-B',str(out/'seal.py')],'command':shlex.join(['python3','-B',str(out/'seal.py')]),'startedAtUnix':started,'endedAtUnix':time.time(),'exit_code':0,'stdout':'All original inputs unchanged; output seal written.\n','stderr':'','scope':'Actual self-recording sealing command. Final transport result remains in the conversation; SEAL.json excludes itself to avoid a circular hash.'}
record['elapsedSeconds']=record['endedAtUnix']-record['startedAtUnix']
(out/'commands/seal.json').write_text(json.dumps(record,indent=2)+'\n')
(out/'commands/seal.stdout.txt').write_text(record['stdout'])
(out/'commands/seal.stderr.txt').write_text('')
rows=[]
for p in sorted((out/'commands').glob('*.json')):
 x=load(p);rows.append({'label':x['label'],'exit_code':x['exit_code'],'startedAtUnix':x['startedAtUnix'],'endedAtUnix':x['endedAtUnix'],'elapsedSeconds':x['elapsedSeconds'],'record':str(p.relative_to(out))})
rows.sort(key=lambda x:x['startedAtUnix'])
(out/'commands-index.json').write_text(json.dumps(rows,indent=2)+'\n')
md='Every runner entry retains full actual subprocess argv, stdout, stderr, start/end Unix timestamps and real child exit code. The Python logging runner returns 0 even when its child fails; inspect the recorded child exit_code. Marked negative integrity controls are not product evidence. Early reconstructed readout records and missing raw transport limits are explicitly labeled in reconstructed-initial/ and REVIEW.md.\n\n| Actual command label | Child exit | Seconds | Record |\n| --- | ---: | ---: | --- |\n'
for r in rows:md+='| '+r['label']+' | '+str(r['exit_code'])+' | '+str(round(r['elapsedSeconds'],6))+' | '+r['record']+' |\n'
(out/'COMMANDS.md').write_text(md)
files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SEAL.json'}
seal={'sealedAtUnix':time.time(),'files':files}
(out/'SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
# Read-only verification after sealing does not create any new output artifact.
assert all(hashlib.sha256((out/rel).read_bytes()).hexdigest()==sha for rel,sha in files.items())
print(record['stdout'],end='')
print(json.dumps({'sealed_file_count':len(files),'sealedAtUnix':seal['sealedAtUnix'],'release':end['release'],'reviewWallSeconds':end['reviewWallSeconds'],'seal_sha256':hashlib.sha256((out/'SEAL.json').read_bytes()).hexdigest()},indent=2))
