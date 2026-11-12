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
import sys


def sha(raw): return hashlib.sha256(raw).hexdigest()
def need(ok, why):
    if not ok: raise ValueError(why)


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
    def verify_packet(reference, group, kind):
        value = phase.original(reader, reference); folder = Path(reference['path']).parent
        need(value.get('kind') == kind and value.get('anonymous_group') == group
             and type(value.get('version')) is int and value['version'] == 1,
             'Exact anonymous input kind/group required')
        need(phase.file_inventory(reader.directory(str(folder))) == set(value['files']) | {'SEAL.json'}, 'Input members differ')
        for name, expected in value['files'].items():
            phase.safe_member(name); need(sha(reader.read_bytes(str(folder/name))) == expected, 'Input bytes differ')
        return reference
    cause_rows = {x['group']: x for x in cause['groups']}
    for row in alarm['groups']:
        group = row['group']; original = cause_rows[group]
        base_refs = [reference for reference in original['inputs']
                     if phase.original(reader, reference).get('kind') == 'anonymous-fixed-version-input-seal']
        alarm_refs = [reference for reference in row['inputs']
                      if phase.original(reader, reference).get('kind') == 'anonymous-alarm-material-seal']
        need(len(base_refs) == len(alarm_refs) == 1, 'Exactly one original base and alarm packet required')
        base_ref = verify_packet(base_refs[0], group, 'anonymous-fixed-version-input-seal')
        alarm_packet_ref = verify_packet(alarm_refs[0], group, 'anonymous-alarm-material-seal')
        judges = {}
        for judge in ['J1', 'J2']:
            current = original['seals'][judge]; historical = []
            first = Path(current['path']).parents[1] / 'cause/SEAL.json'
            if str(first) != current['path'] and first.is_file():
                earlier = ref(first); phase.verify_role_seal(reader, earlier, group, judge, 'cause'); historical.append(earlier)
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
    out = root / 'cache/business/blind-quality/matcher-input' / a.id
    need(not out.exists(), 'Fresh matcher preparation required'); out.mkdir(parents=True)
    def save(path, value):
        raw = (projection.json_text(value, sort_keys=True, indent=2)+'\n').encode()
        with path.open('xb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        path.chmod(0o444); return ref(path)
    # The verified-role projections contain no pair times or assignment. The
    # original barrier index refs remain operator-only, outside the new input.
    verified_ref = save(out/'RECORD-BARRIERS.json', {'version': 1, 'cause': cause_verified, 'alarm': alarm_verified})
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
