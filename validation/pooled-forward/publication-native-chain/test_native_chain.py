"""Author HOST hostile controls; no native execution or product conclusions."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

import native_chain as nc
from synthetic import Fixture, ROOT, HERE


RUN = HERE/'HOST'/('synthetic-'+str(time.time_ns()))
RUN.mkdir(parents=True,exist_ok=False)
RESULTS = []
for name in ['native_chain.py','synthetic.py','test_native_chain.py']:
    (RUN/name).write_bytes((HERE/name).read_bytes())


class Controls(unittest.TestCase):
    def fixture(self, mutation=None, prefix=30, terminal_failure=False):
        label=self.id().rsplit('.',1)[-1]
        return Fixture(RUN/label,mutation=mutation,prefix=prefix,terminal_failure=terminal_failure)

    def check(self, fixture, wanted='verified', message=None):
        result=nc.verify_chain(fixture,ROOT,fixture.snapshot_ref)
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'status':result['status'],'expected':wanted,
                        'matched':result['status']==wanted and (message is None or message in result.get('error',{}).get('message','')),
                        'error':result.get('error'),'acquisition_complete':result['acquisition_complete'],
                        'fixture':str(fixture.physical),'fixture_inventory_sha256':nc.digest({p:nc.sha(v) for p,v in fixture.files.items()})})
        self.assertEqual(result['status'],wanted,result)
        if message:self.assertIn(message,result['error']['message'])
        return result

    def test_01_complete_chain_preserves_f_u(self):
        result=self.check(self.fixture())
        self.assertTrue(result['acquisition_complete']);self.assertFalse(result['delivery_verified'])
        self.assertEqual(len(result['preserved_failures']),29)
        self.assertTrue(all(not v['recorded_native_accepted'] for v in result['scopes'].values()))

    def test_02_declared_prefix_stays_pending(self):
        result=self.check(self.fixture(prefix=13))
        self.assertFalse(result['acquisition_complete']);self.assertEqual(len(result['pending_scopes']),17)
        self.assertEqual(result['acquired_scopes'],13)

    def test_03_honest_effective_failure_is_not_acquisition(self):
        result=self.check(self.fixture(terminal_failure=True))
        self.assertFalse(result['acquisition_complete']);self.assertEqual(result['acquired_scopes'],29)
        self.assertEqual(len(result['preserved_failures']),30)

    def test_04_acquired_original_cannot_continue(self):
        self.check(self.fixture(('outcome:T2/I/ios:2',lambda v:v.update(new_ui_acquisition=True))), 'failed','Acquired or ambiguous original UI')

    def test_05_original_process_evidence_forbids_continuation(self):
        self.check(self.fixture(('sdk:T2/I/ios:2',lambda v:v['observed_command_records'].append({'kind':'process_started'}))), 'failed','forwarding evidence')

    def test_06_pinned_absence_assertion_required(self):
        self.check(self.fixture(('zero-index:T2/I/ios',lambda v:v.update(inner_command_log_absent=False))), 'failed','absence assertions')

    def test_07_exact_scope_membership_excludes_i1(self):
        self.check(self.fixture(('authority',lambda v:v['scopes'].update({'T1/I/ios':next(iter(v['scopes'].values()))}))), 'failed','Exact 28')

    def test_08_original_source_hash_domain(self):
        stage='capsule:'+ROOT+'/cache/business/run-cohort2/arms/T1/A/final-source'
        self.check(self.fixture((stage,lambda v:v.update(content_sha256=nc.sha(b'wrong-domain')))), 'failed','capsule hash domain')

    def test_09_unstable_platform_indices(self):
        self.check(self.fixture(('source-model:T1/B/ios',lambda v:v.update(indices=[1]))), 'failed','Unstable platform')

    def test_10_source_after_mutation(self):
        self.check(self.fixture(('source-after:T1/A/ios',lambda v:v.update({'0/Screen.swift':nc.sha(b'changed')}))), 'failed','source-before/after')

    def test_11_receipt_request_substitution(self):
        self.check(self.fixture(('receipt:T1/A/ios',lambda v:v.update(parent_plan_sha256=nc.sha(b'other-plan')))), 'failed','request/receipt')

    def test_12_reused_capture_is_forbidden(self):
        self.check(self.fixture(('outcome:T1/A/ios:3',lambda v:v.update(capture_reused=True))), 'failed','reused UI')

    def test_13_cycle_receipt_substitution(self):
        self.check(self.fixture(('cycle:T1/A/ios',lambda v:v.update(capture_result=ROOT+'/other/result.json'))), 'failed','cycle/capture')

    def test_14_positive_closure_is_required(self):
        self.check(self.fixture(('resources:T1/A/ios:effective',lambda v:v.update(remaining_devices=['synthetic-owned-device']))), 'failed','positive owned resource closure')

    def test_15_foreign_resource_owner(self):
        self.check(self.fixture(('resources:T1/A/ios:effective',lambda v:v['owner'].update(owner_key=nc.sha(b'foreign')))), 'failed','Resource owner/root')

    def test_16_foreign_journal_token(self):
        self.check(self.fixture(('journal:T1/A/ios:effective',lambda v:v.update(token='b'*32))), 'failed','same-owner original journal')

    def test_17_wrong_entry_permit_scope(self):
        self.check(self.fixture(('permit',lambda v:v['entry_resume'].update(scope='T2/B/android'))), 'failed','preclaim-resumption scope')

    def test_18_preclaim_with_ui_claim_is_ambiguous(self):
        # A genuine registered native claim before the narrow preclaim permit
        # can no longer be treated as an entry-only failure.
        def add(v):v['failed_record_files'].pop('failure.json')
        self.check(self.fixture(('permit',lambda v:add(v['entry_resume']))), 'failed','failed-entry inventory')

    def test_19_claim_cannot_change_config(self):
        self.check(self.fixture(('continuation-claim:T1/A/ios',lambda v:v['config'].update(path=ROOT+'/foreign.json'))), 'failed','claim assignment/source/config')

    def test_20_version_aware_runner(self):
        self.check(self.fixture(('entry:T1/A/ios:3',lambda v:v['runner'].update(sha256=nc.CODE['independent_native_v3.py']))), 'failed','Version-aware frozen runner')

    def test_21_sdk_resource_scope(self):
        self.check(self.fixture(('sdk:T1/A/ios:3',lambda v:v['journal_prefixes'][0].update(path=ROOT+'/foreign/events.jsonl'))), 'failed','SDK observation belongs')

    def test_22_inventory_cannot_drop_native_log(self):
        def drop(v):
            target=next(k for k in v if k.endswith('/capture/native.log'));v.pop(target)
        self.check(self.fixture(('inventory:T1/A/ios',drop)), 'failed','inventory membership')

    def test_23_unregistered_record_rejected(self):
        def extra(files):files[ROOT+'/cache/business/independent-evaluation/replacement/T1/A/ios/native/ENTRY.json']=b'{}\n'
        self.check(self.fixture(('files',extra)), 'failed','Unregistered/replacement')

    def test_24_missing_image_is_not_unknown_pass(self):
        def remove(files):files.pop(ROOT+'/cache/business/independent-evaluation/continuations/T1/A/ios/native/service/capture/native/frame.png')
        self.check(self.fixture(('files',remove)), 'failed','Synthetic original absent')

    def test_25_altered_image_bytes_rejected(self):
        def alter(files):files[ROOT+'/cache/business/independent-evaluation/continuations/T1/A/ios/native/service/capture/native/frame.png']=b'tampered'
        self.check(self.fixture(('files',alter)), 'failed','Original pin differs')

    def test_26_closed_prefix_cannot_claim_full_namespace(self):
        self.check(self.fixture(('snapshot',lambda v:v.update(complete_record_namespace=True)),prefix=13), 'failed','Prefix cannot claim')

    def test_27_pending_scopes_cannot_be_dropped(self):
        self.check(self.fixture(('snapshot',lambda v:v['pending_scopes'].pop()),prefix=13), 'failed','terminal prefix/pending')

    def test_28_episode_scope_must_bind_operation(self):
        self.check(self.fixture(('episode:T1/A/continuation',lambda v:v['outcomes'].update(android=v['outcomes']['ios']))), 'failed','Episode outcome registration')

    def test_29_accepted_flag_does_not_follow_exit_zero(self):
        self.check(self.fixture(('outcome:T1/A/ios:3',lambda v:v.update(accepted=True))), 'failed','accepted flag inconsistent')

    def test_30_external_snapshot_pin_required(self):
        f=self.fixture();f.snapshot_ref={**f.snapshot_ref,'sha256':'0'*64}
        self.check(f,'failed','Original pin differs')

    def test_31_duplicate_json_rejected(self):
        f=self.fixture();raw=b'{"version":1,"version":1}\n';f.files[f.snapshot_ref['path']]=raw
        physical=f.physical/f.snapshot_ref['path'].lstrip('/');physical.write_bytes(raw);f.snapshot_ref['sha256']=nc.sha(raw)
        self.check(f,'failed','Duplicate JSON key')

    def test_32_grade_reference_never_read(self):
        class Trap:
            def read_bytes(self,p):raise AssertionError('Forbidden content reached reader')
        with self.assertRaisesRegex(ValueError,'Forbidden'):
            nc.Access(Trap()).raw('/recorded/blind-quality/grades/grade.json')
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'matched':True,'expected':'rejected before read','status':'rejected before read'})

    def test_33_symlink_namespace_rejected(self):
        f=self.fixture();target=f.physical/(ROOT+'/cache/business/independent-evaluation/continuations/T1/A/ios/native/service/capture/native/evil.png').lstrip('/')
        target.symlink_to('frame.png');self.check(f,'failed','Symlink')

    def test_34_post_replay_change_rejected(self):
        f=self.fixture();original_hash=f.hash;first=[True]
        def changed(p):
            if first[0]:first[0]=False;return '0'*64
            return original_hash(p)
        f.hash=changed;self.check(f,'failed','changed after replay')

    def test_35_virtual_restore_no_original_paths(self):
        f=self.fixture(prefix=13);mapping,map_sha,index_sha=f.restore(RUN/'virtual-restore')
        spec=importlib.util.spec_from_file_location('synthetic_frozen_resolver',HERE/'schema-code/resolver.py')
        rm=importlib.util.module_from_spec(spec);spec.loader.exec_module(rm)
        resolver=rm.Resolver(mapping,map_sha256=map_sha,index_sha256=index_sha)
        result=nc.verify_chain(resolver,ROOT,f.snapshot_ref)
        self.assertEqual(result['status'],'verified',result);self.assertFalse(result['acquisition_complete'])
        self.assertFalse(Path(ROOT).exists())
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'matched':True,'expected':'verified prefix','status':result['status'],
                        'map_sha256':map_sha,'index_sha256':index_sha,'original_root_exists':False,'result':result})

    def test_36_early_failure_remains_ambiguous_and_unacquired(self):
        result=self.check(self.fixture(terminal_failure='pre_admission'))
        self.assertFalse(result['acquisition_complete']);self.assertEqual(result['acquired_scopes'],29)
        self.assertFalse(result['scopes']['T5/B/android']['complete_supervision_record'])
        self.assertIn('no zero-inner-UI',result['scopes']['T5/B/android']['failure_absence_scope'])

    def test_37_whole_study_requires_final_collector_terminal(self):
        def remove(v):v['collection_controls']=[r for r in v['collection_controls'] if not r['path'].endswith('continuation-collection-v3/END.json')]
        self.check(self.fixture(('snapshot',remove)),'failed','one final v3 collector terminal')

    def test_38_extra_continuation_claim_rejected(self):
        def add(files):files[ROOT+'/cache/business/independent-evaluation/native-continuation-claims/T1/A/third.json']=b'{}\n'
        self.check(self.fixture(('files',add)),'failed','one-shot claim namespace')

    def test_39_unlisted_native_image_rejected(self):
        def add(files):files[ROOT+'/cache/business/independent-evaluation/continuations/T1/A/ios/native/service/capture/native/unlisted.png']=b'synthetic image'
        self.check(self.fixture(('files',add)),'failed','image inventory')

    def test_40_contract_input_substitution_resealed(self):
        self.check(self.fixture(('execution:T1/A/ios',lambda v:v.update(fixtures_sha256=nc.sha(b'foreign-fixtures')))),
                   'failed','execution contract/source input')

    def test_41_profile_admission_dependency_registry(self):
        def alter(v):v['dependency_files'][ROOT+'/admission.py']='0'*64
        self.check(self.fixture(('admission:T1/A/ios',alter)),'failed','dependency registry')

    def test_42_configured_source_model_cannot_be_omitted(self):
        def remove(v):v.pop('source_model');v.pop('source_model_sha256')
        self.check(self.fixture(('capture-request:T1/B/ios',remove)),'failed','source model is missing')

    def test_43_claim_reservation_time_is_bound(self):
        self.check(self.fixture(('continuation-claim:T1/A/ios',lambda v:v.update(reserved_at_unix=999999))),
                   'failed','reservation is outside')

    def test_44_full_virtual_restore(self):
        f=self.fixture();mapping,map_sha,index_sha=f.restore(RUN/'virtual-full-restore')
        spec=importlib.util.spec_from_file_location('synthetic_frozen_full_resolver',HERE/'schema-code/resolver.py')
        rm=importlib.util.module_from_spec(spec);spec.loader.exec_module(rm)
        resolver=rm.Resolver(mapping,map_sha256=map_sha,index_sha256=index_sha)
        result=nc.verify_chain(resolver,ROOT,f.snapshot_ref)
        self.assertEqual(result['status'],'verified',result);self.assertTrue(result['acquisition_complete'])
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'matched':True,'expected':'verified full','status':result['status'],
                        'map_sha256':map_sha,'index_sha256':index_sha,'result':result})

    def test_45_resealed_runtime_must_match_frozen_tool(self):
        self.check(self.fixture(('capture-request:T1/A/ios',lambda v:v['tool_files'].update({'scripts/ui_loop.py':nc.sha(b'foreign-runtime')}))),
                   'failed','frozen tool hash domain')

    def test_46_context_bound_to_current_platform(self):
        self.check(self.fixture(('capture-context:T1/B/ios',lambda v:v.update(platform='android'))),
                   'failed','Recorded capture context differs')

    def test_47_execution_without_observation_pin_is_incomplete(self):
        self.fixture_count=1
        result=self.check(self.fixture(('receipt:T5/B/android',lambda v:v.pop('observation_sha256'))))
        self.assertFalse(result['acquisition_complete']);self.assertEqual(result['acquired_scopes'],29)
        self.assertEqual(result['recorded_native_first_executions'],30)
        self.assertFalse(result['scopes']['T5/B/android']['observation_pinned'])


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    with (RUN/'RUN.log').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    value={'kind':'author-synthetic-native-chain-controls','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
           'passed':result.wasSuccessful(),'controls':RESULTS,'code_pins':{n:nc.sha((RUN/n).read_bytes()) for n in ['native_chain.py','synthetic.py','test_native_chain.py']},
           'synthetic_only':True,'native_sdk_execution':False,'mapping_or_judgments_parsed':False}
    target=RUN/'RESULT.json';target.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'path':str(target),'sha256':nc.sha(target.read_bytes()),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
