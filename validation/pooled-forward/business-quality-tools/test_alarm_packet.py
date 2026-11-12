import copy
import json
from pathlib import Path
import tempfile
import unittest

from alarm_packet import build
import test_phase_barriers as fixturelib


class AlarmPackets(unittest.TestCase):
    def setUp(self):
        self.base = fixturelib.Barriers('test_all_thirty_review_records_not_quality_pass')
        self.base.setUp(); self.root = self.base.root; self.reader = self.base.reader
        self.barrier = self.base.index()
        raw = self.base.put(self.root / 'original/report.json', {'assertions': [
            {'id': 'example', 'actual': False, 'expected': True, 'status': 'F'}]})
        instructions = self.base.put(self.root / 'original/instructions.json', {'scope': 'Synthetic fixed instruction only'})
        template = self.base.put(self.root / 'original/template.json', {'version': 1, 'anonymous_group': 'Case01-X'})
        self.spec = {'version': 1, 'kind': 'explicit-anonymous-alarm-material-spec', 'anonymous_group': 'Case01-X',
                     'first_cause_barrier': self.barrier, 'documents': [
                         {'original': raw, 'anonymous_relative': 'reports/original.json', 'method': 'bounded-json',
                          'projection': {'omit_top_level': [], 'replacements': [], 'rewrite_pointers': []}}],
                     'anonymous_description': {'anonymous_group': 'Case01-X', 'material': ['reports/original.json']},
                     'instructions': instructions, 'grade_template': template}
        self.output = self.root / 'anonymous'; self.record = self.root / 'operator'

    def tearDown(self): self.base.tearDown()

    def test_recorded_status_expected_actual_are_preserved(self):
        result = build(self.reader, self.spec, self.output, self.record)
        original = json.loads(Path(self.spec['documents'][0]['original']['path']).read_text())
        self.assertEqual(json.loads((self.output / 'reports/original.json').read_text()), original)
        self.assertFalse(result['quality_judgment'])
        self.assertTrue((self.record / 'LEDGER.json').is_file())

    def test_no_alarm_source_read_before_complete_cause_barrier(self):
        self.spec['first_cause_barrier'] = dict(self.barrier, sha256='0' * 64)
        reads = []
        class Spy(fixturelib.Reader):
            def read_bytes(self, path):
                reads.append(str(path)); return super().read_bytes(path)
        with self.assertRaises(ValueError): build(Spy(), self.spec, self.output, self.record)
        self.assertNotIn(self.spec['documents'][0]['original']['path'], reads)
        self.assertFalse(self.output.exists())

    def test_changed_original_stays_failed_and_unsealed(self):
        self.spec['documents'][0]['original']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): build(self.reader, self.spec, self.output, self.record)
        self.assertTrue((self.record / 'FAILED.json').is_file())
        self.assertFalse((self.output / 'SEAL.json').exists())

    def test_raw_copy_is_exact(self):
        self.spec['documents'][0]['method'] = 'copy'
        build(self.reader, self.spec, self.output, self.record)
        self.assertEqual((self.output / 'reports/original.json').read_bytes(), Path(self.spec['documents'][0]['original']['path']).read_bytes())

    def test_measured_value_omission_is_not_a_projection(self):
        self.spec['documents'][0]['projection']['omit_top_level'] = ['assertions']
        with self.assertRaises(ValueError): build(self.reader, self.spec, self.output, self.record)
        self.assertTrue((self.record / 'FAILED.json').is_file())

    def test_duplicate_output_member_is_not_overwritten(self):
        self.spec['documents'].append(copy.deepcopy(self.spec['documents'][0]))
        with self.assertRaises(ValueError): build(self.reader, self.spec, self.output, self.record)


if __name__ == '__main__': unittest.main(verbosity=2)
