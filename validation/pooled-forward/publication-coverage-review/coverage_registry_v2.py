"""Pure prospective applicability projection; no product/report/grade access.

Required native IDs are original assertion_id values, N/A IDs are explicitly
labeled mechanical state/rule identities, source IDs are family/state/rule.
The externally trusted original seal authenticates complete cells/task order;
this adapter cannot independently infer an omitted state or result truth.
"""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

NATIVE_KINDS = {'control', 'event', 'geometry', 'manual', 'text_layout'}
DISPOSITIONS = {'required', 'N/A', 'required-source-review'}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        need(key not in out, 'Duplicate original JSON key')
        out[key] = value
    return out


def parse(raw):
    return json.loads(raw, object_pairs_hook=_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite original JSON')))


def identifier(value):
    return isinstance(value, str) and bool(value) and '/' not in value and '\\' not in value and not any(ord(c) < 32 for c in value)


def evidence_refs(evidence):
    need(type(evidence) is list and evidence, 'Explicit frozen applicability refs required')
    for ref in evidence:
        need(type(ref) is dict and set(ref) == {'path', 'sha256'}
             and isinstance(ref['path'], str) and Path(ref['path']).is_absolute()
             and isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']),
             'Exact absolute original path/SHA256 evidence required')
    need(len({(r['path'], r['sha256']) for r in evidence}) == len(evidence), 'Duplicate applicability evidence ref')


def projection(cells, tasks, evidence):
    need(type(tasks) is list and len(tasks) == 5 and all(identifier(t) for t in tasks)
         and len(set(tasks)) == 5, 'Five distinct prospectively ordered task IDs required')
    evidence_refs(evidence)
    need(type(cells) is list and cells, 'Original nonempty denominator cells required')
    scopes = defaultdict(lambda: {'applicable_ids': [], 'not_applicable_ids': []})
    seen, profiles, identities = set(), set(), []
    for cell in cells:
        need(type(cell) is dict and {'task', 'platform', 'family', 'state', 'rule_id', 'kind', 'disposition'} <= set(cell),
             'Explicit original denominator identity fields required')
        task, platform, family, state, rule, kind, disposition = (cell[k] for k in
            ['task', 'platform', 'family', 'state', 'rule_id', 'kind', 'disposition'])
        need(task in tasks and platform in {'ios', 'android'} and family in {'public', 'private'}
             and identifier(state) and identifier(rule), 'Original task/platform/family/state/rule identity required')
        need(kind in NATIVE_KINDS | {'source'}, 'Unknown original denominator kind')
        need(disposition in DISPOSITIONS, 'Unknown original applicability disposition')
        source = kind == 'source'
        need((disposition == 'required-source-review') == source,
             'Source responsibility and native/image applicability cannot be interchanged')
        if source:
            need('assertion_id' not in cell, 'Source cell must not silently discard an assertion_id')
            name, basis = family+'/'+state+'/'+rule, 'explicit-source-family/state/rule-composite'
            key = (task, platform, family+'/'+state, 'source')
        else:
            name = state+'/'+rule
            if disposition == 'required':
                need('assertion_id' in cell and cell['assertion_id'] == name,
                     'Required native/image cell needs its exact original assertion_id')
                basis = 'original-required-assertion_id'
            else:
                need('assertion_id' not in cell or cell['assertion_id'] == name, 'N/A cell assertion_id conflicts with mechanical state/rule identity')
                basis = 'mechanical-N/A-state/rule-identity' if 'assertion_id' not in cell else 'original-N/A-assertion_id'
            key = (task, platform, state, family+'_native_image')
        identity = (key, name)
        need(identity not in seen, 'Duplicate frozen obligation')
        seen.add(identity)
        scopes[key]['not_applicable_ids' if disposition == 'N/A' else 'applicable_ids'].append(name)
        profiles.add((task, platform, family, 'source' if source else 'native_image'))
        identities.append({'task': task, 'platform': platform, 'family': family, 'state': state,
                           'rule_id': rule, 'kind': kind, 'disposition': disposition,
                           'projected_id': name, 'identity_basis': basis})
    expected_profiles = {(t, p, f, k) for t in tasks for p in ['ios', 'android']
                         for f in ['public', 'private'] for k in ['source', 'native_image']}
    need(profiles == expected_profiles, 'Every task/platform/public-private family must retain native/image and source cells')
    result = {}
    for number, task in enumerate(tasks, 1):
        rows = []
        for key, ids in sorted(scopes.items()):
            if key[0] == task:
                rows.append({'platform': key[1], 'state': key[2], 'family': key[3],
                             'applicable_ids': sorted(ids['applicable_ids']),
                             'not_applicable_ids': sorted(ids['not_applicable_ids']),
                             'evidence': copy.deepcopy(evidence)})
        result['Case%02d' % number] = {v: copy.deepcopy(rows) for v in ['X', 'Y']}
    return {'coverage_denominators': result, 'projection_identity_metadata': identities,
            'identity_policy': 'Required native/image: original assertion_id. N/A without assertion_id: mechanical state/rule identity only, never a compiled assertion or pass. Source: explicit original family/state/rule composite.'}


def registry(cells, tasks, evidence):
    """Metric-compatible rows; use projection() to retain per-cell identity labels."""
    return projection(cells, tasks, evidence)['coverage_denominators']


def pinned(path, expected):
    need(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected), 'External SHA256 required')
    raw = Path(path).read_bytes()
    need(sha(raw) == expected, 'External original byte pin differs')
    return raw


def seal_manifest(raw):
    result = {}
    for line in raw.decode('utf-8').splitlines():
        need('  ' in line, 'Original seal line needs SHA256 and path')
        digest, name = line.split('  ', 1)
        relative = PurePosixPath(name)
        need(re.fullmatch('[0-9a-f]{64}', digest) and name not in result
             and bool(name) and not relative.is_absolute() and str(relative) == name
             and '..' not in relative.parts and '\\' not in name,
             'Unique canonical relative original seal inventory required')
        result[name] = digest
    need(result, 'Original prospective seal must not be empty')
    return result


def sealed_projection(denominator, denominator_sha256, public_packets, public_packets_sha256, seal, seal_sha256):
    """Read only the three explicit caller-pinned files; never follow packet refs."""
    paths = [Path(denominator), Path(public_packets), Path(seal)]
    need(len({p.resolve() for p in paths}) == 3, 'Denominator/public packets/seal must be distinct inputs')
    seal_raw = pinned(paths[2], seal_sha256)
    manifest = seal_manifest(seal_raw)
    for path, wanted in [(paths[0], denominator_sha256), (paths[1], public_packets_sha256)]:
        need(path.parent.resolve() == paths[2].parent.resolve() and manifest.get(path.name) == wanted,
             'Input must be pinned by the externally authenticated prospective design seal')
    denominator_value = parse(pinned(paths[0], denominator_sha256))
    packets_value = parse(pinned(paths[1], public_packets_sha256))
    need(type(denominator_value) is dict and denominator_value.get('version') == 1 and type(denominator_value.get('cells')) is list,
         'Original version1 denominator cells required')
    need(type(packets_value) is dict and packets_value.get('version') == 1 and type(packets_value.get('tasks')) is list
         and all(type(t) is dict and 'task' in t for t in packets_value['tasks']), 'Original version1 public task order required')
    if 'counts' in denominator_value:
        counts = denominator_value['counts']
        observed = Counter(c.get('disposition') for c in denominator_value['cells'] if type(c) is dict)
        need(type(counts) is dict and set(counts) == DISPOSITIONS
             and all(type(counts[k]) is int and counts[k] == observed[k] for k in DISPOSITIONS), 'Original denominator count metadata differs from its cells')
    evidence = [{'path': str(p.resolve()), 'sha256': h} for p, h in
                [(paths[2], seal_sha256), (paths[0], denominator_sha256), (paths[1], public_packets_sha256)]]
    value = projection(denominator_value['cells'], [t['task'] for t in packets_value['tasks']], evidence)
    return {'version': 2, 'kind': 'frozen-applicability-projection', **value,
            'scope': 'Exact original applicability only; external prospective seal is complete-cell/task-order authority. No report/grade/map/native/image/source bodies read, no P/F/U or source approval inferred.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ['denominator', 'public-packets', 'seal']:
        p.add_argument('--'+key, type=Path, required=True)
        p.add_argument('--'+key+'-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    value = sealed_projection(a.denominator, a.denominator_sha256, a.public_packets,
                              a.public_packets_sha256, a.seal, a.seal_sha256)
    with a.output.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    a.output.chmod(0o444)
    print(json.dumps({'output': str(a.output), 'sha256': sha(a.output.read_bytes())}))


if __name__ == '__main__':
    main()
