"""Synthetic operator-only guard controls. No actual RUN/private/SDK imports."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('post_barrier_runner',HERE.parent/'independent_native.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
HOST=HERE/'HOST'


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


class Controls(unittest.TestCase):
    def setUp(self):
        HOST.mkdir(exist_ok=True);self.root=Path(tempfile.mkdtemp(prefix='synthetic-',dir=HOST))
    def put(self,p,value):
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value if isinstance(value,bytes) else (json.dumps(value,sort_keys=True)+'\n').encode());return r.ref(p)
    def transcript(self):
        members={};events=[]
        for i in range(10):
            task='T'+str(i//2+1);arm='A' if i%2==0 else 'B';source=hashlib.sha256(str(i).encode()).hexdigest()
            events += [{'kind':'source_locked','sequence':2*i,'task':task,'arm':arm,'source_sha256':source},{'kind':'self_sealed','sequence':2*i+1,'task':task,'arm':arm,'source_sha256':source}]
            members[task+'/'+arm]={'path':'/SYNTHETIC/'+task+arm,'sha256':'a'*64,'source_sha256':source}
        cohort={'kind':'cohort_sealed','sequence':20,'members':members};auth={'kind':'hidden_authorized','sequence':21,'cohort_sha256':'b'*64}
        events += [cohort,auth,{'kind':'hidden_contexts_validated','sequence':22,'authorization_sequence':21}]
        return members,cohort,{'authorization':auth},events,list(members)
    def test_complete_barrier_and_wrong_member_source_or_order(self):
        args=self.transcript();r.validate_barrier(*args)
        bad=copy.deepcopy(args);bad[0]['T1/A']['source_sha256']='f'*64
        with self.assertRaises(ValueError):r.validate_barrier(*bad)
        bad=copy.deepcopy(args);bad[3][0]['sequence']=30
        with self.assertRaises(ValueError):r.validate_barrier(*bad)
    def test_duplicate_and_early_authorization_rejected(self):
        bad=copy.deepcopy(self.transcript());bad[3].append(copy.deepcopy(bad[2]['authorization']))
        with self.assertRaises(ValueError):r.validate_barrier(*bad)
        bad=copy.deepcopy(self.transcript());bad[2]['authorization']['sequence']=0;bad[3][21]['sequence']=0
        with self.assertRaises(ValueError):r.validate_barrier(*bad)
    def initial(self):
        base=self.root/'cache/business/initial-reference';tasks={}
        manifest={'tasks':[{'id':'T'+str(i),'arms':{'A':{'public_configs':{'ios':'unused','android':'unused'},'source_roots':[str(self.root/'final'/str(i)/'src')],'resource_roots':[str(self.root/'final'/str(i)/'resources')]}}} for i in range(1,6)]}
        for i in range(1,6):
            task='T'+str(i);tasks[task]={}
            source=self.put(base/task/'source-manifest.json',{'roots':[],'files':{},'content_sha256':'a'*64})
            for profile in ['ios','android']:
                config=self.put(base/task/'profiles'/(profile+'.json'),{'synthetic':True})
                tasks[task][profile]={'config':config,'source_manifest':source,'resource_root':str(base/task/'resources'/profile),'source_roots':[str(base/task/'workspace'/'src')]}
        seal=self.put(base/'PREPARATION-SEAL.json',{'version':1,'kind':'canonical-initial-reference-preparation','tasks':tasks})
        return manifest,seal
    def test_exact_initial_pins_and_new_resource_root(self):
        m,s=self.initial();entry,_=r.initial_entry(self.root,'T1','ios',m,Path(s['path']),s['sha256']);self.assertIn('initial-reference/T1/resources/ios',entry['resource_root'])
        document=r.load(s['path']);document['tasks']['T1']['ios']['resource_root']=m['tasks'][0]['arms']['A']['resource_roots'][0];s=self.put(Path(s['path']),document)
        with self.assertRaises(ValueError):r.initial_entry(self.root,'T1','ios',m,Path(s['path']),s['sha256'])
    def test_initial_source_must_not_overlap_final_or_evidence(self):
        m,s=self.initial();document=r.load(s['path']);document['tasks']['T1']['ios']['source_roots']=m['tasks'][0]['arms']['A']['source_roots'];s=self.put(Path(s['path']),document)
        with self.assertRaises(ValueError):r.initial_entry(self.root,'T1','ios',m,Path(s['path']),s['sha256'])
    def test_single_native_claim_cannot_be_retried_with_fresh_record(self):
        evidence=self.root/'evaluation';c={'path':'/CONFIG','sha256':'a'*64};source={'path':'/SOURCE','sha256':'b'*64}
        first=r.reserve_native(evidence,'T1','A','ios',evidence/'first',c,source)
        with self.assertRaises(FileExistsError):r.reserve_native(evidence,'T1','A','ios',evidence/'second',c,source)
        self.assertEqual(r.ref(Path(first['path'])),first)
    def native(self):
        evidence=self.root/'evaluation';record=evidence/'native-original'
        c=self.put(self.root/'config.json',{});source=self.put(self.root/'source.json',{})
        r.reserve_native(evidence,'T1','A','ios',record,c,source)
        capture=self.put(record/'service/capture/result.json',{'status':'verified_capture'});cycle=self.put(record/'service/cycle.json',{'status':'not_accepted'})
        value={'task':'T1','arm':'A','profile':'ios','action':'native','config':c,'source_capsule':source,'source_unchanged':True,'new_ui_acquisition':True,'capture_reused':False,'capture':capture,'cycle':cycle}
        outcome=self.put(record/'outcome.json',value)
        return evidence,record,c,source,value,outcome
    def test_only_registered_own_native_facts_can_be_bound(self):
        evidence,record,c,source,value,outcome=self.native()
        got,_=r.native_reference(evidence,'T1','A','ios',c,source,Path(outcome['path']),outcome['sha256']);self.assertEqual(got,value)
        value['arm']='B';outcome=self.put(record/'outcome.json',value)
        with self.assertRaises(ValueError):r.native_reference(evidence,'T1','A','ios',c,source,Path(outcome['path']),outcome['sha256'])
    def test_capture_cannot_point_outside_own_native_operation(self):
        evidence,record,c,source,value,_outcome=self.native();value['capture']=self.put(evidence/'foreign/capture.json',{})
        outcome=self.put(record/'outcome.json',value)
        with self.assertRaises(ValueError):r.native_reference(evidence,'T1','A','ios',c,source,Path(outcome['path']),outcome['sha256'])
    def test_original_symlink_target_is_not_chmod_or_followed(self):
        outside=self.root/'outside.txt';outside.write_bytes(b'not a service member');outside.chmod(0o644)
        service=self.root/'service';service.mkdir();(service/'normal.txt').write_bytes(b'original');(service/'link').symlink_to(outside)
        inventory,errors=r.preserve(service,self.root/'inventory.json')
        self.assertTrue(errors);self.assertEqual(stat.S_IMODE(outside.stat().st_mode),0o644)
        self.assertEqual(r.load(inventory['path'])[str(service/'link')]['kind'],'symlink')
        self.assertEqual(stat.S_IMODE((service/'normal.txt').stat().st_mode),0o444)
    def test_inventory_write_failure_is_retained_without_escaping_finally(self):
        service=self.root/'service';service.mkdir();(service/'original.txt').write_bytes(b'original');out=self.root/'inventory.json';out.write_text('{}')
        _inventory,errors=r.preserve(service,out);self.assertTrue(errors)
    def test_cleanup_command_bypasses_halt_gate_without_ui_launch(self):
        env={'path':'/FROZEN/native_envelope.py','meter_path':'/FROZEN/measure.py','meter_spec_path':'/FROZEN/spec.json'}
        command=r.forwarding_command(env,'/FROZEN/skill',self.root/'config.json',self.root/'record',self.root/'service','cleanup-native-resources',['UNUSED'])
        self.assertNotIn('/FROZEN/native_envelope.py',command);self.assertIn('/FROZEN/skill/scripts/resource_manager.py',command);self.assertEqual(command[-1],'cleanup')
    def test_closed_initial_monitor_allows_only_readonly_work(self):
        record=self.root/'monitor';r.save(record/'CLOSED.json',{'status':'closed','positive_idle':{'all_clear':True}});r.save(record/'EXTENDED-SPEC.json',{'groups':{'whole_study':{'resource_journals':[]}}})
        cmd,proof=r.monitor_gate(self.root,record,False);self.assertIsNone(cmd);self.assertTrue(proof)
        cmd,_proof=r.monitor_gate(self.root,record,True);self.assertIn('--preflight',cmd)
    def test_entry_failure_still_writes_timed_outcome_without_run_read(self):
        record=self.root/'cache/business/independent-evaluation/failed-admission'
        args=['independent_native.py','--root',str(self.root),'--task','T1','--arm','A','--profile','ios','--config',str(self.root/'not-read-private.json'),'--record',str(record),'--action','native']
        with patch.object(sys,'argv',args),contextlib.redirect_stdout(io.StringIO()):code=r.main()
        self.assertEqual(code,1);out=r.load(record/'outcome.json');self.assertFalse(out['accepted']);self.assertGreaterEqual(out['wall_seconds'],0);self.assertTrue((record/'ENTRY.json').is_file());self.assertTrue((record/'failure.json').is_file())
    def test_profile_guard_code_must_match_original_public_pin_before_import(self):
        run=self.root/'run';script=self.root/'guard.py';approval=self.put(self.root/'approval.json',{'approved':True});dep=self.put(self.root/'dependency.json',{})
        script.write_text('raise AssertionError("must not execute changed script")\n')
        hook={'script':str(script),'approval':approval['path'],'approval_sha256':digest({'approved':True}),'root':str(self.root),'dependencies':[dep['path']]}
        self.put(run/'arms/T1/A/public-inputs.json',{str(script):'0'*64,approval['path']:approval['sha256'],dep['path']:dep['sha256']})
        config=self.put(self.root/'config.json',{});helper=types.SimpleNamespace(domain=types.SimpleNamespace(platform=lambda _c:'ios'),digest=digest)
        with self.assertRaises(ValueError):r.profile_admission(run,'T1','A',{'profile_admissions':{'ios':hook}},Path(config['path']),helper,self.root/'admission.json')


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    HOST.mkdir(exist_ok=True)
    r.save(HOST/('RESULT-'+str(time.time_ns())+'.json'),{'version':1,'at_unix':time.time(),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'Author synthetic guard controls only. No actual RUN/private/config bodies, SDK, live forwarding or business quality claim. All local failure fixtures retained.'})
    raise SystemExit(not result.wasSuccessful())
