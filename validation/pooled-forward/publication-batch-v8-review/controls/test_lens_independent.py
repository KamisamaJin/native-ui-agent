import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
lens=load(ROOT/'vendor/lens.py','independent_lens')
projection=load(ROOT/'revision-v8/publication-alarm-review/revision-v2/anonymous_projection.py','frozen_projection')
REF={'path':'/recorded/synthetic/claim.json','sha256':'a'*64}
def entry(pointer,text,kind='claimed_provenance_locator'):
    digest=hashlib.sha256(text.encode()).hexdigest()
    return {'original_ref':dict(REF),'pointer':pointer,'member_kind':'string_value','original_utf8_sha256':digest,'codepoint_length':len(text),'classification':kind,
        'contains_prose':False,'whole_container_metadata_permission':False,'reference_validated':False,'evidence_credit':False,'projection_authorized':False,
        'identity_spans':[{'start':0,'end':len(text),'unit':'unicode_codepoint','original_utf8_sha256':digest,'span_kind':'complete_canonical_locator'if text.startswith('/')else'complete_execution_identifier'}]}
def run(value,entries):return lens.project(value,REF,entries,{lens.canonical_sha(e,projection)for e in entries},projection)

class LensIndependent(unittest.TestCase):
    def test_exact_decimal_boolean_null_text_and_array_preservation(self):
        value=projection.strict_json(b'{"actual_run_records":[{"artifact_path":"/Users/rex/synthetic/a","status":"F","expected":9007199254740993.0,"actual":1e-999},{"status":"P","actual":true},{"status":"U","actual":null}],"note":"  e\\u0301  "}')
        before=copy.deepcopy(value);projected,proof=run(value,[entry('/actual_run_records/0/artifact_path','/Users/rex/synthetic/a')])
        expected=copy.deepcopy(before);expected['actual_run_records'][0]['artifact_path']='record-ref-0001'
        self.assertEqual(projected,expected);self.assertEqual(value,before)
        self.assertEqual(str(projected['actual_run_records'][0]['expected']),'9007199254740993.0');self.assertEqual(str(projected['actual_run_records'][0]['actual']),'1E-999')
        self.assertEqual([r['status']for r in projected['actual_run_records']],['F','P','U']);self.assertIn('e\u0301',projected['note']);self.assertFalse(proof['changes'][0]['reference_validated'])
    def test_all_raw_protected_names_and_normalized_variants_block(self):
        path='/Users/rex/synthetic/x'
        for key in projection.PROTECTED_KEYS:
            for spelling in [key,key.upper(),key.replace('_','-')]:
                with self.subTest(key=spelling),self.assertRaises(ValueError):run({spelling:{'path':path}},[entry('/'+spelling+'/path',path)])
        for leaf in ['actual_filepath','actualPath','expected_file','observedLocator','measured_source','renderedValue']:
            with self.subTest(leaf=leaf),self.assertRaises(ValueError):run({'summary':{leaf:path}},[entry('/summary/'+leaf,path)])
    def test_numeric_boolean_null_arrays_objects_and_empty_strings_cannot_be_locations(self):
        for value in [False,True,None,1,projection.Decimal('1.0'),[],{},'']:
            e=entry('/slot','synthetic','execution_identity_metadata')
            with self.subTest(value=repr(value)),self.assertRaises(ValueError):run({'slot':value},[e])
    def test_interior_partial_wrong_units_boolean_and_utf16_spans_fail(self):
        text='/Users/rex/🧪/é';base=entry('/slot',text)
        for changes in [{'start':1},{'end':len(text)-1},{'end':len(text)+1},{'start':False},{'end':True},{'unit':'utf16'},{'unit':'bytes'},{'original_utf8_sha256':'b'*64}]:
            e=copy.deepcopy(base);e['identity_spans'][0].update(changes)
            with self.subTest(change=changes),self.assertRaises(ValueError):run({'slot':text},[e])
    def test_non_normalized_unicode_is_exact_and_hashes_do_not_collapse(self):
        a='/Users/rex/e\u0301';b='/Users/rex/é';value={'a':a,'b':b,'unmodified':'e\u0301'}
        projected,_=run(value,[entry('/a',a),entry('/b',b)])
        self.assertNotEqual(projected['a'],projected['b']);self.assertEqual(projected['unmodified'],'e\u0301')
    def test_raw_handle_literals_and_keys_cannot_collide(self):
        value={'a':'A','b':'B','same':'A','record-ref-0001':'record-ref-0002','note':['record-ref-0003','record-ref-0004']}
        projected,_=run(value,[entry('/a','A','execution_identity_metadata'),entry('/b','B','execution_identity_metadata'),entry('/same','A','execution_identity_metadata')])
        self.assertEqual(projected['a'],projected['same']);self.assertNotEqual(projected['a'],projected['b']);self.assertEqual(projected['a'],'record-ref-0005');self.assertEqual(projected['b'],'record-ref-0006')
    def test_ordinal_output_does_not_publish_short_identifier_hashes(self):
        projected,_=run({'arm':'B','actual':'B'},[entry('/arm','B','execution_identity_metadata')]);raw=projection.json_text(projected)
        self.assertNotIn(hashlib.sha256(b'B').hexdigest(),raw);self.assertEqual(projected['actual'],'B');self.assertEqual(projected['arm'],'record-ref-0001')
    def test_bad_pointers_and_array_aliases_fail(self):
        path='/Users/rex/synthetic/x';value={'a':[{'path':path}]}
        for pointer in ['a/0/path','/a/00/path','/a/-1/path','/a/-/path','/a/1/path','/a/0/path~2','/a/0/missing','']:
            with self.subTest(pointer=pointer),self.assertRaises((ValueError,KeyError)):run(value,[entry(pointer,path)])
    def test_escaped_empty_and_slash_keys_are_exact(self):
        path='/Users/rex/synthetic/x';value={'a/b~c':{'':path}}
        projected,_=run(value,[entry('/a~1b~0c/',path)]);self.assertEqual(projected,{'a/b~c':{'':'record-ref-0001'}})
    def test_no_omission_of_unapproved_identity_or_identity_bearing_keys(self):
        for value in [{'candidate-v13.9':'fact'},{'unknown':'baseline-v12.6-common-6'},{'note':'substantive /Users/rex/synthetic/x'}]:
            with self.subTest(value=value),self.assertRaises(ValueError):run(value,[])
    def test_prose_commands_noncanonical_locators_and_control_characters_fail(self):
        for text in ['All pass /Users/rex/x','/Users/rex/a/../x','/Users/rex//x','/Users/rex/a\\x','/Users/rex/a\nx','/Users/rex/\u202ex']:
            kind='claimed_provenance_locator'if text.startswith('/')else'execution_identity_metadata'
            with self.subTest(text=repr(text)),self.assertRaises(ValueError):run({'slot':text},[entry('/slot',text,kind)])
    def test_approval_membership_foreign_record_and_mutated_scalar_fail(self):
        path='/Users/rex/synthetic/x';e=entry('/slot',path);approval={lens.canonical_sha(e,projection)}
        with self.assertRaises(ValueError):lens.project({'slot':path},REF,[e],set(),projection)
        with self.assertRaises(ValueError):lens.project({'slot':path},REF,[e],approval|{'f'*64},projection)
        foreign=dict(REF,path='/recorded/synthetic/other.json')
        with self.assertRaises(ValueError):lens.project({'slot':path},foreign,[e],approval,projection)
        with self.assertRaises(ValueError):run({'slot':path+'changed'},[e])
    def test_no_boolean_flag_coercions_or_new_evidence_credit(self):
        path='/Users/rex/synthetic/x'
        for key in ['contains_prose','whole_container_metadata_permission','reference_validated','evidence_credit','projection_authorized']:
            for flag in [0,None,True]:
                e=entry('/slot',path);e[key]=flag
                with self.subTest(key=key,flag=flag),self.assertRaises(ValueError):run({'slot':path},[e])
    def test_input_nan_cycles_and_surrogates_fail(self):
        for value in [{'x':float('nan')},{'x':projection.Decimal('Infinity')},{'x':'\ud800'}]:
            with self.assertRaises((ValueError,UnicodeError)):run(value,[])
        value={};value['x']=value
        with self.assertRaises(ValueError):run(value,[])
    def test_pure_formatter_never_resolves_or_reads_locator_targets(self):
        from unittest.mock import patch
        path='/Users/rex/does-not-exist/fixture'
        with patch('builtins.open',side_effect=AssertionError('No target IO permitted')):
            projected,_=run({'path':path},[entry('/path',path)])
        self.assertEqual(projected['path'],'record-ref-0001')

if __name__=='__main__':unittest.main()
