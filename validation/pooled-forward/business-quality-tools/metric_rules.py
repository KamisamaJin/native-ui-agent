"""Fixed five-PR arithmetic over separately sealed anonymous adjudication.

This module makes no quality judgments. Authenticate the cause/alarm/matcher
barriers and reveal before supplying their records. Unknown relations remain
unknown; they are never counted as removal or as a successful delivery.
"""
import math
import statistics


CASES = {f'Case0{i}' for i in range(1, 6)}


def need(value, message):
    if not value:
        raise ValueError(message)


def fraction(numerator, denominator):
    need(type(numerator) is int and type(denominator) is int and
         0 <= numerator <= denominator, 'Nonnegative bounded integer counts required')
    return {'numerator': numerator, 'denominator': denominator,
            'value': numerator / denominator if denominator else None}


def seconds(value):
    need(type(value) in {int, float} and math.isfinite(value) and value >= 0,
         'Measured nonnegative finite seconds required; repair the clock ledger instead of clamping')
    return value


def unique(rows, key='id'):
    need(isinstance(rows, list) and all(isinstance(r, dict) and isinstance(r.get(key), str)
                                      and r[key] for r in rows), 'Explicit identified rows required')
    result = {r[key]: r for r in rows}
    need(len(result) == len(rows), 'Duplicate metric unit')
    return result


def summarize(cases, arm, assignment):
    """Compute one arm, retaining all five attempts and explicit unknowns.

    cases: five anonymous case records; assignment: {case_id: {A: X|Y,B: X|Y}}.
    final metrics use version rows, never names or failed atomic-row counts.
    Costs supplied here are original measured episode sums, not an estimate.
    """
    by = unique(cases, 'case_id')
    need(set(by) == set(assignment) == CASES and arm in {'A', 'B'}, 'Exactly five paired PRs required')
    totals = dict(initial=0, present=0, removed=0, unknown_relation=0,
                  detected_initial=0, attempted_initial=0, attempted_removed=0,
                  true_alarm=0, false_alarm=0, unresolved_alarm=0,
                  false_positive_validation=0, unresolved_positive_validation=0,
                  regression=0, unresolved_regression=0, delivered=0)
    public, hidden, attempted_rows = [], [], []
    all_causes = []
    for case_id in sorted(by):
        case = by[case_id]
        pair = assignment[case_id]
        need(set(pair) == {'A', 'B'} and set(pair.values()) == {'X', 'Y'}, 'Exact paired reveal required')
        need(set(case['versions']) == {'X', 'Y'}, 'Both sealed anonymous final versions required')
        initial = unique(case['confirmed_initial_causes'])
        final = case['versions'][pair[arm]]
        relations = unique(final['initial_relations'], 'initial_cause_id')
        need(set(relations) == set(initial), 'Every confirmed initial cause needs one final relation')
        for cause_id, row in relations.items():
            need(row['status'] in {'present', 'removed', 'unresolved'}, 'Unknown final cause relation')
            need(row.get('evidence') and isinstance(row['evidence'], list), 'Explicit relation evidence required')
        status = {k: r['status'] for k, r in relations.items()}
        alarms = unique(final['defect_alarms'])
        detected = set()
        for row in alarms.values():
            need(row['verdict'] in {'true', 'false', 'unresolved'}, 'Explicit adjudicated alarm verdict required')
            ids = row['initial_cause_ids']
            need(isinstance(ids, list) and len(set(ids)) == len(ids) and set(ids) <= set(initial),
                 'Alarm correspondence must name actual initial causes')
            if row['verdict'] != 'true':
                need(not ids, 'False/unresolved alarms cannot earn genuine detection credit')
            else:
                detected.update(ids)
            totals[row['verdict'] + '_alarm'] += 1
        repairs = unique(final['attempted_repairs'])
        attempted = set()
        for row in repairs.values():
            ids = row['initial_cause_ids']
            need(isinstance(ids, list) and len(set(ids)) == len(ids) and set(ids) <= set(initial)
                 and row.get('evidence'), 'Attempted repair needs cause correspondence and actual evidence')
            attempted.update(ids)
        regressions = unique(final['new_regressions'])
        need(all(r.get('evidence') for r in regressions.values()), 'Confirmed regressions require evidence')
        uncertain = unique(final['unresolved_regressions'])
        claims = unique(final['positive_validation_claims'])
        need(all(r['verdict'] in {'true', 'false', 'unresolved'} for r in claims.values()),
             'Positive claims remain separate from defect alarms')
        obligations = final['delivery_obligations']
        need(set(obligations) == {'public_current_all_must_passed', 'private_current_all_must_passed',
                                 'source_all_must_passed', 'owned_resources_closed', 'independent_quality_complete'}
             and all(type(v) is bool for v in obligations.values()), 'All five explicit delivery gates required')
        complete = (all(obligations.values()) and all(v == 'removed' for v in status.values())
                    and not regressions and not uncertain and not final['unresolved_quality'])
        p, h = seconds(final['public_wall_seconds']), seconds(final['hidden_validation_wall_seconds'])
        public.append(p); hidden.append(h)
        totals['initial'] += len(initial)
        totals['present'] += sum(v == 'present' for v in status.values())
        totals['removed'] += sum(v == 'removed' for v in status.values())
        totals['unknown_relation'] += sum(v == 'unresolved' for v in status.values())
        totals['detected_initial'] += len(detected)
        totals['attempted_initial'] += len(attempted)
        totals['attempted_removed'] += sum(status[k] == 'removed' for k in attempted)
        totals['regression'] += len(regressions)
        totals['unresolved_regression'] += len(uncertain)
        totals['false_positive_validation'] += sum(r['verdict'] == 'false' for r in claims.values())
        totals['unresolved_positive_validation'] += sum(r['verdict'] == 'unresolved' for r in claims.values())
        totals['delivered'] += int(complete)
        attempted_rows.append({'case_id': case_id, 'anonymous_version': pair[arm],
                               'complete_delivery': complete, 'public_wall_seconds': p,
                               'hidden_validation_wall_seconds': h,
                               'unresolved_initial_relations': sum(v == 'unresolved' for v in status.values())})
        all_causes.extend(case_id + ':' + k for k in initial)
    d, count = totals['delivered'], totals['initial']
    p, h = sum(public), sum(hidden)
    return {'version': 1, 'arm': arm, 'attempts': 5, 'counts': totals,
            'final_residual_miss_fraction': fraction(totals['present'], count),
            'unresolved_initial_relation_fraction': fraction(totals['unknown_relation'], count),
            'initial_detection_fraction': fraction(totals['detected_initial'], count),
            'repair_fraction': fraction(totals['removed'], count),
            'attempted_repair_fraction': fraction(totals['attempted_removed'], totals['attempted_initial']),
            'false_discovery_fraction': fraction(totals['false_alarm'], totals['false_alarm'] + totals['true_alarm']),
            'complete_delivery_fraction': fraction(d, 5),
            'cost': {'all_attempt_public_seconds': p, 'public_median_seconds': statistics.median(public),
                     'public_range_seconds': [min(public), max(public)], 'hidden_validation_seconds': h,
                     'combined_seconds': p + h, 'successful_delivery_seconds': p / d if d else None,
                     'combined_successful_delivery_seconds': (p + h) / d if d else None,
                     'model_billing': None, 'tokens': None, 'human_monetary_cost': None},
            'attempt_records': attempted_rows,
            'scope': 'Arithmetic over externally sealed evidence-backed adjudication. Unknowns are explicit, zero denominators N/A. Common initial/oracle/research/matcher costs are reported separately; false discovery is not statistical FPR.'}
