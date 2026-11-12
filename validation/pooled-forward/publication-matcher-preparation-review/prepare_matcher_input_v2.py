"""Verify all review barriers and disclose neutral correspondence inputs only.

No grading, cost joining, SDK work, assignment access or source editing occurs.
Original packets and judgments stay at their sealed read-only locations.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys


def sha(raw): return hashlib.sha256(raw).hexdigest()
def need(ok, why):
    if not ok: raise ValueError(why)


ALARM_PACKET_CONTROLS = {'INSTRUCTIONS.md': '5179657118f7ef69664a11290f14f38277ab1585915a26117d464253cbc2c4f8',
                         'GRADE-TEMPLATE.json': 'd86534a2554c10e00cb92a7a281555c2715e1e3574679818c0731dadc0bbe58f'}


def verify_packet(phase, reader, reference, group, kind):
    """Exact original byte inventory plus the published packet core identity."""
    need(kind in {'anonymous-fixed-version-input-seal', 'anonymous-alarm-material-seal'}, 'Unsupported packet kind')
    value = phase.original(reader, reference);folder = Path(reference['path']).parent
    need(Path(reference['path']).name == 'SEAL.json' and value.get('kind') == kind
         and value.get('anonymous_group') == group and type(value.get('version')) is int
         and value['version'] == 1 and isinstance(value.get('files'), dict), 'Exact anonymous input kind/group required')
    files = value['files']
    need({'PACKET.json', 'INSTRUCTIONS.md', 'GRADE-TEMPLATE.json'} <= set(files), 'Packet core members missing')
    if kind == 'anonymous-alarm-material-seal':
        need(all(files[name] == expected for name, expected in ALARM_PACKET_CONTROLS.items()), 'Fixed prospective alarm controls differ')
    need(phase.file_inventory(reader.directory(str(folder))) == set(files) | {'SEAL.json'}, 'Input members differ')
    for name, expected in files.items():
        phase.safe_member(name)
        need(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected)
             and sha(reader.read_bytes(str(folder/name))) == expected, 'Input bytes differ')
    names = ['PACKET.json', 'GRADE-TEMPLATE.json'] if kind == 'anonymous-fixed-version-input-seal' else ['PACKET.json']
    # The alarm template is the frozen group-neutral template. Only base
    # templates have a filled own-group identity in the original writer schema.
    for name in names:
        member = phase.original(reader, {'path': str(folder/name), 'sha256': files[name]})
        need(member.get('anonymous_group') == group, 'Packet core member group differs')
    if kind == 'anonymous-alarm-material-seal':
        template = phase.original(reader, {'path': str(folder/'GRADE-TEMPLATE.json'), 'sha256': files['GRADE-TEMPLATE.json']})
        need(type(template.get('version')) is int and template['version'] == 1 and template.get('kind') == 'independent-blind-alarm-grade'
             and template.get('anonymous_group') is None and template.get('judge_id') is None, 'Prospective group-neutral alarm template differs')
    return reference


def group_packets(phase, reader, original, alarm_row, group):
    def select(row, kind):
        refs = [ref for ref in row['inputs'] if phase.original(reader, ref).get('kind') == kind]
        need(len(refs) == 1, 'Exactly one original own base/alarm packet required')
        return refs[0]
    base = select(original, 'anonymous-fixed-version-input-seal')
    alarm_base = select(alarm_row, 'anonymous-fixed-version-input-seal')
    need(alarm_base == base, 'Alarm and cause must retain the exact original base reference')
    alarm = select(alarm_row, 'anonymous-alarm-material-seal')
    return (verify_packet(phase, reader, base, group, 'anonymous-fixed-version-input-seal'),
            verify_packet(phase, reader, alarm, group, 'anonymous-alarm-material-seal'))


def episode_seals(phase, reader, reference, group, kind, field):
    episode = phase.original(reader, reference)
    need(episode.get('anonymous_group') == group and type(episode.get('version')) is int and episode['version'] == 1
         and episode.get('kind') == kind, 'Unknown or cross-scope historical cause episode')
    start = phase.original(reader, episode['start'])
    need(start.get('anonymous_group') == group, 'Historical cause START belongs to another group')
    if 'judges' in start:need(isinstance(start['judges'], list) and len(start['judges']) == 2 and set(start['judges']) == {'J1', 'J2'}, 'Historical cause START roles differ')
    seals = episode.get(field)
    need(isinstance(seals, dict) and set(seals) == {'J1', 'J2'}, 'Historical cause episode roles incomplete')
    for value in seals.values():phase.recorded_ref(value)
    return seals


def earlier_causes(phase, reader, original, group, judge):
    """Retain original reviews only through the externally pinned episode chain."""
    current = original['seals'][judge]
    first = Path(current['path']).parents[1]/'cause/SEAL.json'
    if str(first) == current['path']:return []
    aggregate = phase.original(reader, original['episode_end'])
    need(aggregate.get('anonymous_group') == group and type(aggregate.get('version')) is int and aggregate['version'] == 1
         and aggregate.get('kind') == 'independent-cause-version-final-seal-index'
         and isinstance(aggregate.get('original_episode'), dict) and isinstance(aggregate.get('complete_input_supplement_episode'), dict),
         'Pinned original/supplement cause lineage required')
    initial = episode_seals(phase, reader, aggregate['original_episode'], group, 'parallel-original-cause-episode-sealed', 'independent_original_grade_seals')
    effective = episode_seals(phase, reader, aggregate['complete_input_supplement_episode'], group, 'parallel-source-contract-supplement-episode-sealed', 'grade_seals')
    need(effective == aggregate.get('grade_seals') == original['seals'], 'Supplement episode changes effective cause refs')
    earlier = initial[judge]
    need(earlier['path'] == str(first), 'Original earlier cause namespace differs')
    phase.verify_role_seal(reader, earlier, group, judge, 'cause')
    return [earlier]


def disclosed_barrier(phase, value):
    """New derived role-only data; original barrier refs stay operator-only."""
    keys = {'version', 'implementation_revision', 'status', 'phase', 'groups', 'distinct_contexts', 'index', 'verified_roles', 'scope'}
    need(set(value) == keys and value.get('status') == 'verified' and value.get('phase') in {'cause', 'alarm'}, 'Unknown verified barrier projection')
    need(type(value.get('version')) is int and value['version'] == 1 and type(value.get('implementation_revision')) is int
         and value['implementation_revision'] == 2 and type(value.get('groups')) is int and value['groups'] == 15
         and type(value.get('distinct_contexts')) is int and value['distinct_contexts'] == 30, 'Verified barrier projection counts differ')
    rows = value['verified_roles']
    need(isinstance(rows, list) and len(rows) == 15 and {r.get('group') for r in rows} == phase.GROUPS, 'Complete anonymous role projection required')
    disclosed = []
    for row in rows:
        need(set(row) == {'group', 'roles'} and set(row['roles']) == {'J1', 'J2'}, 'Unknown role projection fields')
        roles = {}
        for judge, role in row['roles'].items():
            need(set(role) == {'seal', 'member_count', 'grade'}, 'Unknown role projection fields')
            phase.recorded_ref(role['seal']);phase.recorded_ref(role['grade'])
            roles[judge] = {'seal': dict(role['seal']), 'grade': dict(role['grade']), 'member_count': role['member_count']}
        disclosed.append({'group': row['group'], 'roles': roles})
    return {key: (disclosed if key == 'verified_roles' else value[key]) for key in keys-{'index'}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True, type=Path)
    p.add_argument('--id', required=True)
    for name in ['cause-index', 'alarm-index']:
        p.add_argument('--' + name, required=True, type=Path)
        p.add_argument('--' + name + '-sha256', required=True)
    a = p.parse_args(); root = a.root.resolve()
    need(a.id.isascii() and a.id.replace('-', '').isalnum(), 'Fresh finite output identifier required')
    code = root / 'publication-alarm-review/revision-v2'
    pins = {'anonymous_projection.py': '5bc14d37d11bd755dad38cf1f13b5bbc133eccedceb13ebb1e037dbd07361f2b',
            'phase_barriers.py': 'd940081fc9589df43589a1967442da5e78f6b45cb9c15c97ae7f5dca56407d9d'}
    for name, expected in pins.items(): need(sha((code/name).read_bytes()) == expected, 'Frozen barrier code differs')
    need(not any(name[:-3] in sys.modules for name in pins), 'Fresh pinned matcher preparation process required')
    sys.path.insert(0, str(code))
    import phase_barriers as phase
    import anonymous_projection as projection
    resolver = root / 'publication-resolver/resolver.py'
    need(sha(resolver.read_bytes()) == '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204', 'Frozen reader differs')
    spec = importlib.util.spec_from_file_location('matcher_no_follow_reader', resolver)
    r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
    class Reader:
        def read_bytes(self, original): return r.read_regular(original)[0]
        def read_json(self, original): return projection.strict_json(self.read_bytes(original))
        def directory(self, original):
            path = r.absolute(str(original)); fd = r.open_directory(path); os.close(fd); return path
    reader = Reader()
    def ref(path): return {'path': str(path), 'sha256': sha(reader.read_bytes(str(path)))}
    cause_ref = {'path': str(a.cause_index), 'sha256': a.cause_index_sha256}
    alarm_ref = {'path': str(a.alarm_index), 'sha256': a.alarm_index_sha256}
    cause_verified = phase.verify_index(reader, cause_ref, 'cause')
    alarm_verified = phase.verify_index(reader, alarm_ref, 'alarm')
    cause = phase.original(reader, cause_ref); alarm = phase.original(reader, alarm_ref)
    need(alarm['first_cause_barrier'] == cause_ref, 'Exact all30 predecessor required')
    groups = []
    cause_rows = {x['group']: x for x in cause['groups']}
    for row in alarm['groups']:
        group = row['group']; original = cause_rows[group]
        base_ref, alarm_packet_ref = group_packets(phase, reader, original, row, group)
        judges = {}
        for judge in ['J1', 'J2']:
            current = original['seals'][judge]
            historical = earlier_causes(phase, reader, original, group, judge)
            judges[judge] = {'effective_cause': current, 'retained_earlier_causes': historical, 'alarm': row['seals'][judge]}
        groups.append({'group': group, 'base_packet': base_ref, 'alarm_packet': alarm_packet_ref, 'judges': judges})
    need({g['group'] for g in groups} == phase.GROUPS, 'All15 original versions required')
    supplement = root / 'business-source-review-cohort2/source-contract-supplements'
    outer_ref = {'path': str(supplement/'OPERATOR-SEAL.json'), 'sha256': '9f3bf306a5a57875cfb6149fdf9365b6476599074486f60b1d0c65fb304453bc'}
    outer = phase.original(reader, outer_ref); supplements = []
    for i in range(1, 6):
        folder = supplement / ('case-%02d' % i) / 'anonymous'; prefix = folder.relative_to(supplement).as_posix() + '/'
        expected = {name[len(prefix):]: value for name, value in outer['files'].items() if name.startswith(prefix)}
        need(len(expected) == 153 and phase.file_inventory(folder) == set(expected), 'Identical complete source supplement required')
        for name, digest in expected.items(): need(sha(reader.read_bytes(str(folder/name))) == digest, 'Source supplement changed')
        supplements.append({'case_id': 'Case%02d' % i, 'directory': str(folder), 'files': expected})
    instructions = root / 'business-quality-tools/MATCHER-INSTRUCTIONS-v1.md'
    need(sha(instructions.read_bytes()) == 'b487d8b2227f0ea0aae454b579fbe8d355ba8c28fe05b5b45f80d633b70f0080', 'Prospective matcher policy changed')
    out = root / 'cache/business/blind-quality/matcher-input-v2' / a.id
    need(not out.exists(), 'Fresh matcher preparation required'); out.mkdir(parents=True)
    def save(path, value):
        raw = (projection.json_text(value, sort_keys=True, indent=2)+'\n').encode()
        with path.open('xb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        path.chmod(0o444); return ref(path)
    # The verified-role projections contain no pair times or assignment. The
    # original barrier index refs remain operator-only, outside the new input.
    verified_ref = save(out/'RECORD-BARRIERS.json', {'version': 1, 'cause': disclosed_barrier(phase, cause_verified), 'alarm': disclosed_barrier(phase, alarm_verified)})
    index = {'version': 1, 'kind': 'neutral-all15-correspondence-input', 'verified_record_barriers': verified_ref,
             'groups': groups, 'source_supplements': supplements, 'instructions': ref(instructions),
             'scope': 'Original anonymous source/contracts/native/PNGs and both sealed cause/alarm judgments. No map, costs, tool identity or editable subject source.'}
    index_ref = save(out/'INDEX.json', index)
    output = root / 'cache/business/blind-quality/correspondence' / a.id
    need(not output.exists(), 'Fresh independent correspondence output required')
    prompt = ('You are a fresh independent anonymous correspondence/adjudication reviewer. No prior worker, root, source-author or judge context is provided.\n'
              'Read the prospective instructions at '+str(instructions)+' (SHA '+sha(instructions.read_bytes())+').\n'
              'Your complete neutral input index is '+str(out/'INDEX.json')+' (SHA '+index_ref['sha256']+'). Verify its pinned record projections and every supplied input seal/member before use.\n'
              'Allowed reads are this index, RECORD-BARRIERS.json, the listed exact base/alarm packets, each listed judge cause/alarm output (including listed earlier original causes), and the five anonymous source-supplement directories only. Listed barrier refs establish records; do not open operator-parent index/episode files or clocks.\n'
              'Write only '+str(output)+'. Follow the frozen correspondence schema. Output correspondence.json, actual-only source/image consensus for ALL15 groups and a complete inspection/disagreement ledger. Preserve original unknowns, false/true product-defect claims, positive validation claims, source versions, exact document/pointer and visibility from neutral manifests. Worker detection/attempts require original worker-public evidence. Do not infer source values or product truth from declarations/statuses.\n'
              'Every source consensus row must retain family public/private, platform, original claim ID, observed Boolean/null, original actual implementation citations and original judgment refs. Every image consensus must retain exact catalog/observation hashes, original review IDs and frame indices. Unsupported citations/frame methods remain explicit, without fabricating replacements.\n'
              'Do not access map/treatment identity, cost, SDK, editable production roots, other operator parents, or change original grades/contracts/source. Do not spawn subagents or run native/build tools. Deduplicate only with positive raw evidence; preserve disagreements and unresolved causes.\n'
              'Seal every regular output readonly in SEAL.json kind independent-anonymous-correspondence-seal with exact relative_file:SHA inventory. Return only seal path/SHA and coverage, no quality findings to coordinator before this seal.\n')
    with (out/'PROMPT.txt').open('xb') as stream: stream.write(prompt.encode())
    (out/'PROMPT.txt').chmod(0o444)
    start = {'version': 1, 'kind': 'independent-anonymous-correspondence-start', 'index': index_ref,
             'prompt': ref(out/'PROMPT.txt'), 'instructions': ref(instructions),
             'operator_barriers': {'cause': cause_ref, 'alarm': alarm_ref}, 'quality_adjudicated': False,
             'mapping_revealed': False, 'output': str(output)}
    sys.path.insert(0, str(root/'business-quality-tools'))
    need(sha((root/'business-quality-tools/quality_clock.py').read_bytes()) ==
         '8a91e9d25574483b7c3275350c0b04b90cdb8f6cba5b91da041968a0a5e5a45c', 'Frozen shared clock differs')
    import quality_clock
    start.update(quality_clock.point('started'))
    start_ref = save(out/'START.json', start)
    print(json.dumps({'start': start_ref, 'prompt': ref(out/'PROMPT.txt'), 'output': str(output), 'groups': len(groups)}))


if __name__ == '__main__': main()
