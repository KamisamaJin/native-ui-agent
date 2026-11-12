from support import *
import subprocess,platform
import resource_manager as rm
os.environ.update(PATH=str(ROOT/'checks'/'bin')+os.pathsep+os.environ['PATH'],REVIEW_SIM_INVENTORY=str(ROOT/'work'/'simulated-inventory.json'),PYTHONDONTWRITEBYTECODE='1')
rows=[];seen=set();tracked=[]
for cp in sorted((ROOT/'work').rglob('config.json')):
 try:config=d.load(cp)
 except Exception:continue
 if not isinstance(config,dict) or 'source_roots' not in config:continue
 resource=config.get('resources',{}).get('root')
 if not resource:continue
 root=Path(resource)
 if root in seen or not root.exists():continue
 seen.add(root)
 if not root.is_relative_to(ROOT/'work'):raise RuntimeError('Foreign cleanup path refused')
 # The copied root is an intentionally altered negative-case snapshot and must stay preserved.
 if root.name=='copied-scratch':
  rows.append({'config':str(cp),'root':str(root),'status':'preserved negative-case snapshot; ownership rejection already proved'})
  original=root.with_name('scratch')
  if not original.exists():continue
  config=json.loads(json.dumps(config));config['resources']['root']=str(original);root=original
 before={}
 for name in ['owner.json','journal.json','journal-backup.json']:
  path=root/name
  if path.is_file():before[name]={'sha256':sha(path),'bytes':path.stat().st_size}
 if (root/'journal.json').is_file():
  state=d.load(root/'journal.json')
  for key in ['pool_watch','process']:
   if state.get(key):tracked.append(state[key])
 out=ROOT/'raw'/'final-cleanup'/('root-'+str(len(rows)))
 try:
  with rm.Resources(config,out,final=True):pass
  receipt=d.load(out/'resources.json')
  rows.append({'config':str(cp),'root':str(root),'before_artifacts':before,'status':'closed','receipt':str(out/'resources.json'),'remaining_devices':receipt['remaining_devices'],'remaining_directories':receipt['remaining_directories'],'cleanup_errors':receipt['cleanup_errors']})
 except Exception as error:
  rows.append({'config':str(cp),'root':str(root),'before_artifacts':before,'status':'error','error':repr(error),'receipt':str(out/'resources.json') if(out/'resources.json').exists()else None})
pids=sorted({r['pid'] for r in tracked if type(r.get('pid'))is int})
post={}
if pids:
 argv=['ps','-ww','-p',','.join(map(str,pids)),'-o','pid=,pgid=,state=,lstart=,command=']
 p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5)
 post={'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
save(ROOT/'raw'/'final-cleanup-audit.json',{'evidence_class':'HOST closure of private files/processes with SIMULATED inventory retirement','rows':rows,'post_process_query':post,'simulated_inventory':d.load(Path(os.environ['REVIEW_SIM_INVENTORY']))})
prior=d.load(ROOT/'raw'/'candidate-source-hashes.json');current=[]
for p in sorted(CANDIDATE.rglob('*')):
 if p.is_file():current.append({'path':str(p.relative_to(CANDIDATE)),'sha256':sha(p),'bytes':p.stat().st_size})
save(ROOT/'raw'/'candidate-unchanged.json',{'same':prior==current,'before_manifest_sha256':sha(ROOT/'raw'/'candidate-source-hashes.json'),'files':len(current),'differing_paths':sorted({r['path'] for r in prior+current if next((v for v in prior if v['path']==r['path']),None)!=next((v for v in current if v['path']==r['path']),None)})})
save(ROOT/'raw'/'host-info.json',{'evidence_class':'HOST','python_executable':sys.executable,'python_version':sys.version,'platform':platform.platform(),'machine':platform.machine(),'monotonic_clock':str(time.get_clock_info('monotonic')),'host_boot_id':rm.boot_identity(),'free_bytes':__import__('shutil').disk_usage(ROOT).free,'actual_native_commands_executed':0,'performance_samples':0,'test_process_scope':'Only private test helpers/guardians/launchers under review-1; no global process or cache cleanup.'})
print(json.dumps({'roots_examined':len(rows),'cleanup_errors':[r for r in rows if r['status']=='error'],'simulated_inventory_remaining':len(d.load(Path(os.environ['REVIEW_SIM_INVENTORY']))['devices']),'candidate_unchanged':prior==current},indent=2))
