from pathlib import Path
import hashlib,json,time,shutil
R=Path(__file__).resolve().parent;S=R.parents[2]/'native-ui-agent';out=R/'tools-used/revision2';out.mkdir(parents=True,exist_ok=False)
files=[S/'SKILL.md']+list((S/'scripts').glob('*.py'))+list((S/'references').glob('*.md'))+[S/'assets/android-observer/NativeObserverTest.kt',S/'assets/ios-observer/ObserverApp.swift',S/'assets/ios-observer/ObserverTests.swift',S/'assets/ios-observer/CONTRACT.md']
for p in files:
 dest=out/p.relative_to(S);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
(R/'tools-revision2.json').write_text(json.dumps({'epoch':time.time(),'files':{str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}},indent=2)+'\n')
