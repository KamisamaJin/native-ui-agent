#!/usr/bin/env python3
"""Project sealed independent actuals into isolated post-trial review stores.

No renderer, expected override, source edit or arm default behavior is involved.
Original actuals and all range citations remain immutable beside the projection.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import business

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / 'candidate-v12.6/scripts'))
import design_contract as d
import evidence_responsibility as er
import evidence_review
import feedback_loop


def rows(path):
    value = business.read(path)
    return value if isinstance(value, list) else value.get('actuals', value.get('rows', []))


def project_source(config, original, candidate, platform):
    compiled = er.compile_contract(config, business.read(config['plan']), business.read(config['design_lock']))
    claims = {c['id']: c for c in compiled['claims'] if c['method'] == 'source'}
    selected = [r for r in rows(original) if r['candidate'] == candidate and r['platform'] == platform]
    assert {r['claim_id'] for r in selected} == set(claims)
    projected = []
    proof = []
    packet = R / 'business-quality/packet-public'
    for row in selected:
        claim = claims[row['claim_id']]
        cites = []
        for ref in row['citations']:
            relative = ref.get('path', ref.get('packet_path'))
            if not relative or not (packet / relative).is_file():
                continue  # Non-code native provenance stays in the original.
            p = packet / relative
            actual_sha = business.sha(p)
            if ref.get('sha256') and actual_sha != ref['sha256']:
                raise ValueError('Original source citation identity changed')
            matches = [Path(name) for name, expected in claim['files'].items() if expected == actual_sha]
            if len(matches) != 1:
                continue
            target = matches[0]
            assert business.sha(target) == actual_sha
            start = ref.get('line_start', ref.get('line'))
            end = ref.get('line_end', start)
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(target.read_text().splitlines()):
                raise ValueError('Independent citation has no valid original line range')
            cites.extend({'path': str(target), 'line': line} for line in range(start, end + 1))
        cites = [dict(t) for t in sorted({tuple(sorted(v.items())) for v in cites})]
        if row['observed'] is not None and not cites:
            raise ValueError('No byte-equivalent approved source citation for ' + row['claim_id'])
        projected.append({'id': row['claim_id'], 'observed': row['observed'], 'reason': row['reason'], 'citations': cites})
        proof.append({'id': row['claim_id'], 'original_actual_file': str(original), 'original_actual_sha256': business.sha(original),
                      'citation_projection': 'Exact byte-equivalent subject path lookup; original inclusive ranges expanded into the tool single-line wire format. No value, reason or expectation changed.'})
    return {'version': 1, 'observations': projected}, proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reviewer', choices=['1', '2'], required=True)
    parser.add_argument('--candidate', choices=['A', 'B', 'initial'], required=True)
    parser.add_argument('--platform', choices=['ios', 'android'], required=True)
    args = parser.parse_args()
    business.authorize('self-finals')
    reviewer = R / 'business-quality' / ('reviewer-' + args.reviewer)
    initial = args.candidate == 'initial'
    original = R / 'cache/study' / ('initial-hidden/runs' if initial else 'arms/' + args.candidate + '/runs/Hidden') / args.platform
    config = business.read(original / 'config.json')
    output = R / 'cache/study/independent-bindings' / ('reviewer-' + args.reviewer) / args.candidate / args.platform
    output.mkdir(parents=True, exist_ok=False)
    config['review_store'] = str(output / 'image-store')
    config['source_review_store'] = str(output / 'source-store')
    business.save(output / 'config.json', config)
    if initial:
        source_file = reviewer / 'source-actuals-initial-hidden.json'
        if not source_file.exists():
            source_file = reviewer / 'initial-hidden-source-actuals.json'
        image_file = reviewer / ('initial-hidden-' + args.platform + '-submission.json')
    else:
        source_file = reviewer / ('source-actuals-hidden-finals.json' if args.reviewer == '1' else 'hidden-finals-source-actuals.json')
        image_file = reviewer / ('hidden-' + args.candidate + '-' + args.platform + '-submission.json')
    submission, proof = project_source(config, source_file, args.candidate, args.platform)
    business.save(output / 'source-projection.json', submission)
    business.save(output / 'projection-provenance.json', proof)
    source_reference = er.bind(config, submission, output / 'source-binding.json')
    capture = original / 'cycle/capture/result.json'
    image_reference = evidence_review.bind(config, capture, business.sha(capture), image_file, business.sha(image_file), output / 'image-store/original-review')
    cycle = original / 'cycle/cycle.json'
    complete = feedback_loop.complete_review(config, cycle, business.sha(cycle), image_reference, output / 'completion')
    business.save(output / 'evaluation.json', {'at_unix': time.time(), 'candidate': args.candidate, 'platform': args.platform,
                                             'reviewer': args.reviewer, 'status': complete['status'],
                                             'source_reference': source_reference, 'image_reference': image_reference,
                                             'scope': 'Isolated common independent post-trial evaluation. No SDK or arm default backport; all original actuals retained.'})
    print(json.dumps({'candidate': args.candidate, 'platform': args.platform, 'reviewer': args.reviewer, 'status': complete['status']}))


if __name__ == '__main__':
    main()
