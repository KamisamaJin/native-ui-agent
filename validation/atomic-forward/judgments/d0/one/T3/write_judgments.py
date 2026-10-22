from pathlib import Path
import json,sys,collections
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT=BASE/'judgments/d0/one/T3'
sys.path.insert(0,str(BASE/'candidate-v8/scripts'))
import native_checks

def save(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')
clip_indices={('source-a','baseline'):[25,26,27],('source-a','expanded'):[59,60],('source-a','submitted'):[141,142],('source-b','baseline'):[24,25],('source-b','expanded'):[56,57],('source-b','submitted'):[134,135,136]}
summary=[]
for p in sorted((BASE/'evaluation-inputs/d0/T3').glob('*/*/*')):
    so,pl,ca=p.parts[-3:];d={n:json.loads((p/(n+'.json')).read_text()) for n in ['inputs','plan','catalog','automatic','environment-check']};i=d['inputs'];o=json.loads((BASE/i['observation']).read_text());states={s['id']:native_checks.bound_state_evidence(o,s) for s in d['plan']['states']}
    decisions=[];attributions=[]
    for row in d['catalog']['rows']:
        if row['method']!='visual':continue
        sid=row['state'];found,complete,why,capture=states[sid];indices=[idx for idx,_ in found]
        actual=True
        if row['aspect']=='wrapping':
            reason='The complete bound scroll sequence shows the title, subtitle, notice, all six service labels and their detail/reason copy, summary, disclosure label, action label and footer in readable wrapped lines. No required visible text is omitted or visibly truncated; viewport-edge fragments are fully readable in overlapping captures.'
            if sid=='expanded':reason+=' The entire opened global handover body is present below the disclosure and wraps without clipping.'
            else:reason+=' The global guidance is deliberately collapsed in this state.'
            if ca=='P2' and pl=='ios':reason+=' Long words in narrow item-label columns break between characters when the word exceeds that column; every character continues on the next line, with no ellipsis.'
        else:
            reason='Across the complete exact-state scroll sequence, the text blocks, choice indicators, unavailable status/reason, summary, disclosure, primary action and footer remain separated. No unintended overlap or occlusion is visible; clipping at the host viewport edges during scrolling is resolved by adjacent captures.'
        if pl=='android' and ca=='P2':
            actual=False
            label='Hide handover notes' if sid=='expanded' else 'Show handover notes'
            clipped=clip_indices[(so,sid)]
            if row['aspect']=='wrapping':
                reason=f'The original fully visible disclosure control renders {label!r} on two lines, but its rounded left boundary visibly cuts off the beginning of the first letter of both lines. This is word/glyph clipping inside the component, not a viewport-edge fragment or a missing semantic label. Other required text is present; the explicit no-visible-word-clipping wrapping proposition is false.'
            else:
                reason=f'The disclosure control’s rounded left boundary visibly occludes leading glyph portions in both lines of {label!r} while its native box is fully visible. The separate content blocks otherwise do not collide, but the proposition also excludes unintended occlusion. This is that occlusion, not a line-breaking complaint.'
            attributions.append({'id':row['id'],'cause':'product','reason':f'Original same-state frames {clipped} show the identical curved cuts at the two-line disclosure’s leading edge with its entire native activation box inside the viewport. The production Compose TextButton uses zero content padding and its default rounded shape; the component owns this disclosure and its typography. The clip moves with the control across scroll positions, so host viewport clipping, missing state evidence and resizing of contact sheets do not explain it. This is one disclosure-shape clipping cause manifested in both qualitative atoms, not two independent bugs.','snapshot_indices':clipped})
        if so=='source-a' and pl=='ios' and sid=='submitted':
            if row['aspect']=='wrapping':
                actual=None
                reason='The actually rendered words are readable and show no visible truncation, but the authoritative replacement input selects b and the later successful a toggle requires a+b in the submitted summary. The captured summary instead contains a alone and 20 min, omitting the required wheel-selection summary text. The proposition explicitly forbids treating missing required text as correct wrapping; wrapping of that absent content is unknown.'
            if not complete:
                actual=None
                reason+=' '+('Additionally, ' if row['aspect']=='wrapping' else '')+'The frozen bound_state_evidence reports an incomplete per-state interval union for this exact submitted state, so a complete-content visual pass cannot be established even though a bottom/footer frame exists.'
        if not found:
            actual=None;indices=[];reason='No exact coherent state-bound original evidence: '+why
        elif not complete and actual is True:
            actual=None;reason='The frozen bound_state_evidence reports '+why+'; full-content coverage is required and a bottom frame alone cannot establish it.'
        decisions.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
    for row in d['automatic']['assertions']:
        if row['status']!='failed':continue
        sid=row['state'];found,complete,why,capture=states[sid];allowed=[idx for idx,_ in found]
        if not allowed:continue
        indices=[idx for idx in row.get('snapshot_indices',[]) if idx in allowed]
        if not indices:
            indices=[idx for idx,snap in found if snap.get('callbacks')][-2:] or allowed[-2:]
        rid=row['id']
        if rid=='baseline/primary-surface-color':
            reason='The recomputed frozen pixel sample lies in a solid, glyph-free side strip of the actual fully visible disabled primary button, with suitable dominant support. The original PNG visibly dims the entire button fill and text. Source defines the approved disabled palette value on the label background but applies native disabled behavior to the plain SwiftUI button; the rendered disabled treatment changes that owned surface. The sampled region is the component action, not the host or a text leaf, so this is a product rendered-style defect, not an unsuitable observation. The precise platform compositing mechanism is inferred from source plus visible disabled treatment; the strict pixel contradiction itself is recomputed.'
        elif sid=='replaced':
            reason='The caller advances in the same process to fixture 1 (revision bicycle-1), whose actual incoming initialSelectedIDs is [b]; the updated notice is visibly present and stable input/epoch bindings agree. Nevertheless the component shows neither service selected, No work selected / 0 min, and a disabled primary button. The component’s revision-driven state handling fails the authoritative incoming selection. This same product behavior explains the summary, enablement and disabled action-fill failures; they are not independent root causes. Source-a’s SwiftUI state/onChange implementation owns resetting selection; no host input or screenshot-epoch failure is evidenced.'
        elif sid in ['reselected','submitted']:
            reason='The original fixture-1 frames show only a selected and its 20-minute summary even though the authoritative replacement selected b and the later a action adds a. The demonstrated native a toggle emits bicycle:toggle:a:true, establishing that a is being added after the replacement rather than deselected. The component has lost b during revision replacement; the continued summary/callback failures are manifestations of that product state defect. Source, changed notice, actual fixture and stable native bindings establish that the caller update reached the live component. This assessment does not infer a handler from a label or a blocked disabled action.'
        else:
            reason='A supported exact-state failure exists, but this review does not establish a specific ownership cause.'
        if sid=='submitted':
            reason+=' The successful native xcui_tap at stimulus action 8 emits bicycle:submit:a; the exact submitted-state frames retain that callback interval and fixture binding, confirming the wrong forwarded set after demonstrated activation.'
        attributions.append({'id':rid,'cause':'product' if sid in ['baseline','replaced','reselected','submitted'] else 'uncertain','reason':reason,'snapshot_indices':indices})
    judge={'review':{'version':1,'catalog_sha256':d['catalog']['catalog_sha256'],'observation_sha256':i['observation_sha256'],'decisions':decisions},'attributions':attributions}
    save(OUT/so/pl/ca/'judge.json',judge)
    counts=collections.Counter('unknown' if r['actual'] is None else str(r['actual']).lower()for r in decisions)
    summary.append({'source':so,'platform':pl,'case':ca,'qualitative':dict(counts),'attributions':len(attributions)})
save(OUT/'judgment-summary.json',summary);print(json.dumps(summary,indent=2))
