#!/usr/bin/env python3
"""Use original failed checks and approved dependencies to choose diagnostic feedback."""
from __future__ import annotations
import argparse
from pathlib import Path
import design_contract as design
from requirement_routes import report_rows


def propose(coverage, parent, report, failed_ids, *, changed_files, source_before, source_after):
    if (design.digest(parent) != coverage['plan_sha256'] or source_before == source_after or
            any(not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v) for v in [source_before, source_after])):
        raise ValueError('Exact parent plan and a changed source version required')
    if not changed_files or any(not v or Path(v).is_absolute() or '..' in Path(v).parts for v in changed_files):
        raise ValueError('Explicit relative changed production paths required')
    rows = report_rows(report, parent)
    if not failed_ids or len(failed_ids) != len(set(failed_ids)) or any(k not in rows or rows[k]['status'] != 'failed' for k in failed_ids):
        raise ValueError('Feedback must start from original failed checks, never invented failures')
    owners = [o for o in coverage['obligations'] if set(o['assertion_ids']) & set(failed_ids)]
    if not owners: raise ValueError('Failure has no approved requirement route')
    selected = {o['id'] for o in owners}
    # All independently declared regression obligations are closed transitively.
    while True:
        expanded = selected | {r for o in coverage['obligations'] if o['id'] in selected for r in o['route']['regression_obligations']}
        if expanded == selected: break
        selected = expanded
    obligations = [o for o in coverage['obligations'] if o['id'] in selected]
    states = [s['id'] for s in parent['states'] if any(s['id'] in o['states'] for o in obligations)]
    return {'version': 1, 'parent_plan_sha256': coverage['plan_sha256'], 'source_before': source_before, 'source_after': source_after,
            'changed_files': changed_files, 'original_failed_ids': failed_ids, 'obligations': sorted(selected), 'states': states,
            'assertion_ids': sorted({r for o in obligations for r in o['assertion_ids']}),
            'requires_fresh_capture': True, 'full_final_required': True,
            'unverified_obligations': [o['id'] for o in coverage['obligations'] if o['id'] not in selected],
            'scope': 'Diagnostic feedback only. Dependencies express approved regression checks, not a proven source-impact graph. Full fresh final verification remains mandatory.'}


def main():
    p = argparse.ArgumentParser()
    for name in ['coverage', 'plan', 'report', 'change', 'output']: p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--failed-id', action='append', required=True); a = p.parse_args()
    change = design.load(a.change)
    value = propose(design.load(a.coverage), design.load(a.plan), design.load(a.report), a.failed_id,
                    changed_files=change['changed_files'], source_before=change['source_before'], source_after=change['source_after'])
    with a.output.open('x') as stream: stream.write(__import__('json').dumps(value, indent=2, ensure_ascii=False) + '\n')
if __name__ == '__main__': main()
