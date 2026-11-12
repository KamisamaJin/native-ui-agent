#!/usr/bin/env python3
"""Independent revision: complete base and predecessor context binding.

Record integrity only. Does not interpret product grades, reveal assignment,
dispatch an agent, run an SDK, or grant a new native sample.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re


ORDER = ['Case%02d-I' % i for i in range(1, 6)] + ['Case%02d-%s' % (i, v) for i in range(1, 6) for v in ['X', 'Y']]
CONTROLS = {
    'ALARM-INSTRUCTIONS-v1.md': '5179657118f7ef69664a11290f14f38277ab1585915a26117d464253cbc2c4f8',
    'ALARM-GRADE-TEMPLATE-v1.json': 'd86534a2554c10e00cb92a7a281555c2715e1e3574679818c0731dadc0bbe58f',
    'ALARM-POLICY-v1.json': 'a1cef456bf95f25c4a048138f335fec1cc6a513c84ae3abd3b951f9699b85d00',
}
DISPATCH_DIRECTORY = 'alarm-dispatches-v4'


def need(value, message):
    if not value: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()
def ref(reader, path): return {'path': str(path), 'sha256': sha(reader.read_bytes(str(path)))}


def verify_base(phase, reader, reference, group):
    """Verify the original writer's exact {relative:SHA} member format."""
    value = phase.original(reader, reference)
    need(Path(reference['path']).name == 'SEAL.json'
         and type(value.get('version')) is int and value['version'] == 1
         and value.get('kind') == 'anonymous-fixed-version-input-seal'
         and value.get('anonymous_group') == group and isinstance(value.get('files'), dict),
         'Complete own base input seal required')
    files = value['files']; folder = Path(reference['path']).parent
    need({'PACKET.json', 'INSTRUCTIONS.md', 'GRADE-TEMPLATE.json'} <= set(files), 'Base core input members missing')
    need(phase.file_inventory(reader.directory(str(folder))) == set(files) | {'SEAL.json'}, 'Base member inventory differs')
    for name, expected in files.items():
        phase.safe_member(name)
        need(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected)
             and sha(reader.read_bytes(str(folder / name))) == expected, 'Base member bytes differ')
    for name in ['PACKET.json', 'GRADE-TEMPLATE.json']:
        document = phase.original(reader, {'path': str(folder / name), 'sha256': files[name]})
        need(document.get('anonymous_group') == group, 'Base member group differs')
    return reference


def verify_prepared(batch, reader, root, cause_ref, packets_ref, selection_ref, actors_ref):
    phase = batch._presentation['phase_barriers']; packet_code = batch._presentation['alarm_packet']
    phase.verify_index(reader, cause_ref, 'cause')
    cause = phase.original(reader, cause_ref)
    # No alarm packet body is read before the complete cause record barrier.
    selected = phase.original(reader, selection_ref)
    packets = phase.original(reader, packets_ref)
    actors = phase.original(reader, actors_ref)
    groups = set(ORDER)
    need(actors.get('kind') == 'original-independent-role-context-registry' and set(actors['groups']) == groups,
         'All original actor declarations required')
    cause_rows = {r['group']: r for r in cause['groups']}
    for group in ORDER:
        need(actors['groups'][group]['actors'] == cause_rows[group]['actors'], 'Original contexts differ')
    need(selected.get('kind') == 'all15-uniform-original-alarm-selection-seal'
         and type(selected.get('version')) is int and selected['version'] == 1
         and selected.get('original_root') == str(root)
         and selected.get('first_cause_barrier') == cause_ref
         and selected.get('closed_cause_contexts') == 30
         and selected.get('code_pins') == batch.code_pins()
         and selected.get('mapping_revealed_to_judges_or_model') is False
         and selected.get('quality_adjudicated') is False, 'Original all15 selection provenance differs')
    metadata_authority = selected.get('metadata_authority')
    metadata_context = batch.load_metadata_context(reader,root,metadata_authority,cause_ref) if metadata_authority is not None else None
    metadata_claims = set()
    for rows in [selected.get('groups'), packets.get('groups')]:
        need(isinstance(rows, list) and len(rows) == 15 and {r.get('group') for r in rows} == groups,
             'All fifteen selection and packet scopes required')
    need(type(packets.get('version')) is int and packets['version'] == 1
         and packets.get('selection_seal') == selection_ref
         and packets.get('code_pins') == batch.code_pins()
         and packets.get('phase2_dispatched') is False, 'Packet set is not bound to original selected inputs')
    for name, wanted in CONTROLS.items():
        need(sha(reader.read_bytes(str(root / 'business-quality-tools' / name))) == wanted, 'Prospective policy bytes differ')
    packet_rows = {r['group']: r for r in packets['groups']}
    bases = {}
    for row in selected['groups']:
        group = row['group']; spec = phase.original(reader, row['spec'])
        derivations = batch.pinned_value(reader, row['derivations'])
        need(type(spec.get('version')) is int and spec['version'] == 1
             and spec.get('kind') == 'explicit-anonymous-alarm-material-spec'
             and spec.get('anonymous_group') == group and spec.get('first_cause_barrier') == cause_ref
             and spec.get('anonymous_description', {}).get('anonymous_group') == group,
             'Selected original group/spec/cause differs')
        documents = packet_code._documents(spec)
        by_name = {d['anonymous_relative']: d for d in documents}
        description = {d['path']: d for d in spec['anonymous_description']['documents']}
        need(len(description) == len(documents) and set(description) == set(by_name), 'Material description membership differs')
        used_metadata = batch.verify_metadata_spec(spec,derivations,metadata_context,metadata_authority)
        need(not metadata_claims & used_metadata, 'Original worker metadata claim reused across groups')
        metadata_claims.update(used_metadata)
        derived = set()
        for item in derivations:
            batch.verify_derivation(reader, item, metadata_context=metadata_context); name = item['anonymous_relative']
            need(name not in derived and name in by_name and by_name[name]['original'] == item['derived']
                 and description[name].get('raw_original_sha256') == item['original']['sha256'],
                 'Original derivation is not bound to selected material')
            derived.add(name)
        need(derived == {n for n, d in description.items() if 'raw_original_sha256' in d}, 'Original derivation inventory differs')
        current = packet_rows[group]; seal = phase.original(reader, current['packet_seal'])
        ledger = phase.original(reader, current['operator_ledger'])
        folder = Path(current['packet_seal']['path']).parent
        need(Path(current['packet_seal']['path']).name == 'SEAL.json'
             and type(seal.get('version')) is int and seal['version'] == 1
             and seal.get('kind') == 'anonymous-alarm-material-seal' and seal.get('anonymous_group') == group,
             'Packet seal belongs to a different version')
        wanted = {}; copies = []; projections = []
        for document in documents:
            raw = reader.read_bytes(document['original']['path'])
            need(sha(raw) == document['original']['sha256'], 'Original selected bytes differ')
            name = document['anonymous_relative']
            if document['method'] == 'copy':
                anonymous = raw
                copies.append({'original': document['original'], 'anonymous_relative': name, 'bytes': len(raw), 'sha256': sha(raw)})
            else:
                value, proof = batch._presentation['anonymous_projection'].project(batch.strict_json(raw), **document['projection'])
                anonymous = packet_code.encoded(value)
                projections.append({'original': document['original'], 'anonymous_relative': name, 'bytes': len(anonymous), 'sha256': sha(anonymous), 'projection': proof})
            wanted[name] = {'sha256': sha(anonymous), 'bytes': len(anonymous)}
        description_raw = packet_code.encoded(spec['anonymous_description'])
        wanted['PACKET.json'] = {'sha256': sha(description_raw), 'bytes': len(description_raw)}
        for key, name, output_name in [('instructions', 'ALARM-INSTRUCTIONS-v1.md', 'INSTRUCTIONS.md'),
                                      ('grade_template', 'ALARM-GRADE-TEMPLATE-v1.json', 'GRADE-TEMPLATE.json')]:
            original = {'path': str(root / 'business-quality-tools' / name), 'sha256': CONTROLS[name]}
            need(spec[key] == original, 'Fixed instruction/template reference differs')
            raw = reader.read_bytes(original['path'])
            copies.append({'original': original, 'anonymous_relative': output_name, 'bytes': len(raw), 'sha256': sha(raw)})
            wanted[output_name] = {'sha256': sha(raw), 'bytes': len(raw)}
        expected_ledger = {'version': 1, 'implementation_revision': packet_code.IMPLEMENTATION_REVISION,
            'kind': 'operator-only-alarm-byte-and-projection-ledger', 'anonymous_group': group,
            'first_cause_barrier': cause_ref, 'closed_cause_contexts': 30, 'copies': copies, 'projections': projections,
            'quality_judgment': False, 'mapping_revealed': False, 'anonymous_inventory': wanted}
        need(ledger == expected_ledger, 'Packet byte/projection ledger differs from sealed selection')
        need(seal['files'] == {n: v['sha256'] for n, v in wanted.items()}, 'Packet seal differs from selected materials')
        need(phase.file_inventory(reader.directory(str(folder))) == set(wanted) | {'SEAL.json'}, 'Packet membership differs')
        for name, metadata in wanted.items():
            raw = reader.read_bytes(str(folder / name))
            need(sha(raw) == metadata['sha256'] and len(raw) == metadata['bytes'], 'Packet member bytes differ')
        inputs = []
        for original in cause_rows[group]['inputs']:
            value = phase.original(reader, original)
            if value.get('kind') == 'anonymous-fixed-version-input-seal' and value.get('anonymous_group') == group:
                inputs.append(original)
        need(len(inputs) == 1, 'Unique original cause input required')
        bases[group] = verify_base(phase, reader, inputs[0], group)
    need(metadata_context is None or metadata_claims == set(metadata_context.documents), 'All ten authorized metadata originals required')
    return {'metadata_authority':metadata_authority,'cause_rows': cause_rows, 'packet_rows': packet_rows, 'base_refs': bases,
            'bindings': {'cause_index': cause_ref, 'packets_index': packets_ref,
                         'selection_seal': selection_ref, 'actor_registry': actors_ref,'metadata_authority':metadata_authority}}


def verify_previous(phase, reader, root, group, previous_ref, cause_ref, packet_rows, *, cause_rows, base_refs, bindings):
    need(set(bindings) == {'cause_index', 'packets_index', 'selection_seal', 'actor_registry', 'batch', 'dispatcher','metadata_authority'}
         and bindings['cause_index'] == cause_ref, 'Complete current dispatch input/code bindings required')
    prior = ORDER[:ORDER.index(group)]
    need((previous_ref is None) == (not prior), 'Immediate preceding pair closure required')
    current = previous_ref
    for before in reversed(prior):
        expected = root / 'cache/business/blind-quality/episodes' / before / 'alarm/END.json'
        need(current['path'] == str(expected), 'Previous closure chain order differs')
        end = phase.original(reader, current)
        need(type(end.get('version')) is int and end['version'] == 2
             and end.get('kind') == 'parallel-independent-alarm-episode-end' and end.get('status') == 'sealed'
             and end.get('anonymous_group') == before and end.get('judges') == ['J1', 'J2'], 'Previous alarm pair not closed')
        start = phase.original(reader, end['start'])
        need(end['start']['path'] == str(expected.with_name('START.json'))
             and start.get('version') == 4 and type(start.get('version')) is int
             and start.get('kind') == 'parallel-independent-alarm-episode-start'
             and start.get('anonymous_group') == before and start.get('judges') == ['J1', 'J2']
             and start.get('first_cause_barrier') == cause_ref
             and start.get('metadata_authority') == bindings['metadata_authority']
             and start.get('packet_seal') == packet_rows[before]['packet_seal']
             and start.get('base_packet') == base_refs[before]
             and start.get('original_cause_episode') == cause_rows[before]['episode_end'], 'Previous pair input binding differs')
        destination = root / 'operators/cohort2/coordination' / DISPATCH_DIRECTORY / before
        prepared_ref = start.get('dispatch_prepared')
        need(isinstance(prepared_ref, dict) and prepared_ref.get('path') == str(destination / 'PREPARED.json'), 'Previous dispatch reference differs')
        prepared = phase.original(reader, prepared_ref)
        need(type(prepared.get('version')) is int and prepared['version'] == 4
             and prepared.get('kind') == 'verified-original-context-alarm-dispatch'
             and prepared.get('group') == before and prepared.get('mapping_revealed') is False
             and prepared.get('previous_pair') == start.get('previous_pair')
             and prepared.get('base_packet') == base_refs[before]
             and prepared.get('packet_seal') == packet_rows[before]['packet_seal']
             and prepared.get('original_cause_episode') == cause_rows[before]['episode_end']
             and all(prepared.get(key) == expected for key, expected in bindings.items()), 'Previous dispatch input/code binding differs')
        entries = prepared.get('entries')
        need(isinstance(entries, list) and len(entries) == 2
             and {e.get('judge') for e in entries} == {'J1', 'J2'}, 'Previous dispatch pair entries differ')
        for entry in entries:
            judge = entry['judge']; output_path = root / 'cache/business/blind-quality/grades' / before / judge / 'alarm'
            need(set(entry) == {'judge', 'actor', 'prompt', 'output'}
                 and entry['actor'] == cause_rows[before]['actors'][judge]
                 and entry['output'] == str(output_path)
                 and entry['prompt'].get('path') == str(destination / (judge + '-PROMPT.txt')), 'Previous original actor/output/prompt differs')
            phase.recorded_ref(entry['prompt'])
            need(sha(reader.read_bytes(entry['prompt']['path'])) == entry['prompt']['sha256'], 'Previous prompt bytes differ')
        need(set(end['outputs']) == {'J1', 'J2'}, 'Previous pair has incomplete outputs')
        for judge, output in end['outputs'].items():
            wanted_path = root / 'cache/business/blind-quality/grades' / before / judge / 'alarm/SEAL.json'
            need(isinstance(output, dict) and set(output) == {'seal', 'grade', 'members'}
                 and output['seal']['path'] == str(wanted_path), 'Previous original grade output reference differs')
            verified = phase.verify_role_seal(reader, output['seal'], before, judge, 'alarm')
            need(output['grade'] == verified['grade'] and type(output['members']) is int
                 and output['members'] == verified['member_count'], 'Previous exact grade/member reference differs')
        current = start.get('previous_pair')
    need(current is None, 'Unexpected predecessor before first original pair')


def load_pinned_module(path, wanted, name):
    need(re.fullmatch('[0-9a-f]{64}', wanted) is not None and sha(path.read_bytes()) == wanted, 'External code pin differs')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', required=True, type=Path); p.add_argument('--group', required=True)
    for name in ['batch', 'cause-index', 'packets-index', 'selection-seal', 'actors']:
        p.add_argument('--' + name, required=True, type=Path); p.add_argument('--' + name + '-sha256', required=True)
    p.add_argument('--previous-end', type=Path); p.add_argument('--previous-end-sha256')
    a = p.parse_args(); root = a.root.resolve(); need(a.group in ORDER, 'Unknown original group')
    batch = load_pinned_module(a.batch, a.batch_sha256, 'alarm_dispatch_batch')
    reader = batch.LiveReader(root); phase = batch._presentation['phase_barriers']
    def arg_ref(name): return {'path': str(getattr(a, name)), 'sha256': getattr(a, name + '_sha256')}
    cause_ref, packets_ref = arg_ref('cause_index'), arg_ref('packets_index')
    checked = verify_prepared(batch, reader, root, cause_ref, packets_ref, arg_ref('selection_seal'), arg_ref('actors'))
    need(checked['metadata_authority'] is not None, 'Default dispatch requires externally pinned worker metadata authority')
    dispatcher_ref = ref(reader, Path(__file__).resolve())
    checked['bindings'].update(batch=arg_ref('batch'), dispatcher=dispatcher_ref)
    previous = {'path': str(a.previous_end), 'sha256': a.previous_end_sha256} if a.previous_end else None
    need((a.previous_end is None) == (a.previous_end_sha256 is None), 'Complete external previous-end path/SHA pair required')
    verify_previous(phase, reader, root, a.group, previous, cause_ref, checked['packet_rows'],
                    cause_rows=checked['cause_rows'], base_refs=checked['base_refs'], bindings=checked['bindings'])
    clock = load_pinned_module(root / 'business-quality-tools/quality_clock.py',
        '8a91e9d25574483b7c3275350c0b04b90cdb8f6cba5b91da041968a0a5e5a45c', 'alarm_dispatch_clock')
    row = checked['cause_rows'][a.group]; packet_ref = checked['packet_rows'][a.group]['packet_seal']
    base_ref = checked['base_refs'][a.group]; base = Path(base_ref['path']).parent
    supplement_root = root / 'business-source-review-cohort2/source-contract-supplements'
    outer_ref = {'path': str(supplement_root / 'OPERATOR-SEAL.json'), 'sha256': '9f3bf306a5a57875cfb6149fdf9365b6476599074486f60b1d0c65fb304453bc'}
    outer = phase.original(reader, outer_ref)
    supplement = supplement_root / ('case-%02d' % int(a.group[4:6])) / 'anonymous'; inventory = {}
    prefix = supplement.relative_to(supplement_root).as_posix() + '/'
    expected_members = {name[len(prefix):] for name in outer['files'] if name.startswith(prefix)}
    need(phase.file_inventory(reader.directory(str(supplement))) == expected_members, 'Original own supplement membership differs')
    for name in sorted(phase.file_inventory(reader.directory(str(supplement)))):
        raw = reader.read_bytes(str(supplement / name)); wanted = outer['files'][(supplement / name).relative_to(supplement_root).as_posix()]
        need(sha(raw) == wanted, 'Original own source-contract supplement differs')
        inventory[name] = {'sha256': wanted, 'bytes': len(raw)}
    need(len(inventory) == 153, 'Complete original own supplement required')
    supplement_sha = sha(json.dumps(inventory, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
    coord = root / 'operators/cohort2/coordination'; destination = coord / DISPATCH_DIRECTORY / a.group
    episode = root / 'cache/business/blind-quality/episodes' / a.group / 'alarm'
    need(not destination.exists() and not episode.exists(), 'Fresh original alarm dispatch and episode required')
    entries = []
    for judge in ['J1', 'J2']:
        output = root / 'cache/business/blind-quality/grades' / a.group / judge / 'alarm'
        need(not output.exists(), 'Original alarm output already exists')
        prompt = destination / (judge + '-PROMPT.txt'); original = row['seals'][judge]
        text = f'''You are original independent reviewer {judge} returning ONLY for the sealed alarm phase of {a.group}. Continue your own prior context.
Allowed reads: this instruction; your original base packet {base} (SEAL SHA {base_ref['sha256']}); unchanged own source-contract supplement {supplement} (153files, canonical sorted compact ensure_ascii=False {{relative:{{sha256,bytes}}}} digest {supplement_sha}); own original cause output {Path(original['path']).parent} (SEAL SHA {original['sha256']}); new own-version alarm packet {Path(packet_ref['path']).parent} (SEAL SHA {packet_ref['sha256']}). Write ONLY {output}.
Verify every supplied seal/member. Follow packet INSTRUCTIONS.md and GRADE-TEMPLATE.json. Inspect original source/native/PNGs needed to assess all candidate claims. Original statuses and worker statements are claims, not truth. Deduplicate repeated product causes, retain all unadjudicated/unknown claims, separate positive validation claims and measurement/infrastructure/work from defect alarms. Preserve exact supporting source version and worker-public versus post-seal-private visibility. Image aliases need exact SHA and independent state/epoch binding. No expected declaration substitutes for an actual observation.
Keep first cause grade unchanged. Evidence-backed additions/corrections belong only in your new sealed appendix; later matcher preserves agreements/disagreements. No sibling version, other judge, operator parent, map, tool identity, cost, SDK execution, source/expected edit, model override or subagent. All original reports are supplied; do not invent a defect denominator or turn uninspected work into an FP.
Complete grade.json and actual inspection/claim ledgers, seal all regular output members readonly. Return only exact SEAL path/SHA and coverage; omit product findings from coordinator completion. Remain available. This phase establishes records, not delivery or assignment.
'''
        batch.write(prompt, text.encode()); entries.append({'judge': judge, 'actor': row['actors'][judge], 'prompt': ref(reader, prompt), 'output': str(output)})
    prepared = {'version': 4, 'kind': 'verified-original-context-alarm-dispatch', 'group': a.group, 'entries': entries, 'cause_index': cause_ref,
        'packets_index': packets_ref, 'selection_seal': arg_ref('selection_seal'), 'actor_registry': arg_ref('actors'),
        'metadata_authority':checked['metadata_authority'],
        'batch': arg_ref('batch'), 'dispatcher': dispatcher_ref, 'base_packet': base_ref, 'packet_seal': packet_ref,
        'original_cause_episode': row['episode_end'], 'previous_pair': previous, 'mapping_revealed': False}
    batch.write(destination / 'PREPARED.json', batch.encoded(prepared))
    start = {'version': 4, 'kind': 'parallel-independent-alarm-episode-start', 'anonymous_group': a.group,
        'metadata_authority':checked['metadata_authority'],
        **clock.point('started'), 'judges': ['J1', 'J2'], 'packet_seal': packet_ref,
        'first_cause_barrier': cause_ref, 'original_cause_episode': row['episode_end'],
        'base_packet': base_ref, 'previous_pair': previous, 'dispatch_prepared': ref(reader, destination / 'PREPARED.json'),
        'scope': 'All15 original selections/derivations/packet/context bindings verified. Same original actors; concurrent pair wall counted once. No quality or mapping inference.'}
    batch.write(episode / 'START.json', batch.encoded(start))
    print(json.dumps({'group': a.group, 'entries': entries, 'prepared': ref(reader, destination / 'PREPARED.json')}))


if __name__ == '__main__': main()
