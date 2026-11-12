#!/usr/bin/env python3
"""Prepare original-context alarm roles only after complete sealed input sets."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p): return {'path': str(p), 'sha256': sha(p)}


def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(value, f, sort_keys=True, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    p.chmod(0o444)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True); p.add_argument('--group', required=True)
    for name in ['cause-index', 'packets-index', 'actors']:
        p.add_argument('--' + name, type=Path, required=True); p.add_argument('--' + name + '-sha256', required=True)
    a = p.parse_args(); root = a.root.resolve(); coord = root / 'operators/cohort2/coordination'
    phase_root = root / 'publication-alarm-review/revision-v2'
    pins = {'anonymous_projection.py': '5bc14d37d11bd755dad38cf1f13b5bbc133eccedceb13ebb1e037dbd07361f2b',
            'phase_barriers.py': 'd940081fc9589df43589a1967442da5e78f6b45cb9c15c97ae7f5dca56407d9d'}
    for name, expected in pins.items():
        if sha(phase_root / name) != expected: raise ValueError('Reviewed phase code differs')
        if name[:-3] in sys.modules: raise ValueError('Fresh dispatch process required')
    sys.path.insert(0, str(phase_root)); import phase_barriers as phase
    reader_path = root / 'publication-resolver/resolver.py'
    if sha(reader_path) != '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204': raise ValueError('Reader code differs')
    spec = importlib.util.spec_from_file_location('alarm_dispatch_live_reader', reader_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    class Reader:
        def read_bytes(self, original): return module.read_regular(original)[0]
        def read_json(self, original): return module.strict_json(self.read_bytes(original))
        def directory(self, original):
            path = module.absolute(str(original)); fd = module.open_directory(path); os.close(fd); return path
    reader = Reader(); cause_ref = {'path': str(a.cause_index), 'sha256': a.cause_index_sha256}
    phase.verify_index(reader, cause_ref, 'cause')
    cause = phase.original(reader, cause_ref)
    packets = phase.original(reader, {'path': str(a.packets_index), 'sha256': a.packets_index_sha256})
    actors = phase.original(reader, {'path': str(a.actors), 'sha256': a.actors_sha256})
    expected = phase.GROUPS; rows = packets.get('groups')
    if not isinstance(rows, list) or len(rows) != 15 or {r['group'] for r in rows} != expected or set(actors['groups']) != expected:
        raise ValueError('All fifteen original packet/actor scopes required')
    for row in rows:
        seal = phase.original(reader, row['packet_seal']); folder = Path(row['packet_seal']['path']).parent
        if seal.get('kind') != 'anonymous-alarm-material-seal' or seal.get('anonymous_group') != row['group']:
            raise ValueError('Alarm packet seal belongs to another version')
        members = phase.file_inventory(reader.directory(str(folder)))
        if members != set(seal['files']) | {'SEAL.json'}: raise ValueError('Alarm packet member inventory differs')
        for name, wanted in seal['files'].items():
            phase.safe_member(name)
            if hashlib.sha256(reader.read_bytes(str(folder / name))).hexdigest() != wanted:
                raise ValueError('Alarm packet member bytes differ')
    order = ['Case0%d-I' % i for i in range(1, 6)] + ['Case0%d-%s' % (i, v) for i in range(1, 6) for v in ['X', 'Y']]
    if a.group not in order: raise ValueError('Unknown original anonymous group')
    for before in order[:order.index(a.group)]:
        if not (root / 'cache/business/blind-quality/episodes' / before / 'alarm/END.json').is_file():
            raise ValueError('Previous alarm pair must close before next dispatch')
    cause_row = next(r for r in cause['groups'] if r['group'] == a.group)
    if actors['groups'][a.group]['actors'] != cause_row['actors']: raise ValueError('Original own-version actors required')
    row = next(r for r in rows if r['group'] == a.group); packet = Path(row['packet_seal']['path']).parent
    first = root / 'cache/business/blind-quality/episodes' / a.group / 'cause/START.json'
    first_start = reader.read_json(str(first)); base = Path(first_start['packet_seal']['path']).parent
    supplement_root = root / 'business-source-review-cohort2/source-contract-supplements'
    outer_ref = {'path': str(supplement_root / 'OPERATOR-SEAL.json'),
                 'sha256': '9f3bf306a5a57875cfb6149fdf9365b6476599074486f60b1d0c65fb304453bc'}
    outer = phase.original(reader, outer_ref)
    supplement = supplement_root / ('case-%02d' % int(a.group[4:6])) / 'anonymous'
    inventory = {}
    for name in sorted(phase.file_inventory(reader.directory(str(supplement)))):
        raw = reader.read_bytes(str(supplement / name)); wanted = outer['files'][(supplement / name).relative_to(supplement_root).as_posix()]
        if hashlib.sha256(raw).hexdigest() != wanted: raise ValueError('Original own supplement differs')
        inventory[name] = {'sha256': wanted, 'bytes': len(raw)}
    if len(inventory) != 153: raise ValueError('Complete original own contract supplement required')
    supplement_digest = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    clock_path = root / 'business-quality-tools/quality_clock.py'
    if sha(clock_path) != '8a91e9d25574483b7c3275350c0b04b90cdb8f6cba5b91da041968a0a5e5a45c': raise ValueError('Shared clock differs')
    spec = importlib.util.spec_from_file_location('alarm_dispatch_shared_clock', clock_path)
    clock = importlib.util.module_from_spec(spec); spec.loader.exec_module(clock)
    episode = root / 'cache/business/blind-quality/episodes' / a.group / 'alarm'
    save(episode / 'START.json', {'version': 2, 'kind': 'parallel-independent-alarm-episode-start',
        'anonymous_group': a.group, **clock.point('started'), 'judges': ['J1', 'J2'],
        'packet_seal': row['packet_seal'], 'first_cause_barrier': cause_ref,
        'original_cause_episode': ref(first.parent / 'END.json'),
        'scope': 'Same original own-version contexts, after verified all30cause and all15 sealed alarm packets. Record concurrent pair wall once; no quality or mapping inference.'})
    entries = []
    for judge in ['J1', 'J2']:
        original_grade = cause_row['seals'][judge]
        output = root / 'cache/business/blind-quality/grades' / a.group / judge / 'alarm'
        output.mkdir(parents=True, exist_ok=False)
        prompt = coord / 'alarm-dispatches' / a.group / (judge + '-PROMPT.txt')
        text = f'''You are original independent reviewer {judge} returning for the sealed alarm phase of {a.group}.
Continue ONLY your own prior context. Allowed reads: this instruction; own original base packet {base}; own unchanged source-contract supplement {supplement}; own original cause output {Path(original_grade['path']).parent}; and new own-version alarm packet {packet}. Write ONLY {output}.
Verify alarm SEAL.json SHA {row['packet_seal']['sha256']} and all members. Original cause SEAL SHA is {original_grade['sha256']}. Supplement has153 files and canonical {{relative:{{sha256,bytes}}}} digest {supplement_digest} (sorted keys, compact JSON, ensure_ascii=False). Original base/source inputs remain exact.
Follow the new packet INSTRUCTIONS.md and GRADE-TEMPLATE.json completely. Inspect relevant exact source/native/PNGs, preserve every deduplicated candidate claim and uncertainty, distinguish genuine defect alarms from positive claims/measurement/infrastructure/work items. Preserve worker-public versus post-seal-private visibility and exact supporting source versions. Do not treat a recorded P/F/U or selfclaim as truth, manufacture a nonzero defect denominator, or silently turn unadjudicated work into an FP. Original native/image aliases require SHA proof and exact state/epoch membership.
Keep your original first cause grade unchanged; new evidence-backed causes/corrections go only in the new sealed appendix for the later matcher. No sibling/other-judge result, operator parent, mapping, tool identity, costs, SDK, source/expected edits, model overrides or subagents.
Complete the template and actual inspection/claim ledgers, seal all regular output members readonly as instructed. Return only exact SEAL path/SHA and coverage; no product findings to coordinator. Remain available after completion; this does not reveal assignment or establish delivery.
'''
        write = prompt.parent.mkdir(parents=True, exist_ok=True)
        with prompt.open('x') as f: f.write(text); f.flush(); os.fsync(f.fileno())
        prompt.chmod(0o444); entries.append({'judge': judge, 'actor': cause_row['actors'][judge], 'prompt': ref(prompt), 'output': str(output)})
    save(coord / 'alarm-dispatches' / a.group / 'PREPARED.json', {'version': 1, 'group': a.group,
         'entries': entries, 'first_cause_barrier': cause_ref, 'all_packets': ref(a.packets_index), 'mapping_revealed': False})
    print(json.dumps({'group': a.group, 'entries': entries}))


if __name__ == '__main__': main()
