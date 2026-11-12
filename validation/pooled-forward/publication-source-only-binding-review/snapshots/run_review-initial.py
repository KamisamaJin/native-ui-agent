import copy,hashlib,importlib.util,json,sys,tempfile,traceback,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
sys.path.insert(0,str(PROJECT/'native-ui-agent/tests'))
sys.path.insert(0,str(PROJECT/'validation/pooled-forward/operators'))
import test_managed_execution as fixtures
import test_source_only_binding as author

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
original=load(ROOT/'snapshots/source_only_binding.py','independent_original_binding')
TARGET=Path(sys.argv[1])if len(sys.argv)>1 else ROOT/'snapshots/source_only_binding.py'
RUN=ROOT/'results'/('v2'if 'revision-v2'in str(TARGET)else'v1');RUN.mkdir()
subject=load(TARGET,'independent_review_binding');author.subject=subject
class RetainedTemp:
    def __init__(self,*a,**kw):self.name=tempfile.mkdtemp(dir=ROOT/'fixtures',prefix='synthetic-')
    def cleanup(self):pass
    def __enter__(self):return self.name
    def __exit__(self,*unused):pass

class Independent(author.SourceOnlyControls):
    def test_06_real_backend_compiled_fields_and_original_gate_survive_true_false_null(self):
        for observed in [True,False,None]:
            root,config,actual,backend=self.fixture();actual['observations'][0]['observed']=observed
            config['review_store']=str(root/'original-native-reviews');Path(config['review_store']).mkdir()
            baseline=backend.compile_contract(config,backend.d.load(Path(config['plan'])),backend.d.load(Path(config['design_lock'])))
            result=subject.bind_source(config,actual,root/'independent-extra',backend)
            derived=json.loads(Path(result['config']).read_text());compiled=json.loads((root/'independent-extra/compiled-original.json').read_text())
            self.assertEqual({k for k in config if config[k]!=derived[k]},{'source_review_store'});self.assertEqual(derived['review_store'],config['review_store'])
            self.assertEqual(compiled,baseline);self.assertIs(compiled['claims'][0]['expected'],True);self.assertEqual(compiled['claims'][0]['unit'],'bool')
            self.assertEqual(compiled['claims'][0]['files'],baseline['claims'][0]['files'])
            row=json.loads(Path(result['evaluation']).read_text())['rows'][0];self.assertIs(row['actual'],observed)
            self.assertEqual(backend.evaluate(config,baseline)['rows'][0]['status'],'unassessed')
    def test_07_source_change_during_real_evaluate_must_fail_before_publication(self):
        root,config,actual,backend=self.fixture()
        class Drifting:
            d=backend.d;compile_contract=staticmethod(backend.compile_contract);bind=staticmethod(backend.bind)
            @staticmethod
            def evaluate(config,compiled):
                result=backend.evaluate(config,compiled);Path(config['bridge']).write_text('changed during evaluation');return result
        with self.assertRaisesRegex(ValueError,'changed'):
            subject.bind_source(config,actual,root/'late-drift',Drifting)
        self.assertFalse((root/'late-drift/source-only-evaluation.json').exists())
    def test_08_bound_reference_change_during_real_evaluate_must_fail(self):
        root,config,actual,backend=self.fixture()
        class ChangedRef:
            d=backend.d;compile_contract=staticmethod(backend.compile_contract);bind=staticmethod(backend.bind)
            @staticmethod
            def evaluate(config,compiled):
                result=backend.evaluate(config,compiled)
                path=next(Path(config['source_review_store']).glob('*.json'));path.write_text(path.read_text()+'\n')
                return result
        with self.assertRaisesRegex(ValueError,'reference|changed'):
            subject.bind_source(config,actual,root/'late-reference',ChangedRef)
        self.assertFalse((root/'late-reference/source-only-evaluation.json').exists())
    def test_09_symlink_and_native_or_finish_cli_surface_fail_closed(self):
        root,config,actual,backend=self.fixture();link=root/'source-link';link.symlink_to(config['source_roots'][0])
        altered=copy.deepcopy(config);altered['source_roots']=[str(link)]
        with self.assertRaisesRegex(ValueError,'Symlink'):subject.bind_source(altered,actual,root/'bad-link',backend)
        import subprocess
        result=subprocess.run([sys.executable,'-B',str(TARGET),'--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0);self.assertIn('--submission-sha256',result.stdout)
        for flag in ['--native','--image','--finish','--capture']:self.assertNotIn(flag,result.stdout)

class Recorded(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.rows=[]
    def addSuccess(self,t):super().addSuccess(t);self.rows.append({'test':t.id(),'status':'pass'})
    def addFailure(self,t,e):super().addFailure(t,e);self.rows.append({'test':t.id(),'status':'fail','traceback':''.join(traceback.format_exception(*e))})
    def addError(self,t,e):super().addError(t,e);self.rows.append({'test':t.id(),'status':'error','traceback':''.join(traceback.format_exception(*e))})
with patch.object(tempfile,'TemporaryDirectory',RetainedTemp):
    result=unittest.TextTestRunner(verbosity=2,resultclass=Recorded).run(unittest.defaultTestLoader.loadTestsFromTestCase(Independent))
report={'version':1,'source_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'control_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'tests':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors),'failures':len(result.failures),'errors':len(result.errors),'controls':result.rows,'actual_data_access':False,'backend':str(fixtures.er.__file__),'fixture_retention':'All synthetic temporary directories retained under review root; no cleanup outside root'}
(RUN/'RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
sys.exit(not result.wasSuccessful())
