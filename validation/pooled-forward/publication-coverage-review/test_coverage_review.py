"""Independent bounded synthetic applicability proofs; no actual study input."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import coverage_registry_v2 as revised

HERE = Path(__file__).resolve().parent
OBSERVATIONS = []


def module(name, filename, expected):
    path = HERE/'vendor'/filename
    if revised.sha(path.read_bytes()) != expected:
        raise ValueError('Frozen review source pin differs')
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


original = module('frozen_coverage_registry', 'coverage_registry.py', '75e5018b4974c4f9b62a251b9ccefcdd2ddb7d6569fe0a93177666746942ad69')
metric = module('frozen_metric_rules_v2', 'metric_rules_v2.py', '9d2bc0eb825eefb0b69f9de1668249dfa00bf53ba6cb3226dbed16d97f5a033f')


def fixture():
    tasks = ['synthetic_task_'+str(i) for i in range(1, 6)]
    cells = []
    for task in tasks:
        for platform in ['ios', 'android']:
            for family in ['public', 'private']:
                for state, kind, rule in [('ready', 'control', 'enabled'), ('after', 'event', 'callback')]:
                    cells.append(dict(task=task, platform=platform, family=family, state=state, rule_id=rule,
                                      kind=kind, disposition='required', assertion_id=state+'/'+rule))
                    cells.append(dict(task=task, platform=platform, family=family, state=state,
                                      rule_id='computed-font', kind='text_layout', disposition='N/A'))
                for rule in ['production-api', 'thin-bridge', 'production-placement']:
                    cells.append(dict(task=task, platform=platform, family=family, state='source-boundary',
                                      rule_id=rule, kind='source', disposition='required-source-review', actual='unassessed'))
    evidence = [{'path': '/synthetic/original/SEAL.sha256', 'sha256': '1'*64},
                {'path': '/synthetic/original/MASTER-DENOMINATOR.json', 'sha256': '2'*64},
                {'path': '/synthetic/original/PUBLIC-PACKETS.json', 'sha256': '3'*64}]
    return tasks, cells, evidence


def original_observation(name, changed, result):
    OBSERVATIONS.append({'control': name, 'synthetic_change': changed, 'original_result': result,
                         'frozen_original_sha256': '75e5018b4974c4f9b62a251b9ccefcdd2ddb7d6569fe0a93177666746942ad69'})


def write_fixture(root, *, malformed_json=False, omit_seal_entry=False):
    tasks, cells, _ = fixture()
    counts = {d: sum(c['disposition'] == d for c in cells) for d in revised.DISPOSITIONS}
    denominator = {'version': 1, 'cells': cells, 'counts': counts}
    packets = {'version': 1, 'tasks': [{'task': t, 'public_packet': 'public/tasks/'+t} for t in tasks]}
    d = json.dumps(denominator, sort_keys=True).encode()
    if malformed_json:
        d = b'{"version":2,"version":1,'+d[1:]
    names = ['MASTER-DENOMINATOR.json', 'PUBLIC-PACKETS.json', 'SEAL.sha256']
    paths = [root/n for n in names]
    raws = [d, json.dumps(packets, sort_keys=True).encode()]
    for path, raw in zip(paths[:2], raws):
        path.write_bytes(raw)
    lines = [revised.sha(raw)+'  '+path.name for path, raw in zip(paths[:2], raws)]
    if omit_seal_entry:
        lines.pop(0)
    paths[2].write_text('\n'.join(lines)+'\n')
    return paths, [revised.sha(p.read_bytes()) for p in paths]


def cli(paths, pins, output, script='coverage_registry_v2.py'):
    script_path = HERE/script if '/' not in script else HERE/script
    command = [sys.executable, '-B', str(script_path)]
    for name, path, pin in zip(['denominator', 'public-packets', 'seal'], paths, pins):
        command += ['--'+name, str(path), '--'+name+'-sha256', pin]
    command += ['--output', str(output)]
    return subprocess.run(command, capture_output=True, text=True)


class ProjectionReview(unittest.TestCase):
    def test_01_exact_projection_roundtrip_both_platforms_families_and_states(self):
        tasks, cells, evidence = fixture()
        before = copy.deepcopy((tasks, cells, evidence))
        result = revised.projection(cells, tasks, evidence)
        self.assertEqual((tasks, cells, evidence), before)
        self.assertEqual(len(result['projection_identity_metadata']), len(cells))
        for number, task in enumerate(tasks, 1):
            rows = result['coverage_denominators']['Case%02d' % number]
            self.assertEqual(rows['X'], rows['Y'])
            expected = set()
            for c in cells:
                if c['task'] != task:
                    continue
                source = c['kind'] == 'source'
                name = c['family']+'/'+c['state']+'/'+c['rule_id'] if source else c['state']+'/'+c['rule_id']
                state = c['family']+'/'+c['state'] if source else c['state']
                family = 'source' if source else c['family']+'_native_image'
                expected.add((c['platform'], state, family, c['disposition'] == 'N/A', name))
            projected = {(r['platform'], r['state'], r['family'], na, name) for r in rows['X']
                         for na, field in [(False, 'applicable_ids'), (True, 'not_applicable_ids')] for name in r[field]}
            self.assertEqual(projected, expected)
            self.assertEqual(len(projected), sum(c['task'] == task for c in cells))
            self.assertTrue(all(set(r) == {'platform', 'state', 'family', 'applicable_ids', 'not_applicable_ids', 'evidence'} for r in rows['X']))

    def test_02_required_missing_assertion_id_is_original_admission(self):
        tasks, cells, evidence = fixture()
        del cells[0]['assertion_id']
        old = original.registry(cells, tasks, evidence)
        self.assertTrue(any('ready/enabled' in r['applicable_ids'] for r in old['Case01']['X']))
        original_observation(self.id(), {'cell_index': 0, 'delete': 'assertion_id'}, 'admitted and synthesized required ID ready/enabled')
        with self.assertRaisesRegex(ValueError, 'exact original assertion_id'):
            revised.registry(cells, tasks, evidence)

    def test_03_na_without_assertion_is_labeled_mechanical_not_a_pass(self):
        tasks, cells, evidence = fixture()
        result = revised.projection(cells, tasks, evidence)
        na = [x for x in result['projection_identity_metadata'] if x['disposition'] == 'N/A']
        self.assertTrue(na)
        self.assertTrue(all(x['identity_basis'] == 'mechanical-N/A-state/rule-identity' for x in na))
        self.assertFalse(any('passed_ids' in row for case in result['coverage_denominators'].values() for row in case['X']))

    def test_04_wrong_required_or_na_explicit_id_rejected(self):
        for position in [0, 1]:
            tasks, cells, evidence = fixture()
            cells[position]['assertion_id'] = 'made-up/id'
            with self.assertRaises(ValueError):
                revised.registry(cells, tasks, evidence)

    def test_05_source_composites_preserve_all_three_duties_and_families(self):
        tasks, cells, evidence = fixture()
        result = revised.projection(cells, tasks, evidence)
        source = [x for x in result['projection_identity_metadata'] if x['kind'] == 'source']
        self.assertEqual(len(source), 60)
        for row in source:
            self.assertEqual(row['projected_id'], row['family']+'/'+row['state']+'/'+row['rule_id'])
            self.assertEqual(row['identity_basis'], 'explicit-source-family/state/rule-composite')

    def test_06_unknown_kind_original_admitted(self):
        tasks, cells, evidence = fixture()
        cells[0]['kind'] = 'misspelled-control'
        original.registry(cells, tasks, evidence)
        original_observation(self.id(), {'cell_index': 0, 'kind': cells[0]['kind']}, 'admitted as native/image')
        with self.assertRaisesRegex(ValueError, 'Unknown original denominator kind'):
            revised.registry(cells, tasks, evidence)

    def test_07_frozen_generator_native_kinds_supported(self):
        for kind in revised.NATIVE_KINDS:
            tasks, cells, evidence = fixture()
            cells[0]['kind'] = kind
            revised.registry(cells, tasks, evidence)

    def test_08_missing_source_public_family_original_admitted(self):
        tasks, cells, evidence = fixture()
        cells = [c for c in cells if not (c['task'] == tasks[0] and c['platform'] == 'ios' and c['family'] == 'public' and c['kind'] == 'source')]
        original.registry(cells, tasks, evidence)
        original_observation(self.id(), {'delete_scope': [tasks[0], 'ios', 'public', 'source']}, 'admitted because private source masks missing public source family')
        with self.assertRaisesRegex(ValueError, 'public-private family'):
            revised.registry(cells, tasks, evidence)

    def test_09_duplicate_cells_platform_family_and_tasks_rejected(self):
        tasks, cells, evidence = fixture()
        for changed in [cells+[cells[0]], [c for c in cells if c['platform'] != 'ios'], [c for c in cells if c['family'] != 'public']]:
            with self.assertRaises(ValueError):
                revised.registry(changed, tasks, evidence)
        with self.assertRaises(ValueError):
            revised.registry(cells, tasks[:-1]+tasks[:1], evidence)

    def test_10_source_cannot_be_na_native_or_carry_ignored_assertion(self):
        for disposition in ['required', 'N/A']:
            tasks, cells, evidence = fixture()
            next(c for c in cells if c['kind'] == 'source')['disposition'] = disposition
            with self.assertRaises(ValueError):
                revised.registry(cells, tasks, evidence)
        tasks, cells, evidence = fixture()
        next(c for c in cells if c['kind'] == 'source')['assertion_id'] = 'unrelated/assertion'
        original.registry(cells, tasks, evidence)
        original_observation(self.id(), {'source_assertion_id': 'unrelated/assertion'}, 'admitted; conflicting field ignored')
        with self.assertRaisesRegex(ValueError, 'discard an assertion_id'):
            revised.registry(cells, tasks, evidence)

    def test_11_output_independent_of_input_and_anonymous_sibling(self):
        tasks, cells, evidence = fixture()
        old = original.registry(cells, tasks, evidence)
        old['Case01']['X'][0]['applicable_ids'].append('mutated')
        self.assertIn('mutated', old['Case01']['Y'][0]['applicable_ids'])
        old['Case01']['X'][0]['evidence'][0]['path'] = '/mutated'
        self.assertEqual(evidence[0]['path'], '/mutated')
        original_observation(self.id(), {'mutate': 'X row ID then output evidence path'}, 'Y row and caller evidence both mutated through returned aliases')
        tasks, cells, evidence = fixture()
        before = copy.deepcopy((tasks, cells, evidence))
        result = revised.registry(cells, tasks, evidence)
        result['Case01']['X'][0]['applicable_ids'].append('mutated')
        result['Case01']['X'][0]['evidence'][0]['path'] = '/mutated'
        self.assertNotIn('mutated', result['Case01']['Y'][0]['applicable_ids'])
        self.assertEqual((tasks, cells, evidence), before)
        self.assertNotEqual(result['Case01']['X'][0]['evidence'], result['Case01']['X'][1]['evidence'])

    def test_12_evidence_exact_pins_and_identifiers_required(self):
        tasks, cells, evidence = fixture()
        for bad in [[], ['frozen'], [{'path': 'relative', 'sha256': 'a'*64}], [{'path': '/original', 'sha256': 'not-a-sha'}]]:
            with self.assertRaises(ValueError):
                revised.registry(cells, tasks, bad)
        for key in ['state', 'rule_id']:
            changed = copy.deepcopy(cells)
            changed[0][key] = 'ambiguous/part'
            with self.assertRaises(ValueError):
                revised.registry(changed, tasks, evidence)

    def test_13_individual_omission_is_external_seal_boundary_not_oracle(self):
        tasks, cells, evidence = fixture()
        removed = cells.pop(0)
        result = revised.registry(cells, tasks, evidence)
        self.assertFalse(any(removed['assertion_id'] in r['applicable_ids'] for r in result['Case01']['X']
                             if r['platform'] == removed['platform'] and r['family'] == removed['family']+'_native_image' and r['state'] == removed['state']))
        # No invented replacement, inferred pass, or requirement regenerated from results.

    def test_14_metric_rows_compatible_and_unknowns_preserved(self):
        tasks, cells, evidence = fixture()
        registry = revised.registry(cells, tasks, evidence)['Case01']['X']
        rows = [{'platform': r['platform'], 'state': r['state'], 'family': r['family'],
                 'frozen_applicable_ids': r['applicable_ids'], 'passed_ids': [], 'failed_ids': [],
                 'unassessed_ids': r['applicable_ids'], 'not_applicable_ids': r['not_applicable_ids'], 'denominator_evidence': r['evidence']} for r in registry]
        result = metric.coverage({'mandatory_coverage': rows}, registry)
        self.assertEqual(result['counts'], {'passed': 0, 'failed': 0, 'unassessed': 20, 'applicable': 20, 'not_applicable': 8})
        self.assertFalse(result['complete'])
        rows[0]['passed_ids'] = rows[0]['not_applicable_ids'][:]
        with self.assertRaisesRegex(ValueError, 'N/A cannot become pass'):
            metric.coverage({'mandatory_coverage': rows}, registry)


class SealedCLIReview(unittest.TestCase):
    def owned(self):
        base = HERE/'HOST'
        base.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(prefix='generic-sealed-', dir=base)

    def test_15_cli_exact_pins_inputs_unchanged_and_output_readonly(self):
        with self.owned() as name:
            paths, pins = write_fixture(Path(name))
            before = [p.read_bytes() for p in paths]
            out = Path(name)/'projection.json'
            result = cli(paths, pins, out)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, [p.read_bytes() for p in paths])
            projected = json.loads(out.read_bytes())
            self.assertEqual(projected['version'], 2)
            self.assertEqual(len(projected['projection_identity_metadata']), 140)
            self.assertEqual(out.stat().st_mode & 0o222, 0)
            self.assertTrue(all(r['evidence'][0]['sha256'] == pins[2] for r in projected['coverage_denominators']['Case01']['X']))

    def test_16_changed_external_input_and_seal_pins_rejected(self):
        with self.owned() as name:
            paths, pins = write_fixture(Path(name))
            for index in [0, 1, 2]:
                changed = list(pins)
                changed[index] = '0'*64
                result = cli(paths, changed, Path(name)/('out'+str(index)+'.json'))
                self.assertNotEqual(result.returncode, 0)
            paths[0].write_bytes(paths[0].read_bytes()+b' ')
            self.assertNotEqual(cli(paths, pins, Path(name)/'changed.json').returncode, 0)

    def test_17_missing_inventory_input_and_outside_parent_rejected(self):
        with self.owned() as name:
            paths, pins = write_fixture(Path(name), omit_seal_entry=True)
            self.assertNotEqual(cli(paths, pins, Path(name)/'missing.json').returncode, 0)
            sub = Path(name)/'elsewhere';sub.mkdir()
            outside = sub/paths[0].name;outside.write_bytes(paths[0].read_bytes())
            changed = [outside, paths[1], paths[2]]
            self.assertNotEqual(cli(changed, pins, Path(name)/'outside.json').returncode, 0)

    def test_18_duplicate_json_original_cli_admitted_revision_refuses(self):
        with self.owned() as name:
            paths, pins = write_fixture(Path(name), malformed_json=True)
            old = cli(paths, pins, Path(name)/'original.json', 'vendor/coverage_registry.py')
            self.assertEqual(old.returncode, 0, old.stderr)
            new = cli(paths, pins, Path(name)/'revised.json')
            self.assertNotEqual(new.returncode, 0)
            self.assertIn('Duplicate original JSON key', new.stderr)
            original_observation(self.id(), {'denominator_prefix': '{"version":2,"version":1,...}', 'input_sha256': pins[0]}, 'original CLI admitted duplicate JSON identity keys')

    def test_19_duplicate_or_noncanonical_seal_and_count_mismatch_rejected(self):
        for raw in [b'a'*64+b'  ../MASTER.json\n', b'a'*64+b'  same\n'+b'b'*64+b'  same\n', b'X'*64+b'  valid\n']:
            with self.assertRaises(ValueError):
                revised.seal_manifest(raw)
        with self.owned() as name:
            paths, pins = write_fixture(Path(name))
            data = json.loads(paths[0].read_bytes());data['counts']['required'] += 1
            paths[0].write_text(json.dumps(data));pins[0] = revised.sha(paths[0].read_bytes())
            paths[2].write_text(pins[0]+'  '+paths[0].name+'\n'+pins[1]+'  '+paths[1].name+'\n');pins[2] = revised.sha(paths[2].read_bytes())
            result = cli(paths, pins, Path(name)/'counts.json')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('count metadata differs', result.stderr)

    def test_20_output_overwrite_refused(self):
        with self.owned() as name:
            paths, pins = write_fixture(Path(name))
            out = Path(name)/'projection.json'
            out.write_bytes(b'preserve me')
            result = cli(paths, pins, out)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(out.read_bytes(), b'preserve me')


if __name__ == '__main__':
    unittest.main(verbosity=2)
