import json,hashlib
from pathlib import Path
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT=BASE/'claim-judgments/two/T3'
products=json.loads((OUT/'common-confirmed-product-rows.json').read_text())
pixels=json.loads((OUT/'original-pixel-recomputation.json').read_text())
for source in ['source-a','source-b']:
    transport=json.loads((BASE/'evaluation-inputs/claims/T3'/source/'claims.json').read_text())
    failed=[c for c in transport['claims']if c['original_status']=='failed']
    claims=[];excluded=[]
    for c in failed:
        if c.get('duplicate_of'):
            excluded.append({'claim_id':c['claim_id'],'duplicate_of':c['duplicate_of'],
                             'reason':'Explicit transport machine-failure duplicate with identical original scope; retained outside the unique failure-alarm denominator.'})
            continue
        key=c['original_scope'][0];case,platform,state,rule=key.split('/')
        if rule=='current-summary':
            reason=(f'The unchanged original plan requires the exact {state} current summary. Original own-D0 native labels and the inspected exact-state PNG show '+
                    ('No work selected / 0 min after the same-instance revision replacement, although delivered fixture 1 seeds available b.'if state=='replaced'else
                     'only Brake inspection / 20 min, omitting incoming b, although fixture 1 seeds b and the demonstrated a toggle adds a.')+
                    ' Original capture bindings are stable; step 6 records successful caller_fixture_update without a business callback. This explicitly supports this state/summary row only, which common D0 confirms as a product failure.')
        elif rule=='primary-action-enabled':
            reason=('The original plan expects enabled=true. Own-D0 original native submit facts report false and the original replaced-state PNG shows the disabled action. Same-instance fixture replacement succeeded and delivered initialSelectedIDs=[b] with b available, so the action should be enabled. This is directly supported in the original state and is a common D0 confirmed product row; it is not inferred from a later repair.')
        elif rule=='successful-activation-callback':
            reason=('The original plan expects exactly [bicycle:submit:a,b]. Original raw step 8 demonstrates an enabled native xcui_tap (succeeded=true) under fixture 1 and its callback_delta contains exactly bicycle:submit:a. Original submitted-state native labels/PNG retain a only / 20 min. This directly establishes the earlier wrong current-set callback; common D0 independently confirms this product row.')
        elif rule=='primary-surface-color':
            rs=[p for p in pixels if p['claim_id']==c['claim_id']]
            argb=rs[0]['argb'];expected=rs[0]['expected']
            reason=(f'Original exact-state PNG and native submit box were inspected. Frozen native_pixels.sample on that same original evidence, using the approved fully-visible semantic side strip and zero tolerance, reproduces solid #{argb:08X} rather than unchanged original expected #{expected:08X}; all selected samples are measured contradictions. '+
                    ('The control is correctly disabled at baseline, but the production PlainButtonStyle/.disabled treatment changes its component-owned final fill despite the explicit approved palette. 'if state=='baseline'else
                     'After delivered revision 1 the control remains disabled with no b selection, so this original replaced-state fill contradicts the required enabled action palette. ')+
                    'This exact original color finding maps to the common D0 confirmed product row; no other state receives detection credit.')
        elif rule in ['content-wrapping','content-overlap']:
            reason=('The original failure explicitly identifies the disclosure leading glyphs cut by its own rounded button boundary. Inspected own-D0 exact-state originals show the curved cuts in Show/Hide and notes while the disclosure is fully inside the viewport; '+
                    ('for the expanded state, supplemental original snapshot 63 was inspected because the initial contact-sheet selection 65 was below the disclosure. 'if source=='source-b'and state=='expanded'else '')+
                    ('The approved wrapping question explicitly makes visible word clipping false. 'if rule=='content-wrapping'else
                     'The approved overlap question excludes unintended occlusion, including this masking of text by the control boundary. ')+
                    'Production Compose TextButton has zero content padding, and the glyph cuts move with the control rather than the host edge. This supports only the original state/aspect. Common D0 confirms the matching product row; the shared cause does not extend claim scope.')
        else:raise AssertionError(key)
        original=c.get('original_plan')or c['original']
        claims.append({'claim_id':c['claim_id'],'status':'TP','supported_rows':c['original_scope'],
                       'reason':reason,'false_alarm_supported':False,
                       'original_expected':original.get('expected'),'original_unit':original.get('unit')})
    universe=[r['key']for r in products[source]]
    baseline=[k for k in universe if '/ios/baseline/primary-surface-color'in k]
    android=[k for k in universe if '/android/'in k]
    clusters=[{'id':'ios-disabled-final-fill','rows':sorted(baseline),'certainty':'confirmed',
               'reason':'Both P1 light and P2 dark baseline actions correctly have no selected services and native enabled=false. Source explicitly fills the label with the approved disabled palette then applies PlainButtonStyle and .disabled. Original own/common PNGs and approved-strip samples show the same whole-button disabled rendering changes the final owned fill. The palettes differ but the same production style path and state trigger explain both rows. The exact platform compositing implementation remains inferred, without weakening the shared observed style cause.'},
              {'id':'android-disclosure-rounded-clip','rows':sorted(android),'certainty':'confirmed',
               'reason':'The same component TextButton disclosure uses PaddingValues(0.dp), full-width copy and the default rounded button shape. Exact-state originals show identical curved removal of leading portions of both wrapped lines in P2 baseline, expanded and submitted, clear of the viewport edge. Wrapping (lost readable glyph portions) and overlap (local text occlusion) are separate questions about that one clipping defect. No separate independent bug is invented per state or aspect.'}]
    if source=='source-a':
        state=[k for k in universe if k not in baseline and k not in android]
        clusters.append({'id':'ios-revision-selection-loss','rows':sorted(state),'certainty':'confirmed',
                         'reason':'In both P1 and P2, the live fixture advances to revision bicycle-1 with initialSelectedIDs=[b], stable new input hash and successful caller_fixture_update. The component nevertheless has no selected b: summary is empty, primary action is disabled and its replacement fill is consequently wrong. Demonstrated subsequent a toggle adds a, then submitted summary and callback contain only a. The same lost incoming b explains these 12 downstream rows through the shared chosenServices reducer and callback forwarding in the original source. Replaced color is grouped with the missing incoming selection because its required enabled palette depends on that state; the separately observed baseline disabled-fill defect is a contributing rendering effect, not another independent replacement manifestation. Exact SwiftUI onChange/closure mechanism is not proven, but source ownership, stable delivered input and common native sequence establish this shared product-state cause.'})
    value={'claims':claims,'clusters':clusters,'excluded_duplicate_claims':excluded,
           'nonfailure_observation_count':sum(c['original_status']!='failed'for c in transport['claims']),
           'integrity':{'all_original_files_sha256_match':True,'all_original_json_pointers_match':True,
                        'original_expected_and_unit_match_original_plans':True,
                        'details':'../input-integrity.json, ../common-input-integrity.json and ../original-plan-verification.json'},
           'inspection':{'evidence_extract':'../original-evidence-extract.json','original_screenshots':'../screenshot-inspection-manifest.json',
                         'supplemental_screenshots':'../supplemental-inspection.json','common_d0_evidence':'../common-original-facts.json',
                         'pixel_recomputation':'../original-pixel-recomputation.json'},
           'schema_descriptor_limitations':[
               'Original expected/unit values are retained exactly in the untouched source artifacts, copied failed-originals transport and judgment fields; no expectation or grade was repaired.',
               'Source-a manual qualitative findings lack a Boolean actual/bound review descriptor in their original review format. Their explicit failed status and precise glyph-clipping reason are semantically supported by their own original PNG; this formatting difference does not erase a supported finding or create an FP.',
               'Engineering failures, missing fields, incomplete measurements and nonfailure/unassessed observations are not product alarms. No schema rejection was used as FP evidence.',
               'Source-a original wrapping claims do not claim overlap. The three common overlap rows remain outside their detection scope despite sharing a defect cause.'],
           'preserved_uncertainties':[
               'Common D0 consensus defines a product-defect universe relative to two AI panels; it is not human gold.',
               'Native capture facts are retained when a submit control is offscreen/unresolved in some P2 snapshots; fully visible captures supply enabled/color evidence. No offscreen null becomes a negative.',
               'The exact native disabled-compositing mechanism and source-a SwiftUI revision-state mechanism are inferred; cluster membership is supported by the shared source path and original causal sequence.',
               'No original claim is extended to a new state or aspect; later FINAL repairs are not used as evidence of original detection. No TN or classical FPR universe is invented.']}
    folder=OUT/source;folder.mkdir(exist_ok=True)
    (folder/'judgment.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    product=set(universe);assigned=[k for g in clusters for k in g['rows']]
    assert len(assigned)==len(set(assigned))and set(assigned)==product
    assert len(claims)+len(excluded)==len(failed)
    assert all(set(c['supported_rows'])<=product for c in claims)
    print(source,'judged',len(claims),'duplicates',len(excluded),'product rows',len(product),'clusters',len(clusters))
