"""Bounded JSON identity projection for later anonymous alarm packets.

Only declared metadata omissions and exact path/tool-name substitutions are
allowed. Measured/expected/UI values cannot be edited through this API. Original
bytes and every transformation must remain in a separate operator ledger.
"""
import copy
import hashlib
import json
from pathlib import PurePosixPath
import re


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
                  'payload', 'callback', 'event', 'color', 'font_size', 'padding', 'margin'}
LEAK = re.compile(r'baseline-v12|candidate-v13|stateful-default|baseline-explicit-prior|/Users/rex/|/Library/Developer/|/business/T[1-5]/[AB]/|run-cohort2/(?:arms|requests)/')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


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
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def pointer(parts):
    return ''.join('/' + str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def project(original, *, omit_top_level=(), replacements=(), rewrite_pointers=()):
    if not isinstance(original, dict):
        raise ValueError('A recorded JSON object is required')
    omissions = set(omit_top_level)
    if not omissions <= METADATA_OMISSIONS or len(omissions) != len(omit_top_level):
        raise ValueError('Only distinct declared outer metadata fields may be omitted')
    rules = []
    for row in replacements:
        if not isinstance(row, dict) or set(row) != {'original', 'anonymous'}:
            raise ValueError('Exact identity substitution pair required')
        before, after = row['original'], row['anonymous']
        if not isinstance(before, str) or not before or not isinstance(after, str) or not after:
            raise ValueError('Nonempty identity substitution required')
        if before.startswith('/'):
            p = PurePosixPath(before)
            if str(p) != before or '..' in p.parts or not before.startswith(('/Users/rex/', '/Library/Developer/')):
                raise ValueError('Only canonical recorded machine paths are identity metadata')
        elif before not in IDENTITY_TOKENS:
            raise ValueError('Arbitrary factual string substitution is forbidden')
        if after.startswith('/') or '..' in PurePosixPath(after).parts or LEAK.search(after):
            raise ValueError('Anonymous identity substitute must be neutral and relative')
        rules.append((before, after))
    if len({before for before, _ in rules}) != len(rules):
        raise ValueError('Ambiguous identity substitution')
    rules.sort(key=lambda row: -len(row[0]))
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
        if key in PROTECTED_KEYS or key not in PATH_KEYS | NARRATIVE_KEYS:
            raise ValueError('Rendered, expected or measured fact pointer cannot be rewritten')
        changed = value
        applied = []
        for before, after in rules:
            if before in changed:
                changed = changed.replace(before, after)
                applied.append({'original': before, 'anonymous': after})
        if changed == value:
            raise ValueError('Declared metadata rewrite performs no exact substitution')
        used.add(here)
        changes.append({'pointer': here, 'original': value, 'anonymous': changed,
                        'rules': applied, 'semantic_value_fields_changed': False})
        return changed

    result = walk(result, [])
    if used != declared:
        raise ValueError('Declared rewrite pointer was absent, omitted or non-scalar')
    serialized = json.dumps(result, ensure_ascii=False, allow_nan=False)
    if LEAK.search(serialized):
        raise ValueError('Identity-bearing content remains; retain failed preparation, do not redact facts')
    ledger = {'version': 1, 'kind': 'bounded-alarm-identity-value-projection',
              'original_value_sha256': digest(original), 'projected_value_sha256': digest(result),
              'omitted_top_level': {key: {'original_value_sha256': digest(original[key])}
                                   for key in sorted(omissions) if key in original},
              'identity_metadata_changes': changes,
              'scope': 'Exact declared outer metadata omissions/path or tool-name substitutions only. All other keys, arrays, statuses, expected and measured values are unchanged. Original bytes retained separately; no quality judgment.'}
    return result, ledger
