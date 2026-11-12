#!/usr/bin/env python3
"""HOST/SIM v2 tests: synthetic independent approvals, NO SDK forwarding."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import unittest

import test_blind_study as base

b, put = base.b, base.put

PROFILE_GUARD = '''
import hashlib,json
from pathlib import Path
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def verify(root,approval,approval_sha,platform,config):
    if digest(approval)!=approval_sha: raise ValueError('approval pin')
    wanted=approval['profiles'][platform]
    for key in ['design_lock','plan','policy','routes','environment','fixtures']:
        if str(Path(config[key]).resolve())!=wanted[key]['path'] or digest(json.loads(Path(config[key]).read_text()))!=wanted[key]['sha256']:
            raise ValueError('profile '+key)
    if str(Path(config['bridge']).resolve())!=wanted['bridge']['path'] or hashlib.sha256(Path(config['bridge']).read_bytes()).hexdigest()!=wanted['bridge']['sha256']:
        raise ValueError('profile bridge')
    plan=json.loads(Path(config['plan']).read_text())
    if plan['design_contract']['platform']!=platform or plan['design_contract']['lock_sha256']!=config['design_sha256']:
        raise ValueError('profile platform/lock')
    return {'status':'admitted_profile','platform':platform,'design_sha256':config['design_sha256'],'plan_sha256':wanted['plan']['sha256'],'scope':'HOST/SIM pure config guard; no native work'}
'''


def enable_domain(f):
    root = Path(f.manifest['protocol']['path']).parent
    reviewer = root / 'independent-reviewer' / 'shape-reviewer'; reviewer.mkdir(parents=True)
    registry = put(root / 'REVIEW-REGISTRY.json', {'version': 1, 'kind': 'independent-source-domain-review-registry',
                   'reviewers': {'shape-reviewer': {'root': str(reviewer), 'scope': 'source_shape_only'}}, 'operators': ['controller']})
    f.manifest['source_domain_reviews'] = {'registry': {'path': registry, 'sha256': b.sha(registry)}, 'max_requests_per_arm': 4}
    for t in f.manifest['tasks']:
        for a in t['arms'].values():
            folder = Path(a['workspace']).parent
            component = Path(a['source_roots'][0]) / 'Opaque.txt'
            bridge = put(folder / 'public-design/Bridge.txt', 'HOST/SIM exact bridge bytes\n')
            approval = {'version': 1, 'scope': 'HOST/SIM finite source shape, no behavior/oracle claim',
                        'common_host_shape': {'finite': True}, 'expected_policy': {'must_remain': 'identical SIM value'},
                        'actual_subject_binding': {'component_subject': 'component', 'bridge_subject': 'bridge'},
                        'platforms': {p: {'component_install_path': 'Sources/Opaque.txt', 'exact_bridge': {'sha256': b.sha(bridge)},
                                         'approved_component_revisions': {'initial': {'sha256': b.sha(component), 'bytes': component.stat().st_size}}}
                                      for p in ['ios', 'android']}}
            domain_path = put(folder / 'public-design/DOMAIN.json', approval)
            provider = put(folder / 'public-design/PROVIDER.json', {'scope': 'HOST/SIM unchanged provider'})
            guarded = {}
            for profile, path in a['public_configs'].items():
                c = b.load(path)
                for key in ['design_lock', 'policy', 'routes', 'environment', 'fixtures']:
                    c[key] = put(folder / 'public-design' / profile / (key + '.json'), {'kind': key, 'profile': profile, 'scope': 'HOST/SIM only'})
                c['design_sha256'] = b.digest(b.load(c['design_lock']))
                c['plan'] = put(folder / 'public-design' / profile / 'plan.json', {'design_contract': {'platform': profile, 'lock_sha256': c['design_sha256']}})
                c['bridge'] = bridge
                c['evidence_subjects'] = {'component': [str(component)], 'bridge': [bridge]}
                c['coverage_domain_ref'] = {'path': domain_path, 'sha256': b.digest(approval)}
                c['coverage_provider_ref'] = {'path': provider, 'sha256': b.digest(b.load(provider))}
                c['native_options']['package' if profile == 'ios' else 'project'] = a['workspace']
                put(path, c)
                a['public_readset'] += [c[k] for k in ['design_lock', 'plan', 'policy', 'routes', 'environment', 'fixtures', 'bridge']]
                guarded[profile] = {k: {'path': str(Path(c[k]).resolve()), 'sha256': b.digest(b.load(c[k]))} for k in ['design_lock', 'plan', 'policy', 'routes', 'environment', 'fixtures']}
                guarded[profile]['bridge'] = {'path': bridge, 'sha256': b.sha(bridge)}
            script = put(folder / 'public-design/admit_profile.py', PROFILE_GUARD)
            profile_approval = put(folder / 'public-design/PROFILE-APPROVAL.json', {'profiles': guarded})
            a['profile_admissions'] = {p: {'script': script, 'root': str(folder / 'public-design'), 'approval': profile_approval,
                                          'approval_sha256': b.digest(b.load(profile_approval))} for p in a['public_configs']}


class DomainTests(unittest.TestCase):
    def setUp(self):
        base.ControllerTests.setUp(self)
        enable_domain(self.fixture)

    def tearDown(self):
        base.ControllerTests.tearDown(self)

    def ready(self, alias='A'):
        f = self.fixture
        if not hasattr(f, 'study'):
            f.init(); f.study.admit('T1')
        f.d0(alias=alias); f.study.feedback_ready('T1', alias)
        component = Path(f.study.arm('T1', alias)['source_roots'][0]) / 'Opaque.txt'
        component.write_text('HOST/SIM independently reviewed current patch ' + alias + '\n')
        return f.study

    def review(self, event, mutate=None):
        f = self.fixture; s = f.study; request = b.load(event['request']['path'])
        authority, identities = s.domain_authority()
        folder = Path(identities['shape-reviewer']['path']) / request['request_id']; folder.mkdir()
        previous = b.load(request['parent_approval']['path']); proposed = copy.deepcopy(previous)
        proposed['platforms'][request['platform']]['approved_component_revisions']['reviewed_current'] = {k: request['component'][k] for k in ['sha256', 'bytes']}
        if mutate: mutate(proposed, request)
        put(folder / 'approval.json', proposed)
        shutil.copyfile(request['component_capsule']['path'], folder / 'component.source')
        record = {'version': 1, 'kind': 'independent-source-domain-review', 'reviewer_id': 'shape-reviewer', 'scope': 'source_shape_only',
                  'decision': 'approved', 'request_id': request['request_id'], 'request_sha256': event['request']['sha256'],
                  'study_id': request['study_id'], 'task': request['task'], 'arm': request['arm'], 'profile': request['profile'], 'platform': request['platform'],
                  'source_sha256': request['source']['content_sha256'], 'component': request['component'],
                  'parent_approval_sha256': request['parent_approval_sha256'], 'proposed_approval_sha256': b.digest(proposed),
                  'policy_sha256': request['policy_sha256'], 'config_sha256': request['active_config']['sha256'],
                  'reason': 'HOST/SIM independent source-shape observation only; no business/native quality claim'}
        put(folder / 'review.json', record)
        seal = put(folder / 'SEAL.json', {'version': 1, 'kind': 'source-domain-review-seal', 'reviewer_id': 'shape-reviewer',
                                        'files': {p: b.sha(folder / p) for p in ['review.json', 'approval.json', 'component.source']}})
        provenance = put(Path(f.temp if hasattr(f, 'temp') else self.temp) / ('provenance-' + request['request_id'] + '.json'),
                         {'version': 1, 'kind': 'independent-source-domain-review-provenance', 'request_id': request['request_id'],
                          'review_seal_sha256': b.sha(seal), 'reviewer_id': 'shape-reviewer', 'operator_id': 'controller',
                          'independent_of_repair': True, 'delivery_reference': 'HOST/SIM separately delivered independent review'})
        return {'request_id': request['request_id'], 'seal': seal, 'seal_sha': b.sha(seal), 'provenance': provenance, 'provenance_sha': b.sha(provenance)}

    def test_exact_append_active_config_both_arms_and_default_transport(self):
        f = self.fixture
        for alias in ['A', 'B']:
            s = self.ready(alias)
            anchor = s.one('T1', alias, 'repair_started')
            original = s.active_configs('T1', alias)['ios']; old = b.load(original['path'])
            event = s.request_domain_review('T1', alias, 'ios'); admitted = s.admit_domain_review(**self.review(event))
            active = s.active_configs('T1', alias)['ios']; new = b.load(active['path'])
            self.assertEqual(b.sha(original['path']), original['sha256'])
            self.assertEqual({k: v for k, v in old.items() if k != 'coverage_domain_ref'}, {k: v for k, v in new.items() if k != 'coverage_domain_ref'})
            self.assertEqual(b.domain.digest(b.domain.policy(b.load(old['coverage_domain_ref']['path']))), b.domain.digest(b.domain.policy(b.load(new['coverage_domain_ref']['path']))))
            self.assertEqual(s.one('T1', alias, 'repair_started'), anchor)
            self.assertEqual(admitted['source_deadline_clock'], anchor['deadline_clock'])
            s.enqueue('T1', alias, 'diagnostic'); result = s.serve(f.execute)
            self.assertTrue(all(not o.get('error') for o in result['outcomes']))
            call = [c for c in f.calls if c['arm'] == alias and c['profile'] == 'ios'][-1]
            self.assertEqual(call['argv'][call['argv'].index('--config') + 1], active['path'])
            self.assertEqual('--previous' in call['argv'], alias == 'A')
            if alias == 'B': self.assertNotIn('--history', call['argv'])

    def test_policy_and_prior_revision_mutations_are_rejected(self):
        s = self.ready()
        for mutate in [lambda a, r: a['expected_policy'].update(must_remain='changed'),
                       lambda a, r: a['platforms']['ios']['approved_component_revisions'].pop('initial'),
                       lambda a, r: a['platforms']['ios']['approved_component_revisions']['initial'].update(bytes=1),
                       lambda a, r: a['platforms']['ios']['approved_component_revisions'].update(duplicate=dict(a['platforms']['ios']['approved_component_revisions']['reviewed_current']))]:
            event = s.request_domain_review('T1', 'A', 'ios')
            with self.assertRaises(ValueError): s.admit_domain_review(**self.review(event, mutate))
        self.assertEqual(s.history('T1', 'A', 'domain_review_admitted'), [])
        with self.assertRaisesRegex(ValueError, 'cap'): s.request_domain_review('T1', 'A', 'ios')

    def test_source_change_after_independent_review_is_rejected(self):
        s = self.ready(); event = s.request_domain_review('T1', 'A', 'ios'); response = self.review(event)
        Path(b.load(event['request']['path'])['component']['path']).write_text('HOST/SIM changed after review')
        with self.assertRaisesRegex(ValueError, 'stale'): s.admit_domain_review(**response)

    def test_future_sha_bytes_wildcard_and_unreviewed_extra_revision_rejected(self):
        s = self.ready()
        for mutate in [lambda a, r: a['platforms']['ios']['approved_component_revisions']['reviewed_current'].update(sha256='0' * 64),
                       lambda a, r: a['platforms']['ios']['approved_component_revisions']['reviewed_current'].update(bytes=r['component']['bytes'] + 1),
                       lambda a, r: a['platforms']['ios']['approved_component_revisions']['reviewed_current'].update(sha256='*'),
                       lambda a, r: a['platforms']['android']['approved_component_revisions'].update(future={'sha256': '1' * 64, 'bytes': 42})]:
            event = s.request_domain_review('T1', 'A', 'ios')
            with self.assertRaises(ValueError): s.admit_domain_review(**self.review(event, mutate))
        self.assertEqual(len(s.history(kind='domain_review_rejected')), 4)

    def test_forged_seal_and_operator_provenance_rejected(self):
        s = self.ready(); event = s.request_domain_review('T1', 'A', 'ios'); response = self.review(event)
        with self.assertRaisesRegex(ValueError, 'forged'):
            s.admit_domain_review(**{**response, 'seal_sha': '0' * 64})
        self.assertEqual(s.history(kind='domain_review_rejected')[-1]['request_id'], response['request_id'])
        provenance = b.load(response['provenance']); provenance['independent_of_repair'] = False; put(response['provenance'], provenance)
        response['provenance_sha'] = b.sha(response['provenance'])
        with self.assertRaisesRegex(ValueError, 'Trusted operator'): s.admit_domain_review(**response)

    def test_original_seal_path_cannot_be_substituted_with_symlink(self):
        s = self.ready(); event = s.request_domain_review('T1', 'A', 'ios'); response = self.review(event)
        alias = Path(self.temp) / 'aliased-review-seal.json'; alias.symlink_to(response['seal'])
        with self.assertRaisesRegex(ValueError, 'real original paths'):
            s.admit_domain_review(**{**response, 'seal': str(alias)})

    def test_wrong_task_arm_path_sha_bytes_or_reviewer_rejected(self):
        s = self.ready(); event = s.request_domain_review('T1', 'A', 'ios'); response = self.review(event)
        folder = Path(response['seal']).parent
        original = b.load(folder / 'review.json')
        for key, value in [('task', 'T2'), ('arm', 'B'), ('component', {'path': '/foreign', 'sha256': '0' * 64, 'bytes': 0})]:
            record = {**original, key: value}; put(folder / 'review.json', record)
            seal = b.load(response['seal']); seal['files']['review.json'] = b.sha(folder / 'review.json'); put(response['seal'], seal)
            response['seal_sha'] = b.sha(response['seal'])
            provenance = b.load(response['provenance']); provenance['review_seal_sha256'] = response['seal_sha']; put(response['provenance'], provenance); response['provenance_sha'] = b.sha(response['provenance'])
            with self.assertRaisesRegex(ValueError, 'exact request'): s.admit_domain_review(**response)
        put(folder / 'review.json', original)
        seal = b.load(response['seal']); seal['reviewer_id'] = 'unregistered'; seal['files']['review.json'] = b.sha(folder / 'review.json'); put(response['seal'], seal)
        response['seal_sha'] = b.sha(response['seal'])
        with self.assertRaisesRegex(ValueError, 'Unregistered'): s.admit_domain_review(**response)

    def test_bridge_fixture_provider_original_config_mutations_rejected(self):
        s = self.ready(); event = s.request_domain_review('T1', 'A', 'ios'); response = self.review(event)
        c = b.load(s.arm('T1', 'A')['public_configs']['ios'])
        for path in [c['bridge'], c['fixtures'], c['coverage_provider_ref']['path'], s.arm('T1', 'A')['public_configs']['ios']]:
            p = Path(path); original = p.read_bytes(); p.write_text('HOST/SIM tamper')
            with self.assertRaisesRegex(ValueError, 'public input'): s.admit_domain_review(**response)
            p.write_bytes(original)

    def test_no_config_admission_during_pending_native_ticket(self):
        s = self.ready(); event = s.request_domain_review('T1', 'A', 'ios'); response = self.review(event)
        s.enqueue('T1', 'A', 'diagnostic')
        with self.assertRaisesRegex(ValueError, 'pending native ticket'): s.admit_domain_review(**response)
        with self.assertRaisesRegex(ValueError, 'pending native ticket'): s.request_domain_review('T1', 'A', 'ios')

    def test_readonly_source_lock_allows_review_without_deadline_reset(self):
        s = self.ready(); anchor = s.one('T1', 'A', 'repair_started'); s.lock_source('T1', 'A')
        event = s.request_domain_review('T1', 'A', 'ios'); admitted = s.admit_domain_review(**self.review(event))
        self.assertEqual(admitted['source_deadline_clock'], anchor['deadline_clock'])
        self.assertFalse(Path(admitted['component']['path']).stat().st_mode & 0o222)
        self.assertEqual(s.one('T1', 'A', 'source_locked')['source_sha256'], b.load(event['request']['path'])['source']['content_sha256'])

    def test_after_self_seal_and_cohort_reject_and_chain_tamper_is_visible(self):
        f = self.fixture; s = self.ready(); event = s.request_domain_review('T1', 'A', 'ios'); response = self.review(event)
        admitted = s.admit_domain_review(**response); s.lock_source('T1', 'A'); s.enqueue('T1', 'A', 'final'); s.serve(f.execute)
        claim = put(Path(self.temp) / 'selfclaim.json', {'statement': 'HOST/SIM only'})
        s.seal_self('T1', 'A', claim)
        with self.assertRaisesRegex(ValueError, 'final self/cohort'): s.admit_domain_review(**response)
        with self.assertRaisesRegex(ValueError, 'before final self/cohort'): s.request_domain_review('T1', 'A', 'ios')
        f.d0(alias='B'); s.feedback_ready('T1', 'B'); s.lock_source('T1', 'B'); s.enqueue('T1', 'B', 'final'); s.serve(f.execute); s.seal_self('T1', 'B', claim)
        for n in range(2, 6): f.finish_task('T' + str(n))
        s.seal_cohort()
        with self.assertRaisesRegex(ValueError, 'final self/cohort'): s.admit_domain_review(**response)
        p = Path(admitted['config']['path']); p.chmod(0o644); changed = b.load(p); changed['bridge'] = '/foreign'; put(p, changed)
        with self.assertRaisesRegex(ValueError, 'version changed'): s.authorize_hidden()

    def test_default_profile_hook_rejects_wrong_fixture_before_any_forwarding(self):
        f = self.fixture
        arm = f.manifest['tasks'][0]['arms']['A']; config = b.load(arm['public_configs']['ios'])
        put(config['fixtures'], {'scope': 'HOST/SIM wrong immutable fixture before init'})
        s = f.init(); s.admit('T1'); s.enqueue('T1', 'A', 'diagnostic'); result = s.serve(f.execute)
        ios = next(o for o in result['outcomes'] if o['profile'] == 'ios')
        self.assertIn('profile fixtures', ios['error']['message'])
        self.assertFalse(any(c['profile'] == 'ios' for c in f.calls))

    def test_profile_hook_pins_exact_active_config_receipt_and_actual_platform(self):
        f = self.fixture; s = self.ready(); event = s.request_domain_review('T1', 'A', 'ios'); admitted = s.admit_domain_review(**self.review(event))
        receipt = b.load(Path(admitted['config']['path']).parent / 'profile-admission.json')
        self.assertEqual(receipt['config']['sha256'], admitted['config']['sha256'])
        self.assertEqual(receipt['config']['canonical_sha256'], b.digest(b.load(admitted['config']['path'])))
        self.assertEqual(receipt['platform'], 'ios')
        self.assertEqual(receipt['platform_source'], 'actual config.plan.design_contract.platform')
        s.enqueue('T1', 'A', 'diagnostic'); result = s.serve(f.execute)
        ios = next(o for o in result['outcomes'] if o['profile'] == 'ios')
        command_folder = Path(ios['service_output']).parent
        before_native = b.load(command_folder / 'profile-admission.json')
        self.assertEqual(before_native['config']['sha256'], admitted['config']['sha256'])
        self.assertEqual(before_native['platform'], b.load(b.load(admitted['config']['path'])['plan'])['design_contract']['platform'])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DomainTests))
    put(base.ARTIFACTS / 'DOMAIN-RESULT.json', {'kind': 'HOST/SIM', 'native_execution': False, 'sdk_forwarding': False,
        'scope': 'Synthetic independent source-domain admission and pure profile guard tests; no business/native outcomes',
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful()})
    raise SystemExit(0 if result.wasSuccessful() else 1)
