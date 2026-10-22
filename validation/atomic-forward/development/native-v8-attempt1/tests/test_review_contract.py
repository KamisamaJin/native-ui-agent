"""Behavioral controls for approved expectations, original pixels and independent panels."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

S = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S / 'scripts'))
import acceptance
import design_contract as d
import native_checks as n
import native_pixels
import review_contract as review


class AtomicReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = S / 'assets/atomic-example'
        self.lock = d.load(source / 'lock.json'); self.lock_sha = d.digest(self.lock)
        self.policy = d.load(source / 'policy.json'); self.policy_sha = d.digest(self.policy)
        self.plan, _ = d.compile_contract(self.lock, self.lock_sha, 'neutral', 'android', d.load(source / 'bindings.json'), d.load(source / 'actions.json'))
        self.cat = review.catalog(self.plan, self.lock, self.lock_sha, self.policy, self.policy_sha, 'android')
        self.obs = {'snapshots': [], 'state_captures': [], 'configuration': {'direction': 'Ltr', 'font_scale': 1., 'night_mode_mask': 16}}
        for index, (state, fill, canvas) in enumerate([('observed', '#397A91', '#D6E8F3'), ('changed', '#976038', '#ECE2D1')]):
            im = Image.new('RGB', (100, 120), canvas)
            ImageDraw.Draw(im).rectangle((10, 20, 69, 49), fill=fill)
            im.save(self.root / (state + '.png'))
            binding = {'fixture_index': index, 'instance': 'neutral-run', 'event_revision': 0, 'input_sha256': 'fixture-' + str(index)}
            nodes = []
            for uid, bounds in [('canvas', [0, 0, 100, 120]), ('tile', [10, 20, 70, 50]), ('title', [10, 2, 70, 18])]:
                nodes.append({'identifier': 'probe.' + uid, 'node_id': len(nodes) + 1, 'parent_id': -1,
                              'intersects_viewport': True, 'fully_visible': True, 'unclipped_bounds_dp': bounds})
            snap = {'state_id': state, 'binding': binding, 'capture_consistent': True, 'binding_after_capture': binding,
                    'screenshot': state + '.png', 'screenshot_pixels': {'width': 100, 'height': 120},
                    'logical_viewport_dp': {'width': 100, 'height': 120}, 'nodes': nodes,
                    'scroll_offset_dp': 0, 'scroll_max_dp': 0, 'viewport_height_dp': 120}
            self.obs['snapshots'].append(snap)
            self.obs['state_captures'].append({'state_id': state, 'after_action': 0 if index == 0 else 2, 'binding': binding,
                                               'snapshot_indices': [index], 'top_reached': True, 'bottom_reached': True, 'stable_binding': True})
        self.obs_sha = d.digest(self.obs)
        self.submission = {'version': 1, 'catalog_sha256': d.digest(self.cat), 'observation_sha256': self.obs_sha, 'decisions': []}
        for row in self.cat['rows']:
            if row['method'] == 'visual':
                self.submission['decisions'].append({'review_id': row['review_id'], 'actual': True, 'reason': 'Original title has no overlap',
                                                     'snapshot_indices': [0 if row['state'] == 'observed' else 1]})

    def bind(self, submission=None, obs=None):
        return review.bind(self.plan, self.lock, self.lock_sha, self.policy, self.policy_sha,
                           obs or self.obs, self.obs_sha, self.root, submission or self.submission, 'android')

    def evaluate(self, manual=None):
        return n.evaluate(self.plan, self.obs, 'android', manual or self.bind(), self.root, self.obs_sha,
                          self.lock, self.lock_sha, self.policy, self.policy_sha)

    def test_tool_generates_expected_unit_and_pixels_without_manual_entry(self):
        manual = self.bind(); findings = manual['review_contract']['findings']
        self.assertTrue(all(f['status'] == 'passed' for f in findings))
        self.assertEqual(findings[0]['expected'], 0xff397a91)
        self.assertEqual(findings[0]['unit'], 'argb')
        self.assertEqual(self.evaluate()['counts'], {'passed': 6, 'failed': 0, 'unassessed': 0})

    def test_cannot_override_expectations_actual_pixels_or_identity(self):
        for key, value in [('expected', False), ('unit', 'string'), ('status', 'passed'), ('target', {'identifier': 'other'})]:
            submitted = copy.deepcopy(self.submission); submitted['decisions'][0][key] = value
            with self.assertRaises(ValueError): self.bind(submitted)
        submitted = copy.deepcopy(self.submission); submitted['decisions'][0]['review_id'] = self.cat['rows'][0]['review_id']
        with self.assertRaises(ValueError): self.bind(submitted)
        for key in ['catalog_sha256', 'observation_sha256']:
            submitted = copy.deepcopy(self.submission); submitted[key] = '0' * 64
            with self.assertRaises(ValueError): self.bind(submitted)

    def test_native_pixel_contradiction_is_not_a_schema_false_alarm(self):
        im = Image.open(self.root / 'observed.png').convert('RGB')
        ImageDraw.Draw(im).rectangle((10, 20, 69, 49), fill='#115522'); im.save(self.root / 'observed.png')
        report = self.evaluate()
        self.assertEqual(report['assertions'][0]['status'], 'failed')
        self.assertEqual(report['assertions'][1]['status'], 'passed')

    def test_bound_bundle_tamper_or_downgrade_is_rejected(self):
        for field, value in [('status', 'failed'), ('reason', 'replacement rationale')]:
            manual = self.bind(); manual['decisions'][0][field] = value
            with self.assertRaises(ValueError): self.evaluate(manual)
        manual = self.bind(); manual['review_contract']['findings'][0]['expected'] = 0
        with self.assertRaises(ValueError): self.evaluate(manual)
        manual = self.bind(); del manual['review_contract']
        with self.assertRaises(ValueError): self.evaluate(manual)
        with self.assertRaises(ValueError):
            n.evaluate(self.plan, self.obs, 'android', self.bind(), self.root, self.obs_sha, self.lock, self.lock_sha)

    def test_cross_state_and_input_drift_cannot_borrow_evidence(self):
        submitted = copy.deepcopy(self.submission); submitted['decisions'][0]['snapshot_indices'] = [1]
        with self.assertRaises(ValueError): self.bind(submitted)
        obs = copy.deepcopy(self.obs); obs['snapshots'][0]['binding'] = dict(obs['snapshots'][0]['binding'], fixture_index=99)
        with self.assertRaises(ValueError): self.bind(obs=obs)
        manual = self.bind(submission=dict(self.submission, decisions=[]), obs=obs)
        self.assertTrue(all(f['status'] == 'unassessed' for f in manual['review_contract']['findings'][:3]))

    def test_missing_visual_review_stays_unknown(self):
        submission = dict(self.submission, decisions=[])
        manual = self.bind(submission)
        self.assertEqual([r['status'] for r in manual['decisions']].count('unassessed'), 2)

    def test_sampling_uncertainty_transparency_and_mapping_are_not_passes(self):
        spec = self.policy['atoms'][0]['sampling']; snap = self.obs['snapshots'][0]
        im = Image.open(self.root / 'observed.png').convert('RGB'); pix = im.load()
        for y in range(20, 50):
            for x in range(10, 70):pix[x, y] = (0, 0, 0) if (x + y) % 2 else (255, 255, 255)
        im.save(self.root / 'observed.png')
        self.assertEqual(native_pixels.sample(snap, {'identifier': 'probe.tile'}, 'android', self.root, spec)['status'], 'unassessed')
        bad = copy.deepcopy(snap); bad['screenshot_pixels']['width'] = 99
        with self.assertRaises(ValueError): native_pixels.sample(bad, {'identifier': 'probe.tile'}, 'android', self.root, spec)

    def test_policy_cannot_omit_atoms_guess_owner_or_be_repinned_in_submission(self):
        policy = copy.deepcopy(self.policy); policy['atoms'].pop()
        with self.assertRaises(ValueError): review.catalog(self.plan, self.lock, self.lock_sha, policy, d.digest(policy), 'android')
        policy = copy.deepcopy(self.policy); policy['ownership']['canvas'] = 'unknown'
        with self.assertRaises(ValueError): review.catalog(self.plan, self.lock, self.lock_sha, policy, d.digest(policy), 'android')
        policy = copy.deepcopy(self.policy); policy['atoms'][0]['expected'] = '#FFFF0000'
        with self.assertRaises(ValueError): review.catalog(self.plan, self.lock, self.lock_sha, policy, d.digest(policy), 'android')

    def test_native_environment_uses_actual_wire_and_rejects_unknown(self):
        expected = {'width': 100, 'height': 120, 'direction': 'ltr', 'theme': 'light', 'font_scale': 1.}
        self.assertEqual(acceptance.environment(self.obs, expected, 'android')['status'], 'P')
        obs = copy.deepcopy(self.obs); obs['configuration']['direction'] = 'LTR'
        self.assertEqual(acceptance.environment(obs, expected, 'android')['status'], 'F')
        obs = copy.deepcopy(self.obs); del obs['configuration']['font_scale']
        self.assertEqual(acceptance.environment(obs, expected, 'android')['status'], 'U')

    def test_explicit_native_screen_quantization_is_not_a_layout_tolerance(self):
        import struct
        f32 = lambda x: struct.unpack('!f', struct.pack('!f', x))[0]
        expected = {'width': 390, 'height': 600, 'direction': 'ltr', 'theme': 'light', 'font_scale': 1.,
                    'dimension_encoding': 'paparazzi-float32-screen-config-v1'}
        obs = copy.deepcopy(self.obs)
        obs['configuration'].update(dimension_encoding=expected['dimension_encoding'], requested_width_dp=390., requested_height_dp=600., density=2.75)
        for s in obs['snapshots']:
            s['native_viewport_px'] = {'width': 1072, 'height': 1650, 'density': 2.75}
            s['logical_viewport_dp'] = {'width': f32(1072 / 2.75), 'height': 600.}
        result = acceptance.environment(obs, expected, 'android')
        self.assertEqual(result['status'], 'P')
        self.assertNotEqual(result['frames'][0]['actual']['width'], 390)
        obs['snapshots'][0]['native_viewport_px']['width'] += 1
        self.assertEqual(acceptance.environment(obs, expected, 'android')['status'], 'F')
        del obs['snapshots'][0]['native_viewport_px']
        self.assertEqual(acceptance.environment(obs, expected, 'android')['status'], 'U')

    def test_disagreement_retained_and_pixels_cannot_be_voted_away(self):
        a = self.evaluate(); b = copy.deepcopy(a); b['assertions'][2]['status'] = 'failed'
        b['assertions'][0]['status'] = 'failed'
        env = {'status': 'P'}
        merged = acceptance.consensus(self.plan, a, a, b, self.cat, env)
        self.assertEqual(merged['rows'][0]['status'], 'passed')
        self.assertEqual(merged['rows'][2]['status'], 'unassessed')
        self.assertTrue(merged['rows'][2]['panel_disagreement'])
        gated = acceptance.consensus(self.plan, a, a, b, self.cat, {'status': 'F'})
        self.assertTrue(all(r['status'] == 'unassessed' for r in gated['rows']))
        self.assertEqual(gated['rows'][0]['ungated_fact_status'], 'passed')

    def test_full_acceptance_requires_independent_cause_support(self):
        im = Image.open(self.root / 'observed.png').convert('RGB')
        ImageDraw.Draw(im).rectangle((10, 20, 69, 49), fill='#115522'); im.save(self.root / 'observed.png')
        expected = {'width': 100, 'height': 120, 'direction': 'ltr', 'theme': 'light', 'font_scale': 1.}
        attribution = {'id': 'observed/tile-fill', 'cause': 'product', 'reason': 'Original solid tile contradicts the independently approved fill', 'snapshot_indices': [0]}
        judge = {'review': self.submission, 'attributions': [attribution]}
        def evaluate(a, b):
            return acceptance.evaluate(self.plan, self.lock, self.lock_sha, self.policy, self.policy_sha,
                                       self.obs, self.obs_sha, self.root, 'android', expected, a, b)
        report = evaluate(judge, judge)
        self.assertEqual(report['rows'][0]['status'], 'failed')
        self.assertEqual(report['rows'][0]['cause_category'], 'product')
        other = copy.deepcopy(judge); other['attributions'][0]['cause'] = 'observation'
        report = evaluate(judge, other)
        self.assertEqual(report['rows'][0]['status'], 'failed')
        self.assertEqual(report['rows'][0]['cause_category'], 'uncertain')
        other['attributions'][0]['snapshot_indices'] = [1]
        with self.assertRaises(ValueError): evaluate(judge, other)

    def test_source_backed_question_and_rendered_channel_semantics(self):
        policy = copy.deepcopy(self.policy)
        policy['atoms'][2]['question'] = {'source': 'reference', 'pointer': '/visual/noOverlap'}
        with self.assertRaises(ValueError): review.catalog(self.plan, self.lock, self.lock_sha, policy, d.digest(policy), 'android')
        self.assertTrue(native_pixels.matches(0xff10ff00, 0xff110000, 255))
        self.assertFalse(native_pixels.matches(0xff10ff00, 0xff110000, 1))
        with self.assertRaises(ValueError): native_pixels.matches(0xff000000, 0x7f000000, 0)

    def test_ios_mapping_uses_app_frame_and_clips_to_actual_viewport(self):
        snapshot = {'app_frame': {'x': 0, 'y': 0, 'width': 100, 'height': 200},
                    'viewport': {'x': 10, 'y': 20, 'width': 80, 'height': 120},
                    'screenshot_pixels': {'width': 300, 'height': 600}}
        node = {'frame': {'x': 15, 'y': 30, 'width': 20, 'height': 40}}
        box, clip = native_pixels.image_rectangle(snapshot, node, 'ios', (300, 600))
        self.assertEqual(box, [45, 90, 105, 210])
        self.assertEqual(clip, [30, 60, 270, 420])

    def test_mixed_coherent_pixel_values_and_missing_target_do_not_manufacture_pass(self):
        obs = copy.deepcopy(self.obs)
        other = copy.deepcopy(obs['snapshots'][0]); other['screenshot'] = 'different.png'
        Image.new('RGB', (100, 120), '#445566').save(self.root / 'different.png')
        obs['snapshots'].append(other); obs['state_captures'][0]['snapshot_indices'].append(2)
        manual = self.bind(obs=obs)
        self.assertEqual(manual['decisions'][0]['status'], 'unassessed')
        self.assertEqual(len(manual['review_contract']['findings'][0]['actual']['samples']), 2)


if __name__ == '__main__':
    unittest.main()
