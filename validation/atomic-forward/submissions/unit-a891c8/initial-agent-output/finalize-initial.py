from pathlib import Path
import datetime, hashlib, json, shutil, time
w=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-a891c8')
o=w/'agent-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
source_paths=[w/'alerttoast/Sources/AlertToast/RiverSensorTriageBoard.swift',w/'reply/Reply/app/src/main/java/com/example/reply/ui/components/RiverSensorTriageBoard.kt']
for platform,path in zip(['ios','android'],source_paths):
 dest=o/'initial-source'/platform/path.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
plan_files=sorted((o/'plans').rglob('*'))
plan_files=[p for p in plan_files if p.is_file()]
scripts=sorted(o.glob('*.py'))
artifacts=plan_files+scripts+[o/'approved-lock.json',o/'public-inputs.json']
write(o/'plans-seal.json',{'version':1,'phase':'initial','sealedAtUnix':time.time(),'approvedLockSha256':'c21f3c012a188c7c39e8017dc92e8749b821a74aa3ad84d007732cfffa48e000','originalUneditedGeneratedArtifacts':True,'files':[{'path':str(p.relative_to(w)),'sha256':sha(p),'bytes':p.stat().st_size} for p in artifacts]})
records=[json.loads(line) for line in (o/'commands.jsonl').read_text().splitlines() if line.strip()]
failures=[r for r in records if r['returncode']!=0]
write(o/'failed-attempts.json',{'version':1,'failedAttempts':failures,'notes':'No plan/compiler or build failures occurred. Read-only shell inspections also returned zero; tool output truncation prompted narrower reads, not discarded checks.'})
write(o/'inspection-record.json',{
 'version':1,'method':'Read-only filesystem inspection and independent supplied reference image viewing',
 'prompt':'/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/prompts/unit-a891c8-initial.txt',
 'skill':'/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/baseline-v7/SKILL.md',
 'skill_references':['platforms.md','design-contract.md','native-precision.md','state-evidence.md','coverage.md'],
 'public_inputs':'public-inputs.json',
 'project_instructions':'No AGENTS.md found in the workspace, ancestor chain, AlertToast project or Reply project.',
 'project_inspections':['bootstrap.json','alerttoast/Package.swift','alerttoast/Sources/AlertToast/AlertToast.swift','reply/Reply/app/build.gradle.kts','reply/Reply/app/src/main/java/com/example/reply/ui/theme/Theme.kt','git status --short in own two repositories'],
 'notes':['The initial public filename inventory also listed excluded compiled/validation-logs paths. Their contents were never read or used. Subsequent reads were explicitly limited to approved public files and cases.','Existing bootstrap modifications in Package.swift, Reply/app/build.gradle.kts and Reply/.native-ui were not changed by this implementation.','Some bulk inspection outputs were truncated by the tool; narrower reads and structured summaries followed.'],
 'per_command_inspection_timestamps':'Not separately recorded; the tool transcript is authoritative. Compilation and plan-generation argv/times/results are recorded in commands.jsonl.'})
finished=time.time()
write(o/'implementation.json',{
 'version':1,'phase':'initial','status':'implemented_compile_only_passed',
 'startedAtUnix':1792634255,'startedAtUtc':'2026-10-22T01:57:35Z',
 'finishedAtUnix':finished,'finishedAtUtc':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat(),
 'wallSeconds':finished-1792634255,'budgetSeconds':1500,
 'changed_files':[str(p.relative_to(w)) for p in source_paths],
 'source_files':[{'path':str(p.relative_to(w)),'sha256':sha(p)} for p in source_paths],
 'commands':'agent-output/commands.jsonl','inspection_record':'agent-output/inspection-record.json',
 'logs':[str(p.relative_to(w)) for p in sorted((o/'logs').iterdir()) if p.is_file()],
 'plan_paths':[{'case':case,'platform':platform,'plan':f'agent-output/plans/{case}/{platform}/plan.json','actions':f'agent-output/plans/{case}/{platform}/actions.json','cells':98,'assertions':81} for case in ['P1','P2'] for platform in ['ios','android']],
 'plans_seal':'agent-output/plans-seal.json','failures':'agent-output/failed-attempts.json',
 'build_results':{'ios':'compile-only exit 0; build-for-testing succeeded','android':'compile-only exit 0; compileDebugKotlin succeeded'},
 'implementation_notes':['Public production API, Codable Swift models, revision-keyed state, exact callbacks, disabled choices, selected semantics, disclosure guidance and inline selected dossier implemented in production components.','Component owns canvas and palettes, eager timeline, natural wrapping, native font scaling, direction-aware leading rail, minimum control heights and public semantic identifiers.','Explicit brief values take precedence over approximate SVG text metrics; supporting text uses 14 base native units.'],
 'limits':['No App launch, observer, preview, screenshot, runtime action dispatch or SDK rendering was performed.','Successful compilation does not verify runtime callback behavior, native geometry, color sampling, complete wrapping or overlap.','All generated assertions and original stimulus routes are retained unchanged, including unsupported iOS native title-weight measurement.','Visual and runtime evidence remains unassessed until root explicitly resumes after the full initial cohort seal.'],
 'stop_state':'Initial work complete; no further repairs or rendering authorized until explicit root resume.'})
print(json.dumps({'finishedAtUtc':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat(),'wallSeconds':finished-1792634255,'planArtifacts':len(plan_files),'sealedScripts':len(scripts),'sources':[{'path':str(p.relative_to(w)),'sha256':sha(p)} for p in source_paths]},indent=2))
