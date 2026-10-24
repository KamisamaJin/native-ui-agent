"""Write the independent review, without changing any sealed proposal."""
import datetime
import hashlib
import json
import pathlib
import time

ROOT = pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
OUT = pathlib.Path(__file__).resolve().parent
D = 'validation/feedback-forward/design/T1/'
F = 'validation/feedback-forward/candidate-v9/'

def load(name):
    return json.loads((OUT / name).read_text())

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

sources = load('source-files.json')
for name, sha in sources.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name

def ref(name, pointer=None, line=None):
    value = {'path': name, 'sha256': sources[name]}
    if pointer is not None:
        value['pointer'] = pointer
    if line is not None:
        value['line'] = line
    return value

issues = [
    {
        'id': 'T1-R1', 'severity': 'high',
        'title': 'The acknowledgement false transition has no obligation or executable route',
        'rationale': 'BRIEF clause 2 requires a second pre-release selection to clear acknowledgement and emit false exactly once. Every public and private route taps choice only once, at action 2. All approved choice-receipt expectations contain only true. The generic choice-selected and choice-receipt obligations therefore omit this branch; successful matrix reconstruction does not verify it.',
        'affected_platforms': ['ios', 'android'],
        'source_refs': [ref(D+'public/BRIEF.md', line=6), ref(D+'public/reference.json', '/obligations'), ref(D+'public/contract.json', '/scenarios'), ref(D+'private/contract.json', '/scenarios/H1/actions')],
        'required_revision': 'Independently specify and route the pre-release clear transition, including its selected/label/status/enabled results and a successful native stimulus with the exact false callback interval. Preserve the current seal as a prior revision.'
    },
    {
        'id': 'T1-R2', 'severity': 'high',
        'title': 'Acknowledge-under-hold is never exercised',
        'rationale': 'The routes acknowledge only initial models with both guards true. Seal and coolant holds appear only after the final identity replacement, where acknowledgement has reset to false and no further activation occurs. Thus the clause that acknowledgement cannot override either hold, and the full primary-enabled predicate, lack a verification route for the acknowledged held condition. H1 does correctly cover both guards false for status precedence, but still with acknowledgement false.',
        'affected_platforms': ['ios', 'android'],
        'source_refs': [ref(D+'public/BRIEF.md', line=5), ref(D+'public/BRIEF.md', line=6), ref(D+'public/BRIEF.md', line=11), ref(D+'public/cases/P1/fixtures.json'), ref(D+'public/cases/P2/fixtures.json'), ref(D+'private/cases/H1/fixtures.json'), ref(D+'public/contract.json', '/scenarios')],
        'required_revision': 'Add independently approved same-API states/actions which acknowledge each held condition and assess the resulting hold status and disabled primary. Do not count a disabled primary attempt as successful dispatch.'
    },
    {
        'id': 'T1-R3', 'severity': 'high',
        'title': 'Disclosure requirements are only partly represented',
        'rationale': 'There is one disclosure activation at action 1 and no close activation in any scenario. There is no event rule bound to that action, so disclosure zero-callback behavior is not checked: later choice and request assertions use their own later intervals. The collapsed-content proposition hides only body paragraphs, omitting headings even though the BRIEF toggles heading/body pairs. Disclosure enabled after request is specified by API.md but has neither an enabled assertion nor a post-request activation.',
        'affected_platforms': ['ios', 'android'],
        'source_refs': [ref(D+'public/BRIEF.md', line=8), ref(D+'public/API.md', line=57), ref(D+'public/reference.json', '/questions/collapsed-content'), ref(D+'public/reference.json', '/obligations'), ref(D+'public/contract.json', '/rules'), ref(D+'public/contract.json', '/scenarios'), ref(D+'private/contract.json', '/scenarios')],
        'required_revision': 'Represent and route native open/close behavior, complete collapsed pair absence, disclosure quietness bound to its actual successful activation interval, and its required enabled behavior after request.'
    },
    {
        'id': 'T1-R4', 'severity': 'high',
        'title': 'All-text wrapping is narrower in the atomic questions than in the BRIEF',
        'rationale': 'The BRIEF requires all text to wrap without line limits. The only wrapping propositions cover the title and expanded body paragraphs. Section headings, subtitle, status and control text have exact semantic-label checks and horizontal clipping checks, but these do not establish untruncated natural wrapping or reject an ellipsis inside the bounds. This matters in the approved narrow/large profile. A source-backed obligation must cover these required text classes without inventing computed SwiftUI font or line facts.',
        'affected_platforms': ['ios', 'android'],
        'source_refs': [ref(D+'public/BRIEF.md', line=15), ref(D+'public/reference.json', '/questions/title-wrapping'), ref(D+'public/reference.json', '/questions/body-wrapping'), ref(D+'public/reference.json', '/questions/horizontal-clipping'), ref(D+'public/policy.json', '/atoms')],
        'required_revision': 'Independently add the missing wrapping scope and feasible atomic visual routes, retaining distinct clipping and overlap propositions.'
    },
    {
        'id': 'T1-R5', 'severity': 'medium',
        'title': 'Mandatory layout and scrolling ownership clauses have no corresponding route',
        'rationale': 'The obligation index and questions do not check full-width component canvas ownership, the minimum 16-native-unit status text inset, absence of fixed-height blank spacer rows, or the prohibition on a component nested scroller. The five pixel atoms prove only their approved solid sample strips. In particular the status sample spans 1.2–3.5% of the semantic band and cannot establish a 16-unit text inset. Full parent sweep coverage proves reachability, not which object owns scrolling or why content is tall. Internal nominal spacing tokens and status minimum height are correctly advisory; this finding does not turn them into measured MUSTs.',
        'affected_platforms': ['ios', 'android'],
        'source_refs': [ref(D+'public/BRIEF.md', line=15), ref(D+'public/reference.json', '/obligations'), ref(D+'public/reference.json', '/questions'), ref(D+'public/policy.json', '/atoms/0/sampling'), ref(D+'public/routes.json')],
        'required_revision': 'Give each mandatory structural/layout clause an independently approved feasible evidence route and ownership. If the current collector cannot support a mandatory exact quantity, report that limitation in the revised design review rather than substituting fabricated computed facts.'
    },
    {
        'id': 'T1-R6', 'severity': 'minor',
        'title': 'The independently authored acknowledgement obligation contains an unrelated preference',
        'rationale': 'The choice-selected clause says acknowledgement or Wi-Fi preference, and the route reason repeats this. T1 has no Wi-Fi preference. This is a source clarity discrepancy; the frozen T1 Boolean expectations themselves are consistent.',
        'affected_platforms': ['ios', 'android'],
        'source_refs': [ref(D+'public/reference.json', '/obligations/5/clause'), ref(D+'public/routes.json', '/routes/choice-selected/reason'), ref(D+'private/reference.json', '/obligations/5/clause')],
        'required_revision': 'Remove the unrelated alternative in a separately sealed revision; do not silently edit this proposal.'
    }
]

def row(clause, routes, result='complete_for_declared_scenarios', limitation=None):
    item = {'brief_clause': clause, 'existing_obligations_or_routes': routes,
            'independent_mapping_result': result, 'platforms': ['ios', 'android']}
    if limitation:
        item['gap_or_limit'] = limitation
    return item

mapping = [
    row('BRIEF:3 genuine production component on SwiftUI and Compose', ['API.md exported signatures and production paths', 'thin bridges', 'execution_plan source-root binding'], limitation='SDK-free source/design review; actual product compilation is intentionally deferred.'),
    row('BRIEF:5 both seal and coolant are required', ['primary-enabled', 'status-label'], 'incomplete', 'T1-R2: held models are assessed only while unacknowledged.'),
    row('BRIEF:5 broken seal precedes coolant absence', ['status-label'], limitation='P1 replacement covers seal false/coolant true; P2 covers true/false; H1 privately covers false/false with Seal needs attention.'),
    row('BRIEF:6 initially unchecked', ['choice-selected', 'choice-label', 'primary-enabled', 'status-label']),
    row('BRIEF:6 first choice sets true and emits exactly once', ['choice-receipt action 2', 'choice-selected permitted', 'choice-label permitted']),
    row('BRIEF:6 second pre-release choice clears and emits false', ['choice-selected', 'choice-receipt'], 'incomplete', 'T1-R1: no second activation or false event expectation.'),
    row('BRIEF:6 acknowledgement cannot override either hold', ['primary-enabled', 'status-label'], 'incomplete', 'T1-R2: no held+acknowledged state.'),
    row('BRIEF:7 eligible acknowledged primary calls onRelease(id) once and becomes requested', ['request-receipt action 4', 'primary-label', 'primary-enabled', 'choice-enabled', 'status-label']),
    row('BRIEF:7 no second release in local requested state', ['primary-enabled requested', 'choice-enabled requested', 'real native Buttons in API.md'], limitation='Disabled semantics are the approved constraint; no blocked tap is claimed as successful callback dispatch.'),
    row('BRIEF:7 records request without physical transfer', ['public API callback scope', 'BRIEF out-of-scope hardware/navigation/network definition'], limitation='Physical hardware behavior is outside this component acceptance scope.'),
    row('BRIEF:8 disclosure initially closed', ['disclosure-label overview', 'collapsed-content overview'], 'incomplete', 'The visual absence proposition omits headings; see T1-R3.'),
    row('BRIEF:8 disclosure toggles all heading/body pairs in caller order', ['section-N-heading/body', 'expanded-order', 'collapsed-content'], 'incomplete', 'T1-R3: open path only; no close stimulus; collapsed proposition only mentions bodies.'),
    row('BRIEF:8 disclosure emits no caller callback', [], 'missing', 'T1-R3: no event rule or obligation for disclosure action interval.'),
    row('BRIEF:8 Review/Hide labels reflect local state', ['disclosure-label']),
    row('BRIEF:9 different ID resets acknowledgement/disclosure/requested', ['replacement-quiet action 6', 'choice-selected replaced', 'choice-enabled replaced', 'disclosure-label replaced', 'primary-label replaced', 'primary-enabled replaced', 'collapsed-content replaced']),
    row('BRIEF:9 replacement renders title/destination/temperature/guards in same mount, callback quiet', ['title-label replaced', 'subtitle-label replaced', 'status-label replaced', 'replacement-quiet caller_update action 6', 'thin bridge/host inspection']),
    row('BRIEF:11 exact status precedence and primary predicate', ['status-label', 'primary-enabled'], 'incomplete', 'Guard priority has a hidden false/false example; acknowledged held predicate branch is absent (T1-R2). Same-ID behavior is expressly unspecified and is not added by this review.'),
    row('BRIEF:11 exact subtitle and control labels', ['subtitle-label', 'disclosure-label', 'primary-label', 'choice-label']),
    row('BRIEF:13 overview/permitted/requested/replaced actual checkpoints', ['explicit state definitions after actions 0/3/5/7, stimuli 2/4/6', 'compile_execution complete manifests']),
    row('BRIEF:13 ordinary P1 and narrow large P2, native host padding, same source/API', ['fixture profile fields', 'environment digests', 'host source inspection', 'execution source fingerprints'], limitation='400/280 viewport widths produce component offered widths 368/248 native units. Android uses the named Float32 encoding; actual environment remains to be collected.'),
    row('BRIEF:15 full-width canvas with component-owned surface', ['canvas-fill', 'surface-fill', 'policy ownership'], 'incomplete', 'Solid-region ownership is explicit, but full width has no obligation or verification proposition (T1-R5).'),
    row('BRIEF:15 one vertical flow in specified order', ['flow-order', 'expanded-order', 'row-overlap']),
    row('BRIEF:15 nominal internal dimensions/gaps/status minimum', ['typography-nominal advisory disposition'], 'explicitly_advisory', 'No generic SwiftUI layout allocation is fabricated.'),
    row('BRIEF:15 actual choice-to-primary gap 12 ±0.75', ['choice-primary-gap geometry/control/accessibility_box'], limitation='Both real controls must be fully visible in one coherent frame. Bottom sweep frames plausibly contain the adjacent controls; measurement support is native AX pt and Compose integer px/density.'),
    row('BRIEF:15 status text inset at least 16 and leading 4% empty', ['status-fill sample at normalized x=0.012..0.035'], 'incomplete', 'T1-R5: sample-region color does not measure text inset or the entire leading 4%.'),
    row('BRIEF:15 all text wraps without line limits', ['title-wrapping', 'body-wrapping'], 'incomplete', 'T1-R4: remaining text classes have no wrapping proposition.'),
    row('BRIEF:15 no fixed blank spacer rows and no nested component scroller', [], 'missing', 'T1-R5: full-content reachability alone does not check these structural prohibitions.'),
    row('BRIEF:17 exact distinct solid roles, atomic fill/canvas/ink', ['status-fill', 'primary-fill', 'surface-fill', 'canvas-fill', 'ink-fill'], limitation='Opaque ARGB anchors and zero channel tolerance are preserved. Ink mark is the measured carrier, not proof of every glyph color.'),
    row('BRIEF:17 exact computed SwiftUI font and text color', ['typography-nominal empty route with rationale'], 'explicitly_advisory', 'Unsupported computed facts are not silently promoted to MUST passes.'),
    row('BRIEF:17 hierarchy/wrapping/overlap/clipping remain separate visual propositions', ['title-hierarchy', 'title-wrapping', 'body-wrapping', 'row-overlap', 'horizontal-clipping'], limitation='Atoms are individually source-backed; all-text scope gap is T1-R4.'),
    row('BRIEF:19 native semantics vs pixels vs two independent qualitative reviews', ['control rules', 'policy native_pixels atoms', 'policy visual atoms', 'COLLECTION.md two-review requirement', 'acceptance.consensus']),
    row('BRIEF:19 long content overlapping sweep and actual bottom reachability', ['full_content for every state', 'native sweep state_captures', 'execution_plan.coverage_receipt', 'review_contract.bind'], limitation='Content/height sizing is illustrative. Native full sweeps, overlap, stable binding and sentinel remain mandatory at execution.'),
    row('BRIEF:19 successful callback stimuli and real caller update interval', ['choice-receipt stimulus 2', 'request-receipt stimulus 4', 'replacement-quiet caller_update stimulus 6', 'native_checks.callback_verdict']),
    row('BRIEF:21 exclusions and independent preimplementation review', ['scope exclusions', 'source-pinned current review'], limitation='No SDK, app launch, production implementation, prior case, assignment or other review was accessed.')
]
save('semantic-mapping.json', {'version': 1, 'rows': mapping,
     'each_public_BRIEF_MUST_mapping_complete': False,
     'distinction': 'The frozen route audit is complete against its own index. This independently authored mapping finds prose clauses absent from that index or not actually exercised.'})

technical = {
    'bridges_and_host_calls': 'Swift ObserverBridge.make(fixture:onEvent:) returns AnyView of the exported AlertToast initializer; Kotlin ObserverBridge.Content(JsonObject,(String)->Unit) matches the actual trailing-lambda host call and imports the declared Reply package. Parameter names/types and callback interpolation match API.md. Bridges only decode models and forward events; no wrapper id/key, local UI/state, expectation or reset logic is present.',
    'state_ownership_and_identity': 'Same bridge position and component type are preserved by both hosts. Component-owned identity reset is feasible with the declared production API; the existing bridges do not perform it. This is a feasibility assessment, not an observation of a product reset.',
    'semantic_allocation': 'Canvas/surface can be noninteractive semantic containers preserving descendants; status can expose its whole painted band; solid accent can be an explicitly accessible noninteractive rectangle. These are feasible public native semantics allocations. Unique target resolution and native ancestry prevent duplicate proxies or multi-control groups from earning typed control/pixel results. Actual platform trees are intentionally deferred.',
    'geometry': 'Control/accessibility_box is supported by both native geometry routes. SwiftUI internal layout_box is not asserted. The 56 primary and 12 gap use source-backed pt/dp values and 0.75 same-unit tolerances. Adjacent bottom controls can share a 600-unit frame; full sweep rather than independent disjoint control crops is required.',
    'pixel_regions': 'At offered widths 368 and 248, 8-unit canvas and 16-unit surface gutters leave the approved physical-left sample strips inside solids. Status/primary leading strips, opaque mark center and minimum pixel counts are feasible; surface/canvas explicitly permit visible fragments for tall allocations. RTL text alignment does not itself invalidate a physical-left solid inset sample when both horizontal insets are painted. Pixel strips do not prove wrapping, text color, exact text inset or full-width allocation.',
    'expected_units_tolerances_and_provenance': 'Frozen compiler and catalog reconstruct all 123 assertions and 44 manual atoms per scenario/platform, including typed expected values, geometry tolerance sources and qualitative proposition provenance, exactly from the sealed lock and policy. No implementation-derived expectations were supplied.',
    'NA_rationale': 'Closed disclosure descendant text, expanded body/hierarchy/order when descendants do not exist, opposite disclosure propositions, and unrelated callback stimulus classes have specific N/A rationales. These are reasonable cell dispositions for the stated four checkpoints; they do not cure missing business transitions, missing disclosure headings absence or missing obligation scope.',
    'public_and_hidden_profiles': 'P1 ordinary and P2 narrow/large public profiles match their launch/environment sources. H1 is independently fixed, changes ID/title/destination/temperature/notes and direction to RTL, uses the identical production API and bridge, and exercises a both-guards-false replacement. Private values were read solely under this review authorization and must not be included in builder prompts.',
    'reference_PNG_SVG_inspection': 'Inspected all 12 state reference PNGs directly and parsed all state/reference SVG structures. Copy, state roles, vertical order, realistic nonblank reading material and RTL alignment are expressed independently. P2 expanded PNGs are tall (3120 illustrative pixels); exact native font rasterization or height is not inferred from them. The P2 status illustration is a single SVG text run and must not replace the required native wrapping assessment.',
    'tool_issue_result': 'No general frozen-tool defect was established by these SDK-free checks. Two reviewer-probe assumptions failed before correction: caller includes profile fields, and frozen catalog CLI adds a self-excluding catalog_sha256. Original scripts/errors were retained. Neither was a proposal mutation or tool fix.'
}
save('technical-feasibility.json', technical)

mechanical = load('mechanical-checks.json')
report = {
    'version': 1,
    'status': 'revision_required',
    'approval': 'Not approved. Preserve this proposal and independently revise/reseal the missing requirements before builders or native runs.',
    'task': 'T1',
    'startedAtUnix': load('phase-start.json')['startedAtUnix'],
    'finishedAtUnix': time.time(),
    'source_exact_hashes': {'manifest': 'source-files.json', 'manifest_sha256': hashlib.sha256((OUT/'source-files.json').read_bytes()).hexdigest(),
        'public': mechanical['source_seals']['public'], 'private': mechanical['source_seals']['private'],
        'frozen_skill': ref(F+'SKILL.md'), 'request': ref('validation/feedback-forward/operators/T1-design-review-request.txt')},
    'mechanical_checks': {
        'detail_file': 'mechanical-checks.json', 'source_files_unchanged_at_finish': True,
        'source_seal_file_counts': {'public': 68, 'private': 41},
        'case_platform_reconstructions': 6, 'all_exactly_match': True,
        'assertions_per_case_platform': 123, 'catalog_atoms_per_case_platform': 44,
        'api_attempts': 62, 'expected_generic_verifier_rejections': 12,
        'event_stimulus_actions': {'choice-receipt': 2, 'request-receipt': 4, 'replacement-quiet': 6},
        'sweep_checkpoints': {'overview': 0, 'permitted': 3, 'requested': 5, 'replaced': 7},
        'route_audit_gaps_against_existing_index': [],
        'caller_update_success_gate_generic_test': 'successful same-process update passes; unsuccessful update plus empty interval remains unassessed',
        'native_execution_performed': False, 'product_acceptance_claimed': False,
        'commands_and_errors': ['commands.json', 'api-attempts.json', 'reconstruction.attempt-1.stderr.log', 'reconstruction.stderr.attempt-2.log', 'reconstruction.stderr.log']},
    'each_MUST_mapping_complete': False,
    'feasible_on_both_platforms': True,
    'feasibility_scope': 'The declared component/API and currently authored native/geometry/pixel/visual/update routes are technically feasible and reconstruct under the actual frozen APIs. This true value does not approve semantic coverage: several required clauses lack routes, as listed below. No native build or runtime feasibility result is claimed.',
    'complete_requirement_set_has_verification_route': False,
    'production_paths': ['Sources/AlertToast/ColdStorageTransferPanel.swift', 'app/src/main/java/com/example/reply/ui/components/ColdStorageTransferPanel.kt'],
    'production_path_roots': {'Sources/AlertToast/ColdStorageTransferPanel.swift': {'repository': 'AlertToast', 'revision': '76a1c1793cd3443001c20c6033beb84453b25d9f'}, 'app/src/main/java/com/example/reply/ui/components/ColdStorageTransferPanel.kt': {'repository': 'Reply upstream Gradle root', 'revision': '53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79'}},
    'issues': issues,
    'semantic_mapping_file': 'semantic-mapping.json',
    'technical_feasibility_file': 'technical-feasibility.json',
    'remaining_limits': [
        'This is an independent preimplementation, SDK-free feasibility review. Production source, native SDK evidence, implementation outcomes, other reviews and assignments were not read.',
        'Source hashes establish proposal identity and exact reconstruction, not authorship or complete understanding. Missing prose routes are blockers despite the index audit reporting zero gaps.',
        'Actual compiler availability, iOS 14 product compilation, real semantic allocations, exact rendered sample support, full native sweep coverage and panel agreement await separately authorized implementation/execution after independent design closure.',
        'The advisory computed SwiftUI typography/text-color/internal-allocation route is intentionally unavailable. No MUST was passed using fabricated computed style facts.',
        'No design, tool or expectation was edited; no SDK/rendering/app launch, production changes, commits or agent communication occurred. Two reviewer harness parser assumptions and their errors are retained.'
    ]
}
save('review.json', report)

commands = load('commands.json')
commands.append({'command': 'python3 -B validation/feedback-forward/design-review/T1/write_review.py',
                 'purpose': 'Write independent semantic mapping, technical assessment and revision_required review; verify all pinned source hashes unchanged.'})
commands.append({'tool': 'view_image', 'purpose': 'Directly inspect original independent PNG files; no rendering or editing',
                 'paths': [D+scope+'/references/'+case+'/'+state+'.png' for scope,case in [('public','P1'),('public','P2'),('private','H1')] for state in ['overview','permitted','requested','replaced']]})
save('commands.json', commands)
print(json.dumps({'status': report['status'], 'issues': len(issues),
                  'each_MUST_mapping_complete': report['each_MUST_mapping_complete'],
                  'feasible_on_both_platforms': report['feasible_on_both_platforms'],
                  'finishedAtUnix': report['finishedAtUnix']}))
