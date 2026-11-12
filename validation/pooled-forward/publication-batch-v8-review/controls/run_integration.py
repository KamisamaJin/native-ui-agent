import copy
import json
from pathlib import Path
import sys
import traceback
import unittest
from fixture_v8 import ROOT,OLD,PRIOR,Reader,reader,batch,dispatch,cause,put,ref,entry,authority,study_authority,load,sha

sys.path.insert(0,str(OLD/'controls'))
from fixture import Study
base=load(ROOT.parent/'publication-batch-v6-review/controls/review_v6.py','retained_v6_controls')
compat=Study.existing(OLD/'fixtures/compatible',batch,OLD);compat.reader=reader
rich=Study.existing(OLD/'fixtures/rich',batch,OLD);rich.reader=reader
AUTH_COMPAT=study_authority(compat,'compat-authority')
AUTH_RICH=study_authority(rich,'rich-authority')
base.ROOT=ROOT;base.batch=batch;base.reader=reader;base.compat=compat;base.rich=rich;base.cause=cause
base.legacy.ROOT=ROOT;base.legacy.ACTIVE=batch;base.legacy.RUN=ROOT/'results/integration-final';base.legacy.READER=Reader
def current_teardown(self):
    (self.case/'OBSERVATIONS.json').write_bytes(batch.encoded(self.log))
    self.assertLessEqual(sum(q.is_file() for q in ROOT.rglob('*'))+140,600)
base.legacy.Cases.tearDown=current_teardown
base.legacy.Reader=Reader;base.legacy.COMPAT=compat;base.legacy.RICH=rich;base.legacy.CAUSE=cause;base.legacy.MINI=None
def prepared(self,fixture,name='selection'):
    batch.MAP_SEAL_SHA=fixture.mapping_seal['sha256']
    return batch.prepare(fixture.root,fixture.reader,cause,fixture.snapshot,fixture.native_result,self.case/name,self.case/(name+'-intermediates'),metadata_authority_ref=AUTH_RICH if fixture is rich else AUTH_COMPAT)
base.legacy.Cases.prepare=prepared
def native_pin(self):
    bad=dict(compat.snapshot,sha256='0'*64);r=Reader()
    with self.assertRaisesRegex(ValueError,'Original pinned bytes differ'):
        batch.prepare(compat.root,r,cause,bad,compat.native_result,self.case/'out',self.case/'work',metadata_authority_ref=AUTH_COMPAT)
    self.assertFalse(any('MAPPING.json'in str(x)for x in r.reads))
base.legacy.Cases.test_04_wrong_native_snapshot_pin_stops_before_mapping=native_pin

fresh_value=batch.strict_json(b'{"statement":"Synthetic original worker statement","assignment":"A","other":"A","literal":"record-ref-0001","actual_tool_runs":{"target_path":"/Users/rex/synthetic/unavailable-target","status":"F","rows":[{"status":"F","expected":9007199254740993.0,"actual":1e-999},{"status":"P","actual":true},{"status":"U","actual":null}]},"actual":"A","note":"  e\\u0301  "}')
FRESH_RAW=put(ROOT/'fixtures/fresh-originals/01.json',fresh_value)
locations=[entry(FRESH_RAW,'/assignment','A','execution_identity_metadata'),entry(FRESH_RAW,'/other','A','execution_identity_metadata'),entry(FRESH_RAW,'/actual_tool_runs/target_path','/Users/rex/synthetic/unavailable-target')]
fresh_docs=[{'original_ref':FRESH_RAW,'locations':locations}]
for i in range(2,11):fresh_docs.append({'original_ref':put(ROOT/'fixtures/fresh-originals'/('%02d.json'%i),{'statement':'Synthetic original '+str(i),'actual':False}),'locations':[]})
AUTH_FRESH=authority('fresh-authority',compat.root,fresh_docs)
CONTEXT=batch.load_metadata_context(reader,compat.root,AUTH_FRESH,cause)

def overlay_ref(r,reference,value):
    raw=batch.encoded(value);r.overlay[reference['path']]=raw;return dict(reference,sha256=sha(raw))
def changed_auth(r,reference,callback):
    auth=batch.pinned(r,reference);callback(auth);return overlay_ref(r,reference,auth)
def republish(r,reference,*,catalog_change=None,approval_change=None):
    auth=batch.pinned(r,reference)
    if catalog_change:
        cat=batch.pinned(r,auth['catalog_ref']);catalog_change(cat);auth['catalog_ref']=overlay_ref(r,auth['catalog_ref'],cat)
        seal=batch.pinned(r,auth['catalog_seal']);seal['artifact_manifest'][0].update(sha256=auth['catalog_ref']['sha256'],size_bytes=len(r.read_bytes(auth['catalog_ref']['path'])))
        auth['catalog_seal']=overlay_ref(r,auth['catalog_seal'],seal)
    approval=batch.pinned(r,auth['approval_ref']);approval.update(catalog_ref=auth['catalog_ref'],catalog_seal=auth['catalog_seal'])
    if approval_change:approval_change(approval)
    auth['approval_ref']=overlay_ref(r,auth['approval_ref'],approval)
    seal=batch.pinned(r,auth['approval_seal']);seal.update(catalog_ref=auth['catalog_ref'],catalog_seal=auth['catalog_seal'],approval_ref=auth['approval_ref'])
    seal['artifact_manifest'][0].update(sha256=auth['approval_ref']['sha256'],size_bytes=len(r.read_bytes(auth['approval_ref']['path'])))
    auth['approval_seal']=overlay_ref(r,auth['approval_seal'],seal)
    return overlay_ref(r,reference,auth)

class Integration(base.V6Cases):
    def test_34_all_ten_authority_and_complete_pure_lens_context(self):
        self.assertEqual(len(CONTEXT.documents),10);self.assertEqual(Path(FRESH_RAW['path']).stat().st_mode&0o777,0o644)
        value,proof=batch._worker_lens(batch.pinned(reader,FRESH_RAW),FRESH_RAW,CONTEXT)
        self.assertEqual(value['assignment'],value['other']);self.assertNotEqual(value['assignment'],'record-ref-0001')
        self.assertEqual(value['actual'],'A');self.assertEqual(value['actual_tool_runs']['rows'],fresh_value['actual_tool_runs']['rows'])
        self.assertNotIn(sha(b'A'),batch.json_text(value));self.assertEqual(proof['authority'],AUTH_FRESH)
    def test_35_default_prepare_cannot_skip_external_all_ten_authority(self):
        r=Reader()
        with self.assertRaisesRegex(ValueError,'All ten external'):batch.prepare(compat.root,r,cause,compat.snapshot,compat.native_result,self.case/'out',self.case/'work')
        self.assertNotIn(compat.snapshot['path'],r.reads);self.assertFalse((self.case/'out').exists())
    def test_36_bad_authority_flags_root_lens_and_document_count_fail(self):
        for label,callback in [('credit',lambda a:a.update(evidence_credit=True)),('bool-credit',lambda a:a.update(reference_validated=0)),
            ('root',lambda a:a.update(original_root=str(ROOT))),('count',lambda a:a['original_document_refs'].pop()),
            ('lens',lambda a:a['lens_ref'].update(sha256='f'*64))]:
            r=Reader();changed=changed_auth(r,AUTH_FRESH,callback)
            with self.subTest(case=label),self.assertRaises(ValueError):batch.load_metadata_context(r,compat.root,changed,cause)
    def test_37_approval_missing_duplicate_foreign_hash_or_original_order_fail(self):
        changes=[lambda a:a['approved_locations'].pop(),lambda a:a['approved_locations'].append(copy.deepcopy(a['approved_locations'][0])),
            lambda a:a['approved_locations'][0].update(location_sha256='f'*64),lambda a:a['original_document_refs'].reverse(),
            lambda a:a.update(unapproved_locations=[{'pointer':'/unknown'}])]
        for i,change in enumerate(changes):
            r=Reader();changed=republish(r,AUTH_FRESH,approval_change=change)
            with self.subTest(case=i),self.assertRaises(ValueError):batch.load_metadata_context(r,compat.root,changed,cause)
    def test_38_catalogue_extension_cannot_reapprove_or_hide_an_unapproved_slot(self):
        r=Reader();changed=republish(r,AUTH_FRESH,catalog_change=lambda c:c['documents'][0]['locations'][0].update(codepoint_length=99))
        with self.assertRaisesRegex(ValueError,'lacks independent approval'):batch.load_metadata_context(r,compat.root,changed,cause)
    def test_39_manifest_stale_hash_extra_member_and_writable_artifact_fail(self):
        auth=batch.pinned(reader,AUTH_FRESH)
        r=Reader();r.overlay[auth['catalog_ref']['path']]=b'{}\n'
        with self.assertRaisesRegex(ValueError,'artifact bytes/mode'):batch.load_metadata_context(r,compat.root,AUTH_FRESH,cause)
        # Separate physical extra-member namespace remains retained as a negative.
        extra=self.case/'EXTRA.json';put(extra,{'synthetic':True},True)
        r=Reader();r.directories[str(Path(auth['catalog_seal']['path']).parent)]=self.case
        with self.assertRaises((ValueError,FileNotFoundError)):batch.load_metadata_context(r,compat.root,AUTH_FRESH,cause)
    def test_40_changed_original_or_foreign_original_byte_pin_fail(self):
        r=Reader();r.overlay[FRESH_RAW['path']]=b'{"statement":"changed"}\n'
        with self.assertRaisesRegex(ValueError,'Original pinned bytes differ'):batch.load_metadata_context(r,compat.root,AUTH_FRESH,cause)
        value={'statement':'unlicensed'};foreign=put(self.case/'FOREIGN.json',value)
        with self.assertRaisesRegex(ValueError,'absent from exact external'):batch._worker_lens(value,foreign,CONTEXT)
    def test_41_cause_gate_precedes_any_metadata_or_claim_read(self):
        r=Reader();bad=put(self.case/'BAD-CAUSE.json',{'version':1,'kind':'global-independent-cause-grade-barrier','groups':[]})
        with self.assertRaises(ValueError):batch.load_metadata_context(r,compat.root,AUTH_FRESH,bad)
        self.assertEqual(r.reads,[bad['path']])
    def test_42_exact_ten_selfseal_registry_is_checked_before_selection_outputs(self):
        batch.MAP_SEAL_SHA=compat.mapping_seal['sha256']
        with self.assertRaisesRegex(ValueError,'All ten approved raw claims'):batch.prepare(compat.root,reader,cause,compat.snapshot,compat.native_result,self.case/'out',self.case/'work',metadata_authority_ref=AUTH_FRESH)
        self.assertFalse((self.case/'out').exists());self.assertFalse((self.case/'work').exists())
    def test_43_fresh_whole_claim_packet_and_context_required_proof(self):
        work=self.case/'work';work.mkdir();group=batch.Group(compat.root,reader,'Case01-X','T1','A',{},[],{}, {},work,CONTEXT)
        group.json_document(FRESH_RAW,'worker/self-claim.json',{'kind':'original-worker-self-claim','visibility':'worker_public'})
        proof=group.derivations[0]
        with self.assertRaisesRegex(ValueError,'validated metadata context'):batch.verify_derivation(reader,proof)
        with self.assertRaisesRegex(ValueError,'validated metadata context'):batch.verify_derivation(reader,proof,metadata_context=proof['metadata_lens'])
        batch.verify_derivation(reader,proof,metadata_context=CONTEXT)
        spec={'version':1,'kind':'explicit-anonymous-alarm-material-spec','anonymous_group':'Case01-X','first_cause_barrier':cause,'metadata_authority':AUTH_FRESH,
            'documents':group.documents,'anonymous_description':group.description,'instructions':batch.ref(reader,rich.root/'business-quality-tools/ALARM-INSTRUCTIONS-v1.md'),
            'grade_template':batch.ref(reader,rich.root/'business-quality-tools/ALARM-GRADE-TEMPLATE-v1.json')}
        self.assertEqual(batch.verify_metadata_spec(spec,group.derivations,CONTEXT,AUTH_FRESH),{batch._reference_key(FRESH_RAW)})
        built=batch.build(reader,spec,self.case/'packet',self.case/'operator');supplied=reader.read_json(self.case/'packet/worker/self-claim.json')
        self.assertEqual(supplied['actual_tool_runs']['rows'],fresh_value['actual_tool_runs']['rows']);self.assertEqual(supplied['actual'],'A');self.assertEqual(supplied['note'],fresh_value['note'])
        self.assertEqual(supplied['assignment'],supplied['other']);self.assertIn('do not imply supplied or validated',group.description['metadata_reference_scope']);self.assertIn('different documents establishes no identity or evidence relationship',group.description['metadata_reference_scope'])
        changed=copy.deepcopy(proof);changed['metadata_lens']['proof']['changes'][0]['anonymous_literal']='forged'
        with self.assertRaisesRegex(ValueError,'raw-to-metadata-lens proof differs'):batch.verify_derivation(reader,changed,metadata_context=CONTEXT)
        missing=copy.deepcopy(proof);del missing['metadata_lens']
        with self.assertRaisesRegex(ValueError,'cannot fall back'):batch.verify_derivation(reader,missing,metadata_context=CONTEXT)
        changed=copy.deepcopy(spec);changed['metadata_authority']=AUTH_COMPAT
        with self.assertRaisesRegex(ValueError,'Selection/spec'):batch.verify_metadata_spec(changed,group.derivations,CONTEXT,AUTH_FRESH)
        self.observe('fresh real packet',built)
    def test_44_non_worker_reports_keep_exact_v6_projection_and_no_lens(self):
        old=base.load(ROOT.parent/'publication-batch-v6-review/revision-v6/alarm-material-tools-v6/batch.py','stable_v6_comparison')
        value={'rows':[{'status':'F','expected':48,'actual':44}],'scope':'Factual exact scope'}
        self.assertEqual(old.present_value(value),batch.present_value(value));self.assertEqual(old.m.neutralize(value),batch.m.neutralize(value))
    def test_45_proof_cannot_change_genre_or_drop_selfclaim_document(self):
        value,lp=batch._worker_lens(fresh_value,FRESH_RAW,CONTEXT);neutral,projection=batch.m.neutralize(batch.present_value(value)[0])
        derived=put(self.case/'DERIVED.json',neutral)
        row={'original':FRESH_RAW,'derived':derived,'anonymous_relative':'worker/self-claim.json','metadata_lens':lp,'projection':projection,'emitter_admission':batch.present_value(value)[1],'outer_fact_selection':None}
        spec={'anonymous_group':'Case01-X','metadata_authority':AUTH_FRESH,'anonymous_description':{'documents':[{'path':'worker/self-claim.json','kind':'another-report'}]}}
        with self.assertRaisesRegex(ValueError,'selfclaim document membership'):batch.verify_metadata_spec(spec,[row],CONTEXT,AUTH_FRESH)
        row['outer_fact_selection']={}
        with self.assertRaisesRegex(ValueError,'cannot rewrite outcome'):batch.verify_derivation(reader,row,metadata_context=CONTEXT)

class Recorded(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.rows=[]
    def addSuccess(self,test):super().addSuccess(test);self.rows.append({'test':test.id(),'status':'pass'})
    def addError(self,test,error):super().addError(test,error);self.rows.append({'test':test.id(),'status':'error','traceback':''.join(traceback.format_exception(*error))})
    def addFailure(self,test,error):super().addFailure(test,error);self.rows.append({'test':test.id(),'status':'fail','traceback':''.join(traceback.format_exception(*error))})

if __name__=='__main__':
    (ROOT/'fixtures').mkdir(exist_ok=True)
    result=unittest.TextTestRunner(verbosity=2,resultclass=Recorded).run(unittest.defaultTestLoader.loadTestsFromTestCase(Integration))
    report={'version':1,'tests_run':result.testsRun,'passed':result.testsRun-len(result.errors)-len(result.failures),'errors':len(result.errors),'failures':len(result.failures),'controls':result.rows,
        'batch_sha256':sha((ROOT/'revision-v8/alarm-material-tools-v8/batch.py').read_bytes()),'control_sha256':sha(Path(__file__).read_bytes()),'actual_data':False}
    (ROOT/'results/INTEGRATION-final.json').write_bytes(batch.encoded(report));sys.exit(not result.wasSuccessful())
