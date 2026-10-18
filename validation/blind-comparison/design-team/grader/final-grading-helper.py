#!/usr/bin/env python3
"""Prepare, validate and seal FINAL review records without inspecting packets.

Only frozen design artifacts, prior grader seals, and explicit grader records
are opened. Evidence paths are stored/checked as strings, never opened here.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent.parent
G = ROOT / 'grader'
H = runpy.run_path(str(G / 'grading-helper.py'))
OUTCOMES = H['OUTCOMES']
METHODS = H['METHODS']
RUNTIME_SCOPES = H['RUNTIME_SCOPES']
ANONYMOUS_IDS = ['submission-06e6f6', 'submission-bab86f']
FORBIDDEN_SEEN_FLAGS = ['treatment_mapping_seen', 'assignment_seen',
                        'implementation_directory_read', 'skill_files_read',
                        'sibling_conversations_read']
PROTECTED = [ROOT / p for p in H['DESIGN']] + [
    G / (i + suffix) for i in ANONYMOUS_IDS
    for suffix in ['-D0-sealed.json', '-D0-sealed.json.sha256']
] + [G / n for n in ['detection-matching.json', 'detection-matching.json.sha256',
                     'detection-matching-seal.json']]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def protected_hashes():
    return {str(p.relative_to(ROOT)): sha(p) for p in PROTECTED}


def oracle():
    return json.loads((ROOT / 'private/oracle.json').read_text())


def baseline(anonymous_id):
    if anonymous_id not in ANONYMOUS_IDS:
        raise ValueError('Use one of the existing anonymous IDs; no assignment lookup is available.')
    p = G / (anonymous_id + '-D0-sealed.json')
    return json.loads(p.read_text())['rating']


def incidence_key(platform, case_id, rule_id):
    return '/'.join([platform, case_id, rule_id])


def old_failures(anonymous_id):
    rows = []
    for case in baseline(anonymous_id)['cases']:
        for inc in case['incidences']:
            if inc['status'] == 'failed':
                rows.append({'platform': case['platform'], 'case_id': case['case_id'],
                             'rule_id': inc['rule_id'],
                             'checks': [c for c in inc['checks'] if c['status'] == 'failed']})
    return rows


def empty_incidence(rule):
    return {'rule_id': rule['rule_id'], 'applicable': True,
            'applicability_reason': 'Assess only relevant branches of the frozen public rule.',
            'coverage_complete': False, 'coverage': 'none', 'status': 'not_assessed',
            'checks': [], 'findings': [], 'visual_rating': None,
            'missing_branches': [], 'methods_observed': []}


def accepted_repair_methods(old_check):
    if old_check['scope'] in RUNTIME_SCOPES:
        return ['native_semantics']
    if old_check['scope'] == 'rendered' or old_check['method'] in ['native_pixels', 'blinded_visual']:
        return ['native_pixels', 'blinded_visual']
    return [old_check['method']]


def make_template(anonymous_id):
    spec = oracle()
    cases = []
    for fixture in spec['fixtures']:
        for platform in fixture['platforms']:
            cases.append({'case_id': fixture['fixture_id'], 'platform': platform,
                          'fixture_stage': fixture['stage'], 'packet_pseudonym': None,
                          'packet_paths': [],
                          'build': {'status': 'not_assessed', 'evidence': None, 'observation': None},
                          'render': {'status': 'not_assessed', 'evidence': None, 'observation': None},
                          'viewport_evidence': {'top': None, 'bottom': None,
                                                'lower_content_assessed': False},
                          'incidences': [empty_incidence(r) for r in spec['rules']]})
    reassess = []
    for old in old_failures(anonymous_id):
        aspects = []
        inc = next(i for c in cases if c['case_id'] == old['case_id'] and c['platform'] == old['platform']
                   for i in c['incidences'] if i['rule_id'] == old['rule_id'])
        for check in old['checks']:
            aspects.append({'aspect': check['aspect'], 'D0_scope': check['scope'],
                            'D0_method': check['method'], 'D0_observation': check['observation'],
                            'D0_evidence': check['evidence'],
                            'accepted_final_methods': accepted_repair_methods(check),
                            'status': 'not_assessed', 'method': None,
                            'execution': 'not_executed', 'evidence': [],
                            'observation': 'Awaiting anonymous FINAL native evidence.'})
            inc['checks'].append({'aspect': check['aspect'], 'scope': check['scope'],
                                  'status': 'not_assessed', 'method': None,
                                  'execution': 'not_executed', 'evidence': [],
                                  'observation': 'Old failing aspect must be independently reassessed from FINAL evidence.'})
            inc['missing_branches'].append(check['aspect'])
        reassess.append({'platform': old['platform'], 'case_id': old['case_id'],
                         'rule_id': old['rule_id'], 'status': 'not_assessed',
                         'evidence': [], 'observation': 'No FINAL packet has been reviewed.',
                         'old_failing_aspects': aspects,
                         'whole_rule_result_independent': True})
    return {'schema_version': '1.0', 'artifact_role': 'ungraded_FINAL_template',
            'stage': 'FINAL', 'anonymous_implementation_id': anonymous_id,
            'reviewer_type': 'independent_AI_not_human_expert',
            'protected_artifact_sha256': protected_hashes(),
            'D0_sealed_baseline': str(G / (anonymous_id + '-D0-sealed.json')),
            'blinding': {**{k: False for k in FORBIDDEN_SEEN_FLAGS},
                         'self_review_claims_seen_in_prior_separate_matching_phase': True,
                         'D0_was_sealed_before_self_review_claims': True},
            'final_packet_root': None, 'final_source_sha256_from_manifest': None,
            'final_source_frozen_revision': None, 'review_started_at': None,
            'review_completed_at': None, 'global_blockers': [],
            'case_count': len(cases),
            'rule_incidence_count': sum(len(c['incidences']) for c in cases),
            'cases': cases, 'repair_reassessment': reassess,
            'new_failure_incidences': [], 'new_failure_aspects': [],
            'visual_anchors': spec['blinded_visual_rubric']['anchors'],
            'known_method_boundaries': spec['platform_method_policy'],
            'interpretation': 'Repair reassessment considers every old failing aspect only. The whole-rule matrix separately includes other missing branches, new failures and holdouts. No partial repair implies whole-rule pass.'}


def aggregate_repair(entry):
    aspects = entry.get('old_failing_aspects', [])
    if any(a.get('status') == 'failed' and a.get('execution') == 'observed' for a in aspects):
        return 'failed'
    if aspects and all(a.get('status') == 'passed' and a.get('execution') == 'observed'
                       and a.get('evidence') and a.get('observation') for a in aspects):
        return 'passed'
    return 'not_assessed'


def derived_new_failures(record):
    """Newly observed failure is not automatically a newly introduced regression."""
    anon = record['anonymous_implementation_id']
    old_cases = {(c['platform'], c['case_id']): c for c in baseline(anon)['cases']}
    old_failed = {incidence_key(o['platform'], o['case_id'], o['rule_id']): o for o in old_failures(anon)}
    new_incidences, new_aspects = [], []
    for case in record['cases']:
        for inc in case['incidences']:
            key = incidence_key(case['platform'], case['case_id'], inc['rule_id'])
            if inc['status'] == 'failed' and key not in old_failed:
                new_incidences.append({'platform': case['platform'], 'case_id': case['case_id'],
                                       'rule_id': inc['rule_id'], 'status': 'failed',
                                       'baseline_category': 'repair_holdout_newly_assessed' if case['fixture_stage'] == 'repair_holdout' else 'not_failed_in_D0'})
            old_inc = next((i for i in old_cases.get((case['platform'], case['case_id']), {}).get('incidences', []) if i['rule_id'] == inc['rule_id']), None)
            old_bad_aspects = {c['aspect'] for c in old_failed.get(key, {}).get('checks', [])}
            for check in inc['checks']:
                if check['status'] != 'failed' or check['aspect'] in old_bad_aspects:
                    continue
                prior = next((c for c in old_inc['checks'] if c['aspect'] == check['aspect']), None) if old_inc else None
                category = ('repair_holdout_newly_assessed' if not old_inc else
                            'previously_observed_pass' if prior and prior['status'] == 'passed' else
                            'previously_unassessed' if prior else 'new_aspect_not_checked_at_D0')
                new_aspects.append({'platform': case['platform'], 'case_id': case['case_id'],
                                    'rule_id': inc['rule_id'], 'aspect': check['aspect'],
                                    'status': 'failed', 'baseline_category': category,
                                    'introduced_regression_proven': category == 'previously_observed_pass',
                                    'evidence': check.get('evidence', []),
                                    'observation': check.get('observation')})
    return new_incidences, new_aspects


def has_final_packet_evidence(record, evidence):
    base = record.get('final_packet_root')
    if not base:
        return False
    root = Path(base)
    return any(Path(p).is_absolute() and (Path(p) == root or root in Path(p).parents)
               for p in evidence if isinstance(p, str))


def validate(record, require_sealable=False):
    errors, warnings = [], []
    if record.get('stage') != 'FINAL': errors.append('Expected FINAL stage.')
    for flag in FORBIDDEN_SEEN_FLAGS:
        if record.get('blinding', {}).get(flag) is not False:
            errors.append('Treatment blindness flag must explicitly remain false: ' + flag)
    if record.get('protected_artifact_sha256') != protected_hashes():
        errors.append('Protected design, D0 or matching bytes changed.')
    spec = oracle()
    methods = {r['rule_id']: set(r['measurement_methods']) for r in spec['rules']}
    expected_pairs = {(f['fixture_id'], p) for f in spec['fixtures'] for p in f['platforms']}
    pairs = [(c.get('case_id'), c.get('platform')) for c in record.get('cases', [])]
    if set(pairs) != expected_pairs or len(pairs) != len(expected_pairs):
        errors.append('Expected exactly 8 fixtures × 2 platforms, without omitted/duplicate cases.')
    if record.get('case_count') != len(expected_pairs): errors.append('case_count mismatch.')
    if record.get('rule_incidence_count') != len(expected_pairs)*len(methods): errors.append('rule_incidence_count mismatch.')
    fixture_stages = {f['fixture_id']: f['stage'] for f in spec['fixtures']}
    for case in record.get('cases', []):
        prefix = str(case.get('platform'))+'/'+str(case.get('case_id'))
        if case.get('fixture_stage') != fixture_stages.get(case.get('case_id')):
            errors.append(prefix+': initial/holdout stage differs from frozen oracle.')
        ids = [i.get('rule_id') for i in case.get('incidences', [])]
        if set(ids) != set(methods) or len(ids) != len(methods):
            errors.append(prefix+': all 23 public rules exactly once required.')
        for inc in case.get('incidences', []):
            key = prefix+'/'+str(inc.get('rule_id'))
            if inc.get('status') not in OUTCOMES: errors.append(key+': invalid outcome.')
            if not inc.get('applicable', True) and not inc.get('applicability_reason'):
                errors.append(key+': inapplicability requires a reason.')
            for check in inc.get('checks', []):
                status, method = check.get('status'), check.get('method')
                if status not in OUTCOMES: errors.append(key+': invalid check outcome.')
                if method is not None and method not in methods.get(inc.get('rule_id'), set()):
                    errors.append(key+': method not admitted by frozen rule.')
                if status in ['passed','failed']:
                    if check.get('execution') != 'observed' or not check.get('evidence') or not check.get('observation'):
                        errors.append(key+': observed evidence required for pass/fail.')
                if status == 'passed' and check.get('scope') in RUNTIME_SCOPES:
                    if method != 'native_semantics': errors.append(key+': source/pixels cannot pass runtime behavior.')
                if status == 'passed' and check.get('scope') == 'runtime_callback':
                    a, e = check.get('actual_callback_events'), check.get('expected_callback_events')
                    if a is None or e is None or a != e: errors.append(key+': actual and expected executed callback arrays required and must match.')
                if case.get('platform') == 'swiftui_ios' and check.get('aspect') == 'empty_AX_export' and status == 'failed':
                    errors.append(key+': known iOS host AX absence is not a component failure.')
            outcome, coverage = H['aggregate_incidence'](inc)
            if inc.get('status') != outcome or inc.get('coverage') != coverage:
                errors.append(key+': outcome/coverage inconsistent with assessed and missing branches.')
            rating = inc.get('visual_rating')
            if rating is not None:
                if inc.get('rule_id') not in ['TQ-VIS-01','TQ-VIS-02'] or type(rating.get('score')) is not int or not 1<=rating.get('score',0)<=5:
                    errors.append(key+': valid 1–5 anchored visual rating required.')
                if not rating.get('evidence') or not rating.get('specific_observation'):
                    errors.append(key+': rating requires native image evidence and observation.')
    old = old_failures(record['anonymous_implementation_id'])
    expected = {incidence_key(o['platform'],o['case_id'],o['rule_id']): o for o in old}
    entries = record.get('repair_reassessment', [])
    entry_keys = [incidence_key(e.get('platform',''),e.get('case_id',''),e.get('rule_id','')) for e in entries]
    if set(entry_keys) != set(expected) or len(entry_keys) != len(expected):
        errors.append('Repair reassessment must include EVERY D0 failed case×rule exactly once, no additions.')
    for entry in entries:
        key = incidence_key(entry['platform'],entry['case_id'],entry['rule_id'])
        if key not in expected: continue
        checks = {c['aspect']:c for c in expected[key]['checks']}
        aspects = entry.get('old_failing_aspects', [])
        if {a.get('aspect') for a in aspects} != set(checks) or len(aspects) != len(checks):
            errors.append(key+': every old failing aspect must be reassessed exactly once.')
        inc = next(i for c in record['cases'] if c['platform']==entry['platform'] and c['case_id']==entry['case_id'] for i in c['incidences'] if i['rule_id']==entry['rule_id'])
        for a in aspects:
            old_check = checks.get(a['aspect'])
            if not old_check: continue
            if a.get('D0_scope') != old_check['scope'] or a.get('D0_method') != old_check['method'] or a.get('D0_observation') != old_check['observation'] or a.get('D0_evidence') != old_check['evidence']:
                errors.append(key+': old failing-aspect description/evidence must remain unchanged.')
            if a.get('accepted_final_methods') != accepted_repair_methods(old_check):
                errors.append(key+': repair method boundary cannot be weakened.')
            if a.get('status') not in ['passed','failed','not_assessed']:
                errors.append(key+': repair aspect status must be passed/failed/not_assessed.')
            if a.get('status') in ['passed','failed']:
                if a.get('execution')!='observed' or not a.get('evidence') or not a.get('observation'):
                    errors.append(key+': old-aspect result requires observed FINAL evidence.')
                if a.get('method') not in accepted_repair_methods(old_check):
                    errors.append(key+': rendered repair cannot pass from source review; runtime repair needs actual native execution.')
                if not has_final_packet_evidence(record,a.get('evidence',[])):
                    errors.append(key+': old D0/self-review artifacts cannot substitute for FINAL native evidence.')
                counterpart = [c for c in inc['checks'] if c.get('aspect')==a['aspect']]
                if len(counterpart)!=1 or any(counterpart[0].get(k)!=a.get(k) for k in ['status','method','execution','evidence','observation']):
                    errors.append(key+': repair result must agree with the same aspect in the whole-rule matrix.')
            elif a.get('execution')=='observed' and a.get('method')=='source_review':
                # Source may supplement a missing rendered observation; it cannot repair it.
                pass
        if entry.get('status') != aggregate_repair(entry):
            errors.append(key+': repair status must reflect ALL old failing aspects, not one successful subset.')
        if entry.get('status') in ['passed','failed'] and (not entry.get('evidence') or not entry.get('observation')):
            errors.append(key+': repaired/still-failed entry needs evidence and observation.')
        if entry.get('status') not in ['passed','failed','not_assessed']:
            errors.append(key+': invalid repair outcome.')
        if entry.get('whole_rule_result_independent') is not True:
            errors.append(key+': repair success is separate from whole-rule completeness/new failures.')
    new_inc, new_aspects = derived_new_failures(record)
    if record.get('new_failure_incidences') != new_inc:
        errors.append('new_failure_incidences must separately match newly failed matrix incidences.')
    if record.get('new_failure_aspects') != new_aspects:
        errors.append('new_failure_aspects must separately include all newly failed aspects, including inside an old failing rule.')
    if require_sealable:
        if record.get('artifact_role') != 'FINAL_rating': errors.append('Ungraded FINAL template cannot be sealed.')
        for field in ['final_packet_root','final_source_sha256_from_manifest','final_source_frozen_revision','review_started_at','review_completed_at']:
            if not record.get(field): errors.append('Sealing requires '+field)
        packet_root = record.get('final_packet_root')
        if packet_root and (not Path(packet_root).is_absolute() or Path(packet_root).name in ['d0','self-review']):
            errors.append('FINAL packet root must be an explicit new anonymous packet path.')
    return {'valid':not errors,'errors':errors,'warnings':warnings}


def summarize(record):
    return {'anonymous_id':record['anonymous_implementation_id'],
            'stage':'FINAL','global_blockers':record.get('global_blockers',[]),
            'matrix':{p:{'outcomes':dict(Counter(i['status'] for c in record['cases'] if c['platform']==p for i in c['incidences'])),
                         'coverage':dict(Counter(i['coverage'] for c in record['cases'] if c['platform']==p for i in c['incidences']))} for p in ['compose_android','swiftui_ios']},
            'repair_reassessment':dict(Counter(e['status'] for e in record['repair_reassessment'])),
            'new_failure_incidence_count':len(record['new_failure_incidences']),
            'new_failure_aspect_count':len(record['new_failure_aspects']),
            'note':'Repair results do not replace whole-rule outcomes or evidence coverage. Holdout failures are newly observed, not automatically introduced regressions.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest='command',required=True)
    init=subs.add_parser('init');init.add_argument('--anonymous-id',choices=ANONYMOUS_IDS,required=True);init.add_argument('--out',required=True)
    for name in ['validate','summarize','derive-new-failures']:
        p=subs.add_parser(name);p.add_argument('record')
    seal=subs.add_parser('seal');seal.add_argument('record');seal.add_argument('--out',required=True)
    args=parser.parse_args()
    if args.command=='init':
        p,d=H['write_json'](args.out,make_template(args.anonymous_id),exclusive=True)
        print(json.dumps({'created':str(p),'sha256':d,'graded':False}));return
    record=H['read_record'](args.record)
    if args.command=='summarize':print(json.dumps(summarize(record),ensure_ascii=False,indent=2));return
    if args.command=='derive-new-failures':
        a,b=derived_new_failures(record)
        print(json.dumps({'new_failure_incidences':a,'new_failure_aspects':b},ensure_ascii=False,indent=2));return
    verdict=validate(record,require_sealable=args.command=='seal')
    if args.command=='validate' or not verdict['valid']:
        print(json.dumps(verdict,ensure_ascii=False,indent=2))
        if not verdict['valid']:sys.exit(1)
        return
    p,d=H['write_json'](args.out,{'seal_type':'FINAL_rating_with_separate_repair_reassessment',
                               'sealed_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                               'rating':record},exclusive=True)
    with H['output_path'](str(p)+'.sha256').open('x') as f:f.write(d+'  '+p.name+'\n')
    print(json.dumps({'sealed':str(p),'sha256':d}))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError) as e:
        print(str(e),file=sys.stderr);sys.exit(2)
