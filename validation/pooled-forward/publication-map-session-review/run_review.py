import ast,hashlib,importlib.util,json,os,stat,sys,traceback,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import test_session as author
import session

class Independent(author.SessionControls):
    def test_21_full_map_boundary_hashes_are_not_skipped_or_repeated_per_payload(self):
        real=session.base.read_regular
        with patch.object(session.base,'read_regular',wraps=real)as spy:
            reader=self.resolver();initial=sum(str(c.args[0])==str(self.map)for c in spy.call_args_list)
            self.assertEqual(initial,2)
            for unused in range(10):self.assertEqual(reader.hash(self.original+'/packet/result.json'),author.fixture.sha(self.payload))
            self.assertEqual(sum(str(c.args[0])==str(self.map)for c in spy.call_args_list),initial)
            self.assertEqual(reader.verify_all(),3);reader.close()
            maps=[c for c in spy.call_args_list if str(c.args[0])==str(self.map)]
            self.assertEqual(len(maps),5);self.assertTrue(all(c.kwargs.get('expected_sha')==self.pin for c in maps))
    def test_22_map_rewrite_during_payload_hash_is_caught_by_post_access_identity(self):
        reader=self.resolver();real=session.base.read_regular;target=Path(self.rows[self.original+'/packet/result.json']['physical_path'])
        def changed(path,**kwargs):
            result=real(path,**kwargs)
            if Path(path)==target:self.map.write_bytes(self.map.read_bytes())
            return result
        with patch.object(session.base,'read_regular',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'map identity changed'):reader.hash(self.original+'/packet/result.json')
    def test_23_replaced_namespace_identity_cannot_reuse_a_session(self):
        reader=self.resolver();old=self.namespace.with_name('original-files');self.namespace.rename(old);self.namespace.mkdir()
        with self.assertRaisesRegex(ValueError,'namespace identity changed'):reader.read_bytes(self.original+'/packet/result.json')
    def test_24_close_full_hash_and_closed_all_apis_fail(self):
        reader=self.resolver();self.map.write_bytes(self.map.read_bytes()+b' ')
        with self.assertRaises(ValueError):reader.close()
        # A separate valid session verifies close then rejects every entry point.
        self.write_map();reader=self.resolver();reader.close()
        for call in [lambda:reader.verify_all(),lambda:reader.verify_map(),lambda:reader.read_bytes(self.original+'/packet/result.json'),lambda:reader.file(self.original+'/packet/result.json'),lambda:reader.directory(self.original+'/packet'),lambda:reader.close()]:
            with self.assertRaisesRegex(ValueError,'closed'):call()
    def test_25_full_closure_hashes_unrequested_payloads_and_keeps_original_bytes(self):
        reader=self.resolver();key=self.original+'/packet/native/frames/second.png';p=Path(self.rows[key]['physical_path']);p.chmod(0o644);p.write_bytes(b'X'*self.rows[key]['bytes']);p.chmod(0o444)
        reader.hash(self.original+'/packet/result.json')
        with self.assertRaisesRegex(ValueError,'SHA256 differs'):reader.verify_all()
    def test_26_payload_json_is_strict_without_payload_or_original_rewriting(self):
        key=self.original+'/packet/result.json';path=Path(self.rows[key]['physical_path']);raw=b'{"duplicate":1,"duplicate":2}\n'
        path.chmod(0o644);path.write_bytes(raw);path.chmod(0o444);self.rows[key].update(bytes=len(raw),sha256=author.fixture.sha(raw));self.write_map();reader=self.resolver()
        self.assertEqual(reader.read_bytes(key),raw)
        with self.assertRaisesRegex(ValueError,'Duplicate JSON key'):reader.read_json(key)
    def test_27_replay_preserves_frozen_checker_arguments_gates_and_unsupported_limits(self):
        old=ast.parse((ROOT/'comparison/preserve.py').read_bytes());new=ast.parse((ROOT/'replay.py').read_bytes())
        old_fn=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name=='replay');new_fn=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='replay')
        class Normal(ast.NodeTransformer):
            def visit_Attribute(self,node):
                node=self.generic_visit(node)
                if isinstance(node.value,ast.Name)and node.value.id=='p':return ast.Name(id=node.attr,ctx=node.ctx)
                return node
        def norm(node):return ast.dump(Normal().visit(node),include_attributes=False)
        def assignment(fn,name):return next(n.value for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets))
        for name in ['public','history','native','occurrence']:self.assertEqual(norm(assignment(old_fn,name)),norm(assignment(new_fn,name)))
        def conditions(fn):return[norm(n.value.args[0])for n in fn.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and norm(n.value.func)==norm(ast.Name(id='need',ctx=ast.Load()))]
        self.assertEqual(conditions(old_fn),conditions(new_fn))
        def archives(fn):return[norm(n.value)for n in fn.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='verify']
        self.assertEqual(archives(old_fn),archives(new_fn));self.assertEqual(len(archives(new_fn)),2)
        result=next(n.value for n in new_fn.body if isinstance(n,ast.Return));values={k.value:v.value for k,v in zip(result.keys,result.values)if isinstance(k,ast.Constant)and isinstance(v,ast.Constant)}
        for key in ['source_domain_evaluation','source_responsibility_evaluation']:self.assertEqual(values[key],'unsupported')
        for key in ['current_source_delivery_verified','cleanup_authorized']:self.assertIs(values[key],False)
        self.assertIs(values['common_publication_io_not_treatment_benefit'],True)
        self.assertTrue(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='verify_all'for n in ast.walk(new_fn)))
        self.assertTrue(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='close'for n in ast.walk(new_fn)))
        pins=ast.literal_eval(next(n.value for n in old.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PINS'for t in n.targets)))
        for name,wanted in pins.items():self.assertEqual(hashlib.sha256((ROOT/'comparison/vendor'/(name+'.py')).read_bytes()).hexdigest(),wanted)

class Recorded(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.rows=[]
    def addSuccess(self,t):super().addSuccess(t);self.rows.append({'test':t.id(),'status':'pass'})
    def addFailure(self,t,e):super().addFailure(t,e);self.rows.append({'test':t.id(),'status':'fail','traceback':''.join(traceback.format_exception(*e))})
    def addError(self,t,e):super().addError(t,e);self.rows.append({'test':t.id(),'status':'error','traceback':''.join(traceback.format_exception(*e))})
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2,resultclass=Recorded).run(unittest.defaultTestLoader.loadTestsFromTestCase(Independent))
    report={'version':1,'tests':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors),'errors':len(result.errors),'failures':len(result.failures),'controls':result.rows,
        'session_sha256':hashlib.sha256((ROOT/'session.py').read_bytes()).hexdigest(),'replay_sha256':hashlib.sha256((ROOT/'replay.py').read_bytes()).hexdigest(),'control_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'author_controls_rerun':20,'independent_controls':7,'actual_data_or_qualification_raw_map_read':False,'replay_scope':'Source AST/frozen checker pin equivalence only; no actual archive/cohort replay.'}
    (ROOT/'results/RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');sys.exit(not result.wasSuccessful())
