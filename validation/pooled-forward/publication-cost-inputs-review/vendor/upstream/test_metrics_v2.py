"""Independent synthetic reproductions of frozen v1 metric limitations."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import unittest

import metric_rules_v2 as v2
import replay as rp


HERE=Path(__file__).resolve().parent;RUN=HERE/'HOST'/('metrics-'+str(time.time_ns()));RUN.mkdir(parents=True,exist_ok=False)
for name in ['metric_rules_v2.py','test_metrics_v2.py']:(RUN/name).write_bytes((HERE/name).read_bytes())
spec=importlib.util.spec_from_file_location('frozen_metric_v1',HERE/'vendor/original-metrics/metric_rules.py');v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1)
RESULTS=[]


def fixture():
    cases=[];assignment={};registries={}
    evidence=[{'path':'/recorded/frozen-applicability.json','sha256':'a'*64}]
    for i in range(1,6):
        key=f'Case0{i}';assignment[key]={'A':'X','B':'Y'};coverage=[];frozen=[]
        for platform in ['ios','android']:
            for family in ['public_native_image','private_native_image','source']:
                uid=platform+'/'+family+'/required';na=platform+'/'+family+'/explicit-na'
                coverage.append({'platform':platform,'state':'ready','family':family,'frozen_applicable_ids':[uid],
                    'passed_ids':[uid],'failed_ids':[],'unassessed_ids':[],'not_applicable_ids':[na],'denominator_evidence':evidence})
                frozen.append({'platform':platform,'state':'ready','family':family,'applicable_ids':[uid],'not_applicable_ids':[na],'evidence':evidence})
        version={'initial_relations':[],'defect_alarms':[],'attempted_repairs':[],'new_regressions':[],'unresolved_regressions':[],
                 'positive_validation_claims':[],'unresolved_quality':[],'public_wall_seconds':i*10,'hidden_validation_wall_seconds':3,
                 'delivery_obligations':{k:True for k in v2.GATES},'mandatory_coverage':coverage}
        cases.append({'case_id':key,'confirmed_initial_causes':[],'versions':{'X':copy.deepcopy(version),'Y':copy.deepcopy(version)}})
        registries[key]={'X':copy.deepcopy(frozen),'Y':copy.deepcopy(frozen)}
    shared={k:0 for k in ['initial_oracle_seconds','design_preparation_seconds','common_infrastructure_seconds','independent_grading_matcher_seconds']}
    return cases,assignment,registries,shared


def cause(cases,status='present'):
    cases[0]['confirmed_initial_causes']=[{'id':'initial-a'}]
    final=cases[0]['versions']['X'];final['initial_relations']=[{'initial_cause_id':'initial-a','status':status,'evidence':['synthetic sealed native/source evidence']}]
    return final


def provenance(phase):return {'phase':phase,'source_version':'b'*64,'evidence':[{'path':'/recorded/original-public-or-private-record.json','sha256':'c'*64}]}


class Metrics(unittest.TestCase):
    def run_v2(self,f):
        c,m,r,s=f;return v2.summarize(c,'A',m,shared_costs=s,coverage_denominators=r)
    def preserve(self,label,fixture,result):
        c,m,r,s=fixture
        p=RUN/(label+'-inputs.json');p.write_text(json.dumps({'cases':c,'synthetic_assignment':m,'frozen_coverage_denominators':r,'shared_costs':s},indent=2,sort_keys=True)+'\n')
        out=RUN/(label+'-v1-result.txt');out.write_text(repr(result)+'\n')
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'synthetic_only':True,'inputs':{'path':str(p),'sha256':rp.sha(p.read_bytes())},
                        'frozen_v1_result_repr':{'path':str(out),'sha256':rp.sha(out.read_bytes())}})

    def test_01_frozen_v1_author_tests_reproduce(self):
        p=subprocess.run([sys.executable,'-B',str(HERE/'vendor/original-metrics/test_metric_rules.py')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False)
        (RUN/'frozen-v1-tests.log').write_bytes(p.stdout);self.assertEqual(p.returncode,0,p.stdout.decode());self.assertIn(b'Ran 11 tests',p.stdout)
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True,'frozen_v1_tests':11})

    def test_02_zero_denominators_na_and_five_attempts(self):
        result=self.run_v2(fixture());self.assertIsNone(result['repair_fraction']['value']);self.assertIsNone(result['false_discovery_fraction']['value'])
        self.assertEqual(result['attempts'],5);self.assertEqual(result['mandatory_coverage']['counts']['applicable'],30)
        self.assertEqual(result['mandatory_coverage']['counts']['not_applicable'],30)

    def test_03_hidden_alarm_v1_wrongly_earns_worker_detection(self):
        f=fixture();v=cause(f[0]);v['defect_alarms']=[{'id':'hidden','verdict':'true','initial_cause_ids':['initial-a'],
            'worker_visible':False,'provenance':provenance('independent_private_after_seal')}]
        old=v1.summarize(f[0],'A',f[1]);self.assertEqual(old['initial_detection_fraction']['value'],1);self.preserve('hidden-detection',f,old)
        new=self.run_v2(f);self.assertEqual(new['initial_detection_fraction']['value'],0)
        self.assertEqual(new['alarm_by_phase']['independent_private_after_seal']['adjudicated_denominator'],1)
        self.assertEqual(new['alarm_by_phase']['worker_public']['adjudicated_denominator'],0)

    def test_04_visible_public_alarm_can_earn_detection(self):
        f=fixture();v=cause(f[0]);v['defect_alarms']=[{'id':'public','verdict':'true','initial_cause_ids':['initial-a'],
            'worker_visible':True,'provenance':provenance('worker_public')}]
        self.assertEqual(self.run_v2(f)['initial_detection_fraction']['value'],1)

    def test_05_visibility_requires_boolean_and_source_pin(self):
        for visibility in [None,0,1,'true']:
            f=fixture();v=cause(f[0]);v['defect_alarms']=[{'id':'a','verdict':'true','initial_cause_ids':['initial-a'],
                'worker_visible':visibility,'provenance':provenance('worker_public')}]
            with self.assertRaisesRegex(ValueError,'Boolean worker_visible'):self.run_v2(f)
        f=fixture();v=cause(f[0]);p=provenance('worker_public');p['source_version']='initial'
        v['defect_alarms']=[{'id':'a','verdict':'true','initial_cause_ids':['initial-a'],'worker_visible':True,'provenance':p}]
        with self.assertRaisesRegex(ValueError,'source-version'):self.run_v2(f)

    def test_06_hidden_repair_cannot_be_worker_attempt(self):
        f=fixture();v=cause(f[0],'removed');v['attempted_repairs']=[{'id':'r','initial_cause_ids':['initial-a'],'evidence':['synthetic independent final validation'],
              'worker_visible':False,'provenance':provenance('independent_private_after_seal')}]
        old=v1.summarize(f[0],'A',f[1]);self.assertEqual(old['attempted_repair_fraction']['value'],1);self.preserve('hidden-repair',f,old)
        with self.assertRaisesRegex(ValueError,'worker-public action'):self.run_v2(f)

    def test_07_unknown_alarm_denominator_stays_separate(self):
        f=fixture();v=cause(f[0]);v['defect_alarms']=[{'id':name,'verdict':verdict,'initial_cause_ids':['initial-a'] if verdict=='true' else [],
            'worker_visible':True,'provenance':provenance('worker_public')} for name,verdict in [('t','true'),('f','false'),('u','unresolved')]]
        r=self.run_v2(f);self.assertEqual(r['false_discovery_fraction']['value'],.5);self.assertEqual(r['alarm_unadjudicated_denominator'],1)
        self.assertEqual(r['unadjudicated_alarm_fraction'],{'numerator':1,'denominator':3,'value':1/3})

    def test_08_mandatory_u_v1_is_unreported_and_can_be_concealed(self):
        f=fixture();row=f[0][0]['versions']['X']['mandatory_coverage'][0];uid=row['passed_ids'].pop();row['unassessed_ids']=[uid]
        old=v1.summarize(f[0],'A',f[1]);self.assertEqual(old['counts']['delivered'],5);self.assertNotIn('mandatory_coverage',old);self.preserve('concealed-mandatory-u',f,old)
        with self.assertRaisesRegex(ValueError,'contradicts frozen mandatory F/U'):self.run_v2(f)
        f[0][0]['versions']['X']['delivery_obligations']['public_current_all_must_passed']=False
        r=self.run_v2(f);self.assertEqual(r['counts']['delivered'],4);self.assertEqual(r['mandatory_coverage']['unassessed_fraction']['numerator'],1)
        self.assertEqual(r['mandatory_coverage']['unassessed_fraction']['denominator'],30)

    def test_09_changed_denominator_is_rejected(self):
        f=fixture();row=f[0][0]['versions']['X']['mandatory_coverage'][0];row['frozen_applicable_ids']=[];row['passed_ids']=[]
        with self.assertRaisesRegex(ValueError,'separately frozen applicability'):self.run_v2(f)

    def test_10_omitted_frozen_state_is_rejected(self):
        f=fixture();new=copy.deepcopy(f[2]['Case01']['X'][0]);new['state']='another-state';f[2]['Case01']['X'].append(new)
        with self.assertRaisesRegex(ValueError,'Every frozen platform/state'):self.run_v2(f)

    def test_11_na_never_enters_pass_numerator(self):
        f=fixture();row=f[0][0]['versions']['X']['mandatory_coverage'][0];row['passed_ids'].append(row['not_applicable_ids'][0])
        with self.assertRaisesRegex(ValueError,'N/A cannot become pass'):self.run_v2(f)

    def test_12_aggregate_overflow_v1_is_not_finite(self):
        f=fixture()
        for row in f[0]:row['versions']['X']['public_wall_seconds']=1e308
        old=v1.summarize(f[0],'A',f[1]);self.assertTrue(math.isinf(old['cost']['all_attempt_public_seconds']));self.preserve('aggregate-cost-overflow',f,old)
        with self.assertRaisesRegex(ValueError,'Aggregate cost'):self.run_v2(f)

    def test_13_all_failed_attempt_costs_remain(self):
        f=fixture()
        for row in f[0][1:]:row['versions']['X']['delivery_obligations']['independent_quality_complete']=False
        f[3]['initial_oracle_seconds']=123;r=self.run_v2(f)
        self.assertEqual(r['cost']['successful_delivery_seconds'],150);self.assertEqual(r['cost']['combined_successful_delivery_seconds'],165)
        self.assertEqual(r['cost']['shared_cost_total_seconds'],123);self.assertEqual(r['complete_delivery_fraction']['denominator'],5)

    def test_14_zero_delivery_cost_na(self):
        f=fixture()
        for row in f[0]:row['versions']['X']['delivery_obligations']['owned_resources_closed']=False
        self.assertIsNone(self.run_v2(f)['cost']['successful_delivery_seconds'])

    def test_15_unknown_cause_is_not_removed_or_delivery(self):
        f=fixture();cause(f[0],'unresolved');r=self.run_v2(f)
        self.assertEqual(r['repair_fraction']['value'],0);self.assertEqual(r['unresolved_initial_relation_fraction']['value'],1);self.assertEqual(r['counts']['delivered'],4)

    def test_16_removed_without_detection_stays_removed(self):
        f=fixture();cause(f[0],'removed');r=self.run_v2(f)
        self.assertEqual(r['repair_fraction']['value'],1);self.assertEqual(r['initial_detection_fraction']['value'],0)

    def test_17_postseal_cannot_be_marked_visible(self):
        f=fixture();v=cause(f[0]);v['defect_alarms']=[{'id':'a','verdict':'true','initial_cause_ids':['initial-a'],
                'worker_visible':True,'provenance':provenance('independent_private_after_seal')}]
        with self.assertRaisesRegex(ValueError,'cannot be worker-visible'):self.run_v2(f)

    def test_18_invalid_clocks_and_shared_categories_rejected(self):
        for bad in [True,-.1,float('nan'),float('inf')]:
            f=fixture();f[0][0]['versions']['X']['public_wall_seconds']=bad
            with self.assertRaises(ValueError):self.run_v2(f)
        f=fixture();f[3].pop('initial_oracle_seconds')
        with self.assertRaisesRegex(ValueError,'shared cost categories'):self.run_v2(f)

    def test_19_null_quality_inventory_cannot_mean_complete(self):
        f=fixture();f[0][0]['versions']['X']['unresolved_quality']=None
        old=v1.summarize(f[0],'A',f[1]);self.assertEqual(old['counts']['delivered'],5);self.preserve('null-quality-inventory',f,old)
        with self.assertRaisesRegex(ValueError,'null is not complete'):self.run_v2(f)


def main():
    with (RUN/'RUN.log').open('w') as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Metrics))
    value={'kind':'independent-synthetic-metric-rule-validation','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'passed':r.wasSuccessful(),
           'reproductions':RESULTS,'actual_product_grade_alarm_mapping_data_read':False,'code_pins':{n:rp.sha((RUN/n).read_bytes()) for n in ['metric_rules_v2.py','test_metrics_v2.py']},
           'frozen_v1_sha256':rp.sha((HERE/'vendor/original-metrics/metric_rules.py').read_bytes()),'fixed_spec_sha256':rp.sha((HERE/'vendor/BUSINESS-METRICS.md').read_bytes())}
    p=RUN/'RESULT.json';p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');print(json.dumps({'path':str(p),'sha256':rp.sha(p.read_bytes()),'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors)}))
    return 0 if r.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
