"""Small synthetic batch inputs; no native execution or real study artifacts."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import stat


PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')


def sha(raw): return hashlib.sha256(raw).hexdigest()


class Reader:
    def __init__(self, root, encoder): self.root = root; self.encoder = encoder; self.reads = []
    def read_bytes(self, raw):
        path = Path(raw); self.reads.append(str(raw))
        if not path.is_absolute() or not path.is_relative_to(self.root) or '..' in path.parts:
            raise ValueError('Synthetic reader path escapes review root')
        for part in (path, *path.parents):
            if part.is_symlink(): raise ValueError('Synthetic reader rejects symlinks')
            if part == self.root: break
        if not stat.S_ISREG(path.stat().st_mode): raise ValueError('Synthetic reader requires regular files')
        return path.read_bytes()
    def read_json(self, path): return self.encoder.strict_json(self.read_bytes(path))
    def hash(self, path): return sha(self.read_bytes(path))
    def directory(self, raw):
        path = Path(raw)
        if not path.is_absolute() or not path.is_relative_to(self.root) or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('Synthetic reader requires a physical directory')
        if not path.is_dir(): raise FileNotFoundError(str(path))
        return path


class Store:
    def __init__(self, root, module): self.root = root; self.module = module; self.pins = {}
    def put(self, path, value=None, raw=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        body = self.module.encoded(value) if raw is None else raw
        path.write_bytes(body); result = {'path': str(path), 'sha256': sha(body)}; self.pins[str(path)] = result['sha256']; return result


def cause(root, module):
    store = Store(root, module); rows = []
    for case in range(1, 6):
        for version in ('I', 'X', 'Y'):
            group = 'Case0%d-%s' % (case, version); seals = {}
            for judge in ('J1', 'J2'):
                folder = root / group / judge
                grade = store.put(folder / 'grade.json', {'anonymous_group': group, 'judge_id': judge,
                    'scope': 'Synthetic review record only; no product finding'})
                seals[judge] = store.put(folder / 'SEAL.json', {'version': 1, 'kind': 'independent-blind-cause-grade-seal',
                    'anonymous_group': group, 'judge_id': judge, 'files': {'grade.json': grade['sha256']}})
            inp = store.put(root / group / 'input/SEAL.json', {'kind': 'anonymous-fixed-version-input-seal', 'anonymous_group': group})
            end = store.put(root / group / 'END.json', {'anonymous_group': group, 'grade_seals': seals})
            rows.append({'group': group, 'actors': {j: '/root/synthetic_' + group + '_' + j for j in ('J1', 'J2')},
                         'seals': seals, 'inputs': [inp], 'episode_end': end, 'fork_turns': 'none', 'model_override': None})
    return store.put(root / 'INDEX.json', {'version': 1, 'kind': 'global-independent-cause-grade-barrier',
        'groups': rows, 'review_record_barrier_closed': True, 'product_quality_verified': False})


class Study(Store):
    @classmethod
    def existing(cls, root, module, review, rich=False):
        value = cls.__new__(cls); Store.__init__(value, root, module); value.rich = rich
        value.run = root / 'cache/business/run-cohort2'; value.evidence = root / 'cache/business/independent-evaluation'
        value.reader = Reader(review, module); value.capsules = {}; value.configs = {}; value.private_claims = {}; value.report_paths = []
        def ref(path): return {'path': str(path), 'sha256': value.reader.hash(str(path))}
        for task in ['T%d' % i for i in range(1, 6)]:
            for arm in ('A', 'B'):
                for stage in ('initial', 'final-source'):
                    path = value.run / 'arms' / task / arm / stage / 'source.json'
                    value.capsules[(task, arm, stage)] = (value.reader.read_json(str(path)), ref(path))
                for profile in ('ios', 'android'): value.configs[(task, arm, profile)] = ref(root / 'profiles' / task / arm / (profile + '.json'))
            for scope in ('I', 'A', 'B'):
                for profile in ('ios', 'android'):
                    value.private_claims[(task, scope, profile)] = ref(value.evidence / 'native-claims' / task / scope / (profile + '.json'))
        value.snapshot = ref(root / 'NATIVE-SNAPSHOT.json'); value.native_result = ref(root / 'NATIVE-RESULT.json')
        value.mapping_seal = ref(root / 'operators/cohort2/coordination/anonymous-map/SEAL.json')
        value.terminal = value.reader.read_json(value.snapshot['path'])['terminal_records']
        value.events = [ref(path) for path in sorted((value.run / 'events').glob('*.json'))]
        return value

    def __init__(self, root, module, review, rich=True):
        super().__init__(root, module); self.root.mkdir(parents=True); self.rich = rich; self.events = []; self.capsules = {}; self.configs = {}
        self.run = root / 'cache/business/run-cohort2'; self.evidence = root / 'cache/business/independent-evaluation'
        self.reader = Reader(review, module); self.report_paths = []; self.outcomes = {}; self.original_refs = {}; self.private_claims = {}
        for name in ('ALARM-INSTRUCTIONS-v1.md', 'ALARM-GRADE-TEMPLATE-v1.json'):
            self.put(root / 'business-quality-tools' / name, raw=(review / 'snapshots/source' / name).read_bytes())
        self.put(root / 'publication-resolver/resolver.py', raw=(review / 'snapshots/source/resolver.py').read_bytes())
        self.sources = {}
        for task in ['T%d' % i for i in range(1, 6)]:
            for arm in ('A', 'B'):
                workspace = root / 'source-spaces' / task / arm; workspace.mkdir(parents=True)
                for stage, version in [('initial', 0), ('final-source', 2 if rich and task == 'T1' and arm == 'A' else 0)]:
                    body = ('Synthetic source version %d.\n' % version).encode()
                    files = {'0/unit.txt': {'sha256': sha(body), 'bytes': len(body)}}
                    cap = {'files': files, 'content_sha256': sha(module.json_text(files, sort_keys=True).encode()),
                           'roots': [{'path': str(workspace), 'device': 0, 'inode': 0}]}
                    folder = self.run / 'arms' / task / arm / stage
                    ref = self.put(folder / 'source.json', cap); self.put(folder / 'files/0/unit.txt', raw=body)
                    self.capsules[(task, arm, stage)] = (cap, ref)
                for profile in ('ios', 'android'):
                    self.configs[(task, arm, profile)] = self.put(root / 'profiles' / task / arm / (profile + '.json'),
                        {'source_roots': [str(workspace)], 'synthetic_only': True})
        self.capture_refs = {}
        for version in (0, 2):
            for profile in ('ios', 'android'):
                native = root / 'capture-records' / ('v%d' % version) / profile / 'native'
                image = 'attachments/frame.png' if profile == 'ios' else 'frame.png'
                image_ref = self.put(native / image, raw=PNG)
                observation = {'schema_version': 2, 'platform': profile, 'status': 'U',
                    'snapshots': [{'index': 0, 'name': 'synthetic', 'screenshot': image,
                                  'nodes': [{'identifier': 'synthetic.badge', 'text': '  Synthetic  ', 'frame': {'height': 44}}]}],
                    'issues': ['Synthetic measurement limitation'], 'epoch': 7, 'state_id': 'synthetic-state'}
                if rich:
                    observation['operations'] = {'counts': {'capture': 1, 'selector_query': 2},
                        'seconds': {'capture': module.strict_json('0.1234567890123456789012345'), 'selector_query': 0},
                        'scope': 'Nested inclusive operation walls, not additive elapsed time'}
                obs = self.put(native / 'observation.json', observation)
                self.capture_refs[(version, profile)] = self.put(native.parent / 'result.json', {
                    'observation_sha256': obs['sha256'], 'image_hashes': {image: image_ref['sha256']},
                    'source_sha256': sha(('selected-platform-domain-%s-%d' % (profile, version)).encode()),
                    'source_model_sha256': sha(('model-' + profile).encode())})
        # Public terminal registry follows the frozen writer's exact event order.
        for task in ['T%d' % i for i in range(1, 6)]:
            for arm in ('A', 'B'):
                for action in ('diagnostic', 'final'):
                    cap, cap_ref = self.capsules[(task, arm, 'initial' if action == 'diagnostic' else 'final-source')]
                    version = 2 if rich and task == 'T1' and arm == 'A' and action == 'final' else 0
                    request_id = task + arm + action
                    event = {'task': task, 'arm': arm, 'request_id': request_id, 'action': action,
                             'profiles': ['ios', 'android'], 'source': cap,
                             'active_configs': {p: self.configs[(task, arm, p)] for p in ('ios', 'android')}}
                    self.event('request_enqueued', **event)
                    outcomes = []
                    for profile in event['profiles']:
                        record = self.run / 'requests' / request_id / profile
                        failed_d0 = rich and action == 'diagnostic' and (task, arm) != ('T2', 'A')
                        outcome_ref = self.operation(record, task, arm, profile, action, cap_ref,
                            self.configs[(task, arm, profile)], version, public=True,
                            failed=failed_d0,
                            coverage=rich and task == 'T1' and arm == 'A' and action == 'final' and profile == 'ios')
                        outcomes.append(module.strict_json(Path(outcome_ref['path']).read_bytes()))
                    result = self.put(self.run / 'requests' / request_id / 'result.json', {
                        'task': task, 'arm': arm, 'request_id': request_id, 'outcomes': outcomes})
                    self.event('request_finished', task=task, arm=arm, request_id=request_id,
                               result_path=result['path'], result_sha256=result['sha256'])
                if rich and (task, arm) == ('T1', 'A'):
                    cap, cap_ref = self.capsules[(task, arm, 'final-source')]
                    capture_path = Path(self.capture_refs[(2, 'ios')]['path']).parent
                    submission = self.put(self.run / 'requests/T1Areview/original-submission.json', {
                        'rows': [{'status': 'U', 'expected': '  Synthetic  ', 'actual': '  Synthetic  ',
                                  'image_ref': str(capture_path / 'native/attachments/frame.png'),
                                  'source_ref': str(root / 'source-spaces/T1/A/unit.txt')}],
                        'scope': 'Synthetic config ' + self.configs[('T1', 'A', 'ios')]['path']})
                    event_ref = dict(submission, original_path=str(root / 'worker-submissions/T1A.json'))
                    self.event('request_enqueued', task=task, arm=arm, request_id='T1Areview', action='review-native',
                        profiles=['ios'], source=cap, active_configs={'ios': self.configs[('T1', 'A', 'ios')]}, submission=event_ref)
                    outcome = self.operation(self.run / 'requests/T1Areview/ios', task, arm, 'ios', 'review-native',
                        cap_ref, self.configs[('T1', 'A', 'ios')], 2, public=True)
                    result = self.put(self.run / 'requests/T1Areview/result.json', {'task': task, 'arm': arm,
                        'request_id': 'T1Areview', 'outcomes': [module.strict_json(Path(outcome['path']).read_bytes())]})
                    self.event('request_finished', task=task, arm=arm, request_id='T1Areview', result_path=result['path'], result_sha256=result['sha256'])
                final_cap = self.capsules[(task, arm, 'final-source')][0]
                claim = self.put(self.run / 'arms' / task / arm / 'self-claim.json',
                    {'statement': 'Synthetic worker completion claim', 'accepted_claim': True})
                self.event('self_sealed', task=task, arm=arm, claim_path=claim['path'], claim_sha256=claim['sha256'],
                           source_sha256=final_cap['content_sha256'])
        terminal = {}; entry_failure = None
        for task in ['T%d' % i for i in range(1, 6)]:
            for scope in ('I', 'A', 'B'):
                arm = 'A' if scope == 'I' else scope
                cap, cap_ref = self.capsules[(task, arm, 'initial' if scope == 'I' else 'final-source')]
                version = 2 if rich and task == 'T1' and scope == 'A' else 0
                for profile in ('ios', 'android'):
                    config = self.configs[(task, arm, profile)]
                    special = (task, scope, profile) in {('T1', 'A', 'ios'), ('T1', 'B', 'android')}
                    original_record = self.evidence / 'original' / task / scope / profile / 'native'
                    original = self.operation(original_record, task, scope, profile, 'native', cap_ref, config, version,
                                              failed=special)
                    self.original_refs[(task, scope, profile)] = original
                    claim = self.put(self.evidence / 'native-claims' / task / scope / (profile + '.json'),
                        {'version': 1, 'task': task, 'arm': scope, 'profile': profile, 'record': str(original_record),
                         'config': config, 'source_capsule': cap_ref})
                    self.private_claims[(task, scope, profile)] = claim
                    effective = original
                    if special:
                        record = self.evidence / 'effective' / task / scope / profile / 'native'
                        effective = self.operation(record, task, scope, profile, 'native', cap_ref, config, version,
                                                   original=original)
                    terminal[task + '/' + scope + '/' + profile] = {'outcome': effective}
                    if (task, scope, profile) == ('T1', 'B', 'android'):
                        record = self.evidence / 'entry-failure' / task / scope / profile / 'native'
                        entry_failure = self.operation(record, task, scope, profile, 'native', cap_ref, config, version, failed=True)
        manifest = self.put(root / 'manifest.json', {'version': 1, 'synthetic_only': True})
        permit = self.put(root / 'operators/cohort2/coordination/UNCLAIMED-ENTRY-v3-ADMISSION.json',
            {'entry_resume': {'scope': 'T1/B/android', 'failed_record_files': {'outcome.json': entry_failure}}})
        mapping = self.put(root / 'operators/cohort2/coordination/anonymous-map/MAPPING.json',
            {'mapping': {'Case0%d' % i: {'task': 'T%d' % i, 'I': 'I', 'X': 'A', 'Y': 'B'} for i in range(1, 6)}})
        self.mapping_seal = self.put(root / 'operators/cohort2/coordination/anonymous-map/SEAL.json',
            {'files': {'MAPPING.json': mapping['sha256']}})
        self.snapshot = self.put(root / 'NATIVE-SNAPSHOT.json', {'original_root': str(root), 'terminal_records': terminal,
            'anchors': {'manifest': manifest, 'entry': permit}})
        # This is an explicitly synthetic proof input, not a claim of SDK/native verification.
        self.native_result = self.put(root / 'NATIVE-RESULT.json', {'snapshot': self.snapshot,
            'result': {'status': 'verified', 'acquired_scopes': 30}, 'files_read': dict(self.pins),
            'synthetic_only': True, 'SDK_executed': False})
        self.terminal = terminal
        self.put(root / 'FIXTURE-SCOPE.json', {'synthetic_only': True, 'native_proof_is_fixture_assertion': True,
            'mapping_pin_is_fixture_substitution': self.mapping_seal, 'actual_mapping_read': False,
            'source_versions': {str(k): v[0]['content_sha256'] for k, v in self.capsules.items()}})

    def event(self, kind, **values):
        sequence = len(self.events)
        previous = self.events[-1]['sha256'] if self.events else None
        event = {'kind': kind, 'sequence': sequence, 'previous_sha256': previous, **values}
        result = self.put(self.run / 'events' / ('%06d.json' % sequence), event)
        self.events.append(result); return event

    def operation(self, record, task, arm, profile, action, cap_ref, config_ref, version, public=False,
                  failed=False, original=None, coverage=False):
        outcome = {'task': task, 'arm': arm, 'profile': profile, 'action': action, 'config': config_ref,
                   'source_capsule': cap_ref, 'exit_code': 1 if failed else 0, 'accepted': False,
                   'source_unchanged': True}
        if self.rich and not public:
            cap = self.module.strict_json(Path(cap_ref['path']).read_bytes())
            outcome.update(version=4, kind='independent-original-fact-operation',
                operator_revision='strict-own-platform-shared-workflow-preclaim-entry-v3',
                scope='Synthetic preserved original operation scope; never a product verdict',
                source_before=cap['files'], source_after=cap['files'], tool_root='/Users/rex/synthetic-engine',
                preservation_errors=[])
            if original: outcome['original_zero_forwarding_outcome'] = original
        if failed:
            outcome['error'] = {'type': 'ValueError', 'message': 'Synthetic original pre-forward failure'}
        elif self.rich:
            service = record / 'service'
            report = self.put(service / 'automatic.json', raw=b'{"rows":[{"id":"synthetic-F","status":"F","expected":9007199254740993.0,"actual":1e-999},{"id":"synthetic-P","status":"P","actual":true},{"id":"synthetic-U","status":"U","actual":null}],"issues":[{"message":"Synthetic issue remains","status":"U"}]}\n')
            self.report_paths.append(report)
            self.put(service / 'cycle.json', {'trace': ['route_findings', 'locator_diagnostics', 'retest_plan.dispatch'],
                'status': 'synthetic_pending', 'positive_claim': False})
            if coverage: self.put(service / 'coverage.json', {'must_route_gaps': [{'status': 'U', 'id': 'synthetic-gap'}]})
            if coverage:
                self.put(service / 'capture/request.json', {'argv': ['synthetic-native-tool'], 'wall_seconds': 12345})
                self.put(service / 'capture/expected-environment.json', {'synthetic_control_cost_marker': 12345})
                self.put(service / 'capture/coverage-domain-prepared.json', {'synthetic_input_approval': True})
                self.put(service / 'capture/native/native-summary.json', {'synthetic_runner_metadata': True, 'wall_seconds': 12345})
                self.put(service / 'capture/native/attachments/manifest.json', {'synthetic_attachment_export': True})
                self.put(service / 'capture/environment-check.json', {'status': 'U', 'rows': [{'expected': 'synthetic-platform', 'actual': 'synthetic-platform'}]})
                self.put(service / 'capture/execution-coverage.json', {'status': 'U', 'coverage_gaps': ['synthetic-gap']})
            inventory = {str(p): sha(p.read_bytes()) for p in service.rglob('*') if p.is_file()}
            inv = self.put(record / 'original-inventory.json', inventory)
            outcome.update(service_output=str(service), inventory=inv, capture=self.capture_refs[(version, profile)],
                acquisition_evidence={'capture_receipt': self.capture_refs[(version, profile)],
                    'execution': None, 'native_log': None, 'observation': None,
                    'scope': 'Synthetic binding: config ' + config_ref['path'] + '; inventory ' + inv['path'] + '; status remains unknown'})
        ref = self.put(record / 'outcome.json', outcome); self.outcomes[str(record / 'outcome.json')] = ref; return ref
