"""Revision 2: compatible gated alarm packaging, without alarm truth synthesis."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import unicodedata

from anonymous_projection import LEAK, json_text, project, strict_json
from phase_barriers import canonical_absolute, file_inventory, recorded_ref, verify_index


IMPLEMENTATION_REVISION = 2


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _directory_fd(path, *, create=False):
    """Open canonical directory components without following any symlink."""
    path = canonical_absolute(str(path))
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            if create:
                try:
                    os.mkdir(part, dir_fd=fd)
                except FileExistsError:
                    pass
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


def _fresh_directory(path):
    parent = _directory_fd(path.parent, create=True)
    try:
        os.mkdir(path.name, dir_fd=parent)
    finally:
        os.close(parent)


def write(path, raw):
    path = canonical_absolute(str(path))
    parent = _directory_fd(path.parent, create=True)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
    finally:
        os.close(parent)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), 0o444)


def encoded(value):
    # Dict insertion order and every list order are retained; no float coercion.
    return (json_text(value, indent=2) + '\n').encode('utf-8')


def member(name):
    if not isinstance(name, str) or not name or '\\' in name or any(
            unicodedata.category(char).startswith('C') for char in name):
        raise ValueError('Canonical neutral packet member required')
    p = PurePosixPath(name)
    if p.is_absolute() or str(p) != name or not p.parts or '..' in p.parts or any(
            part.casefold() in {'.git', 'seal.json'} for part in p.parts) or LEAK.search(name):
        raise ValueError('Canonical neutral packet member required')
    return name


def _destination(value):
    # Do not resolve aliases: the supplied spelling itself must identify a fresh,
    # disjoint physical namespace. Existing ancestors may not be symlinks.
    path = canonical_absolute(os.fspath(value))
    for component in (path, *path.parents):
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            continue
        if component == path or not stat.S_ISDIR(mode):
            raise ValueError('Fresh physical output directory with no symlink ancestors required')
    return path


def _neutral_bytes(raw, name):
    # Scan raw ASCII-bearing metadata even in binary containers. This is an
    # identity token guard, not image inspection or arbitrary-code evaluation.
    if LEAK.search(raw.decode('latin-1')):
        raise ValueError('Identity leak in neutral alarm material')
    try:
        text = raw.decode(json.detect_encoding(raw))
    except (UnicodeDecodeError, LookupError):
        text = None
    if text is not None and LEAK.search(text):
        raise ValueError('Identity leak in decoded neutral alarm material')
    suffix = PurePosixPath(name).suffix.casefold()
    if suffix in {'.jsonl', '.ndjson'}:
        if text is None:
            raise ValueError('Structured alarm material is not decodable JSON text')
        values = [strict_json(line) for line in text.splitlines() if line.strip()]
    elif suffix == '.json':
        values = [strict_json(raw)]
    elif text is not None and text.lstrip().startswith(('{', '[')):
        try:
            values = [strict_json(raw)]
        except (ValueError, UnicodeDecodeError):
            values = []  # A byte-exact code/contract copy can start with { or [.
    else:
        values = []
    if any(LEAK.search(json_text(value)) for value in values):
        raise ValueError('Identity leak in decoded structured alarm material')


def _documents(spec):
    documents = spec.get('documents')
    if not isinstance(documents, list):
        raise ValueError('Explicit ordered alarm document selection required')
    names = set()
    reserved = {'packet.json', 'instructions.md', 'grade-template.json', 'seal.json'}
    for item in documents:
        if not isinstance(item, dict):
            raise ValueError('Explicit alarm document record required')
        name = member(item['anonymous_relative'])
        folded = unicodedata.normalize('NFC', name).casefold()
        if folded in names or any(folded == n or folded.startswith(n + '/') or n.startswith(folded + '/') for n in names | reserved):
            raise ValueError('Duplicate, aliased, conflicting or reserved alarm packet member')
        names.add(folded)
        recorded_ref(item['original'])
        if item.get('method') not in {'copy', 'bounded-json'}:
            raise ValueError('Unknown alarm material preparation method')
        if item['method'] == 'bounded-json' and not isinstance(item.get('projection'), dict):
            raise ValueError('Explicit bounded JSON projection required')
    return documents


def build(reader, spec, output, operator_record):
    """Same v1 call shape; the complete cause barrier precedes every alarm read.

    Source bytes remain in the externally pinned read-only source namespace.
    Its exact selection/spec and byte/value transformation provenance are kept
    in the operator directory, which cannot alias the anonymous namespace.
    """
    if not isinstance(spec, dict) or type(spec.get('version')) is not int or spec['version'] != 1 or spec.get('kind') != 'explicit-anonymous-alarm-material-spec':
        raise ValueError('Exact alarm material spec required')
    verified = verify_index(reader, spec['first_cause_barrier'], 'cause')
    group = spec['anonymous_group']
    if group not in {row['group'] for row in verified['verified_roles']}:
        raise ValueError('Anonymous group is absent from the closed cause barrier')
    output, record = _destination(output), _destination(operator_record)
    if output == record or output in record.parents or record in output.parents:
        raise ValueError('Fresh disjoint anonymous and operator-only directories required')
    spec_raw = encoded(spec)
    _fresh_directory(output); _fresh_directory(record)
    write(record / 'SPEC.json', spec_raw)
    ledger = {'version': 1, 'implementation_revision': IMPLEMENTATION_REVISION,
              'kind': 'operator-only-alarm-byte-and-projection-ledger',
              'anonymous_group': group, 'first_cause_barrier': spec['first_cause_barrier'],
              'closed_cause_contexts': verified['distinct_contexts'], 'copies': [], 'projections': [],
              'quality_judgment': False, 'mapping_revealed': False}
    try:
        documents = _documents(spec)
        for item in documents:
            name = item['anonymous_relative']
            raw = reader.read_bytes(item['original']['path'])
            if digest(raw) != item['original']['sha256']:
                raise ValueError('Original alarm material bytes changed')
            if item['method'] == 'copy':
                anonymous = raw
                ledger['copies'].append({'original': item['original'], 'anonymous_relative': name,
                                         'bytes': len(raw), 'sha256': digest(raw)})
            else:
                value, proof = project(strict_json(raw), **item['projection'])
                anonymous = encoded(value)
                ledger['projections'].append({'original': item['original'], 'anonymous_relative': name,
                                              'bytes': len(anonymous), 'sha256': digest(anonymous), 'projection': proof})
            _neutral_bytes(anonymous, name)
            write(output / name, anonymous)
        description = spec['anonymous_description']
        if not isinstance(description, dict) or description.get('anonymous_group') != group or LEAK.search(json_text(description)):
            raise ValueError('Neutral description identity differs')
        write(output / 'PACKET.json', encoded(description))
        for key, name in [('instructions', 'INSTRUCTIONS.md'), ('grade_template', 'GRADE-TEMPLATE.json')]:
            value = recorded_ref(spec[key])
            raw = reader.read_bytes(value['path'])
            if digest(raw) != value['sha256']:
                raise ValueError('Original fixed alarm instruction/template differs')
            _neutral_bytes(raw, name)
            write(output / name, raw)
            ledger['copies'].append({'original': value, 'anonymous_relative': name,
                                     'bytes': len(raw), 'sha256': digest(raw)})
        inventory = {}
        for name in sorted(file_inventory(output)):
            raw = (output / name).read_bytes()
            inventory[name] = {'sha256': digest(raw), 'bytes': len(raw)}
        ledger['anonymous_inventory'] = inventory
        ledger_raw = encoded(ledger)
        write(record / 'LEDGER.json', ledger_raw)
        packet_seal_raw = encoded({'version': 1, 'kind': 'anonymous-alarm-material-seal',
                                  'anonymous_group': group,
                                  'files': {name: row['sha256'] for name, row in inventory.items()}})
        summary = {'version': 1, 'implementation_revision': IMPLEMENTATION_REVISION,
                   'packet_seal': {'path': str(output / 'SEAL.json'), 'sha256': digest(packet_seal_raw)},
                   'operator_ledger': {'path': str(record / 'LEDGER.json'), 'sha256': digest(ledger_raw)},
                   'quality_judgment': False, 'mapping_revealed': False}
        # Publish the anonymous seal only after all required operator records
        # have been written. A failed operator seal cannot leave a sealed task.
        write(record / 'SEAL.json', encoded(summary))
        write(output / 'SEAL.json', packet_seal_raw)
        return summary
    except BaseException as error:
        write(record / 'FAILED.json', encoded({'version': 1, 'implementation_revision': IMPLEMENTATION_REVISION,
              'error': {'type': type(error).__name__, 'message': str(error)},
              'partial_ledger': ledger,
              'scope': 'Incomplete original preparation retained; no alarm role may receive an unsealed packet, no quality or oracle change.'}))
        raise
