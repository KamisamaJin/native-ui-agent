"""Revision 2: lossless JSON and narrowly bounded identity metadata projection.

Public project()/strict_json() call shapes and v1 ledger fields are retained.
Decimal is used for recorded JSON fractional/exponent tokens; use json_text()
when serializing those values. No fact, source criterion or verdict is created.
"""
import copy
from decimal import Decimal
import hashlib
import json
import math
from pathlib import PurePosixPath
import re
import unicodedata


IMPLEMENTATION_REVISION = 2
METADATA_OMISSIONS = {'operations', 'tool', 'tool_root', 'arm', 'cost', 'costs', 'timing',
                      'own_delivery_wall_seconds', 'started_at_unix', 'finished_at_unix',
                      'started_at_monotonic', 'finished_at_monotonic', 'wall_seconds',
                      'startedAtUnix', 'finishedAtUnix', 'argv', 'trace',
                      'tool_version', 'skill_version', 'execution_api'}
IDENTITY_TOKENS = {'baseline-v12.6-common-6', 'candidate-v13.9',
                   'stateful-default', 'baseline-explicit-prior'}
PATH_KEYS = {'path', 'file', 'filename', 'directory', 'root', 'source_roots',
             'capture_result', 'capture_path', 'output', 'source_path', 'subject',
             'artifact', 'plan', 'policy', 'bridge', 'fixtures', 'environment',
             'cycle_path', 'review_result', 'review_store', 'source_review_store',
             'source', 'uri', 'image', 'image_path', 'screenshot', 'screenshot_path',
             'image_ref', 'source_ref', 'plan_path', 'policy_path', 'bridge_path', 'fixture_path'}
NARRATIVE_KEYS = {'reason', 'statement', 'message', 'details', 'description',
                  'explanation', 'scope', 'scope_limit', 'limitation', 'note', 'notes'}
PROTECTED_KEYS = {'actual', 'expected', 'text', 'label', 'value', 'identifier',
                  'payload', 'callback', 'event', 'color', 'font_size', 'padding', 'margin',
                  'measured', 'observed', 'rendered', 'status', 'verdict'}
LEAK = re.compile(r'baseline-v12|candidate-v13|stateful-default|baseline-explicit-prior|/Users/rex/|/Library/Developer/|/business/T[1-5]/[AB]/|run-cohort2/(?:arms|requests)/')

# Compound outer execution metadata can be omitted only when every member has
# one of these execution/cost/time names. Unknown fields stop preparation. This
# is deliberately a bounded schema check, not a classifier for arbitrary prose.
_EXECUTION_KEYS = METADATA_OMISSIONS | {
    'seconds', 'milliseconds', 'nanoseconds', 'duration_seconds', 'duration_ms',
    'count', 'calls', 'bytes', 'tokens', 'input_tokens', 'output_tokens',
    'cached_tokens', 'total_tokens', 'input', 'output', 'total', 'amount',
    'usd', 'currency', 'unit', 'units', 'rate', 'rates', 'price',
    'name', 'id', 'type', 'operation', 'operation_id', 'request_id', 'call_id',
    'version', 'api', 'endpoint', 'method', 'pid', 'cwd', 'path', 'root',
    'start', 'end', 'started', 'finished', 'elapsed', 'duration'}
_EXECUTION_SCALAR_KEYS = {
    'own_delivery_wall_seconds', 'started_at_unix', 'finished_at_unix',
    'started_at_monotonic', 'finished_at_monotonic', 'wall_seconds',
    'startedAtUnix', 'finishedAtUnix'}


def _normalized(key):
    return re.sub('[^a-z0-9]', '', key.casefold())


_PROTECTED_NORMALIZED = {_normalized(key) for key in PROTECTED_KEYS}


def _protected(key):
    return isinstance(key, str) and (
        _normalized(key) in _PROTECTED_NORMALIZED or
        _normalized(key).startswith(('actual', 'expected', 'measured', 'observed', 'rendered')))


def _validate_json(value, active=None):
    """Reject Python-only containers, non-string members, cycles and nonfinite numbers."""
    if active is None:
        active = set()
    if value is None or type(value) in (str, bool, int):
        if type(value) is str:
            value.encode('utf-8')  # Lone surrogate values cannot be faithfully emitted.
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError('Nonfinite JSON is forbidden')
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError('Nonfinite JSON is forbidden')
        return
    if type(value) not in (dict, list):
        raise ValueError('Only recorded JSON values are permitted')
    if id(value) in active:
        raise ValueError('Cyclic JSON is forbidden')
    active.add(id(value))
    try:
        if type(value) is dict:
            for key, item in value.items():
                if type(key) is not str:
                    raise ValueError('JSON object members must be strings')
                key.encode('utf-8')
                _validate_json(item, active)
        else:
            for item in value:
                _validate_json(item, active)
    finally:
        active.remove(id(value))


def json_text(value, *, sort_keys=False, indent=None):
    """Serialize exact finite Decimal JSON numbers as numbers, never strings/floats."""
    _validate_json(value)
    if indent is not None and (type(indent) is not int or indent < 0):
        raise ValueError('Nonnegative indentation required')

    def emit(item, depth):
        if isinstance(item, dict):
            keys = sorted(item) if sort_keys else list(item)
            rows = [(json.dumps(key, ensure_ascii=False), emit(item[key], depth + 1)) for key in keys]
            if not rows:
                return '{}'
            if indent is None:
                return '{' + ','.join(key + ':' + val for key, val in rows) + '}'
            return '{\n' + ',\n'.join(' ' * (indent * (depth + 1)) + key + ': ' + val for key, val in rows) + '\n' + ' ' * (indent * depth) + '}'
        if isinstance(item, list):
            rows = [emit(val, depth + 1) for val in item]
            if not rows:
                return '[]'
            if indent is None:
                return '[' + ','.join(rows) + ']'
            return '[\n' + ',\n'.join(' ' * (indent * (depth + 1)) + val for val in rows) + '\n' + ' ' * (indent * depth) + ']'
        if type(item) is Decimal:
            return str(item)
        return json.dumps(item, ensure_ascii=False, allow_nan=False, separators=(',', ':'))

    return emit(value, 0)


def digest(value):
    return hashlib.sha256(json_text(value, sort_keys=True).encode('utf-8')).hexdigest()


def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('Duplicate JSON member')
            result[key] = value
        return result

    def invalid(value):
        raise ValueError('Nonfinite JSON is forbidden: ' + value)

    value = json.loads(raw, object_pairs_hook=pairs, parse_float=Decimal, parse_constant=invalid)
    _validate_json(value)
    return value


def pointer(parts):
    return ''.join('/' + str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def _metadata_only(value):
    if isinstance(value, dict):
        return all(key in _EXECUTION_KEYS and not _protected(key) and _metadata_only(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return all(_metadata_only(item) for item in value)
    return True


def _safe_omission(key, value):
    if key in _EXECUTION_SCALAR_KEYS:
        return value is None or type(value) in (int, float, Decimal)
    if key in {'arm', 'tool', 'tool_root', 'tool_version', 'skill_version', 'execution_api'}:
        return value is None or type(value) is str
    if key == 'argv':
        return isinstance(value, list) and all(type(item) is str for item in value)
    return _metadata_only(value)


def _control_text(value):
    return any(unicodedata.category(char).startswith('C') for char in value)


def _rule(before, after):
    if not isinstance(before, str) or not before or not isinstance(after, str) or not after:
        raise ValueError('Nonempty identity substitution required')
    if _control_text(before) or _control_text(after) or '\\' in before or '\\' in after:
        raise ValueError('Identity substitutions cannot contain controls or path aliases')
    if before.startswith('/'):
        p = PurePosixPath(before)
        if str(p) != before or '..' in p.parts or not before.startswith(('/Users/rex/', '/Library/Developer/')):
            raise ValueError('Only canonical recorded machine paths are identity metadata')
        # A declared path can replace itself or its descendants, never a distinct
        # filename/directory that merely shares the same textual prefix.
        pattern = re.compile(r'(?<![\w./\\-])' + re.escape(before) + r'(?=$|/|[\s,;:)\]}>"\'])')
    elif before in IDENTITY_TOKENS:
        pattern = re.compile(r'(?<![\w.-])' + re.escape(before) + r'(?![\w.-])')
    else:
        raise ValueError('Arbitrary factual string substitution is forbidden')
    p = PurePosixPath(after)
    if after.startswith('/') or str(p) != after or not p.parts or '..' in p.parts or LEAK.search(after):
        raise ValueError('Anonymous identity substitute must be neutral and canonical relative')
    return before, after, pattern


def project(original, *, omit_top_level=(), replacements=(), rewrite_pointers=()):
    if type(original) is not dict:
        raise ValueError('A recorded JSON object is required')
    _validate_json(original)
    if not isinstance(omit_top_level, (list, tuple)) or not all(isinstance(key, str) for key in omit_top_level):
        raise ValueError('Explicit outer metadata omission names required')
    omissions = set(omit_top_level)
    if not omissions <= METADATA_OMISSIONS or len(omissions) != len(omit_top_level):
        raise ValueError('Only distinct declared outer metadata fields may be omitted')
    for key in omissions:
        if key in original and not _safe_omission(key, original[key]):
            raise ValueError('Outer metadata omission contains factual or unknown structured fields: ' + key)
    rules = []
    for row in replacements:
        if not isinstance(row, dict) or set(row) != {'original', 'anonymous'}:
            raise ValueError('Exact identity substitution pair required')
        rules.append(_rule(row['original'], row['anonymous']))
    if len({before for before, _, _ in rules}) != len(rules):
        raise ValueError('Ambiguous identity substitution')
    rules.sort(key=lambda row: -len(row[0]))
    if not isinstance(rewrite_pointers, (list, tuple)) or not all(
            isinstance(p, str) and p.startswith('/') and not re.search(r'~(?![01])', p) for p in rewrite_pointers):
        raise ValueError('Explicit canonical JSON pointers required')
    declared = set(rewrite_pointers)
    if len(declared) != len(rewrite_pointers):
        raise ValueError('Duplicate rewrite pointer')
    used = set()
    changes = []
    result = {k: copy.deepcopy(v) for k, v in original.items() if k not in omissions}

    def walk(value, parts):
        here = pointer(parts)
        if isinstance(value, dict):
            return {key: walk(item, parts + [key]) for key, item in value.items()}
        if isinstance(value, list):
            return [walk(item, parts + [i]) for i, item in enumerate(value)]
        if here not in declared:
            return value
        if not isinstance(value, str) or not parts:
            raise ValueError('Only declared metadata string values may be rewritten')
        key = parts[-1] if isinstance(parts[-1], str) else parts[-2] if len(parts) > 1 else None
        if any(_protected(part) for part in parts) or key not in PATH_KEYS | NARRATIVE_KEYS:
            raise ValueError('Rendered, expected or measured fact subtree cannot be rewritten')
        changed = value
        applied = []
        for before, after, pattern in rules:
            updated, count = pattern.subn(lambda _match: after, changed)
            if count:
                applied.append({'original': before, 'anonymous': after})
            changed = updated
        if changed == value:
            raise ValueError('Declared metadata rewrite performs no exact bounded substitution')
        used.add(here)
        changes.append({'pointer': here, 'original': value, 'anonymous': changed,
                        'rules': applied, 'semantic_value_fields_changed': False})
        return changed

    result = walk(result, [])
    if used != declared:
        raise ValueError('Declared rewrite pointer was absent, omitted or non-scalar')
    if LEAK.search(json_text(result)):
        raise ValueError('Identity-bearing content remains; retain failed preparation, do not redact facts')
    ledger = {'version': 1, 'implementation_revision': IMPLEMENTATION_REVISION,
              'kind': 'bounded-alarm-identity-value-projection',
              'original_value_sha256': digest(original), 'projected_value_sha256': digest(result),
              'omitted_top_level': {key: {'original_value_sha256': digest(original[key])}
                                   for key in sorted(omissions) if key in original},
              'identity_metadata_changes': changes,
              'scope': 'Exact declared outer execution metadata omissions/bounded path or tool-name substitutions only. Protected fact subtrees, other fields, array order, statuses and exact JSON numeric values remain unchanged. Original bytes retained separately; no quality judgment.'}
    return result, ledger
