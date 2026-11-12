import hashlib
import json
import unittest

import disk_accounting as module


class Reader:
    def __init__(self): self.files = {}
    def put(self, path, raw):
        self.files[path] = raw
        return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest()}
    def read_bytes(self, path): return self.files[path]


def fixture():
    reader = Reader(); scopes = ['T%d/%s' % (i, arm) for i in range(1, 6) for arm in ['A', 'B']]
    features = {'kind': 'public-feature-occurrence-receipts', 'records': [
        {'task': key.split('/')[0], 'arm': key.split('/')[1], 'window': {'start_unix': 10, 'end_unix': 20}}
        for key in scopes]}
    scans = [{'started_at_unix': start, 'finished_at_unix': end,
              'groups': {key: {'allocated_bytes': size} for key in scopes}, 'total_allocated_bytes': size*7}
             for start, end, size in [(9, 11, 1000), (12, 14, 100), (16, 18, 150), (21, 22, 5000)]]
    feature_ref = reader.put('/windows.json', json.dumps(features).encode())
    meter_ref = reader.put('/meter.jsonl', b''.join((json.dumps(s)+'\n').encode() for s in scans))
    return reader, meter_ref, feature_ref, features, scans


class DiskControls(unittest.TestCase):
    def test_whole_scan_brackets_and_independent_union_are_retained(self):
        reader, meter, windows, _, _ = fixture(); result = module.public_windows(reader, meter, windows)
        row = result['records'][0]
        self.assertEqual((row['fully_contained_scans'], row['overlapping_scans']), (2, 3))
        self.assertEqual(row['contained_peak_allocated_bytes'], 150)
        self.assertEqual(row['overlap_peak_allocated_bytes'], 1000)
        self.assertEqual(result['arms']['A']['largest_observed_per_pr_peak_bytes'], 150)
        self.assertEqual(result['whole_stream_simultaneous_union_scan_peak_bytes'], 35000)
        self.assertEqual(result['scan_duration_seconds']['median'], 2)
        self.assertEqual(result['inputs']['meter'], meter)

    def test_unobserved_window_stays_unknown_not_zero(self):
        reader, meter, windows, features, _ = fixture()
        features['records'][0]['window'] = {'start_unix': 100, 'end_unix': 200}
        windows = reader.put('/windows.json', json.dumps(features).encode())
        result = module.public_windows(reader, meter, windows)
        self.assertIsNone(result['records'][0]['contained_peak_allocated_bytes'])
        self.assertEqual(result['arms']['A']['unobserved_pr_windows'], 1)

    def test_partial_stream_wrong_hash_and_bool_bytes_fail(self):
        for kind in ['partial', 'hash', 'bool']:
            reader, meter, windows, _, scans = fixture()
            if kind == 'partial': meter = reader.put('/meter.jsonl', reader.files['/meter.jsonl'][:-1])
            elif kind == 'hash': reader.files['/meter.jsonl'] += b' '
            else:
                scans[0]['groups']['T1/A']['allocated_bytes'] = True
                meter = reader.put('/meter.jsonl', b''.join((json.dumps(s)+'\n').encode() for s in scans))
            with self.assertRaises(ValueError): module.public_windows(reader, meter, windows)


if __name__ == '__main__': unittest.main(verbosity=2)
