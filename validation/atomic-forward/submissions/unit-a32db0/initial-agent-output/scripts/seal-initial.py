import pathlib,json,hashlib,time,datetime,shutil,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
out=root/'agent-output'
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p): return {'path':str(p.relative_to(root)),'sha256':h(p),'bytes':p.stat().st_size}
for platform in ['ios','android']:
 for attempt in [1,2]:
  cache=root/f'cache/compile-{platform}-{attempt}'
  for name in ['build.log','record.json']:
   dest=out/f'build-records/{platform}-{attempt}-{name}'; dest.parent.mkdir(exist_ok=True)
   shutil.copyfile(cache/name,dest)
failed=[
 {'kind':'inspection_command','command':"rg --files -g AGENTS.md -g SKILL.md -g BRIEF.md -g API.md -g policy.json -g bindings.json -g approval.json -g contract.json -g reference.json .",'cwd':str(root),'exitCode':1,'reason':'No matching files in fresh workspace. No implementation or compiler failure.','exactTimeAvailable':False,'timeRangeUnix':[1792634246.0,1792634375.1015658]},
 {'kind':'tool_orchestration_parse','tool':'functions.exec','executionStarted':False,'error':'SyntaxError: missing ) after argument list','reason':'JavaScript wrapper failed before invoking any command. Same intended edit and compile invocation were corrected and executed next.','exactTimeAvailable':False,'timeRangeUnix':[1792634455.123023,1792634545.1838531]}
]
(out/'failed-attempts.json').write_text(json.dumps(failed,indent=2)+'\n')
(out/'logs/orchestration-parse-failure.log').write_text('Script failed\nWall time 0.0 seconds\nScript error:\nSyntaxError: missing ) after argument list\nNo nested commands ran.\n')
source_paths=[root/'alerttoast/Sources/AlertToast/RiverSensorTriageBoard.swift',root/'reply/Reply/app/src/main/java/com/example/reply/ui/components/RiverSensorTriageBoard.kt']
source_files=[]
for p in source_paths:
 dest=out/'source-snapshot'/p.relative_to(root); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,dest)
 source_files.append(record(p))
plans=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  directory=out/f'plans/{case}/{platform}'
  plan=json.loads((directory/'plan.json').read_text())
  plans.append({'case':case,'platform':platform,'plan':str((directory/'plan.json').relative_to(root)),'actions':str((directory/'actions.json').relative_to(root)),'assertions':len(plan['assertions']),'states':len(plan['states']),'selectedCells':98})
plan_artifacts=sorted((out/'plans').rglob('*.json'))+sorted((out/'scripts').glob('*.py'))
seal={'version':1,'phase':'initial','sealedAtUnix':time.time(),'designLockSHA256':'c21f3c012a188c7c39e8017dc92e8749b821a74aa3ad84d007732cfffa48e000','generatedBy':'Assigned frozen scripts/design_contract.py compile; no generated expectations, routes, units, tolerances, coverage or precision edited','files':[record(p) for p in plan_artifacts]}
(out/'plans-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
settings=[root/'alerttoast/Package.swift',root/'reply/Reply/app/build.gradle.kts',root/'reply/Reply/gradle/libs.versions.toml',root/'reply/Reply/gradle/wrapper/gradle-wrapper.properties']
commands=json.loads((out/'plan-commands.json').read_text())
commands += [json.loads(p.read_text()) for p in sorted(out.glob('compile-*-command.json'))]
start=json.loads((out/'phase-start.json').read_text())
finish=time.time()
implementation={
 'version':1,'phase':'initial','status':'implemented_and_compile_only_passed','workspace':str(root),
 'startedAtUnix':start['startedAtUnix'],'startedAtUtc':start['startedAtUtc'],
 'finishedAtUnix':finish,'finishedAtUtc':datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat(),
 'elapsedWallSeconds':finish-start['startedAtUnix'],'budgetWallSeconds':1500,
 'changed_files':[str(p.relative_to(root)) for p in source_paths], 'productionArtifacts':source_files,
 'sourceSnapshots':[record(p) for p in sorted((out/'source-snapshot').rglob('*')) if p.is_file()],
 'buildSettings':{'changedByAgent':False,'note':'Package.swift and Reply/app/build.gradle.kts already include pinned SnapshotTesting/Paparazzi setup; upstream git status lists those preexisting modifications. Agent wrote only the two production files and evidence/scripts/cache inside this workspace.','hashes':[record(p) for p in settings]},
 'implementationNotes':[
  'Public Codable SwiftUI models and memberwise initializers; public Compose data classes and component API.',
  'Eager six-entry chronological timeline. Item time, label, uppercase severity, literal Unavailable and caller reason share each native selection control; noninteractive mirrored leading rail.',
  'Revision-keyed native component state, valid available incoming selection, idempotent reselect callback, disabled unavailable controls, disclosure guidance or inline selected dossier, summary, conditional primary action and stable draft after submission.',
  'Light/dark source palette, native scalable typography, naturally wrapping full-height text, minimum 56 native-unit primary/card controls, 16-unit internal padding and continuous canvas gutter.',
  'Static reference review extended each timeline rail through the following 12-unit gap; both platforms recompiled after this edit.'
 ],
 'commands':commands,'failedAttempts':'agent-output/failed-attempts.json',
 'plans':plans,'plansSeal':'agent-output/plans-seal.json','plansSealSHA256':h(out/'plans-seal.json'),
 'compilerSource':{'path':'/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/candidate-v8/scripts/design_contract.py','sha256':h(pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/candidate-v8/scripts/design_contract.py'))},
 'logs':[str(p.relative_to(root)) for p in sorted((out/'logs').glob('*'))]+[str(p.relative_to(root)) for p in sorted((out/'build-records').glob('*'))],
 'limits':[
  'No App launch, preview, native observer, screenshot capture, SDK rendering, runtime interaction or rendered feedback in this phase.',
  'Compile-only success establishes compilation only; visual acceptance and native control/callback behavior remain unassessed.',
  'All generated plan cells retained; unsupported iOS computed title typography remains unsupported and no numerical claim is made from source.',
  'No commits, pushes, agents, reference/contract/bridge/compiler edits, unrelated UI changes or build-setting edits.',
  'Only assigned frozen Skill, public independent T2 inputs, own workspace project sources and explicit compile-only helper were accessed; public compiled/validation-log contents were not read.',
  'Initial read-only inspection commands preceded timed command wrappers; their exact individual wall times were not instrumented. First action clock and all compiler/build invocation times are recorded without inferred precision.',
  'Stopped after initial source and original plan sealing. Await explicit root authorization after full cohort initial sealing.'
 ]}
(out/'implementation.json').write_text(json.dumps(implementation,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'finishedAtUnix':finish,'elapsedWallSeconds':implementation['elapsedWallSeconds'],'productionArtifacts':source_files,'plansSealSHA256':h(out/'plans-seal.json'),'implementationSHA256':h(out/'implementation.json')},indent=2))
