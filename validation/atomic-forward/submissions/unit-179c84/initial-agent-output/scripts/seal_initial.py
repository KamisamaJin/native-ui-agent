import datetime,hashlib,json,pathlib,shutil,time
work=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-179c84')
out=work/'agent-output'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
for name in ['compile-android-1','compile-ios-1','compile-ios-2']:
 for src_name,dest_name in [('build.log',f'{name}.full.log'),('record.json',f'{name}.native-record.json')]:
  shutil.copyfile(work/'cache'/name/src_name,out/'logs'/dest_name)
failed=[
 {'command':"rg --files -g 'AGENTS.md' -g '!cache/**' -g '!agent-output/**' -g '!**/.git/**' . && rg --files /Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/baseline-v7",'cwd':str(work),'exitCode':1,'output':'','reason':'No matching workspace AGENTS.md; the chained Skill listing was therefore run separately next.','commandTime':'2026-10-22T02:05 UTC (tool transcript; exact subsecond unavailable)'},
 {'command':"ls -la && find .. -maxdepth 1 -name AGENTS.md -print && rg --files -g 'AGENTS.md' -g '!cache/**' -g '!agent-output/**' -g '!**/.git/**' .",'cwd':str(work),'exitCode':1,'output':'Workspace listing showed alerttoast, reply, bootstrap.json, agent-output; no AGENTS.md found.','reason':'rg returned its ordinary no-match status. Subsequent project-local find also found no AGENTS.md.','commandTime':'2026-10-22T02:05 UTC (tool transcript; exact subsecond unavailable)'}]
write(out/'failed-attempts.json',failed)
write(out/'static-review.json',{
 'method':'source_review_only',
 'checks':[
  'Public API and Codable camelCase fields implemented in production files.',
  'Selection is an available-ID set initialized and reset by authoritative revision; recomposition preserves transient state.',
  'Summary follows model service order and totals chosen minutes; submit preserves the draft.',
  'Unavailable controls retain literal status, supplied reason and ordinary details, with native disabled state.',
  'Each choice has one selection action and selected semantics; disclosure emits one Boolean callback.',
  'Component owns palette, full canvas semantic container, eager content, natural multiline text and minimum control heights.',
  'Host padding, viewport, fixtures, bridges, original stimuli and pinned build files were not edited.'
 ],
 'runtime_verification':'not_executed',
 'visual_verification':'not_executed',
 'compile_only':'passed on both platforms; final Swift source rebuilt after notice container adjustment'
})
artifacts=sorted(list((out/'plans').rglob('*.json'))+list((out/'scripts').glob('*.py')))
entries=[{'path':str(p.relative_to(work)),'sha256':digest(p)} for p in artifacts]
sealed_at=time.time()
write(out/'plans-seal.json',{
 'version':1,'sealedAtUnix':sealed_at,'sealedAtUtc':datetime.datetime.fromtimestamp(sealed_at,datetime.timezone.utc).isoformat(),
 'designLockSHA256':'0653c194d723fbb087b20ee8eac97b1388256ff2b8e3ba6db203c7a45cec4656',
 'originalGeneratedPlans':True,'generatedExpectedValuesEdited':False,
 'files':entries,
 'manifestSHA256':hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(',',':')).encode()).hexdigest()
})
source_paths=['alerttoast/Sources/AlertToast/BicycleServiceIntake.swift','reply/Reply/app/src/main/java/com/example/reply/ui/components/BicycleServiceIntake.kt']
plans=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  plan_path=pathlib.Path('agent-output/plans')/case/platform/'plan.json'
  actions_path=plan_path.with_name('actions.json')
  plan=json.loads((work/plan_path).read_text())
  plans.append({'case':case,'platform':platform,'plan':str(plan_path),'actions':str(actions_path),'cells':len(plan['matrix_contract']['cells']),'assertions':len(plan['assertions'])})
start=json.loads((out/'phase-start.json').read_text())
finish=time.time()
compile_records=[json.loads(p.read_text()) for p in sorted(out.glob('compile-*.json'))]
write(out/'implementation.json',{
 'version':1,'phase':'initial','status':'implemented_compile_only',
 'startedAtUnix':start['startedAtUnix'],'startedAtUtc':start['startedAtUtc'],
 'finishedAtUnix':finish,'finishedAtUtc':datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat(),
 'elapsedWallSeconds':finish-start['startedAtUnix'],'maximumWallSeconds':1500,
 'changed_files':source_paths,'sourceSHA256':{p:digest(work/p) for p in source_paths},
 'plans':plans,'plansSeal':'agent-output/plans-seal.json',
 'commands':json.loads((out/'plan-commands.json').read_text())+compile_records,
 'failedAttempts':'agent-output/failed-attempts.json',
 'failedBuildAttempts':[],
 'logs':[str(p.relative_to(work)) for p in sorted((out/'logs').glob('*'))],
 'staticReview':'agent-output/static-review.json',
 'untouchedPinnedBuildFiles':{p:digest(work/p) for p in ['alerttoast/Package.swift','reply/Reply/app/build.gradle.kts']},
 'limits':[
  'Initial phase only; no app launch, preview, observer acquisition, SDK rendering or screenshot command was run.',
  'Native runtime behavior, actual control geometry, full-content wrapping, overlap and rendered pixel colors remain unverified.',
  'Original compiler-generated unsupported and N/A cells retained, including unavailable generic SwiftUI computed title weight.',
  'No bridge, fixture, design source, original action, pinned build setting, unrelated production file, Skill or tool was changed.',
  'No commits, pushes or subagents.',
  'Stop after this seal and await root authorization for the separate read-only visual phase.'
 ]
})
print(json.dumps({'implementation':str(out/'implementation.json'),'elapsedWallSeconds':finish-start['startedAtUnix'],'sealedFiles':len(entries),'sourceSHA256':{p:digest(work/p) for p in source_paths}},indent=2))
