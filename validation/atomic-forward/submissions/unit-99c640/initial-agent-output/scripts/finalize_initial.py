from pathlib import Path
import json,time,datetime,hashlib,shutil
W=Path(__file__).resolve().parents[2]
A=W/'agent-output'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for platform in ['ios','android']:
 src=W/'cache'/f'compile-{platform}-01'
 for name in ['record.json','build.log']:
  shutil.copy2(src/name,A/'logs'/f'{platform}-01-{name}')
plan_files=sorted((A/'plans').rglob('*.json'))
scripts=sorted((A/'scripts').rglob('*'))
sealed=[p for p in plan_files+scripts if p.is_file()]
seal={'version':1,'sealedAtUnix':time.time(),'kind':'original_initial_plans_actions_and_scripts','design_lock_sha256':'1595cbbb3a50848a0fe9a639bc775dde0a781690fc94381a6eb8f0a469d4c31a','files':{str(p.relative_to(W)):digest(p) for p in sealed}}
(A/'plans-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
source_paths=[W/'alerttoast/Sources/AlertToast/WorkshopSlotPlanner.swift',W/'reply/Reply/app/src/main/java/com/example/reply/ui/components/WorkshopSlotPlanner.kt']
started=json.loads((A/'phase-start.json').read_text())
finished=time.time()
commands=json.loads((A/'plan-command-record.json').read_text())
commands += [json.loads(p.read_text()) for p in sorted(A.glob('compile-*-command.json'))]
record={
 'phase':'initial','status':'implemented_compile_only_passed_awaiting_cohort_seal',
 'startedAtUnix':started['startedAtUnix'],'startedAtUTC':started['startedAtUTC'],
 'finishedAtUnix':finished,'finishedAtUTC':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat(),
 'elapsedSeconds':finished-started['startedAtUnix'],'wallBudgetSeconds':1500,
 'changed_files':[str(p.relative_to(W)) for p in source_paths],
 'source_sha256':{str(p.relative_to(W)):digest(p) for p in source_paths},
 'commands':commands,
 'command_history_notes':[
  'Read assigned initial specification first; phase-start.json was recorded immediately afterward using Python time.time and UTC datetime.',
  'Read only assigned frozen Skill, own workspace instructions/source/settings, and specified independent public design sources/cases/reference SVG and PNGs. No AGENTS.md was found in this workspace.',
  'An initial rg file-name inventory was too broad and included names under public/compiled and public/validation-logs; no contents in those directories were read.',
  'Inspected design compiler compile --help and compile_only.py --help; both exited 0.',
  'Created the two production source files, plan generator, compile recorder and finalizer with shell heredocs; all write commands exited 0.',
  'All original plan generation and actual compile commands are preserved in command JSON/logs. No failed compile or generation attempts occurred.',
  'Own git status was inspected after compilation. Existing Package.swift, Reply/app/build.gradle.kts and Reply/.native-ui are bootstrap/helper inputs; no direct edits to them were made during implementation.'
 ],
 'plan_paths':[str(p.relative_to(W)) for p in plan_files],
 'plans_seal':'agent-output/plans-seal.json',
 'compiler':{'path':'/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/baseline-v7/scripts/design_contract.py','sha256':digest(Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/baseline-v7/scripts/design_contract.py'))},
 'requirements_implemented':[
  'Public Swift Codable models/memberwise initializers and Compose data models/API.',
  'Eager responsive grid, one selection, disabled availability, verbatim reasons plus ordinary details, exact summary/action/disclosure labels.',
  'Revision-authoritative selection/disclosure reset with no callbacks; same revision retains user state.',
  'Native control disabled/selected semantics and production-owned exact target IDs.',
  'Component-owned palette/canvas/panels, scalable text, natural wrapping and expanding controls with no internal scrolling.'
 ],
 'limits':[
  'Initial phase only. No direct SDK rendering, previews, observers, screenshots, app launch or runtime interaction was performed.',
  'Only independent reference PNGs were viewed. Compile success does not establish screenshot acceptance, wrapping, color samples or runtime callback correctness.',
  'All generated checks including unsupported iOS computed title weight remain original and unedited.',
  'No private design, other candidate source, other Skill version, old trial/report, evaluation or common corpus content was accessed.',
  'No commits or pushes; no subagents; no tools, bridges, expected values, tolerances or build settings were edited.',
  'Stop after this record and original seal; no repair or rendering until root explicitly resumes after full cohort seal.'
 ]
}
(A/'implementation.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'status':record['status'],'elapsedSeconds':record['elapsedSeconds'],'planFiles':len(plan_files),'sealedFiles':len(sealed),'productionSources':len(source_paths),'implementation':str(A/'implementation.json'),'plansSeal':str(A/'plans-seal.json')},indent=2))
