"""Project preimplementation applicability, without reading evaluated results.

This is a publication input adapter. It cannot determine P/F/U, change a frozen
denominator, decide delivery, or infer an arm assignment.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path


def need(value, message):
    if not value:
        raise ValueError(message)


def registry(cells, tasks, evidence):
    need(isinstance(tasks, list) and len(tasks) == 5 and len(set(tasks)) == 5,
         'Five distinct, prospectively ordered task IDs required')
    need(isinstance(evidence, list) and evidence, 'Frozen applicability evidence required')
    need(isinstance(cells, list) and cells, 'Original nonempty denominator cells required')
    scopes = defaultdict(lambda: {'applicable_ids': [], 'not_applicable_ids': []})
    seen = set()
    for cell in cells:
        task, platform, family, state, rule = (cell[k] for k in ['task', 'platform', 'family', 'state', 'rule_id'])
        need(task in tasks and platform in {'ios', 'android'} and family in {'public', 'private'}
             and isinstance(state, str) and state and isinstance(rule, str) and rule,
             'Original task/platform/family/state/rule identity required')
        source = cell['kind'] == 'source'
        disposition = cell['disposition']
        need(disposition in {'required', 'N/A', 'required-source-review'}, 'Unknown applicability disposition')
        need((disposition == 'required-source-review') == source,
             'Source responsibility and native/image applicability cannot be interchanged')
        if source:
            name = family + '/' + state + '/' + rule
            key = (task, platform, family + '/' + state, 'source')
        else:
            name = state + '/' + rule
            need(cell.get('assertion_id', name) == name, 'Original atomic ID differs from its state/rule')
            key = (task, platform, state, family + '_native_image')
        identity = (key, name)
        need(identity not in seen, 'Duplicate frozen obligation')
        seen.add(identity)
        scopes[key]['not_applicable_ids' if disposition == 'N/A' else 'applicable_ids'].append(name)
    result = {}
    for number, task in enumerate(tasks, 1):
        rows = []
        for key, ids in sorted(scopes.items()):
            if key[0] != task:
                continue
            rows.append({'platform': key[1], 'state': key[2], 'family': key[3],
                         'applicable_ids': sorted(ids['applicable_ids']),
                         'not_applicable_ids': sorted(ids['not_applicable_ids']),
                         'evidence': evidence})
        need({(r['platform'], r['family']) for r in rows} ==
             {(p, f) for p in ['ios', 'android'] for f in ['public_native_image', 'private_native_image', 'source']},
             'Every task must retain both platforms and all evidence families')
        # X/Y use the same original contract. This is deliberately independent
        # of the concealed treatment assignment and observed result values.
        result['Case%02d' % number] = {v: rows for v in ['X', 'Y']}
    return result


def pinned(path, wanted):
    raw = Path(path).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == wanted, 'External original byte pin differs')
    return raw


def main():
    p = argparse.ArgumentParser()
    for key in ['denominator', 'public_packets', 'seal']:
        p.add_argument('--' + key.replace('_', '-'), required=True, type=Path)
        p.add_argument('--' + key.replace('_', '-') + '-sha256', required=True)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    raw_seal = pinned(a.seal, a.seal_sha256)
    manifest = {}
    for line in raw_seal.decode().splitlines():
        sha, name = line.split('  ', 1)
        need(name not in manifest and len(sha) == 64, 'Unique original seal inventory required')
        manifest[name] = sha
    for path, wanted in [(a.denominator, a.denominator_sha256), (a.public_packets, a.public_packets_sha256)]:
        need(path.parent == a.seal.parent and manifest.get(path.name) == wanted,
             'Input must be pinned by the prospectively sealed design inventory')
    denominator = json.loads(pinned(a.denominator, a.denominator_sha256))
    packets = json.loads(pinned(a.public_packets, a.public_packets_sha256))
    evidence = [{'path': str(a.seal.resolve()), 'sha256': a.seal_sha256},
                {'path': str(a.denominator.resolve()), 'sha256': a.denominator_sha256},
                {'path': str(a.public_packets.resolve()), 'sha256': a.public_packets_sha256}]
    value = {'version': 1, 'kind': 'frozen-applicability-projection',
             'coverage_denominators': registry(denominator['cells'], [t['task'] for t in packets['tasks']], evidence),
             'scope': 'Exact preimplementation mandatory/N/A cell projection only. No report, grade, mapping, P/F/U, current source or delivery inference.'}
    with a.output.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2); f.write('\n')
    a.output.chmod(0o444)
    print(json.dumps({'output': str(a.output), 'sha256': hashlib.sha256(a.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
