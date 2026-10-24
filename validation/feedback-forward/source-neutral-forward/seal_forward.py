from pathlib import Path
import hashlib, json, sys, time
O=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward/source-neutral-forward')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,v):
    with p.open('x') as f:f.write(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
# Preserve the first seal as an intermediate event and retain the complete controller output.
initial=load(O/'SEAL.json')
initial_sha=sha(O/'SEAL.json')
write(O/'INTERIM-SEAL.json',initial)
old=load(O/'finalization-record.json')
write(O/'interim-finalization-record.json',old)
cmd033=load(O/'commands/033-truthful-changed-source.json')
actual_stdout=json.dumps({k:cmd033[k] for k in ['label','returncode','stdout','stderr']})+'\n'+old['stdout']+json.dumps({'sealedFileCount':len(initial['files']),'sealByteSha256':initial_sha,'honestStatus':'not_accepted','honestCounts':{'passed':6,'failed':0,'unassessed':1}})+'\n'
old['stdout']=actual_stdout
old['stdioCorrection']='The earlier record preserved only its planned summary. This record now preserves the full controller stdout from the first finalization invocation. The intermediate record and seal are retained separately; SEAL.json is the final seal.'
(O/'finalization-record.json').write_text(json.dumps(old,indent=2)+'\n')
# The preceding controllers have deterministic stdout assembled from their preserved child records.
controllers={}
for name,labels in [('run_forward.py',['005-seal-lock','006-definitions-before-source','007-source-catalog','008-read-original-source']),('run_boundaries.py',[p.stem for p in sorted((O/'commands').glob('*.json')) if not p.stem.startswith(('005-','006-','007-','008-','009999','033-'))])]:
    records=[load(O/'commands'/f'{label}.json') for label in labels]
    controllers[name]={'stdout':''.join(json.dumps({k:r[k] for k in ['label','returncode','stdout','stderr']})+'\n' for r in records),'stderr':''}
controllers['finish_forward.py']={'stdout':actual_stdout,'stderr':''}
write(O/'controller-stdio.json',{'recordedAtUnix':time.time(),'controllers':controllers,'note':'CLI/subprocess argv/stdout/stderr and times are preserved independently in commands/. Initial read controllers are recorded in command-001 through command-004.'})
report=O/'REPORT.md'
report.write_text(report.read_text()+'\nThe initial seal was superseded solely to retain complete controller stdout. `INTERIM-SEAL.json` and `interim-finalization-record.json` preserve that intermediate event; `controller-stdio.json` and the corrected finalization record preserve the full outputs. `seal-command.json` records the final sealing invocation. The final `SEAL.json` includes these additional records.\n')
# Save the final command's exact deterministic stdout before hashing, then write SEAL last.
record_path=O/'seal-command.json'
count=len([p for p in O.rglob('*') if p.is_file() and p.name!='SEAL.json'])+1
message=f'Sealed {count} readable output files; verified every SHA.\n'
write(record_path,{'argv':[sys.executable,str(O/'seal_forward.py')],'cwd':'/Users/rex/Documents/ChatGPT/mobile-native-skill','startedAtUnix':time.time(),'returncode':0,'stdout':message,'stderr':'','note':'SEAL.json is written last. Its own bytes are necessarily excluded from its file map.'})
files={str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SEAL.json'}
assert len(files)==count
seal={'sealedAtUnix':time.time(),'files':files}
(O/'SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
assert all(sha(O/k)==v for k,v in files.items())
print(message,end='')
