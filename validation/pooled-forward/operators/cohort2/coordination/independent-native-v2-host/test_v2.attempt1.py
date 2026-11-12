#!/usr/bin/env python3
"""Synthetic metadata/control-flow guards; never actual RUN, private data or SDK."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=module(HERE.parent/'independent_native_v2.py','host_v2_runner')
c=module(HERE.parent/'collect_independent_v2.py','host_v2_collector')
old=module(HERE.parent/'collect_independent.py','host_original_collector_helpers')
OUT=HERE/'HOST'/str(time.time_ns());OUT.mkdir(parents=True)


def fixture(name):
    root=OUT/name;root.mkdir();evidence=root/'cache/business/independent-evaluation';record=evidence/'T2/I/ios/native'
    config=root/'config.json';capsule=root/'capsule.json';m.save(config,{'synthetic':'config'});m.save(capsule,{'synthetic':'capsule'})
    config_ref=m.ref(config);capsule_ref=m.ref(capsule);tool=root/'synthetic-frozen-tool'
    argv=[sys.executable,'-B',str(tool/'scripts/ui_loop.py'),'native','--config',str(config),'--output',str(record/'service'),'--final']
    recovery=[sys.executable,'-B',str(tool/'scripts/resource_manager.py'),'--config',str(config),'--output',str(record/'envelope/error-recovery'),'cleanup']
    m.save(record/'command.json',{'argv':argv,'config':config_ref})
    m.save(record/'sdk-observation.json',{'observed_command_records':[]})
    m.save(record/'envelope/request.json',{'argv':argv})
    m.save(record/'envelope/result.json',{'argv':argv,'exit_code':None,'error':{'type':'ValueError','message':'Resource ownership differs from this project'},'source_unchanged':True,'recovery':{'argv':recovery,'exit_code':0}})
    m.save(record/'envelope/error-recovery/resources.json',{'final':True,'cleanup_errors':[],'remaining_directories':[],'remaining_devices':[]})
    m.save(record/'envelope/error-recovery/resource-journal.json',{'synthetic':True})
    (record/'envelope/exception.log').write_text('synthetic original owner rejection')
    (record/'envelope/recovery.log').write_text('synthetic owned cleanup')
    (record/'envelope/error-recovery/resource-events.jsonl').write_text('')
    claimp=m.scope_path(evidence,'T2','I','ios')
    m.save(claimp,{'task':'T2','arm':'I','profile':'ios','action':'native','record':str(record),'config':config_ref,'source_capsule':capsule_ref})
    before={'synthetic_readonly_source':'exact'}
    m.save(record/'outcome.json',{'task':'T2','arm':'I','profile':'ios','action':'native','config':config_ref,'source_capsule':capsule_ref,
                                 'source_before':before,'source_after':before,'source_unchanged':True,'tool_root':str(tool)})
    original={'original_claim':m.ref(claimp),'original_outcome':m.ref(record/'outcome.json'),'original_config':config_ref,'original_source_capsule':capsule_ref,
              'envelope_request':m.ref(record/'envelope/request.json'),'envelope_result':m.ref(record/'envelope/result.json'),'positive_recovery_resources':m.ref(record/'envelope/error-recovery/resources.json')}
    names={'command':'command.json','sdk_observation':'sdk-observation.json','exception_log':'envelope/exception.log','envelope_result':'envelope/result.json','recovery_log':'envelope/recovery.log',
           'recovery_resources':'envelope/error-recovery/resources.json','recovery_journal':'envelope/error-recovery/resource-journal.json','recovery_events':'envelope/error-recovery/resource-events.jsonl'}
    target=evidence/'continuations/T2/I/ios/native'
    row={'original':original,'original_sidecars':{k:m.ref(record/relative) for k,relative in names.items()},'record':str(target)}
    auth=root/'AUTH.json';m.save(auth,{'synthetic':'authority'})
    return root,evidence,record,config_ref,capsule_ref,before,row,auth


class RunnerGuards(unittest.TestCase):
    def test_global_unique_envelope_leaf_for_same_record_basename(self):
        first=m.envelope_record(OUT/'T1/I/ios/native');second=m.envelope_record(OUT/'T2/I/ios/native')
        self.assertNotEqual(first.name,second.name)
        self.assertEqual(first,m.envelope_record(OUT/'T1/I/ios/native'))

    def test_all_scope_action_envelope_leaves_unique(self):
        records=[OUT/f'T{i}/{a}/{p}/{action}' for i in range(1,6) for a in ['A','B','I'] for p in ['ios','android'] for action in ['native','source','image','finish']]
        self.assertEqual(len({m.envelope_record(r).name for r in records}),len(records))

    def test_cleanup_bypasses_new_ui_envelope(self):
        env={'meter_path':'/synthetic/meter.py','meter_spec_path':'/synthetic/spec.json','path':'/synthetic/envelope.py'}
        command=m.forwarding_command(env,'/synthetic/tool',OUT/'config',OUT/'record',OUT/'service','cleanup-native-resources',[])
        self.assertNotIn('/synthetic/envelope.py',command)
        self.assertIn('/synthetic/tool/scripts/resource_manager.py',command)
        self.assertEqual(command[-1],'cleanup')

    def test_exact_original_zero_forwarding_allowed(self):
        f=fixture(self._testMethodName);m.verify_unforwarded(f[6],f[3],f[4])

    def test_even_empty_command_log_forbids_continuation(self):
        f=fixture(self._testMethodName);(f[2]/'envelope/command.log').write_text('')
        with self.assertRaises(ValueError):m.verify_unforwarded(f[6],f[3],f[4])

    def test_any_service_namespace_forbids_continuation(self):
        f=fixture(self._testMethodName);(f[2]/'service').mkdir()
        with self.assertRaises(ValueError):m.verify_unforwarded(f[6],f[3],f[4])

    def test_any_capture_or_cycle_forbids_continuation(self):
        f=fixture(self._testMethodName);p=f[2]/'outcome.json';v=m.load(p);v['capture']={'synthetic':'unknown-existing-capture'};p.chmod(0o644);p.write_text(json.dumps(v));f[6]['original']['original_outcome']=m.ref(p)
        with self.assertRaises(ValueError):m.verify_unforwarded(f[6],f[3],f[4])

    def test_original_sidecar_drift_rejected(self):
        f=fixture(self._testMethodName);p=f[2]/'sdk-observation.json';p.chmod(0o644);p.write_text('{"changed":true}')
        with self.assertRaises(ValueError):m.verify_unforwarded(f[6],f[3],f[4])

    def test_foreign_config_or_capsule_rejected(self):
        f=fixture(self._testMethodName)
        for config,capsule in [({'path':'/synthetic/foreign','sha256':'x'},f[4]),(f[3],{'path':'/synthetic/foreign','sha256':'x'})]:
            with self.assertRaises(ValueError):m.verify_unforwarded(f[6],config,capsule)

    def test_wrong_source_before_does_not_consume_continuation(self):
        f=fixture(self._testMethodName);authority={'scopes':{'T2/I/ios':f[6]}}
        with patch.object(m,'continuation_authority',return_value=(authority,m.ref(f[7]))),self.assertRaises(ValueError):
            m.reserve_continuation(f[0],f[1],'T2','I','ios',Path(f[6]['record']),f[3],f[4],{'different':'source'},f[7],m.sha(f[7]))
        self.assertFalse(m.continuation_claim_path(f[1],'T2','I','ios').exists())

    def test_continuation_claim_is_one_shot_and_old_claim_unchanged(self):
        f=fixture(self._testMethodName);before=m.sha(Path(f[6]['original']['original_claim']['path']));authority={'scopes':{'T2/I/ios':f[6]}}
        with patch.object(m,'continuation_authority',return_value=(authority,m.ref(f[7]))):
            m.reserve_continuation(f[0],f[1],'T2','I','ios',Path(f[6]['record']),f[3],f[4],f[5],f[7],m.sha(f[7]))
            with self.assertRaises(FileExistsError):m.reserve_continuation(f[0],f[1],'T2','I','ios',Path(f[6]['record']),f[3],f[4],f[5],f[7],m.sha(f[7]))
        self.assertEqual(before,m.sha(Path(f[6]['original']['original_claim']['path'])))

    def test_acquired_I1_scope_excluded(self):
        f=fixture(self._testMethodName)
        with patch.object(m,'continuation_authority',return_value=({'scopes':{}},m.ref(f[7]))),self.assertRaises(ValueError):
            m.reserve_continuation(f[0],f[1],'T1','I','ios',Path(f[6]['record']),f[3],f[4],f[5],f[7],m.sha(f[7]))

    def test_binding_only_registered_continuation_outcome(self):
        f=fixture(self._testMethodName);authority={'scopes':{'T2/I/ios':f[6]}};pin=m.ref(f[7]);target=Path(f[6]['record'])
        with patch.object(m,'continuation_authority',return_value=(authority,pin)):
            claim,original,_=m.reserve_continuation(f[0],f[1],'T2','I','ios',target,f[3],f[4],f[5],f[7],m.sha(f[7]))
            m.save(target/'service/capture/result.json',{'synthetic':'capture'});m.save(target/'service/cycle.json',{'synthetic':'cycle'})
            outcome={'task':'T2','arm':'I','profile':'ios','action':'native','config':f[3],'source_capsule':f[4],
                     'native_continuation_claim':claim,'original_zero_forwarding_outcome':original['original_outcome'],
                     'source_unchanged':True,'new_ui_acquisition':True,'capture_reused':False,
                     'capture':m.ref(target/'service/capture/result.json'),'cycle':m.ref(target/'service/cycle.json')}
            m.save(target/'outcome.json',outcome)
            value,_=m.native_reference(f[1],'T2','I','ios',f[3],f[4],target/'outcome.json',m.sha(target/'outcome.json'))
            self.assertEqual(value,outcome)
            with self.assertRaises(ValueError):m.native_reference(f[1],'T2','I','android',f[3],f[4],target/'outcome.json',m.sha(target/'outcome.json'))


class CollectorGuards(unittest.TestCase):
    def run_case(self,mode):
        root=OUT/('collector-'+mode);root.mkdir();evidence=root/'cache/business/independent-evaluation';coord=root/'operators/cohort2/coordination';coord.mkdir(parents=True)
        runner=coord/'independent_native_v2.py';runner.write_text('# synthetic; never executed')
        old_path=coord/'collect_independent.py';old_path.write_text('# synthetic; helpers explicitly mocked')
        order=[{'task':f'T{i}','scope':'I','profiles':['ios','android']} for i in range(1,6)]
        order += [{'task':t,'scope':a,'profiles':['ios','android']} for t,a in [('T1','A'),('T1','B'),('T2','B'),('T2','A'),('T3','A'),('T3','B'),('T4','B'),('T4','A'),('T5','A'),('T5','B')]]
        order_path=coord/'POST-PUBLIC-ACQUISITION-ORDER.json';c.save(order_path,{'episodes':order})
        initial=root/'cache/business/initial-reference/PREPARATION-SEAL.json';c.save(initial,{})
        monitor=root/'monitor';c.save(monitor/'READY.json',{'synthetic':True})
        scopes={}
        for item in order:
            t,a=item['task'],item['scope']
            if (t,a)==('T1','I'):continue
            ep=evidence/'episodes'/t/a;c.save(ep/'START.json',{'task':t,'arm':a,'started_at_monotonic':time.monotonic()-20,'started_at_unix':time.time()-20})
            c.save(ep/'END.json',{'finished_at_monotonic':time.monotonic()-10})
            for p in item['profiles']:scopes[t+'/'+a+'/'+p]={'record':str(evidence/f'continuations/{t}/{a}/{p}/native'),'original':{'original_config':{'path':str(root/'config')},'original_outcome':{'synthetic':'original'}}}
        auth=root/'AUTH.json';c.save(auth,{})
        authority={'initial_monitor_record':str(monitor),'scopes':scopes}
        fake_runner=types.SimpleNamespace(continuation_authority=lambda *a:(authority,c.ref(auth)),continuation_scope=m.continuation_scope,envelope_record=m.envelope_record)
        calls=[]
        if mode=='initial-halt':c.save(root/'operators/RESOURCE-HALT.json',{})
        if mode=='existing-record':Path(scopes['T2/I/ios']['record']).mkdir(parents=True)
        def execute(argv,**kwargs):
            if '--preflight' in argv:
                calls.append('preflight');c.save(monitor/'CLOSED.json',{'status':'failed','positive_idle':{'all_clear':False}});return subprocess.CompletedProcess(argv,0)
            action=argv[argv.index('--action')+1];calls.append(action);record=Path(argv[argv.index('--record')+1])
            if action=='cleanup-native-resources':
                c.save(record/'service/resources.json',{'final':True,'cleanup_errors':[],'remaining_directories':[],'remaining_devices':[]});return subprocess.CompletedProcess(argv,0)
            result={'source_unchanged':True,'new_ui_acquisition':True,'capture_reused':False}
            if mode not in ['no-capture','halt-needs-cleanup']:
                c.save(record/'service/capture/result.json',{'synthetic':True});c.save(record/'service/cycle.json',{'synthetic':True})
                result.update(capture=c.ref(record/'service/capture/result.json'),cycle=c.ref(record/'service/cycle.json'))
            if mode=='wrapper-exception':result['error']={'type':'SyntheticError','message':'retained'}
            if mode!='halt-needs-cleanup':c.save(record/'service/resources.json',{'final':True,'cleanup_errors':[],'remaining_directories':[],'remaining_devices':[]})
            c.save(record/'outcome.json',result)
            if mode in ['halt-after-native','halt-needs-cleanup']:c.save(root/'operators/RESOURCE-HALT.json',{})
            return subprocess.CompletedProcess(argv,0)
        argv=['test','--root',str(root),'--authority',str(auth),'--authority-sha256',c.sha(auth),'--monitor',str(monitor),'--runner-sha256',c.sha(runner)]
        def modules(path,name):return fake_runner if name=='explicit_zero_forward_runner_v2' else old
        with patch.object(sys,'argv',argv),patch.object(c,'module',side_effect=modules),patch.object(c,'OLD_COLLECTOR_SHA',c.sha(old_path)),patch.object(c,'ORDER_SHA',c.sha(order_path)),patch.object(c,'INITIAL_SHA',c.sha(initial)),patch.object(c.subprocess,'run',side_effect=execute),contextlib.redirect_stdout(io.StringIO()),self.assertRaises((ValueError,FileNotFoundError)):
            c.main()
        self.assertTrue((evidence/'continuation-collection/FAILED.json').is_file())
        return calls,root

    def test_no_capture_stops_without_retry_or_next_scope(self):self.assertEqual(self.run_case('no-capture')[0],['native'])
    def test_wrapper_exception_stops_without_retry(self):self.assertEqual(self.run_case('wrapper-exception')[0],['native'])
    def test_initial_halt_forwards_nothing(self):self.assertEqual(self.run_case('initial-halt')[0],[])
    def test_halt_after_native_forbids_next_item(self):self.assertEqual(self.run_case('halt-after-native')[0],['native'])
    def test_halt_does_not_block_needed_positive_cleanup(self):self.assertEqual(self.run_case('halt-needs-cleanup')[0],['native','cleanup-native-resources'])
    def test_existing_continuation_record_forbids_retry(self):self.assertEqual(self.run_case('existing-record')[0],[])
    def test_monitor_failure_forbids_all_final_hidden_UI(self):self.assertEqual(self.run_case('bad-monitor-close')[0],['native']*8+['preflight'])


if __name__=='__main__':
    stream=io.StringIO();suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(RunnerGuards),unittest.defaultTestLoader.loadTestsFromTestCase(CollectorGuards)])
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(OUT/'test.log').write_text(stream.getvalue())
    m.save(OUT/'RESULT.json',{'version':1,'kind':'author-synthetic-zero-forward-continuation-host','controls':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),
                            'actual_RUN_or_private_read':False,'SDK_or_native_execution':False,'runner_sha256':m.sha(HERE.parent/'independent_native_v2.py'),'collector_sha256':m.sha(HERE.parent/'collect_independent_v2.py')})
    print(stream.getvalue(),end='');print(json.dumps({'result':str(OUT/'RESULT.json'),'passed':result.wasSuccessful()}));raise SystemExit(0 if result.wasSuccessful() else 1)
