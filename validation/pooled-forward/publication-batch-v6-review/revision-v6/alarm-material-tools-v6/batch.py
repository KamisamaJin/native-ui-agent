#!/usr/bin/env python3
"""Gated uniform fifteen-version alarm selection; no product adjudication.

Selection/derivation is separate from immutable alarm_packet.build. Raw original
bytes and every intermediate projection remain outside judge inputs. Actual
data is inaccessible through this entry until the full cause barrier verifies.
"""
import argparse
import builtins
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import time
import traceback
import types

MATERIAL_SHA = '4783735c450d882c7fcf62e5a1192dacafa96352fee899023a8e67a12e2e94ac'
EMITTER_SCHEMA_SHA = '7149cb0873e30cfe3690e0b64c1f7d711c916c927a313f0a82e19d1841acbda9'
_here = Path(__file__).resolve().parent
_material_bytes = (_here / 'material.py').read_bytes()
if hashlib.sha256(_material_bytes).hexdigest() != MATERIAL_SHA:
    raise ValueError('Pinned material-v3 source differs')
m = types.ModuleType('batch_private_material_v3'); m.__file__ = str(_here / 'material.py')
exec(compile(_material_bytes, m.__file__, 'exec'), m.__dict__)
_schema_bytes = (_here / 'EMITTER-SCHEMA-v5.json').read_bytes()
if hashlib.sha256(_schema_bytes).hexdigest() != EMITTER_SCHEMA_SHA:
    raise ValueError('Pinned emitter admission schema differs')
EMITTER_SCHEMA = m.projection.strict_json(_schema_bytes)


def presentation_modules():
    """Execute pinned sources afresh; do not trust mutable sys.modules entries."""
    modules = {}; real_import = builtins.__import__
    def private_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in modules: return modules[name]
        return real_import(name, globals, locals, fromlist, level)
    for name in ['anonymous_projection', 'phase_barriers', 'alarm_packet']:
        path = Path(__file__).resolve().parent.parent / 'publication-alarm-review/revision-v2' / (name + '.py')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != m.PINS[name + '.py']:
            raise ValueError('Pinned presentation source differs')
        module = types.ModuleType('batch_private_' + name); module.__file__ = str(path)
        module.__dict__['__builtins__'] = dict(vars(builtins), __import__=private_import)
        exec(compile(raw, str(path), 'exec'), module.__dict__)
        modules[name] = module
    return modules


_presentation = presentation_modules()
json_text = _presentation['anonymous_projection'].json_text
strict_json = _presentation['anonymous_projection'].strict_json
verify_index = _presentation['phase_barriers'].verify_index
build = _presentation['alarm_packet'].build
MAP_SEAL_SHA = 'b7f575344dbe240ab0a2ffb041f52e5b450ccf0b77179a59633f69bc66a837c3'


def digest(raw): return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    _presentation['alarm_packet'].write(path, raw)


def encoded(value): return (json_text(value, sort_keys=True, indent=2) + '\n').encode()


class LiveReader:
    """Explicit no-follow original access for preparation, never restore fallback."""
    def __init__(self, root):
        p = root / 'publication-resolver/resolver.py'
        if digest(p.read_bytes()) != '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204':
            raise ValueError('Frozen Resolver source differs')
        spec = importlib.util.spec_from_file_location('alarm_prepare_live_reader', p)
        self.module = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.module)
    def read_bytes(self, original): return self.module.read_regular(original)[0]
    def read_json(self, original): return strict_json(self.read_bytes(original))
    def hash(self, original): return digest(self.read_bytes(original))
    def directory(self, original):
        p = self.module.absolute(str(original)); fd = self.module.open_directory(p); os.close(fd); return p


def ref(reader, path): return {'path': str(path), 'sha256': reader.hash(str(path))}


def pinned(reader, value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('Exact original reference required')
    raw = reader.read_bytes(value['path'])
    if digest(raw) != value['sha256']: raise ValueError('Original pinned bytes differ')
    return strict_json(raw)


def relative(value):
    if not isinstance(value, str) or not value or '\x00' in value:
        raise ValueError('Safe original relative artifact required')
    p = PurePosixPath(value)
    if p.is_absolute() or str(p) != value or not p.parts or '..' in p.parts or '\\' in value:
        raise ValueError('Safe original relative artifact required')
    return p


REPORT_NAMES = m.REPORT_NAMES | set(EMITTER_SCHEMA['additional_reports'])
NONREPORT_JSON = set(EMITTER_SCHEMA['nonreport_control_paths'])
OPAQUE_PREFIXES = ('tool-runtime/', 'capture/tool-runtime/', 'native/sources/',
    'native/tool-sources/', 'native/compiled-project/', 'capture/native/sources/',
    'capture/native/tool-sources/', 'capture/native/compiled-project/',
    'native/test.xcresult/', 'capture/native/test.xcresult/')


def inventory_kind(relative_name):
    """Explicit frozen emitter layout; unknown JSON is never guessed nonfactual."""
    relative_name = relative(relative_name).as_posix()
    if relative_name.startswith(OPAQUE_PREFIXES): return 'control'
    normalized = relative_name[len('capture/'):] if relative_name.startswith('capture/') else relative_name
    attachment = EMITTER_SCHEMA['factual_attachment_reports']
    path = PurePosixPath(normalized)
    if (path.parent.as_posix() == attachment['directory'] and path.suffix == attachment['suffix']
            and path.name not in attachment['excluded_basenames']):
        return 'report'
    if PurePosixPath(relative_name).name in REPORT_NAMES: return 'report'
    if normalized in NONREPORT_JSON: return 'control'
    if normalized == 'native/observation.json': return 'native-observation'
    if PurePosixPath(relative_name).suffix.lower() in {'.json', '.jsonl'}:
        raise ValueError('Unreviewed service JSON member; no silent report filtering: ' + relative_name)
    return 'other-original-member'


def code_pins():
    return {'batch_sha256': digest(Path(__file__).read_bytes()), 'material_sha256': MATERIAL_SHA,
            'emitter_schema_sha256': EMITTER_SCHEMA_SHA}


def namespace(reader, original):
    return _presentation['phase_barriers'].file_inventory(reader.directory(str(original)))


def chain_ref(reader, path, pins):
    key = str(path)
    if key not in pins:
        raise ValueError('Required original is absent from the verified native read set: ' + key)
    raw = reader.read_bytes(key)
    if digest(raw) != pins[key]:
        raise ValueError('Required original changed from the verified native chain: ' + key)
    return {'path': key, 'sha256': pins[key]}


def _numeric(value, integer=False):
    return (type(value) is int if integer else type(value) in (int, float, m.projection.Decimal)) and value >= 0


def metadata_file_key(original_path):
    """Opaque path identity only: never an assertion that a file is supplied."""
    if not m._path(original_path) or original_path == '/':
        raise ValueError('Canonical original absolute metadata file path required')
    return 'record-ref-' + digest(original_path.encode('utf-8'))


def admit_metadata_keys(original):
    """Source-typed key composition before the unchanged factual projector.

    No caller alias selects a key. Raw paths and exact before/after map hashes
    are operator-only proof; every SHA value and other recorded field remains.
    """
    m.projection._validate_json(original)
    if type(original) is not dict: raise ValueError('Recorded report object required')
    value = copy.deepcopy(original); proof = []
    schema = EMITTER_SCHEMA['metadata_key_admission']
    def sha(value):
        return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
    def file_map(row, parts, kind):
        if any(m.projection._protected(part) for part in parts):
            raise ValueError('Protected factual metadata map cannot be rewritten')
        files = row['files']
        if type(files) is not dict: raise ValueError('Exact source-declared file SHA map required')
        admitted, entries = {}, []
        for key, expected in files.items():
            if not sha(expected): raise ValueError('Exact source-declared file SHA value required')
            anonymous = metadata_file_key(key)
            if anonymous in admitted: raise ValueError('Metadata key alias collision; no file-map merge')
            admitted[anonymous] = expected
            entries.append({'original_key': key, 'anonymous_key': anonymous, 'file_sha256': expected})
        row['files'] = admitted
        proof.append({'pointer': m.projection.pointer(parts), 'source_schema': kind,
            'original_map_sha256': m.projection.digest(files), 'admitted_map_sha256': m.projection.digest(admitted),
            'entries': entries, 'availability': schema['availability']})
    compiled = schema['compiled']; bound = schema['bound_source']
    if set(value) == set(compiled['fields']) and type(value['version']) is int and value['version'] == 1 and value['explicit'] is True:
        if (not sha(value['design_lock_sha256']) or not sha(value['plan_sha256'])
                or type(value['source_ref']) is not dict or set(value['source_ref']) != {'source', 'pointer'}
                or type(value['claims']) is not list or type(value['issues']) is not list or type(value['scope']) is not str):
            raise ValueError('Unreviewed compiled evidence responsibility schema')
        for index, row in enumerate(value['claims']):
            if (type(row) is not dict or set(row) != set(compiled['row_fields'])
                    or row['expected'] is not True or row['unit'] != 'bool' or type(row['supported']) is not bool
                    or type(row['rule_ids']) is not list or type(row['assertion_ids']) is not list
                    or type(row['provenance']) is not dict or set(row['provenance']) != {'source', 'pointer', 'design_lock_sha256'}
                    or row['provenance']['design_lock_sha256'] != value['design_lock_sha256']
                    or any(row['provenance'][k] != value['source_ref'][k] for k in ['source', 'pointer'])):
                raise ValueError('Unreviewed compiled evidence claim metadata schema')
            file_map(row, ['claims', index, 'files'], compiled['kind'])
    elif value.get('format') == bound['kind']:
        if (set(value) != set(bound['fields']) or not sha(value['design_lock_sha256'])
                or type(value['observations']) is not list or type(value['scope']) is not str):
            raise ValueError('Unreviewed bound source review schema')
        for index, row in enumerate(value['observations']):
            if (type(row) is not dict or set(row) != set(bound['row_fields'])
                    or type(row['observed']) not in {bool, type(None)} or not sha(row['claim_sha256'])
                    or type(row['reason']) is not str or not row['reason'].strip() or type(row['citations']) is not list
                    or row['observed'] is not None and not row['citations']
                    or any(type(ref) is not dict or set(ref) != {'path', 'line'} or type(ref['path']) is not str
                        or type(ref['line']) is not int or ref['line'] < 1 for ref in row['citations'])):
                raise ValueError('Unreviewed bound source observation metadata schema')
            file_map(row, ['observations', index, 'files'], bound['kind'])
    def reject_unknown(item):
        if type(item) is dict:
            for key, sub in item.items():
                if key.startswith('/') or m.projection.LEAK.search(key):
                    raise ValueError('Unreviewed path-keyed or identity-bearing object map; no factual key rewrite')
                reject_unknown(sub)
        elif type(item) is list:
            for sub in item: reject_unknown(sub)
    reject_unknown(value)
    return value, proof


def present_value(original, *, outcome=False):
    """Compose explicit source-schema metadata admission with frozen material-v3.

    Only exact known execution shapes are omitted here. All raw refs and hashes
    remain in the operator derivation; extra known outcome facts are retained.
    """
    m.projection._validate_json(original)
    if not isinstance(original, dict):
        raise ValueError('Recorded report object required')
    admitted, key_maps = admit_metadata_keys(original); omitted = {}
    def omit(key, schema):
        omitted[key] = {'original_value_sha256': m.projection.digest(admitted[key]), 'schema': schema}
        del admitted[key]
    if 'trace' in admitted:
        trace = admitted['trace']
        if not isinstance(trace, list) or not all(type(x) is str and x in EMITTER_SCHEMA['trace_methods'] for x in trace):
            raise ValueError('Unreviewed emitter trace; retain the original, do not drop factual rows')
        omit('trace', 'frozen-feedback-method-identifiers')
    operations = admitted.get('operations')
    if isinstance(operations, dict) and ('counts' in operations or operations.get('scope') == EMITTER_SCHEMA['operation_scope']):
        methods = set(EMITTER_SCHEMA['operation_methods'])
        if (set(operations) != {'counts', 'seconds', 'scope'} or operations['scope'] != EMITTER_SCHEMA['operation_scope']
                or not isinstance(operations['counts'], dict) or not isinstance(operations['seconds'], dict)
                or set(operations['counts']) != set(operations['seconds']) or not set(operations['counts']) <= methods
                or not all(_numeric(v, True) for v in operations['counts'].values())
                or not all(_numeric(v) for v in operations['seconds'].values())):
            raise ValueError('Unreviewed native operation counters; no hidden factual omission')
        omit('operations', 'frozen-native-counts-seconds-exact-scope')
    if outcome:
        if admitted.get('version') in EMITTER_SCHEMA['native_outcome_versions'] and type(admitted.get('version')) is int:
            if admitted.get('kind') != EMITTER_SCHEMA['native_outcome_kind']:
                raise ValueError('Unreviewed native outcome kind/version')
            omit('version', 'frozen-native-outcome-version')
        if 'operator_revision' in admitted:
            if admitted['operator_revision'] not in EMITTER_SCHEMA['operator_revisions']:
                raise ValueError('Unreviewed native operator revision')
            omit('operator_revision', 'frozen-native-operator-revision')
        if 'tool_root' in admitted:
            if not m._path(admitted['tool_root']):
                raise ValueError('Unreviewed native tool-root metadata')
            omit('tool_root', 'canonical-execution-tool-root')
        extras = {key: admitted[key] for key in admitted if key in EMITTER_SCHEMA['retained_outcome_extensions']}
        base = {key: val for key, val in admitted.items() if key not in extras}
        selected = m.outcome_view(base)
        value = {key: copy.deepcopy(admitted[key]) for key in admitted if key in selected or key in extras}
    else:
        value = admitted
    admission = {'schema_sha256': EMITTER_SCHEMA_SHA,
                 'original_value_sha256': m.projection.digest(original),
                 'admitted_value_sha256': m.projection.digest(admitted),
                 'selected_value_sha256': m.projection.digest(value), 'omitted_top_level': omitted,
                 'metadata_key_maps': key_maps}
    return value, admission


class Group:
    def __init__(self, root, reader, group, task, arm, manifest, events, snapshot, native_read_pins, work):
        self.root, self.reader, self.group, self.task, self.arm = root, reader, group, task, arm
        self.manifest, self.events, self.snapshot, self.native_read_pins = manifest, events, snapshot, native_read_pins
        self.work = work / group; _presentation['alarm_packet']._fresh_directory(self.work)
        self.documents, self.derivations, self.description = [], [], {
            'anonymous_group': group, 'versions': [], 'episodes': [], 'documents': [],
            'scope': 'Original all-status reports and claims; status is not independent truth. Source capsules, native epochs and original image layout remain explicit.',
            'metadata_reference_scope': 'record-ref-* values are opaque original provenance identifiers, not supplied packet members.'}
        self.versions, self.aliases, self.captures, self.document_paths, self.metadata_aliases = {}, {}, {}, {}, {}
        self.run = root / 'cache/business/run-cohort2'
        self.initial = group.endswith('-I')

    def original(self, path): return self.reader.read_json(str(path))

    def exact(self, original_ref, destination, info):
        name = relative(destination).as_posix(); raw = self.reader.read_bytes(original_ref['path'])
        if digest(raw) != original_ref['sha256']: raise ValueError('Original material pin differs')
        if any(item['anonymous_relative'] == name for item in self.documents):
            raise ValueError('Duplicate anonymous selected document')
        self.documents.append({'original': original_ref, 'anonymous_relative': name, 'method': 'copy'})
        self.description['documents'].append(dict(info, path=name, original_sha256=original_ref['sha256']))
        self.document_paths[original_ref['path']] = name

    def json_document(self, original_ref, destination, info, *, outcome=False, aliases=None):
        raw = self.reader.read_bytes(original_ref['path'])
        if digest(raw) != original_ref['sha256']: raise ValueError('Original report pin differs')
        original = strict_json(raw); value, admission = present_value(original, outcome=outcome)
        if not isinstance(value, dict): raise ValueError('Recorded report object required')
        neutral, proof = m.neutralize(value, aliases)
        path = self.work / ('derived-%05d.json' % len(self.derivations))
        write(path, encoded(neutral))
        self.derivations.append({'original': original_ref, 'derived': ref(self.reader, path),
            'anonymous_relative': destination, 'projection': proof, 'emitter_admission': admission,
            'outer_fact_selection': {'kind': 'fixed-operation-outcome-fields',
                'retained': list(value), 'omitted': [k for k in original if k not in value]} if outcome else None})
        self.exact(ref(self.reader, path), destination, dict(info, raw_original_sha256=original_ref['sha256']))
        self.document_paths[original_ref['path']] = relative(destination).as_posix()

    def sources(self, required, workspace_roots, candidates):
        content = required['content_sha256']
        if digest(json_text(required['files'], sort_keys=True).encode()) != content:
            raise ValueError('Original controller full-capsule source identity differs')
        if not isinstance(required['files'], dict) or not required['files']:
            raise ValueError('Nonempty original full-capsule source map required')
        for rel, expected in required['files'].items():
            relative(rel)
            if (not isinstance(expected, dict) or set(expected) != {'sha256', 'bytes'}
                    or not isinstance(expected['sha256'], str) or len(expected['sha256']) != 64
                    or any(c not in '0123456789abcdef' for c in expected['sha256'])
                    or type(expected['bytes']) is not int or expected['bytes'] < 0):
                raise ValueError('Exact source member SHA and bytes required')
            root_index, tail = rel.split('/', 1)
            if str(int(root_index)) != root_index or not 0 <= int(root_index) < len(workspace_roots):
                raise ValueError('Original full-capsule root index differs')
        if content not in self.versions:
            name = 'v%d' % len(self.versions); aliases = {}; missing = []
            for i, (rel, expected) in enumerate(sorted(required['files'].items())):
                relative(rel); match = candidates.get((rel, expected['sha256'], expected['bytes']))
                if match is None:
                    missing.append({'relative': rel, **expected}); continue
                actual = self.reader.read_bytes(str(match))
                if digest(actual) != expected['sha256'] or len(actual) != expected['bytes']:
                    raise ValueError('Supporting exact original source bytes differ')
                destination = 'sources/' + name + '/' + rel
                self.exact(ref(self.reader, match), destination,
                           {'kind': 'source', 'source_version': content, 'relative': rel})
                if self.reader.hash(str(match)) != expected['sha256']:
                    raise ValueError('Supporting original source member changed')
                root_index, tail = rel.split('/', 1)
                aliases[str(Path(workspace_roots[int(root_index)]) / tail)] = destination
            self.versions[content] = name; self.aliases[content] = aliases
            self.description['versions'].append({'id': name, 'controller_content_sha256': content,
                 'source_member_count': len(required['files']), 'missing_original_members': missing,
                 'source_scope': 'Original full-controller capsule; selected-platform native hashes have a separate domain. A missing intermediate member is unavailable, never replaced by current source.'})
        # Identical initial bytes occur in both public roots. Their original
        # citation paths still need separate exact aliases to the same bytes.
        for rel, expected in required['files'].items():
            if (rel, expected['sha256'], expected['bytes']) in candidates:
                root_index, tail = rel.split('/', 1)
                self.aliases[content][str(Path(workspace_roots[int(root_index)]) / tail)] = (
                    'sources/' + self.versions[content] + '/' + rel)
        for index, root in enumerate(workspace_roots):
            if not m._path(root):
                raise ValueError('Canonical original workspace root required')
            self.aliases[content][root] = 'sources/' + self.versions[content] + '/' + str(index)
        return content

    def operation_aliases(self, outcome, config_ref, source_version):
        aliases = dict(self.metadata_aliases); aliases.update(self.aliases[source_version])
        def references(item):
            if isinstance(item, dict):
                if ('path' in item and 'sha256' in item and m._path(item['path'])
                        and isinstance(item['sha256'], str) and len(item['sha256']) == 64):
                    aliases[item['path']] = self.document_paths.get(item['path'], 'record-ref-' + digest(item['path'].encode())[:24])
                for value in item.values(): references(value)
            elif isinstance(item, list):
                for value in item: references(value)
        references(outcome); references(config_ref)
        return aliases

    def operation(self, outcome_ref, episode, source, config_ref, candidates, visibility, attempt_origins=None):
        outcome = pinned(self.reader, outcome_ref); config = pinned(self.reader, config_ref)
        version = self.sources(source, config['source_roots'], candidates)
        profile = outcome['profile']; base = 'episodes/' + episode + '/' + profile
        if profile not in {'ios', 'android'}:
            raise ValueError('Original own platform profile required')
        info = {'episode': episode, 'platform': profile, 'source_version': version, 'visibility': visibility}
        if attempt_origins is not None: info['attempt_origins'] = list(attempt_origins)
        aliases = self.operation_aliases(outcome, config_ref, version)
        inventory_ref = outcome.get('inventory')
        if inventory_ref:
            inventory = pinned(self.reader, inventory_ref); service = Path(outcome['service_output'])
            if not isinstance(inventory, dict): raise ValueError('Explicit original service inventory required')
            for original in inventory:
                p = Path(original)
                if not m._path(original) or not p.is_relative_to(service):
                    raise ValueError('Original service inventory escapes its namespace')
                rel = p.relative_to(service).as_posix()
                if inventory_kind(rel) == 'report': aliases[original] = base + '/reports/' + rel
        capture_ref = outcome.get('capture')
        if capture_ref:
            receipt = pinned(self.reader, capture_ref); key = capture_ref['sha256']
            prefix = self.captures[key]['prefix'] if key in self.captures else 'captures/n%d/native' % len(self.captures)
            native = Path(capture_ref['path']).parent / 'native'; obs = native / 'observation.json'
            aliases[str(obs)] = prefix + '/observation.json'
            for rel in receipt.get('image_hashes', {}):
                aliases[str(native / relative(rel))] = prefix + '/' + rel
        self.metadata_aliases.update(aliases)
        self.json_document(outcome_ref, base + '/outcome.json', dict(info, kind='operation-result'), outcome=True, aliases=aliases)
        entry = dict(info, outcome=base + '/outcome.json', action=outcome.get('action'), capture=None)
        if inventory_ref:
            inventory = pinned(self.reader, inventory_ref); service = Path(outcome['service_output'])
            if not isinstance(inventory, dict): raise ValueError('Explicit original service inventory required')
            selected_names = set()
            for original in inventory:
                p = Path(original)
                if not m._path(original) or not p.is_relative_to(service):
                    raise ValueError('Original service inventory escapes its namespace')
                selected_names.add(p.relative_to(service).as_posix())
            if namespace(self.reader, service) != selected_names:
                raise ValueError('Original service inventory membership differs; no silent report drop')
            for original, row in sorted(inventory.items()):
                p = Path(original)
                if not p.is_relative_to(service): raise ValueError('Original service inventory escapes its namespace')
                if isinstance(row, dict) and (set(row) != {'sha256', 'bytes'} or type(row['bytes']) is not int or row['bytes'] < 0):
                    raise ValueError('Unreviewed original inventory row')
                expected = row if isinstance(row, str) else row['sha256']
                if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
                    raise ValueError('Exact original inventory SHA required')
                rel = p.relative_to(service).as_posix()
                kind = inventory_kind(rel)
                if kind == 'report':
                    if isinstance(row, dict) and len(self.reader.read_bytes(original)) != row['bytes']:
                        raise ValueError('Original report byte count differs')
                    destination = base + '/reports/' + p.relative_to(service).as_posix()
                    self.json_document({'path': original, 'sha256': expected}, destination,
                                       dict(info, kind='original-service-report'), aliases=aliases)
                elif kind == 'native-observation' and not capture_ref:
                    raise ValueError('Unbound partial native observation requires prospective presentation review')
        if capture_ref:
            if key not in self.captures:
                images = receipt.get('image_hashes', {})
                try: native_names = namespace(self.reader, native)
                except FileNotFoundError:
                    if images or receipt.get('observation_sha256'): raise
                    native_names = set()
                if not isinstance(images, dict) or {name for name in native_names if name.lower().endswith('.png')} != set(images):
                    raise ValueError('Original PNG inventory differs')
                if receipt.get('observation_sha256'):
                    observation_ref = {'path': str(obs), 'sha256': receipt['observation_sha256']}
                    observation = pinned(self.reader, observation_ref)
                    if not isinstance(observation.get('snapshots'), list):
                        raise ValueError('Unreviewed original native snapshot layout')
                    for snap in observation['snapshots']:
                        if 'screenshot' in snap and relative(snap['screenshot']).as_posix() not in images:
                            raise ValueError('Original snapshot does not bind a declared PNG')
                    for snap in observation.get('coverage_screenshots', {}).values():
                        if snap.get('screenshot') and relative(snap['screenshot']).as_posix() not in images:
                            raise ValueError('Original coverage snapshot does not bind a declared PNG')
                    self.json_document(observation_ref, prefix + '/observation.json',
                                       dict(info, kind='original-native-observation'), aliases=aliases)
                    self.captures[key] = {'prefix': prefix, 'observation': prefix + '/observation.json',
                         'native_source_sha256': receipt.get('source_sha256'),
                         'native_source_model_sha256': receipt.get('source_model_sha256'),
                         'first_supplied_full_source_version': version,
                         'original_capture_sha256': key}
                else:
                    self.captures[key] = {'prefix': prefix, 'observation': None, 'availability': 'Original operation has no pinned native observation', 'original_capture_sha256': key}
                self.captures[key]['images'] = []
                for rel, expected in images.items():
                    safe = relative(rel)
                    self.exact({'path': str(native / safe), 'sha256': expected}, prefix + '/' + rel,
                               dict(info, kind='original-native-image'))
                    self.captures[key]['images'].append({'path': prefix + '/' + rel, 'sha256': expected})
            entry['capture'] = self.captures[key]
        else: entry['availability'] = 'Original operation retained no capture reference; no native pass is inferred.'
        self.description['episodes'].append(entry)

    def prepare(self):
        own = 'A' if self.initial else self.arm
        source_folders = [self.run / f'arms/{self.task}/{own}/initial', self.run / f'arms/{self.task}/{own}/final-source']
        candidates, sources = {}, []
        for folder in source_folders:
            source_path = folder / 'source.json'
            if self.native_read_pins.get(str(source_path)) != self.reader.hash(str(source_path)):
                raise ValueError('Supporting source capsule is not in the independently verified chain')
            source = self.original(source_path); sources.append(source)
            for rel, row in source['files'].items():
                p = folder / 'files' / relative(rel)
                if self.reader.hash(str(p)) != row['sha256'] or len(self.reader.read_bytes(str(p))) != row['bytes']:
                    raise ValueError('Original own source capsule member differs')
                candidates[(rel, row['sha256'], row['bytes'])] = p
        requests = [e for e in self.events if e['kind'] == 'request_enqueued' and e.get('task') == self.task
                    and (e.get('action') == 'diagnostic' if self.initial else e.get('arm') == own)]
        requests.sort(key=lambda e: e['sequence'])
        if self.initial:
            first = {a: next(e for e in requests if e['arm'] == a) for a in ['A', 'B']}
            requests = sorted(first.values(), key=lambda e: e['sequence'])
        else:
            seals = [e for e in self.events if e['kind'] == 'self_sealed' and e.get('task') == self.task and e.get('arm') == own]
            if len(seals) != 1 or seals[0].get('source_sha256') != sources[-1]['content_sha256']:
                raise ValueError('Unique original self-seal/final source binding required')
            sealed = seals[0]
            if any(e['sequence'] > sealed['sequence'] for e in requests): raise ValueError('Public request occurred after original self-seal')
        for i, event in enumerate(requests):
            request_path = self.run / 'requests' / event['request_id']; request = event
            terminal = next(e for e in self.events if e['kind'] == 'request_finished'
                            and e.get('request_id') == event['request_id'])
            result = pinned(self.reader, {'path': terminal['result_path'], 'sha256': terminal['result_sha256']})
            if (any(result.get(k) != event[k] for k in ['task', 'arm', 'request_id'])
                    or terminal.get('task') != event['task'] or terminal.get('arm') != event['arm']
                    or not isinstance(result.get('outcomes'), list)
                    or len(result['outcomes']) != len(event['profiles'])
                    or {row.get('profile') for row in result['outcomes']} != set(event['profiles'])):
                raise ValueError('Original public event/result scope or profile inventory differs')
            label = 'public-%03d' % i
            for platform in request['profiles']:
                path = request_path / platform / 'outcome.json'
                row = next(item for item in result['outcomes'] if item['profile'] == platform)
                if json_text(row, sort_keys=True) != json_text(self.original(path), sort_keys=True):
                    raise ValueError('Public outcome differs from its original event-pinned result')
                self.operation(ref(self.reader, path), label, event['source'], event['active_configs'][platform], candidates,
                               'common-initial-public' if self.initial else 'worker_public')
            if request.get('submission'):
                version = event['source']['content_sha256']
                self.json_document({'path': request['submission']['path'], 'sha256': request['submission']['sha256']},
                    'episodes/' + label + '/original-submission.json',
                    {'kind': 'original-worker-submission', 'episode': label, 'source_version': version,
                    'visibility': 'common-initial-public' if self.initial else 'worker_public'}, aliases={**self.metadata_aliases, **self.document_paths, **self.aliases[version]})
        scope = 'I' if self.initial else own; independent = self.root / 'cache/business/independent-evaluation'
        for platform in ['ios', 'android']:
            key = self.task + '/' + scope + '/' + platform
            effective = self.snapshot['terminal_records'][key]
            effective_outcome = pinned(self.reader, effective['outcome'])
            original_claim = independent / 'native-claims' / self.task / scope / (platform + '.json')
            claim = pinned(self.reader, chain_ref(self.reader, original_claim, self.native_read_pins))
            if any(claim.get(k) != expected for k, expected in [('task', self.task), ('arm', scope), ('profile', platform)]):
                raise ValueError('Original private claim belongs to another scope')
            original_outcome = Path(claim['record']) / 'outcome.json'
            refs = [('original', chain_ref(self.reader, original_outcome, self.native_read_pins))]
            entry_permit_ref = next((v for v in self.snapshot['anchors'].values()
                if Path(v['path']).name == 'UNCLAIMED-ENTRY-v3-ADMISSION.json'), None)
            if entry_permit_ref:
                entry_permit = pinned(self.reader, entry_permit_ref)['entry_resume']
                if entry_permit['scope'] == key:
                    refs.append(('licensed-entry-failure', entry_permit['failed_record_files']['outcome.json']))
            refs.append(('effective', effective['outcome']))
            unique = {}
            for origin, item in refs:
                key_ref = (item['path'], item['sha256'])
                if key_ref not in unique: unique[key_ref] = {'ref': item, 'origins': []}
                unique[key_ref]['origins'].append(origin)
            for i, selected in enumerate(unique.values()):
                item = selected['ref']
                if self.native_read_pins.get(item['path']) != item['sha256']:
                    raise ValueError('Private selected outcome is not in independently verified native chain')
                value = pinned(self.reader, item)
                if (any(value.get(k) != expected for k, expected in [('task', self.task), ('arm', scope), ('profile', platform)])
                        or value.get('source_capsule') != effective_outcome['source_capsule']
                        or value.get('config') != effective_outcome['config']):
                    raise ValueError('Original/effective private source/config/scope differs from the admitted continuation contract')
                source = pinned(self.reader, value['source_capsule'])
                self.operation(item, 'private-attempt-%d' % i, source, value['config'], candidates,
                               'independent_private_after_seal', attempt_origins=selected['origins'])
        if not self.initial:
            self.json_document({'path': sealed['claim_path'], 'sha256': sealed['claim_sha256']},
                'worker/self-claim.json', {'kind': 'original-worker-self-claim', 'visibility': 'worker_public',
                'source_version': sources[-1]['content_sha256']}, aliases={**self.metadata_aliases, **self.document_paths, **self.aliases[sources[-1]['content_sha256']]})


def prepare(root, reader, cause_ref, snapshot_ref, native_result_ref, output, work):
    # This precedes mapping, manifest, event, report, source and image reads.
    verified = verify_index(reader, cause_ref, 'cause')
    snapshot = pinned(reader, snapshot_ref); result = pinned(reader, native_result_ref)
    if (result.get('snapshot') != snapshot_ref or result.get('result', {}).get('status') != 'verified'
            or result['result'].get('acquired_scopes') != 30 or snapshot.get('original_root') != str(root)):
        raise ValueError('Externally pinned all30 native acquisition proof required')
    mapping_seal = pinned(reader, {'path': str(root / 'operators/cohort2/coordination/anonymous-map/SEAL.json'),
                                  'sha256': MAP_SEAL_SHA})
    mapping_path = root / 'operators/cohort2/coordination/anonymous-map/MAPPING.json'
    mapping = pinned(reader, {'path': str(mapping_path), 'sha256': mapping_seal['files']['MAPPING.json']})['mapping']
    if set(mapping) != {'Case0%d' % i for i in range(1, 6)}:
        raise ValueError('Exactly the five original anonymous cases required')
    if len({row['task'] for row in mapping.values()}) != 5 or any({row['X'], row['Y']} != {'A', 'B'} for row in mapping.values()):
        raise ValueError('Original five distinct tasks and paired versions required')
    manifest = pinned(reader, snapshot['anchors']['manifest'])
    run = root / 'cache/business/run-cohort2'
    event_root = run / 'events'; names = namespace(reader, event_root)
    expected = {str(Path(p).relative_to(event_root)) for p in result['files_read'] if Path(p).is_relative_to(event_root)}
    if names != expected or names != {'%06d.json' % i for i in range(len(names))}:
        raise ValueError('Complete original event namespace differs from verified acquisition; no silent request drop')
    events = []; previous = None
    for i, name in enumerate(sorted(names)):
        path = event_root / name
        if result['files_read'].get(str(path)) != reader.hash(str(path)):
            raise ValueError('Original public event differs from independently verified acquisition chain')
        event = reader.read_json(str(path))
        if event.get('sequence') != i or event.get('previous_sha256') != previous:
            raise ValueError('Original public event sequence/SHA chain differs')
        previous = result['files_read'][str(path)]; events.append(event)
    enqueued = [e['request_id'] for e in events if e['kind'] == 'request_enqueued']
    terminal = [e['request_id'] for e in events if e['kind'] == 'request_finished']
    if len(set(enqueued)) != len(enqueued) or len(set(terminal)) != len(terminal) or set(enqueued) != set(terminal):
        raise ValueError('Unique complete public request/terminal registry required')
    for event in events:
        if event['kind'] != 'request_enqueued': continue
        if (not isinstance(event['request_id'], str) or not event['request_id'] or
                any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in event['request_id'])
                or event.get('action') not in {'diagnostic', 'final', 'review-native', 'review-source', 'finish-review', 'retire'}
                or not isinstance(event.get('profiles'), list) or not event['profiles']
                or len(event['profiles']) != len(set(event['profiles'])) or not set(event['profiles']) <= {'ios', 'android'}):
            raise ValueError('Unreviewed original public request schema')
    output, work = _presentation['alarm_packet']._destination(output), _presentation['alarm_packet']._destination(work)
    if output == work or output in work.parents or work in output.parents:
        raise ValueError('Fresh disjoint selection and intermediate namespaces required')
    _presentation['alarm_packet']._fresh_directory(output); _presentation['alarm_packet']._fresh_directory(work)
    all_specs = []
    for version in ['I', 'X', 'Y']:
        for case in sorted(mapping):
            group = case + '-' + version; row = mapping[case]
            collector = Group(root, reader, group, row['task'], row[version], manifest, events, snapshot, result['files_read'], work)
            collector.prepare()
            spec = {'version': 1, 'kind': 'explicit-anonymous-alarm-material-spec', 'anonymous_group': group,
                    'first_cause_barrier': cause_ref, 'documents': collector.documents,
                    'anonymous_description': collector.description,
                    'instructions': ref(reader, root / 'business-quality-tools/ALARM-INSTRUCTIONS-v1.md'),
                    'grade_template': ref(reader, root / 'business-quality-tools/ALARM-GRADE-TEMPLATE-v1.json')}
            folder = output / group; folder.mkdir()
            write(folder / 'SPEC.json', encoded(spec)); write(folder / 'DERIVATIONS.json', encoded(collector.derivations))
            all_specs.append({'group': group, 'spec': ref(reader, folder / 'SPEC.json'),
                              'derivations': ref(reader, folder / 'DERIVATIONS.json')})
    value = {'version': 1, 'kind': 'all15-uniform-original-alarm-selection-seal', 'at_unix': time.time(),
             'original_root': str(root),
             'first_cause_barrier': cause_ref, 'groups': all_specs, 'closed_cause_contexts': verified['distinct_contexts'],
             'code_pins': code_pins(),
             'mapping_revealed_to_judges_or_model': False, 'quality_adjudicated': False}
    write(output / 'ALL-SPECS-SEAL.json', encoded(value))
    return ref(reader, output / 'ALL-SPECS-SEAL.json')


def verify_derivation(reader, row):
    if not isinstance(row, dict) or set(row) != {'original', 'derived', 'anonymous_relative', 'projection', 'emitter_admission', 'outer_fact_selection'}:
        raise ValueError('Exact original/derived composition proof required')
    original = pinned(reader, row['original'])
    value, admission = present_value(original, outcome=row['outer_fact_selection'] is not None)
    if admission != row['emitter_admission']:
        raise ValueError('Source-schema admission proof differs')
    if row['outer_fact_selection'] is not None:
        selected = {'kind': 'fixed-operation-outcome-fields', 'retained': list(value),
                    'omitted': [key for key in original if key not in value]}
        if selected != row['outer_fact_selection']:
            raise ValueError('Original outcome field selection differs')
    proof = row['projection']; rules = {}; pointers = []
    for change in proof['identity_metadata_changes']:
        pointers.append(change['pointer'])
        for rule in change['rules']:
            if rule['original'] in rules and rules[rule['original']] != rule:
                raise ValueError('Ambiguous recorded projection rule')
            rules[rule['original']] = rule
    projected, replayed = _presentation['anonymous_projection'].project(value,
        omit_top_level=list(proof['omitted_top_level']), replacements=list(rules.values()), rewrite_pointers=pointers)
    if replayed != proof or digest(encoded(projected)) != row['derived']['sha256']:
        raise ValueError('Exact raw-to-derived presentation proof differs')
    raw = reader.read_bytes(row['derived']['path'])
    if digest(raw) != row['derived']['sha256']:
        raise ValueError('Original derived bytes changed')


def package_selected(root, reader, selection_ref, packet_root, operator_root, summary_path=None):
    """Validate all15 selections/proofs before creating the first packet.

    This function prepares bytes only; no role dispatch exists here.
    """
    selected = pinned(reader, selection_ref)
    expected = {'Case0%d-%s' % (i, version) for i in range(1, 6) for version in ['I', 'X', 'Y']}
    if (selected.get('kind') != 'all15-uniform-original-alarm-selection-seal'
            or type(selected.get('version')) is not int or selected['version'] != 1
            or not isinstance(selected.get('groups'), list) or len(selected['groups']) != 15
            or {row['group'] for row in selected['groups']} != expected or selected.get('code_pins') != code_pins()
            or selected.get('original_root') != str(root)
            or selected.get('mapping_revealed_to_judges_or_model') is not False or selected.get('quality_adjudicated') is not False):
        raise ValueError('Complete same-revision all15 selection seal required')
    verified = verify_index(reader, selected['first_cause_barrier'], 'cause')
    if selected.get('closed_cause_contexts') != verified['distinct_contexts']:
        raise ValueError('Selection cause barrier count differs')
    ready = []
    for row in selected['groups']:
        spec = pinned(reader, row['spec']); derivations = pinned_value(reader, row['derivations'])
        if (spec.get('version') != 1 or spec.get('kind') != 'explicit-anonymous-alarm-material-spec'
                or spec.get('anonymous_group') != row['group'] or spec.get('first_cause_barrier') != selected['first_cause_barrier']
                or spec.get('anonymous_description', {}).get('anonymous_group') != row['group']
                or not isinstance(derivations, list)):
            raise ValueError('Selection row/spec/group/cause binding differs')
        descriptions = spec['anonymous_description'].get('documents', [])
        if len(descriptions) != len(spec['documents']) or {d['path'] for d in descriptions} != {d['anonymous_relative'] for d in spec['documents']}:
            raise ValueError('Selected material manifest omits or duplicates a document')
        by_name = {d['anonymous_relative']: d for d in spec['documents']}
        if len(by_name) != len(spec['documents']): raise ValueError('Duplicate selected packet document')
        descriptions = {d['path']: d for d in descriptions}; derived_names = set()
        for derivation in derivations:
            verify_derivation(reader, derivation)
            name = derivation['anonymous_relative']
            if (name in derived_names or name not in by_name or by_name[name]['original'] != derivation['derived']
                    or descriptions[name].get('raw_original_sha256') != derivation['original']['sha256']):
                raise ValueError('Derived material is not bound to the selected packet document')
            derived_names.add(name)
        if {name for name, info in descriptions.items() if 'raw_original_sha256' in info} != derived_names:
            raise ValueError('Missing original derivation proof')
        for document in spec['documents']:
            _presentation['alarm_packet'].member(document['anonymous_relative'])
            raw = reader.read_bytes(document['original']['path'])
            if digest(raw) != document['original']['sha256']:
                raise ValueError('All15 selected material bytes must verify before packaging')
        for key, name in [('instructions', 'ALARM-INSTRUCTIONS-v1.md'), ('grade_template', 'ALARM-GRADE-TEMPLATE-v1.json')]:
            if spec[key] != ref(reader, root / 'business-quality-tools' / name):
                raise ValueError('Uniform original instruction/template binding differs')
        ready.append((row, spec))
    packet_root, operator_root = _presentation['alarm_packet']._destination(packet_root), _presentation['alarm_packet']._destination(operator_root)
    if packet_root == operator_root or packet_root in operator_root.parents or operator_root in packet_root.parents:
        raise ValueError('Fresh disjoint packet and operator namespaces required')
    _presentation['alarm_packet']._fresh_directory(packet_root); _presentation['alarm_packet']._fresh_directory(operator_root)
    write(operator_root / 'ALL15-PREFLIGHT.json', encoded({'version': 1, 'selection_seal': selection_ref,
          'groups': [row['group'] for row, _ in ready], 'all_raw_derived_and_document_pins_verified': True,
          'code_pins': code_pins(), 'quality_adjudicated': False, 'phase2_dispatched': False}))
    summaries = []
    for row, spec in ready:
        group = row['group']
        summary = build(reader, spec, packet_root / group, operator_root / group)
        summaries.append({'group': group, **summary})
    result = {'version': 1, 'groups': summaries, 'selection_seal': selection_ref,
              'code_pins': code_pins(), 'phase2_dispatched': False,
              'scope': 'All15 original selections/proofs verified before packaging; no quality or reveal.'}
    if summary_path is not None: write(summary_path, encoded(result))
    return result


def pinned_value(reader, value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('Exact original reference required')
    raw = reader.read_bytes(value['path'])
    if digest(raw) != value['sha256']: raise ValueError('Original pinned bytes differ')
    return strict_json(raw)


def main():
    p = argparse.ArgumentParser(); p.add_argument('command', choices=['prepare', 'build'])
    p.add_argument('--root', type=Path, required=True); p.add_argument('--id', required=True)
    for name in ['cause-index', 'native-snapshot', 'native-result', 'selection-seal']:
        p.add_argument('--' + name); p.add_argument('--' + name + '-sha256')
    a = p.parse_args(); root = a.root.resolve()
    if not a.id.isascii() or not a.id.replace('-', '').isalnum(): raise ValueError('Simple unique preparation ID required')
    reader = LiveReader(root); output = root / 'operators/cohort2/coordination/alarm-material-selections' / a.id
    try:
        if a.command == 'prepare':
            refs = [{ 'path': getattr(a, name), 'sha256': getattr(a, name + '_sha256')}
                    for name in ['cause_index', 'native_snapshot', 'native_result']]
            answer = prepare(root, reader, *refs, output,
                root / 'cache/business/blind-quality/alarm-intermediates' / a.id)
            print(json.dumps({'selection_seal': answer, 'groups': 15, 'quality_adjudicated': False}))
        else:
            answer = package_selected(root, reader, {'path': a.selection_seal, 'sha256': a.selection_seal_sha256},
                root / 'cache/business/blind-quality/alarm-packets' / a.id, output / 'packaging', output / 'ALL-PACKETS-SEAL.json')
            print(json.dumps({'groups': len(answer['groups']), 'packets_seal': ref(reader, output / 'ALL-PACKETS-SEAL.json')}))
    except BaseException as error:
        output.mkdir(parents=True, exist_ok=True)
        failure = output / ('FAILED-' + str(time.time_ns()) + '.json')
        write(failure, encoded({'version': 1, 'error': {'type': type(error).__name__, 'message': str(error)},
              'traceback': traceback.format_exc(), 'quality_adjudicated': False, 'phase2_dispatched': False}))
        raise


if __name__ == '__main__': main()
