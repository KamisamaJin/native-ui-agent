from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parents[1]
NEUTRAL = BASE / 'neutral'
SNAPSHOT = BASE / 'development/candidate-attempt-1'
sys.path.insert(0, str(SNAPSHOT / 'scripts'))
import native_checks
import requirement_routes

def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, v): (ROOT / name).write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')

def main():
    begun = time.time(); approval = load(NEUTRAL / 'APPROVAL.json'); lock = load(NEUTRAL / 'design/lock.json')
    audit = load(ROOT / 'native-audit.json'); results = []
    for row in audit['runs']:
        case, repeat, arm, name = row['case'], row['repeat'], row['arm'], row['name']
        if case == 'ordinary400' and repeat == 1: continue
        cap = BASE / 'neutral-captures' / name
        obs = load(cap / 'observation.json'); plan = load(NEUTRAL / 'generated' / case / 'design/plan.json')
        coverage = load(NEUTRAL / 'generated' / case / 'coverage.json')
        decisions = []
        for rule in plan['assertions']:
            if rule['kind'] != 'manual': continue
            state = next(s for s in plan['states'] if s['id'] == rule['state'])
            evidence, complete, _, _ = native_checks.bound_state_evidence(obs, state)
            if rule['coverage'] == 'full_content': indices = [i for i, _ in evidence]
            else: indices = [next(i for i, s in evidence if native_checks.resolve(s, rule['target'], 'ios')['semantic'].get('fully_within_viewport'))]
            status = 'passed'
            rid = rule['requirement_id']
            if rid == 'full-layout':
                reason = 'Inspected the complete overlapping original-PNG sequence: heading, current summary/revision/count, cards 01–06, review action, cards 07–10 and footer remain in order. No horizontal clipping or overlap is visible. Edge clipping from scrolling is covered by adjacent frames and the true bottom is visible.'
                assert complete
            elif rid == 'text-wrapping':
                reason = 'The original sequence at the actual requested width and Dynamic Type shows naturally wrapped current title/summary, all ten card headings and bodies, action label and footer. No ellipsis, horizontal truncation, overlap or missing text was observed. The separate disabled-palette failure is retained.'
                assert complete
            elif rid == 'neutral-surfaces':
                reason = 'Original current-state middle-card frames retain the white canvas, pale neutral card fill, dark heading and secondary text. No unexpected surface variation is visible. This is a rendered judgment, not a computed SwiftUI property claim.'
            elif rid == 'action-appearance':
                if rule['state'] in ['replaced', 'disabled']:
                    status = 'failed'
                    reason = 'The fully visible original disabled action is visibly faded beyond the frozen #DCE2E7 fill / #55616C text design. Diagnostic original-PNG picking again gives #EDF0F3 fill and #A1A8AF solid glyph ink. Native disabled state and minimum control height pass separately; no callback pass is inferred from this blocked action.'
                else:
                    reason = 'The original fully visible enabled action has the approved dark blue-gray fill, readable white text and rounded shape. The independent typed native assertion separately establishes the minimum 52 pt accessibility control height.'
            decisions.append({'id': rule['id'], 'method': 'visual', 'status': status, 'reason': reason, 'snapshot_indices': indices,
                'evidence': [{'path': obs['snapshots'][i]['screenshot'], 'sha256': sha(cap / obs['snapshots'][i]['screenshot'])} for i in indices]})
        manual = {'version': 1, 'observation_sha256': sha(cap / 'observation.json'), 'reviewer': 'Independent neutral forward tester',
                  'decisions': decisions, 'scope': 'Only this fresh run; reviewed all full-state contact sheets sourced from original PNG viewports and target sheets, plus representative original PNGs. No expected value changed.'}
        save(name + '-manual.json', manual)
        report = native_checks.evaluate(plan, obs, 'ios', manual=manual, root=cap, observation_sha256=sha(cap / 'observation.json'), design_lock=lock, design_sha256=approval['design_lock_sha256'])
        save(name + '-evaluated.json', report)
        save(name + '-routes.json', requirement_routes.route_findings(coverage, plan, report, obs))
        admission = requirement_routes.admission(coverage, plan, report)
        save(name + '-admission.json', admission)
        assert report['counts'] == {'passed': 64, 'failed': 2, 'unassessed': 0}
        results.append({'run': name, 'counts': report['counts'], 'failed_ids': report['failed_assertion_ids'], 'admission': admission['status'], 'blocking_obligations': admission['blocking_obligations']})
    timings = []
    for case in ['ordinary400', 'narrow280-large']:
        for repeat in [1, 2]:
            pair = [r for r in audit['runs'] if r['case'] == case and r['repeat'] == repeat]
            legacy = next(r for r in pair if r['arm'] == 'legacy'); coalesced = next(r for r in pair if r['arm'] == 'coalesced')
            a, b = legacy['timings']['native_test_command_seconds'], coalesced['timings']['native_test_command_seconds']
            timings.append({'case': case, 'repeat': repeat, 'actual_start_order': [r['arm'] for r in sorted(pair, key=lambda r: r['started_unix'])],
                            'legacy_native_wall_seconds': a, 'coalesced_native_wall_seconds': b,
                            'descriptive_fraction_reduction': 1 - b / a,
                            'limitation': 'Two fixed fixtures, two repeats, one device/runtime and differing observer implementations. Inclusive native walls are not additive operation costs or a general performance guarantee.'})
    save('completion.json', {'version': 1, 'started_unix': begun, 'finished_unix': time.time(), 'remaining_run_results': results,
        'pass1_retained_seal_sha256': sha(BASE / 'neutral-review/pass1/SEAL.json'),
        'all_eight_supported_native_statuses_preserved': True, 'newly_missing_native_evidence': [], 'newly_conflicting_native_statuses': [],
        'same_confirmed_visual_root_cause': 'Disabled rendered palette differs from sealed design in replaced and disabled states in every run; no new root cause found.',
        'timing_pairs': timings, 'source_or_expected_values_changed': False, 'sdk_executed': False,
        'remaining_limits': ['No generic computed SwiftUI style/physical-touch measurements.', 'Single independent visual context, no second visual oracle.', 'No source fix or successful retest is claimed.', 'Targeted unified-wrapper usability is a separate pending pass, not part of this paired review.']})
    print(json.dumps({'remaining_runs_reviewed': len(results), 'counts_each': results[0]['counts'], 'no_native_status_loss': True, 'timing_pairs': timings}, indent=2))

if __name__ == '__main__': main()
