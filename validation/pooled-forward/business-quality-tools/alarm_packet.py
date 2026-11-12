"""Generic gated alarm material packaging; no alarm truth or cause synthesis."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

from anonymous_projection import LEAK, project, strict_json
from phase_barriers import original, verify_index


def digest(raw): return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    path.chmod(0o444)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()


def member(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or str(p) != name or '..' in p.parts or '\\' in name or p.name == 'SEAL.json':
        raise ValueError('Canonical neutral packet member required')
    return name


def build(reader, spec, output, operator_record):
    """Use explicit immutable file selection and an already closed cause barrier.

    The original spec/ledger stays outside the anonymous output. Every original
    copied byte or bounded JSON transformation is pinned there. The caller must
    seal all groups' artifact selections uniformly before alarm dispatch.
    """
    if spec.get('version') != 1 or spec.get('kind') != 'explicit-anonymous-alarm-material-spec':
        raise ValueError('Exact alarm material spec required')
    verified = verify_index(reader, spec['first_cause_barrier'], 'cause')
    group = spec['anonymous_group']
    barrier = original(reader, spec['first_cause_barrier'])
    if group not in {row['group'] for row in barrier['groups']}:
        raise ValueError('Anonymous group is absent from the closed cause barrier')
    output, record = Path(output), Path(operator_record)
    if output.exists() or record.exists() or output == record or output in record.parents or record in output.parents:
        raise ValueError('Fresh disjoint anonymous and operator-only directories required')
    output.mkdir(parents=True); record.mkdir(parents=True)
    write(record / 'SPEC.json', encoded(spec))
    ledger = {'version': 1, 'kind': 'operator-only-alarm-byte-and-projection-ledger',
              'anonymous_group': group, 'first_cause_barrier': spec['first_cause_barrier'],
              'closed_cause_contexts': verified['distinct_contexts'], 'copies': [], 'projections': [],
              'quality_judgment': False, 'mapping_revealed': False}
    try:
        names = set()
        for item in spec['documents']:
            name = member(item['anonymous_relative'])
            if name in names or name in {'PACKET.json', 'INSTRUCTIONS.md', 'GRADE-TEMPLATE.json'}:
                raise ValueError('Duplicate or reserved alarm packet member')
            names.add(name)
            raw = reader.read_bytes(item['original']['path'])
            if digest(raw) != item['original']['sha256']:
                raise ValueError('Original alarm material bytes changed')
            if item['method'] == 'copy':
                anonymous = raw
                ledger['copies'].append({'original': item['original'], 'anonymous_relative': name,
                                         'bytes': len(raw), 'sha256': digest(raw)})
            elif item['method'] == 'bounded-json':
                value, proof = project(strict_json(raw), **item['projection'])
                anonymous = encoded(value)
                ledger['projections'].append({'original': item['original'], 'anonymous_relative': name,
                                              'bytes': len(anonymous), 'sha256': digest(anonymous), 'projection': proof})
            else:
                raise ValueError('Unknown alarm material preparation method')
            try:
                text = anonymous.decode('utf-8')
            except UnicodeDecodeError:
                text = None
            if text is not None and LEAK.search(text):
                raise ValueError('Identity leak in neutral alarm material')
            write(output / name, anonymous)
        description = spec['anonymous_description']
        if description.get('anonymous_group') != group or LEAK.search(json.dumps(description, ensure_ascii=False)):
            raise ValueError('Neutral description identity differs')
        write(output / 'PACKET.json', encoded(description))
        for key, name in [('instructions', 'INSTRUCTIONS.md'), ('grade_template', 'GRADE-TEMPLATE.json')]:
            value = spec[key]
            raw = reader.read_bytes(value['path'])
            if digest(raw) != value['sha256'] or LEAK.search(raw.decode('utf-8')):
                raise ValueError('Original fixed alarm instruction/template differs or reveals identity')
            write(output / name, raw)
            ledger['copies'].append({'original': value, 'anonymous_relative': name,
                                     'bytes': len(raw), 'sha256': digest(raw)})
        inventory = {str(p.relative_to(output)): {'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size}
                     for p in sorted(output.rglob('*')) if p.is_file()}
        ledger['anonymous_inventory'] = inventory
        write(record / 'LEDGER.json', encoded(ledger))
        write(output / 'SEAL.json', encoded({'version': 1, 'kind': 'anonymous-alarm-material-seal',
              'anonymous_group': group, 'files': {name: row['sha256'] for name, row in inventory.items()}}))
        summary = {'version': 1, 'packet_seal': {'path': str(output / 'SEAL.json'), 'sha256': digest((output / 'SEAL.json').read_bytes())},
                   'operator_ledger': {'path': str(record / 'LEDGER.json'), 'sha256': digest((record / 'LEDGER.json').read_bytes())},
                   'quality_judgment': False, 'mapping_revealed': False}
        write(record / 'SEAL.json', encoded(summary))
        return summary
    except BaseException as error:
        write(record / 'FAILED.json', encoded({'version': 1, 'error': {'type': type(error).__name__, 'message': str(error)},
              'partial_ledger': ledger, 'scope': 'Incomplete original preparation retained; no alarm role may receive an unsealed packet, no quality or oracle change.'}))
        raise
