import copy,hashlib,importlib.util,json,sys,types,unittest,traceback
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
SOURCE=Path(sys.argv[1])if len(sys.argv)>1 else ROOT/'snapshots/verify_publication_v2.py'
RUN=ROOT/'results'/('v3'if'revision-v3'in str(SOURCE)else'v2');RUN.mkdir()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
subject=load(SOURCE,'isolated_publication_consumer');metric=load(ROOT/'snapshots/metric_rules_v3.py','fixed_pure_metric_v3')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()

class Fixture:
    def __init__(self,folder):
        folder.mkdir();self.folder=folder;self.data={};self.events=[];self.closed=False
        def put(path,value):
            raw=encoded(value);self.data[path]=raw;return{'path':path,'sha256':sha(raw)}
        self.put=put
        groups=['Case%02d-%s'%(i,v)for i in range(1,6)for v in ['I','X','Y']]
        rows=[{'group':g,'seals':{j:{'path':'/synthetic/roles/'+g+'/'+j+'/cause/SEAL.json','sha256':sha((g+j+'cause').encode())}for j in ['J1','J2']}}for g in groups]
        causes=put('/synthetic/CAUSE.json',{'groups':rows})
        alarmrows=copy.deepcopy(rows)
        for row in alarmrows:
            for j in row['seals']:row['seals'][j]={'path':row['seals'][j]['path'].replace('/cause/','/alarm/'),'sha256':sha((row['group']+j+'alarm').encode())}
        alarms=put('/synthetic/ALARM.json',{'groups':alarmrows,'first_cause_barrier':causes})
        self.consensus=folder/'consensus';self.consensus.mkdir();body=b'{"synthetic_consensus":true}\n';(self.consensus/'consensus.json').write_bytes(body)
        self.data[str(self.consensus/'consensus.json')]=body
        correspondence=put(str(self.consensus/'SEAL.json'),{'version':1,'kind':'independent-anonymous-correspondence-seal','files':{'consensus.json':sha(body)}})
        (self.consensus/'SEAL.json').write_bytes(self.data[correspondence['path']])
        index=put('/synthetic/INDEX.json',{'version':1,'kind':'neutral-all15-correspondence-input','groups':[{'group':g,'judges':{j:{'effective_cause':rows[i]['seals'][j],'alarm':alarmrows[i]['seals'][j]}for j in ['J1','J2']}}for i,g in enumerate(groups)]})
        self.start=put('/synthetic/START.json',{'version':1,'kind':'independent-anonymous-correspondence-start','operator_barriers':{'cause':causes,'alarm':alarms},'index':index,'output':str(self.consensus),'quality_adjudicated':False,'mapping_revealed':False})
        self.mapping={f'Case0{i}':{'task':'T'+str([3,1,5,2,4][i-1]),'X':'A'if i%2 else'B','Y':'B'if i%2 else'A'}for i in range(1,6)}
        mapped=put('/synthetic/map/MAPPING.json',{'mapping':self.mapping})
        self.map_seal=put('/synthetic/map/SEAL.json',{'files':{'MAPPING.json':mapped['sha256']}})
        self.assignment={case:{row[v]:v for v in ['X','Y']}for case,row in self.mapping.items()}
        inputs={'cause_index':causes,'alarm_index':alarms,'correspondence_seal':correspondence}
        reveal=put('/synthetic/REVEAL.json',{'version':1,'kind':'after-consensus-assignment-reveal',**inputs,'mapping_seal':self.map_seal,'mapping':mapped,'assignment':self.assignment})
        coverage=put('/synthetic/COVERAGE.json',{'coverage_denominators':{'synthetic-fixed-id':['obligation-1']}})
        mi=put('/synthetic/METRIC-INPUT.json',{'version':1,'kind':'sealed-five-case-metric-input','assignment':self.assignment,'cases':[],'shared_costs':{},'coverage_denominators':{'synthetic-fixed-id':['obligation-1']},'provenance':{'correspondence_seal':correspondence,'mapping_reveal':reveal,'coverage_registry':coverage}})
        self.calculated={'version':3,'counts':{'initial':1},'attempt_records':[{'complete_delivery':False}]}
        mr=put('/synthetic/METRIC-RESULT.json',{'version':1,'kind':'five-case-fixed-metric-results','arms':{a:copy.deepcopy(self.calculated)for a in ['A','B']}})
        inputs.update(mapping_reveal=reveal,coverage_registry=coverage,metric_inputs=mi,metric_results=mr)
        if 'matcher_start'in subject.INPUT_KEYS:inputs['matcher_start']=self.start
        self.inputs=inputs;self.plan=put('/synthetic/PLAN.json',{'study_root':'/synthetic/study'})
        self.manifest={'version':1,'kind':'pooled-forward-published-study','study_closed':True,'cleanup_closed':False,'code':{k:{'path':k+'.py','sha256':'0'*64}for k in subject.CODE_KEYS},'inputs':inputs,'preservation_plan':self.plan,'main_transport':'main','transports':[{'id':'main','directory':'synthetic-transport','transport_sha256':'1'*64,'index_sha256':'2'*64,'restore':True}]}
        fixture=self
        class Reader:
            def __init__(self,*a,**kw):fixture.events.append('reader')
            def read_bytes(self,path):return fixture.data[path]
            def directory(self,path):
                if path!=str(fixture.consensus):raise AssertionError('No original fallback or real namespace')
                return fixture.consensus
            def verify_all(self):fixture.events.append('all-payload-hash');return len(fixture.data)
            def close(self):fixture.closed=True;fixture.events.append('close')
        self.Reader=Reader
        def restore(target,out,index,readonly):
            assert readonly is True;out.mkdir();m=out/'RESTORED-MAP.json';m.write_bytes(b'{"synthetic_only":true}\n');return{'mapping':str(m),'index_sha256':index}
        phase=types.SimpleNamespace(verify_index=lambda r,ref,kind:{'distinct_contexts':30},original=lambda r,ref:subject.pinned(r,ref))
        self.modules={'anonymous_projection':types.SimpleNamespace(),'session':types.SimpleNamespace(MapSessionReader=Reader),
          'published_archive':types.SimpleNamespace(verify=lambda *a:{'synthetic':True},restore=restore),
          'published_cold':types.SimpleNamespace(decode=lambda *a:{'synthetic':True}),'published_preserve':types.SimpleNamespace(),
          'published_phase':phase,'published_metric':types.SimpleNamespace(summarize=lambda *a,**kw:copy.deepcopy(fixture.calculated)),
          'published_session_replay':types.SimpleNamespace(replay=lambda *a:{'synthetic_orchestration_only':True,'status':'verified'})}
    def update(self,key,value):self.inputs[key]=self.put(self.inputs[key]['path'],value)
    def run(self):
        output=self.folder/'output';output.mkdir()
        (self.folder/'INPUTS.json').write_bytes(encoded({'manifest':self.manifest,'synthetic_original_bytes':{k:v.decode()for k,v in self.data.items()},'authority_patch':'Only synthetic genuine SHA constants; never real mapping authority or frozen registry'}))
        with patch.object(subject,'code_module',side_effect=lambda reference,name:self.modules[name]),patch.object(subject,'MAPPING_SEAL_SHA',self.map_seal['sha256']),patch.object(subject,'COVERAGE_SHA',self.inputs['coverage_registry']['sha256']):
            return subject.verify(self.manifest,output)

class Controls(unittest.TestCase):
    def fixture(self):return Fixture(RUN/self._testMethodName)
    def test_01_small_orchestration_preserves_precleanup_false_and_fullpayload_end(self):
        f=self.fixture();result=f.run();self.assertEqual(result['status'],'verified');self.assertIs(result['current_source_delivery_verified'],False);self.assertEqual(f.events[-2:],['all-payload-hash','close']);self.assertIs(f.manifest['cleanup_closed'],False)
    def test_02_metric_bool_number_substitution_must_not_count_as_identical(self):
        f=self.fixture();stored=subject.pinned(f.Reader(),f.inputs['metric_results']);stored['arms']['A']['attempt_records'][0]['complete_delivery']=0;stored['arms']['A']['counts']['initial']=True;f.update('metric_results',stored)
        with self.assertRaisesRegex(ValueError,'Fixed metric replay differs'):f.run()
    def test_03_unrelated_matcher_output_must_not_be_accepted(self):
        f=self.fixture();start=subject.pinned(f.Reader(),f.start);start['output']=str(f.folder/'other-consensus');changed=f.put(f.start['path'],start)
        if 'matcher_start'in subject.INPUT_KEYS:f.inputs['matcher_start']=changed
        with self.assertRaisesRegex(ValueError,'consensus output'):f.run()
    def test_04_duplicate_key_and_nonfinite_metadata_reject(self):
        for i,raw in enumerate([b'{"version":1,"version":2}',b'{"value":NaN}',b'{"value":Infinity}']):
            class Reader:
                def read_bytes(self,path):return raw
            with self.subTest(case=i),self.assertRaises(ValueError):subject.pinned(Reader(),{'path':'/synthetic/metadata','sha256':sha(raw)})
    def test_05_reveal_inverse_and_fixed_authority_controls(self):
        f=self.fixture();reader=f.Reader();reveal=subject.pinned(reader,f.inputs['mapping_reveal'])
        with patch.object(subject,'MAPPING_SEAL_SHA',f.map_seal['sha256']):
            self.assertEqual(subject.revealed_assignment(reader,reveal,f.inputs),f.assignment)
            wrong=copy.deepcopy(reveal);wrong['assignment']['Case01']={'A':'Y','B':'X'}
            with self.assertRaisesRegex(ValueError,'inverts'):subject.revealed_assignment(reader,wrong,f.inputs)
        with patch.object(subject,'MAPPING_SEAL_SHA','f'*64):
            with self.assertRaisesRegex(ValueError,'authority differs'):subject.revealed_assignment(reader,reveal,f.inputs)
    def test_06_duplicate_task_and_changed_mapping_pin_fail(self):
        f=self.fixture();reader=f.Reader();value=copy.deepcopy(f.mapping);value['Case02']['task']=value['Case01']['task'];mapping=f.put('/synthetic/map/MAPPING.json',{'mapping':value});seal=f.put('/synthetic/map/SEAL.json',{'files':{'MAPPING.json':mapping['sha256']}})
        reveal=subject.pinned(reader,f.inputs['mapping_reveal']);reveal.update(mapping=mapping,mapping_seal=seal)
        with patch.object(subject,'MAPPING_SEAL_SHA',seal['sha256']):
            with self.assertRaisesRegex(ValueError,'paired original task'):subject.revealed_assignment(reader,reveal,f.inputs)
        reveal['mapping']['sha256']='f'*64
        with patch.object(subject,'MAPPING_SEAL_SHA',seal['sha256']):
            with self.assertRaises(ValueError):subject.revealed_assignment(reader,reveal,f.inputs)
    def test_07_real_v3_partition_gate_keeps_unknown_and_not_applicable_separate(self):
        registry=[];rows=[]
        for platform in ['ios','android']:
            for family in ['public_native_image','private_native_image','source']:
                ids=[platform+'/'+family+'/must'];na=[platform+'/'+family+'/NA'];e=[{'synthetic':'predeclared'}]
                registry.append({'platform':platform,'state':'synthetic','family':family,'applicable_ids':ids,'not_applicable_ids':na,'evidence':e})
                rows.append({'platform':platform,'state':'synthetic','family':family,'frozen_applicable_ids':ids,'passed_ids':[],'failed_ids':[],'unassessed_ids':ids,'not_applicable_ids':na,'denominator_evidence':e})
        result=metric.coverage({'mandatory_coverage':rows},registry);self.assertEqual(result['counts']['unassessed'],6);self.assertEqual(result['counts']['not_applicable'],6);self.assertFalse(result['complete'])
        rows[0]['passed_ids']=rows[0]['unassessed_ids']
        with self.assertRaisesRegex(ValueError,'partitioned exactly'):metric.coverage({'mandatory_coverage':rows},registry)
    def test_08_matcher_barrier_and_original_role_join_fail_closed(self):
        if not hasattr(subject,'matcher_binding'):self.skipTest('v2 has no matcher join; reproduced by test03')
        for field in ['barrier','role','groups']:
            f=self.fixture()if field=='barrier'else Fixture(RUN/(self._testMethodName+'-'+field));start=subject.pinned(f.Reader(),f.start)
            if field=='barrier':start['operator_barriers']['cause']=dict(f.inputs['cause_index'],sha256='f'*64)
            else:
                index=subject.pinned(f.Reader(),start['index'])
                if field=='role':index['groups'][0]['judges']['J1']['alarm']['sha256']='f'*64
                else:index['groups'].pop()
                start['index']=f.put(start['index']['path'],index)
            f.inputs['matcher_start']=f.put(f.start['path'],start)
            with self.subTest(case=field),self.assertRaises(ValueError):f.run()
    def test_09_metric_denominator_cannot_differ_from_frozen_registry(self):
        f=self.fixture();value=subject.pinned(f.Reader(),f.inputs['metric_inputs']);value['coverage_denominators']={'foreign':[]};f.update('metric_inputs',value)
        with self.assertRaisesRegex(ValueError,'applicability differs'):f.run()

class Recorded(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.rows=[]
    def addSuccess(self,t):super().addSuccess(t);self.rows.append({'test':t.id(),'status':'pass'})
    def addSkip(self,t,why):super().addSkip(t,why);self.rows.append({'test':t.id(),'status':'skip','why':why})
    def addFailure(self,t,e):super().addFailure(t,e);self.rows.append({'test':t.id(),'status':'fail','traceback':''.join(traceback.format_exception(*e))})
    def addError(self,t,e):super().addError(t,e);self.rows.append({'test':t.id(),'status':'error','traceback':''.join(traceback.format_exception(*e))})
result=unittest.TextTestRunner(verbosity=2,resultclass=Recorded).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
report={'version':1,'tests':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'controls':result.rows,'source_sha256':sha(SOURCE.read_bytes()),'test_sha256':sha(Path(__file__).read_bytes()),'actual_data_access':False,'scope':'Small fake pure-stage orchestrator/reader with real SHA synthetic assignment authority; real frozenv3 coverage function. Not full cohort/archive replay; constants patched only inside synthetic test.'}
(RUN/'RESULT.json').write_bytes(encoded(report));sys.exit(not result.wasSuccessful())
