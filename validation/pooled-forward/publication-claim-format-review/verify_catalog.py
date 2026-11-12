"""Pure format/byte/span checker; semantics are explicit reviewed DATA only.

No locator target is resolved/read/statted, no actual projection is performed,
and no evidence validity, product quality or assignment is inferred.
"""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata

BLOCKED = {'actual', 'expected', 'observed', 'rendered', 'measured', 'payload',
           'text', 'value', 'label', 'callback', 'event', 'actualfilepath'}
META = {'claimed_provenance_locator', 'execution_identity_metadata'}
PROBES = {
    'reviewed_identity_detector': re.compile(r'baseline-v12|candidate-v13|stateful-default|baseline-explicit-prior|/Users/rex/|/Library/Developer/|/business/T[1-5]/[AB]/|run-cohort2/(?:arms|requests)/'),
    'generic_machine_locator': re.compile(r'/(?:Users|home)/[^/\s]+/|/Library/Developer/'),
    'execution_or_engine_token': re.compile(r'(?i)baseline[-_][a-z0-9.-]+|candidate[-_][a-z0-9.-]+|stateful-default|baseline-explicit-prior|run-cohort[0-9]+'),
    'short_assignment_token': re.compile(r'^(?:T[1-5](?:[-_/ ][AB])?|[AB])$'),
    'opaque_identity_token': re.compile(r'^[a-f0-9]{32}$'),
}


def need(value, message):
    if not value:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def location_sha256(location):return sha(canonical(location))


def parse(raw):
    def pairs(rows):
        out = {}
        for key, value in rows:
            need(key not in out, 'Duplicate JSON key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def normalize(name):return re.sub('[^a-z0-9]', '', name.casefold())


def parts(pointer):
    need(isinstance(pointer, str) and pointer.startswith('/') and not re.search(r'~(?![01])', pointer), 'Canonical non-root RFC6901 pointer required')
    return [s.replace('~1', '/').replace('~0', '~') for s in pointer[1:].split('/')]


def pointer(path):return ''.join('/'+str(p).replace('~', '~0').replace('/', '~1') for p in path)


def blocked(pointer_value):return any(normalize(p) in BLOCKED for p in parts(pointer_value))


def resolve(value, pointer_value, member_kind='string_value'):
    route = parts(pointer_value)
    current = value
    for i, part in enumerate(route):
        if member_kind == 'object_key' and i == len(route)-1:
            need(isinstance(current, dict) and part in current, 'Object-key location absent')
            return part
        if isinstance(current, list):
            need(re.fullmatch('0|[1-9][0-9]*', part) is not None, 'Noncanonical array pointer')
            current = current[int(part)]
        elif isinstance(current, dict):current = current[part]
        else:raise ValueError('Pointer crosses scalar')
    return current


def kind(value):
    if value is None:return 'null'
    if type(value) is bool:return 'boolean'
    if isinstance(value, dict):return 'object'
    if isinstance(value, list):return 'array'
    if isinstance(value, str):return 'string'
    return 'number'


def canonical_path(value):
    # Lexical only: no target lookup, existence, resolve or stat call.
    if not isinstance(value, str) or not value.startswith('/') or '\\' in value or any(unicodedata.category(c).startswith('C') for c in value):return False
    p = PurePosixPath(value)
    return str(p) == value and '..' not in p.parts


def inventory(value):
    strings, keys, scalar_types, containers = [], [], {}, []
    def entry(text, route, parent, member_kind):
        probes = []
        for name, expression in PROBES.items():
            matches = [{'start': m.start(), 'end': m.end(), 'matched_utf8_sha256': sha(m.group().encode('utf-8'))} for m in expression.finditer(text)]
            if matches:probes.append({'probe': name, 'matches': matches})
        shape = ({k: kind(v) for k, v in parent.items()} if isinstance(parent, dict)
                 else {'array_member_types': sorted({kind(v) for v in parent})} if isinstance(parent, list) else None)
        return {'pointer': pointer(route), 'member_kind': member_kind, 'parent_pointer': pointer(route[:-1]),
                'original_value_sha256': sha(json.dumps(text, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')),
                'original_utf8_sha256': sha(text.encode('utf-8')), 'codepoint_length': len(text), 'utf8_length': len(text.encode('utf-8')),
                'canonical_absolute_path': canonical_path(text), 'parent_shape': shape, 'identity_probes': probes}
    def walk(item, route, parent=None):
        if isinstance(item, dict):
            containers.append({'pointer': pointer(route), 'kind': 'object', 'members': {k: kind(v) for k, v in item.items()}})
            for key, sub in item.items():
                keys.append(entry(key, route+[key], item, 'key'));walk(sub, route+[key], item)
        elif isinstance(item, list):
            containers.append({'pointer': pointer(route), 'kind': 'array', 'length': len(item), 'member_types': sorted({kind(v) for v in item})})
            for index, sub in enumerate(item):walk(sub, route+[index], item)
        else:
            scalar_types[pointer(route)] = kind(item)
            if isinstance(item, str):strings.append(entry(item, route, parent, 'value'))
    walk(value, [])
    return {'strings': strings, 'keys': keys, 'scalar_types': scalar_types, 'containers': containers}


def reference(ref):
    need(type(ref) is dict and set(ref) == {'path', 'sha256'} and canonical_path(ref['path'])
         and isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'Exact original path/SHA reference required')
    return ref


def pinned(reader, ref):
    reference(ref);raw = reader.read_bytes(ref['path'])
    need(sha(raw) == ref['sha256'], 'Original byte pin differs')
    return parse(raw)


def location_key(ref, pointer_value, member_kind):
    reference(ref);parts(pointer_value)
    need(member_kind in {'string_value', 'object_key'}, 'Unknown location member kind')
    return (ref['path'], ref['sha256'], pointer_value, member_kind)


def validate_location(location, original_value):
    text = resolve(original_value, location['pointer'], location['member_kind'])
    need(isinstance(text, str), 'Exact location is not a string')
    need(sha(text.encode('utf-8')) == location['original_utf8_sha256'] == location['original_value_sha256'], 'Original scalar UTF8 hash differs')
    need(sha(json.dumps(text, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) == location['original_json_string_sha256']
         and len(text) == location['codepoint_length'], 'Original JSON-string hash/codepoint extent differs')
    boundaries = [p for p in parts(location['pointer']) if normalize(p) in BLOCKED]
    need(boundaries == location['protected_boundary_names'], 'Protected boundary declaration differs')
    need(location['reference_validated'] is False and location['evidence_credit'] is False
         and location['projection_authorized'] is False and location['whole_container_metadata_permission'] is False,
         'Responsibility cannot grant validity, evidence, projection or container permission')
    if location['classification'] in META:
        need(not boundaries and location['contains_prose'] is False and location['member_kind'] == 'string_value', 'Protected/key/prose location cannot receive this scalar metadata approval')
        expected_kind = 'complete_canonical_locator' if canonical_path(text) else 'complete_execution_identifier'
        if location['classification'] == 'claimed_provenance_locator':need(canonical_path(text), 'Claimed locator must be a complete canonical locator')
        elif not canonical_path(text):
            need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', text) is not None, 'Execution scalar is not an unambiguous complete identifier')
        need(location['identity_spans'] == [{'start': 0, 'end': len(text), 'unit': 'unicode_codepoint',
             'original_utf8_sha256': sha(text.encode('utf-8')), 'span_kind': expected_kind}], 'Exact whole-scalar Unicode-codepoint span required')
    return text


def audit(reader, catalog_ref, inspection_ref, survey_ref):
    catalog, inspection, survey = (pinned(reader, r) for r in [catalog_ref, inspection_ref, survey_ref])
    need(catalog['survey_ref'] == inspection['survey_ref'] == survey_ref, 'Survey binding differs')
    refs = survey['claim_refs']
    need(len(refs) == 10 and len({r['path'] for r in refs}) == 10
         and [d['original_ref'] for d in catalog['documents']] == refs
         and [d['original_ref'] for d in inspection['documents']] == refs, 'All ten original documents required in exact surveyed order')
    need(set(catalog['unconditional_blocked_normalized_names']) == BLOCKED, 'Unconditional blocked names differ')
    totals = Counter();classes = Counter();coverage = [];location_keys = set()
    for ordinal, (doc, inspected, original_ref) in enumerate(zip(catalog['documents'], inspection['documents'], refs), 1):
        raw = reader.read_bytes(original_ref['path']);need(sha(raw) == original_ref['sha256'], 'Original document changed before audit')
        value = parse(raw);need(isinstance(value, dict), 'Original SELFCLAIM root must be an object')
        actual = inventory(value)
        need(doc['document_ordinal'] == inspected['document_ordinal'] == ordinal and inspected['original_size_bytes'] == len(raw), 'Document ordinal/size differs')
        for field in ['strings', 'keys', 'scalar_types', 'containers']:
            need(actual[field] == inspected[field], 'Complete independent inventory differs: '+field)
        candidates = {(x['pointer'], member): x for field, member in [('strings', 'string_value'), ('keys', 'object_key')]
                      for x in actual[field] if x['identity_probes']}
        declared = {(x['pointer'], x['member_kind']): x for x in doc['locations']}
        need(len(declared) == len(doc['locations']) and set(declared) == set(candidates), 'Exact unfiltered discovered identity coverage required')
        for key, location in declared.items():
            need(location['original_ref'] == original_ref, 'Location original document differs')
            uid = location_key(original_ref, *key);need(uid not in location_keys, 'Duplicate original location');location_keys.add(uid)
            validate_location(location, value)
            item = candidates[key]
            need(location['parent_pointer'] == item['parent_pointer'] and location['parent_shape_only'] == item['parent_shape'], 'Original parent structure differs')
            classes[location['classification']] += 1
        for note in doc['mixed_container_responsibility_notes']:
            container = resolve(value, note['pointer'])
            need(isinstance(container, (dict, list)) and note['whole_container_projection_permission'] is False, 'Mixed container cannot inherit metadata permission')
        need(sha(reader.read_bytes(original_ref['path'])) == original_ref['sha256'], 'Original document changed after audit')
        counts = {'strings': len(actual['strings']), 'keys': len(actual['keys']), 'locations': len(declared),
                  'key_locations': sum(k[1] == 'object_key' for k in declared)}
        totals.update(counts);coverage.append({'document_ordinal': ordinal, 'original_ref': original_ref, 'counts': counts, 'unchanged_before_after': True})
    expected = catalog['coverage_counts']
    need(totals['strings'] == expected['string_values_inventoried'] and totals['keys'] == expected['object_keys_inventoried']
         and totals['locations'] == expected['cataloged_locations'] == expected['detected_identity_locations']
         and totals['key_locations'] == expected['classified_object_key_locations']
         and dict(classes) == {k: v for k, v in expected['classifications'].items() if v}, 'Catalogue aggregate coverage differs')
    return {'kind': 'independent-full-selfclaim-format-coverage-verification', 'documents': len(refs), 'counts': dict(totals),
            'classifications': dict(classes), 'document_coverage': coverage, 'all_originals_reverified_unchanged': True,
            'referenced_targets_read_resolved_or_statted': False, 'projection_performed': False,
            'scope': 'Format/byte/span/structure only; metadata role is separately reviewed DATA and carries no validity, evidence or product credit.'}


def validate_approval(catalog, approval):
    need(set(approval) == {'version', 'kind', 'catalog_seal', 'catalog_ref', 'original_document_refs', 'approved_locations',
                          'unapproved_locations', 'all_originals_reverified_unchanged', 'scope_limits'}, 'Exact approval DATA contract required')
    need(type(approval['version']) is int and approval['version'] == 1
         and approval['kind'] == 'independent-worker-claim-metadata-responsibility-approval'
         and approval['all_originals_reverified_unchanged'] is True and isinstance(approval['scope_limits'], list) and approval['scope_limits'], 'Wrong/incomplete independent approval')
    reference(approval['catalog_ref']);reference(approval['catalog_seal'])
    need(approval['original_document_refs'] == [d['original_ref'] for d in catalog['documents']], 'Approval original document refs differ')
    all_locations = {location_key(x['original_ref'], x['pointer'], x['member_kind']): x for d in catalog['documents'] for x in d['locations']}
    need(len(all_locations) == sum(len(d['locations']) for d in catalog['documents']), 'Duplicate catalogue locations')
    seen = set();approved = {}
    for approved_flag, rows in [(True, approval['approved_locations']), (False, approval['unapproved_locations'])]:
        need(isinstance(rows, list), 'Explicit approval partition required')
        for row in rows:
            need(set(row) == {'original_ref', 'pointer', 'member_kind', 'location_sha256'}, 'Exact location approval reference required')
            key = location_key(row['original_ref'], row['pointer'], row['member_kind'])
            need(key in all_locations and key not in seen, 'Unknown/duplicate approval location');seen.add(key)
            location = all_locations[key]
            need(row['location_sha256'] == location_sha256(location), 'Entire exact catalogue location hash differs')
            if approved_flag:
                need(location['classification'] in META and not blocked(row['pointer']) and location['contains_prose'] is False
                     and row['member_kind'] == 'string_value' and location['whole_container_metadata_permission'] is False
                     and all(location[x] is False for x in ['reference_validated', 'evidence_credit', 'projection_authorized']), 'Uncertain/proposition/protected/key/prose location cannot be approved')
                approved[key] = copy.deepcopy(location)
    need(seen == set(all_locations), 'Approval must account for every catalogued location without selective filtering')
    return approved


def verify_contract(reader, approval_ref, expected_catalog_seal):
    """Externally pinned approval/catalog binding before generic-lens consumption.

    Performs no projection; the returned approved map is only responsibility
    DATA. Its caller must separately admit any lens or substitution mechanism.
    """
    approval = pinned(reader, approval_ref)
    need(approval['catalog_seal'] == expected_catalog_seal, 'External catalogue authority differs')
    seal = pinned(reader, expected_catalog_seal)
    need(type(seal.get('version')) is int and seal['version'] == 1
         and seal['kind'] == 'independent-selfclaim-format-responsibility-catalog-seal', 'Wrong catalogue seal')
    manifest = {r['path']: r for r in seal['artifact_manifest']}
    need(len(manifest) == len(seal['artifact_manifest']) and approval['catalog_ref']['path'] in manifest
         and approval['catalog_ref']['sha256'] == manifest[approval['catalog_ref']['path']]['sha256'], 'Catalogue ref differs from external seal')
    catalog = pinned(reader, approval['catalog_ref'])
    need(catalog['kind'] == 'sealed-selfclaim-format-responsibility-data-catalog' and type(catalog.get('version')) is int and catalog['version'] == 1, 'Wrong catalogue DATA')
    inspection_path = str(PurePosixPath(approval['catalog_ref']['path']).with_name('INSPECTION.json'))
    need(inspection_path in manifest, 'Full inventory is missing from catalogue seal')
    inspected_ref = {'path': inspection_path, 'sha256': manifest[inspection_path]['sha256']}
    verification = audit(reader, approval['catalog_ref'], inspected_ref, catalog['survey_ref'])
    approved = validate_approval(catalog, approval)
    return verification, approved


class ExactReader:
    """Owned byte copies plus ten explicitly registered raw originals, no fallback."""
    def __init__(self, root, entries):self.root, self.entries, self.reads = Path(root), entries, []
    def read_bytes(self, original):
        need(original in self.entries, 'Read outside explicit authorized input set')
        row = self.entries[original]
        if 'copy' in row:
            rel = PurePosixPath(row['copy']);need(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe owned copy path')
            path = self.root.joinpath(*rel.parts)
        else:
            need(row.get('authorized_raw_original') is True, 'Raw original access was not declared')
            path = Path(original)
        before = path.lstat();need(stat.S_ISREG(before.st_mode), 'Regular explicit input required')
        raw = path.read_bytes();after = path.lstat()
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and sha(raw) == row['sha256'], 'Explicit input changed')
        self.reads.append(original)
        return raw
