import json,pathlib,subprocess,sys,time,shutil
out=pathlib.Path(__file__).resolve().parent;w=out.parents[1]
platform=sys.argv[1]
cache=w/'cache'/f'repair-compile-{platform}-01'
cmd=['python3','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/compile_only.py','--workspace',str(w),'--platform',platform,'--output',str(cache)]
if platform=='ios':cmd += ['--bridge','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T3/public/Bridge.swift']
record={'command':cmd,'startedAtUnix':time.time(),'status':'running'}
rp=out/f'compile-{platform}-01.json';rp.write_text(json.dumps(record,indent=2)+'\n')
try:
 with (out/f'compile-{platform}-01.log').open('w') as log:
  p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=650)
 record.update(exitCode=p.returncode,status='passed' if p.returncode==0 else 'failed')
except subprocess.TimeoutExpired:
 record.update(exitCode=None,status='timeout')
finally:
 record['finishedAtUnix']=time.time()
 record['log']=str(out/f'compile-{platform}-01.log')
 record['output']=str(cache)
 rp.write_text(json.dumps(record,indent=2)+'\n')
 for name in ['record.json','build.log']:
  if (cache/name).exists():shutil.copy2(cache/name,out/f'{platform}-01-{name}')
print(json.dumps(record))
