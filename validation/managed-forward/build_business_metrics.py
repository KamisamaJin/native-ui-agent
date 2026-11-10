#!/usr/bin/env python3
"""Derive the closed paired-study metrics from original sealed records; no SDK."""
import argparse
import json
from pathlib import Path

import business
import costs_business

R = Path(__file__).resolve().parent


def compute():
    business.authorize('quality')
    common = business.read(R / 'business-quality/cause-matching/common-causes.json')
    mapping = business.read(R / 'business-administration/REVEAL.json')
    costs = costs_business.compute()
    commands = business.read(R / 'business-administration/independent-binding-v3-commands.json')
    assert len(commands) == 12 and all(row['exit_code'] == 0 for row in commands)
    accepted_at = max(business.read(R / 'gates/quality.json')['sealedAtUnix'],
                      max(row['finished_at_unix'] for row in commands))
    cleanup = business.read(R / 'CLEANUP-2.json')
    assert cleanup['status'] == 'complete' and not cleanup['post_cleanup']['path_exists']
    arms = {}
    causes = common['initial_causes']
    for arm, version in mapping['arms'].items():
        repaired = sum(c['status_by_arm'][arm]['repaired'] for c in causes)
        residual = sum(c['status_by_arm'][arm]['residual'] for c in causes)
        assert not any(c['status_by_arm'][arm]['unresolved'] for c in causes)
        delivery = common['complete_delivery'][arm]
        alerts = common['alerts_by_arm'][arm]['deduplicated_common_cause_counts']
        cost = costs['arms'][arm]
        gross = accepted_at - costs['author_dispatch_at_unix']
        arms[arm] = {
            'tool': version, 'confirmed_initial_causes': len(causes),
            'repaired': repaired, 'residual': residual,
            'final_miss_rate': residual / len(causes) if causes else None,
            'repair_rate': repaired / len(causes) if causes else None,
            'business_miss_rate': None, 'business_repair_rate': None,
            'new_confirmed_regressions': len(common['regressions'][arm]['confirmed']),
            'product_alerts': alerts,
            'false_positive_rate': alerts['FP'] / (alerts['TP'] + alerts['FP']) if alerts['TP'] + alerts['FP'] else None,
            'required_U': delivery['required_U_count'],
            'required_counts': delivery['complete_required_counts'],
            'complete_delivery': delivery['accepted'], 'delivery_attempts': 1,
            'author_to_public_self_closure_seconds': cost['author_to_public_self_closure_seconds'],
            'author_to_complete_acceptance_gross_seconds': gross,
            'successful_delivery_gross_seconds': gross if delivery['accepted'] else None,
            'native_command_work_seconds': sum(cost['native_command_seconds_by_platform'].values()),
            'peak_configured_allocated_bytes': cost['configured_group_peak_allocated_bytes_through_own_hidden_native'],
        }
    assert common['initial_category_counts']['business'] == 0
    inputs = ['gates/quality.json', 'business-quality/cause-matching/seal.json',
              'business-administration/REVEAL.json', 'business-administration/independent-binding-v3-commands.json',
              'business-administration/whole-study-meter.jsonl', 'business-administration/whole-study-meter-2.jsonl',
              'business-administration/public-closure-A.json', 'business-administration/public-closure-B.json',
              'operators/owned-device-final-check.json', 'CLEANUP-2.json']
    return {
        'version': 1, 'mapping': mapping['arms'], 'input_sha256': {p: business.sha(R / p) for p in inputs},
        'quality_common_seal_sha256': business.sha(R / 'business-quality/cause-matching/seal.json'),
        'initial_confirmed_causes': len(causes), 'initial_category_counts': common['initial_category_counts'],
        'complete_acceptance_at_unix': accepted_at, 'arms': arms, 'timing': costs,
        'cleanup': {'receipt': 'CLEANUP-2.json', 'removed_file_count': cleanup['pre_cleanup']['file_count'],
                    'removed_allocated_file_bytes': cleanup['pre_cleanup']['allocated_file_bytes'],
                    'remaining_owned_devices': cleanup['remaining_owned_devices'],
                    'cache_exists_after': cleanup['post_cleanup']['path_exists']},
        'limits': [
            'One paired component PR, descriptive not population evidence; baseline v11 already has the Skill.',
            'Business/functional initial defect denominator is zero; business miss and repair rates are N/A.',
            'Complete-delivery gross endpoints share hidden/reviewer/cohort barriers; not an isolated single-PR cost benchmark.',
            'Command sums are serial-equivalent work; concurrent wall-time endpoints are separately reported.',
            'Common acquisition/replay adapter failures are retained, not attributed as a treatment benefit.',
            'Sampled configured allocated-byte peaks exclude global SDK caches and reviewer packets/crops; not exact APFS physical use.',
            'Source intent is not runtime computed style; Android semantic OnClick is not OS physical touch.',
        ],
    }


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    result = compute()
    target = R / 'METRICS.json'
    if args.check:
        assert business.read(target) == result, 'Published metrics differ from original closed records'
        print(json.dumps({'status': 'PASS', 'metrics': str(target)}))
    else:
        business.save(target, result)
        print(json.dumps({'status': 'created', 'metrics': str(target)}))
