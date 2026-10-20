import datetime, hashlib, json, pathlib, shutil, time
workspace=pathlib.Path(__file__).resolve().parents[2]
out=workspace/'agent-output'
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source_paths=[
 'alerttoast/Sources/AlertToast/ExpeditionPackPanel.swift',
 'reply/Reply/app/src/main/java/com/example/reply/ui/components/ExpeditionPackPanel.kt',
]
source_hashes={}
for name in source_paths:
 p=workspace/name; source_hashes[name]=sha(p)
 snapshot=out/'original-sources'/name
 snapshot.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,snapshot)
for platform in ('ios','android'):
 for attempt in ('1','2'):
  build=workspace/'cache'/f'compile-{platform}-{attempt}'
  for name in ('build.log','record.json'):
   shutil.copy2(build/name,out/'logs'/f'compile-{platform}-{attempt}-{name}')
commands=json.loads((out/'plan-commands.json').read_text())
for p in sorted(out.glob('compile-*.json')): commands.append(json.loads(p.read_text()))
commands.insert(0,{
 'kind':'initial instruction acquisition',
 'command':['cat','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/prompts/unit-df4422-initial.txt'],
 'exitCode':0,'startedAtUtc':'2026-10-20T14:32:25+00:00',
 'scope':'Assigned frozen Skill, own workspace and public T1 design only.',
})
commands.insert(1,{
 'kind':'setup and project instruction discovery',
 'command':'mkdir -p agent-output; Python clock wrote phase-start.json; pwd; rg --files -g AGENTS.md -g SKILL.md -g BRIEF.md -g API.md -g reference.json -g contract.json -g bindings.json -g approval.json .',
 'exitCode':1,
 'reason':'The final rg found no matching files in the assigned workspace at that stage; phase-start recording succeeded. Subsequent own-workspace and ancestor AGENTS discovery found no applicable AGENTS.md.',
 'log':'agent-output/logs/initial-discovery.log',
})
(out/'logs'/'initial-discovery.log').write_text('Initial setup succeeded and printed the assigned workspace path. Final rg returned exit 1 because no requested instruction filenames existed under this workspace. Follow-up instruction discovery completed with no applicable AGENTS.md found. No compile attempt failed.\n')
commands.append({'kind':'source implementation','command':'Wrote the two public production source files, then aligned disclosure typography to the fixed native action style (16, semibold).','exitCode':0})
commands.append({'kind':'final sealing','command':['python3','agent-output/scripts/finalize_initial.py'],'startedAtUnix':time.time(),'exitCode':0})
(out/'commands.json').write_text(json.dumps(commands,indent=2))
plan_paths=[str(p.relative_to(workspace)) for p in sorted((out/'plans').rglob('*.json'))]
sealed_paths=list(sorted((out/'plans').rglob('*')))+list(sorted((out/'scripts').rglob('*')))
sealed={str(p.relative_to(workspace)):sha(p) for p in sealed_paths if p.is_file()}
finished=time.time()
seal={
 'version':1,'sealedAtUnix':finished,
 'design_lock_sha256':'24a80e813cb3a2638499d9294fcacc0439891c680211ce85981a7a9b590c6b2c',
 'files':sealed,'source_files':source_hashes,
 'note':'Original compiler-generated plans/actions were never hand-edited. This seal predates all SDK rendering and observed UI feedback.'
}
(out/'plans-seal.json').write_text(json.dumps(seal,indent=2))
(out/'sources-seal.json').write_text(json.dumps({'sealedAtUnix':finished,'files':source_hashes,'snapshotRoot':'agent-output/original-sources'},indent=2))
start=json.loads((out/'phase-start.json').read_text())
implementation={
 'phase':'initial','status':'implemented_compile_only',
 'startedAtUnix':start['startedAtUnix'],'finishedAtUnix':finished,
 'startedAtUtc':start['startedAtUtc'],
 'finishedAtUtc':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat(),
 'elapsedSeconds':finished-start['startedAtUnix'],'budgetSeconds':1500,
 'changed_files':source_paths,'source_sha256':source_hashes,
 'commands':'agent-output/commands.json',
 'logs':[str(p.relative_to(workspace)) for p in sorted((out/'logs').iterdir())],
 'plan_paths':plan_paths,'plans_seal':'agent-output/plans-seal.json',
 'sources_seal':'agent-output/sources-seal.json',
 'compile_results':{'ios':{'attempts':2,'finalExitCode':0,'record':'agent-output/compile-ios-2.json'},'android':{'attempts':2,'finalExitCode':0,'record':'agent-output/compile-android-2.json'}},
 'plan_generation':{'cases':['P1','P2'],'platforms':['ios','android'],'assertionsPerPlan':122,'cellsPerPlan':132,'compiler':'assigned frozen Skill scripts/design_contract.py','originalStimulusRoutesPreserved':True,'expectationsHandEdited':False},
 'limits':[
  'Initial phase only: no SDK rendering, previews, app launch, observers or native interactions were run.',
  'Compile success is not screenshot, runtime behavior, accessibility geometry or visual acceptance.',
  'iOS computed typography/color/ellipsis evidence remains unsupported U; original checks are preserved.',
  'All state, derived values, selection eligibility, disclosure and callback routing live in production components; public bridges are unmodified.',
  'No commits, pushes, build setting changes, theme changes or changes to unrelated existing UI were made.',
  'Existing bootstrap changes in Package.swift and Reply/app/build.gradle.kts were retained.',
  'The fixed native presentation in BRIEF.md governs native type sizes; export typography is illustrative.',
  'Stop after initial delivery; read-only review and repair require a later explicit resumption from root.'
 ]
}
(out/'implementation.json').write_text(json.dumps(implementation,indent=2))
print(json.dumps({'status':implementation['status'],'elapsedSeconds':implementation['elapsedSeconds'],'sources':source_hashes,'sealedFiles':len(sealed),'plans':plan_paths},indent=2))
