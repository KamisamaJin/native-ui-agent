from pathlib import Path
import hashlib, json, os, subprocess, sys, time
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
ORIGINAL=ROOT/'validation/feedback-forward/source-neutral-forward'
OUT=ROOT/'validation/feedback-forward/source-neutral-cli-check'
TOOL=ROOT/'tools/implementation_audit.py'
START=time.time()

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:f.write(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def snapshot():
    seal=load(ORIGINAL/'SEAL.json')
    files={str(p.relative_to(ORIGINAL)):sha(p) for p in sorted(ORIGINAL.rglob('*')) if p.is_file()}
    mismatches={rel:{'expected':expected,'actual':files.get(rel)} for rel,expected in seal['files'].items() if files.get(rel)!=expected}
    return {'capturedAtUnix':time.time(),'sealByteSha256':sha(ORIGINAL/'SEAL.json'),'fileCount':len(files),'files':files,'symlinks':{str(p.relative_to(ORIGINAL)):os.readlink(p) for p in ORIGINAL.rglob('*') if p.is_symlink()},'originalSealMismatches':mismatches}
def run(label,args):
    t=time.time();p=subprocess.run([str(v) for v in args],cwd=ROOT,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    rec={'label':label,'startedAtUnix':t,'endedAtUnix':time.time(),'cwd':str(ROOT),'argv':[str(v) for v in args],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    write(OUT/'commands'/f'{label}.json',rec)
    return rec
before=snapshot();assert not before['originalSealMismatches']
write(OUT/'original-before.json',before)
tool_before=sha(TOOL)
write(OUT/'tool-identity.json',{'recordedAtUnix':time.time(),'path':str(TOOL),'byteSha256':tool_before,'bytes':TOOL.stat().st_size,'priorToolByteSha256':load(ORIGINAL/'read-inputs.json')['files']['tools/implementation_audit.py']['sha256'],'note':'Current shared tool identity. Only the actual CLI is exercised; no tool or fixture edits.'})
pin=load(ORIGINAL/'independent-pin.json')
common=['--design-lock',ORIGINAL/'fixture/design/lock.json','--design-sha256',pin['lockCanonicalSha256'],'--policy',ORIGINAL/'fixture/design/implementation-audit.json','--policy-sha256',pin['policyCanonicalSha256'],'--source-root',ORIGINAL/'fixture/source','--design-root',ORIGINAL/'fixture/design']
records=[]
records.append(run('01-honest-catalog',[sys.executable,TOOL,'catalog']+common+['--output',OUT/'catalog.json']))
records.append(run('02-honest-bind',[sys.executable,TOOL,'bind']+common+['--submission',ORIGINAL/'honest-submission.json','--output',OUT/'honest-gate.json']))
records.append(run('03-missing-submission',[sys.executable,TOOL,'bind']+common+['--output',OUT/'missing-submission-gate.json']))
records.append(run('04-all-unknown-bind',[sys.executable,TOOL,'bind']+common+['--submission',ORIGINAL/'cases/023-all-unknown-no-evidence/TEMPORARY-submission.json','--output',OUT/'unknown-gate.json']))
# Inspect payloads explicitly; process return codes are independent observations.
cat=load(OUT/'catalog.json');honest=load(OUT/'honest-gate.json');unknown=load(OUT/'unknown-gate.json')
checks={'catalogMatchesOriginal':cat==load(ORIGINAL/'catalog.json'),'catalogCanonicalShaMatchesOriginalSubmission':digest(cat)==load(ORIGINAL/'honest-submission.json')['catalog_sha256'],'honestGateMatchesOriginal':honest==load(ORIGINAL/'honest-gate.json'),'honestPayloadIsBlockedWith6Passed1Unknown':honest['status']=='not_accepted' and honest['counts']=={'passed':6,'failed':0,'unassessed':1} and honest['blocking_obligations']==['formatter-localization'],'unknownGateMatchesOriginal':unknown==load(ORIGINAL/'cases/023-all-unknown-no-evidence/gate.json'),'unknownPayloadIsBlockedWith7Unknown':unknown['status']=='not_accepted' and unknown['counts']=={'passed':0,'failed':0,'unassessed':7} and len(unknown['blocking_obligations'])==7,'catalogExitZero':records[0]['returncode']==0,'honestBlockedExitNonzero':records[1]['returncode']!=0,'unknownBlockedExitNonzero':records[3]['returncode']!=0,'missingSubmissionExitNonzero':records[2]['returncode']!=0,'missingSubmissionNoOutput':not (OUT/'missing-submission-gate.json').exists(),'missingSubmissionNoTraceback':'Traceback' not in records[2]['stderr'],'currentToolUnchangedDuringPass':sha(TOOL)==tool_before}
after=snapshot();write(OUT/'original-after.json',after)
checks['originalFilesExactlyUnchanged']=before['files']==after['files'] and before['symlinks']==after['symlinks'] and not after['originalSealMismatches']
write(OUT/'results.json',{'startedAtUnix':START,'finishedAtUnix':time.time(),'sourceToolByteSha256':tool_before,'python':sys.version,'checks':checks,'commands':[{k:r[k] for k in ['label','argv','returncode','stdout','stderr']} for r in records],'honestPayload':{k:honest[k] for k in ['status','counts','blocking_obligations']},'unknownPayload':{k:unknown[k] for k in ['status','counts','blocking_obligations']},'priorDishonestReviewLimitation':'Unchanged documented reviewer-truth limitation; not retested in this CLI-only regression.'})
report=f'''# CLI regression against the sealed neutral fixture

All {len(checks)} recorded checks passed: {all(checks.values())}. No original fixture, proposition, expected value, submission, or source was changed. Original folder inventory, every file SHA (including its seal), retained symlink identity, and the original seal map were checked before and after and remained exactly unchanged.

| Invocation | Exit | JSON inspection |
| --- | --- | --- |
| Honest source catalog | {records[0]['returncode']} | Exactly equal to the original catalog |
| Honest bind | {records[1]['returncode']} | `not_accepted`; 6 passed, 0 failed, 1 unknown; formatter-localization blocks |
| Bind without submission | {records[2]['returncode']} | No output created; concise usage error, no traceback |
| Existing all-unknown submission | {records[3]['returncode']} | `not_accepted`; 0 passed, 0 failed, 7 unknown; all seven block |

The two blocked commands wrote their gate JSON and exited nonzero. Their payloads exactly match the sealed earlier gates. This confirms the revised CLI boundary without inferring semantics from process exit alone. The missing-submission stderr is preserved verbatim in `commands/03-missing-submission.json` and `results.json`.

The current shared tool byte SHA256 is `{tool_before}`. `tool-identity.json` also records the earlier tool SHA and the current size/time. Exact argv, cwd, Unix start/end times, stdout, stderr and exit codes are in `commands/`. `run_cli_regression.py` preserves the controller source. No SDK, device, business design, product implementation, source edits, subagents, commits, or agent-message tools were used.

The earlier dishonest-review limitation remains documented in the sealed original report and was not retested or reinterpreted. These CLI changes provide no additional source-semantic, rendered-style, or native-runtime proof. This follow-up observed no additional CLI error in the requested invocations.

`SEAL.json` is written last and hashes every other readable file in this new folder. Its own bytes are necessarily excluded. `controller-record.json` preserves the controller invocation and its complete stdout/stderr.
'''
(OUT/'REPORT.md').write_text(report)
assert all(checks.values()),checks
# Record deterministic controller stdout before creating the final seal.
count=len([p for p in OUT.rglob('*') if p.is_file() and p.name!='SEAL.json'])+1
msg=json.dumps({'allChecksPassed':True,'checkCount':len(checks),'exitCodes':{r['label']:r['returncode'] for r in records},'sealedFileCount':count,'originalUnchanged':checks['originalFilesExactlyUnchanged'],'toolByteSha256':tool_before})+'\n'
write(OUT/'controller-record.json',{'argv':[sys.executable,str(OUT/'run_cli_regression.py')],'cwd':str(ROOT),'startedAtUnix':START,'endedAtUnix':time.time(),'returncode':0,'stdout':msg,'stderr':''})
files={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SEAL.json'}
assert len(files)==count
write(OUT/'SEAL.json',{'sealedAtUnix':time.time(),'files':files})
assert all(sha(OUT/rel)==expected for rel,expected in files.items())
print(msg,end='')
