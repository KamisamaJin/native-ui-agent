"""Common post-seal actual-only binding format adapter, never a new oracle.

The caller authenticates the independent consensus, compiled claims, exact
packet source inventory/aliases, catalog and original observation. This pure
adapter cannot authorize those inputs. It never supplies expectations/units,
infers an actual, changes source, or grants a product pass. Unsupported rows
become explicit unknowns; valid rows keep their exact original actuals. The
unchanged frozen binders remain responsible for the final evidence evaluation.
"""
import copy
import hashlib
import re


def need(ok, why):
    if not ok: raise ValueError(why)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def index(rows, key, fields, known):
    need(type(rows) is list, 'Explicit sealed actual rows required')
    result = {}
    for row in rows:
        need(type(row) is dict and set(row) == fields, 'Actual-only row schema required; no expectation/unit overrides')
        name = row[key]
        need(type(name) is str and name in known and name not in result, 'Known unique obligation identity required')
        result[name] = row
    return result


def source_rows(claims, rows, source_inventory, citation_aliases, reader):
    """Project separately authenticated current source observations.

    source_inventory contains only byte-verified actual component/bridge/placement
    packet members. Explicit aliases come from the operator's positive copy
    proof, never basename/text guessing or the reviewing AI. Current claimed
    subject hashes and viewed bytes must both match before a citation is kept.
    """
    need(type(claims) is list and type(source_inventory) is dict and type(citation_aliases) is dict,
         'Compiled claims and authenticated source maps required')
    by_id = {claim['id']: claim for claim in claims if claim['method'] == 'source'}
    need(len(by_id) == sum(claim['method'] == 'source' for claim in claims), 'Unique compiled source obligations required')
    observed = index(rows, 'id', {'id', 'observed', 'reason', 'citations'}, set(by_id))
    output = []; records = []
    for claim_id, claim in by_id.items():
        raw = observed.get(claim_id); unsupported = []; citations = []
        if not claim.get('supported'):
            records.append({'id': claim_id, 'original_actual': copy.deepcopy(raw),
                            'binding': 'unsupported-compiled-provider', 'reasons': [claim.get('unsupported_reason')]})
            continue  # The frozen binder forbids unsupported claim IDs; its audit retains U.
        if raw is None:
            unsupported.append('No sealed source observation supplied')
        else:
            if type(raw['observed']) not in {bool, type(None)}: unsupported.append('Actual must be Boolean/null')
            if type(raw['reason']) is not str or not raw['reason'].strip(): unsupported.append('Missing original rationale')
            if type(raw['citations']) is not list:
                unsupported.append('Explicit original citations required')
            else:
                for citation in raw['citations']:
                    if type(citation) is not dict or set(citation) != {'path', 'line'}:
                        unsupported.append('Malformed original source citation'); continue
                    alias = citation['path']; line = citation['line']
                    target = citation_aliases.get(alias) if type(alias) is str else None
                    entry = source_inventory.get(alias) if type(alias) is str else None
                    kinds = {'component': {'production-source'}, 'bridge': {'actual-bridge-source'},
                             'integration': {'production-placement', 'integration-source'}}.get(claim.get('owner'), set())
                    if (type(alias) is not str or type(target) is not str or type(entry) is not dict
                            or set(entry) != {'sha256', 'kind'}
                            or entry['kind'] not in kinds
                            or target not in claim['files'] or entry['sha256'] != claim['files'][target]):
                        unsupported.append('Citation lacks an exact approved production-subject alias'); continue
                    try: current = reader.read_bytes(target)
                    except (OSError, KeyError, ValueError):
                        unsupported.append('Current approved subject is unavailable or failed reader integrity'); continue
                    if sha(current) != claim['files'][target]:
                        unsupported.append('Current approved subject changed'); continue
                    try: count = len(current.decode('utf-8').splitlines())
                    except UnicodeDecodeError:
                        unsupported.append('Source citation is not readable UTF8'); continue
                    if type(line) is not int or not 1 <= line <= count:
                        unsupported.append('Citation line is outside the exact current subject'); continue
                    citations.append({'path': target, 'line': line})
            if raw['observed'] is not None and not citations: unsupported.append('Non-null source actual has no approved implementation citation')
        if unsupported:
            row = {'id': claim_id, 'observed': None, 'reason': 'Unsupported sealed observation: ' + '; '.join(unsupported), 'citations': []}
        else:
            row = {'id': claim_id, 'observed': raw['observed'], 'reason': raw['reason'], 'citations': citations}
        output.append(row)
        records.append({'id': claim_id, 'original_actual': copy.deepcopy(raw),
                        'binding': 'unknown' if unsupported else 'retained-actual', 'reasons': unsupported,
                        'projected_actual': copy.deepcopy(row)})
    return {'version': 1, 'observations': output}, {'kind': 'source-actual-format-projection', 'records': records,
        'scope': 'Only source citation aliases/format are projected. No source truth, source expected value, native execution or complete delivery credit.'}


def visual_rows(required_review_ids, rows, sealed_context, original_context, allowed_frames):
    """Preserve valid actuals; isolate unsupported citations to their own row.

    Frame sets must come from the frozen bound_state_evidence for this exact
    original observation. Full-content coverage and P/F/U are still evaluated
    by the unchanged backend, not by this adapter.
    """
    need(type(required_review_ids) is list and all(type(rid) is str and rid for rid in required_review_ids)
         and len(set(required_review_ids)) == len(required_review_ids), 'Unique generated review IDs required')
    fields = {'catalog_sha256', 'observation_sha256'}
    need(type(sealed_context) is dict and set(sealed_context) == fields
         and type(original_context) is dict and set(original_context) == fields
         and all(type(v) is str and re.fullmatch('[0-9a-f]{64}', v) for v in original_context.values())
         and sealed_context == original_context, 'Original catalog/observation context differs; no context rewriting')
    need(set(allowed_frames) == set(required_review_ids), 'Exact independently bound original state/frame sets required')
    need(all(type(frames) in {set, list, tuple} and all(type(i) is int and i >= 0 for i in frames)
             for frames in allowed_frames.values()), 'Original frame provider must supply nonnegative integer indices')
    observed = index(rows, 'review_id', {'review_id', 'actual', 'reason', 'snapshot_indices'}, set(required_review_ids))
    output = []; records = []
    for rid in required_review_ids:
        raw = observed.get(rid); unsupported = []
        if raw is None: unsupported.append('No sealed visual observation supplied')
        else:
            if type(raw['actual']) not in {bool, type(None)}: unsupported.append('Actual must be Boolean/null')
            if type(raw['reason']) is not str or not raw['reason'].strip(): unsupported.append('Missing original rationale')
            indices = raw['snapshot_indices']
            if (type(indices) is not list or any(type(i) is not int for i in indices)
                    or len(set(indices)) != len(indices) or not set(indices) <= set(allowed_frames[rid])):
                unsupported.append('Frame citation is not unique or outside this exact state')
            elif raw['actual'] is not None and not indices:
                unsupported.append('Non-null visual actual has no original frame evidence')
        if unsupported:
            row = {'review_id': rid, 'actual': None, 'reason': 'Unsupported sealed observation: ' + '; '.join(unsupported), 'snapshot_indices': []}
        else: row = copy.deepcopy(raw)
        output.append(row); records.append({'review_id': rid, 'original_actual': copy.deepcopy(raw),
            'binding': 'unknown' if unsupported else 'retained-actual', 'reasons': unsupported,
            'projected_actual': copy.deepcopy(row)})
    return dict(version=1, **original_context, decisions=output), {'kind': 'visual-actual-format-projection', 'records': records,
        'scope': 'Exact original state-frame citation/format only. No inferred actual, expected/unit, pixel measurement, full-content or product pass.'}
