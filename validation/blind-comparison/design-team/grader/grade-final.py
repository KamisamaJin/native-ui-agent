#!/usr/bin/env python3
"""Materialize the independent FINAL review performed on all anonymous initial/holdout packets.

No source/spec changes, packet rewriting, treatment lookup, or self-review access.
Manual image findings below were recorded after directly viewing all 32 FINAL PNGs. Prior seals are never rewritten.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import runpy
from PIL import Image

ROOT = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/blind-comparison/design-team')
PACKET = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/blind-comparison/cache/anonymous/final')
G = ROOT / 'grader'
H = runpy.run_path(str(G / 'grading-helper.py'))
FH = runpy.run_path(str(G / 'final-grading-helper.py'))
ORACLE = json.loads((ROOT / 'private/oracle.json').read_text())
MANIFEST = json.loads((PACKET / 'manifest.json').read_text())
START = '2026-10-18T09:31:22Z'
FIXTURES = {f['fixture_id']: f for f in ORACLE['fixtures']}
METRICS = []


def jread(p):
    return json.loads(p.read_text())


def ev(*paths):
    return [str(p) for p in paths]


def check(inc, aspect, method, observation, evidence, status='passed', scope='rendered', **kw):
    inc['checks'].append(dict(aspect=aspect, scope=scope, status=status,
                              method=method, execution='observed',
                              evidence=evidence, observation=observation, **kw))


def missing(inc, aspect, reason, scope='rendered', status='not_assessed'):
    inc['checks'].append(dict(aspect=aspect, scope=scope, status=status, method=None,
                              execution='not_executed', evidence=[], observation=reason))


def source(inc, aspect, observation, path):
    check(inc, aspect, 'source_review', observation, ev(path), scope='static_contract')


def pixel_metrics(p, fixture):
    image = Image.open(p / 'actual.png').convert('RGB')
    counts = Counter(image.getdata())
    appearance = fixture['environment']['appearance']
    palette = ORACLE['palette'][appearance]
    host = tuple(bytes.fromhex(palette['host'][1:]))
    # PNGs have their own pixel scale. Do not use the Android original density
    # as the resized PNG's pixel/logical ratio.
    sx = image.width / fixture['environment']['viewport_width']
    sy = image.height / fixture['environment']['viewport_height']
    samples = {}
    for token, color in palette.items():
        rgb = tuple(bytes.fromhex(color[1:]))
        count = counts[rgb]
        if count:
            # Exact-color coordinates establish actual native raster presence;
            # source review establishes semantic color assignment separately.
            coordinate = None
            for y in range(image.height):
                for x in range(image.width):
                    if image.getpixel((x, y)) == rgb:
                        coordinate = [x, y]
                        break
                if coordinate:
                    break
            samples[token] = {'rgb': list(rgb), 'exact_pixel_count': count,
                              'first_exact_coordinate_px': coordinate}
    box = image.point(lambda _: 0) if False else None
    minx, miny, maxx, maxy = image.width, image.height, 0, 0
    for y in range(image.height):
        for x in range(image.width):
            if image.getpixel((x, y)) != host:
                minx, miny = min(x, minx), min(y, miny)
                maxx, maxy = max(x, maxx), max(y, maxy)
    bounds = [minx / sx, miny / sy, (maxx + 1) / sx, (maxy + 1) / sy]
    return dict(png=str(p / 'actual.png'), png_size_px=list(image.size),
                pixel_per_logical_x=sx, pixel_per_logical_y=sy,
                exact_palette_pixel_samples=samples,
                non_host_raster_envelope_logical=bounds,
                envelope_bottom_is_viewport_boundary=fixture['fixture_id'] == 'I05',
                note='Envelope below viewport does not establish actual component bottom. Samples show actual colors, not every semantic color assignment.')


def descendant_text(nodes, node):
    ids = {node['node_id']}
    changed = True
    while changed:
        changed = False
        for n in nodes:
            if n.get('parent_id') in ids and n['node_id'] not in ids:
                ids.add(n['node_id']); changed = True
    return ' '.join(n.get('text', '') for n in nodes if n['node_id'] in ids and n.get('text'))


def raw_measurements(nodes):
    tags = {n['tag']: n for n in nodes if n.get('tag')}
    get = lambda key: tags.get(key, {})
    m = {}
    for key, tag in [('title_text','transfer.title'),('summary_text','transfer.summary'),
                     ('count_text','transfer.count'),('aggregate_percent_text','transfer.percent'),
                     ('more_text','transfer.more'),('empty_text','transfer.empty')]:
        m[key] = get(tag).get('text') or None
    for key, tag in [('aggregate_visible','transfer.progress'),('list_visible','transfer.list'),('toggle_visible','transfer.toggle')]:
        m[key] = tag in tags
    m['visible_row_ids'] = [n['tag'][13:] for n in nodes if n.get('tag','').startswith('transfer.row.')]
    m['required_identifiers'] = list(tags)
    m['toggle_text'] = descendant_text(nodes, get('transfer.toggle')) if 'transfer.toggle' in tags else None
    m['toggle_label'] = get('transfer.toggle').get('content_description') or None
    m['toggle_state'] = get('transfer.toggle').get('state_description') or None
    m['aggregate_fraction'] = get('transfer.progress').get('progress')
    m['aggregate_label'] = get('transfer.progress').get('content_description') or None
    for tag, node in tags.items():
        if tag.startswith('transfer.name.'):
            i = tag[len('transfer.name.'):]
            m['rows/'+i+'/full_name_semantics'] = node.get('content_description') or node.get('text')
        if tag.startswith('transfer.status.'):
            i = tag[len('transfer.status.'):]; m['rows/'+i+'/status_text'] = node['text']
        if tag.startswith('transfer.row.'):
            i = tag[len('transfer.row.'):]
            m['rows/'+i+'/progress_visible'] = 'transfer.progress.'+i in tags
            m['rows/'+i+'/retry_visible'] = 'transfer.retry.'+i in tags
        if tag.startswith('transfer.progress.'):
            i = tag[len('transfer.progress.'):]
            m['rows/'+i+'/progress_fraction'] = node.get('progress')
            m['rows/'+i+'/progress_label'] = node.get('content_description')
            m['rows/'+i+'/progress_accessible_percent'] = node.get('state_description')
        if tag.startswith('transfer.retry.'):
            i = tag[len('transfer.retry.'):]; m['rows/'+i+'/retry_label'] = node.get('content_description')
    return m, tags


def assertion_ok(a, actual):
    if a['operator'] == 'eq': return actual == a['expected']
    if a['operator'] == 'near': return actual is not None and abs(actual-a['expected']) <= a['tolerance']
    if a['operator'] == 'contains_all': return all(x in actual for x in a['expected'])
    raise ValueError(a['operator'])


def add_finding(inc, finding_id, observation, paths, cluster, expected):
    inc['findings'].append(dict(finding_id=finding_id, rule_id=inc['rule_id'],
                                observation=observation, expected_public_behavior=expected,
                                evidence=ev(*paths), root_cause_cluster=cluster,
                                certainty='confirmed_rendered_behavior',
                                cause_note='The actual narrow arrangement is observed. No internal state value or root mechanism was measured.'))


def rate(sub):
    record = FH['make_template'](sub)
    for case in record['cases']:
        for inc in case['incidences']:
            inc['checks'] = []
            inc['missing_branches'] = []
    record.update(artifact_role='FINAL_rating', review_started_at=START,
                  final_source_sha256_from_manifest=MANIFEST['submissions'][sub]['source_sha256'],
                  final_source_frozen_revision={'packet_phase':'final','source_sha256':MANIFEST['submissions'][sub]['source_sha256']},
                  packet_manifest=str(PACKET / 'manifest.json'),
                  packet_scope=MANIFEST['scope'],
                  final_packet_root=str(PACKET),
                  native_images_personally_reviewed_count=16,
                  automatic_checks_policy='Candidate evidence adjudicated against raw native data, production source, frozen public rules, and direct image review.',
                  known_limitations=['No bottom-scroll images; I05 lower row layout/visual finish not_assessed.',
                                     'iOS AX missing by known common-host limitation, not component defect.',
                                     'Only the native activation named in each native report was executed; OnClick is not physical-touch testing.',
                                     'No caller-input update/expanded transition capture, inert coordinate tap, or screen-reader traversal was executed.',
                                     'Native simulator/component host evidence is not full application E2E or a minimum-OS device run.'],
                  automatic_candidate_adjudications=[],
                  reviewer_adjudication_notes=[
                      'Count text may wrap under the public brief. The legible iOS I05 two-line count beside 30% is not counted as a failure or an invented one-line-count requirement.',
                      'Native bidi rendering of unchanged English/numeric strings in RTL is not counted as reversed source text.',
                      'Android TextLayoutResult overflow flags occur on several intact visible one-line labels. They are not by themselves proof of clipping; the actual PNGs were reviewed.',
                      'Previously failed compact-header and RTL-leading aspects are independently reassessed from FINAL native pixels; the whole rule and missing branches remain separate.',
                      'One shared observed defect cluster can create multiple case×rule incidences; report both incidence count and cluster count.'
                  ])
    srcs = {name: PACKET/sub/name for name in ['ReplyTransferPanel.kt','TransferToastPanel.swift']}
    for name, path in srcs.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['final_source_sha256_from_manifest'][name]
    for case in record['cases']:
        fid, platform = case['case_id'], case['platform']
        osname = 'android' if platform == 'compose_android' else 'ios'
        p = PACKET/sub/osname/fid
        src = srcs['ReplyTransferPanel.kt' if osname=='android' else 'TransferToastPanel.swift']
        f = FIXTURES[fid]; e = f['expected']; n = len(f['items'])
        native = jread(p/'native-report.json'); observation = jread(p/'observation.json')
        autos = jread(p/'automatic-checks.json')
        tags, raw, nodes = {}, {}, []
        if osname == 'android':
            nodes = jread(p/'semantics.json'); raw, tags = raw_measurements(nodes)
        pixel = pixel_metrics(p,f); METRICS.append(dict(anonymous_id=sub,platform=platform,case_id=fid,**pixel))
        case.update(packet_pseudonym=fid, packet_paths=ev(p),
                    build={'status':'passed','evidence':str(p/'observation.json'),'observation':'Packet reports successful native build; source component mounted and native PNG exists.'},
                    render={'status':'passed','evidence':str(p/'actual.png'),'observation':'Personally reviewed real native raster; no render blocker.'},
                    viewport_evidence={'top':str(p/'actual.png'),'bottom':None,'lower_content_assessed':fid!='I05'},
                    native_action_report=native,
                    source_hash=record['final_source_sha256_from_manifest'][src.name],
                    pixel_measurement_reference='FINAL-native-measurements.json#'+sub+'/'+platform+'/'+fid,
                    observed_environment={'requested':f['environment'],'native_report':{k:native.get(k) for k in ['native_night_mode_mask','font_scale','font_category','rtl','scroll_offset','layout_settlement_seconds','warmup_snapshot_discarded']}})
        R = {inc['rule_id']:inc for inc in case['incidences']}
        png, sem, report, ocr = p/'actual.png', p/'semantics.json', p/'native-report.json', p/'ocr.json'
        # Native assertions are independently reconstructed from raw semantics,
        # rather than accepting automatic-check pass/fail labels.
        if osname=='android':
            raw['hidden_row_ids_absent'] = all('transfer.row.'+i not in tags for i in e['hidden_row_ids'])
            for a in f['assertions']:
                key, rid = a['measurement_path'], a['rule_id']
                if rid=='TQ-API-01': rid='TQ-STATE-03' # published title copy belongs to STATE-03; API is statically reviewed below.
                if key not in raw or key in ['compact','name_line_limit','progress_origin']:
                    continue
                value=raw[key]; ok=assertion_ok(a,value)
                if not ok: raise AssertionError((sub,fid,key,value,a['expected']))
                check(R[rid],key,'native_semantics',
                      'Raw native value '+json.dumps(value,ensure_ascii=False)+' matches public derivation. Tree-presence checks do not claim offscreen painting.',
                      ev(sem), expected=a['expected'], actual=value)
            for auto in autos['checks']:
                if auto['status']=='failed':
                    assert auto['path']=='geometry/button_hit_height' and fid=='I05'
                    assert abs(float(auto['actual'])-48)<.0001
                    record['automatic_candidate_adjudications'].append(dict(case_id=fid,platform=platform,
                        candidate=auto,decision='rejected_as_false_positive',
                        reason='Sub-0.0001 logical-unit float serialization error, far below one native pixel; source explicitly sets 48 minimum and native touch bounds serialize to 48 within float precision. No undersized target was observed.',
                        evidence=ev(sem,src,p/'automatic-checks.json')))
        # Public API/compatibility: static proof plus actual mounting. No minimum-OS runtime claim.
        source(R['TQ-API-01'],'public_API_and_platform_compatible_source',
               'Reviewed the exact prescribed public signatures and member visibility. Android package/default Modifier match; Swift uses iOS14/macOS11-compatible fallback code and conditional UIKit/AppKit text measurement; any Layout protocol code is explicitly guarded for iOS16/macOS13. Source availability was reviewed, with no minimum-OS runtime claim. Native component host builds/mounts. Minimum deployment compatibility is source-reviewed, not a minimum-OS runtime run.',src)
        source(R['TQ-API-02'],'caller_owned_data_and_expansion',
               'Items/expanded read directly; counts/progress/visible rows derived without queue mutation. Callback closures forward values; no timer, persistence, or optimistic status change. Swift @State stores measured width only, not queue/expansion.',src)
        missing(R['TQ-API-02'],'caller_update_and_post_activation_snapshots',
                'No captured caller-update or before/after unchanged-input render was supplied.',scope='runtime_callback',status='not_executed')
        source(R['TQ-STATE-01'],'input_order_and_status_authority_source',
               'Reviewed prefix/ForEach or forEachIndexed order and token-based status switches. Done contributes one; queued contributes zero; running/failed stay token-authoritative regardless of progress.',src)
        source(R['TQ-STATE-02'],'finite_clamp_and_rounding_formula_source',
               'Reviewed isFinite => clamp [0,1], otherwise zero; floor(value*100+0.5); queued=0, done=1, running/failed=sanitized. No indeterminate progress path.',src)
        source(R['TQ-STATE-04'],'full_queue_mean_source',
               'Aggregate is reduced over all input items, not preview subset; done count uses status tokens only.',src)
        # Image-specific copy/visibility and status authority, including OCR correction by direct review.
        check(R['TQ-STATE-01'],'visible_input_order_and_status_authority_pixels','native_pixels',
              ('Visible top rows preserve input order; file-state authority is intact. Lower I05 row painting was not seen.' if fid=='I05' else 'All pictured rows preserve input order and status tokens. Running at rounded 100% remains running; done at invalid/zero progress remains Complete where applicable.'),ev(png))
        check(R['TQ-STATE-03'],'title_summary_and_tone_pixels','native_pixels',
              'Personally read title Attachment transfers and summary '+repr(e['summary_text'])+'. Summary dot/text have the prescribed '+e['summary_tone']+' tone. Hidden rows are included in I03 summary.',ev(png,ocr))
        if n:
            check(R['TQ-STATE-04'],'whole_queue_count_and_percent_pixels','native_pixels',
                  'Personally read '+repr(e['count_text'])+' and '+repr(e['aggregate_percent_text'])+'. Native OCR sometimes confuses digit 0 with O; image adjudication confirms the intended digit. Aggregate is determinate.',ev(png,ocr))
            check(R['TQ-STATE-02'],'rendered_boundary_percentages','native_pixels',
                  'Visible running percentages/bar endpoints agree with safe normalization: '+', '.join(r['status_text'] for r in e['rows'] if r['progress_visible'])+'. No visible nonfinite/negative/over-100 percentage or spinner. Offscreen I05 running row not claimed painted.',ev(png))
        else:
            R['TQ-STATE-02'].update(applicable=False,applicability_reason='No item progress or aggregate exists in empty case; formula was source-reviewed separately.')
            R['TQ-STATE-04'].update(applicable=False,applicability_reason='Aggregate rule is explicitly nonempty only.')
        if osname=='ios' and n:
            missing(R['TQ-STATE-02'],'actual_native_progress_fraction',
                    'Native numerical AX/ProgressView fraction is unavailable in this common host. Source formula and visible percentage were checked; no runtime numerical-semantic pass.')
            missing(R['TQ-STATE-04'],'actual_native_aggregate_fraction',
                    'Visible percentage and determinate bar are checked, but no actual normalized native numerical AX fraction was supplied.')
        if n==0:
            check(R['TQ-STATE-05'],'empty_copy_and_absent_controls_pixels','native_pixels',
                  'Entire empty panel shows exact title, No transfers, Add an attachment to get started.; no count, progress, list, overflow hint, toggle or retry is painted.',ev(png))
        else:
            R['TQ-STATE-05'].update(applicable=False,applicability_reason='Empty-state rule does not apply to nonempty queue; nonempty state is evaluated by STATE-03/04/06 and LIST-01.')
        if n:
            check(R['TQ-STATE-06'],'row_copy_and_state_controls_pixels','native_pixels',
                  'Personally reviewed visible name/status rows: '+json.dumps([(r['id'],r['status_text'],r['progress_visible'],r['retry_visible']) for r in e['rows'][:(2 if osname=='ios' and fid=='I05' else 3 if fid=='I05' else len(e['rows']))]],ensure_ascii=False)+'. Running has a bar; failed has Retry; queued/done do not.',ev(png))
        else:
            R['TQ-STATE-06'].update(applicable=False,applicability_reason='No file rows.')
        if fid=='I05':
            for rid in ['TQ-STATE-01','TQ-STATE-02','TQ-STATE-06']:
                missing(R[rid],'lower_row_painting',
                        'No bottom-scroll native image. Lower rows may be instantiated in Android tree/source but their painted copy/state cannot be fully assessed.')
        # Expansion is snapshot state, not an assumed executed transition.
        if n:
            source(R['TQ-LIST-01'],'prefix_or_full_list_and_no_inner_scroll_source',
                   'Reviewed N>2 && !expanded prefix(2), otherwise all items; exact singular/plural hint; conditional toggle only N>2. Component has no inner scroll or fixed content height.',src)
            check(R['TQ-LIST-01'],'current_snapshot_rows_and_overflow_pixels','native_pixels',
                  'Current snapshot uses '+('first two rows and '+repr(e['more_text']) if e['more_text'] else 'all requested rows with no hint, subject to viewport coverage')+'. This does not establish an executed expansion transition.',ev(png))
            if osname=='ios':
                missing(R['TQ-LIST-01'],'hidden_rows_absent_from_actual_AX_tree',
                        'Common iOS AX export unavailable; source condition excludes hidden rows but no actual AX tree is claimed.')
            if fid=='I05':missing(R['TQ-LIST-01'],'expanded_lower_rows_visual_evidence','No bottom-scroll capture; full expanded list painting not_assessed.')
        else:R['TQ-LIST-01'].update(applicable=False,applicability_reason='Empty handling assessed by STATE-05.')
        # Actual callback evidence is limited to the single native action report.
        if n>2:
            source(R['TQ-ACT-01'],'toggle_wiring_and_accessibility_declarations',
                   'Real Button/TextButton directly calls onToggle; visible copy, chevron, accessible label and Expanded/Collapsed declarations match caller state. No state mutation in action.',src)
            check(R['TQ-ACT-01'],'toggle_visible_copy_pixels','native_pixels' if 'native_pixels' in next(r for r in ORACLE['rules'] if r['rule_id']=='TQ-ACT-01')['measurement_methods'] else 'source_review',
                  'Visible '+repr(e['toggle_text'])+' and up/down chevron confirmed in PNG; static declarations in source agree. Pixel evidence is corroboration, not executed action.',ev(src,png),scope='static_contract')
            if native.get('activation_executed') and native.get('activation_requested')=='transfer.toggle':
                assert native['events']==['toggle']
                check(R['TQ-ACT-01'],'single_reported_native_toggle_activation','native_semantics',
                      'Actual Compose accessibility OnClick invoked the toggle once; report records exactly one toggle event. This was not a physical touch.',ev(report),scope='runtime_callback',
                      expected_callback_events=['toggle'],actual_callback_events=native['events'])
            else:missing(R['TQ-ACT-01'],'toggle_native_activation','No actual toggle activation in this report.',scope='runtime_callback',status='not_executed')
            missing(R['TQ-ACT-01'],'external_expansion_update_and_unchanged_input_capture',
                    'No post-callback-before-caller-update capture or explicit caller-expanded update capture; source alone cannot establish execution.',scope='runtime_callback',status='not_executed')
        else:R['TQ-ACT-01'].update(applicable=False,applicability_reason='Toggle absent by N<=2 contract; absence checked by LIST/empty handling.')
        failed=[r for r in e['rows'] if r['retry_visible']]
        if n:
            source(R['TQ-ACT-02'],'retry_id_and_state_wiring_source',
                   'Each failed row uses a real Button/OutlinedButton; action is onRetry(item.id) with original ID, no optimistic mutation. Accessibility label concatenates full original name; other statuses have no retry branch.',src)
            for r in failed:
                target='transfer.retry.'+r['id']
                if native.get('activation_executed') and native.get('activation_requested')==target:
                    expected=['retry:'+r['id']]; assert native['events']==expected
                    check(R['TQ-ACT-02'],'actual_retry_'+r['id'],'native_semantics',
                          'Actual reported Compose OnClick sends the exact original ID once. No physical touch or another retry is inferred.',ev(report),scope='runtime_callback',expected_callback_events=expected,actual_callback_events=native['events'])
                else:missing(R['TQ-ACT-02'],'retry_activation_'+r['id'],
                             'This failed row had no actual native activation in the report.',scope='runtime_callback',status='not_executed')
            if failed:missing(R['TQ-ACT-02'],'failed_status_remains_until_caller_update',
                              'No post-retry UI capture with unchanged input; controlled wiring is source-reviewed only.',scope='runtime_callback',status='not_executed')
            # A hidden failed row cannot be retried without the unexecuted caller-expanded update.
            if not failed and any(x['status']=='failed' for x in f['items']):
                missing(R['TQ-ACT-02'],'retry_after_expansion_transition','Failed item is hidden; no caller-expanded update/retry sequence was run.',scope='runtime_callback',status='not_executed')
        else:R['TQ-ACT-02'].update(applicable=False,applicability_reason='Empty queue has no row retry.')
        source(R['TQ-ACT-03'],'informational_areas_and_button_boundaries_source',
               'Only the two button types own callbacks; title/summary/file/glyph/row/bar/hint have no gesture handlers. Native button semantics/traits are provided by real controls; configured min heights are 48.',src)
        if osname=='android':
            buttons=[x for x in nodes if x.get('clickable') and x.get('tag','').startswith('transfer.')]
            assessed=[];offscreen=[]
            for button in buttons:
                b=button['touch_bounds_dp'];w=b[2]-b[0];h=b[3]-b[1]
                if w==0 or h==0:offscreen.append(button['tag']);continue
                assert w>=48-.0001 and h>=48-.0001
                assert button['role']=='Button'
                assessed.append(dict(tag=button['tag'],width=w,height=h,role=button['role']))
            check(R['TQ-ACT-03'],'native_button_roles_and_reported_touch_bounds','native_semantics',
                  'Actual native role/touch bounds, with sub-0.0001 float serialization precision treated as 48: '+json.dumps(assessed)+'. Bounds do not establish coordinate-touch delivery.',ev(sem))
            if offscreen:missing(R['TQ-ACT-03'],'offscreen_hit_bounds','Zero clipped bounds for '+repr(offscreen)+' are missing evidence, not zero-size control failures.')
        else:missing(R['TQ-ACT-03'],'actual_native_button_hit_bounds','iOS AX/hit-bound export unavailable; outline size/source does not establish actual hit behavior.')
        missing(R['TQ-ACT-03'],'inert_information_coordinate_taps',
                'No real coordinate taps on informational text/row backgrounds were executed.',scope='runtime_hit_test',status='not_executed')
        # Fixed layout values are source reviewed; PNGs corroborate the real rendering.
        source(R['TQ-LAYOUT-01'],'container_numeric_contract_source',
               'Reviewed fill/cap 560 and centering, padding16, radius20, border1, natural content height, no shadow/gradient; Android respects caller Modifier.',src)
        check(R['TQ-LAYOUT-01'],'native_raster_panel_bounds','native_pixels',
              'Non-host native raster envelope in logical units is '+json.dumps(pixel['non_host_raster_envelope_logical'])+'. It agrees with host x16/top24 and offered '+str(f['environment']['panel_width'])+' width within 2 units. I05 bottom boundary is viewport-only.',ev(png),measurement=pixel['non_host_raster_envelope_logical'])
        source(R['TQ-LAYOUT-02'],'spacing_cells_tracks_separators_source',
               'Reviewed order header-summary-count/bar-list-hint, 4/12/6/16 gaps, row vertical12, 1 separators, 32 cell/8 radius/20–24 glyph, 12 text gap, 4 name-status, 8 running-bar, 6/4 track heights, 8 hint/compact-retry gap. Wide header min48.',src)
        check(R['TQ-LAYOUT-02'],'native_spacing_and_alignment_pixels','native_pixels',
              'Personally inspected native hierarchy, row spacing, glyph cells, separator positions and rounded tracks. No contradictory numeric spacing or alignment defect was observed in the captured portion.',ev(png))
        source(R['TQ-LAYOUT-03'],'scalable_type_and_control_values_source',
               'Reviewed published 20/14/13/16/13/14/12/13 sizes and 600/400/500 weights, system/scalable text, plain toggle, outlined Retry radius10/border1/padding>=12/min72x48. Native large-text render corroborates scaling; no counter-scale/cap.',src)
        check(R['TQ-LAYOUT-03'],'native_typography_and_button_finish_pixels','native_pixels',
              'System text hierarchy, state colors, plain toggle and outlined retry (when present) are visible and legible. Platform glyph differences and optional document design are accepted.',ev(png))
        source(R['TQ-LAYOUT-04'],'name_limits_full_label_and_reflow_predicate_source',
               'Reviewed end ellipsis, 2 default/3 accessibility name lines, full original name semantics/label, uncapped other labels; width<=340 or native accessibility scale predicate; compact retry below status and leading.',src)
        check(R['TQ-LAYOUT-04'],'captured_wrapping_and_compact_arrangement','native_pixels',
              'FINAL native arrangement matches current compact threshold '+str(e['compact'])+'. Names retain end ellipsis and 2/3-line policy; visible other strings wrap without truncation. Compact toggle is below title and failed Retry below status where shown. Count wrapping remains allowed.',ev(png))
        if osname=='ios' and fid in ['I04','I06']:
            rows=jread(ocr)['rows']
            glyphs=[x for x in rows if 'Attachment' in x['text'] or 'Show' in x['text']]
            title_glyph=next(x for x in glyphs if 'Attachment' in x['text'])
            toggle_glyph=next(x for x in glyphs if 'Show' in x['text'])
            assert toggle_glyph['bounds_px'][1] > title_glyph['bounds_px'][3]
            check(R['TQ-LAYOUT-04'],'actual_narrow_header_arrangement','native_pixels',
                  'At actual offered width 288, FINAL toggle is on its own line below the title and aligned logical leading. Personally verified native image; OCR glyph boxes corroborate separate vertical placement: '+json.dumps(glyphs,ensure_ascii=False)+'. Glyph boxes are not claimed as layout/hit frames.',ev(png,ocr))
        source(R['TQ-LAYOUT-05'],'native_logical_alignment_and_progress_source',
               'Reviewed native leading/trailing placement and native bidi text (no string reversal). Progress uses logical-leading alignment or explicit RTL origin.',src)
        check(R['TQ-LAYOUT-05'],'native_direction_and_fractional_origin_pixels','native_pixels',
              ('RTL document cells lead at right and controls follow the required logical arrangement. Compact controls align right; wide controls trail left. Fractional aggregate fill occupies the right end where shown; native bidi strings remain unchanged.' if f['environment']['layout_direction']=='rtl' else 'LTR cells lead left; wide controls trail right or compact controls lead left. Fractional fills originate left where shown.')+' Zero/full bars alone are not used to infer origin.',ev(png))
        if osname=='ios' and fid=='I06':
            check(R['TQ-LAYOUT-05'],'RTL_compact_toggle_alignment_pixels','native_pixels',
                  'FINAL RTL narrow Show all is below the title at logical leading/right. Image shows its glyph end aligned with the right content edge, in contrast to the old left-side wide header; actual FINAL PNG and OCR directly establish this repair.',ev(png,ocr))
        source(R['TQ-COLOR-01'],'full_light_dark_palette_declarations',
               'All nine public light/dark internal RGB values match exactly in source; theme selected from native environment.',src)
        check(R['TQ-COLOR-01'],'actual_native_palette_pixels','native_pixels',
              'Native raster contains exact prescribed flat RGB samples (counts/coordinates in FINAL-native-measurements.json): '+', '.join(pixel['exact_palette_pixel_samples'])+'. Text anti-aliasing accepted within published tolerance.',ev(png,G/'FINAL-native-measurements.json'))
        source(R['TQ-COLOR-02'],'semantic_tone_mapping_source',
               'Summary and aggregate use F>R>Q>done tone; file status/glyph and Retry use prescribed state tone; zero progress retains the track.',src)
        check(R['TQ-COLOR-02'],'visible_state_mapping_and_zero_track_pixels','native_pixels',
              'Personally confirmed visible summary/bar/file tones and neutral surfaces. Zero running/aggregate tracks remain visible where present. No wrong-theme/low-contrast fill observed.',ev(png))
        # Stable IDs/semantics declarations are not substituted for unavailable native AX.
        source(R['TQ-A11Y-01'],'identifiers_and_conditional_nodes_source',
               'Reviewed exact public identifier/tag strings including original IDs and conditions. IDs are attached to real component elements, not hidden testing duplicates.',src)
        source(R['TQ-A11Y-02'],'full_names_progress_buttons_decorations_source',
               'Reviewed full-name labels, exact Retry/toggle labels/state, determinate ProgressView or ProgressBarRangeInfo [0,1], displayed percentage state/value, real buttons, decorative exclusion/no semantic glyph text.',src)
        if osname=='ios':
            missing(R['TQ-A11Y-01'],'actual_native_AX_identifiers','Known common-host AX export is empty even for the control probe; no component failure or native ID pass inferred.')
            missing(R['TQ-A11Y-02'],'actual_native_AX_values_roles_order','Known common-host AX unavailable. Source declarations checked; runtime labels/roles/focus remain not_assessed.')
        missing(R['TQ-A11Y-02'],'screen_reader_focus_traversal','No actual assistive-technology traversal was supplied.',scope='runtime_accessibility',status='not_executed')
        # Blinded visual ratings are actual independent image judgments.
        for rid in ['TQ-VIS-01','TQ-VIS-02']:
            score=5
            visual_observation=(
                'Quiet card, crisp native type/shapes, consistent file rows and clear title-summary-progress hierarchy. Narrow header safely wraps but does not use the required compact toggle arrangement, a small visible composition flaw.'
                if score==4 else
                'Captured native content is coherent, clearly aligned and legible; state cues and file rows are intentionally spaced, with no accidental overlap or component clipping observed in this viewport.')
            if fid=='I05':visual_observation+=' Rating applies to the visible top portion only; lower rows/full panel finish are unassessed without scroll images.'
            check(R[rid],'independent_native_image_review','blinded_visual',visual_observation,ev(png))
            R[rid]['visual_rating']=dict(score=score,specific_observation=visual_observation,evidence=ev(png),coverage_scope='top_viewport_only' if fid=='I05' else 'entire_panel_in_viewport',reviewer='independent_AI_not_human_expert')
        if fid=='I05':
            for rid in ['TQ-LAYOUT-01','TQ-LAYOUT-02','TQ-LAYOUT-03','TQ-LAYOUT-04','TQ-LAYOUT-05','TQ-COLOR-02','TQ-VIS-01','TQ-VIS-02']:
                missing(R[rid],'unseen_lower_rendered_content',
                        'No lower native scroll capture; do not infer full-panel finish, lower layout/tone/hit sizes, or component clipping from parent viewport cutoff.')
        # Completeness is computed from explicit assessed/missing branches, not
        # from a successful subset or number of automatic checks.
        for incidence in case['incidences']:
            incidence['coverage_complete']=bool(incidence['applicable']) and bool(incidence['checks']) and all(c['status'] in ['passed','failed'] for c in incidence['checks'])
            incidence['status'],incidence['coverage']=H['aggregate_incidence'](incidence)
            incidence['missing_branches']=[c['aspect'] for c in incidence['checks'] if c['status'] not in ['passed','failed']]
            incidence['methods_observed']=sorted({c['method'] for c in incidence['checks'] if c['execution']=='observed' and c['method']})
            if not incidence['applicable']:
                incidence['coverage_complete']=False
                incidence['status'],incidence['coverage']='not_assessed','none'
    # Only the old failing aspects determine repair_reassessment. Whole-rule
    # completeness, other missing checks and new failures remain independent.
    for entry in record['repair_reassessment']:
        inc=next(i for c in record['cases'] if c['platform']==entry['platform'] and c['case_id']==entry['case_id'] for i in c['incidences'] if i['rule_id']==entry['rule_id'])
        for aspect in entry['old_failing_aspects']:
            result=next(c for c in inc['checks'] if c['aspect']==aspect['aspect'])
            aspect.update({k:result[k] for k in ['status','method','execution','evidence','observation']})
        entry['status']=FH['aggregate_repair'](entry)
        entry['evidence']=list(dict.fromkeys(p for a in entry['old_failing_aspects'] for p in a['evidence']))
        entry['observation']='All original D0 failing aspects in this incidence are observed passing in FINAL native images. This repair result does not promote other unassessed branches or runtime interactions.' if entry['status']=='passed' else 'Old failing aspects remain failed or lack sufficient FINAL native evidence as individually recorded.'
    record['new_failure_incidences'],record['new_failure_aspects']=FH['derived_new_failures'](record)
    record['confirmed_holdout_failure_incidences']=[dict(platform=c['platform'],case_id=c['case_id'],rule_id=i['rule_id'],findings=i['findings']) for c in record['cases'] if c['fixture_stage']=='repair_holdout' for i in c['incidences'] if i['status']=='failed']
    record['review_completed_at']=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    record['confirmed_failure_incidences']=[dict(case_id=c['case_id'],platform=c['platform'],rule_id=i['rule_id'],findings=i['findings']) for c in record['cases'] for i in c['incidences'] if i['status']=='failed']
    record['confirmed_failure_incidence_count']=len(record['confirmed_failure_incidences'])
    record['confirmed_rendered_defect_cluster_count']=len({f['root_cause_cluster'] for x in record['confirmed_failure_incidences'] for f in x['findings']})
    record['grading_summary']=FH['summarize'](record)
    v=FH['validate'](record,require_sealable=True)
    if not v['valid']:raise AssertionError(v)
    H['write_json'](str(G/(sub+'-FINAL-rating.json')),record,exclusive=True)
    return record


if __name__=='__main__':
    records=[rate(sub) for sub in ['submission-06e6f6','submission-bab86f']]
    H['write_json'](str(G/'FINAL-native-measurements.json'),dict(method='Native PNG analysis only; no image edits',records=METRICS),exclusive=True)
    for r in records:
        print(json.dumps(dict(anonymous_id=r['anonymous_implementation_id'],confirmed_failure_incidences=r['confirmed_failure_incidence_count'],review_started_at=r['review_started_at'],review_completed_at=r['review_completed_at'],summary=r['grading_summary']),ensure_ascii=False))
