import pathlib,json,time,subprocess
w=pathlib.Path(__file__).resolve().parents[2];o=w/'agent-output/repair';build=w/'cache/compile-ios-repair'
command=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/compile_only.py','--workspace',str(w),'--platform','ios','--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward/design-v2/T2/public/Bridge.swift','--output',str(build)]
record={'command':command,'startedAtUnix':time.time(),'status':'running'}
p=o/'compile-driver-record.json';p.write_text(json.dumps(record,indent=2)+'\n')
with (o/'compile-driver.log').open('w') as f:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
record.update(finishedAtUnix=time.time(),status='finished',exitCode=r.returncode);p.write_text(json.dumps(record,indent=2)+'\n')
for f in build.rglob('*'):
 if f.is_file() and (f.suffix=='.log' or (f.suffix=='.json' and f.name in ['record.json','result.json'])):(o/('compile-'+f.name)).write_bytes(f.read_bytes())
print(json.dumps(record,indent=2));raise SystemExit(r.returncode)
