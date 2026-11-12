"""HOST-only operator postprocessor tests; no benchmark/native episode executes.

Every native replay is an explicit non-forwarding stub. These cases test the
operator's structural accounting/acceptance checks, never native proof or speed.
"""
import sys,importlib.util,hashlib,json,copy,subprocess,contextlib,io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'operator-review';SOURCE=BASE/'original-source/verify_benchmark.py'
spec=importlib.util.spec_from_file_location('review8_benchmark_postprocessor',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=[]
def probe(name,change,expected_pass):
 root=BASE/'probes'/name;root.mkdir(parents=True);work=root/'synthetic-study';work.mkdir();admission={'order':[list(x)for x in m.ORDER],'threshold':0.20,'required_native_atoms':104,'verifier_sha256':sha(SOURCE),'arms':{'A':{'skill':'SIMULATED-baseline','freeze_sha256':'a'*64},'B':{'skill':'SIMULATED-candidate','freeze_sha256':'b'*64}},'production_files':{'same/component.swift':'c'*64},'driver_sha256':'d'*64,'envelope_sha256':'e'*64};replay_results={};cursor=1000
 for block,arm in m.ORDER:
  episode=work/'cache/benchmark'/block/arm;episode.mkdir(parents=True);wall=100.0 if arm=='A'else 70.0;stages=[{'stage':label,'wall_seconds':wall/4,'started_at_unix':cursor+i*wall/4,'finished_at_unix':cursor+(i+1)*wall/4}for i,label in enumerate(['C0','R0','W1','F2'])]
  result={'failed':None,'source_unchanged':True,'stages':stages,'collection_wall_seconds':wall,'collection_stage_seconds':wall,'operator_and_meter_seconds':0,'collection_started_at_unix':cursor,'finished_at_unix':cursor+wall};entry={'skill_seal_sha256':admission['arms'][arm]['freeze_sha256'],'source_map':copy.deepcopy(admission['production_files']),'driver_sha256':admission['driver_sha256'],'envelope_sha256':admission['envelope_sha256'],'profile_admission_sha256':'p'*64}
  save(episode/'result.json',result);save(episode/'ADMISSION.json',entry);save(episode/'meter.summary.json',{'budget_exceeded':False,'sampling_error':None,'observed_total_peak_allocated_bytes':12345})
  for step,case in m.STEPS:
   profile=episode/'profiles'/(case+'.json');save(profile,{'SIMULATED':True,'case':case});packet=episode/'original-packets'/(step+'.json');save(packet,{'SIMULATED':True,'actual_native_executed':False})
   source_row={'id':'thin-bridge','priority':'must','owner':'bridge','method':'source','status':'passed','files':{'SIMULATED-current-bridge':'f'*64}}
   cycle={'capture_result':str(packet),'status':'accepted'if step.startswith('F2-')else'awaiting_full_final','native_executed':True,'evidence_responsibility':{'blocking_claims':[],'rows':[source_row]}}
   save(episode/'evidence'/step/'cycle.json',cycle);save(episode/'evidence'/step/'resources.json',{'remaining_devices':[],'remaining_directories':[],'cleanup_errors':[]})
   pl='android'if case=='android'else'ios';replayed={'packet':str(packet),'source_map':{},'platform':pl,'design_sha256':'design','plan_sha256':'plan-'+case,'fixtures_sha256':'fixture-'+case,'bridge_sha256':'bridge-'+pl,'environment_sha256':'environment-'+pl,'rows':[{'id':'atom-'+str(i),'state':'state-'+str(i%5),'status':'passed','reason':'SIMULATED replay stub; no native proof','requirement_id':'rule-'+str(i),'property':'present','kind':'control','unit':'bool','expected':True,'op':'eq'}for i in range(104)],'native_counts':{'passed':104,'failed':0,'unassessed':0},'coverage':{'satisfied':True},'environment':{'status':'P'},'native_tests':1,'passed':True,'evidence_class':'SIMULATED trust-boundary output, zero SDK/native/time credit'};replay_results[str(packet)]=replayed
  cursor+=wall+10
 change(work,replay_results)
 adm=root/'SYNTHETIC-ADMISSION.json';save(adm,admission)
 calls=[]
 def fake_run(argv,**kwargs):
  calls.append({'argv':argv,'boundary':'SIMULATED native-replay response only; never launches a process'});packet=argv[argv.index('--packet')+1];out=argv[argv.index('--output')+1];save(out,replay_results[packet]);return subprocess.CompletedProcess(argv,0,stdout='SIMULATED no native replay executed\n')
 output=root/'postprocessor-output';stream=io.StringIO()
 with patch.object(m,'R',work),patch.object(m.subprocess,'run',fake_run),contextlib.redirect_stdout(stream):code=m.evaluate(SimpleNamespace(admission=str(adm),output=str(output)))
 actual=json.loads((output/'RESULT.json').read_text());save(root/'replay-boundary-calls.json',calls);save(root/'SIMULATION.json',{'native_runs':0,'benchmark_episodes_run':0,'no_SDK_or_subprocess_forwarded':True,'test_subject':'Pinned verifier postprocessor accounting only; all replay bodies synthetic'});row={'id':name,'status':'P'if actual['passed']==expected_pass else'F','expected_gate_pass':expected_pass,'actual_gate_pass':actual['passed'],'claimed_reduction':actual['reduction'],'errors':actual['errors'],'gate_output':str(output/'RESULT.json'),'source_sha256':sha(SOURCE),'evidence_class':'HOST operator postprocessor on SIMULATED files/replays; no performance/native qualification'};rows.append(row);save(root/'probe-result.json',row);print(name+': '+row['status']+'; gate_pass='+str(actual['passed']),flush=True)
def episodes(w):return sorted((w/'cache/benchmark').glob('*/*'))
def edit(p,fn):v=json.loads(p.read_text());fn(v);save(p,v)
probe('O01-coherent-structural-positive',lambda w,r:None,True)
probe('O02-source-duty-denominator-zero',lambda w,r:[edit(p,lambda v:v['evidence_responsibility'].update(rows=[]))for p in(w/'cache/benchmark').glob('*/*/evidence/F2-*/cycle.json')],False)
probe('O03-negative-B-wall',lambda w,r:[edit(e/'result.json',lambda v:v.update(collection_wall_seconds=-10))for e in episodes(w)if e.name=='B'],False)
probe('O04-wall-disagrees-with-stages-and-envelope',lambda w,r:[edit(e/'result.json',lambda v:v.update(collection_wall_seconds=1,operator_and_meter_seconds=-69))for e in episodes(w)if e.name=='B'],False)
probe('O05-order-overlap-rejected',lambda w,r:[edit(e/'result.json',lambda v:v.update(collection_started_at_unix=0,finished_at_unix=100))for e in episodes(w)],False)
probe('O06-source-changed-rejected',lambda w,r:edit(episodes(w)[0]/'result.json',lambda v:v.update(source_unchanged=False)),False)
probe('O07-native-denominator-count-rejected',lambda w,r:[v.update(native_counts={'passed':103,'failed':0,'unassessed':1})for v in r.values()],False)
probe('O08-final-resource-retirement-rejected',lambda w,r:[edit(p,lambda v:v.update(remaining_devices=['SIMULATED-leftover']))for p in(w/'cache/benchmark').glob('*/*/evidence/F2-*/resources.json')],False)
save(BASE/'probe-results.json',rows)
