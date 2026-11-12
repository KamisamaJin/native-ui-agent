"""Pure source-domain revision transport, shared by both frozen study arms.

No oracle, source edit, native call, automatic approval, or workflow mutation.
Authority is procedural: an immutable independent-reviewer registry and a trusted
operator's separately pinned delivery provenance, not cryptographic identity.
"""
import copy
import hashlib
import json
from pathlib import Path
import re


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(v): return hashlib.sha256(canonical(v)).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def reference(p): return {'path': str(Path(p).resolve()), 'sha256': sha(p)}


def policy(approval):
    # Exact documented frozen coverage_domain.policy semantics. Revisions are
    # observations; all host/shape/fixture/design policy remains in the digest.
    value = copy.deepcopy(approval)
    for k in ['approved_at_utc', 'approved_by']: value.pop(k, None)
    for platform in value['platforms'].values(): platform.pop('approved_component_revisions', None)
    return value


def platform(config):
    actual = load(config['plan'])['design_contract']['platform']
    if actual not in {'ios', 'android'} or ('platform' in config and config['platform'] != actual):
        raise ValueError('Actual plan platform must be unambiguous; no caller platform override')
    return actual


def original(config):
    ref = config.get('coverage_domain_ref')
    if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
        raise ValueError('Exact existing coverage_domain_ref required')
    approval = load(ref['path'])
    if digest(approval) != ref['sha256']:
        raise ValueError('Pinned source-domain approval changed')
    pl = platform(config)
    definition = approval['platforms'][pl]
    project = Path(config['native_options']['package' if pl == 'ios' else 'project']).resolve()
    component = (project / definition['component_install_path']).resolve()
    if not component.is_file() or not component.is_relative_to(project) or not any(component.is_relative_to(Path(r).resolve()) for r in config['source_roots']):
        raise ValueError('Actual component must be installed in assigned production source roots')
    subjects = config['evidence_subjects']; binding = approval['actual_subject_binding']
    if [str(Path(p).resolve()) for p in subjects[binding['component_subject']]] != [str(component)]:
        raise ValueError('Coverage component is not the actual configured source subject')
    bridge = Path(config['bridge']).resolve()
    if [str(Path(p).resolve()) for p in subjects[binding['bridge_subject']]] != [str(bridge)] or sha(bridge) != definition['exact_bridge']['sha256']:
        raise ValueError('Exact independently approved bridge required')
    return {'platform': pl, 'approval': approval, 'approval_ref': reference(ref['path']),
            'approval_sha256': digest(approval), 'policy_sha256': digest(policy(approval)),
            'component': {'path': str(component), 'sha256': sha(component), 'bytes': component.stat().st_size}}


def validate_append(previous, proposed, pl, component):
    if digest(policy(previous)) != digest(policy(proposed)):
        raise ValueError('Source-domain policy/host/oracle changes are forbidden')
    if set(previous['platforms']) != set(proposed['platforms']):
        raise ValueError('Source-domain platform set changed')
    added = []
    for key, old in previous['platforms'].items():
        before = old['approved_component_revisions']
        after = proposed['platforms'][key]['approved_component_revisions']
        if not isinstance(after, dict) or any(k not in after or after[k] != value for k, value in before.items()):
            raise ValueError('Old approved revisions cannot be deleted or rewritten')
        seen = set()
        for label, value in after.items():
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}', label):
                raise ValueError('Explicit source revision label required')
            if not re.fullmatch(r'[0-9a-f]{64}', value.get('sha256', '')) or type(value.get('bytes')) is not int or value['bytes'] < 0:
                raise ValueError('Exact finite source SHA256 and byte count required; no wildcards')
            pair = value['sha256'], value['bytes']
            if pair in seen:
                raise ValueError('Duplicate source revision aliases are forbidden')
            seen.add(pair)
        for label in set(after) - set(before):
            added.append((key, label, after[label]))
    expected = {'sha256': component['sha256'], 'bytes': component['bytes']}
    if len(added) != 1 or added[0][0] != pl or added[0][2] != expected:
        raise ValueError('Append exactly one independently reviewed ACTUAL component revision')
    return added[0][1]


def registry(ref):
    if set(ref) != {'path', 'sha256'} or sha(ref['path']) != ref['sha256']:
        raise ValueError('Independent reviewer registry pin changed')
    value = load(ref['path'])
    if value.get('version') != 1 or value.get('kind') != 'independent-source-domain-review-registry' or not value.get('reviewers') or not value.get('operators'):
        raise ValueError('Predeclared independent reviewers and trusted operators required')
    identities = {}
    for reviewer, spec in value['reviewers'].items():
        p = Path(spec['root'])
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', reviewer) or spec.get('scope') != 'source_shape_only' or not p.is_absolute() or not p.is_dir() or any(q.is_symlink() for q in [p, *p.parents]):
            raise ValueError('Independent reviewer needs an existing separate real registry directory and shape-only scope')
        identities[reviewer] = {'path': str(p), 'device': p.stat().st_dev, 'inode': p.stat().st_ino}
    return value, identities


def response(authority, identities, seal_path, seal_sha, provenance_path, provenance_sha, request, request_sha):
    for raw in [Path(seal_path), Path(provenance_path)]:
        if not raw.is_absolute() or any(p.is_symlink() for p in [raw, *raw.parents]):
            raise ValueError('Independent seal/provenance must use exact real original paths')
    seal_path = Path(seal_path).resolve(); provenance_path = Path(provenance_path).resolve()
    if sha(seal_path) != seal_sha or sha(provenance_path) != provenance_sha:
        raise ValueError('Pinned independent review seal/provenance changed or forged')
    seal = load(seal_path); provenance = load(provenance_path)
    reviewer = seal.get('reviewer_id')
    if reviewer not in authority['reviewers'] or seal.get('version') != 1 or seal.get('kind') != 'source-domain-review-seal':
        raise ValueError('Unregistered independent reviewer or malformed seal')
    root = Path(identities[reviewer]['path'])
    if not seal_path.is_relative_to(root) or seal_path.parent == root or any(p.is_symlink() for p in [seal_path, *seal_path.parents]):
        raise ValueError('Independent review seal must come from its predeclared separate reviewer registry')
    required = {'review.json', 'approval.json', 'component.source'}
    if set(seal.get('files', {})) != required:
        raise ValueError('Exact independently sealed review/approval/component inventory required')
    for relative in required:
        p = seal_path.parent / relative
        if p.is_symlink() or not p.is_file() or sha(p) != seal['files'][relative]:
            raise ValueError('Independent sealed review member changed: ' + relative)
    record = load(seal_path.parent / 'review.json')
    checks = {'version': 1, 'kind': 'independent-source-domain-review', 'reviewer_id': reviewer,
              'scope': 'source_shape_only', 'decision': 'approved', 'request_id': request['request_id'],
              'request_sha256': request_sha, 'study_id': request['study_id'], 'task': request['task'], 'arm': request['arm'],
              'profile': request['profile'], 'platform': request['platform'], 'source_sha256': request['source']['content_sha256'],
              'component': request['component'], 'parent_approval_sha256': request['parent_approval_sha256'],
              'policy_sha256': request['policy_sha256'], 'config_sha256': request['active_config']['sha256']}
    if any(record.get(k) != v for k, v in checks.items()) or not isinstance(record.get('reason'), str) or not record['reason'].strip():
        raise ValueError('Independent review does not bind this exact request/source/component/config/policy')
    actual_bytes = (seal_path.parent / 'component.source').read_bytes()
    if hashlib.sha256(actual_bytes).hexdigest() != request['component']['sha256'] or len(actual_bytes) != request['component']['bytes']:
        raise ValueError('Independent review component capsule differs from actual reviewed bytes')
    proposed = load(seal_path.parent / 'approval.json')
    if record.get('proposed_approval_sha256') != digest(proposed):
        raise ValueError('Independent proposed approval pin differs')
    pchecks = {'version': 1, 'kind': 'independent-source-domain-review-provenance', 'request_id': request['request_id'],
               'review_seal_sha256': seal_sha, 'reviewer_id': reviewer, 'independent_of_repair': True}
    if any(provenance.get(k) != v for k, v in pchecks.items()) or provenance.get('independent_of_repair') is not True or provenance.get('operator_id') not in authority['operators'] or not isinstance(provenance.get('delivery_reference'), str) or not provenance['delivery_reference'].strip():
        raise ValueError('Trusted operator must separately attest independent review delivery provenance')
    return {'reviewer_id': reviewer, 'record': record, 'proposed': proposed, 'seal': seal,
            'provenance': provenance, 'original_files': {str(seal_path): seal_sha, str(provenance_path): provenance_sha,
                                                      **{str(seal_path.parent / p): h for p, h in seal['files'].items()}}}
