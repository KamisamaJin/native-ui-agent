"""Observed allocation scans in fixed public windows, never summed peaks."""
import hashlib
import io
import json
import math
import statistics


def need(ok, why):
    if not ok: raise ValueError(why)


def original(reader, reference):
    raw = reader.read_bytes(reference['path'])
    need(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'Exact disk/window input pin differs')
    return raw


def finite(value):
    need(type(value) in {int, float} and math.isfinite(value), 'Finite scan endpoint required')
    return value


def allocation(value):
    need(type(value) is int and value >= 0, 'Nonnegative integer allocated bytes required')
    return value


def distribution(values):
    return {'count': len(values), 'minimum': min(values) if values else None,
            'median': statistics.median(values) if values else None, 'maximum': max(values) if values else None}


def public_windows(reader, meter_reference, feature_reference):
    features = json.loads(original(reader, feature_reference))
    need(features['kind'] == 'public-feature-occurrence-receipts', 'Original fixed public-window record required')
    windows = {}
    for row in features['records']:
        key = row['task'] + '/' + row['arm']; window = row['window']
        need(key not in windows and finite(window['start_unix']) <= finite(window['end_unix']), 'Unique ordered public window required')
        windows[key] = {'task': row['task'], 'arm': row['arm'], 'window': window,
                        'fully_contained_scans': 0, 'overlapping_scans': 0,
                        'contained_peak_allocated_bytes': None, 'overlap_peak_allocated_bytes': None}
    need(set(windows) == {'T%d/%s' % (i, arm) for i in range(1, 6) for arm in ['A', 'B']}, 'Exactly10 paired windows required')
    raw = original(reader, meter_reference)
    need(not raw or raw.endswith(b'\n'), 'Closed complete meter stream required')
    durations = []; gaps = []; previous = None; rows = 0; simultaneous_union_peak = None
    for line in io.BytesIO(raw):
        scan = json.loads(line); rows += 1
        start, end = finite(scan['started_at_unix']), finite(scan['finished_at_unix'])
        need(end >= start, 'Clock-reversed scan remains unsupported, not clamped')
        durations.append(end-start)
        if previous is not None: gaps.append(start-previous)
        previous = start
        total = allocation(scan['total_allocated_bytes'])
        simultaneous_union_peak = total if simultaneous_union_peak is None else max(simultaneous_union_peak, total)
        for key, record in windows.items():
            need(key in scan['groups'], 'Every configured group required in every scan')
            size = allocation(scan['groups'][key]['allocated_bytes'])
            window = record['window']
            if start <= window['end_unix'] and end >= window['start_unix']:
                record['overlapping_scans'] += 1
                old = record['overlap_peak_allocated_bytes']; record['overlap_peak_allocated_bytes'] = size if old is None else max(old, size)
            if start >= window['start_unix'] and end <= window['end_unix']:
                record['fully_contained_scans'] += 1
                old = record['contained_peak_allocated_bytes']; record['contained_peak_allocated_bytes'] = size if old is None else max(old, size)
    arms = {}
    for arm in ['A', 'B']:
        selected = [r['contained_peak_allocated_bytes'] for r in windows.values() if r['arm'] == arm]
        known = [value for value in selected if value is not None]
        arms[arm] = {'observed_per_pr_peaks': distribution(known), 'unobserved_pr_windows': len(selected)-len(known),
                     'largest_observed_per_pr_peak_bytes': max(known) if known else None}
    return {'version': 1, 'kind': 'fixed-public-window-allocation-accounting',
            'inputs': {'meter': meter_reference, 'public_windows': feature_reference}, 'records': list(windows.values()),
            'arms': arms, 'stream_rows': rows, 'scan_duration_seconds': distribution(durations),
            'scan_start_gap_seconds': distribution(gaps), 'whole_stream_simultaneous_union_scan_peak_bytes': simultaneous_union_peak,
            'scope': 'Primary per-PR values use only scans fully contained in the original public Unix window. Overlap scans are separate. Scan durations/gaps are observed, not nominal2s. Values are sequential allocated-byte scans, not atomic filesystem snapshots or exact APFS physical/transient peaks. Group/per-PR peaks are never added; stream union uses its separately recorded total. SDK/shared-cache and other unmeasured storage are outside the declared scope.'}
