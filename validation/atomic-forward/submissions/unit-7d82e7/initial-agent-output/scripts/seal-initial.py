import datetime,hashlib,json,pathlib,time
workspace=pathlib.Path(__file__).resolve().parents[2]
output=workspace/'agent-output'
started=json.loads((output/'phase-start.json').read_text())
sources=['alerttoast/Sources/AlertToast/BicycleServiceIntake.swift','reply/Reply/app/src/main/java/com/example/reply/ui/components/BicycleServiceIntake.kt']
plans=sorted(str(p.relative_to(workspace)) for p in (output/'plans').rglob('*.json'))
scripts=sorted(str(p.relative_to(workspace)) for p in (output/'scripts').glob('*.py'))
for platform in ['ios','android']:
 cache=workspace/'cache'/f'compile-{platform}-01'
 for name in ['record.json','build.log']:
  source=cache/name
  if source.exists(): (output/'logs'/f'{platform}-01-{name}').write_bytes(source.read_bytes())
finished=time.time()
records=[json.loads((output/f'compile-{platform}-01.json').read_text()) for platform in ['ios','android']]
implementation={
 'phase':'initial','status':'implemented_compile_only_passed',
 'startedAtUnix':started['startedAtUnix'],'startedAtUtc':started['startedAtUtc'],
 'finishedAtUnix':finished,'finishedAtUtc':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat().replace('+00:00','Z'),
 'wallSeconds':finished-started['startedAtUnix'],'budgetSeconds':1500,
 'changed_files':sources,
 'designLockSHA256':'0653c194d723fbb087b20ee8eac97b1388256ff2b8e3ba6db203c7a45cec4656',
 'assignedSkill':'/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/candidate-v8/SKILL.md',
 'referenceRoot':'/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T3/public',
 'plan_paths':plans,'scripts':scripts,
 'commands':{'plan_generation':'agent-output/plan-commands.json','compile_only':records,'inspection_and_writes':'agent-output/activity-record.json'},
 'logs':sorted(str(p.relative_to(workspace)) for p in (output/'logs').glob('*')),
 'compile_results':{r['command'][r['command'].index('--platform')+1]:r['status'] for r in records},
 'failed_attempts':[],
 'business_implementation':['Public models, Codable/memberwise Swift initializers and named Kotlin API','Revision-keyed local selection/disclosure reset; no replacement callbacks','Eager grouped independent multiselection, disabled unavailable choices and verbatim reasons','Model-order live estimate, enabled submission and one callback per successful action','Real production semantic IDs, selected semantics and disabled control semantics','Component palette, scalable typography and naturally growing full-width content'],
 'baseline_worktree_notes':['Package.swift and Reply/app/build.gradle.kts already carried bootstrap changes when first read; no build settings were edited by this implementation. Reply/.native-ui was supplied by bootstrap.'],
 'limits':['No app launch, preview, observer, screenshot or SDK render was run.','Compile-only success does not establish native activation, runtime model replacement, typography or visual acceptance.','All original compiler expectations, action routes, units, precision, coverage and unsupported checks are unchanged.','No commits, pushes, bridge changes, tool changes, injected defects or agents.','Initial phase stops after this seal; further repairs require explicit root resumption.']
}
(output/'implementation.json').write_text(json.dumps(implementation,ensure_ascii=False,indent=2)+'\n')
files=sources+plans+scripts
seal={'version':1,'phase':'initial','sealedAtUnix':time.time(),'designLockSHA256':implementation['designLockSHA256'],'files':{name:hashlib.sha256((workspace/name).read_bytes()).hexdigest() for name in files},'originalCompilerOutputs':True,'renderedFeedbackReceived':False}
(output/'plans-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'status':implementation['status'],'wallSeconds':implementation['wallSeconds'],'sealedFiles':len(files),'seal':'agent-output/plans-seal.json'},indent=2))
