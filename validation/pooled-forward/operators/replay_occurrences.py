"""Pure receipt arithmetic over exact recorded public windows.

Reader may be a losslessly restored Resolver. No original-path fallback, SDK,
source judgment, pending claim promotion or cost allocation is performed here.
"""
import collections
import hashlib
import json


def need(ok, why):
    if not ok: raise ValueError(why)


def pinned(reader, reference):
    raw = reader.read_bytes(reference['path'])
    need(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'Original receipt hash differs')
    return json.loads(raw)


def replay(reader, reference):
    recorded = pinned(reader, reference)
    need(type(recorded['version']) is int and recorded['version'] == 1
         and recorded['kind'] == 'public-feature-occurrence-receipts',
         'Original feature occurrence record required')
    rows = []; seen = set()
    for row in recorded['records']:
        identity = (row['task'], row['arm'])
        need(identity not in seen, 'Duplicate arm window'); seen.add(identity)
        native = collections.Counter(); native['packet_adoption_true'] = 0
        result_paths = set()
        for reference in row['original_result_refs']:
            need(reference['path'] not in result_paths, 'Duplicate original result'); result_paths.add(reference['path'])
            result = pinned(reader, reference)
            need((result['task'], result['arm']) == identity, 'Foreign result scope')
            for outcome in result['outcomes']:
                value = outcome.get('new_ui_acquisition')
                need(value is None or type(value) is bool, 'New-UI flag must be explicit Boolean/null')
                if type(value) is bool:
                    key = outcome['action'] + '/' + outcome['profile'] + '/new_ui_' + str(value).lower()
                    native[key] += 1
                if outcome.get('capture_reused') is True: native['packet_adoption_true'] += 1
        owned = collections.Counter(); journals = []
        for reference in row['journal_prefix_refs']:
            raw = reader.read_bytes(reference['path'])
            length = reference['prefix_bytes']
            need(type(length) is int and length >= 0 and len(raw) >= length, 'Recorded complete prefix required')
            prefix = raw[:length]
            need(hashlib.sha256(prefix).hexdigest() == reference['prefix_sha256'], 'Recorded resource prefix differs')
            events = [json.loads(line) for line in prefix.splitlines()]
            events = [event for event in events if row['window']['start_unix'] <= event['at_unix'] <= row['window']['end_unix']]
            for event in events:
                kind = event['kind']
                if kind in {'simulator_create_intent', 'simulator_removed', 'simulator_pool_return', 'simulator_pool_checkout'}:
                    owned[kind] += 1
                if kind == 'simctl_command' and event['exit_code'] == 0:
                    argv = event['argv']
                    if 'simctl' in argv:
                        command = argv[argv.index('simctl') + 1]
                        if command in {'create', 'delete'}: owned['simctl_' + command + '_exit_0'] += 1
            journals.append({'prefix': reference, 'events_in_public_window': len(events)})
        need(dict(native) == row['native_operation_counts'], 'Native occurrence arithmetic differs')
        need(dict(owned) == row['owned_resource_event_counts'], 'Owned resource occurrence arithmetic differs')
        rows.append({'task': identity[0], 'arm': identity[1], 'native_operation_counts': dict(native),
                     'owned_resource_event_counts': dict(owned), 'result_count': len(result_paths), 'journal_prefixes': journals})
    need(seen == {('T%d' % i, arm) for i in range(1, 6) for arm in ['A', 'B']}, 'All10 original public windows required')
    return {'version': 1, 'kind': 'verified-public-feature-occurrence-arithmetic', 'input': reference,
            'records': rows, 'status': 'verified',
            'scope': 'Counts of recorded actual operations in the pinned public windows. A false new-UI flag does not mean zero SDK work, zero cost or delivery. No quality adjudication.'}
