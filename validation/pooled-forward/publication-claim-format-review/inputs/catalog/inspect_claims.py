#!/usr/bin/env python3
"""Uniform read-only string/key inventory. No claim evaluation or projection."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SURVEY = ROOT / 'operators/cohort2/coordination/ALARM-SELFCLAIM-IDENTITY-POINTER-SURVEY-v1.json'
SURVEY_SHA256 = 'e2ffa885b0e8cc2c33f417ba6e58431962e2b4c173cc9dadea48828a8df29e77'
SOURCES = [
    Path('/Users/rex/.codex/skills/.system/skill-creator/SKILL.md'),
    ROOT / 'business-quality-tools/ALARM-POLICY-v1.json',
    ROOT / 'publication-alarm-review/revision-v2/anonymous_projection.py',
    ROOT / 'publication-material-review/revision-v3/alarm-material-tools-v3/material.py',
]
PROBES = {
    'reviewed_identity_detector': re.compile(r'baseline-v12|candidate-v13|stateful-default|baseline-explicit-prior|/Users/rex/|/Library/Developer/|/business/T[1-5]/[AB]/|run-cohort2/(?:arms|requests)/'),
    'generic_machine_locator': re.compile(r'/(?:Users|home)/[^/\s]+/|/Library/Developer/'),
    'execution_or_engine_token': re.compile(r'(?i)baseline[-_][a-z0-9.-]+|candidate[-_][a-z0-9.-]+|stateful-default|baseline-explicit-prior|run-cohort[0-9]+'),
    'short_assignment_token': re.compile(r'^(?:T[1-5](?:[-_/ ][AB])?|[AB])$'),
    'opaque_identity_token': re.compile(r'^[a-f0-9]{32}$'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def scalar_sha(value):
    return sha(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8'))


def pointer(parts):
    return ''.join('/' + str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def strict(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('Duplicate JSON member')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _v: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def kind(value):
    if value is None:
        return 'null'
    if type(value) is bool:
        return 'boolean'
    if isinstance(value, dict):
        return 'object'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, str):
        return 'string'
    return 'number'


def canonical_path(value):
    if not value.startswith('/') or '\\' in value or any(unicodedata.category(c).startswith('C') for c in value):
        return False
    path = PurePosixPath(value)
    return str(path) == value and '..' not in path.parts


def inspect(ref, ordinal):
    path = Path(ref['path'])
    if not path.is_absolute() or not path.is_relative_to(ROOT / 'cache/business/run-cohort2/arms') or path.name != 'self-claim.json':
        raise ValueError('Claim reference outside authorized claim class')
    raw = path.read_bytes()
    if sha(raw) != ref['sha256']:
        raise ValueError('Pinned claim bytes differ')
    value = strict(raw)
    if not isinstance(value, dict):
        raise ValueError('Claim root must be an object')
    strings, keys, scalar_types, containers = [], [], {}, []

    def entry(text, parts, parent, member_kind):
        probes = []
        for name, regex in PROBES.items():
            matches = [{'start': m.start(), 'end': m.end(), 'matched_utf8_sha256': sha(m.group().encode())}
                       for m in regex.finditer(text)]
            if matches:
                probes.append({'probe': name, 'matches': matches})
        parent_shape = ({key: kind(item) for key, item in parent.items()} if isinstance(parent, dict)
                        else {'array_member_types': sorted({kind(item) for item in parent})} if isinstance(parent, list)
                        else None)
        return {
            'pointer': pointer(parts), 'member_kind': member_kind,
            'parent_pointer': pointer(parts[:-1]),
            'original_value_sha256': scalar_sha(text),
            'original_utf8_sha256': sha(text.encode()),
            'codepoint_length': len(text), 'utf8_length': len(text.encode()),
            'canonical_absolute_path': canonical_path(text),
            'parent_shape': parent_shape, 'identity_probes': probes,
        }

    def walk(item, parts, parent=None):
        if isinstance(item, dict):
            containers.append({'pointer': pointer(parts), 'kind': 'object',
                               'members': {key: kind(sub) for key, sub in item.items()}})
            for key, sub in item.items():
                keys.append(entry(key, parts + [key], item, 'key'))
                walk(sub, parts + [key], item)
        elif isinstance(item, list):
            containers.append({'pointer': pointer(parts), 'kind': 'array',
                               'length': len(item), 'member_types': sorted({kind(sub) for sub in item})})
            for index, sub in enumerate(item):
                walk(sub, parts + [index], item)
        else:
            scalar_types[pointer(parts)] = kind(item)
            if isinstance(item, str):
                strings.append(entry(item, parts, parent, 'value'))
    walk(value, [])
    return {
        'document_ordinal': ordinal, 'original_ref': dict(ref), 'byte_pin_verified': True,
        'original_size_bytes': len(raw), 'scalar_types': scalar_types,
        'containers': containers, 'strings': strings, 'keys': keys,
        'counts': {
            'strings': len(strings), 'keys': len(keys), 'scalars': len(scalar_types),
            'probe_identity_string_locations': sum(bool(row['identity_probes']) for row in strings),
            'probe_identity_key_locations': sum(bool(row['identity_probes']) for row in keys),
        },
    }


def main():
    survey_raw = SURVEY.read_bytes()
    if sha(survey_raw) != SURVEY_SHA256:
        raise ValueError('Survey pin differs')
    survey = strict(survey_raw)
    refs = survey['claim_refs']
    if len(refs) != 10 or len({ref['path'] for ref in refs}) != 10:
        raise ValueError('Exactly ten distinct pinned claims required')
    result = {
        'version': 1, 'kind': 'uniform-sealed-selfclaim-string-key-inventory',
        'scope': 'Format and provenance responsibility only; no evaluation or projection. No referenced artifact is read or credited.',
        'survey_ref': {'path': str(SURVEY), 'sha256': SURVEY_SHA256},
        'reference_source_refs': [{'path': str(path), 'sha256': sha(path.read_bytes())} for path in SOURCES],
        'hash_encoding': 'original_value_sha256 is SHA256 of compact UTF-8 JSON string serialization with ensure_ascii=false; original_utf8_sha256 hashes unquoted decoded string bytes.',
        'probe_limit': 'Identity probes are discovery aids, not role classifiers or permission. Every string/key is inventoried; manual responsibility decisions must remain explicit data.',
        'documents': [inspect(ref, ordinal) for ordinal, ref in enumerate(refs, 1)],
    }
    (HERE / 'INSPECTION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'documents': len(result['documents']),
                      'byte_pins_verified': sum(doc['byte_pin_verified'] for doc in result['documents']),
                      'counts': {key: sum(doc['counts'][key] for doc in result['documents']) for key in result['documents'][0]['counts']}}))


if __name__ == '__main__':
    main()
