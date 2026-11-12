from pathlib import Path
import subprocess,sys,os,json,hashlib,tarfile
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
ROOT=BASE/'business-design'; OUT=BASE/'business-design-review'; TOOL=BASE/'candidate-v13.9/scripts'
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
runs=[];env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
for task in range(1,6):
 for phase in ['public','private']:
  src=ROOT/f'T{task}'/phase;target=OUT/f'T{task}'/phase;target.mkdir(parents=True,exist_ok=True)
  seal=json.loads((src/'seal.json').read_text()); locksha=seal['design_lock_sha256']; scenario=seal['scenario']
  cmds=[('seal',[sys.executable,'-B',str(TOOL/'design_contract.py'),'seal','--contract',str(src/'contract.json'),'--root',str(src),'--output',str(target/'resealed-lock.json')])]
  for platform in ['ios','android']:
   cmds.append(('compile-'+platform,[sys.executable,'-B',str(TOOL/'design_contract.py'),'compile','--lock',str(src/'lock.json'),'--lock-sha256',locksha,'--scenario',scenario,'--platform',platform,'--bindings',str(src/f'bindings.{platform}.json'),'--actions',str(src/f'actions.{platform}.json'),'--output',str(target/platform/'compiled')]))
  for name,cmd in cmds:
   proc=subprocess.run(cmd,cwd=str(BASE.parent.parent),env=env,text=True,capture_output=True)
   (target/(name+'.stdout.txt')).write_text(proc.stdout);(target/(name+'.stderr.txt')).write_text(proc.stderr)
   runs.append({'family':f'T{task}/{phase}','stage':name,'argv':cmd,'exit_code':proc.returncode,'stdout_path':str(target/(name+'.stdout.txt')),'stderr_path':str(target/(name+'.stderr.txt')),'stdout':proc.stdout,'stderr':proc.stderr})
  for platform in ['ios','android']:
   dump(target/platform/'blocked-dependent-stages.json',{'catalog':'blocked: parent plan generation rejected original design','requirement_routes_audit':'blocked: parent plan unavailable','execution_plan':'blocked: parent plan unavailable','source_repair_performed':False,'SDK_or_native_run':False})
dump(OUT/'pure-run-log.json',runs)
archive=OUT/'rejected-original-design.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(ROOT.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(Path('business-design')/p.relative_to(ROOT)),recursive=False)
dump(OUT/'rejected-original-preservation.json',{'source_seal_sha256':hashlib.sha256((ROOT/'SEAL.sha256').read_bytes()).hexdigest(),'archive_path':str(archive),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(ROOT.rglob('*')) if p.is_file()]})
print(json.dumps({'run_count':len(runs),'successes':sum(r['exit_code']==0 for r in runs),'failures':sum(r['exit_code']!=0 for r in runs),'pure_only':True,'original_archive':str(archive)},indent=2))
