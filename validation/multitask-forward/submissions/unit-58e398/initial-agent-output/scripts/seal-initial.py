import hashlib,json,shutil,time
from pathlib import Path
workspace=Path(__file__).resolve().parents[2]
output=workspace/'agent-output'
for platform in ['ios','android']:
 cache=workspace/'cache'/f'{platform}-compile-01'
 shutil.copyfile(cache/'record.json',output/f'build-{platform}-record.json')
 shutil.copyfile(cache/'build.log',output/'logs'/f'build-{platform}.log')
files=sorted(list((output/'plans').rglob('plan.json'))+list((output/'plans').rglob('actions.json'))+list((output/'scripts').glob('*')))
entries=[{'path':str(p.relative_to(workspace)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files if p.is_file()]
seal={'version':1,'phase':'original-initial','sealedAtUnix':time.time(),'designLockCanonicalSHA256':'24a80e813cb3a2638499d9294fcacc0439891c680211ce85981a7a9b590c6b2c','files':entries}
(output/'plans-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
sources=['alerttoast/Sources/AlertToast/ExpeditionPackPanel.swift','reply/Reply/app/src/main/java/com/example/reply/ui/components/ExpeditionPackPanel.kt']
commands=json.loads((output/'plan-commands.json').read_text())
commands += [json.loads((output/f'compile-{platform}-01.json').read_text()) for platform in ['ios','android']]
started=json.loads((output/'phase-start.json').read_text())
finished=time.time()
record={
 'phase':'initial',
 'status':'implemented_compile_only_passed',
 'startedAtUnix':started['startedAtUnix'],
 'finishedAtUnix':finished,
 'elapsedWallSeconds':finished-started['startedAtUnix'],
 'budgetWallSeconds':1500,
 'changed_files':sources,
 'sourceHashes':{p:hashlib.sha256((workspace/p).read_bytes()).hexdigest() for p in sources},
 'commands':commands,
 'logs':[str(p.relative_to(workspace)) for p in sorted((output/'logs').glob('*'))],
 'plans':[str(p.relative_to(workspace)) for p in sorted((output/'plans').rglob('*.json'))],
 'plansSeal':'agent-output/plans-seal.json',
 'compileRecords':['agent-output/build-ios-record.json','agent-output/build-android-record.json'],
 'failedAttempts':[],
 'limits':[
  'Initial implementation only; no repair after rendered feedback.',
  'No rendering, screenshots, previews, observers, app launches or SDK execution other than the authorized no-render compile helper.',
  'Visual appearance, native accessibility geometry, actual dispatch, mounted state transitions and complete scrolling are not runtime verified.',
  'Compiler output expected values, source provenance, units, precision, coverage and original public action routes were not edited.',
  'Unsupported native style checks remain in the original compiler plans, including unmeasurable iOS computed typography and color.',
  'No commits or pushes; existing framework/build settings, themes and unrelated UI were not changed.'
 ]
}
(output/'implementation.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'status':record['status'],'startedAtUnix':record['startedAtUnix'],'finishedAtUnix':finished,'elapsedWallSeconds':record['elapsedWallSeconds'],'sealedFiles':len(entries),'sourceHashes':record['sourceHashes']},indent=2))
