#!/usr/bin/env python3
"""Independent synthetic behavioral controls; every case is retained on disk.

Run one revision per fresh process. No business inputs, SDK, network or Git.
"""
import argparse
import copy
import base64
from decimal import Decimal
import hashlib
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import traceback
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent.parent
GROUPS = {f'Case0{i}-{version}' for i in range(1, 6) for version in ('I', 'X', 'Y')}
RUN = None
projection = packet = barriers = None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True,
                              default=lambda v: {'python_type': type(v).__name__, 'value': str(v)}) + '\n')


class ScopedReader:
    """Synthetic equivalent of the frozen live reader's no-follow file access.

    directory() checks the selected directory, as LiveReader does, leaving
    member inventory validation to phase_barriers. Every attempted read is saved.
    """
    def __init__(self, root):
        self.root = root
        self.reads = []

    def checked(self, value):
        path = Path(value)
        if not path.is_absolute() or str(PurePosixPath(str(path))) != str(value) or '..' in path.parts:
            raise ValueError('Synthetic reader requires a canonical absolute path')
        if not path.is_relative_to(self.root):
            raise ValueError('Synthetic reader refuses access outside the retained case')
        for component in (path, *path.parents):
            if component.is_symlink():
                raise ValueError('Synthetic reader rejects a symlink path')
            if component == self.root:
                break
        return path

    def read_bytes(self, value):
        self.reads.append(str(value))
        path = self.checked(value)
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError('Synthetic reader requires a regular file')
        return path.read_bytes()

    def read_json(self, value):
        return json.loads(self.read_bytes(value))

    def directory(self, value):
        path = self.checked(value)
        if not path.is_dir():
            raise ValueError('Synthetic reader requires a directory')
        return path


class ThirtyRoles:
    """Self-contained synthetic thirty-role fixture, independent of author tests."""
    def __init__(self, root, phase='cause'):
        self.root = root
        self.phase = phase
        self.reader = ScopedReader(root)
        self.rows = []
        for group in sorted(GROUPS):
            seals = {}
            for judge in ('J1', 'J2'):
                folder = root / phase / group / judge
                grade = self.put(folder / 'grade.json', {
                    'version': 1, 'kind': 'independent-blind-' + phase + '-grade',
                    'anonymous_group': group, 'judge_id': judge,
                    'observations': [{'status': 'F'}, {'status': 'P'}, {'status': 'U'}],
                    'scope': 'Entirely synthetic record; no product finding'})
                seals[judge] = self.put(folder / 'SEAL.json', {
                    'version': 1, 'kind': 'independent-blind-' + phase + '-grade-seal',
                    'anonymous_group': group, 'judge_id': judge,
                    'files': {'grade.json': grade['sha256']}})
            contract = self.put(root / phase / group / 'input/contract.json', {'synthetic': True})
            input_seal = self.put(root / phase / group / 'input/SEAL.json', {
                'version': 1, 'kind': 'anonymous-fixed-version-input-seal',
                'anonymous_group': group, 'files': {'contract.json': contract['sha256']}})
            end = self.put(root / phase / group / 'episode/END.json', {
                'anonymous_group': group, 'grade_seals': seals})
            self.rows.append({
                'group': group,
                'actors': {j: '/root/synthetic_' + group + '_' + j for j in ('J1', 'J2')},
                'seals': seals, 'inputs': [input_seal], 'episode_end': end,
                'fork_turns': 'none', 'model_override': None})

    def put(self, path, value=None, *, raw=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        body = encoded(value) if raw is None else raw
        path.write_bytes(body)
        return {'path': str(path), 'sha256': sha(body)}

    def index(self, *, rows=None, raw=None, predecessor=None, version=1):
        value = {
            'version': version, 'kind': 'global-independent-' + self.phase + '-grade-barrier',
            'groups': self.rows if rows is None else rows,
            'review_record_barrier_closed': True, 'product_quality_verified': False,
            'scope': 'Synthetic role-record barrier only'}
        if predecessor is not None:
            value['first_cause_barrier'] = predecessor
        return self.put(self.root / self.phase / 'INDEX.json', value, raw=raw)

    def spec(self, *, report=None, raw=None, method='bounded-json'):
        if report is None and raw is None:
            report = {'assertions': [
                {'id': 'positive', 'status': 'P', 'expected': True, 'actual': True},
                {'id': 'alarm', 'status': 'F', 'expected': 48, 'actual': 44},
                {'id': 'limit', 'status': 'U', 'expected': None, 'actual': None}],
                'issues': [{'message': 'Synthetic measurement limitation', 'status': 'U'}],
                'worker_claims': [{'statement': 'Synthetic all-complete claim', 'status': 'claimed'}]}
        original = self.put(self.root / 'original/report.json', report, raw=raw)
        instructions = self.put(self.root / 'fixed/instructions.md', raw=b'Synthetic instructions. Assess complete rows.\n')
        template = self.put(self.root / 'fixed/template.json', {'version': 1, 'anonymous_group': None})
        return {
            'version': 1, 'kind': 'explicit-anonymous-alarm-material-spec',
            'anonymous_group': 'Case01-X', 'first_cause_barrier': self.index(),
            'documents': [{'original': original, 'anonymous_relative': 'reports/report.json',
                           'method': method,
                           'projection': {'omit_top_level': [], 'replacements': [], 'rewrite_pointers': []}}],
            'anonymous_description': {'anonymous_group': 'Case01-X', 'material': ['reports/report.json']},
            'instructions': instructions, 'grade_template': template}


class ReviewCase(unittest.TestCase):
    def setUp(self):
        self.case = RUN / 'cases' / self._testMethodName
        self.case.mkdir(parents=True)
        self.observations = []
        self.fixture = None

    def tearDown(self):
        if self.fixture:
            dump(self.case / 'READS.json', self.fixture.reader.reads)
        dump(self.case / 'OBSERVATIONS.json', self.observations)

    def observe(self, label, value):
        self.observations.append({'label': label, 'value': value})

    def input(self, value, name='INPUT.json'):
        dump(self.case / name, value)
        return value

    def roles(self, phase='cause'):
        self.fixture = ThirtyRoles(self.case / 'synthetic', phase)
        return self.fixture

    def rejects(self, callback, label='fail-closed'):
        try:
            result = callback()
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
            self.observe(label, {'rejected': True, 'error': type(error).__name__, 'message': str(error)})
            return error
        self.observe(label, {'rejected': False, 'returned': result})
        self.fail('Accepted material that must fail closed: ' + label)

    def build(self, fixture, spec, *, output=None, record=None):
        self.input(spec, 'SPEC-INPUT.json')
        return packet.build(fixture.reader, spec, output or self.case / 'anonymous',
                            record or self.case / 'operator')

    def gate_rejects(self, mutate):
        f = self.roles(); spec = f.spec(); mutate(f, spec)
        alarm_paths = {item['original']['path'] for item in spec['documents']}
        self.rejects(lambda: self.build(f, spec), 'incomplete/malformed cause gate')
        self.assertFalse(alarm_paths.intersection(f.reader.reads), 'Alarm source read before cause gate')
        self.assertFalse((self.case / 'anonymous/SEAL.json').exists())


class ProjectionControls(ReviewCase):
    def test_projection_01_legitimate_mixed_reports_preserve_rows_and_native_values(self):
        value = self.input({
            'arm': 'B', 'operations': {'seconds': 9, 'execution_api': 'synthetic'},
            'assertions': [
                {'id': 'a', 'status': 'F', 'expected': 56, 'actual': 44,
                 'reason': 'See /Users/rex/synthetic/captures/state.png; candidate-v13.9 reported this claim'},
                {'id': 'b', 'status': 'P', 'expected': '#102030', 'actual': '#102030'},
                {'id': 'c', 'status': 'U', 'expected': False, 'actual': None}],
            'native': {'issues': [{'status': 'U', 'message': 'Observation is partial'}],
                       'order': [3, 1, 2], 'text': 'A label', 'padding': [2, 4]},
            'routed_work': [{'responsibility': 'pending', 'admission': False}],
            'worker_claims': [{'statement': 'Synthetic completion claim', 'status': 'claim'}]})
        before = copy.deepcopy(value)
        result, ledger = projection.project(value, omit_top_level=['arm', 'operations'],
            replacements=[{'original': '/Users/rex/synthetic/captures', 'anonymous': 'observations/native'},
                          {'original': 'candidate-v13.9', 'anonymous': 'frozen-tool'}],
            rewrite_pointers=['/assertions/0/reason'])
        self.observe('projected', result); self.observe('ledger', ledger)
        expected = copy.deepcopy(before); del expected['arm']; del expected['operations']
        expected['assertions'][0]['reason'] = 'See observations/native/state.png; frozen-tool reported this claim'
        self.assertEqual(result, expected)
        self.assertEqual(value, before)
        self.assertEqual(ledger['identity_metadata_changes'][0]['original'], before['assertions'][0]['reason'])

    def test_projection_02_expected_ancestor_cannot_be_rewritten(self):
        value = self.input({'expected': {'path': '/Users/rex/synthetic/expected.swift'}})
        self.rejects(lambda: projection.project(value,
            replacements=[{'original': '/Users/rex/synthetic', 'anonymous': 'own-source'}],
            rewrite_pointers=['/expected/path']), 'expected subtree path')

    def test_projection_03_actual_ancestor_cannot_be_rewritten(self):
        value = self.input({'assertions': [{'actual': {'reason': 'candidate-v13.9'}}]})
        self.rejects(lambda: projection.project(value,
            replacements=[{'original': 'candidate-v13.9', 'anonymous': 'frozen-tool'}],
            rewrite_pointers=['/assertions/0/actual/reason']), 'measured subtree narrative')

    def test_projection_04_rendered_ancestor_cannot_be_rewritten(self):
        value = self.input({'native': {'rendered': {'path': '/Users/rex/synthetic/visible-label'}}})
        self.rejects(lambda: projection.project(value,
            replacements=[{'original': '/Users/rex/synthetic', 'anonymous': 'own'}],
            rewrite_pointers=['/native/rendered/path']), 'rendered subtree path')

    def test_projection_05_factual_operations_cannot_be_omitted(self):
        value = self.input({'operations': [{'operation': 'submit', 'status': 'F', 'expected': 1, 'actual': 0}],
                            'assertions': [{'status': 'P'}]})
        self.rejects(lambda: projection.project(value, omit_top_level=['operations']), 'substantive operation alarm')

    def test_projection_06_factual_timing_cannot_be_omitted(self):
        value = self.input({'timing': {'expected': 100, 'actual': 800, 'status': 'F'}})
        self.rejects(lambda: projection.project(value, omit_top_level=['timing']), 'substantive timing measurement')

    def test_projection_07_declared_execution_metadata_omission_is_supported(self):
        value = self.input({'operations': {'seconds': 12, 'count': 4},
                            'timing': {'wall_seconds': 12}, 'tool_version': 'candidate-v13.9',
                            'issues': [{'status': 'U', 'reason': 'Synthetic collector limitation'}]})
        result, ledger = projection.project(value, omit_top_level=['operations', 'timing', 'tool_version'])
        self.observe('projected', result)
        self.assertEqual(result, {'issues': value['issues']})
        self.assertEqual(set(ledger['omitted_top_level']), {'operations', 'timing', 'tool_version'})

    def test_projection_08_precise_decimal_measurement_survives_parse(self):
        raw = b'{"expected":9007199254740993.0,"actual":0.12345678901234567890123456789}'
        (self.case / 'INPUT.json').write_bytes(raw)
        value = projection.strict_json(raw); result, _ = projection.project(value)
        self.observe('parsed/projected', result)
        self.assertEqual(Decimal(str(result['expected'])), Decimal('9007199254740993.0'))
        self.assertEqual(Decimal(str(result['actual'])), Decimal('0.12345678901234567890123456789'))

    def test_projection_09_tiny_finite_measurement_does_not_become_zero(self):
        raw = b'{"actual":1e-999,"expected":2e-999}'
        (self.case / 'INPUT.json').write_bytes(raw)
        value = projection.strict_json(raw); result, _ = projection.project(value)
        self.observe('parsed/projected', result)
        self.assertEqual(Decimal(str(result['actual'])), Decimal('1e-999'))
        self.assertEqual(Decimal(str(result['expected'])), Decimal('2e-999'))

    def test_projection_10_duplicate_nonfinite_and_invalid_json_fail_closed(self):
        for index, raw in enumerate([b'{"a":1,"a":2}', b'{"outer":{"x":0,"x":1}}',
                                     b'{"actual":NaN}', b'{"actual":Infinity}', b'{"actual":-Infinity}',
                                     b'{"a":1} trailing']):
            (self.case / f'INPUT-{index}.json').write_bytes(raw)
            self.rejects(lambda raw=raw: projection.strict_json(raw), f'invalid JSON {index}')

    def test_projection_11_pointer_escaping_is_exact_and_missing_pointers_fail(self):
        value = self.input({'a/b~c': {'reason': 'From /Users/rex/synthetic/report.json'}, 'actual': 1})
        result, _ = projection.project(value,
            replacements=[{'original': '/Users/rex/synthetic', 'anonymous': 'reports'}],
            rewrite_pointers=['/a~1b~0c/reason'])
        self.observe('projected', result)
        self.assertEqual(result['a/b~c']['reason'], 'From reports/report.json')
        for pointers in (['/missing'], ['/actual', '/actual'], ['/a~2b/reason']):
            self.rejects(lambda pointers=pointers: projection.project({'actual': 1}, rewrite_pointers=pointers), str(pointers))

    def test_projection_12_path_prefix_collision_cannot_change_another_path(self):
        value = self.input({'source_path': '/Users/rex/synthetic-repository/Main.swift'})
        self.rejects(lambda: projection.project(value,
            replacements=[{'original': '/Users/rex/synthetic', 'anonymous': 'own'}],
            rewrite_pointers=['/source_path']), 'different recorded path sharing a prefix')

    def test_projection_13_tool_token_prefix_collision_cannot_change_another_name(self):
        value = self.input({'reason': 'candidate-v13.90 reported this claim'})
        self.rejects(lambda: projection.project(value,
            replacements=[{'original': 'candidate-v13.9', 'anonymous': 'frozen-tool'}],
            rewrite_pointers=['/reason']), 'different tool token sharing a prefix')

    def test_projection_14_replacement_cannot_inject_control_text(self):
        value = self.input({'reason': 'candidate-v13.9 reported this claim'})
        self.rejects(lambda: projection.project(value,
            replacements=[{'original': 'candidate-v13.9', 'anonymous': 'own\nF: newly inserted claim'}],
            rewrite_pointers=['/reason']), 'control-character replacement')

    def test_projection_15_unsupported_factual_edits_and_unhandled_identity_fail(self):
        for value, options in [({'actual': 'candidate-v13.9'}, {
                'replacements': [{'original': 'candidate-v13.9', 'anonymous': 'frozen-tool'}], 'rewrite_pointers': ['/actual']}),
                ({'expected': '#fff'}, {'omit_top_level': ['expected']}),
                ({'reason': '/Users/rex/unlisted/report.json'}, {}),
                ({'actual': '#fff'}, {'replacements': [{'original': '#fff', 'anonymous': '#000'}]})]:
            self.input(value, f'INPUT-{len(self.observations)}.json')
            self.rejects(lambda value=value, options=options: projection.project(value, **options))

    def test_projection_16_unicode_paths_and_punctuation_keep_narrative_and_order(self):
        value = self.input({'notes': ['First: (/Users/rex/synthetic space/한국/frame.png).',
                                      'Then candidate-v13.9; preserve this F claim.'],
                            'assertions': [{'status': 'F', 'expected': '공백  x', 'actual': '공백 x'},
                                           {'status': 'U', 'actual': False}, {'status': 'P', 'actual': None}]})
        result, _ = projection.project(value,
            replacements=[{'original': '/Users/rex/synthetic space/한국', 'anonymous': 'observations/한국'},
                          {'original': 'candidate-v13.9', 'anonymous': 'frozen-tool'}],
            rewrite_pointers=['/notes/0', '/notes/1'])
        self.observe('projected', result)
        self.assertEqual(result['notes'], ['First: (observations/한국/frame.png).',
                                           'Then frozen-tool; preserve this F claim.'])
        self.assertEqual(result['assertions'], value['assertions'])


class PacketControls(ReviewCase):
    def test_packet_01_whole_reports_source_and_image_bytes_and_provenance_are_retained(self):
        f = self.roles(); spec = f.spec()
        source = f.put(f.root / 'original/Main.swift', raw=b'let syntheticValue = 44\n')
        image = f.put(f.root / 'original/frame.png', raw=base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='))
        spec['documents'].extend([
            {'original': source, 'anonymous_relative': 'source/Main.swift', 'method': 'copy'},
            {'original': image, 'anonymous_relative': 'observations/frame.png', 'method': 'copy'}])
        spec['anonymous_description']['material'].extend(['source/Main.swift', 'observations/frame.png'])
        summary = self.build(f, spec); self.observe('summary', summary)
        original = json.loads(Path(spec['documents'][0]['original']['path']).read_bytes())
        projected = json.loads((self.case / 'anonymous/reports/report.json').read_bytes())
        self.assertEqual(projected, original)
        self.assertEqual([r['status'] for r in projected['assertions']], ['P', 'F', 'U'])
        self.assertEqual((self.case / 'anonymous/source/Main.swift').read_bytes(), Path(source['path']).read_bytes())
        self.assertEqual((self.case / 'anonymous/observations/frame.png').read_bytes(), Path(image['path']).read_bytes())
        ledger = json.loads((self.case / 'operator/LEDGER.json').read_bytes())
        self.assertEqual(ledger['projections'][0]['original'], spec['documents'][0]['original'])
        self.assertFalse(summary['quality_judgment']); self.assertFalse(summary['mapping_revealed'])
        seal = json.loads((self.case / 'anonymous/SEAL.json').read_bytes())
        for name, expected in seal['files'].items():
            self.assertEqual(sha((self.case / 'anonymous' / name).read_bytes()), expected)
            self.assertEqual((self.case / 'anonymous' / name).stat().st_mode & 0o222, 0)
        self.assertEqual(set(seal['files']), {'reports/report.json', 'source/Main.swift', 'observations/frame.png',
                                             'PACKET.json', 'INSTRUCTIONS.md', 'GRADE-TEMPLATE.json'})

    def test_packet_02_finite_decimal_values_survive_end_to_end(self):
        f = self.roles(); raw = b'{"assertions":[{"status":"F","expected":9007199254740993.0,"actual":1e-999}]}'
        spec = f.spec(raw=raw)
        self.build(f, spec)
        actual = json.loads((self.case / 'anonymous/reports/report.json').read_bytes(), parse_float=Decimal)
        expected = json.loads(raw, parse_float=Decimal)
        self.observe('output', actual)
        self.assertEqual(actual, expected)

    def test_packet_03_identity_in_member_name_fails_closed(self):
        f = self.roles(); spec = f.spec()
        spec['documents'][0]['anonymous_relative'] = 'candidate-v13.9/report.json'
        self.rejects(lambda: self.build(f, spec), 'identity-bearing neutral member name')
        self.assertFalse((self.case / 'anonymous/SEAL.json').exists())

    def test_packet_04_escaped_identity_in_copy_json_fails_closed(self):
        f = self.roles(); spec = f.spec(raw=b'{"tool":"\\u0063andidate-v13.9","status":"F"}', method='copy')
        self.rejects(lambda: self.build(f, spec), 'JSON-escaped copied identity')
        self.assertFalse((self.case / 'anonymous/SEAL.json').exists())

    def test_packet_05_utf16_identity_in_copy_text_fails_closed(self):
        f = self.roles(); spec = f.spec(raw='{"tool":"candidate-v13.9","status":"F"}'.encode('utf-16'), method='copy')
        self.rejects(lambda: self.build(f, spec), 'UTF-16 copied identity')
        self.assertFalse((self.case / 'anonymous/SEAL.json').exists())

    def test_packet_06_operator_alias_cannot_enter_anonymous_output(self):
        f = self.roles(); spec = f.spec()
        output = self.case / 'anonymous'
        alias = self.case / 'alias'; alias.symlink_to(output, target_is_directory=True)
        self.rejects(lambda: self.build(f, spec, output=output, record=alias / 'operator'), 'operator symlink alias')
        self.assertFalse((output / 'SEAL.json').exists())

    def test_packet_07_operator_dotdot_alias_cannot_enter_anonymous_output(self):
        f = self.roles(); spec = f.spec()
        (self.case / 'other').mkdir()
        output = self.case / 'anonymous'
        record = self.case / 'other' / '..' / 'anonymous' / 'operator'
        self.rejects(lambda: self.build(f, spec, output=output, record=record), 'operator dotdot alias')
        self.assertFalse((output / 'SEAL.json').exists())

    def test_packet_08_changed_original_stays_failed_and_unsealed(self):
        f = self.roles(); spec = f.spec(); spec['documents'][0]['original']['sha256'] = '0' * 64
        self.rejects(lambda: self.build(f, spec), 'changed original bytes')
        self.assertTrue((self.case / 'operator/FAILED.json').is_file())
        self.assertTrue((self.case / 'operator/SPEC.json').is_file())
        self.assertFalse((self.case / 'anonymous/SEAL.json').exists())

    def test_packet_09_bad_pointer_stays_failed_and_unsealed(self):
        f = self.roles(); spec = f.spec()
        spec['documents'][0]['projection']['rewrite_pointers'] = ['/absent/path']
        self.rejects(lambda: self.build(f, spec), 'absent explicit pointer')
        self.assertTrue((self.case / 'operator/FAILED.json').is_file())
        self.assertFalse((self.case / 'anonymous/SEAL.json').exists())

    def test_packet_10_traversal_reserved_and_duplicate_members_fail_closed(self):
        for index, name in enumerate(['../escape.json', '/absolute.json', 'SEAL.json', 'PACKET.json', 'a\\b.json']):
            f = ThirtyRoles(self.case / f'variant-{index}/synthetic')
            spec = f.spec(); spec['documents'][0]['anonymous_relative'] = name
            self.rejects(lambda f=f, spec=spec, index=index: self.build(f, spec,
                output=self.case / f'variant-{index}/anonymous', record=self.case / f'variant-{index}/operator'), name)
        f = self.roles(); spec = f.spec(); spec['documents'].append(copy.deepcopy(spec['documents'][0]))
        self.rejects(lambda: self.build(f, spec), 'duplicate member')

    def test_packet_11_operator_seal_write_failure_leaves_no_anonymous_seal(self):
        f = self.roles(); spec = f.spec()
        actual_write = packet.write
        def failing_write(path, raw):
            if Path(path) == self.case / 'operator/SEAL.json':
                raise OSError('Synthetic operator-seal write failure')
            return actual_write(path, raw)
        with mock.patch.object(packet, 'write', side_effect=failing_write):
            self.rejects(lambda: self.build(f, spec), 'operator-seal failure')
        self.assertTrue((self.case / 'operator/FAILED.json').is_file())
        self.assertFalse((self.case / 'anonymous/SEAL.json').exists(), 'Failed preparation left a dispatchable anonymous seal')

    def test_packet_12_neutral_utf16_and_escaped_json_copies_remain_byte_exact(self):
        f = self.roles()
        raw = '{"assertions":[{"status":"F","actual":"한국","expected":"공백  x"}]}'.encode('utf-16')
        spec = f.spec(raw=raw, method='copy')
        escaped = f.put(f.root / 'original/escaped.json', raw=b'{"status":"U","message":"\\u6d4b\\u8bd5"}\n')
        spec['documents'].append({'original': escaped, 'anonymous_relative': 'reports/escaped.json', 'method': 'copy'})
        spec['anonymous_description']['material'].append('reports/escaped.json')
        self.build(f, spec)
        self.assertEqual((self.case / 'anonymous/reports/report.json').read_bytes(), raw)
        self.assertEqual((self.case / 'anonymous/reports/escaped.json').read_bytes(), Path(escaped['path']).read_bytes())


class GateControls(ReviewCase):
    def test_gate_01_complete_thirty_roles_is_only_a_record_barrier(self):
        f = self.roles(); result = barriers.verify_index(f.reader, f.index(), 'cause')
        self.observe('verification', result)
        self.assertEqual(result['distinct_contexts'], 30)
        self.assertEqual(result['groups'], 15)
        self.assertIn('No product pass', result['scope'])

    def test_gate_02_missing_group_blocks_all_alarm_reads(self):
        self.gate_rejects(lambda f, spec: spec.update(first_cause_barrier=f.index(rows=f.rows[:-1])))

    def test_gate_03_last_of_thirty_bad_seal_blocks_all_alarm_reads(self):
        def mutate(f, spec):
            rows = copy.deepcopy(f.rows); rows[-1]['seals']['J2']['sha256'] = '0' * 64
            spec['first_cause_barrier'] = f.index(rows=rows)
        self.gate_rejects(mutate)

    def test_gate_04_reused_context_blocks_all_alarm_reads(self):
        def mutate(f, spec):
            rows = copy.deepcopy(f.rows); rows[-1]['actors']['J2'] = rows[0]['actors']['J1']
            spec['first_cause_barrier'] = f.index(rows=rows)
        self.gate_rejects(mutate)

    def test_gate_05_missing_own_input_blocks_all_alarm_reads(self):
        def mutate(f, spec):
            rows = copy.deepcopy(f.rows); rows[-1]['inputs'] = []
            spec['first_cause_barrier'] = f.index(rows=rows)
        self.gate_rejects(mutate)

    def test_gate_06_changed_last_grade_blocks_all_alarm_reads(self):
        def mutate(f, spec):
            path = Path(f.rows[-1]['seals']['J2']['path']).parent / 'grade.json'
            value = json.loads(path.read_bytes()); value['observations'][0]['status'] = 'P'
            path.write_bytes(encoded(value))
        self.gate_rejects(mutate)

    def test_gate_07_ambiguous_duplicate_index_fails_before_alarm_reads(self):
        def mutate(f, spec):
            raw = Path(spec['first_cause_barrier']['path']).read_bytes()
            ambiguous = b'{"review_record_barrier_closed":false,' + raw.lstrip()[1:]
            spec['first_cause_barrier'] = f.put(f.root / 'cause/AMBIGUOUS.json', raw=ambiguous)
        self.gate_rejects(mutate)

    def test_gate_08_bool_version_is_not_an_exact_version_number(self):
        self.gate_rejects(lambda f, spec: spec.update(first_cause_barrier=f.index(version=True)))

    def test_gate_09_duplicate_grade_members_cannot_close_the_gate(self):
        def mutate(f, spec):
            row = f.rows[-1]; judge = 'J2'; folder = Path(row['seals'][judge]['path']).parent
            raw = (folder / 'grade.json').read_bytes()
            raw = b'{"observations":[{"status":"P"}],' + raw.lstrip()[1:]
            grade = f.put(folder / 'grade.json', raw=raw)
            seal = json.loads(Path(row['seals'][judge]['path']).read_bytes())
            seal['files']['grade.json'] = grade['sha256']
            row['seals'][judge] = f.put(folder / 'SEAL.json', seal)
            row['episode_end'] = f.put(Path(row['episode_end']['path']), {'anonymous_group': row['group'], 'grade_seals': row['seals']})
            spec['first_cause_barrier'] = f.index()
        self.gate_rejects(mutate)

    def test_gate_10_unsealed_symlink_directory_cannot_close_the_gate(self):
        def mutate(f, spec):
            folder = Path(f.rows[-1]['seals']['J2']['path']).parent
            target = f.root / 'unsealed-target'; target.mkdir(); (target / 'extra.txt').write_bytes(b'Synthetic extra output\n')
            (folder / 'hidden-alias').symlink_to(target, target_is_directory=True)
        self.gate_rejects(mutate)

    def test_gate_11_alarm_barrier_requires_original_own_actors(self):
        f = self.roles(); cause_ref = f.index()
        alarm = ThirtyRoles(f.root, phase='alarm')
        ref = alarm.index(predecessor=cause_ref)
        result = barriers.verify_index(f.reader, ref, 'alarm')
        self.observe('valid-alarm-barrier', result)
        self.assertEqual(result['distinct_contexts'], 30)
        alarm.rows[-1]['actors']['J2'] = '/root/synthetic_new_context'
        self.rejects(lambda: barriers.verify_index(f.reader, alarm.index(predecessor=cause_ref), 'alarm'), 'new actor in alarm phase')

    def test_gate_12_unsealed_regular_output_blocks_all_alarm_reads(self):
        def mutate(f, spec):
            folder = Path(f.rows[-1]['seals']['J2']['path']).parent
            (folder / 'unsealed-note.txt').write_bytes(b'Synthetic extra regular output\n')
        self.gate_rejects(mutate)

    def test_gate_13_noncanonical_actor_alias_cannot_inflate_context_count(self):
        def mutate(f, spec):
            rows = copy.deepcopy(f.rows)
            rows[-1]['actors']['J2'] = '/root/alias/../' + rows[0]['actors']['J1'].split('/root/', 1)[1]
            spec['first_cause_barrier'] = f.index(rows=rows)
        self.gate_rejects(mutate)


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.rows = []

    def addSuccess(self, test):
        super().addSuccess(test); self.rows.append({'test': test.id(), 'status': 'pass'})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.rows.append({'test': test.id(), 'status': 'fail', 'traceback': ''.join(traceback.format_exception(*error))})

    def addError(self, test, error):
        super().addError(test, error)
        self.rows.append({'test': test.id(), 'status': 'error', 'traceback': ''.join(traceback.format_exception(*error))})


def main():
    global RUN, projection, packet, barriers
    parser = argparse.ArgumentParser()
    parser.add_argument('--modules', required=True, type=Path)
    parser.add_argument('--run', required=True, type=Path)
    args = parser.parse_args()
    for path in (args.modules, args.run):
        if not path.is_absolute() or not path.is_relative_to(HERE):
            raise ValueError('All review inputs/outputs must stay inside the exclusive review root')
    RUN = args.run
    RUN.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.modules))
    projection = importlib.import_module('anonymous_projection')
    barriers = importlib.import_module('phase_barriers')
    packet = importlib.import_module('alarm_packet')
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                               for cls in (ProjectionControls, PacketControls, GateControls))
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    source_pins = {p.name: sha(p.read_bytes()) for p in args.modules.glob('*.py')}
    value = {'version': 1, 'kind': 'independent-synthetic-alarm-tool-behavior-results',
             'modules': str(args.modules), 'module_sha256': source_pins,
             'control_sha256': sha(Path(__file__).read_bytes()),
             'tests_run': result.testsRun, 'passed': result.testsRun - len(result.failures) - len(result.errors),
             'failures': len(result.failures), 'errors': len(result.errors), 'controls': result.rows,
             'synthetic_only': True, 'SDK_or_device_execution': False, 'business_judgments': False}
    dump(RUN / 'RESULT.json', value)
    print(json.dumps({k: value[k] for k in ('tests_run', 'passed', 'failures', 'errors', 'control_sha256')}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
