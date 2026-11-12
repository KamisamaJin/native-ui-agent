"""Read-only, explicit historical shared-workflow view over a pinned Resolver.

Only original sibling checkpoint paths named by registered context proofs can
be redirected. No original-path access, native/source/contract overrides,
rewriting, implicit current fallback, mixed directories or version guessing.
"""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re


FORMAT = 'explicit-shared-workflow-history-v1'
EXPECTED_SCOPES = ['T'+str(i)+'/B/android' for i in range(1, 6)]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


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


def absolute(value):
    need(isinstance(value, str) and value.startswith('/') and '\x00' not in value and '\\' not in value,
         'Canonical original absolute path required')
    p = PurePosixPath(value)
    need(str(p) == value and all(part not in {'.', '..'} and part.casefold() != '.git' for part in value.split('/')),
         'Unsafe or noncanonical original path')
    return p


def hexsha(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Exact SHA256 required')
    return value


def workflow_root(root, task):
    need(task in {'T'+str(i) for i in range(1, 6)}, 'Unregistered task')
    return absolute(str(root)) / f'cache/business/{task}/B/hidden-workflow'


def registered_record(root, scope, record):
    need(scope in EXPECTED_SCOPES, 'Only registered B/android sibling-proof scopes are supported')
    task, arm, profile = scope.split('/')
    ev = absolute(str(root)) / 'cache/business/independent-evaluation'
    licensed = ev / f'continuations/{task}/{arm}/{profile}/native'
    resumed = ev / 'entry-resumptions/T1/B/android/native'
    need(absolute(record) == licensed or (scope == 'T1/B/android' and absolute(record) == resumed),
         'Unregistered native context-proof namespace')
    return absolute(record)


def requirements(reader, root, registration):
    """Validate proof/claim scope; return only its four historical file refs.

    Does not read native outcomes, measurements, sources, contracts or grades.
    Frozen native_chain separately checks the complete permission/native chain.
    """
    root = absolute(str(root)); scope = registration['scope']
    need(scope in EXPECTED_SCOPES, 'Unregistered history scope')
    task, arm, profile = scope.split('/')
    claim_ref = registration['claim']; proof_ref = registration['proof']
    wanted_claim = root / f'cache/business/independent-evaluation/native-continuation-claims/{task}/{arm}/{profile}.json'
    need(claim_ref['path'] == str(wanted_claim), 'Foreign registered continuation claim')
    claim = pinned(reader, claim_ref, parse=True)
    need(all(claim.get(k) == v for k, v in {'version':1,'task':task,'arm':arm,'profile':profile,'action':'native'}.items()),
         'Registered claim scope differs')
    record = registered_record(root, scope, claim['record'])
    need(proof_ref['path'] == str(record / 'fresh-platform-context.json'), 'Foreign native context-proof path')
    proof = pinned(reader, proof_ref, parse=True)
    need(proof.get('current_platform_fresh') is True and proof.get('workflow') in
         {'fresh_empty','not_configured','registered_same_arm_sibling_only'}, 'Unsupported recorded context admission')
    if proof['workflow'] != 'registered_same_arm_sibling_only':
        need(not proof.get('sibling_files') and not proof.get('owner'), 'Unexpected history refs on a fresh/absent workflow proof')
        return {}
    base = workflow_root(root, task); names = {'owner.json','ios.lock','ios.json','ios-backup.json'}
    need(set(proof['sibling_files']) == names, 'Exact registered sibling file set required')
    need(proof['owner'] == proof['sibling_files']['owner.json'], 'Recorded workflow owner alias differs')
    refs = {}
    for name, ref in proof['sibling_files'].items():
        need(set(ref) == {'path','sha256'} and ref['path'] == str(base/name),
             'Only exact registered shared-workflow sibling paths may be preserved')
        hexsha(ref['sha256']); refs[ref['path']] = ref
    return refs


def pinned(reader, ref, *, parse=False):
    need(isinstance(ref, dict) and set(ref) >= {'path','sha256'}, 'Explicit original reference required')
    original = str(absolute(ref['path'])); expected = hexsha(ref['sha256'])
    raw = reader.read_bytes(original)
    need(isinstance(raw, bytes) and sha(raw) == expected, 'Pinned history/proof bytes differ: '+original)
    if 'bytes' in ref:
        need(type(ref['bytes']) is int and len(raw) == ref['bytes'], 'Historical byte count differs')
    return strict_json(raw) if parse else raw


class HistoryReader:
    """Immutable historical view; compatible with frozen native_chain API.

    base_reader must be the separately pinned archive Resolver (or an explicitly
    labeled author synthetic reader). It resolves history copies by their own
    original absolute archive keys. There is no direct filesystem byte access.
    """
    def __init__(self, base_reader, ledger_ref, *, require_complete=True):
        self.base = base_reader
        self.ledger_ref = dict(ledger_ref)
        self.ledger = pinned(self.base, self.ledger_ref, parse=True)
        value = self.ledger
        need(value.get('format') == FORMAT and value.get('version') == 1, 'Unsupported history ledger')
        self.root = absolute(value['original_root'])
        self.blocked_roots = [workflow_root(self.root, 'T'+str(i)) for i in range(1, 6)]
        need(value.get('status') in {'complete','partial','failed'} and not value.get('failures'),
             'History ledger contains a failed or ambiguous checkpoint')
        selection = value['selection']
        need(selection.get('expected_scopes') == EXPECTED_SCOPES, 'History selection must retain the exact five registered scope slots')
        regs = selection['registered_proofs']; scopes = [r['scope'] for r in regs]
        pending = selection['pending_scopes']
        need(len(scopes) == len(set(scopes)) and set(scopes) <= set(EXPECTED_SCOPES)
             and [k for k in EXPECTED_SCOPES if k not in scopes] == pending, 'History proof selection/pending complement differs')
        if require_complete:
            need(value['status'] == 'complete' and not pending, 'Complete historical scope selection required')
        else:
            need(value['status'] in {'complete','partial'}, 'Failed historical view is forbidden')
        # API read_bytes(path) cannot distinguish two expected versions at one
        # original key. Preserve both in a ledger if necessary, but refuse this
        # view rather than guessing which temporal version the caller intended.
        versions = value['versions']; required_by_path = {}
        for row in versions:
            original = str(absolute(row['original_path'])); hexsha(row['required_sha256'])
            required_by_path.setdefault(original,set()).add(row['required_sha256'])
        need(all(len(v) == 1 for v in required_by_path.values()), 'Ambiguous multiple historical versions for one original path')
        expected = {}; proof_refs = {}
        for reg in regs:
            for original, ref in requirements(self.base, self.root, reg).items():
                need(original not in expected or expected[original] == ref['sha256'], 'Context proofs require conflicting historical versions')
                expected[original] = ref['sha256']
                proof_refs.setdefault((original,ref['sha256']),[]).append({'scope':reg['scope'],'proof':reg['proof'],'claim':reg['claim']})
        need(len(versions) == len(expected), 'Historical version inventory duplicates or omits required files')
        self.rows = {}
        ledger_dir = absolute(self.ledger_ref['path']).parent
        checkpoint_root = absolute(value['checkpoint_root'])
        need(checkpoint_root == ledger_dir, 'History checkpoint root differs from ledger namespace')
        copies = set()
        for row in versions:
            original = row['original_path']; wanted = expected.get(original)
            need(wanted == row['required_sha256'] and row.get('status') == 'preserved', 'Unregistered or missing historical override')
            need(type(row['bytes']) is int and row['bytes'] >= 0, 'Exact historical byte count required')
            copy = row['copy']; copied = absolute(copy['path'])
            copy_expected = checkpoint_root / 'versions' / sha(original.encode()) / wanted / absolute(original).name
            need(copied == copy_expected and copied != absolute(original) and str(copied) not in copies,
                 'Historical copy aliases an original or another copied file')
            copies.add(str(copied))
            need(copy['sha256'] == wanted and copy['bytes'] == row['bytes'] and row['proof_provenance'] == proof_refs[(original,wanted)],
                 'Historical copy/proof pins differ')
            observation = row['original_observation']
            need(observation.get('original_path') == original and observation.get('sha256') == wanted
                 and observation.get('stable_read') is True and observation['identity_before'] == observation['identity_after']
                 and observation['identity_before']['bytes'] == row['bytes']
                 and all(type(observation[k]) in {int,float} and math.isfinite(observation[k])
                         for k in ['read_started_at_unix','read_finished_at_unix'])
                 and observation['read_finished_at_unix'] >= observation['read_started_at_unix'], 'Historical read identity/provenance differs')
            identity = observation['identity_before']
            need(set(identity) == {'device','inode','bytes','mode','mtime_ns','ctime_ns'}
                 and all(type(x) is int for x in identity.values()) and identity['inode'] > 0 and identity['device'] >= 0,
                 'Original timestamp/inode provenance is malformed')
            pinned(self.base, copy)
            self.rows[original] = row
        self._check()

    def _check(self):
        need(self.base.hash(self.ledger_ref['path']) == self.ledger_ref['sha256'], 'Pinned historical ledger changed')

    def _historical_namespace(self, original):
        p = absolute(str(original))
        return any(p == root or p.is_relative_to(root) for root in self.blocked_roots)

    def read_bytes(self, original):
        original = str(absolute(str(original))); self._check()
        if original in self.rows:
            # Never inspect the current original workflow path, even if a copy
            # is missing or its pin fails. Errors propagate without fallback.
            raw = pinned(self.base, self.rows[original]['copy'])
        else:
            need(not self._historical_namespace(original), 'Workflow path is not selected by this pinned historical view')
            raw = self.base.read_bytes(original)
        self._check()
        return raw

    def read_json(self, original):
        return strict_json(self.read_bytes(original))

    def hash(self, original):
        return sha(self.read_bytes(original))

    def directory(self, original):
        original = absolute(str(original)); self._check()
        need(not any(original == root or original.is_relative_to(root) or root.is_relative_to(original) for root in self.blocked_roots),
             'Directory would mix historical and final workflow versions')
        value = self.base.directory(str(original)); self._check()
        return value
