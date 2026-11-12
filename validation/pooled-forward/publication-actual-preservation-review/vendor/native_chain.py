"""Pure recorded native provenance replay. No SDK, fallback, grading or writes.

The reader is the frozen publication Resolver protocol. Original absolute keys
are retained. A separately pinned snapshot selects a terminal prefix; missing
restore files are errors, never historical absence/freshness evidence.
"""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re


CODE = {
    'independent_native.py': '3c305880a818ab87c21c0c1043064b02af5991633efc7d3ab8d31405c4990a5d',
    'independent_native_v2.py': '7c8cf014299ea94db1646d22bd09be69040aaf183a10e50a7fd824126dbb02d2',
    'independent_native_v3.py': '7672ec99ca986a149d303eb8e37fb81da71edf1826c6eb1273da534945ddf722',
    'collect_independent.py': 'd80522b8bb620e7b0a58a5da4a9bdb566c15a78d6cd3a69b7619023c335b7047',
    'collect_independent_v2.py': '6d8cdda538e115d01fea2116d2bc9d4397867a4bfe80536e7226d0ec5b5dd8a2',
    'collect_independent_v3.py': '3f52be8628c483aee62690d89f93db0f59f497c0605fa60c233620befaf30641',
    'blind_study.py': '1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05',
    'source_domain.py': 'fd82356e7b76a8b3099351d6de4d19259eeb241dd99e06b1c4efad3668ba7c8c',
}
ANCHORS = {
    'manifest': 'cache/business/run-cohort2/manifest.json',
    'initial_cohort': 'cache/business/run-cohort2/INITIAL-COHORT.json',
    'cohort': 'cache/business/run-cohort2/COHORT-SEAL.json',
    'hidden_authorization': 'cache/business/run-cohort2/HIDDEN-AUTHORIZATION.json',
    'initial_preparation': 'cache/business/initial-reference/PREPARATION-SEAL.json',
    'order': 'operators/cohort2/coordination/POST-PUBLIC-ACQUISITION-ORDER.json',
    'authority': 'operators/cohort2/coordination/UNFORWARDED-CONTINUATION-AUTHORIZATION.json',
    'entry_permit': 'operators/cohort2/coordination/UNCLAIMED-ENTRY-v3-ADMISSION.json',
    'plan': 'operators/cohort2/coordination/REMAINING-NATIVE-SCOPES-v3.json',
}
SIDECARS = {
    'command': 'command.json', 'sdk_observation': 'sdk-observation.json',
    'exception_log': 'envelope/exception.log', 'envelope_result': 'envelope/result.json',
    'recovery_log': 'envelope/recovery.log', 'recovery_resources': 'envelope/error-recovery/resources.json',
    'recovery_journal': 'envelope/error-recovery/resource-journal.json',
    'recovery_events': 'envelope/error-recovery/resource-events.jsonl',
}
CLAIM_SCOPE = 'One admitted native attempt; failure/interruption never authorizes a replacement sample'
CONT_SCOPE = 'Single explicit continuation before first inner native UI; original failed claim/outcome/cost retained. Never a replacement sample.'
OWNERSHIP_ERROR = {'type': 'ValueError', 'message': 'Resource ownership differs from this project'}
ENTRY_ERROR = {'type': 'ValueError', 'message': 'Original fresh independent context is no longer empty before first native UI'}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                          allow_nan=False).encode())


def strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'Duplicate JSON key')
            out[key] = value
        return out
    def constant(_):
        raise ValueError('Nonfinite JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def path(value):
    need(isinstance(value, str) and value.startswith('/') and '\\' not in value and '\x00' not in value,
         'Canonical original absolute key required')
    p = PurePosixPath(value)
    need(str(p) == value and all(v not in {'.', '..'} and v.casefold() != '.git' for v in value.split('/')),
         'Unsafe original path')
    need(p.name != 'MAPPING.json' and '/anonymous-map/' not in value and '/blind-quality/grades/' not in value
         and not any(x in p.name for x in ['worker-prompt', 'self-claim', 'findings']),
         'Forbidden judgment, mapping or worker content reference')
    return p


def relative(value):
    need(isinstance(value, str) and value and '\\' not in value and '\x00' not in value,
         'Canonical relative member required')
    p = PurePosixPath(value)
    need(not p.is_absolute() and str(p) == value and all(v not in {'.', '..'} and v.casefold() != '.git' for v in value.split('/')),
         'Unsafe relative member')
    return p


def hexsha(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Exact SHA256 pin required')
    return value


def finite(value):
    return type(value) in {int, float} and math.isfinite(value)


class Access:
    """All file bytes flow through reader; returned directory Paths enumerate only."""
    def __init__(self, reader):
        self.reader = reader
        self.seen = {}
        self.trees = {}

    def raw(self, original):
        original = str(path(str(original)))
        raw = self.reader.read_bytes(original)
        need(isinstance(raw, bytes), 'Reader must return original bytes')
        actual = sha(raw)
        need(original not in self.seen or self.seen[original] == actual, 'Original changed during replay')
        self.seen[original] = actual
        return raw

    def load(self, original):
        return strict_json(self.raw(original))

    def ref(self, ref, *, parse=True):
        need(isinstance(ref, dict) and set(ref) >= {'path', 'sha256'}, 'Original file reference required')
        raw = self.raw(ref['path'])
        need(sha(raw) == hexsha(ref['sha256']), 'Original pin differs: ' + ref['path'])
        if 'bytes' in ref:
            need(type(ref['bytes']) is int and len(raw) == ref['bytes'], 'Original byte count differs')
        if 'canonical_sha256' in ref:
            need(digest(strict_json(raw)) == ref['canonical_sha256'], 'Canonical hash domain differs')
        return strict_json(raw) if parse else raw

    def pin(self, original):
        return {'path': str(path(str(original))), 'sha256': sha(self.raw(original))}

    def names(self, original):
        original = str(path(str(original)))
        physical = self.reader.directory(original)
        need(isinstance(physical, Path), 'directory() must return a verified physical Path')
        files, dirs = set(), set()
        for p in physical.rglob('*'):
            need(not p.is_symlink(), 'Symlink in verified namespace')
            name = str(relative(p.relative_to(physical).as_posix()))
            if p.is_file():
                files.add(name)
            elif p.is_dir():
                dirs.add(name)
            else:
                raise ValueError('Unsupported entry in verified namespace')
        # Original SDK output may retain empty ordinary directories. The frozen
        # explicit-file Resolver preserves file membership and itself rejects
        # unmapped restore entries. Empty originals are not absence evidence.
        need(original not in self.trees or self.trees[original] == files, 'Recorded namespace changed during replay')
        self.trees[original] = files
        return files

    def recheck(self):
        for original, expected in list(self.seen.items()):
            need(self.reader.hash(original) == expected, 'Original changed after replay: ' + original)
        for original in list(self.trees):
            self.names(original)


class Chain:
    def __init__(self, reader, original_root, snapshot_ref):
        self.a = Access(reader)
        self.root = path(str(original_root))
        self.run = self.root / 'cache/business/run-cohort2'
        self.ev = self.root / 'cache/business/independent-evaluation'
        self.coord = self.root / 'operators/cohort2/coordination'
        self.snapshot_ref = snapshot_ref
        self.s = self.a.ref(snapshot_ref)
        need(self.s.get('kind') == 'recorded-native-chain-snapshot-v1' and self.s.get('version') == 1
             and self.s.get('original_root') == str(self.root), 'Unsupported native-chain snapshot')
        need(set(self.s['anchors']) == set(ANCHORS), 'Complete explicit anchor pins required')
        self.docs = {}
        for key, name in ANCHORS.items():
            ref = self.s['anchors'][key]
            need(ref['path'] == str(self.root / name), 'Foreign anchor path: ' + key)
            self.docs[key] = self.a.ref(ref)
        for name, expected in CODE.items():
            original = (self.root / 'business-tools-v4' if name in {'blind_study.py', 'source_domain.py'} else self.coord) / name
            self.a.ref({'path': str(original), 'sha256': expected}, parse=False)
        self.capsules = {}
        self.scopes = {}
        self.original_times = {}
        self.failures = []
        self.limits = [
            'Recorded provenance only; no present-source, SDK, device or historical-empty-directory claim.',
            'Recorded permission/reviewer identity is authority evidence, not cryptographic proof of the reviewer or exhaustive absence of bypasses.',
            'No product grading, comparison, judgment replay or delivery acceptance is performed.',
            'Public controller replay, archive/index validation and immutable restoration remain separate prerequisites.',
        ]

    def capsule(self, ref, roots, *, stored=True):
        key = (ref['path'], ref['sha256'])
        if key in self.capsules:
            value = self.capsules[key]
            need([v['path'] for v in value['roots']] == roots, 'Cached capsule root order differs')
            return value
        value = self.a.ref(ref)
        need(set(value) == {'roots', 'files', 'content_sha256'} and value['files'], 'Exact nonempty capsule required')
        need([v['path'] for v in value['roots']] == roots and len(set(roots)) == len(roots), 'Capsule source-root order differs')
        for row in value['roots']:
            path(row['path'])
            need(set(row) == {'path', 'device', 'inode'} and type(row['device']) is int and type(row['inode']) is int,
                 'Recorded original root identities required')
        need(digest(value['files']) == value['content_sha256'], 'Controller capsule hash domain differs')
        for member, spec in value['files'].items():
            p = relative(member)
            need(len(p.parts) >= 2 and p.parts[0].isdigit() and str(int(p.parts[0])) == p.parts[0]
                 and int(p.parts[0]) < len(roots), 'Unstable capsule root index')
            need(set(spec) == {'sha256', 'bytes'} and type(spec['bytes']) is int and spec['bytes'] >= 0,
                 'Exact capsule file SHA/byte count required')
            hexsha(spec['sha256'])
        if stored:
            base = path(ref['path']).parent / 'files'
            need(self.a.names(base) == set(value['files']), 'Capsule stored member set differs')
            for member, spec in value['files'].items():
                self.a.ref({'path': str(base / member), **spec}, parse=False)
        self.capsules[key] = value
        return value

    def barrier(self):
        m, cohort, hidden = (self.docs[k] for k in ['manifest', 'cohort', 'hidden_authorization'])
        need(m.get('version') == 1 and len(m['tasks']) == 5 and [v['id'] for v in m['tasks']] == ['T'+str(i) for i in range(1, 6)], 'Five tasks required')
        self.tasks = {v['id']: v for v in m['tasks']}
        expected = {t+'/'+arm for t in self.tasks for arm in ['A', 'B']}
        need(all(set(t['arms']) == {'A', 'B'} for t in m['tasks']) and set(cohort['members']) == expected,
             'Ten-member source/cohort barrier differs')
        names = self.a.names(self.run / 'events')
        need(names == {f'{i:06d}.json' for i in range(len(names))}, 'Original event filenames/sequence differ')
        events, previous = [], None
        for i in range(len(names)):
            original = self.run / 'events' / f'{i:06d}.json'
            raw = self.a.raw(original); e = strict_json(raw)
            need(e['sequence'] == i and e['previous_sha256'] == previous, 'Original event SHA chain differs')
            previous = sha(raw); events.append(e)
        co = [e for e in events if e['kind'] == 'cohort_sealed']
        au = [e for e in events if e['kind'] == 'hidden_authorized']
        va = [e for e in events if e['kind'] == 'hidden_contexts_validated']
        need(len(co) == len(au) == len(va) == 1 and co[0] == cohort and au[0] == hidden['authorization'],
             'Original unique barrier/authorization events required')
        need(cohort['sequence'] < au[0]['sequence'] < va[0]['sequence'] and va[0]['authorization_sequence'] == au[0]['sequence']
             and au[0]['cohort_sha256'] == self.s['anchors']['cohort']['sha256'], 'Hidden authorization order/pin differs')
        enq = [e['request_id'] for e in events if e['kind'] == 'request_enqueued']
        terminal = [e['request_id'] for e in events if e['kind'] == 'request_finished']
        need(len(enq) == len(set(enq)) and len(terminal) == len(set(terminal)) and set(enq) == set(terminal),
             'Recorded public request registry is not terminal')
        self.locks = {}
        for task in self.tasks:
            for arm, spec in self.tasks[task]['arms'].items():
                locks = [e for e in events if e['kind'] == 'source_locked' and (e.get('task'), e.get('arm')) == (task, arm)]
                seals = [e for e in events if e['kind'] == 'self_sealed' and (e.get('task'), e.get('arm')) == (task, arm)]
                need(len(locks) == len(seals) == 1 and locks[0]['sequence'] < seals[0]['sequence'] < cohort['sequence'],
                     'Original source/self/cohort order differs')
                lock, sealed = locks[0], seals[0]; member = cohort['members'][task+'/'+arm]
                need(lock['source_sha256'] == sealed['source_sha256'] == member['source_sha256'], 'Cohort source lock differs')
                # Self-claim content is deliberately never read or parsed.
                self.a.ref({'path': member['path'], 'sha256': member['sha256']}, parse=False)
                ref = {'path': lock['source_manifest'], 'sha256': lock['source_manifest_sha256']}
                need(ref['path'] == str(self.run / f'arms/{task}/{arm}/final-source/source.json'), 'Final capsule namespace differs')
                cap = self.capsule(ref, spec['source_roots'])
                need(cap['content_sha256'] == lock['source_sha256'], 'Lock/capsule digest differs')
                self.locks[(task, arm)] = ref
        self.authorized_at = va[0]['at_unix']
        prep = self.docs['initial_preparation']; initial = self.docs['initial_cohort']
        need(self.a.load(self.ev / 'INITIAL-PREPARATION-AUTHORITY.json') == self.s['anchors']['initial_preparation'],
             'Original initial-preparation authority registry differs')
        need(set(prep) == {'version', 'kind', 'tasks'} and prep['version'] == 1
             and prep['kind'] == 'canonical-initial-reference-preparation' and set(prep['tasks']) == set(initial) == set(self.tasks),
             'Canonical initial preparation membership differs')
        for task, entry in prep['tasks'].items():
            need(set(entry) == {'ios', 'android'} and set(initial[task]) == {'A', 'B'}, 'Initial task/profile set differs')
            original_caps = [self.capsule(initial[task][arm], self.tasks[task]['arms'][arm]['source_roots']) for arm in ['A', 'B']]
            need(original_caps[0]['files'] == original_caps[1]['files'], 'Original initial pair differs')
            for profile, row in entry.items():
                need(set(row) == {'config', 'source_manifest', 'source_roots', 'resource_root'}, 'Initial preparation entry schema differs')
                base = self.root / f'cache/business/initial-reference/{task}'
                need(row['config']['path'] == str(base / f'profiles/{profile}.json')
                     and row['resource_root'] == str(base / f'resources/{profile}')
                     and path(row['source_manifest']['path']).is_relative_to(base), 'Initial reference namespace differs')
                cap = self.capsule(row['source_manifest'], row['source_roots'], stored=False)
                need(cap['files'] == original_caps[0]['files'], 'Canonical initial differs from original initial bytes')
                for root in row['source_roots']:
                    need(path(root).is_relative_to(base / 'workspace'), 'Canonical initial source namespace differs')

    def schedule(self):
        order = self.docs['order']['episodes']
        pairs = [(r['task'], r['scope']) for r in order]
        need(len(pairs) == 15 and len(set(pairs)) == 15 and set(pairs) == {(t, a) for t in self.tasks for a in ['I', 'A', 'B']}
             and pairs[:5] == [('T'+str(i), 'I') for i in range(1, 6)]
             and all(r['profiles'] == ['ios', 'android'] for r in order), 'Prospective acquisition schedule differs')
        self.order = [t+'/'+a+'/'+p for t, a in pairs for p in ['ios', 'android']]
        need(self.docs['order']['cohort_sha256'] == self.s['anchors']['cohort']['sha256'], 'Order/cohort binding differs')
        terminal = self.s['terminal_scopes']; pending = self.s['pending_scopes']
        need(type(terminal) is list and type(pending) is list and terminal + pending == self.order
             and len(set(terminal + pending)) == 30, 'Declared terminal prefix/pending complement differs')
        need(set(self.s['terminal_records']) == set(terminal), 'Terminal prefix record set differs')
        need(type(self.s['complete_record_namespace']) is bool and (not pending or not self.s['complete_record_namespace']),
             'Prefix cannot claim a complete acquisition namespace')

    def config(self, task, arm, profile):
        if arm == 'I':
            row = self.docs['initial_preparation']['tasks'][task][profile]
            ref, capsule = row['config'], row['source_manifest']
            roots, resource = row['source_roots'], row['resource_root']
        else:
            row = self.docs['hidden_authorization']['hidden_configs'][task][arm][profile]
            ref = {k: row[k] for k in ['path', 'sha256']}; capsule = self.locks[(task, arm)]
            spec = self.tasks[task]['arms'][arm]; roots = spec['source_roots']; resource = None
        config = self.a.ref(ref)
        need(config['source_roots'] == roots and config['platform'] == profile and config['resources'].get('max_simulators', 1) == 1,
             'Authorized source/platform/resource configuration differs')
        if arm == 'I':
            need(config['resources']['root'] == resource, 'Initial resource root differs')
        else:
            need(config['resources']['root'] in spec['resource_roots'] and config['review_store'] in row['context_roots']
                 and config['source_review_store'] in row['context_roots'], 'Hidden resource/context binding differs')
        plan = self.a.load(config['plan'])
        need(plan['design_contract']['platform'] == profile, 'Actual plan platform differs')
        return ref, capsule, config

    def closure(self, ref, config):
        value = self.a.ref(ref)
        need(value.get('final') is True and all(value.get(k) == [] for k in ['cleanup_errors', 'remaining_directories', 'remaining_devices']),
             'No positive owned resource closure')
        owner = value.get('owner', {})
        owner_key = sha(json.dumps(config['source_roots']).encode())
        need(value.get('root') == config['resources']['root'] and owner.get('format') == 'native-ui-owned-resources-v1'
             and owner.get('owner_key') == owner_key and re.fullmatch('[0-9a-f]{32}', owner.get('token', '')),
             'Resource owner/root scope differs')
        journal = self.a.load(path(ref['path']).parent / 'resource-journal.json')
        need(journal.get('token') == owner['token'] and journal.get('devices') == [] and journal.get('directories') == []
             and not journal.get('process'), 'Positive closure lacks an empty same-owner original journal')
        self.a.raw(path(ref['path']).parent / 'resource-events.jsonl')
        return value

    def unforwarded(self, key, row):
        task, arm, profile = key.split('/'); original = row['original']
        config_ref, cap_ref, config = self.config(task, arm, profile)
        claim = self.a.ref(original['original_claim']); old = self.a.ref(original['original_outcome'])
        self.original_times[key] = (old['started_at_unix'], old['finished_at_unix'])
        record = self.ev / f'{task}/{arm}/{profile}/native'
        need(original['original_claim']['path'] == str(self.ev / f'native-claims/{task}/{arm}/{profile}.json')
             and original['original_outcome']['path'] == str(record / 'outcome.json') and claim['record'] == str(record),
             'Original one-shot namespace differs')
        for value in [claim, old]:
            need(all(value.get(k) == v for k, v in {'task': task, 'arm': arm, 'profile': profile, 'action': 'native',
                 'config': config_ref, 'source_capsule': cap_ref}.items()), 'Original unforwarded source/config/scope differs')
        need(claim.get('scope') == CLAIM_SCOPE and original['original_config'] == config_ref
             and original['original_source_capsule'] == cap_ref, 'Original claim/config/capsule binding differs')
        need(original.get('inner_command_log_absent') is True and original.get('service_namespace_absent') is True,
             'Recorded original absence assertions required')
        need(old.get('source_unchanged') is True and old['source_before'] == old['source_after'] == self.a.ref(cap_ref)
             and not old.get('capture') and not old.get('cycle') and old.get('new_ui_acquisition') is not True,
             'Acquired or ambiguous original UI forbids continuation')
        need(old.get('native_claim') == original['original_claim'] and old.get('accepted') is False,
             'Original failed operation claim/acceptance differs')
        if arm == 'I':
            need(old.get('initial_preparation') == self.s['anchors']['initial_preparation']
                 and old.get('original_initial_capsule') == self.docs['initial_cohort'][task]['A'],
                 'Original initial failure preparation/capsule chain differs')
        self.entry(record, old, 2)
        need(old.get('error'), 'Original failed work must remain a failure')
        failure = self.a.load(record / 'failure.json')
        need(failure['error'] == old['error'] and failure.get('traceback'), 'Original failure sidecar missing/changed')
        sidecars = row['original_sidecars']; need(set(sidecars) == set(SIDECARS), 'Exact original sidecar set required')
        for name, rel in SIDECARS.items():
            need(sidecars[name]['path'] == str(record / rel), 'Foreign zero-forward sidecar')
            self.a.ref(sidecars[name], parse=False)
        need(sidecars['envelope_result'] == original['envelope_result'] and sidecars['recovery_resources'] == original['positive_recovery_resources'],
             'Original sidecar aliases differ')
        env = self.a.ref(original['envelope_result']); request = self.a.ref(original['envelope_request'])
        need(original['envelope_request']['path'] == str(record / 'envelope/request.json') and env.get('exit_code') is None
             and env.get('error') == OWNERSHIP_ERROR and env.get('source_unchanged') is True,
             'Only exact recorded pre-forward ownership failure may continue')
        source = {k: v['sha256'] for k, v in old['source_before']['files'].items()}
        need(all(env.get(k) == v for k, v in request.items()) and env['config_sha256'] == config_ref['sha256']
             and request['source_before'] == env['source_after'] == source,
             'Original zero-forward supervisor request/source/config binding differs')
        command = self.a.ref(sidecars['command'])
        wanted = [env['argv'][0], '-B', str(path(old['tool_root']) / 'scripts/ui_loop.py'), 'native', '--config', config_ref['path'], '--output', str(record / 'service'), '--final']
        need(env['argv'] == request['argv'] == command['argv'] == wanted and command['config'] == config_ref,
             'Original inner request/command differs')
        recovery = env.get('recovery', {})
        need(recovery.get('exit_code') == 0 and recovery.get('argv') == [env['argv'][0], '-B', str(path(old['tool_root']) / 'scripts/resource_manager.py'),
             '--config', config_ref['path'], '--output', str(record / 'envelope/error-recovery'), 'cleanup'], 'Original recovery command differs')
        sdk = self.a.ref(sidecars['sdk_observation'])
        need(not any(v.get('kind') == 'process_started' for v in sdk['observed_command_records']), 'Recorded original forwarding evidence forbids continuation')
        # Namespace completeness is checked, but its missing entries are only
        # corroboration of pinned historical assertions, never their substitute.
        names = self.a.names(record)
        need('envelope/command.log' not in names and not any(v.startswith('service/') for v in names),
             'Original execution artifact contradicts pinned absence assertions')
        self.closure(original['positive_recovery_resources'], config)
        self.failures.append({'scope': key, 'kind': 'original_pre_forward_transport_failure', 'outcome': original['original_outcome']})
        return old

    def authority(self):
        auth = self.docs['authority']; pin = self.s['anchors']['authority']
        need(auth.get('version') == 1 and auth.get('kind') == 'explicit-single-unforwarded-native-continuation-authority'
             and auth.get('approval_delivery', {}).get('operator_review_completed') is True, 'Explicit reviewed continuation authority required')
        need(auth['original_runner'] == {'path': str(self.coord / 'independent_native.py'), 'sha256': CODE['independent_native.py']}, 'Original runner authority differs')
        for key in ['cohort', 'hidden_authorization', 'initial_preparation']:
            need(auth[key] == self.s['anchors'][key], 'Continuation barrier/source authority binding differs')
        prior_closed = self.a.ref(auth['prior_monitor_positive_closed'])
        need(prior_closed.get('status') == 'closed' and prior_closed.get('positive_idle', {}).get('all_clear') is True,
             'Original supplemental monitor did not positively close')
        self.original_monitor_closed = prior_closed['finished_at_unix']
        index = self.a.ref(auth['zero_forwarding_index']); review = self.a.ref(auth['independent_review'])
        need(review.get('status') == 'verified' and review.get('errors') == [] and review['index'] == auth['zero_forwarding_index'], 'Recorded zero-forward review chain differs')
        wanted = set(self.order) - {'T1/I/ios', 'T1/I/android'}
        indexed = {'/'.join(v[k] for k in ['task', 'arm', 'profile']): v for v in index['failures']}
        reviewed = {'/'.join(v[k] for k in ['task', 'arm', 'profile']): v for v in review['checked']}
        need(len(index['failures']) == len(review['checked']) == 28 and set(indexed) == set(reviewed) == set(auth['scopes']) == wanted,
             'Exact 28 original unforwarded scopes required; acquired I1 excluded')
        need(self.a.load(self.ev / 'NATIVE-CONTINUATION-AUTHORITY.json') == pin, 'Registered continuation authority differs')
        for key, row in auth['scopes'].items():
            need(row['original'] == indexed[key] and reviewed[key]['original_outcome'] == row['original']['original_outcome']
                 and row['record'] == str(self.ev / ('continuations/' + key + '/native')), 'Continuation license/original review scope differs')
            need(row.get('unique_envelope_leaf') == 'envelope-' + sha(row['record'].encode()), 'Licensed unique supervisor namespace differs')
            self.unforwarded(key, row)
        permit = self.docs['entry_permit']; plan = self.docs['plan']
        need(permit.get('kind') == 'explicit-unclaimed-pre-forward-entry-admission' and permit.get('operator_review_completed') is True
             and permit['base_authority'] == pin and permit['remaining_plan'] == self.s['anchors']['plan'], 'Explicit v3 entry permit chain differs')
        for field in ['diagnosis', 'independent_review', 'reviewed_proposal']:
            self.a.ref(permit[field], parse=False)
        need(plan.get('kind') == 'remaining-unexecuted-native-scopes-v3' and plan['base_authority'] == pin,
             'Remaining plan authority differs')
        licensed_order = self.order[2:]
        need([(r['scope'], r['licensed_record']) for r in plan['remaining']] == [(k, auth['scopes'][k]['record']) for k in licensed_order[11:]]
             and len(plan['remaining']) == 17, 'Exact remaining seventeen order differs')
        need([r['scope'] for r in plan['prior_continuation_acquisitions']] == licensed_order[:11], 'Prior acquired prefix differs')
        for row in plan['prior_continuation_acquisitions']:
            for field in ['claim', 'outcome', 'positive_resources']:
                self.a.ref(row[field], parse=False)
        entry = permit['entry_resume']; failed = auth['scopes']['T1/B/android']['record']
        resumed = str(self.ev / 'entry-resumptions/T1/B/android/native')
        need(entry['scope'] == 'T1/B/android' and entry['licensed_record'] == failed and entry['resumed_record'] == resumed
             and plan['entry_resumption_record'] == resumed, 'Narrow preclaim-resumption scope differs')
        need(set(entry['failed_record_files']) == {'ENTRY.json', 'outcome.json', 'failure.json'}
             and self.a.names(failed) == {'ENTRY.json', 'outcome.json', 'failure.json'}, 'Preclaim failed-entry inventory differs')
        for name, ref in entry['failed_record_files'].items():
            need(ref['path'] == str(path(failed) / name), 'Foreign failed preclaim entry')
            self.a.ref(ref, parse=False)
        old = self.a.ref(entry['failed_record_files']['outcome.json'])
        original = auth['scopes']['T1/B/android']['original']
        need(old.get('error') == ENTRY_ERROR and old.get('source_unchanged') is True and old['source_before'] == old['source_after']
             and old['config'] == original['original_config'] and old['source_capsule'] == original['original_source_capsule']
             and not any(old.get(k) for k in ['native_claim', 'native_continuation_claim', 'envelope_record', 'service_output', 'capture', 'cycle']),
             'Acquired or ambiguous preclaim entry forbids resumption')
        need(self.a.ref(entry['failed_record_files']['failure.json'])['error'] == ENTRY_ERROR, 'Preclaim failure sidecar differs')
        self.entry(path(failed), old, 3)
        self.failures.append({'scope': 'T1/B/android', 'kind': 'later_preclaim_entry_failure', 'outcome': entry['failed_record_files']['outcome.json']})
        for i, row in enumerate(plan['remaining']):
            need(row['record'] == (resumed if i == 0 else row['licensed_record']), 'Additional entry without exact narrow permit')
        self.resume = resumed

    def entry(self, record, outcome, version):
        entry = self.a.load(record / 'ENTRY.json')
        need(outcome.get('version') == entry.get('version') == version and outcome.get('kind') == entry.get('kind') == 'independent-original-fact-operation',
             'Version-aware operator entry/outcome differs')
        for field in ['task', 'arm', 'profile', 'action', 'started_at_unix', 'started_at_monotonic']:
            need(entry[field] == outcome[field], 'Original operator entry identity/time differs')
        name = {2: 'independent_native.py', 3: 'independent_native_v2.py', 4: 'independent_native_v3.py'}[version]
        need(entry['runner'] == {'path': str(self.coord / name), 'sha256': CODE[name]}, 'Version-aware frozen runner differs')
        argv = entry['argv']
        for flag, value in [('--root', str(self.root)), ('--record', str(record)), ('--task', outcome['task']), ('--arm', outcome['arm']),
                            ('--profile', outcome['profile']), ('--action', 'native')]:
            need(argv.count(flag) == 1 and argv[argv.index(flag)+1] == value, 'Original entry argv binding differs')
        need(all(finite(outcome.get(k)) for k in ['started_at_unix', 'finished_at_unix', 'started_at_monotonic', 'finished_at_monotonic', 'wall_seconds'])
             and outcome['finished_at_unix'] >= outcome['started_at_unix'] >= self.authorized_at
             and outcome['finished_at_monotonic'] >= outcome['started_at_monotonic'] and outcome['wall_seconds'] >= 0,
             'Recorded operator wall/order is invalid')
        need(abs(outcome['wall_seconds'] - (outcome['finished_at_monotonic'] - outcome['started_at_monotonic'])) < 0.1,
             'Recorded process-local wall arithmetic differs')
        if version == 4:
            need(entry.get('started_at_clock_gettime_monotonic') == outcome.get('started_at_clock_gettime_monotonic')
                 and finite(outcome.get('finished_at_clock_gettime_monotonic'))
                 and outcome['finished_at_clock_gettime_monotonic'] >= outcome['started_at_clock_gettime_monotonic'], 'Recorded shared v3 clock differs')

    def admission(self, record, config_ref, config, task, arm, profile):
        admission = self.a.load(record / 'profile-admission.json')
        need({k: admission['config'][k] for k in ['path', 'sha256']} == config_ref and admission['platform'] == profile,
             'Original profile admission source/config scope differs')
        self.a.ref(admission['config'], parse=False)
        alias = 'A' if arm == 'I' else arm
        hook = self.tasks[task]['arms'][alias]['profile_admissions'][profile]
        need(admission['script']['path'] == hook['script'] and admission['approval']['path'] == hook['approval']
             and admission['approval']['canonical_sha256'] == hook['approval_sha256'], 'Profile admission authority differs')
        self.a.ref(admission['script'], parse=False); self.a.ref(admission['approval'], parse=False)
        public = self.a.load(self.run / f'arms/{task}/{alias}/public-inputs.json')
        dependencies = [hook['script'], hook['approval'], *hook.get('dependencies', [])]
        need(admission['dependency_files'] == {p: public[p] for p in dependencies},
             'Original profile-admission dependency registry differs')
        for original, expected in admission['dependency_files'].items():
            self.a.ref({'path': original, 'sha256': expected}, parse=False)
        required = {'design_lock', 'plan', 'policy', 'routes', 'environment', 'fixtures', 'bridge'}
        required |= {k for k in ['coverage_domain_ref', 'coverage_provider_ref'] if k in config}
        need(set(admission['inputs']) == required, 'Exact admitted input inventory differs')
        for key, ref in admission['inputs'].items():
            expected = config[key]['path'] if key.endswith('_ref') else config[key]
            need(ref['path'] == expected, 'Admitted input belongs to another config')
            self.a.ref(ref, parse=False)
        # This is a recorded admission, not re-execution of mutable admission code.
        need(admission['verdict'].get('status') == 'admitted_profile' and admission['verdict'].get('platform') == profile,
             'Original recorded platform admission absent')
        return admission

    def capture(self, record, outcome, cap, config, profile):
        cycle = self.a.ref(outcome['cycle']); receipt = self.a.ref(outcome['capture'])
        capture = path(outcome['capture']['path']).parent
        need(outcome['cycle']['path'] == str(record / 'service/cycle.json') and outcome['capture']['path'] == str(record / 'service/capture/result.json')
             and cycle.get('native_executed') is True and not cycle.get('capture_reused')
             and cycle.get('capture_result') == outcome['capture']['path'] and cycle.get('capture_sha256') == outcome['capture']['sha256'],
             'Original cycle/capture acquisition binding differs')
        req = self.a.load(capture / 'request.json')
        need(all(receipt.get(k) == v for k, v in req.items()), 'Original capture request/receipt differs')
        task, arm = outcome['task'], outcome['arm']; alias = 'A' if arm == 'I' else arm
        tool = self.docs['manifest']['tools'][self.tasks[task]['arms'][alias]['tool']]
        need(isinstance(req.get('tool_files'), dict) and req['tool_files'], 'Recorded native runtime inventory required')
        for name, expected in req['tool_files'].items():
            relative(name)
            need(tool['files'].get(name) == expected, 'Native runtime differs from frozen tool hash domain')
            self.a.ref({'path': str(capture / 'tool-runtime' / name), 'sha256': expected}, parse=False)
        roots = config['source_roots']; wanted = {k: v['sha256'] for k, v in cap['files'].items()}
        model = receipt.get('source_model')
        need(not config.get('platform_source_roots') or model is not None, 'Configured platform source model is missing')
        need(model is None or receipt.get('capture_context_sha256'), 'Platform-selective capture lacks recorded context')
        if model is not None:
            need(model == self.a.load(capture / 'source-model.json') and digest(model) == receipt['source_model_sha256'], 'Native source-model binding differs')
            need(model.get('version') == 1 and model['platform'] == profile and model['source_roots'] == roots
                 and set(model['groups']) == {'ios', 'android', 'shared'}, 'Source model platform/root set differs')
            groups = model['groups']; seen = set()
            for group in groups.values():
                need(len(group) == len(set(group)) and set(group) <= set(roots) and not (set(group) & seen), 'Overlapping/unregistered source groups')
                seen.update(group)
            need(seen == set(roots), 'Unclassified roots must be shared')
            declared = config.get('platform_source_roots', {})
            for group in ['ios', 'android']:
                need(groups[group] == declared.get(group, []), 'Source group differs from authorized config')
            indices = [i for i, root in enumerate(roots) if root in groups[profile] or root in groups['shared']]
            need(model['indices'] == indices, 'Unstable platform source-root indices')
            wanted = {k: v for k, v in wanted.items() if int(k.split('/', 1)[0]) in indices}
        before = self.a.load(capture / 'source-before.json'); after = self.a.load(capture / 'source-after.json')
        need(before == after == wanted and receipt['source_sha256'] == req['source_sha256'] == digest(wanted)
             and receipt['source_roots'] == roots and receipt.get('source_unchanged') is True, 'Native source-before/after or hash domain differs')
        for name, expected in receipt['input_hashes'].items():
            self.a.ref({'path': str(capture / relative(name)), 'sha256': expected}, parse=False)
        for name, expected in receipt.get('packet_files', {}).items():
            self.a.ref({'path': str(capture / relative(name)), 'sha256': expected}, parse=False)
        plan = self.a.load(capture / 'parent-plan.json'); execution = self.a.load(capture / 'execution.json')
        execution_body = {k: v for k, v in execution.items() if k != 'execution_sha256'}
        need(execution.get('execution_sha256') == digest(execution_body) == receipt['execution_sha256']
             and digest(plan) == receipt['parent_plan_sha256']
             and plan == self.a.load(config['plan']), 'Capture plan/execution config binding differs')
        need(execution['platform'] == profile and execution['scope'] == 'full'
             and execution['parent_plan_sha256'] == receipt['parent_plan_sha256']
             and execution['design_lock_sha256'] == digest(self.a.load(config['design_lock']))
             and execution['fixtures_sha256'] == digest(self.a.load(config['fixtures']))
             and execution['bridge_sha256'] == sha(self.a.raw(config['bridge'])), 'Original execution contract/source input binding differs')
        if 'capture_context_sha256' in receipt:
            context = self.a.load(capture / 'capture-context.json')
            need(digest(context) == receipt['capture_context_sha256'] and context['platform'] == profile
                 and context['source_model'] == model and context['native_options'] == config['native_options'], 'Recorded capture context differs')
            for key, expected in context['files'].items():
                self.a.ref({'path': config[key], 'sha256': expected}, parse=False)
        self.a.raw(capture / 'native.log')
        images = receipt.get('image_hashes', {})
        for name, expected in images.items():
            self.a.ref({'path': str(capture / 'native' / relative(name)), 'sha256': expected}, parse=False)
        native_names = self.a.names(capture / 'native')
        need({n for n in native_names if n.lower().endswith('.png')} == set(images), 'Original image inventory differs')
        if receipt.get('observation_sha256'):
            self.a.ref({'path': str(capture / 'native/observation.json'), 'sha256': receipt['observation_sha256']}, parse=False)
        if receipt.get('automatic_sha256'):
            self.a.ref({'path': str(capture / 'automatic.json'), 'sha256': receipt['automatic_sha256']}, parse=False)
        # No observation assertions, automatic outcomes or image judgments parsed.
        return {'image_files': len(images), 'observation_pinned': bool(receipt.get('observation_sha256')),
                'facts_available': bool(receipt.get('observation_sha256')) and bool(images)}

    def operation(self, key, row):
        task, arm, profile = key.split('/'); config_ref, cap_ref, config = self.config(task, arm, profile)
        ordinary = self.ev / f'native-claims/{task}/{arm}/{profile}.json'
        continued = self.ev / f'native-continuation-claims/{task}/{arm}/{profile}.json'
        original_claim = self.a.load(ordinary)
        is_cont = key not in {'T1/I/ios', 'T1/I/android'}
        claim_path = continued if is_cont else ordinary
        need(row['claim']['path'] == str(claim_path), 'Effective one-shot claim path differs')
        claim = self.a.ref(row['claim']); record = path(claim['record'])
        expected = self.resume if key == 'T1/B/android' else str(self.ev / (('continuations/' if is_cont else '') + key + '/native'))
        need(str(record) == expected and row['outcome']['path'] == str(record / 'outcome.json'), 'Effective registered endpoint differs')
        for value in [original_claim, claim]:
            need(all(value.get(k) == v for k, v in {'version': 1, 'task': task, 'arm': arm, 'profile': profile, 'action': 'native',
                 'config': config_ref, 'source_capsule': cap_ref}.items()), 'One-shot claim assignment/source/config differs')
        if is_cont:
            old = self.docs['authority']['scopes'][key]['original']
            need(claim['scope'] == CONT_SCOPE and claim['original_claim'] == old['original_claim'] and claim['original_outcome'] == old['original_outcome']
                 and claim['authority'] == self.s['anchors']['authority'], 'Continuation claim license chain differs')
            if key == 'T1/B/android':
                entry = self.docs['entry_permit']['entry_resume']
                need(claim.get('entry_resume_permit') == self.s['anchors']['entry_permit'] and claim.get('failed_preclaim_entry') == entry['failed_record_files']['outcome.json']
                     and claim.get('licensed_original_record') == entry['licensed_record'], 'Resumed claim permit/failure chain differs')
            else:
                need(not claim.get('entry_resume_permit'), 'Unexpected entry-resume permit')
        else:
            need(claim['scope'] == CLAIM_SCOPE, 'Original one-shot claim scope differs')
        outcome = self.a.ref(row['outcome']); cap = self.a.ref(cap_ref)
        if not is_cont:
            self.original_times[key] = (outcome['started_at_unix'], outcome['finished_at_unix'])
        need(all(outcome.get(k) == v for k, v in {'task': task, 'arm': arm, 'profile': profile, 'action': 'native', 'config': config_ref, 'source_capsule': cap_ref}.items()),
             'Effective original operation assignment/source/config differs')
        self.entry(record, outcome, outcome['version'])
        need(finite(claim.get('reserved_at_unix')) and outcome['started_at_unix'] <= claim['reserved_at_unix'] <= outcome['finished_at_unix'],
             'One-shot claim reservation is outside its original operation')
        need(outcome['native_claim'] == self.a.pin(ordinary), 'Original native claim reference differs')
        if is_cont:
            need(outcome.get('native_continuation_claim') == row['claim'] and outcome.get('original_zero_forwarding_outcome') == claim['original_outcome']
                 and outcome.get('continuation_authority') == self.s['anchors']['authority'], 'Effective continuation outcome chain differs')
        if arm == 'I':
            need(outcome.get('initial_preparation') == self.s['anchors']['initial_preparation']
                 and outcome.get('original_initial_capsule') == self.docs['initial_cohort'][task]['A'],
                 'Effective initial preparation/capsule chain differs')
        need(outcome.get('source_unchanged') is True and outcome['source_before'] == outcome['source_after'] == cap,
             'Recorded full source-before/after identity differs')
        alias = 'A' if arm == 'I' else arm
        need(outcome['tool_root'] == self.docs['manifest']['tools'][self.tasks[task]['arms'][alias]['tool']]['skill_root'], 'Frozen tool selection differs')
        acquired = outcome.get('new_ui_acquisition') is True
        record_names = self.a.names(record)
        if 'profile-admission.json' in record_names:
            self.admission(record, config_ref, config, task, arm, profile)
        else:
            need(not acquired and outcome.get('error'), 'Acquisition lacks original profile admission')
        need(not outcome.get('capture_reused'), 'Replacement/reused UI acquisition is forbidden')
        images = 0; facts_available = False; observation_pinned = False
        if acquired:
            need(outcome.get('capture') and outcome.get('cycle'), 'Claimed acquisition lacks original capture/cycle')
            packet = self.capture(record, outcome, cap, config, profile)
            images = packet['image_files']; facts_available = packet['facts_available']; observation_pinned = packet['observation_pinned']
            if not facts_available:
                self.failures.append({'scope': key, 'kind': 'native_first_execution_without_complete_fact_binding', 'outcome': row['outcome']})
        else:
            need(not outcome.get('capture') and not outcome.get('cycle'), 'Ambiguous capture cannot be silently classed unexecuted')
            need(outcome.get('error') or outcome.get('exit_code') not in {None, 0}, 'Non-acquisition lacks an original failure')
            need(not ({'service/cycle.json', 'service/capture/result.json'} & record_names), 'Recorded native packet is concealed by a failure outcome')
            self.failures.append({'scope': key, 'kind': 'effective_native_transport_failure_or_ambiguous_execution', 'outcome': row['outcome']})
            # Preserve partial SDK/entry evidence without construing missing
            # phase files as historical proof that no inner native command ran.
            for name in record_names:
                self.a.raw(record / name)
        if outcome.get('error'):
            failure = self.a.load(record / 'failure.json')
            need(failure['error'] == outcome['error'] and failure.get('traceback'), 'Effective failure must retain original traceback')
        expected_accepted = outcome.get('exit_code') == 0 and not outcome.get('error') and not outcome.get('preservation_errors') and outcome.get('service_status') == 'accepted' and outcome['source_unchanged']
        need(outcome.get('accepted') is expected_accepted, 'Native process exit/recorded accepted flag inconsistent')
        inventory = self.a.ref(outcome['inventory']) if outcome.get('inventory') else {}
        if inventory:
            service = path(outcome['service_output']); need(service == record / 'service', 'Original service namespace differs')
            names = self.a.names(service)
            need(set(inventory) == {str(service / name) for name in names}, 'Original service inventory membership differs')
            for original, spec in inventory.items():
                need(set(spec) == {'sha256', 'bytes'}, 'Nonregular original preserved service member')
                self.a.ref({'path': original, **spec}, parse=False)
        env_leaf = 'envelope-' + sha(str(record).encode()) if is_cont else 'envelope'
        envelope_complete = {env_leaf+'/request.json', env_leaf+'/result.json', env_leaf+'/command.log', 'command.json', 'sdk-observation.json'} <= record_names
        if acquired or envelope_complete:
            self.envelope(record, outcome, config_ref, config, cap, is_cont)
        resources = self.closure(row['closure'], config)
        allowed = {str(record / 'service/resources.json'), str(record / ('envelope-' + sha(str(record).encode())) / 'error-recovery/resources.json'),
                   str(record.parent / 'explicit-cleanup/service/resources.json'), str(record.parent / 'explicit-cleanup-v3/service/resources.json')}
        need(row['closure']['path'] in allowed, 'Foreign effective resource closure')
        if outcome.get('resources'):
            need(row['closure'] == outcome['resources'], 'Effective own resource receipt differs')
        if outcome['version'] == 4 and (acquired or outcome.get('fresh_platform_context')):
            self.context(outcome, config, cap_ref, key)
        self.scopes[key] = {'outcome': row['outcome'], 'acquired': acquired and facts_available,
                            'recorded_native_first_execution': acquired, 'observation_pinned': observation_pinned, 'positive_resource_closed': True,
                            'image_files': images, 'recorded_service_status': outcome.get('service_status'),
                            'recorded_native_accepted': outcome['accepted'], 'started_at_unix': outcome['started_at_unix'],
                            'finished_at_unix': outcome['finished_at_unix'], 'error_retained': bool(outcome.get('error')),
                            'complete_supervision_record': envelope_complete,
                            'failure_absence_scope': None if acquired else 'Partial records are retained; no zero-inner-UI or replacement license inferred.'}

    def envelope(self, record, outcome, config_ref, config, cap, is_cont):
        env = record / ('envelope-' + sha(str(record).encode()) if is_cont else 'envelope')
        if is_cont:
            need(outcome.get('envelope_record') == str(env), 'Unique supervisor namespace differs')
        request = self.a.load(env / 'request.json'); result = self.a.load(env / 'result.json')
        command = self.a.load(record / 'command.json')
        need(all(result.get(k) == v for k, v in request.items()), 'Supervisor request/receipt differs')
        need(request['config_sha256'] == config_ref['sha256'] and command['config'] == config_ref and command['argv'] == request['argv'],
             'Supervisor config/inner command binding differs')
        wanted = [request['argv'][0], '-B', str(path(outcome['tool_root']) / 'scripts/ui_loop.py'), 'native', '--config', config_ref['path'], '--output', str(record / 'service'), '--final']
        need(request['argv'] == wanted, 'Effective inner native command differs')
        source = {k: v['sha256'] for k, v in cap['files'].items()}
        need(request['source_before'] == result['source_after'] == source and result.get('source_unchanged') is True, 'Supervisor source identity differs')
        self.a.raw(env / 'command.log'); self.a.raw(record / 'supervisor.log')
        sdk = self.a.load(record / 'sdk-observation.json')
        need(isinstance(sdk['journal_prefixes'], list) and isinstance(sdk['observed_command_records'], list), 'Recorded SDK observation schema differs')
        for row in sdk['journal_prefixes']:
            need(row['path'] == str(path(config['resources']['root']) / 'events.jsonl') and type(row['start_byte']) is int
                 and type(row['end_byte']) is int and 0 <= row['start_byte'] <= row['end_byte'], 'SDK observation belongs to another resource scope')
            hexsha(row['prefix_sha256'])

    def context(self, outcome, config, cap_ref, key):
        proof = self.a.ref(outcome['fresh_platform_context'])
        need(proof.get('current_platform_fresh') is True and proof.get('workflow') in {'not_configured', 'fresh_empty', 'registered_same_arm_sibling_only'},
             'Recorded v3 context admission absent')
        if proof['workflow'] != 'registered_same_arm_sibling_only':
            return
        task, arm, profile = key.split('/'); sibling = 'android' if profile == 'ios' else 'ios'
        need(arm == 'B', 'Cross-arm/platform workflow sharing forbidden')
        native = self.a.ref(proof['sibling_native'])
        need(native['task'] == task and native['arm'] == arm and native['profile'] == sibling and native['source_capsule'] == cap_ref
             and native.get('new_ui_acquisition') is True and not native.get('capture_reused'), 'Sibling native registration/source differs')
        sibling_claim = self.a.ref(native['native_continuation_claim'])
        need(proof['sibling_native']['path'] == str(path(sibling_claim['record']) / 'outcome.json'), 'Sibling endpoint differs')
        workflow = path(config['workflow']['root'])
        need(set(proof['sibling_files']) == {'owner.json', sibling+'.lock', sibling+'.json', sibling+'-backup.json'}, 'Shared workflow member set differs')
        for name, ref in proof['sibling_files'].items():
            need(ref['path'] == str(workflow / name), 'Foreign shared workflow reference')
            self.a.ref(ref, parse=False)
        need(proof['owner'] == proof['sibling_files']['owner.json'], 'Shared workflow owner alias differs')
        owner = self.a.ref(proof['owner']); expected_owner = digest(config['source_roots'])
        need(owner.get('format') == 'native-ui-workflow-v1' and owner.get('owner') == expected_owner, 'Shared workflow owner differs')
        service = path(native['service_output']); inventory = self.a.ref(native['inventory'])
        for name in ['workflow-state.json', 'workflow-context.json']:
            original = str(service / name); self.a.ref({'path': original, **inventory[original]}, parse=False)
        state = self.a.load(service / 'workflow-state.json'); context = self.a.load(service / 'workflow-context.json')
        need(state.get('owner') == expected_owner and state.get('platform') == sibling and state.get('cycles') == [{'cycle': native['cycle'], 'context_sha256': digest(context)}]
             and state.get('capture') == {'cycle': native['cycle'], 'context_sha256': digest(context), 'capture': native['capture'], 'context': self.a.pin(service / 'workflow-context.json')},
             'Original sibling first-cycle checkpoint binding differs')
        expected = dict(state); expected['generation'] += 2
        need(self.a.ref(proof['sibling_files'][sibling+'.json']) == self.a.ref(proof['sibling_files'][sibling+'-backup.json']) == expected
             and self.a.ref(proof['sibling_files'][sibling+'.lock'], parse=False) == b'', 'Frozen sibling checkpoint/empty lock differs')

    def episodes(self):
        records = self.s['episodes']; seen, covered = set(), set()
        for ref in records:
            end = self.a.ref(ref); need(ref['path'] not in seen, 'Duplicate episode terminal')
            seen.add(ref['path']); start = self.a.ref(end['start'])
            need(path(end['start']['path']).parent == path(ref['path']).parent and path(ref['path']).name == 'END.json'
                 and end['status'] in {'closed', 'failed'} and end.get('quality_evaluated') is False, 'Episode terminal/start scope differs')
            need(finite(start['started_at_unix']) and finite(end['finished_at_unix']) and end['finished_at_unix'] >= start['started_at_unix'], 'Episode wall/order differs')
            closures = end.get('positive_resource_closure', end.get('positive_resource_closures', {}))
            for profile, out_ref in end['outcomes'].items():
                out = self.a.ref(out_ref)
                task, arm = start['task'], start['arm']
                need(out['task'] == task and out['arm'] == arm and out['profile'] == profile and out['action'] == 'native'
                     and start['started_at_unix'] <= out['started_at_unix'] <= out['finished_at_unix'] <= end['finished_at_unix'] + 1,
                     'Episode outcome registration/time differs')
                if out_ref in [v['outcome'] for v in self.s['terminal_records'].values()]:
                    key = task+'/'+arm+'/'+profile; wanted = self.s['terminal_records'][key]
                    need(closures.get(profile) == wanted['closure'], 'Episode positive closure binding differs')
                    covered.add(key)
                if profile in closures:
                    self.closure(closures[profile], self.config(task, arm, profile)[2])
        originals = {str(self.ev / f'episodes/{task}/{arm}/END.json') for task in self.tasks for arm in ['I', 'A', 'B']}
        need(originals <= seen, 'Original failed/closed episodes must all be retained')
        need(set(self.s['terminal_scopes']) <= covered, 'Effective terminal prefix lacks episode registration')
        controls = {}
        for ref in self.s['collection_controls']:
            value = self.a.ref(ref)
            original = path(ref['path']); need(original.is_relative_to(self.ev) and original.parent.name in {'collection-operations', 'continuation-collection', 'continuation-collection-v3'}, 'Foreign collection control')
            need(str(original) not in controls, 'Duplicate collection control')
            controls[str(original)] = (ref, value)
            if original.name == 'ENTRY.json':
                runner = value.get('collector', value.get('scheduler'))
                name = {'collection-operations': 'collect_independent.py', 'continuation-collection': 'collect_independent_v2.py', 'continuation-collection-v3': 'collect_independent_v3.py'}[original.parent.name]
                need(runner == {'path': str(self.coord / name), 'sha256': CODE[name]}, 'Frozen collection entry differs')
            for row in value.get('episodes', value.get('completed', [])):
                need(row['end']['path'] in seen, 'Collection omits registered episode terminal')
            if original.name == 'FAILED.json':
                need(value.get('error') and value.get('traceback'), 'Failed collection traceback must remain')
            if 'quality_evaluated' in value:
                need(value['quality_evaluated'] is False, 'Collection cannot claim quality credit')
            if 'mapping_revealed' in value:
                need(value['mapping_revealed'] is False, 'Collection cannot claim mapping reveal')
        control_names = {r['path'] for r in self.s['collection_controls']}
        mandatory = [self.ev / 'collection-operations' / n for n in ['ENTRY.json', 'START.json', 'END.json']]
        mandatory += [self.ev / 'continuation-collection' / n for n in ['ENTRY.json', 'START.json', 'FAILED.json']]
        mandatory += [self.ev / 'continuation-collection-v3' / n for n in ['ENTRY.json', 'START.json']]
        need(set(map(str, mandatory)) <= control_names, 'Original collection and later failed collection controls must remain separate')
        v1_end = controls[str(self.ev / 'collection-operations/END.json')][0]
        v2_failed = controls[str(self.ev / 'continuation-collection/FAILED.json')][0]
        v2_start = controls[str(self.ev / 'continuation-collection/START.json')][1]
        v3_start = controls[str(self.ev / 'continuation-collection-v3/START.json')][1]
        need(v2_start['authority'] == v3_start['authority'] == self.s['anchors']['authority']
             and v2_start['old_collection_end'] == v1_end and v2_start['original_order'] == self.s['anchors']['order']
             and v3_start['prior_failed_collection'] == v2_failed and v3_start['permit'] == self.s['anchors']['entry_permit']
             and v3_start['plan'] == self.s['anchors']['plan'], 'Collection continuation/failure/permit registration differs')
        self.a.ref(v2_start['new_monitor_ready'], parse=False)
        closed_ref = v3_start['initial_monitor_closed']
        need(closed_ref['path'] == str(path(self.docs['authority']['initial_monitor_record']) / 'CLOSED.json'),
             'Supplemental continuation monitor namespace differs')
        closed = self.a.ref(closed_ref)
        need(closed.get('status') == 'closed' and closed.get('positive_idle', {}).get('all_clear') is True,
             'Supplemental continuation monitor did not positively close')
        self.continuation_monitor_closed = closed['finished_at_unix']
        if self.s['complete_record_namespace']:
            final = [controls[str(self.ev / 'continuation-collection-v3' / name)] for name in ['END.json', 'FAILED.json']
                     if str(self.ev / 'continuation-collection-v3' / name) in controls]
            need(len(final) == 1, 'Whole-study mode requires one final v3 collector terminal')
            if path(final[0][0]['path']).name == 'END.json':
                need(final[0][1].get('status') == 'closed' and final[0][1].get('first_UI_v3') == 17,
                     'Closed v3 collection must register seventeen first executions')

    def finish(self):
        self.barrier(); self.schedule(); self.authority()
        for key in self.s['terminal_scopes']:
            self.operation(key, self.s['terminal_records'][key])
        self.episodes()
        original_previous = None
        for key in self.order:
            if key not in self.original_times:
                continue
            started, finished = self.original_times[key]
            need(original_previous is None or original_previous <= started + 1, 'Original native operations overlap/order differs')
            if key.split('/')[1] != 'I':
                need(self.original_monitor_closed <= started + 1, 'Original hidden attempt preceded positive initial monitor closure')
            original_previous = finished
        previous = None
        for key in self.s['terminal_scopes']:
            scope = self.scopes[key]
            if previous:
                need(previous['finished_at_unix'] <= scope['started_at_unix'] + 1, 'Serialized effective native operations overlap/order differs')
            if key.split('/')[1] != 'I':
                need(self.continuation_monitor_closed <= scope['started_at_unix'] + 1,
                     'Effective hidden native preceded positive supplemental initial closure')
            previous = scope
        if self.s['complete_record_namespace']:
            names = self.a.names(self.ev)
            allowed = {str(self.ev / (key + '/native')) for key in self.order}
            allowed |= {r['record'] for r in self.docs['authority']['scopes'].values()} | {self.resume}
            actual = {str(self.ev / PurePosixPath(n).parent) for n in names if n.endswith('/native/ENTRY.json') or n.endswith('/native/outcome.json')}
            need(actual == allowed, 'Unregistered/replacement or missing native record in complete namespace')
            claims = {f'native-claims/{k}.json' for k in self.order}
            continuations = {f'native-continuation-claims/{k}.json' for k in self.order[2:]}
            need({n for n in names if n.startswith('native-claims/')} == claims
                 and {n for n in names if n.startswith('native-continuation-claims/')} == continuations,
                 'Whole-study one-shot claim namespace differs')
        else:
            self.limits.append('Only the explicitly pinned terminal prefix is certified; excluded scopes remain pending in this snapshot even if newer live records exist.')
        self.a.recheck()
        acquired = sum(r['acquired'] for r in self.scopes.values())
        return {'status': 'verified', 'kind': 'recorded-native-chain-integrity', 'snapshot': self.snapshot_ref,
                'terminal_scopes': len(self.scopes), 'expected_scopes': 30, 'acquired_scopes': acquired,
                'recorded_native_first_executions': sum(r['recorded_native_first_execution'] for r in self.scopes.values()),
                'pending_scopes': self.s['pending_scopes'], 'acquisition_complete': acquired == 30 and not self.s['pending_scopes'],
                'delivery_verified': False, 'preserved_failures': self.failures, 'scopes': self.scopes,
                'ordering_clock_scope': 'Recorded Unix cross-process order; v3 shared CLOCK_MONOTONIC endpoints checked where present. Earlier process-local monotonic origins are never joined.',
                'original_files_checked': len(self.a.seen), 'limitations': self.limits}


def verify_chain(reader, original_root, snapshot_ref):
    """Verify a separately byte-pinned snapshot using exact original keys.

    Returns failed for corrupt/missing required evidence. An intact partial
    prefix returns verified with pending scopes and acquisition_complete=False.
    Honest native failures are retained, never upgraded to product acceptance.
    """
    try:
        return Chain(reader, original_root, snapshot_ref).finish()
    except (ValueError, KeyError, TypeError, IndexError, OSError) as exc:
        return {'status': 'failed', 'kind': 'recorded-native-chain-integrity', 'snapshot': snapshot_ref,
                'acquisition_complete': False, 'delivery_verified': False,
                'error': {'type': type(exc).__name__, 'message': str(exc)}}
