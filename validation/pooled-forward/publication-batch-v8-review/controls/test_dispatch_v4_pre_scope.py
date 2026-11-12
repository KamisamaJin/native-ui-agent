import copy
import json
from pathlib import Path
import sys
import traceback
import unittest
from fixture_v8 import ROOT,OLD,DISPATCH,Reader,reader,batch,dispatch,load,sha,put,ref,authority

fixture_code=load(DISPATCH/'fixture_dispatch.py','borrowed_closed_dispatch_fixture')
f=fixture_code.Fixture(OLD)
r=Reader();r.overlay.update(f.reader.overlay);r.directories.update(f.reader.directories)
docs=[{'original_ref':ref(OLD/'fixtures/rich/study/cache/business/run-cohort2/arms'/task/arm/'self-claim.json'),'locations':[]}for task in []for arm in []]
# Derive the exact synthetic original set from the selected claim descriptors.
selected_old=batch.pinned(r,f.selection_ref);originals=[]
for row in selected_old['groups']:
    spec=batch.pinned(r,row['spec']);derivations=batch.pinned_value(r,row['derivations'])
    names={d['path']for d in spec['anonymous_description']['documents']if d.get('kind')=='original-worker-self-claim'}
    originals.extend(d['original']for d in derivations if d['anonymous_relative']in names)
docs=[{'original_ref':original,'locations':[]}for original in originals]
AUTH=authority('dispatch-authority',f.root,docs)
ALT=authority('dispatch-alternate-authority',f.root,docs)
ctx=batch.load_metadata_context(r,f.root,AUTH,f.cause_ref)
selected=copy.deepcopy(selected_old);selected.update(code_pins=batch.code_pins(),metadata_authority=AUTH)
for row in selected['groups']:
    spec=batch.pinned(r,row['spec']);spec['metadata_authority']=AUTH
    derivations=batch.pinned_value(r,row['derivations'])
    names={d['path']for d in spec['anonymous_description']['documents']if d.get('kind')=='original-worker-self-claim'}
    for d in derivations:
        raw=batch.pinned(r,d['original'])
        if d['anonymous_relative']in names:
            raw,proof=batch._worker_lens(raw,d['original'],ctx);d['metadata_lens']=proof
        d['emitter_admission']=batch.present_value(raw,outcome=d['outer_fact_selection']is not None)[1]
    row['spec']=put(ROOT/'fixtures/dispatch-wrap'/row['group']/'SPEC.json',spec)
    row['derivations']=put(ROOT/'fixtures/dispatch-wrap'/row['group']/'DERIVATIONS.json',derivations)
SELECTION=put(ROOT/'fixtures/dispatch-wrap/SELECTION.json',selected)
packets=batch.pinned(r,f.packets_ref);packets.update(code_pins=batch.code_pins(),selection_seal=SELECTION)
PACKETS=put(ROOT/'fixtures/dispatch-wrap/PACKETS.json',packets)
CHECKED=dispatch.verify_prepared(batch,r,f.root,f.cause_ref,PACKETS,SELECTION,f.actors_ref)
CHECKED['bindings'].update(batch=ref(ROOT/'revision-v8/alarm-material-tools-v8/batch.py'),dispatcher=ref(ROOT/'revision-v8/prepare_alarm_dispatch_v4.py'))

def vput(path,value):
    raw=batch.encoded(value);r.overlay[str(path)]=raw;return{'path':str(path),'sha256':sha(raw)}
ends={};previous=None;new_virtual={}
for group in dispatch.ORDER[:-1]:
    old_end=batch.pinned(r,f.ends[group]);old_start=batch.pinned(r,old_end['start']);prepared=batch.pinned(r,old_start['dispatch_prepared'])
    destination=f.root/'operators/cohort2/coordination'/dispatch.DISPATCH_DIRECTORY/group
    for e in prepared['entries']:
        raw=r.read_bytes(e['prompt']['path']);path=destination/(e['judge']+'-PROMPT.txt');r.overlay[str(path)]=raw;e['prompt']={'path':str(path),'sha256':sha(raw)}
    prepared.update(version=4,**CHECKED['bindings'],previous_pair=previous)
    prepared_ref=vput(destination/'PREPARED.json',prepared)
    old_start.update(version=4,metadata_authority=AUTH,previous_pair=previous,dispatch_prepared=prepared_ref)
    start=vput(Path(old_end['start']['path']),old_start);old_end['start']=start
    previous=vput(Path(f.ends[group]['path']),old_end);ends[group]=previous
new_virtual={key:raw.decode()for key,raw in r.overlay.items()if f.reader.overlay.get(key)!=raw}
put(ROOT/'fixtures/DISPATCH-V4-VIRTUAL-CHAIN.json',new_virtual)
put(ROOT/'fixtures/DISPATCH-V4-REFS.json',{'selection':SELECTION,'packets':PACKETS,'authority':AUTH,'ends':ends,'bindings':CHECKED['bindings']})

def clone():
    result=Reader();result.overlay=dict(r.overlay);result.directories=dict(r.directories);return result
def overlay(q,reference,value):
    raw=batch.encoded(value);q.overlay[reference['path']]=raw;return dict(reference,sha256=sha(raw))
OBS=[]
class DispatchV4(unittest.TestCase):
    def verify(self,q,selection=SELECTION,packets=PACKETS,actors=f.actors_ref,cause=f.cause_ref):
        return dispatch.verify_prepared(batch,q,f.root,cause,packets,selection,actors)
    def previous(self,q,previous=None):
        return dispatch.verify_previous(batch._presentation['phase_barriers'],q,f.root,dispatch.ORDER[-1],previous or ends[dispatch.ORDER[-2]],f.cause_ref,CHECKED['packet_rows'],cause_rows=CHECKED['cause_rows'],base_refs=CHECKED['base_refs'],bindings=CHECKED['bindings'])
    def changed_selection(self,q,callback):
        selected=batch.pinned(q,SELECTION);callback(selected,q);sr=overlay(q,SELECTION,selected)
        packets=batch.pinned(q,PACKETS);packets['selection_seal']=sr;return sr,overlay(q,PACKETS,packets)
    def tearDown(self):
        OBS.append({'test':self.id(),'actual_data':False})
    def test_01_all15_external_context_packets_original_actors_and_base_seals(self):
        checked=self.verify(clone());self.assertEqual(len(checked['base_refs']),15);self.assertEqual(checked['metadata_authority'],AUTH)
        self.assertEqual(len({a for row in checked['cause_rows'].values()for a in row['actors'].values()}),30)
    def test_02_all15_default_package_replays_ten_lens_proofs_before_freshness_stop(self):
        q=clone();before=len(q.reads)
        with self.assertRaisesRegex(ValueError,'Fresh physical output directory'):
            batch.package_selected(f.root,q,SELECTION,OLD/'results/v3/cases/test_01_complete_unmocked_all15_selection_and_packaging/packets',ROOT/'unused-package-operator')
        self.assertFalse((ROOT/'unused-package-operator').exists());self.assertGreater(len(q.reads)-before,100)
    def test_03_v4_fourteen_pair_chain_retains_same_actors_and_new_namespace(self):
        self.previous(clone());self.assertEqual(dispatch.DISPATCH_DIRECTORY,'alarm-dispatches-v4')
    def test_04_partial_cause_stops_before_metadata_and_packets(self):
        q=clone();bad=batch.pinned(q,f.cause_ref);bad['groups'].pop();cause=overlay(q,f.cause_ref,bad);q.reads.clear()
        with self.assertRaises(ValueError):self.verify(q,cause=cause)
        self.assertEqual(q.reads,[cause['path']])
    def test_05_valid_alternate_auth_cannot_replace_only_selection_binding(self):
        q=clone();selection,packets=self.changed_selection(q,lambda selected,_q:selected.update(metadata_authority=ALT))
        with self.assertRaisesRegex(ValueError,'Selection/spec external metadata authority differs'):self.verify(q,selection,packets)
    def test_06_one_spec_cannot_nominate_another_root_authority(self):
        q=clone()
        def change(selected,q):
            row=selected['groups'][-1];spec=batch.pinned(q,row['spec']);spec['metadata_authority']=ALT;row['spec']=overlay(q,row['spec'],spec)
        selection,packets=self.changed_selection(q,change)
        with self.assertRaisesRegex(ValueError,'Selection/spec external metadata authority differs'):self.verify(q,selection,packets)
    def test_07_nonempty_lens_proof_cannot_be_dropped_or_self_reapproved(self):
        for mutation in ['drop','foreign']:
            q=clone()
            def change(selected,q):
                row=selected['groups'][-1];ds=batch.pinned_value(q,row['derivations']);claim=next(d for d in ds if d.get('metadata_lens')is not None)
                if mutation=='drop':del claim['metadata_lens']
                else:claim['metadata_lens']['authority']=ALT
                row['derivations']=overlay(q,row['derivations'],ds)
            selection,packets=self.changed_selection(q,change)
            with self.subTest(case=mutation),self.assertRaises(ValueError):self.verify(q,selection,packets)
    def test_08_last_original_actor_mismatch_still_blocks(self):
        q=clone();actors=batch.pinned(q,f.actors_ref);actors['groups'][dispatch.ORDER[-1]]['actors']['J2']='foreign-synthetic-actor'
        with self.assertRaisesRegex(ValueError,'Original contexts differ'):self.verify(q,actors=overlay(q,f.actors_ref,actors))
    def test_09_prior_v3_start_or_wrong_auth_fails_v4_chain(self):
        for field,value in [('version',3),('metadata_authority',ALT)]:
            q=clone();end=batch.pinned(q,ends[dispatch.ORDER[-2]]);start=batch.pinned(q,end['start']);start[field]=value;end['start']=overlay(q,end['start'],start)
            bad=overlay(q,ends[dispatch.ORDER[-2]],end)
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'Previous pair input binding differs'):self.previous(q,bad)
    def test_10_prior_prepared_authority_and_current_selected_binding_are_exact(self):
        q=clone();end=batch.pinned(q,ends[dispatch.ORDER[-2]]);start=batch.pinned(q,end['start']);prepared=batch.pinned(q,start['dispatch_prepared']);prepared['metadata_authority']=ALT
        start['dispatch_prepared']=overlay(q,start['dispatch_prepared'],prepared);end['start']=overlay(q,end['start'],start)
        with self.assertRaisesRegex(ValueError,'Previous dispatch input/code binding differs'):self.previous(q,overlay(q,ends[dispatch.ORDER[-2]],end))

class Recorded(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.rows=[]
    def addSuccess(self,test):super().addSuccess(test);self.rows.append({'test':test.id(),'status':'pass'})
    def addError(self,test,error):super().addError(test,error);self.rows.append({'test':test.id(),'status':'error','traceback':''.join(traceback.format_exception(*error))})
    def addFailure(self,test,error):super().addFailure(test,error);self.rows.append({'test':test.id(),'status':'fail','traceback':''.join(traceback.format_exception(*error))})
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2,resultclass=Recorded).run(unittest.defaultTestLoader.loadTestsFromTestCase(DispatchV4))
    put(ROOT/'results/DISPATCH.json',{'version':1,'tests_run':result.testsRun,'passed':result.testsRun-len(result.errors)-len(result.failures),'errors':len(result.errors),'failures':len(result.failures),
        'controls':result.rows,'batch_sha256':sha((ROOT/'revision-v8/alarm-material-tools-v8/batch.py').read_bytes()),'dispatcher_sha256':sha((ROOT/'revision-v8/prepare_alarm_dispatch_v4.py').read_bytes()),
        'control_sha256':sha(Path(__file__).read_bytes()),'virtual_member_count':len(new_virtual),'actual_data':False})
    sys.exit(not result.wasSuccessful())
