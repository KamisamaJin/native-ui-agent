import copy
import hashlib
import json
import unittest

import replay_occurrences_v2 as module


class Reader:
    def __init__(self): self.files = {}
    def put(self, path, value, raw=False):
        data = value if raw else json.dumps(value).encode()
        self.files[path] = data
        return {'path': path, 'sha256': hashlib.sha256(data).hexdigest()}
    def read_bytes(self, path): return self.files[path]


def fixture():
    reader = Reader(); rows = []
    for number in range(1, 6):
        for arm in ['A', 'B']:
            task = 'T%d' % number; base = '/' + task + '/' + arm
            result = reader.put(base + '/result.json', {'task': task, 'arm': arm,
                'outcomes': [{'action': 'diagnostic', 'profile': 'ios', 'new_ui_acquisition': True, 'capture_reused': False}]})
            raw = (json.dumps({'kind': 'simulator_pool_return', 'at_unix': 15})+'\n').encode()
            journal = reader.put(base + '/events.jsonl', raw, True)
            rows.append({'task': task, 'arm': arm, 'window': {'start_unix': 10, 'end_unix': 20},
                'original_result_refs': [result],
                'journal_prefix_refs': [{'path': journal['path'], 'prefix_bytes': len(raw), 'prefix_sha256': journal['sha256']}],
                'native_operation_counts': {'diagnostic/ios/new_ui_true': 1, 'packet_adoption_true': 0},
                'owned_resource_event_counts': {'simulator_pool_return': 1}})
    data = {'version': 1, 'kind': 'public-feature-occurrence-receipts', 'records': rows}
    reference = reader.put('/feature.json', data)
    return reader, reference, data


class OccurrenceControls(unittest.TestCase):
    def test_returned_input_binds_feature_record_not_last_journal(self):
        reader, reference, data = fixture()
        value = module.replay(reader, reference)
        self.assertEqual(value['input'], reference)
        self.assertEqual(len(value['records']), 10)

    def test_changed_result_and_prefix_cannot_reuse_hashes(self):
        for field in ['original_result_refs', 'journal_prefix_refs']:
            reader, reference, data = fixture()
            path = data['records'][0][field][0]['path']; reader.files[path] += b' '
            # A journal suffix beyond its recorded prefix is deliberately legal;
            # alter the actual prefix instead for the hash-boundary control.
            if field == 'journal_prefix_refs': reader.files[path] = b'X' + reader.files[path][1:]
            with self.assertRaises(ValueError): module.replay(reader, reference)

    def test_future_journal_append_does_not_enter_public_window(self):
        reader, reference, data = fixture()
        for row in data['records']:
            reader.files[row['journal_prefix_refs'][0]['path']] += b'{"kind":"simulator_pool_checkout","at_unix":99}\n'
        self.assertEqual(module.replay(reader, reference)['input'], reference)

    def test_wrong_event_counts_fail_even_when_record_repinned(self):
        reader, reference, data = fixture()
        data['records'][0]['owned_resource_event_counts']['simulator_pool_checkout'] = 1
        reference = reader.put('/feature.json', data)
        with self.assertRaises(ValueError): module.replay(reader, reference)

    def test_new_ui_integer_cannot_masquerade_as_boolean(self):
        reader, reference, data = fixture(); row = data['records'][0]
        ref = row['original_result_refs'][0]; result = json.loads(reader.files[ref['path']])
        result['outcomes'][0]['new_ui_acquisition'] = 1
        row['original_result_refs'][0] = reader.put(ref['path'], result)
        reference = reader.put('/feature.json', data)
        with self.assertRaises(ValueError): module.replay(reader, reference)

    def test_duplicate_scope_or_result_cannot_double_count(self):
        for scope in [True, False]:
            reader, reference, data = fixture()
            if scope: data['records'].append(copy.deepcopy(data['records'][0]))
            else: data['records'][0]['original_result_refs'] *= 2
            reference = reader.put('/feature.json', data)
            with self.assertRaises(ValueError): module.replay(reader, reference)


if __name__ == '__main__': unittest.main(verbosity=2)
