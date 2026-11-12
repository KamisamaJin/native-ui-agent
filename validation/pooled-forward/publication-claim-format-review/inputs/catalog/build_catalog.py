#!/usr/bin/env python3
"""Compile exact-pointer responsibility DATA and validate format only.

No document container names, case selection, claim grading or projector is here.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
CLASSES = {'claimed_provenance_locator', 'execution_identity_metadata',
           'actual_or_proposition', 'uncertain'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('Duplicate JSON member')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _v: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def read_json(path):
    return decode_json(path.read_bytes())


def parts(pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/') or re.search(r'~(?![01])', pointer):
        raise ValueError('Canonical RFC6901 non-root pointer required')
    return [part.replace('~1', '/').replace('~0', '~') for part in pointer[1:].split('/')]


def resolve(value, pointer, member_kind):
    path = parts(pointer)
    item = value
    for index, part in enumerate(path):
        if member_kind == 'object_key' and index == len(path) - 1:
            if not isinstance(item, dict) or part not in item:
                raise ValueError('Key pointer absent')
            return part
        if isinstance(item, list):
            if not re.fullmatch(r'0|[1-9][0-9]*', part):
                raise ValueError('Canonical array index required')
            item = item[int(part)]
        elif isinstance(item, dict):
            item = item[part]
        else:
            raise ValueError('Pointer crosses scalar')
    return item


def normalized(value):
    return re.sub('[^a-z0-9]', '', value.casefold())


def main():
    inspection = read_json(HERE / 'INSPECTION.json')
    reasons = read_json(HERE / 'RESPONSIBILITY-REASONS.json')
    survey_ref = inspection['survey_ref']
    survey_raw = Path(survey_ref['path']).read_bytes()
    if sha(survey_raw) != survey_ref['sha256']:
        raise ValueError('Survey input changed')
    if decode_json(survey_raw)['claim_refs'] != [doc['original_ref'] for doc in inspection['documents']]:
        raise ValueError('Inventory original refs differ from externally pinned survey')
    for ref in inspection['reference_source_refs']:
        if sha(Path(ref['path']).read_bytes()) != ref['sha256']:
            raise ValueError('Authorized process-reference source changed')
    if reasons['span_policy'] != {
            'range_unit': 'unicode_codepoint', 'listed_locations_are_complete_identity_scalars': True,
            'range': '[0,codepoint_length)', 'prose_locations': []}:
        raise ValueError('This compiler requires explicit complete-scalar DATA; prose needs a separate exact-span DATA review')
    decisions = [read_json(path) for path in sorted(HERE.glob('decisions-*.json'))]
    by_sha = {item['document_sha256']: item for item in decisions}
    expected_shas = {doc['original_ref']['sha256'] for doc in inspection['documents']}
    if len(decisions) != len(by_sha) or set(by_sha) != expected_shas:
        raise ValueError('Uniform distinct input-document DATA coverage required')
    protected = set(reasons['unconditional_blocked_normalized_names'])
    documents, all_counts, uncertain = [], Counter({name: 0 for name in sorted(CLASSES)}), []
    coverage = []
    all_protected_candidates = []
    for doc in inspection['documents']:
        ref = doc['original_ref']
        raw = Path(ref['path']).read_bytes()
        if sha(raw) != ref['sha256']:
            raise ValueError('Original byte pin changed')
        value = decode_json(raw)
        candidates = {}
        for collection, member_kind in [('strings', 'string_value'), ('keys', 'object_key')]:
            for row in doc[collection]:
                if row['identity_probes']:
                    key = (row['pointer'], member_kind)
                    if key in candidates:
                        raise ValueError('Duplicate inventory location')
                    candidates[key] = row
        decision = by_sha[ref['sha256']]
        catalog_rows, used, doc_counts = [], set(), Counter({name: 0 for name in sorted(CLASSES)})
        for reason_id, declared_pointers in decision['groups'].items():
            reason = reasons['reasons'][reason_id]
            classification = reason['classification']
            if classification not in CLASSES:
                raise ValueError('Unrecognized DATA classification')
            for pointer in declared_pointers:
                key = (pointer, 'string_value')
                if key in used or key not in candidates:
                    raise ValueError('Duplicate or noncandidate DATA location')
                used.add(key)
                item = candidates[key]
                original_string = resolve(value, pointer, 'string_value')
                if not isinstance(original_string, str):
                    raise ValueError('Catalog location is not a string')
                if sha(original_string.encode()) != item['original_utf8_sha256']:
                    raise ValueError('Inventory string hash differs')
                json_sha = sha(json.dumps(original_string, ensure_ascii=False, separators=(',', ':')).encode())
                if json_sha != item['original_value_sha256'] or len(original_string) != item['codepoint_length']:
                    raise ValueError('Inventory scalar serialization or extent differs')
                boundaries = [part for part in parts(pointer) if normalized(part) in protected]
                is_metadata = classification in {'claimed_provenance_locator', 'execution_identity_metadata'}
                if boundaries and is_metadata:
                    raise ValueError('Unconditional raw-data boundary cannot be exempted')
                spans = []
                if is_metadata:
                    spans = [{'start': 0, 'end': len(original_string), 'unit': 'unicode_codepoint',
                              'original_utf8_sha256': sha(original_string.encode()),
                              'span_kind': 'complete_canonical_locator' if item['canonical_absolute_path'] else 'complete_execution_identifier'}]
                row = {
                    'original_ref': dict(ref), 'pointer': pointer, 'member_kind': 'string_value',
                    'original_value_sha256': sha(original_string.encode()),
                    'original_utf8_sha256': sha(original_string.encode()),
                    'original_json_string_sha256': json_sha,
                    'codepoint_length': len(original_string), 'classification': classification,
                    'structural_reason': reason['structural_reason'],
                    'source_context_explanation': reason['source_context_explanation'],
                    'decision_reason_id': reason_id, 'parent_pointer': item['parent_pointer'],
                    'parent_shape_only': item['parent_shape'],
                    'identity_spans': spans, 'contains_prose': False,
                    'protected_boundary_names': boundaries,
                    'whole_container_metadata_permission': False,
                    'reference_validated': False, 'evidence_credit': False,
                    'projection_authorized': False,
                }
                catalog_rows.append(row)
                doc_counts[classification] += 1
                if boundaries:
                    all_protected_candidates.append({'original_ref': dict(ref), 'pointer': pointer})
                if classification == 'uncertain':
                    uncertain.append({'original_ref': dict(ref), 'pointer': pointer})
        if used != set(candidates):
            missing = sorted(set(candidates) - used)
            raise ValueError('Uncataloged discovered identity locations: ' + repr(missing))
        all_counts.update(doc_counts)
        coverage.append({
            'document_ordinal': doc['document_ordinal'], 'original_ref': dict(ref),
            'byte_pin_verified_before_and_after': True,
            'string_values_inventoried': len(doc['strings']), 'object_keys_inventoried': len(doc['keys']),
            'detected_identity_locations': len(candidates), 'cataloged_locations': len(catalog_rows),
            'classifications': dict(doc_counts),
        })
        for note in decision['mixed_container_notes']:
            container = resolve(value, note['pointer'], 'string_value')
            if not isinstance(container, (dict, list)) or note['whole_container_projection_permission'] is not False:
                raise ValueError('Mixed-container DATA must preserve the container')
        documents.append({
            'document_ordinal': doc['document_ordinal'], 'original_ref': dict(ref),
            'locations': sorted(catalog_rows, key=lambda row: (row['pointer'], row['member_kind'])),
            'mixed_container_responsibility_notes': decision['mixed_container_notes'],
            'nonenumerated_content_responsibility': 'Preserve exact original value; never infer metadata role from an enclosing container or prefix.'
        })
        if sha(Path(ref['path']).read_bytes()) != ref['sha256']:
            raise ValueError('Original bytes changed during inspection')
    total = sum(all_counts.values())
    validation = {
        'version': 1, 'kind': 'selfclaim-format-catalog-structural-validation',
        'passed': True, 'independent_semantic_review_required': True,
        'documents': len(documents), 'original_byte_pins_verified': len(documents),
        'string_values_inventoried': sum(row['string_values_inventoried'] for row in coverage),
        'object_keys_inventoried': sum(row['object_keys_inventoried'] for row in coverage),
        'detected_identity_locations': total, 'cataloged_locations': total,
        'uncertain_locations': len(uncertain), 'identity_bearing_prose_locations': 0,
        'classified_object_key_locations': 0,
        'unconditional_protected_boundary_candidates': all_protected_candidates,
        'classifications': dict(all_counts), 'document_coverage': coverage,
        'checks': ['all ten externally pinned original bytes remain exact',
                   'authorized process-reference pins remain exact',
                   'every discovered identity string/key has an exact DATA decision',
                   'RFC6901 locations resolve to original strings',
                   'UTF8 and compact JSON-string hashes and codepoint extents match',
                   'no metadata classification crosses unconditional raw-data boundaries',
                   'no mixed container is granted metadata or projection permission'],
        'no_projection_or_dispatch_performed': True,
    }
    result = {
        'version': 1, 'kind': 'sealed-selfclaim-format-responsibility-data-catalog',
        'authority': reasons['authority'], 'survey_ref': survey_ref,
        'original_value_hash_encoding': 'SHA256 of original unquoted decoded string encoded as UTF-8; compact JSON-string hash is separately named.',
        'pointer_encoding': 'RFC6901 JSON pointer; object keys, if present, distinguished by member_kind.',
        'span_encoding': 'Zero-based half-open [start,end) Unicode-codepoint offsets in the original decoded string.',
        'global_limits': reasons['global_limits'],
        'unconditional_blocked_normalized_names': sorted(protected),
        'documents': documents, 'uncertain_locations': uncertain,
        'coverage_counts': {key: validation[key] for key in ['documents', 'original_byte_pins_verified', 'string_values_inventoried', 'object_keys_inventoried', 'detected_identity_locations', 'cataloged_locations', 'uncertain_locations', 'identity_bearing_prose_locations', 'classified_object_key_locations', 'classifications']},
    }
    for filename, item in [('CATALOG.json', result), ('VALIDATION.json', validation)]:
        (HERE / filename).write_text(json.dumps(item, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result['coverage_counts']))


if __name__ == '__main__':
    main()
