from pathlib import Path
import copy, hashlib, json, os, platform, subprocess, sys, time
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill'); OUT=ROOT/'validation/feedback-forward/source-neutral-forward'
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:f.write(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def run(label,args):
    t=time.time();p=subprocess.run([str(v) for v in args],cwd=ROOT,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    write(OUT/'commands'/f'{label}.json',{'label':label,'startedAtUnix':t,'endedAtUnix':time.time(),'cwd':str(ROOT),'argv':[str(v) for v in args],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    print(json.dumps({'label':label,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
    return p
pin=load(OUT/'independent-pin.json'); original_cat=load(OUT/'catalog.json'); temp_cat=load(OUT/'cases/030-unsupported-review/TEMPORARY-catalog.json')
truthful=copy.deepcopy(load(OUT/'honest-submission.json'));truthful['catalog_sha256']=digest(temp_cat)
for row,item in zip(temp_cat['rows'],truthful['decisions']):
    for ref in item['evidence']:ref['sha256']=temp_cat['files'][ref['file']]['sha256']
truthful['decisions'][0]['actual']=False
truthful['decisions'][0]['reason']='TEMPORARY changed-source boundary case: the getter now returns raw count, so count = -1 is a direct counterexample to the fixed clamp proposition.'
write(OUT/'cases/033-truthful-changed-source/TEMPORARY-submission.json',truthful)
common=['--design-lock',OUT/'fixture/design/lock.json','--design-sha256',pin['lockCanonicalSha256'],'--policy',OUT/'fixture/design/implementation-audit.json','--policy-sha256',pin['policyCanonicalSha256'],'--source-root',OUT/'cases/024-changed-source/TEMPORARY-source','--design-root',OUT/'fixture/design']
run('033-truthful-changed-source',[sys.executable,ROOT/'tools/implementation_audit.py','bind']+common+['--submission',OUT/'cases/033-truthful-changed-source/TEMPORARY-submission.json','--output',OUT/'cases/033-truthful-changed-source/gate.json'])
# Evidence and process integrity before the final seal.
honest=load(OUT/'honest-gate.json');defs=load(OUT/'definitions.json');failgate=load(OUT/'cases/033-truthful-changed-source/gate.json')
assert honest['counts']=={'passed':6,'failed':0,'unassessed':1} and honest['blocking_obligations']==['formatter-localization']
assert failgate['counts']=={'passed':5,'failed':1,'unassessed':1} and failgate['status']=='not_accepted'
assert defs['mode']=='definition_only' and all(all(x is None for x in f.values()) for f in defs['files'].values())
assert load(OUT/'planning.json')['fixedAtUnix'] < pin['pinnedAtUnix'] < load(OUT/'fixture-fixed.json')['fixedAtUnix']
inputs=load(OUT/'read-inputs.json')
original_unchanged={rel:sha(ROOT/rel)==entry['sha256'] for rel,entry in inputs['files'].items()}
assert all(original_unchanged.values())
original_source_unchanged={name:sha(OUT/'fixture/source'/name)==desc['sha256'] for name,desc in original_cat['files'].items()}
assert all(original_source_unchanged.values())
symlinks={str(p.relative_to(OUT)):os.readlink(p) for p in OUT.rglob('*') if p.is_symlink()}
write(OUT/'symlink-records.json',{'recordedAtUnix':time.time(),'symlinks':symlinks,'sealInterpretation':'The file map hashes readable file content, including this symlink to a file inside the assigned output folder. Symlink target identity is recorded separately here.'})
command_files=sorted(list(OUT.glob('command-*.json'))+list((OUT/'commands').glob('*.json')))
command_records=[load(p) for p in command_files]
write(OUT/'results.json',{'recordedAtUnix':time.time(),'python':sys.version,'platform':platform.platform(),'inputFilesUnchanged':original_unchanged,'originalSourceUnchanged':original_source_unchanged,'honestGate':{k:honest[k] for k in ['status','counts','blocking_obligations']},'temporaryTruthfulFailureGate':{k:failgate[k] for k in ['status','counts','blocking_obligations']},'temporaryDishonestGate':{k:load(OUT/'cases/030b-unsupported-review-acceptance/gate.json')[k] for k in ['status','counts','blocking_obligations']},'commandRecordCountBeforeFinalization':len(command_records),'commandRecords':[str(p.relative_to(OUT)) for p in command_files],'sourceEvidenceDescriptors':original_cat['files'],'definitionCatalogSha256':digest(defs),'actualCatalogSha256':digest(original_cat),'toolByteSha256':inputs['files']['tools/implementation_audit.py']['sha256'],'apiResults':load(OUT/'api-results.json')})
lines=[
'# Independent neutral source-only forward test',
'',
'The honest result is `not_accepted`: 6 passed, 0 failed, 1 unassessed. The sole blocker is `formatter-localization`. This is a source-review result for an original neutral fixture; it is not a rendered, native-runtime, compiler, AST, or product acceptance result.',
'',
'## Scope and independence',
'',
'I read the shared audit tool, its SOURCE-AUDIT documentation, the frozen candidate-v9 design_contract script, and the frozen generic atomic-example contract/reference. Resource discovery listed filenames only. I did not inspect business designs, prior review/study content, live product workspaces, assignments, or intended outcomes. No SDK, device, product source edits, subagents, commits, or messages to other agents were used. All authored artifacts are inside this folder. Tool execution imports its actual transitive design_contract module; that live module was executed but not manually read or modified. The frozen design-contract CLI also executes its observation_contract import.',
'',
'The independent typed source, design contract, seven atomic source propositions and Boolean expectations were authored and pinned before the two neutral model files existed. `planning.json`, `independent-pin.json`, and command 006 establish this order. `definitions.json` contains null source SHA/size/line descriptors. `catalog.json` is the later source-bound catalog. The generic design-lock schema requires one native rule/state scaffold; it was never observed or used as native evidence. This local synthetic approval makes no authorship or approval claim about a real design.',
'',
'## Honest judgments',
'',
'| Obligation | Actual | Gate status | Original source range |',
'| --- | --- | --- | --- |',
'| Swift clamp | true | passed | BadgeModel.swift:10 |',
'| Swift delegation | true | passed | BadgeModel.swift:11 |',
'| Kotlin clamp | true | passed | BadgeModel.kt:10 |',
'| Kotlin delegation | true | passed | BadgeModel.kt:11 |',
'| Kotlin in-body empty fallback exists | false | passed (expected false) | BadgeModel.kt:11 |',
'| Shared source identifier | true | passed | BadgeModel.swift:8; BadgeModel.kt:6–8 |',
'| Configured formatter localization | unknown | unassessed; must blocker | Interfaces/injection only: Swift:1–7; Kotlin:1–5 |',
'',
'The exact original hashes, byte counts and line counts are in `catalog.json` and `results.json`; `honest-submission.json` attaches the original file SHA and intervals to every known judgment. The model files show getters and constants. They do not supply formatter implementations, wiring, resources, active production integration, or any UI. The unknown is preserved because the localization obligation cannot be resolved from the declared scope.',
'',
'## Integrity results',
'',
'- Direct API catalog and bind output exactly equal the CLI artifacts. The API rejects binding definition-only planning as actual acceptance.',
'- The CLI rejected attempted expected/status/unit additions, a mismatching catalog digest, wrong evidence SHA, zero/out-of-bounds intervals, omitted required file evidence, undeclared evidence files, foreign review IDs, integer actuals, duplicate decisions, changed source bytes, a source symlink escaping its declared root, a changed pinned lock, and a changed pinned policy. Commands 010–021 and 024–027 preserve the full errors.',
'- Omitting one known decision produced 5 passed / 2 unassessed and blocked both obligations. Explicitly submitting every actual as null with no evidence produced 7 unassessed and blocked all seven. Unknown remains distinct from false.',
'- In a marked temporary copy only, the Swift clamp was replaced with raw count. Reusing the original submission was rejected because the recomputed catalog digest changed. A fresh catalog plus an honest false judgment produced 5 passed / 1 failed / 1 unassessed and remained not accepted (command 033).',
'- Existing output protection rejected an overwrite without changing the original catalog (command 029).',
'',
'## False acceptance and evidence limit',
'',
'Command 030b records an evidentiary false acceptance: a deliberately dishonest temporary submission asserted every expected Boolean, citing valid original hashes but unrelated line 1 intervals. It used the temporary source where the clamp was absent and asserted that clamp as true; it also asserted the unresolved localization requirement. The tool returned `accepted`, 7 passed. This is a demonstrated semantic trust boundary, not a hash or source-mutation bypass: the CLI had recomputed the temporary catalog correctly and the reviewer then lied about its meaning. The tool and docs describe reviewer judgment rather than AST/transitive proof. Valid hashes and in-range references cannot establish that a proposition is true, that cited lines support it, or that the reviewed files are integrated production code. Independent honest review is still required. None of these temporary cases alters the honest result.',
'',
'## Actual usability/tool issues',
'',
'- `bind` without `--submission` is accepted by argument parsing and then crashes with `AttributeError: NoneType ... read_text` instead of a conditional usage error (command 028).',
'- A successfully computed `not_accepted` gate exits 0, and the successful definitions/catalog/bind commands emit no stdout summary. Consumers must inspect the JSON status and blockers; process success is not gate acceptance. Validation failures print full Python tracebacks. These are workflow characteristics, not successful evidence judgments.',
'- My first documentation read used an incorrect `docs/validation/...` prefix and failed. Command 001 preserves that operator path error. Command 002 uses the supplied `validation/feedback-forward/SOURCE-AUDIT.md` successfully. This was not a tool defect.',
'',
'## Reproducibility and seal',
'',
'`run_forward.py`, `run_boundaries.py`, `api_probe.py`, and `finish_forward.py` preserve the executed test/controller source. They intentionally require fresh artifacts rather than overwriting this record. Each subprocess record contains exact argv, cwd where applicable, Unix start/end times, exit status, stdout, and stderr. Discovery/read records are `command-001.json` through `command-004.json`; subsequent invocations are in `commands/`. File SHA records and timing are in `read-inputs.json`, `independent-pin.json`, `fixture-fixed.json`, `results.json`, and the finalization record. The initial tool/docs/frozen resources and original source fixture were checked unchanged at completion.',
'',
'`SEAL.json` is written last with `{sealedAtUnix, files:{relative:SHA256}}`; it hashes every other readable file under this output folder. A seal cannot include its own SHA. The retained temporary symlink points only inside this folder; `symlink-records.json` preserves its target and the seal hashes its readable file content. No assertions about other workspaces or outcomes follow from this test.',
'']
(OUT/'REPORT.md').write_text('\n'.join(lines))
# Preserve finalization operations before computing the final file map.
msg='Final checks passed. SEAL.json written last; no output file is modified after sealing.\n'
write(OUT/'finalization-record.json',{'startedAtUnix':time.time(),'argv':[sys.executable,str(OUT/'finish_forward.py')],'cwd':str(ROOT),'returncode':0,'stdout':msg,'stderr':'','checks':{'honestCountsAndBlocker':True,'truthfulTemporaryFailureCounts':True,'definitionsHaveNoSourceIdentity':True,'planningAndPinPrecedeSource':True,'inputResourcesUnchanged':all(original_unchanged.values()),'originalFixtureUnchanged':all(original_source_unchanged.values())},'sealSelfExclusion':'SEAL.json is excluded because a file cannot contain its own SHA256; all other readable output files are included.'})
files={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SEAL.json'}
seal={'sealedAtUnix':time.time(),'files':files}
write(OUT/'SEAL.json',seal)
assert all(sha(OUT/rel)==h for rel,h in seal['files'].items())
print(msg,end='')
print(json.dumps({'sealedFileCount':len(files),'sealByteSha256':sha(OUT/'SEAL.json'),'honestStatus':honest['status'],'honestCounts':honest['counts']}))
