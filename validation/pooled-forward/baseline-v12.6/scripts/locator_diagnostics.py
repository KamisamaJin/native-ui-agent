#!/usr/bin/env python3
"""State-bound locator diagnosis. Candidates are evidence, never substitute selectors."""
from __future__ import annotations
import hashlib
from pathlib import Path
from native_checks import bound_state_evidence, resolve, same_selector


def diagnose(plan, report, observation, source_roots, selected_states=None):
    rows = {v['id']: v for v in report.get('rows', report.get('assertions', []))}
    states = {v['id']: v for v in plan['states']}
    selected = set(selected_states or states)
    source_files = []
    for root in map(Path, source_roots):
        for path in sorted(root.rglob('*')) if root.is_dir() else [root]:
            if path.is_file() and not path.is_symlink() and path.suffix in {'.swift', '.kt', '.java', '.xml', '.m', '.mm'}:
                try: source_files.append((path, path.read_text(), hashlib.sha256(path.read_bytes()).hexdigest()))
                except (UnicodeError, OSError): continue
    results = []
    for rule in plan['assertions']:
        row = rows[rule['id']]
        if row['status'] == 'passed' or rule['state'] not in selected: continue
        found, complete, reason, _ = bound_state_evidence(observation, states[rule['state']])
        targets = []
        for key in ['target', 'reference_target']:
            if rule.get(key) and rule[key] not in targets: targets.append(rule[key])
        evidence = []
        for target in targets:
            identity = target.get('identifier', target.get('label', ''))
            frames = []
            for index, snapshot in found:
                matched = [dict(node_index=i, **n) for i, n in enumerate(snapshot.get('nodes', [])) if same_selector(n, target)]
                candidates = []
                for i, n in enumerate(snapshot.get('nodes', [])):
                    if same_selector(n, target): continue
                    fields = [str(n.get('identifier', '')), str(n.get('label', ''))]
                    if identity and any(identity.casefold() in v.casefold() or (v and v.casefold() in identity.casefold()) for v in fields):
                        candidates.append({'node_index': i, 'identifier': n.get('identifier'), 'label': n.get('label'), 'role': n.get('role'), 'parent_id': n.get('parent_id')})
                frames.append({'snapshot': index, 'screenshot': snapshot.get('screenshot'), 'resolution': resolve(snapshot, target, plan['design_contract']['platform']),
                               'exact_nodes': matched, 'related_identity_candidates': candidates[:20]})
            refs = []
            for path, text, sha in source_files:
                refs.extend({'path': str(path.resolve()), 'sha256': sha, 'line': i, 'text': line.strip()[:300]}
                            for i, line in enumerate(text.splitlines(), 1) if identity and identity in line)
            evidence.append({'selector': target, 'frames': frames, 'source_occurrences': refs[:40]})
        results.append({'assertion_id': rule['id'], 'state': rule['state'], 'issue_status': row['status'], 'reason': row.get('reason', reason),
                        'state_evidence_present': bool(found), 'full_content_complete': complete,
                        'targets': evidence, 'next_action': 'inspect_native_topology_and_source' if found and targets else 'acquire_state_evidence' if not found else 'review_measurement_method',
                        'closure': 'open; diagnosis cannot pass an assertion or change an approved target'})
    return {'version': 1, 'items': results, 'scope': 'Exact state-bound native candidates and literal source references. No coordinate guesses, semantic remapping, style inference or automatic product attribution.'}
