"""Prospective, value-preserving alarm presentation helpers; no adjudication.

The caller must verify the ALL30 cause barrier before passing any actual data.
Whole selected report arrays remain; this module does not select failed rows.
"""
import hashlib
from pathlib import Path, PurePosixPath
import re
import sys


HERE = Path(__file__).resolve().parent
REVISION = HERE.parent / 'publication-alarm-review/revision-v2'
PINS = {'anonymous_projection.py': '5bc14d37d11bd755dad38cf1f13b5bbc133eccedceb13ebb1e037dbd07361f2b',
        'phase_barriers.py': 'd940081fc9589df43589a1967442da5e78f6b45cb9c15c97ae7f5dca56407d9d',
        'alarm_packet.py': '0ac4a6ce93b2c1b0e7b9380891215d796ca82b1ca1cb0092419bed095cb0e0da'}
for filename, expected in PINS.items():
    if hashlib.sha256((REVISION / filename).read_bytes()).hexdigest() != expected:
        raise ValueError('Reviewed presentation library differs')
    name = filename[:-3]
    if name in sys.modules and Path(sys.modules[name].__file__).parent != REVISION:
        raise ValueError('Do not mix presentation revisions in one process')
sys.path.insert(0, str(REVISION))
import anonymous_projection as projection


REPORT_NAMES = {
    'automatic.json', 'before-evaluated.json', 'after-evaluated.json', 'evaluated.json',
    'report.json', 'findings.json', 'before-routes.json', 'after-routes.json', 'routes.json',
    'before-diagnostics.json', 'after-diagnostics.json', 'diagnostics.json',
    'retest-plan.json', 'after-dispatch.json', 'responsibility-results.json', 'admission.json',
    'coverage-domain-task.json', 'review-request.json', 'after-review-request.json',
    'cycle.json', 'completion.json', 'repair-task.json', 'patch-completion.json',
    'repair-completion.json', 'review-result.json', 'bound-manual.json', 'manual.json'}

OUTCOME_FIELDS = {'profile', 'action', 'exit_code', 'service_status', 'accepted', 'error',
                  'interrupted', 'observed_integrity_violation', 'native_collection_success',
                  'source_unchanged', 'integrity'}
OUTCOME_METADATA = {'task', 'arm', 'started_at_unix', 'finished_at_unix', 'wall_seconds',
    'started_at_monotonic', 'finished_at_monotonic', 'started_at_clock_gettime_monotonic',
    'finished_at_clock_gettime_monotonic', 'envelope_record', 'service_output', 'capture',
    'cycle', 'completion', 'bound_review', 'new_ui_acquisition', 'capture_reused',
    'acquisition_evidence', 'native_observer_command_wall_seconds', 'submission', 'inventory',
    'config', 'source_capsule', 'resources', 'native_claim',
    'native_continuation_claim', 'continuation_authority', 'entry_resume_permit',
    'failed_preclaim_entry', 'licensed_original_record', 'version', 'kind', 'final'}
OMIT_CANDIDATES = tuple(sorted(projection.METADATA_OMISSIONS))
REF_METADATA = {'capture', 'cycle', 'completion', 'bound_review', 'submission', 'inventory',
                'config', 'source_capsule', 'resources', 'native_claim', 'native_continuation_claim',
                'continuation_authority', 'entry_resume_permit', 'failed_preclaim_entry'}
MACHINE_PREFIXES = ('/Users/rex/', '/Library/Developer/')
EMBEDDED_PATH = re.compile(r'/(?:Users/rex|Library/Developer)/[^\s\"\'<>\[\]{}(),;:]+')


def outcome_view(value):
    """Fixed operation-result fact fields; reject unfamiliar data-bearing schema.

    Full raw outcomes/receipts remain externally pinned in the derivation ledger.
    Every selected field is copied by value, with exact JSON Decimal numbers.
    """
    if not isinstance(value, dict) or set(value) - OUTCOME_FIELDS - OUTCOME_METADATA:
        raise ValueError('Unreviewed operation outcome fields; retain failed preparation')
    if any(isinstance(value.get(key), (list, dict)) for key in OUTCOME_FIELDS - {'error', 'integrity'}):
        raise ValueError('Unexpected structured outcome fact field')
    if 'error' in value and value['error'] is not None:
        if not isinstance(value['error'], dict) or set(value['error']) != {'type', 'message'}:
            raise ValueError('Unreviewed original error schema')
    def reference(item, extra=()):
        return item is None or (isinstance(item, dict) and set(item) == {'path', 'sha256'} | set(extra)
                                and all(isinstance(v, str) for v in item.values())
                                and re.fullmatch('[0-9a-f]{64}', item['sha256']))
    for key in set(value) & OUTCOME_METADATA:
        item = value[key]
        if key in REF_METADATA:
            if not reference(item, ('original_path',) if key == 'submission' else ()):
                raise ValueError('Unexpected data in omitted outcome reference')
        elif key == 'acquisition_evidence':
            if item is not None and (not isinstance(item, dict) or set(item) != {'capture_receipt', 'execution', 'native_log', 'observation', 'scope'}
                    or not isinstance(item['scope'], str)
                    or not all(reference(item[k]) for k in ['capture_receipt', 'execution', 'native_log', 'observation'])):
                raise ValueError('Unexpected data in acquisition provenance metadata')
        elif isinstance(item, (dict, list)):
            raise ValueError('Structured data cannot be silently omitted as execution metadata')
    return {key: value[key] for key in value if key in OUTCOME_FIELDS}


def neutralize(value, aliases=None):
    """Use reviewed exact metadata substitutions; never alter a fact subtree."""
    aliases = {} if aliases is None else dict(aliases)
    omitted = [key for key in OMIT_CANDIDATES if key in value and
               projection._safe_omission(key, value[key])]
    rules, pointers, seen = {}, [], set()

    def add(before):
        if before not in rules:
            after = aliases.get(before, 'paths/p' + hashlib.sha256(before.encode()).hexdigest()[:24])
            rules[before] = {'original': before, 'anonymous': after}

    def walk(item, parts):
        if isinstance(item, dict):
            for key, sub in item.items():
                if not parts and key in omitted: continue
                walk(sub, parts + [key])
        elif isinstance(item, list):
            for index, sub in enumerate(item): walk(sub, parts + [index])
        elif isinstance(item, str) and projection.LEAK.search(item):
            key = parts[-1] if isinstance(parts[-1], str) else parts[-2] if len(parts) > 1 else None
            if any(projection._protected(p) for p in parts) or key not in projection.PATH_KEYS | projection.NARRATIVE_KEYS:
                raise ValueError('Identity-bearing fact or unfamiliar metadata pointer: ' + projection.pointer(parts))
            if key in projection.PATH_KEYS and item.startswith(MACHINE_PREFIXES):
                path = PurePosixPath(item)
                if str(path) != item or '..' in path.parts or any(ord(c) < 32 for c in item):
                    raise ValueError('Unreviewed recorded machine path')
                add(item)
            else:
                for match in EMBEDDED_PATH.finditer(item): add(match.group(0).rstrip('.'))
            for token in projection.IDENTITY_TOKENS:
                if token in item: rules[token] = {'original': token, 'anonymous': 'recorded-engine'}
            here = projection.pointer(parts)
            if here in seen: raise ValueError('Duplicate metadata pointer')
            seen.add(here); pointers.append(here)
    walk(value, [])
    return projection.project(value, omit_top_level=omitted,
                              replacements=list(rules.values()), rewrite_pointers=pointers)
