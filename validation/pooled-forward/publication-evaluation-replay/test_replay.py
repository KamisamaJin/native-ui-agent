"""Small synthetic original-fact replay controls; actual barrier remains open."""
import copy
import importlib.util
import json
from pathlib import Path
import time
import unittest

import replay as rp
import fixture_utils as fx


HERE=Path(__file__).resolve().parent;RUN=HERE/'HOST'/('replay-'+str(time.time_ns()));RUN.mkdir(parents=True,exist_ok=False)
for name in ['replay.py','runner/worker.py','fixture_utils.py','test_replay.py']:
    p=RUN/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((HERE/name).read_bytes())
RESULTS=[]


class Replay(unittest.TestCase):
    def setup_fixture(self,**kwargs):return fx.fixture(RUN/self.id().rsplit('.',1)[-1],**kwargs)
    def run_replay(self,f,ref,expected='verified',contains=None,**kwargs):
        i,w=fx.code_refs();r=rp.replay(f,ref,i,w,**kwargs)
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'expected':expected,'status':r['status'],'error':r.get('error'),
                        'backend':r.get('backend'),'counts':r.get('backend_results',{}).get('report',{}).get('counts'),
                        'current_source_delivery_verified':r['current_source_delivery_verified']})
        self.assertEqual(r['status'],expected,r)
        if contains:self.assertIn(contains,r['error']['message'])
        return r
    def reseal(self,f,packet):return f.put('/recorded/evaluator/PACKET.json',packet)

    def test_01_baseline_and_candidate_are_fresh_isolated_backends(self):
        f,p,packet=self.setup_fixture(backend='A');a=self.run_replay(f,p);self.assertEqual(a['backend_results']['report']['counts'],{'passed':6,'failed':0,'unassessed':0})
        packet['backend']='B';p=self.reseal(f,packet);b=self.run_replay(f,p)
        self.assertEqual(a['backend_results'],b['backend_results']);self.assertFalse(b['current_source_delivery_verified'])
        self.assertEqual(b['source_responsibility_replay'],'unsupported')

    def test_02_catalog_manual_and_report_exact_replay(self):
        f,p,packet=self.setup_fixture();first=self.run_replay(f,p)
        for role,value in first['backend_results'].items():
            if role not in {'catalog','manual','report'}:continue
            if role=='catalog':value={**value,'catalog_sha256':rp.digest(value)}
            packet['expected_artifacts'][role]=f.put('/recorded/evaluator/bound/'+role+'.json',value)
        second=self.run_replay(f,self.reseal(f,packet));self.assertEqual(set(second['comparisons']),{'catalog','manual','report'})

    def test_03_changed_png_bytes_fail_before_evaluation(self):
        f,p,packet=self.setup_fixture();target=f.physical/'recorded/evaluator/capture/native/observed.png';target.write_bytes(fx.png('#115522','#D6E8F3'))
        self.run_replay(f,p,'failed','Original pin differs')

    def test_04_missing_png_is_not_unknown_pass(self):
        f,p,packet=self.setup_fixture();(f.physical/'recorded/evaluator/capture/native/observed.png').unlink()
        self.run_replay(f,p,'failed','PNG inventory differs')

    def test_05_resealed_png_contradiction_remains_f(self):
        f,p,packet=self.setup_fixture();raw=fx.png('#115522','#D6E8F3');ref=f.put('/recorded/evaluator/capture/native/observed.png',raw)
        packet['image_hashes']['observed.png']=ref['sha256'];receipt=f.read_json(packet['capture_receipt']['path']);receipt['image_hashes']=packet['image_hashes']
        packet['capture_receipt']=f.put(packet['capture_receipt']['path'],receipt)
        r=self.run_replay(f,self.reseal(f,packet));self.assertEqual(r['backend_results']['report']['counts']['failed'],1)
        self.assertEqual(r['backend_results']['report']['status'],'failed')

    def test_06_unassessed_visual_actual_stays_u(self):
        f,p,packet=self.setup_fixture(mutation=('submission',lambda v:v['decisions'][0].update(actual=None)))
        r=self.run_replay(f,p);self.assertGreater(r['backend_results']['report']['counts']['unassessed'],0)
        self.assertFalse(r['backend_results']['report']['complete_requirements_claim'])

    def test_07_same_state_epochs_cannot_be_borrowed(self):
        def mutate(v):
            bad=copy.deepcopy(v['snapshots'][0]);bad['binding']['event_revision']=1;bad['binding_after_capture']=dict(bad['binding'])
            v['snapshots'].append(bad);v['state_captures'][0]['snapshot_indices']=[0,2]
        f,p,packet=self.setup_fixture(mutation=('observation',mutate));submission=f.read_json(packet['submission']['path'])
        submission['decisions']=[r for r in submission['decisions'] if r['snapshot_indices']==[1]]
        packet['submission']=f.put(packet['submission']['path'],submission)
        r=self.run_replay(f,self.reseal(f,packet));self.assertEqual(r['backend_results']['report']['counts'],{'passed':3,'failed':0,'unassessed':3})

    def test_08_cross_state_image_citation_rejected(self):
        f,p,packet=self.setup_fixture(mutation=('submission',lambda v:v['decisions'][0].update(snapshot_indices=[1])))
        self.run_replay(f,p,'failed','outside this exact input/action state')

    def test_09_actual_binding_must_name_original_observation(self):
        f,p,packet=self.setup_fixture(mutation=('submission',lambda v:v.update(observation_sha256='0'*64)))
        self.run_replay(f,p,'failed','another design, plan or native observation')

    def test_10_catalog_binding_cannot_be_replaced(self):
        f,p,packet=self.setup_fixture(mutation=('submission',lambda v:v.update(catalog_sha256='0'*64)))
        self.run_replay(f,p,'failed','another design, plan or native observation')

    def test_11_missing_original_catalog_cannot_fall_back(self):
        f,p,packet=self.setup_fixture();packet['expected_artifacts']['catalog']={'path':'/recorded/evaluator/missing-catalog.json','sha256':'0'*64}
        self.run_replay(f,self.reseal(f,packet),'failed','Synthetic original absent')

    def test_12_changed_catalog_values_are_rejected(self):
        f,p,packet=self.setup_fixture();r=self.run_replay(f,p);catalog=r['backend_results']['catalog'];catalog['rows'][0]['expected']=0
        packet['expected_artifacts']['catalog']=f.put('/recorded/evaluator/bound/catalog.json',catalog)
        self.run_replay(f,self.reseal(f,packet),'failed','Rebuilt catalog differs')

    def test_13_changed_original_report_is_not_rewritten(self):
        f,p,packet=self.setup_fixture();r=self.run_replay(f,p);report=r['backend_results']['report'];report['assertions'][0]['status']='failed'
        packet['expected_artifacts']['report']=f.put('/recorded/evaluator/bound/report.json',report)
        self.run_replay(f,self.reseal(f,packet),'failed','Rebuilt report differs')

    def test_14_changed_code_with_resealed_inventory_fails_frozen_pin(self):
        f,p,packet=self.setup_fixture();i,w=fx.code_refs();inventory=f.read_json(i['path']);inventory['backends']['A']['files']['scripts/native_checks.py']['sha256']='0'*64
        altered=f.put(i['path'],inventory);r=rp.replay(f,p,altered,w);self.assertEqual(r['status'],'failed');self.assertIn('exact frozen inventory',r['error']['message'])
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'status':r['status'],'expected':'failed','error':r['error']})

    def test_15_absent_code_file_is_rejected(self):
        f,p,packet=self.setup_fixture();old=f.read_bytes
        def missing(path):
            if str(path).endswith('/A/scripts/native_checks.py'):raise KeyError('Missing archived code file')
            return old(path)
        f.read_bytes=missing;self.run_replay(f,p,'failed','Missing archived code file')

    def test_16_source_domain_is_honestly_unsupported(self):
        f,p,packet=self.setup_fixture(mutation=('request',lambda v:v['input_hashes'].update({'coverage-domain-prepared.json':'0'*64})))
        r=self.run_replay(f,p,'unsupported');self.assertTrue(r['provenance_bytes_verified']);self.assertNotIn('backend_results',r)

    def test_17_no_actual_data_or_report_access_before_cause_barrier(self):
        f,p,packet=self.setup_fixture(mutation=('packet',lambda v:v.update(data_scope='actual-after-all30-cause')));f.reads=[]
        self.run_replay(f,p,'failed','blocked until root supplies verified ALL30 CAUSE')
        self.assertEqual(f.reads,[p['path']])

    def test_18_synthetic_label_rejects_live_keys(self):
        f,p,packet=self.setup_fixture();packet['observation']['path']='/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward/cache/business/independent-evaluation/forbidden/observation.json'
        self.run_replay(f,self.reseal(f,packet),'failed','Synthetic mode rejects actual study keys')

    def test_19_traversal_png_path_rejected(self):
        f,p,packet=self.setup_fixture(mutation=('observation',lambda v:v['snapshots'][0].update(screenshot='../outside.png')))
        self.run_replay(f,p,'failed','Unsafe relative member')

    def test_20_original_receipt_substitution_rejected(self):
        f,p,packet=self.setup_fixture();receipt=f.read_json(packet['capture_receipt']['path']);receipt['observation_sha256']='0'*64
        packet['capture_receipt']=f.put(packet['capture_receipt']['path'],receipt)
        self.run_replay(f,self.reseal(f,packet),'failed','request/receipt/plan/native/image binding')

    def test_21_real_resolver_with_absent_original_data_paths(self):
        f,p,packet=self.setup_fixture();mapping,map_sha,index_sha=f.restore(RUN/'virtual-restore')
        spec=importlib.util.spec_from_file_location('replay_frozen_resolver',HERE/'vendor/resolver.py');rm=importlib.util.module_from_spec(spec);spec.loader.exec_module(rm)
        reader=rm.Resolver(mapping,map_sha256=map_sha,index_sha256=index_sha);i,w=fx.code_refs();r=rp.replay(reader,p,i,w)
        self.assertEqual(r['status'],'verified',r);self.assertFalse(Path('/recorded/evaluator').exists())
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'expected':'verified','status':r['status'],'map_sha256':map_sha,'index_sha256':index_sha,'original_data_paths_exist':False})

    def test_22_actual_only_submission_cannot_override_expected(self):
        f,p,packet=self.setup_fixture(mutation=('submission',lambda v:v['decisions'][0].update(expected=True)))
        self.run_replay(f,p,'failed','Submit only rule identity, actual proposition')

    def test_23_code_inventory_external_pin_is_required(self):
        f,p,packet=self.setup_fixture();i,w=fx.code_refs();i={**i,'sha256':'0'*64};r=rp.replay(f,p,i,w)
        self.assertEqual(r['status'],'failed');self.assertIn('Original pin differs',r['error']['message'])
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'expected':'failed','status':r['status'],'error':r['error']})


def main():
    with (RUN/'RUN.log').open('w') as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Replay))
    value={'kind':'independent-synthetic-original-fact-replay-controls','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'passed':r.wasSuccessful(),
           'controls':RESULTS,'code_pins':{n:rp.sha((RUN/n).read_bytes()) for n in ['replay.py','runner/worker.py','fixture_utils.py','test_replay.py']},
           'actual_product_grade_alarm_mapping_data_read':False,'actual_dataset_application_performed':False,'SDK_or_device_commands':False,
           'scope':'Synthetic native/visual backend replay only; no source responsibility or delivery success credit.'}
    p=RUN/'RESULT.json';p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');print(json.dumps({'path':str(p),'sha256':rp.sha(p.read_bytes()),'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors)}))
    return 0 if r.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
