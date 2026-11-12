"""No SDK/process execution: inject failure of the supervisor context release."""
import sys,json,hashlib,importlib.util,subprocess,io,contextlib
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'operator-review';source=BASE/'original-source/native_envelope.py';private=BASE/'envelope-release-error';private.mkdir();sys.path.insert(0,str(ROOT.parents[1]/'baseline-v12.6/scripts'));sys.path.insert(0,str(BASE/'original-source'))
spec=importlib.util.spec_from_file_location('review8_pinned_envelope',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
production=private/'production';production.mkdir();(production/'source.swift').write_text('// HOST simulated subject, never compiled\n');config=private/'config.json';save(config,{'source_roots':[str(production)]});save(private/'operators/whole-study-meter-spec-v2.json',{'groups':{'episode':{'paths':[str(private)],'resource_journals':[]}},'max_total_allocated_bytes':1024**3,'min_free_bytes':0,'sample_seconds':2})
class ReleaseError:
 def __init__(self,*args,**kwargs):pass
 def __enter__(self):return self
 def sample(self):return 0
 def check_budget(self):pass
 def run(self,argv,**kwargs):kwargs['stdout'].write('SIMULATED child success; no process spawned\n');return 0
 def __exit__(self,*args):raise RuntimeError('SIMULATED managed supervisor release/cleanup failed after child success')
calls=[]
def recovery(argv,**kwargs):calls.append(argv);return subprocess.CompletedProcess(argv,0)
argv=[str(source),'--config',str(config),'--skill',str(private/'SIMULATED-SKILL'),'--record',str(private/'record'),'--timeout','5','--','SIMULATED-NEVER-EXECUTED'];printed=io.StringIO()
with patch.object(m,'R',private),patch.object(m.rm,'Resources',ReleaseError),patch.object(subprocess,'run',recovery),patch.object(sys,'argv',argv),contextlib.redirect_stdout(printed):code=m.main()
result=json.loads((private/'record/result.json').read_text());row={'id':'O09-envelope-error-after-child-zero','status':'P'if code!=0 else'F','expected_exit':'nonzero for supervisor error','actual_exit':code,'recorded_error':result['error'],'recorded_child_exit':result['exit_code'],'source_unchanged':result['source_unchanged'],'stdout':printed.getvalue(),'recovery_commands_intercepted':calls,'native_runs':0,'actual_processes_spawned':0,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'evidence_class':'HOST pinned envelope with fake resource release and recovery boundary; no SDK/device/timing sample'};save(BASE/'envelope-error-probe.json',row);print(json.dumps(row,indent=2))
