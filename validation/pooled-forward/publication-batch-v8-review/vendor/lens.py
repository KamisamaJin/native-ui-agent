"""Pure, independently authorized metadata projection for sealed worker claims.

This is disclosure formatting, never evidence validation or product evaluation.
The caller authenticates raw bytes, the responsibility catalogue and its separate
independent approval, and supplies only that document's approved location hashes.
"""
import copy
import hashlib
from pathlib import PurePosixPath
import re
import unicodedata


CLASSES = {'claimed_provenance_locator', 'execution_identity_metadata'}


def need(value, message):
    if not value: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def canonical_sha(value, projection):
    return sha(projection.json_text(value, sort_keys=True).encode('utf-8'))


def parts(pointer):
    need(isinstance(pointer, str) and pointer.startswith('/'), 'Non-root RFC6901 metadata pointer required')
    result = []
    for word in pointer.split('/')[1:]:
        need(re.search(r'~(?![01])', word) is None, 'Malformed RFC6901 escape')
        result.append(word.replace('~1', '/').replace('~0', '~'))
    return result


def at(value, pointer):
    current = value
    for word in parts(pointer):
        if type(current) is list:
            need(word.isdigit() and str(int(word)) == word and int(word) < len(current), 'Exact existing array member required')
            current = current[int(word)]
        else:
            need(type(current) is dict and word in current, 'Exact existing object member required')
            current = current[word]
    return current


def locator(value):
    return (value.startswith('/') and '\\' not in value
            and not any(unicodedata.category(c).startswith('C') for c in value)
            and str(PurePosixPath(value)) == value and '..' not in PurePosixPath(value).parts)


def project(value, original_ref, locations, approved_location_hashes, projection):
    """Replace complete independently classified metadata scalars only.

    Per-document ordinal handles preserve equality without publishing an
    unkeyed hash of a short assignment/tool identifier. Raw path hashes and
    catalogue decisions remain in the separate operator proof.
    """
    projection._validate_json(value)
    need(type(value) is dict and type(locations) is list and type(approved_location_hashes) is set,
         'Original worker object and explicit independently approved locations required')
    need(type(original_ref) is dict and set(original_ref) == {'path', 'sha256'}
         and type(original_ref['path']) is str and locator(original_ref['path'])
         and type(original_ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}', original_ref['sha256']),
         'Exact canonical original worker byte reference required')
    by_pointer = {}; seen_hashes = set(); tokens = {}; changes = []
    occupied = set()
    def strings(item):
        if type(item) is dict:
            for key, child in item.items(): occupied.add(key); strings(child)
        elif type(item) is list:
            for child in item: strings(child)
        elif type(item) is str: occupied.add(item)
    strings(value)
    blocked = projection._PROTECTED_NORMALIZED | {'actualfilepath'}
    for entry in sorted(locations, key=lambda row: row['pointer']):
        digest = canonical_sha(entry, projection)
        need(digest in approved_location_hashes and digest not in seen_hashes, 'Missing or duplicate independent location approval')
        seen_hashes.add(digest)
        need(entry.get('original_ref') == original_ref and entry.get('member_kind') == 'string_value'
             and entry.get('classification') in CLASSES, 'Only same-original typed metadata strings are supported')
        pointer = entry['pointer']; path = parts(pointer)
        need(not any(projection._normalized(word) in blocked for word in path)
             and not projection._protected(path[-1]), 'Raw fact container or protected leaf cannot be projected')
        need(pointer not in by_pointer, 'Duplicate metadata pointer')
        text = at(value, pointer)
        need(type(text) is str and bool(text) and sha(text.encode()) == entry['original_utf8_sha256']
             and type(entry.get('codepoint_length')) is int and entry['codepoint_length'] == len(text),
             'Original metadata scalar differs')
        need(entry.get('contains_prose') is False and entry.get('whole_container_metadata_permission') is False,
             'This lens supports complete scalars only; no prose or whole-container grant')
        for flag in ['reference_validated', 'evidence_credit', 'projection_authorized']:
            need(entry.get(flag) is False, 'Responsibility data alone cannot grant validity, evidence or projection authority')
        spans = entry.get('identity_spans')
        need(type(spans) is list and len(spans) == 1 and type(spans[0]) is dict
             and type(spans[0].get('start')) is int and spans[0]['start'] == 0
             and type(spans[0].get('end')) is int and spans[0]['end'] == len(text)
             and spans[0].get('unit') == 'unicode_codepoint'
             and spans[0].get('original_utf8_sha256') == sha(text.encode()), 'Exact full-scalar codepoint span required')
        span_kind = spans[0].get('span_kind')
        if span_kind == 'complete_canonical_locator':
            need(locator(text), 'Canonical claimed locator required; no filesystem target is opened')
        else:
            need(span_kind == 'complete_execution_identifier'
                 and entry['classification'] == 'execution_identity_metadata'
                 and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*', text) is not None,
                 'Explicit execution identifier required; arbitrary prose cannot be hidden')
        if text not in tokens:
            number = len(tokens) + 1
            while 'record-ref-%04d' % number in occupied: number += 1
            tokens[text] = 'record-ref-%04d' % number; occupied.add(tokens[text])
        token = tokens[text]
        by_pointer[pointer] = token
        changes.append({'pointer': pointer, 'member_kind': 'string_value', 'location_sha256': digest,
                        'classification': entry['classification'], 'original_utf8_sha256': sha(text.encode()),
                        'anonymous_literal': token, 'reference_validated': False, 'evidence_credit': False})
    need(seen_hashes == approved_location_hashes, 'No dropped or foreign location approval allowed for this document')
    used = set()
    def walk(item, path):
        here = projection.pointer(path)
        if type(item) is dict:
            result = {}
            for key, child in item.items():
                need(projection.LEAK.search(key) is None, 'Identity-bearing object keys are unsupported by this scalar lens')
                result[key] = walk(child, path + [key])
            return result
        if type(item) is list: return [walk(child, path + [index]) for index, child in enumerate(item)]
        if here in by_pointer:
            need(type(item) is str, 'Only the approved string scalar may change')
            used.add(here); return by_pointer[here]
        if type(item) is str:
            need(projection.LEAK.search(item) is None, 'Unclassified identity-bearing claim content remains blocked')
        return copy.deepcopy(item)
    projected = walk(value, [])
    need(used == set(by_pointer), 'Every approved location must be consumed exactly once')
    projection._validate_json(projected)
    proof = {'version': 1, 'kind': 'independently-classified-worker-metadata-projection',
             'original_ref': original_ref, 'original_value_sha256': canonical_sha(value, projection),
             'projected_value_sha256': canonical_sha(projected, projection), 'changes': changes,
             'scope': 'Per-original ordinal metadata handles only; no omissions, assertion rewriting, target access, validity or evidence credit. Booleans/numbers/arrays and nonmetadata strings stay exact.'}
    return projected, proof
