#!/usr/bin/env python3
"""Write this panel's independently determined, original-evidence judgments."""
import collections
import json
from pathlib import Path

BASE = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT = BASE / 'claim-judgments/one/T1'
native = json.loads((OUT / 'native-inspection.json').read_text())
originals = {}
for source in ['source-a', 'source-b']:
    transport = json.loads((BASE / f'evaluation-inputs/claims/T1/{source}/claims.json').read_text())
    originals[source] = [c for c in transport['claims'] if c['original_status'] == 'failed']
    results, duplicates = [], []
    for claim in originals[source]:
        cid = claim['claim_id']
        if claim.get('duplicate_of'):
            parent = next(c for c in transport['claims'] if c['claim_id'] == claim['duplicate_of'])
            assert parent['origin'] == 'machine' and parent['original_status'] == 'failed'
            assert parent['original_scope'] == claim['original_scope']
            duplicates.append({'claim_id': cid, 'duplicate_of': claim['duplicate_of'],
                               'reason': 'Explicit original_typed_native_check duplicate of the same original machine failure, with identical original scope. Original artifact, SHA and cited screenshots were inspected; excluded from unique alarms as instructed.'})
            continue
        if claim['origin'] == 'machine':
            proof = next(x for x in native['original_color_claims'] if x['claim_id'] == cid)
            expected = proof['original_expected']
            actuals = sorted({s['sample']['argb'] for s in proof['samples']})
            assert all(s['sample']['status'] == 'measured' and s['sample']['argb'] != expected for s in proof['samples'])
            assert all(s['state_id'] == claim['state'] and s['capture_consistent'] for s in proof['samples'])
            key = claim['original_scope'][0]
            assert key in {r['key'] for r in native['common_product_rows'][source]}
            result = {'claim_id': cid, 'status': 'TP', 'supported_rows': [key],
                      'reason': f'The unchanged original plan explicitly expected #{expected:08X} ARGB on workshop.submit in this exact {claim["case"]}/{claim["platform"]}/{claim["state"]} state. Original artifact and plan match the transport and SHA. Direct inspection of every cited original screenshot shows the disabled primary button. Frozen native_pixels recomputation measures ' + ', '.join(f'#{a:08X}' for a in actuals) + ' in the approved solid side strip inside the unique, fully visible, disabled submit semantic box, with consistent native state binding. This is the specific original color finding, and the same exact row is failed/product in common D0. No later state or repair supplies detection support.',
                      'false_alarm_supported': False}
        else:
            facts = next(x for x in native['original_grid_claims'] if x['claim_id'] == cid)
            assert facts['facts']
            assert all(f['native_boxes']['workshop.canvas'][0]['frame']['width'] == 358 for f in facts['facts'])
            result = {'claim_id': cid, 'status': 'U', 'supported_rows': [],
                      'reason': 'The original finding explicitly alleges one grid column where two are required. Its cited original pixels and native facts support that limited finding: P1 iOS reports large Dynamic Type, a 358pt component canvas, and 326pt-wide choices a and b at the same x=38 with distinct vertical positions. The approved brief requires two columns here, but also explicitly excludes grid column count/breakpoint from the selected atomic ledger and says wrapping/overlap do not certify it. The broad original_scope is only an upper bound; this grid sentence detects none of its listed color, wrapping, control, or business atoms. There is no directly supported common-D0 failed/product row for this claim. The original grid issue is not explicitly disproved, so no false product alarm is established. Preserve unknown metric mapping rather than borrowing a color defect or extending the original finding.',
                      'false_alarm_supported': False}
        results.append(result)

    product = sorted(r['key'] for r in native['common_product_rows'][source])
    clusters = []
    if product:
        clusters = [{'id': 'ios-disabled-primary-rendering', 'rows': product,
                     'reason': 'All four rows are the same component-owned workshop.submit disabled appearance path in the same D0 SwiftUI source, spanning light P1/dark P2 and the two no-valid-selection states baseline/replaced. WorkshopSlotPlanner.swift paints palette.disabled in its label and applies PlainButtonStyle() plus .disabled(selected == nil) to the enclosing button. Its palette declares the approved opaque light/dark disabled colors. Direct original and common-D0 screenshots and frozen sampling reproduce #FFCFCDC5 versus #FFAAA99F in light, and #FF33474C versus #FF52666A in dark. The approved observer host supplies background, viewport and environment without an opacity/overlay/button-style substitution; the bridge only maps fixtures and callbacks. Thus these four correlated manifestations share the same disabled component rendering cause, rather than independent defects per state/theme. The exact internal SwiftUI alpha mechanism is inferred, but common source path, ownership and manifestation membership are directly supported. No Android row is in the confirmed product universe.',
                     'certainty': 'confirmed'}]
    judgment = {'claims': results, 'clusters': clusters, 'excluded_duplicates': duplicates,
                'input_integrity': 'All original_files hashes in this source claims transport match; every failed original pointer equals the transport original. The four machine original plans equal the original plan artifacts without changing expected/unit. All eight common D0 input manifests match their file hashes. See ../integrity.json and ../native-inspection.json.',
                'original_screenshot_inspection_coverage': {'method': 'Viewed all original failed-claim cited PNGs in full-screen contact sheets, then recomputed exact original native pixel strips for the four color claims. Original SHA checks precede inspection. Common D0 product frames were separately viewed and recomputed.',
                    'source_sheets': ['../source-a-grid-inspection.png'] if source == 'source-a' else ['../source-b-grid-inspection.png', '../source-b-colors-inspection.png'],
                    'unique_original_screenshots': 7 if source == 'source-a' else 14,
                    'manifest': '../screenshot-manifest.json', 'facts': '../native-inspection.json'},
                'schema_descriptor_limitations': ['Grid count is an explicit full-brief requirement outside the selected atomic ledger. It cannot be reformatted into a color/wrapping/control failure. No original expected/unit/descriptor has been edited.',
                    'No schema rejection alone is used as FP evidence. Only original_status=failed alarms are judged; successful and unassessed observations remain nonalarms.'],
                'preserved_uncertainties': ['AI consensus is not human gold. These judgments are relative to the common D0 confirmed product universe; unsupported scope mapping stays U.',
                    'Precise internal SwiftUI disabled compositing is inferred, separate from directly observed component-owned surface mismatch and source-linked grouping.',
                    'FINAL acceptance was read only as permitted context and provides no original detection or cause-membership credit.'],
                'confirmed_common_d0_product_keys': product,
                'nonfailure_observations_not_judged': sum(c['original_status'] != 'failed' for c in transport['claims'])}
    directory = OUT / source
    directory.mkdir(exist_ok=True)
    (directory / 'judgment.json').write_text(json.dumps(judgment, indent=2) + '\n')
    print(source, collections.Counter(r['status'] for r in results), 'duplicates', len(duplicates), 'clusters', len(clusters), 'product rows', len(product))
(OUT / 'original-failed-claims.json').write_text(json.dumps(originals, indent=2) + '\n')
