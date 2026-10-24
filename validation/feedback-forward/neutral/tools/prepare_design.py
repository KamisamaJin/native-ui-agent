"""Author the independent neutral design and test inputs before Bridge.swift exists."""
from pathlib import Path
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parents[1]

def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def typed(value, unit='string'):
    return {'value': value, 'unit': unit}

states = [
    {'id': 'ready', 'input_index': 0, 'after_action': 0, 'coverage': 'full_content'},
    {'id': 'reviewed', 'input_index': 0, 'after_action': 1, 'coverage': 'targets'},
    {'id': 'replaced', 'input_index': 1, 'after_action': 3, 'stimulus_action': 2, 'coverage': 'full_content'},
    {'id': 'disabled', 'input_index': 1, 'after_action': 4, 'coverage': 'targets'},
]
state_ids = [s['id'] for s in states]
sections = [
    ('Opening note', 'Start with a single purpose. Keep the opening note specific enough to recognize later.'),
    ('Scope note', 'Name the edges of the work. A short boundary makes the rest of the notes easier to read.'),
    ('Order note', 'Put the next useful idea after the current one. Readers should be able to follow the sequence.'),
    ('Detail note', 'Keep one concrete detail close to each main point. Separate details that serve different purposes.'),
    ('Pause note', 'Leave a clear pause between groups. A little space helps the reader find the next section.'),
    ('Review note', 'Read the notes once from top to bottom. Mark the review only after considering the whole sequence.'),
    ('Continuity note', 'Keep the current review count when the caller supplies a new revision of these notes.'),
    ('Context note', 'A replacement can change the title and summary while leaving the same component mounted.'),
    ('Reach note', 'The final sections should remain reachable. Long content must keep its ordinary reading order.'),
    ('Closing note', 'Finish with a clear end note. The revision and review count should agree with the current state.'),
]
initial = {
    'title': 'Observation notes',
    'summary': 'Ten short notes form one continuous reading sequence. Review them once, then compare the replacement revision.',
    'revision': 'A', 'can_review': True,
    'sections': [{'number': i + 1, 'title': a, 'body': b} for i, (a, b) in enumerate(sections)],
}
replacement = dict(initial,
    title='Revised observation notes',
    summary='The caller supplied revision B. The notes remain in the same component, and the completed review stays visible.',
    revision='B', can_review=False)

reference = {
    'provenance': {
        'owner': 'Independent neutral forward-test author',
        'input': 'Parent task dated 2026-10-24: domain-neutral SwiftUI long content; real action, caller replacement, disabled action; four states; ordinary/narrow large-text fixtures.',
        'interpretation': 'A reading-notes panel with ten neutral cards and one review action. This design was fixed before source implementation and before any native image or execution.',
        'independence_limit': 'Separate from the Skill implementation/optimizer and earlier validation results. Design and component are authored sequentially in this tester context; hashes cannot prove semantic correctness.',
    },
    'labels': {
        'titleA': typed(initial['title']), 'titleB': typed(replacement['title']),
        'summaryA': typed(initial['summary']), 'summaryB': typed(replacement['summary']),
        'revisionA': typed('Input revision: A'), 'revisionB': typed('Input revision: B'),
        'status0': typed('Review count: 0'), 'status1': typed('Review count: 1'),
        'actionReady': typed('Mark notes reviewed'), 'actionDone': typed('Review marked'),
        'footerA0': typed('End note: revision A; review count 0'),
        'footerA1': typed('End note: revision A; review count 1'),
        'footerB1': typed('End note: revision B; review count 1'),
        'opening': typed('01 · Opening note'),
        'middle': typed('05 · Pause note'),
        'closing': typed('10 · Closing note'),
        'buttonRole': typed('button'),
    },
    'behavior': {'yes': typed(True, 'bool'), 'no': typed(False, 'bool'),
                 'reviewed': typed(['notes.reviewed.A'], 'events'), 'quiet': typed([], 'events')},
    'geometry': {'minimumActionHeight': typed(52, 'pt'), 'minimumActionHeightAndroid': typed(52, 'dp')},
    'visual': {
        'fullLayout': typed('One vertical reading sequence: heading, summary, revision, review count, cards 01–06, review action, cards 07–10, and end note. Cards have distinct neutral surfaces and vertical gaps. No horizontal clipping, overlap, missing cards, or accidental reordering. Required full-content evidence must reach the real bottom with overlap.'),
        'wrapping': typed('At the approved offered width and Dynamic Type, all headings, summaries, card text, review labels, and end note remain readable and wrap naturally without truncation or ellipses. Narrow text may increase the content height.'),
        'enabledAction': typed('The review action uses a dark blue-gray fill #263746 with white readable text, rounded corners, and at least a 52 pt accessibility control height.'),
        'disabledAction': typed('The disabled review action uses a pale gray fill #DCE2E7 with dark gray readable text #55616C, rounded corners, and at least a 52 pt accessibility control height.'),
        'surface': typed('The canvas is white #FFFFFF. Cards use #F4F6F8. Main text is #17212B and secondary text is #43515E. These are rendered visual expectations; public SwiftUI AX cannot establish computed color or font attributes.'),
    },
    'design': {
        'offeredWidths': [400, 280], 'hostHorizontalPaddingPt': 16, 'childWidthsPt': [368, 248],
        'ordinaryDynamicType': 'large', 'narrowDynamicType': 'xxxLarge',
        'layout': 'VStack spacing 18 pt; each card content padding 16 pt, minimum outer height 180 pt; card radius 12 pt; review action minimum height 52 pt. Typography uses scalable title2, body, headline and subheadline styles. No fixed text heights.',
        'heightIntent': 'Approximately four to five 600 pt viewports at the ordinary fixture. Narrow large text may grow; actual native content height is recorded rather than forced to an expected height.',
    },
    'obligations': [
        {'id': 'current-input', 'clause': 'Visible title, summary and revision match the current caller input in every required state.', 'priority': 'must', 'states': state_ids, 'risk': 'content'},
        {'id': 'review-state', 'clause': 'The review starts at zero, becomes one after activation, and remains one across caller replacement and disabled observation.', 'priority': 'must', 'states': state_ids, 'risk': 'behavior'},
        {'id': 'real-review', 'clause': 'The enabled review action is uniquely dispatched through XCUI tap and emits exactly notes.reviewed.A once.', 'priority': 'must', 'states': ['reviewed'], 'risk': 'behavior'},
        {'id': 'quiet-replacement', 'clause': 'Caller replacement advances exactly one input in the same mounted instance without a business callback.', 'priority': 'must', 'states': ['replaced'], 'risk': 'behavior'},
        {'id': 'availability', 'clause': 'The review action is enabled for revision A and disabled for revision B; disabled observation is not dispatched or scored as callback success.', 'priority': 'must', 'states': state_ids, 'risk': 'behavior'},
        {'id': 'long-content', 'clause': 'All ten cards and the footer remain reachable in the required full-content states, and the remote anchors remain observed for every target checkpoint.', 'priority': 'must', 'states': state_ids, 'risk': 'layout'},
        {'id': 'readable-layout', 'clause': 'Both fixture configurations have readable wrapping, no horizontal clipping or overlap, and the approved vertical order.', 'priority': 'must', 'states': ['ready', 'replaced'], 'risk': 'layout'},
        {'id': 'appearance', 'clause': 'The neutral surfaces and action appearance follow the approved colors and minimum native control height.', 'priority': 'must', 'states': state_ids, 'risk': 'style'},
    ],
}

rules = [
    {'id': 'title', 'kind': 'control', 'target': 'title', 'property': 'label'},
    {'id': 'summary', 'kind': 'control', 'target': 'summary', 'property': 'label'},
    {'id': 'revision', 'kind': 'control', 'target': 'revision', 'property': 'label'},
    {'id': 'review-count', 'kind': 'control', 'target': 'status', 'property': 'label'},
    {'id': 'action-label', 'kind': 'control', 'target': 'action', 'property': 'label'},
    {'id': 'action-enabled', 'kind': 'control', 'target': 'action', 'property': 'enabled'},
    {'id': 'action-unique', 'kind': 'control', 'target': 'action', 'property': 'unique'},
    {'id': 'action-role', 'kind': 'control', 'target': 'action', 'property': 'control_role'},
    {'id': 'action-height', 'kind': 'geometry', 'target': 'action', 'property': 'height', 'basis': 'control', 'measurement': 'accessibility_box', 'op': 'gte'},
    {'id': 'opening-anchor', 'kind': 'control', 'target': 'opening', 'property': 'label'},
    {'id': 'middle-anchor', 'kind': 'control', 'target': 'middle', 'property': 'label'},
    {'id': 'closing-anchor', 'kind': 'control', 'target': 'closing', 'property': 'label'},
    {'id': 'footer', 'kind': 'control', 'target': 'footer', 'property': 'label'},
    {'id': 'activation-receipt', 'kind': 'event', 'required_method': 'xcui_tap'},
    {'id': 'replacement-receipt', 'kind': 'event', 'stimulus': 'caller_update', 'required_method': 'caller_fixture_update'},
    {'id': 'full-layout', 'kind': 'manual', 'target': 'title', 'coverage': 'full_content', 'allowed_methods': ['visual']},
    {'id': 'text-wrapping', 'kind': 'manual', 'target': 'summary', 'coverage': 'full_content', 'allowed_methods': ['visual']},
    {'id': 'neutral-surfaces', 'kind': 'manual', 'target': 'middle', 'coverage': 'target', 'allowed_methods': ['visual']},
    {'id': 'action-appearance', 'kind': 'manual', 'target': 'action', 'coverage': 'target', 'allowed_methods': ['visual']},
]

def cell(path, android=None):
    return {platform: {'source': 'reference', 'pointer': android if platform == 'android' and android else path} for platform in ['ios', 'android']}

paths = {
    'title': ['titleA', 'titleA', 'titleB', 'titleB'],
    'summary': ['summaryA', 'summaryA', 'summaryB', 'summaryB'],
    'revision': ['revisionA', 'revisionA', 'revisionB', 'revisionB'],
    'review-count': ['status0', 'status1', 'status1', 'status1'],
    'action-label': ['actionReady', 'actionDone', 'actionDone', 'actionDone'],
    'action-role': ['buttonRole'] * 4,
    'opening-anchor': ['opening'] * 4, 'middle-anchor': ['middle'] * 4,
    'closing-anchor': ['closing'] * 4,
    'footer': ['footerA0', 'footerA1', 'footerB1', 'footerB1'],
}
values = {rid: {sid: cell('/labels/' + anchor) for sid, anchor in zip(state_ids, anchors)} for rid, anchors in paths.items()}
values['action-enabled'] = {sid: cell('/behavior/' + ('yes' if i < 2 else 'no')) for i, sid in enumerate(state_ids)}
values['action-unique'] = {sid: cell('/behavior/yes') for sid in state_ids}
values['action-height'] = {sid: cell('/geometry/minimumActionHeight', '/geometry/minimumActionHeightAndroid') for sid in state_ids}
for rid, only, pointer, reason in [
    ('activation-receipt', 'reviewed', '/behavior/reviewed', 'No successful activation is requested at this checkpoint. In particular a blocked disabled control cannot establish callback behavior.'),
    ('replacement-receipt', 'replaced', '/behavior/quiet', 'This checkpoint does not follow the independently requested caller replacement stimulus.'),
]:
    values[rid] = {sid: cell(pointer) if sid == only else {'not_applicable': reason} for sid in state_ids}
for rid, pointer in [('full-layout', '/visual/fullLayout'), ('text-wrapping', '/visual/wrapping')]:
    values[rid] = {sid: cell(pointer) if sid in ['ready', 'replaced'] else {'not_applicable': 'This checkpoint deliberately requires named targets, not a whole-content visual acceptance claim.'} for sid in state_ids}
values['neutral-surfaces'] = {sid: cell('/visual/surface') for sid in state_ids}
values['action-appearance'] = {sid: cell('/visual/' + ('enabledAction' if i < 2 else 'disabledAction')) for i, sid in enumerate(state_ids)}
actions = [
    {'type': 'sweep', 'state_id': 'ready', 'max_steps': 28},
    {'type': 'tap', 'target': 'action', 'reveal': True, 'expect_callback': 'notes.reviewed.A', 'state_id': 'reviewed', 'observation_max_scrolls': 36},
    {'type': 'apply_next_fixture'},
    {'type': 'sweep', 'state_id': 'replaced', 'max_steps': 28},
    {'type': 'tap', 'target': 'action', 'reveal': True, 'allow_disabled': True, 'state_id': 'disabled', 'observation_max_scrolls': 36},
]
bindings = {name: {'identifier': 'notes.' + name} for name in ['title', 'summary', 'revision', 'status', 'action', 'opening', 'middle', 'closing', 'footer']}
bound_actions = json.loads(json.dumps(actions))
for action in bound_actions:
    if isinstance(action.get('target'), str): action['target'] = bindings[action['target']]
scenarios = {name: {'states': states, 'actions': actions, 'values': values} for name in ['ordinary400', 'narrow280-large']}
contract = {'version': 1, 'design_owner': reference['provenance']['owner'],
            'approval_reference': 'neutral/design/PREIMPLEMENTATION.json and neutral/APPROVAL.json; frozen before native launch',
            'sources': [], 'required_rule_ids': [r['id'] for r in rules], 'rules': rules, 'scenarios': scenarios}
routes = {'version': 1, 'index': {'source': 'reference', 'pointer': '/obligations'}, 'routes': {
    'current-input': {'rule_ids': ['title', 'summary', 'revision'], 'reason': 'Exact current native semantic labels.', 'regression_obligations': ['readable-layout']},
    'review-state': {'rule_ids': ['review-count', 'action-label', 'footer'], 'reason': 'Top, action and remote footer expose the same retained count.', 'regression_obligations': ['real-review', 'quiet-replacement']},
    'real-review': {'rule_ids': ['activation-receipt'], 'reason': 'Exact ordered event delta gated on a unique successful XCUI dispatch.', 'regression_obligations': ['review-state', 'availability', 'appearance']},
    'quiet-replacement': {'rule_ids': ['replacement-receipt'], 'reason': 'Exact empty event delta gated on successful same-instance caller replacement.', 'regression_obligations': ['current-input', 'review-state', 'availability']},
    'availability': {'rule_ids': ['action-enabled', 'action-unique', 'action-role'], 'reason': 'Actual unique native control state; disabled dispatch facts will be logged separately and cannot pass callback checks.', 'regression_obligations': ['appearance']},
    'long-content': {'rule_ids': ['opening-anchor', 'middle-anchor', 'closing-anchor', 'footer'], 'reason': 'Full states additionally demand complete overlapping coverage; target states preserve exact remote locations.', 'regression_obligations': ['readable-layout']},
    'readable-layout': {'rule_ids': ['full-layout', 'text-wrapping'], 'reason': 'Independent visual review of complete state image sequences.', 'regression_obligations': ['appearance']},
    'appearance': {'rule_ids': ['action-height', 'neutral-surfaces', 'action-appearance'], 'reason': 'Native accessibility control height plus separately scoped visual color/surface review.', 'regression_obligations': ['readable-layout']},
}}
write('design/reference.json', reference)
write('design/contract.json', contract)
write('design/routes.json', routes)
write('inputs/bindings.json', bindings)
write('inputs/actions.json', bound_actions)
for name, width, dynamic_type in [('ordinary400', 400, 'large'), ('narrow280-large', 280, 'xxxLarge')]:
    fixture = {'initial': initial, 'updates': [replacement], 'width': width, 'theme': 'light', 'dynamic_type': dynamic_type,
               'direction': 'ltr', 'canvas_color': '#FFFFFF',
               'required_identifiers': ['notes.' + n for n in ['title', 'summary', 'revision', 'status', 'opening', 'middle', 'action', 'closing', 'footer']],
               'max_scrolls': 28, 'trace_reveal_images': True}
    write('inputs/' + name + '.json', fixture)
paths = ['design/reference.json', 'design/contract.json', 'design/routes.json', 'inputs/bindings.json', 'inputs/actions.json', 'inputs/ordinary400.json', 'inputs/narrow280-large.json']
write('design/PREIMPLEMENTATION.json', {'version': 1, 'created_unix': time.time(), 'source_exists': (ROOT / 'source/Bridge.swift').exists(),
      'decision': 'Design and test inputs fixed before component source or native captures. Final contract only adds exact reference/launch source records.',
      'sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}})
print(json.dumps({'status': 'design_fixed_before_source', 'files': paths}, indent=2))
