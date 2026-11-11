"""Pure anonymous-input integrity checks; no quality judgment or SDK execution.

The reader must expose read_bytes(original), read_json(original), and
directory(original). A pinned publication Resolver is supported without original
path fallback. Callers supply external seal/ledger byte pins, not a mutable index.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


LEAK = re.compile(rb'baseline-v12|candidate-v13|stateful-default|baseline-explicit-prior|/business/T[1-5]/[AB]/|run-cohort2/(?:arms|requests)/|/Users/rex/|/Library/Developer/')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative(value):
    require(isinstance(value, str) and value and '\\' not in value and '\x00' not in value,
            'A nonempty POSIX relative member is required')
    p = PurePosixPath(value)
    require(not p.is_absolute() and str(p) == value and
            all(v not in {'.', '..'} and v.casefold() != '.git' for v in value.split('/')),
            'Unsafe or noncanonical packet member')
    return value


def pinned(reader, ref):
    require(isinstance(ref, dict) and set(ref) >= {'path', 'sha256'}, 'Missing original reference')
    require(re.fullmatch('[0-9a-f]{64}', ref['sha256']) is not None, 'Invalid SHA256 pin')
    raw = reader.read_bytes(ref['path'])
    require(sha(raw) == ref['sha256'], 'Original reference bytes differ: ' + ref['path'])
    return raw


def namespace(reader, root):
    """Exact ordinary file inventory; no follow or acceptance of extra directories."""
    physical = reader.directory(root)
    files = {}
    dirs = set()
    for path in physical.rglob('*'):
        require(not path.is_symlink(), 'Packet symlink is forbidden')
        rel = relative(path.relative_to(physical).as_posix())
        if path.is_file():
            files[rel] = reader.read_bytes(str(Path(root) / rel))
        elif path.is_dir():
            dirs.add(rel)
        else:
            raise ValueError('Packet contains a nonregular member')
    expected_dirs = {str(p) for name in files for p in PurePosixPath(name).parents if str(p) != '.'}
    require(dirs == expected_dirs, 'Unexpected or empty packet directory')
    return files


def verify_packet(reader, original_packet_root, original_ledger_path, *,
                  packet_seal_sha256, ledger_sha256):
    """Verify one complete fixed packet using original paths or a virtual restore.

    Reads operator byte/projection ledgers, but never the X/Y mapping, grades,
    alarms omitted from packets, or tools' execution code. Does not establish
    semantic completeness of requirement inputs, correctness, or genuine defects.
    """
    root = Path(original_packet_root)
    ledger_raw = pinned(reader, {'path': str(original_ledger_path), 'sha256': ledger_sha256})
    ledger = json.loads(ledger_raw)
    seal_raw = pinned(reader, {'path': str(root / 'SEAL.json'), 'sha256': packet_seal_sha256})
    seal = json.loads(seal_raw)
    require(seal.get('kind') == 'anonymous-fixed-version-input-seal' and seal.get('version') == 1,
            'Unsupported packet seal')
    require(ledger.get('kind') == 'operator-only-anonymous-packet-byte-and-projection-ledger'
            and ledger.get('version') == 1, 'Unsupported operator ledger')
    require(ledger.get('group') == seal.get('anonymous_group'), 'Anonymous group differs')
    inventory = ledger['anonymous_inventory']
    require(set(inventory) == set(seal['files']), 'Seal and ledger member sets differ')
    members = namespace(reader, str(root))
    require(set(members) == set(inventory) | {'SEAL.json'}, 'Packet namespace differs')
    for name, row in inventory.items():
        relative(name)
        require(sha(members[name]) == row['sha256'] == seal['files'][name]
                and len(members[name]) == row['bytes'], 'Sealed member bytes differ: ' + name)
        require(LEAK.search(members[name]) is None, 'Identity disclosure in packet: ' + name)
    packet = json.loads(members['PACKET.json'])
    require(packet['anonymous_group'] == ledger['group'], 'Packet description identity differs')
    copies = {}
    for row in ledger['copies']:
        name = relative(row['anonymous_relative'])
        require(name not in copies and name in members, 'Duplicate or missing byte copy')
        raw = pinned(reader, row['original'])
        require(raw == members[name] and len(raw) == row['bytes'], 'Original byte copy differs: ' + name)
        copies[name] = row
    source = json.loads(pinned(reader, ledger['original_source_manifest']))
    require(digest(source['files']) == source['content_sha256'], 'Controller source content pin differs')
    require(source['files'] == packet['source_files'] and len(source['files']) == packet['fixed_source_file_count'],
            'Packet source declaration differs from controller capsule')
    source_names = {'source/' + relative(name) for name in source['files']}
    require({name for name in members if name.startswith('source/') and not name.startswith('source/placement/')} == source_names,
            'Source namespace is incomplete or has extra files')
    for name, expected in source['files'].items():
        raw = members['source/' + name]
        require('source/' + name in copies and sha(raw) == expected['sha256'] and len(raw) == expected['bytes'],
                'Production source byte pin differs')
    for value in packet['production_placement'].values():
        require(value in copies, 'Production placement lacks original bytes')
    for family in packet['contracts'].values():
        for platform in family.values():
            for value in platform.values():
                require(value in copies, 'Contract lacks original bytes')
    observations = {row['id']: row for row in packet['observations']}
    require(len(observations) == len(packet['observations']), 'Duplicate observation id')
    projections = {}
    source_rows = {}
    absent = {}
    for row in ledger['projections']:
        original = json.loads(pinned(reader, row['original']))
        if 'anonymous_relative' in row:
            name = relative(row['anonymous_relative'])
            require(name not in projections and name not in copies and name in members,
                    'Duplicate or missing projected member')
            selection = row['selection']
            if selection == {'all_original_top_level_members_except': ['operations', 'issues'], 'retained_values_unchanged': True}:
                value = {k: v for k, v in original.items() if k not in {'operations', 'issues'}}
            elif selection == {'all_assertions': True, 'member_allowlist': ['id', 'actual', 'snapshot_indices'], 'retained_values_unchanged': True}:
                value = {'assertions': [{k: item[k] for k in ['id', 'actual', 'snapshot_indices'] if k in item}
                                        for item in original.get('assertions', [])]}
            else:
                raise ValueError('Unregistered projection selection')
            require(json.loads(members[name]) == value and sha(members[name]) == row['projection_sha256'],
                    'Projection changes or drops original facts: ' + name)
            projections[name] = row
        elif 'source_model' in row:
            key = row['anonymous_observation']
            require(key in observations and key not in source_rows, 'Duplicate or unknown source binding')
            require(row['controller_content_sha256'] == source['content_sha256'] and
                    row['sut_source_sha256'] == digest(original), 'Source binding hash domain differs')
            capture = Path(row['original']['path']).parent
            request = reader.read_json(str(capture / 'request.json'))
            receipt = reader.read_json(str(capture / 'result.json'))
            model = row['source_model']
            wanted = {key: value['sha256'] for key, value in source['files'].items()}
            if model is not None:
                require(model == receipt['source_model'] == reader.read_json(str(capture / 'source-model.json'))
                        and digest(model) == receipt['source_model_sha256'], 'Native source model differs')
                roots = model['source_roots']
                groups = model['groups']
                require(set(groups) == {'ios', 'android', 'shared'} and len(set(roots)) == len(roots), 'Invalid platform source groups')
                for values in groups.values():
                    require(len(values) == len(set(values)) and set(values) <= set(roots), 'Invalid group roots')
                require(set(roots) == set().union(*map(set, groups.values())), 'Unclassified roots must be shared')
                indices = [i for i, path in enumerate(roots) if path in groups[model['platform']] or path in groups['shared']]
                require(model['platform'] == observations[key]['platform'] and model['indices'] == indices
                        and roots == request['source_roots'], 'Unstable source root indices')
                wanted = {key: value for key, value in wanted.items() if int(key.split('/', 1)[0]) in indices}
            require(original == wanted and receipt['source_sha256'] == digest(original)
                    and request['source_sha256'] == digest(original), 'Native source bytes do not match sealed production')
            require(reader.read_json(str(capture / 'source-after.json')) == original, 'Native source changed during collection')
            source_rows[key] = (capture, receipt)
        else:
            key = row['anonymous_observation']
            require(key in observations and key not in absent and not original.get('capture'),
                    'Claimed absence conflicts with original capture')
            require(row['selection'] == 'Capture absence only; no arm/tool/cost/failure verdict text.', 'Unregistered absence projection')
            absent[key] = row
    catalogs = {}
    for command in ledger['catalog_commands']:
        require(command['native_or_sdk_execution'] is False, 'Catalog origin is not declared pure')
        path = Path(command['output']['path'])
        name = path.name.removesuffix('-catalog-original.json')
        require(path.name == name + '-catalog-original.json' and name not in catalogs, 'Invalid catalog identity')
        original = json.loads(pinned(reader, command['output']))
        expected_sha = original.pop('catalog_sha256')
        require(digest(original) == expected_sha, 'Original catalog digest differs')
        catalogs[name] = (original, expected_sha)
    image_count = 0
    for key, obs in observations.items():
        require(obs['family'] in {'public', 'private'} and obs['platform'] in {'ios', 'android'}, 'Invalid observation scope')
        if not obs['facts_available']:
            require(key in absent or key in source_rows, 'Unknown observation lacks original availability proof')
            if key in source_rows:
                require(not source_rows[key][1].get('observation_sha256'),
                        'Available native facts must not be marked missing')
            require(not any(name.startswith(f'observations/{key}/') for name in members),
                    'Unavailable observation has undisclosed packet facts')
            continue
        require(key in source_rows and key in catalogs, 'Observation lacks bound source or catalog')
        capture, receipt = source_rows[key]
        native_name = obs['native_observation']
        require(native_name in projections and projections[native_name]['original']['path'] == str(capture / 'native/observation.json')
                and obs['original_observation_sha256'] == receipt['observation_sha256'] == projections[native_name]['original']['sha256'],
                'Native observation origin differs')
        prefix = f'observations/{key}/native/'
        expected_images = {prefix + relative(name): expected for name, expected in receipt.get('image_hashes', {}).items()}
        actual_images = {name for name in members if name.startswith(prefix) and name != native_name}
        require(actual_images == set(expected_images) and len(expected_images) == obs['original_image_count'],
                'Native image namespace differs from original receipt')
        for name, expected in expected_images.items():
            require(name in copies and sha(members[name]) == expected and
                    copies[name]['original']['path'] == str(capture / 'native' / name[len(prefix):]), 'Native image origin differs')
        image_count += len(expected_images)
        if 'automatic_actuals' in obs:
            name = obs['automatic_actuals']
            require(name in projections and projections[name]['original']['path'] == str(capture / 'automatic.json')
                    and projections[name]['original']['sha256'] == receipt['automatic_sha256'], 'Automatic actual origin differs')
        catalog, catalog_sha = catalogs[key]
        require(json.loads(members[obs['catalog']]) == catalog, 'Catalog facts differ')
        execution = reader.read_json(str(capture / 'execution.json'))
        visual = [row for row in catalog['rows'] if row['method'] == 'visual' and row['state'] in execution['selected_states']]
        template = {'version': 1, 'catalog_sha256': catalog_sha, 'observation_sha256': receipt['observation_sha256'],
                    'decisions': [{'review_id': row['review_id'], 'actual': None, 'reason': '', 'snapshot_indices': []} for row in visual]}
        expected_visual = {'rows': [{name: row.get(name) for name in ['id', 'state', 'proposition', 'review_id']} for row in visual],
                           'submission_template': template}
        require(json.loads(members[obs['visual_requirements']]) == expected_visual, 'Visual requirements incomplete or modified')
    return {'version': 1, 'kind': 'anonymous-input-mechanical-integrity', 'status': 'passed',
            'group': ledger['group'], 'packet_seal_sha256': packet_seal_sha256, 'ledger_sha256': ledger_sha256,
            'sealed_members': len(inventory), 'byte_exact_copies': len(copies), 'source_files': len(source['files']),
            'projected_documents': len(projections), 'observations': len(observations),
            'native_images': image_count, 'missing_capture_observations': sorted(absent),
            'scope': 'Byte/projection/source-binding/identity integrity only. No requirement completeness, product quality, visual judgment, delivery, independent grade, source API approval, SDK execution, or X/Y mapping reveal.'}
