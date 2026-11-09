import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import action_guard as ag
import evidence_responsibility as er
import resource_manager as rm
import design_contract as d
import test_delivery_plan as fixtures
import feedback_loop as loop


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.source = self.root/'Component.swift'; self.source.write_text('production')
        self.config = {'source_roots': [str(self.source)], 'native_options': {},
                       'resources': {'root': str(self.root/'scratch'), 'min_free_bytes': 0, 'sample_seconds': .1}}

    def test_success_final_reclaims_only_owned_scratch_and_retains_evidence(self):
        evidence = self.root/'final'; user = self.root/'user'; user.mkdir(); (user/'important').write_text('keep')
        with rm.Resources(self.config, evidence, final=True) as resources:
            (resources.directory('build')/'object').write_bytes(b'a'*8192)
            with (self.root/'child.log').open('w') as log:
                result = resources.run([sys.executable, '-c', 'print("actual native stand-in process")'], env=dict(__import__('os').environ), stdout=log)
            self.assertEqual(result, 0)
        self.assertFalse((self.root/'scratch/build').exists()); self.assertEqual((user/'important').read_text(), 'keep')
        self.assertEqual(self.source.read_text(), 'production'); self.assertTrue((evidence/'resources.json').is_file())
        self.assertIn('actual native stand-in', (self.root/'child.log').read_text())

    def test_live_lease_and_marker_substitution_never_delete(self):
        with rm.Resources(self.config, self.root/'one') as resources:
            with self.assertRaises(RuntimeError):
                with rm.Resources(self.config, self.root/'two'): pass
            p = resources.directory('build'); (p/'.native-ui-owner.json').write_text('{}')
        with self.assertRaises(ValueError):
            with rm.Resources(self.config, self.root/'three') as resources: resources.directory('build')
        self.assertTrue((self.root/'scratch/build').exists())

    def test_budget_stops_actual_owned_process_and_preserves_failure(self):
        self.config['resources']['max_bytes'] = 500_000
        with self.assertRaisesRegex(RuntimeError, 'byte budget'):
            with rm.Resources(self.config, self.root/'failed') as resources:
                p = resources.directory('build')/'large'
                with (self.root/'process.log').open('w') as log:
                    resources.run([sys.executable, '-c', 'from pathlib import Path; import time; Path('+repr(str(p))+').write_bytes(b"a"*2_000_000); time.sleep(20)'], env=dict(__import__('os').environ), stdout=log)
        receipt = json.loads((self.root/'failed/resources.json').read_text())
        self.assertEqual(receipt['primary_error']['type'], 'RuntimeError'); self.assertFalse((self.root/'scratch/build').exists())

    def test_unowned_root_and_source_overlap_rejected(self):
        (self.root/'scratch').mkdir()
        with self.assertRaises(ValueError):
            with rm.Resources(self.config, self.root/'result'): pass
        self.config['resources']['root'] = str(self.root)
        with self.assertRaises(ValueError): rm.Resources(self.config, self.root/'result')

    def test_returned_command_does_not_leave_a_heartbeat_descendant(self):
        heartbeat=self.root/'heartbeat'; child='from pathlib import Path; import time\np=Path('+repr(str(heartbeat))+')\nwhile True:\n p.write_text(str(time.time_ns()));time.sleep(.05)'
        body='import subprocess,sys,time\nsubprocess.Popen([sys.executable,"-c",'+repr(child)+'])\ntime.sleep(.5)'
        with rm.Resources(self.config,self.root/'done',final=True) as resources:
            with (self.root/'child.log').open('w') as log:
                self.assertEqual(resources.run([sys.executable,'-c',body],env=dict(__import__('os').environ),stdout=log),0)
        self.assertTrue(heartbeat.is_file()); after=heartbeat.read_bytes();time.sleep(.25);self.assertEqual(heartbeat.read_bytes(),after)

    def test_corrupt_checkpoint_recovers_owned_directory_from_durable_copy(self):
        with rm.Resources(self.config,self.root/'first') as resources: resources.directory('compiled')
        (self.root/'scratch/journal.json').write_text('{truncated')
        with rm.Resources(self.config,self.root/'recovered',final=True):pass
        self.assertFalse((self.root/'scratch/compiled').exists())
        self.assertIn('journal_recovered',(self.root/'recovered/resource-events.jsonl').read_text())

    def test_timeout_retains_primary_error_and_repeat_finish_is_nonmutating(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            with rm.Resources(self.config,self.root/'timed') as resources:
                with (self.root/'timeout.log').open('w') as log:resources.run([sys.executable,'-c','import time;time.sleep(20)'],env=dict(__import__('os').environ),stdout=log,timeout=.25)
        self.assertEqual(json.loads((self.root/'timed/resources.json').read_text())['primary_error']['type'],'TimeoutExpired')
        resources=rm.Resources(self.config,self.root/'repeat',final=True)
        resources.__enter__();resources.directory('temporary');resources.release('temporary');resources.finish()
        original=(self.root/'repeat/resources.json').read_bytes();resources.finish()
        self.assertEqual((self.root/'repeat/resources.json').read_bytes(),original)


class ActionTests(unittest.TestCase):
    def test_forward_and_unknown_dependencies_rejected_before_execution(self):
        for deps in [[0], [1], [-1], [False]]:
            with self.assertRaises(ValueError): ag.compile_actions([{'type': 'checkpoint', 'depends_on': deps}])

    def test_causal_block_does_not_erase_independent_sibling(self):
        actions = ag.compile_actions([{'type':'tap','target':{'identifier':'missing'}},
            {'type':'checkpoint'}, {'type':'checkpoint','depends_on':[]}])
        def proof(i, established):
            return {'action': actions[i], 'guard': {'protocol':1,'depends_on':actions[i]['depends_on'],'conditions':[],'binding':{'instance':'same'},'ready':True,'established':established},
                    'binding_after':{'instance':'same'}, 'outcome':'observed'}
        rows = ag.replay(actions, [proof(0,False), proof(1,True), proof(2,True)], 'android')
        self.assertFalse(rows[0]['established']); self.assertFalse(rows[1]['established']); self.assertTrue(rows[2]['established'])

    def test_actual_typed_predicate_is_replayed_not_boolean_flag(self):
        condition = {'target': {'identifier':'control'},'property':'enabled','op':'eq','expected':True}
        action = ag.compile_actions([{'type':'checkpoint','preconditions':[condition]}])[0]
        step = {'outcome':'observed','binding_after':{'instance':'same'},'guard':{'protocol':1,'depends_on':[],
            'ready':True,'established':True,'conditions':[{'condition':condition,'actual':False,'passed':True}]}}
        self.assertFalse(ag.replay([action],[step],'android')[0]['established'])


class ResponsibilityTests(unittest.TestCase):
    setUp = fixtures.DeliveryPlanTests.setUp
    audit = fixtures.DeliveryPlanTests.audit

    def config(self, owner='bridge', method='source'):
        root = Path(self.temp.name); source = root/'Component.swift'; source.write_text('let token = 16')
        bridge = root/'Bridge.swift'; bridge.write_text('let input = "actual caller"')
        lock = copy.deepcopy(self.lock); lock['sources']['reference']['document']['claims'] = [
            {'id':'binding','clause':'The bridge reads the real caller input.','priority':'must','owner':owner,'method':method,'subject':'actual_bridge','rule_ids':[]}]
        # The separately pinned lock must be resealed from its actual source.
        ref = root/'reference.json'; ref.write_text(json.dumps(lock['sources']['reference']['document']))
        contract = json.loads((root/'contract.json').read_text()); contract['sources'][0]['sha256'] = er.sha(ref)
        (root/'contract.json').write_text(json.dumps(contract)); lock = d.seal(root/'contract.json',root); lock_sha = d.digest(lock)
        plan,_ = d.compile_contract(lock,lock_sha,'public','ios',self.plan['design_contract']['bindings'],self.plan['design_contract']['base_actions'])
        config = {'source_roots':[str(source)],'bridge':str(bridge),'design_sha256':lock_sha,
                  'responsibility_ref':{'source':'reference','pointer':'/claims'},'evidence_subjects':{'actual_bridge':[str(bridge)]},
                  'source_review_store':str(root/'reviews')}
        for key,obj in [('plan',plan),('design_lock',lock)]:
            path=root/(key+'.json');path.write_text(json.dumps(obj));config[key]=str(path)
        return config,plan,lock

    def test_wrong_subject_and_runtime_claim_block_before_sdk(self):
        config,plan,lock = self.config()
        config['evidence_subjects']['actual_bridge']=config['source_roots']
        self.assertTrue(er.compile_contract(config,plan,lock)['issues'])
        config,plan,lock = self.config(method='computed_style')
        self.assertTrue(er.compile_contract(config,plan,lock)['issues'])

    def test_bound_source_actual_auto_imported_and_edit_invalidates(self):
        config,plan,lock = self.config(); root=Path(self.temp.name)
        compiled=er.compile_contract(config,plan,lock);self.assertEqual(er.evaluate(config,compiled)['blocking_claims'],['binding'])
        submission={'version':1,'observations':[{'id':'binding','observed':True,'reason':'Reads actual caller input.','citations':[{'path':config['bridge'],'line':1}]}]}
        er.bind(config,submission,root/'receipt.json')
        self.assertEqual(er.evaluate(config,compiled)['blocking_claims'],[])
        Path(config['bridge']).write_text('different caller input binding')
        self.assertEqual(er.evaluate(config,er.compile_contract(config,plan,lock))['blocking_claims'],['binding'])

    def test_source_review_cannot_override_expected_or_cite_other_owner(self):
        config,plan,lock=self.config();root=Path(self.temp.name)
        submission={'version':1,'observations':[{'id':'binding','observed':True,'reason':'claim','citations':[{'path':config['source_roots'][0],'line':1}]}]}
        with self.assertRaises(ValueError):er.bind(config,submission,root/'bad.json')
        submission['observations'][0]['expected']=False
        with self.assertRaises(ValueError):er.bind(config,submission,root/'bad2.json')


if __name__ == '__main__': unittest.main()
