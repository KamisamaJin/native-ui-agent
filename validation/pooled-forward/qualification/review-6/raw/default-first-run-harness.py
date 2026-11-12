import sys,argparse,copy,shutil,contextlib,io,subprocess,plistlib
sys.dont_write_bytecode=True
from domain_support import *
from unittest.mock import patch
from types import SimpleNamespace
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import ui_loop,feedback_loop,resource_manager,ios_observe,action_guard,coverage_domain,execution_plan,capture_validity
base=ROOT/'work'/a.arm/'default';base.mkdir();rows=[];boundary_calls=[];emitted=[];collector_failure=False
def record(id,passed,detail):
 row={'id':id,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST actual default CLI/state machine/collector with SIMULATED non-forwarding resource/SDK boundary','detail':detail};rows.append(row);save(base/(id+'-result.json'),row)
 if not passed:save(ROOT/'first-failures'/(a.arm+'--default--'+id+'.json'),row)
 print(a.arm+' '+id+': '+row['status'],flush=True)

class NoDeviceResources:
 def __init__(self,config,output,final=False):self.config=config;self.output=Path(output);self.final=final
 def __enter__(self):return self
 def __exit__(self,*unused):
  self.output.mkdir(parents=True,exist_ok=True);save(self.output/'resources.json',{'evidence_class':'SIMULATED resource manager boundary, acquired zero devices/processes','cleanup_errors':[],'remaining_devices':[],'remaining_directories':[]});return False
 def native_options(self,platform):return dict(self.config['native_options'],**{'reset-owned-app':'1'})
 def run(self,argv,*,stdout,env,timeout=None):
  boundary_calls.append({'argv':argv,'evidence_class':'SIMULATED boundary reached; no command process created','failure':collector_failure})
  if collector_failure:stdout.write('SIMULATED acquisition failed before native output\n');return 1
  options={}
  for i in range(4,len(argv),2):options[argv[i][2:].replace('-','_')]=argv[i+1]
  options.setdefault('build_cache',None);options.setdefault('build_context_sha256',None);options.setdefault('coverage_domain',None);options.setdefault('sdk','iphonesimulator');options.setdefault('reset_owned_app',None)
  args=SimpleNamespace(**options);config=load(args.fixtures);actions=load(args.actions)
  # Independent full-width HOST raster, approved 390x600 shape, one simulated
  # start-state sweep. Later action states deliberately remain unobserved.
  src=self.output/'SIMULATED-source';o,s=fixture(src);w,h=390,1100;rng=random.Random(819108);world=Image.new('RGBA',(w,h));world.putdata([(rng.randrange(256),rng.randrange(256),rng.randrange(256),255)for _ in range(w*h)]);world.save(src/'world390.png')
  initial=config['initial'];binding=dict(o['state_captures'][0]['binding'],input_sha256=canonical(initial),instance='SIMULATED-default-'+str(len(boundary_calls)))
  for i,(snap,off)in enumerate(zip(o['snapshots'],[0,250,500])):
   snap.update(state_id='start',screenshot_attachment='frame-'+str(i)+'.png',geometry_encoding=copy.deepcopy(ENCODING),binding=copy.deepcopy(binding),binding_after_capture=copy.deepcopy(binding),app_frame=rect(0,0,w,600),viewport=rect(0,0,w,600),screenshot_pixels={'width':w,'height':600})
   snap['runtime']['content_frame']=rect(0,-off,w,[900,1000,1100][i]);snap['runtime']['actual_environment'].update(fixture_index=0,event_revision=0)
   for n in snap['nodes']:
    r=n['frame'];n['frame']=rect(r['x']*390/64,r['y']*600/96,r['width']*390/64,r['height']*600/96)
   snap['bottom_boundary']['frame']=copy.deepcopy(snap['nodes'][-1]['frame']);snap['bottom_boundary']['binding']=copy.deepcopy(binding)
   world.crop((0,off,w,off+600)).save(src/'images'/('frame-'+str(i)+'.png'))
  capture=o['state_captures'][0];capture.update(state_id='start',binding=copy.deepcopy(binding));guard_actions=action_guard.compile_actions(actions)
  o.update(coverage={'bottom_reached':True,'missing_identifiers':[]},guard_protocol=1,guard_platform='ios',guard_actions=guard_actions,steps=[{'action':guard_actions[0],'outcome':'observed','binding_after':copy.deepcopy(binding),'guard':{'protocol':1,'depends_on':guard_actions[0]['depends_on'],'conditions':[],'ready':True,'established':True,'binding':copy.deepcopy(binding)}}])
  save(src/'observation.json',o)
  def mock_command(cmd,env,log=None):
   emitted.append({'argv':cmd,'evidence_class':'SIMULATED command emission only; never forwarded'})
   text='SIMULATED command output, no external process\n'
   if 'summary'in cmd:text=json.dumps({'totalTestCount':1,'failedTests':0})
   if 'export'in cmd:
    exported=Path(cmd[cmd.index('--output-path')+1]);exported.mkdir();entries=[]
    for i in range(3):
     name='frame-'+str(i)+'.png';shutil.copyfile(src/'images'/name,exported/name);entries.append({'suggestedHumanReadableName':name,'exportedFileName':name})
    save(exported/'manifest.json',entries);save(exported/'SIMULATED-observation.json',o)
   if cmd and cmd[0]=='xcodebuild':
    result=Path(cmd[cmd.index('-resultBundlePath')+1]);result.mkdir();(result/'SIMULATED.txt').write_text('Mock result bundle only, never native\n')
   if log:Path(log).write_text(text)
   return subprocess.CompletedProcess(cmd,0,stdout=text)
  def mock_prepare(args,output,bridge,package,env,manifest):
   (output/'compiled-project').mkdir()
   for rel in['assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift']:shutil.copyfile(arm/rel,output/'compiled-project'/Path(rel).name)
   component=package/'Sources/AlertToast/NativeQualificationProbe.swift';(output/'compiled-build.log').write_text('SIMULATED compile text, not SDK evidence\nSwiftCompile normal arm64 '+str(component)+" (in target 'AlertToast' from project 'SIMULATED')\n")
   runfile=output/'SIMULATED-compiled.xctestrun';runfile.write_bytes(plistlib.dumps({'ObserverTests':{'TestBundlePath':'__TESTROOT__/SIMULATED.xctest'}}));return runfile
  with patch.object(ios_observe,'command',mock_command),patch.object(ios_observe,'prepare_build',mock_prepare),contextlib.redirect_stdout(stdout):return ios_observe.run(args)

def invoke(config,label):
 path=save(base/(label+'-config.json'),config);output=base/label;out=io.StringIO();err=io.StringIO();start=len(boundary_calls)
 argv=[str(arm/'scripts/ui_loop.py'),'native','--config',str(path),'--output',str(output)]
 with patch.object(sys,'argv',argv),patch.object(resource_manager,'Resources',NoDeviceResources),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):code=ui_loop.main()
 raw={'argv':argv,'exit_code':code,'stdout':out.getvalue(),'stderr':err.getvalue(),'boundary_calls':len(boundary_calls)-start,'evidence_class':'HOST public main, all SDK and resource operations replaced in-process'};save(base/(label+'-command.json'),raw)
 result=load(output/'cycle.json')if(output/'cycle.json').exists()else None
 return result,raw,output

# Default unapproved current source must queue before the collector boundary.
config,plan,lock=setup_config(base/'unapproved',arm);component=Path(config['evidence_subjects']['probe-component'][0]);component.write_text(component.read_text()+'\n// unapproved source change\n');r,raw,out=invoke(config,'pre-sdk-source-review')
record('W01-default-unapproved-queues-before-SDK',r is not None and r['status']=='review_source_domain'and not r['native_executed']and raw['boundary_calls']==0,{'command':raw,'cycle':r})

# Start with only normal approved; add independently authored existing repair
# revision as a new approval observation after an actual source patch.
config,plan,lock=setup_config(base/'repair',arm);approval_path=Path(config['coverage_domain_ref']['path']);full_approval=load(approval_path);first=copy.deepcopy(full_approval);first['platforms']['ios']['approved_component_revisions'].pop('repair-control');save(approval_path,first);config['coverage_domain_ref']['sha256']=canonical(first)
context_before=capture_validity.context(config,'ios');r,raw,out=invoke(config,'open-product-failure');task=load(out/'repair-task.json')if(out/'repair-task.json').exists()else None
record('W02-default-owned-original-failure-handoff',task is not None and bool(task['failed_assertions'])and raw['boundary_calls']==1,{'command':raw,'cycle':r,'task':task,'caveat':'Original simulated failed capture is intentionally incomplete for later action states; no native result claimed'})
if task is None:
 save(ROOT/'raw'/(a.arm+'-default-results.json'),rows);save(base/'boundary-calls.json',boundary_calls);save(base/'emitted-sdk-commands.json',emitted);raise SystemExit(1)
component=Path(config['evidence_subjects']['probe-component'][0]);repair=load(SPEC/'INPUTS.json')['sources']['ios']['repair-control'];shutil.copyfile(POOLED/repair['authored_artifact'],component);save(approval_path,full_approval);config['coverage_domain_ref']['sha256']=canonical(full_approval)
context_after=capture_validity.context(config,'ios');collector_failure=True;r2,raw2,out2=invoke(config,'default-patch-approved-collector-failure');state=load(Path(config['workflow']['root'])/'ios.json');completion=load(state['completion']['path'])if state.get('completion')else None
record('W03-default-approval-append-measures-patch-and-retests',context_before==context_after and raw2['boundary_calls']==1 and completion is not None and completion['source_after_sha256']!=completion['source_before_sha256']and state.get('task')is not None,{'command':raw2,'cycle':r2,'completion':completion,'workflow':state,'context_unchanged_by_append_only_approval':context_before==context_after})
for name,mutate in[
 ('W04-pending-host-domain-change',lambda d:d['common_host_shape']['common'].update(terminal_identifier='different-terminal')),
 ('W05-pending-oracle-change',lambda d:d['binds'].update(design_lock_sha256='c'*64)),
 ('W06-pending-premise-change',lambda d:d.update(scope='An extra hidden branch is declared closed'))]:
 c=copy.deepcopy(config);changed=copy.deepcopy(full_approval);mutate(changed);path=save(base/(name+'-approval.json'),changed);c['coverage_domain_ref']={'path':str(path),'sha256':canonical(changed)};result,command,output=invoke(c,name)
 record(name,result is None and command['exit_code']==2 and command['boundary_calls']==0 and 'Pending native retest oracle/bridge/environment changed'in command['stderr'],{'command':command,'pending_completion_remains':load(Path(config['workflow']['root'])/'ios.json').get('completion')})
# A source approval list change is policy-normalized, but removal of the current
# revision still cannot license acquisition/full evidence/adoption.
c=copy.deepcopy(config);path=save(base/'removed-current-approval.json',first);c['coverage_domain_ref']={'path':str(path),'sha256':canonical(first)};result,command,output=invoke(c,'current-source-approval-removed')
record('W07-revision-list-normalization-cannot-waive-admission',result is not None and result['status']=='review_source_domain'and not result['native_executed']and not result.get('capture_reused')and command['boundary_calls']==0,{'command':command,'cycle':result,'pending_completion_retained':bool(load(Path(config['workflow']['root'])/'ios.json').get('completion'))})
manifest=load(out/'capture/native/manifest.json');record('W08-actual-controller-emits-domain-build-and-original-root',bool(manifest.get('execution_coverage'))and(out/'capture/native/coverage-domain-binding.json').is_file()and(out/'capture/native/compiled-project/ObserverApp.swift').is_file()and '--coverage-domain'in boundary_calls[0]['argv'] if boundary_calls else False,{'manifest_status':manifest['status'],'manifest_error':manifest.get('error'),'first_state_coverage':manifest.get('execution_coverage',{}).get('required_states',[None])[0],'compiled_host_sha256':sha(out/'capture/native/compiled-project/ObserverApp.swift'),'source_hashes':manifest['source_hashes'],'all_commands_in_process_nonforwarding':True})
save(ROOT/'raw'/(a.arm+'-default-results.json'),rows);save(base/'boundary-calls.json',boundary_calls);save(base/'emitted-sdk-commands.json',emitted)
