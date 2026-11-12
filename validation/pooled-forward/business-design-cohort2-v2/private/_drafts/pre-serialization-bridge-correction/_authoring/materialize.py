#!/usr/bin/env python3
"""Fix all five new designs together, then run the frozen pure tool chain."""
from author import *
import html

def bridge(t,platform):
    fields=COMMON_FIELDS+t['fields']
    if platform=='ios':
        def value(k,typ):
            cast={'String':'String','Int':'Int','Bool':'Bool','List<String>':'[String]'}[typ]
            return 'fixture["'+k+'"] as! '+cast
        args=',\n            '.join(k+': '+value(k,v) for k,v in fields)
        return f'''// Thin fixture decoder only; this file contains no business UI or local state.
import SwiftUI
import AlertToast

enum ObserverBridge {{
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {{
        let input = {t['model']}(
            {args}
        )
        return AnyView({t['api']}(input: input, onEvent: onEvent))
    }}
}}
'''
    def value(k,typ):
        return {'String':f'fixture.get("{k}").asString','Int':f'fixture.get("{k}").asInt','Bool':f'fixture.get("{k}").asBoolean','List<String>':f'fixture.getAsJsonArray("{k}").map {{ it.asString }}'}[typ]
    args=',\n            '.join(k+' = '+value(k,v) for k,v in fields)
    return f'''// Thin fixture decoder only; no UI, business logic, state, or identity modifier.
package org.nativeobserver

import androidx.compose.runtime.Composable
import com.google.gson.JsonObject
import com.example.reply.ui.components.business.{t['model']}
import com.example.reply.ui.components.business.{t['api']}
import com.example.reply.ui.theme.ContrastAwareReplyTheme

object ObserverBridge {{
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {{
        val input = {t['model']}(
            {args}
        )
        ContrastAwareReplyTheme {{
            {t['api']}(input = input, onEvent = onEvent)
        }}
    }}
}}
'''

def api_doc(t):
    fields=COMMON_FIELDS+t['fields'];swiftmap={'String':'String','Int':'Int','Bool':'Bool','List<String>':'[String]'}
    swift='\n'.join('    public let '+k+': '+swiftmap[v] for k,v in fields)
    swiftinit=', '.join(k+': '+swiftmap[v] for k,v in fields)
    kotlin=',\n'.join('    val '+k+': '+('Boolean' if v=='Bool' else v) for k,v in fields)
    return f'''# {t['name']}: public production contract

This is an additive reusable component. All types below are public production API.
No implementation exists in this design bundle. Swift declarations show signatures,
not compilable bodies. Kotlin models use immutable `val` fields; Swift uses `let`.

Every fixture `Int` must also satisfy fixture.schema.json. The shared transport
domain is signed32-bit: -2147483648 through2147483647. Existing field-specific
positive/nonnegative minima and portfolioScore's maximum100 narrow that domain.
In particular, revision is0 through2147483647 and accountBalanceCents is the full
signed32-bit domain. Swift accepts this common domain and Kotlin/Gson decodes it
without numeric narrowing. Out-of-schema values are outside this API contract.

Revision is an opaque comparison key supplied by the caller, never incremented
by this component. The published decisions use comparisons, key equality, and
string formatting; they require no sums or products. The finite frozen fixtures
do not establish arbitrary implementation arithmetic or universal overflow safety.

Swift file: `Sources/AlertToast/Business/{t['api']}.swift`, exported by existing product `AlertToast`.
Minimum deployment remains the stock package's iOS 14. Do not replace the package API.

```swift
public struct {t['model']}: Equatable {{
{swift}
    public init({swiftinit})
}}
public struct {t['api']}: View {{
    public init(input: {t['model']}, onEvent: @escaping (String) -> Void)
    public var body: some View {{ get }}
}}
```

Kotlin file: `app/src/main/java/com/example/reply/ui/components/business/{t['api']}.kt`.

```kotlin
package com.example.reply.ui.components.business

data class {t['model']}(
{kotlin}
)
@Composable
fun {t['api']}(input: {t['model']}, onEvent: (String) -> Unit)
```

The exact supplied bridges decode the immutable fixture and pass the same `onEvent`
directly. Android's `org.nativeobserver.ObserverBridge` object applies the stock
`ContrastAwareReplyTheme`. iOS's factory returns `AnyView` of the production view.
No bridge-owned UI, state, business decisions, fixture-index lookup, `.id`/key reset,
callback transformation, effects, tasks, timers, loading, network, or asynchronous work.
The production component owns all transient selection and receipt state.
'''

def schema(t):
    props={}
    for k,typ in COMMON_FIELDS+t['fields']:
        val=({'type':'string'} if typ=='String' else {'type':'integer'} if typ=='Int' else {'type':'boolean'} if typ=='Bool' else {'type':'array','items':{'type':'string'}})
        if typ=='Int' and k!='accountBalanceCents':val['minimum']=0
        if typ=='Int':val['maximum']=2147483647
        if k=='accountBalanceCents':val['minimum']=-2147483648
        if k=='entityID':val['pattern']='^[A-Za-z0-9._-]+$';val['minLength']=1
        if k in ('guestCount','seatCount'):val['minimum']=1
        if k=='portfolioScore':val['maximum']=100
        props[k]=val
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':t['model'],'type':'object','additionalProperties':False,'properties':props,'required':list(props)}

def brief(t):
    roots='\n'.join(f'- `{k}` — **{v}**.' for k,v in t['roots']);details='\n'.join(f'- `{k}` — **{v}**.' for k,v in t['details'])
    rules='\n'.join(f'{i+1}. {v}' for i,v in enumerate(t['rules']))
    return f'''# {t['name']}

Build the API in API.md, following this complete public rule set and the sealed
public expected-state table. Private testing adds inputs and paths under these same
rules. It introduces no new requirements or hidden flags.

## Business inputs and decisions

`fixture.schema.json` fixes every input type and valid range. Inputs contain raw
request facts and display content only, with no selected/ready/expected/decision fields.
All Int fields are restricted to the shared signed32-bit transport domain; tighter
positive/nonnegative minima and portfolioScore's maximum100 remain normative.
The component compares the caller's revision key and never computes its successor.
No published rule requires an integer sum or product. The finite corpus provides
no blanket implementation-overflow guarantee outside its listed inputs.
`entityID` is a nonempty delimiter-free identifier; `revision` is a caller-published
nonnegative revision. Empty notes are valid; render their joined text as an empty
label without a placeholder. All title/context/notes strings wrap completely.

Package-level choice labels and IDs are constant, in this order:

{roots}

Dependent choice labels and IDs are constant, in this order:

{details}

Eligibility is deterministic and uses inclusive boundaries exactly as written:

{rules}

All options remain in the document, including unavailable ones. A detail is enabled
only when a root is currently selected and its own eligibility predicate is true.
Disabled rows preserve their natural labels and provide native disabled semantics.
Each choice and confirmation is a native Button with an exact visible label. A
selected button has native selected semantics plus a visible check indicator.
There are no popups, dialogs, menus, overlays, lazy containers, or internal scrolling.

## Transient state and dependency ordering

A fresh instance has no root or detail selected, confirmation false, and no receipt.
Choosing a different eligible root clears detail and confirmation. Choosing a
different eligible detail clears confirmation. Tapping the already selected root
or detail is idempotent and preserves dependent state. Confirmation is a toggle
button labelled **{t['ack']}**, enabled only while valid root and detail exist.

**{t['submit']}** is enabled only when root and detail remain eligible, confirmation
is true, and no request is recorded. A successful actual activation emits exactly
one callback, synchronously, before setting the receipt and locking choices,
confirmation, and primary action. Disabled controls never invoke a business handler.
Selection changes, confirmation toggles, and caller updates emit no callbacks.

Callback grammar, using the selected stable IDs, has no spaces:

`{t['event']}|<entityID>|<revision>|<rootID>|<detailID>|<{t['quantityField']}>`

The recorded display is **{t['receipt']}**; before recording it is **No request recorded.**
No raw callback transport string is displayed to the operator.

For every caller replacement, first compare `(entityID, revision)` to the previous
input. A changed entity OR changed published revision resets all local state,
including a recorded receipt, even when other values match. No indistinguishable
same-value callback epoch or host-index reset is required. For the same pair,
preserve valid state and any receipt; update all display content immediately.
Re-evaluate root eligibility before detail eligibility. An invalid selected root
clears root, detail, confirmation, and receipt. Otherwise an invalid selected detail
clears detail, confirmation, and receipt. Remaining valid selections/confirmation
and a receipt are preserved, even if other raw facts change. Reconciliation emits
no callback and uses no forced view identity in the bridge.

## Exact text generation

Display notes as `notes.joined(separator: "\\n\\n")` / `joinToString("\\n\\n")`.
Render a stable summary in this exact order, substituting full visible choice labels
or **Not chosen**:

`{t['rootCaption']}: <root label>. {t['detailCaption']}: <detail label>. <{t['quantityField']}> {t['quantityUnit']}.`

Status uses the first matching branch:

1. Recorded: `Recorded. Selections are locked for this request.`
2. No eligible root: `No {t['rootNoun']} is eligible for these request details.`
3. Root unselected: `Choose a {t['rootNoun']}.`
4. Detail unselected: `Choose a {t['detailNoun']} for <root label>.`
5. Confirmation false: `Confirm {t['ackShort']} to continue.`
6. Ready: `Ready to {t['submit'][0].lower()+t['submit'][1:]}.`

The reference table fixes all public state strings, selected/disabled controls,
and callback deltas from this grammar. It is normative and independently authored.

## Layout, visual semantics, and evidence scope

Use DESIGN.md, tokens.json and the authored SVGs. Dynamic text must grow vertically,
remain at its specified native type size, and never truncate, shrink, or overlay.
The host owns the only vertical scroll; the component fills its finite offered
width. Long title, context, notes, summary, and receipt must all remain reachable.
Do not move UI into the bridge or special-case a fixture value or state label.

Minimal local observation tags are listed in bindings.*.json. They apply only to
the real component's surface and dynamic Text nodes. Natural action labels identify
buttons; there is no global ID registry or test-only replacement UI.

Native semantics, native AX/Compose control-box geometry, and automatic opaque RGB
gutters have separate claims. iOS public AX cannot measure generic SwiftUI computed
fonts, padding, or colors. iOS typography/wrapping use source-backed visual Boolean
questions; exact native font/color slots are explicitly N/A in MASTER-DENOMINATOR.
Android adds precise available TextLayout facts. These are planned observations,
not results, source approvals, or claims of native execution.
'''

TOKENS={
 'surface':typed('#FFF7F9FC','argb'),'row':typed('#FFFFFFFF','argb'),'selected':typed('#FFE5F1FF','argb'),
 'accent':typed('#FF2459A6','argb'),'disabled':typed('#FFD9E1EC','argb'),'ink':typed('#FF15243B','argb'),
 'muted':typed('#FF526174','argb'),'onAccent':typed('#FFFFFFFF','argb'),'outline':typed('#FFB8C5D6','argb'),
 'ios':{'titleSize':typed(24,'pt'),'bodySize':typed(15,'pt'),'sectionSize':typed(16,'pt'),'weightTitle':typed(600,'scalar'),'weightBody':typed(400,'scalar'),'padding':typed(16,'pt'),'gap':typed(12,'pt'),'minControlHeight':typed(48,'pt'),'corner':typed(12,'pt')},
 'android':{'titleSize':typed(24,'sp'),'bodySize':typed(15,'sp'),'sectionSize':typed(16,'sp'),'weightTitle':typed(600,'scalar'),'weightBody':typed(400,'scalar'),'padding':typed(16,'dp'),'gap':typed(12,'dp'),'minControlHeight':typed(48,'dp'),'corner':typed(12,'dp')},
}

DESIGN='''# Authored design system

The SVGs are independent structure references, never candidate screenshots or pixel
regression baselines. Numeric tokens are native units in tokens.json. Preserve the
stock package/product and Android theme; the component sets these explicit local
surface/type values inside the theme rather than changing a global theme.

Host: offered 390, vertical viewport 600, LTR, light, 16 horizontal inset and 24 top
inset. iOS Dynamic Type Large; Android fontScale 1.0, native density 2.75, requested
390x600 through paparazzi-float32-screen-config-v1. Requested width is not a rounded
actual viewport assertion. Actual Android screen pixels are1072x1650 at density2.75.

Component: fill offered child width, opaque surface #FFF7F9FC, corner radius12,
16 native units inner padding. Header title24 semibold (600), body/context/notes15
normal (400); all text left aligned with ink #FF15243B, secondary text #FF526174.
Use system/SansSerif fonts, no bundled or custom typeface. Root/detail captions16
semibold, visible content ordered title, context, notes, root caption/options,
detail caption/options, summary, confirmation, status, receipt, primary action.
Every block has12 native units vertical separation. No fixed total content height.
Notes may be empty. All supplied strings retain their full content and wrap.

Choice rows: native Button, minimum48pt/dp semantic control height, full width,
8 corner radius, solid #FFFFFFFF fill when unselected, #FFE5F1FF when selected.
Unselected outline1 #FFB8C5D6; selected outline2 #FF2459A6. Inner content inset16,
label15 normal, left aligned, check indicator at trailing edge16 from the edge
only while selected. Disabled labels/indicators #FF526174; enabled labels ink.
Keep the whole Button's native frame around the styled row. Disabled selected rows
retain the selected fill/check; there is no opacity modifier on the whole control.

Confirmation: same row geometry and selected cues, native button toggling selected.
Primary: full width, minimum48pt/dp native control height, corner8, centered label16
semibold; enabled solid #FF2459A6 with #FFFFFFFF text, disabled solid #FFD9E1EC
with #FF526174 text. Lock after recording through native disabled semantics.
Summary is16 semibold ink; status and receipt15 normal muted. No shadows, icons
other than selection checks, gradients, translucent fills, or animations.

Surface gutter pixel sampling: normalized x.02–.035, y.20–.80 within the actual
component surface semantic box. Inner padding keeps children outside the gutter.
Use visible-fragment scope for an oversized surface. Row/button gutter sampling:
x.02–.035, y.25–.75 in the actual control box, outside text/check ink and rounded
corners. Expect opaque dominant sRGB with zero channel tolerance, at least12pixels,
minimum support0.90. These are rendered samples, not computed style/color claims.

Geometry assertions measure the actual native semantic/control accessibility box,
not effective padding or physical touch area. Full-content states have wrapping,
overlap, horizontal clipping and type-hierarchy visual atoms. Intermediate states
have explicit target sets and local fill/check/control facts, without claiming a
whole-state scan. No extra decorative measurement nodes are introduced.
'''

def svg(t,f,s):
    from xml.sax.saxutils import escape
    vals=expected(t,f,s); rows=[];y=48
    def text(value,size=15,weight=400,color='#526174'):
        nonlocal y
        maxchars=24 if size==24 else 42
        for para in value.split('\n'):
            for line in textwrap.wrap(para,maxchars) or ['']:
                rows.append(f'<text x="32" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(line)}</text>');y+=size+6
        y+=12
    def button(label,selected,enabled):
        nonlocal y
        fill='#E5F1FF' if selected else '#FFFFFF'
        rows.append(f'<rect x="32" y="{y}" width="326" height="52" rx="8" fill="{fill}" stroke="'+('#2459A6' if selected else '#B8C5D6')+'"/>')
        rows.append(f'<text x="48" y="{y+31}" font-size="15" fill="'+('#15243B' if enabled else '#526174')+'">'+escape(label)+'</text>')
        if selected:rows.append(f'<text x="333" y="{y+31}" font-size="16" fill="#2459A6">✓</text>')
        y+=64
    text(f['title'],24,600,'#15243B');text(f['context']);text('\n\n'.join(f['notes']))
    text(t['rootCaption'],16,600,'#15243B')
    for k,label in t['roots']:button(label,vals['root-'+k+'-selected'],vals['root-'+k+'-enabled'])
    text(t['detailCaption'],16,600,'#15243B')
    for k,label in t['details']:button(label,vals['detail-'+k+'-selected'],vals['detail-'+k+'-enabled'])
    text(vals['summary-label'],16,600,'#15243B');button(t['ack'],vals['ack-selected'],vals['ack-enabled']);text(vals['status-label']);text(vals['receipt-label'])
    fill='#2459A6' if vals['submit-enabled'] else '#D9E1EC';ink='#FFFFFF' if vals['submit-enabled'] else '#526174'
    rows.append(f'<rect x="32" y="{y}" width="326" height="48" rx="8" fill="{fill}"/><text x="195" y="{y+30}" text-anchor="middle" font-size="16" font-weight="600" fill="{ink}">{escape(t["submit"])}</text>');y+=80
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="390" height="{y+24}" viewBox="0 0 390 {y+24}"><title>Independent authored design, not runtime output</title><rect width="390" height="{y+24}" fill="#FFFFFF"/><rect x="16" y="24" width="358" height="{y-24}" rx="12" fill="#F7F9FC"/><g font-family="system-ui, sans-serif">'+''.join(rows)+'</g></svg>\n'

def rules_for(t,platform):
    rules=[]
    for key in ['title','context','notes','status','summary','receipt']:
        rules.append(dict(id=key+'-label',kind='control',target=key,property='label',coverage='target'))
    for key in ['submit-enabled','ack-enabled','ack-selected']:
        target,prop=key.split('-');rules.append(dict(id=key,kind='control',target=target,property=prop,coverage='target'))
    for category in ['roots','details']:
        prefix='root' if category=='roots' else 'detail'
        for key,label in t[category]:
            for prop in ['enabled','selected']:rules.append(dict(id=prefix+'-'+key+'-'+prop,kind='control',target=prefix+':'+key,property=prop,coverage='target'))
    for rid,stim in [('activation-events','activation'),('replacement-events','caller_update')]:
        rules.append(dict(id=rid,kind='event',stimulus=stim,required_method='caller_fixture_update' if stim=='caller_update' else 'xcui_tap' if platform=='ios' else 'compose_onclick'))
    for name,target in [('primary-height','submit'),('first-option-height','root:'+t['roots'][0][0]),('confirmation-height','ack')]:
        rules.append(dict(id=name,kind='geometry',target=target,property='height',basis='control',measurement='accessibility_box',op='gte',coverage='target'))
    for rid,target,prop in [('surface-fill','surface','rendered_fill_argb'),('primary-fill','submit','rendered_fill_argb'),('first-option-fill','root:'+t['roots'][0][0],'rendered_fill_argb')]:
        rules.append(dict(id=rid,kind='manual',target=target,property=prop,coverage='target',allowed_methods=['native_pixels']))
    for rid,target,aspect in [('selection-mark','root:'+t['roots'][0][0],'content_presence'),('body-wrap','context','wrapping'),('content-overlap','surface','overlap'),('horizontal-fit','surface','clipping'),('type-hierarchy','surface','hierarchy')]:
        rules.append(dict(id=rid,kind='manual',target=target,property=aspect,coverage='target' if rid=='selection-mark' else 'full_content',allowed_methods=['visual']))
    if platform=='android':
        for target in ['title','context']:
            for prop in ['font_sp','font_weight','color_argb','overflow','ellipsized','lines']:
                rules.append(dict(id=target+'-'+prop,kind='text_layout',target=target,property=prop,coverage='target',**({'op':'gte'} if prop=='lines' else {})))
    return rules

QUESTIONS={
 'selection-mark':'Does the first option show a visible trailing check exactly when that option is selected in this published state, without changing its label?',
 'body-wrap':'Is every supplied context sentence visible with natural wrapping at the specified body size throughout this captured state?',
 'content-overlap':'Do the title, paragraphs, choices, summary, confirmation, status, receipt, and primary action remain clear of one another throughout the captured component?',
 'horizontal-fit':'Does all component content remain within the offered child width with no horizontal clipping?',
 'type-hierarchy':'Does the title use a clearly larger semibold system style than the normal body copy, matching the authored 24 and 15 native size intent?',
}
FULL_VISUAL={'body-wrap','content-overlap','horizontal-fit','type-hierarchy'}

def value_for(t,flow,st,r,platform):
    sid=st['id'];shot=flow['snapshots'][sid];f=shot['fixture'];s=shot['local'];values=expected(t,f,s);rid=r['id']
    if rid in values:return typed(values[rid])
    if rid in ['activation-events','replacement-events']:
        i=st.get('stimulus_action',st['after_action']);kind=flow['actions'][i]['type']
        wanted='tap' if rid=='activation-events' else 'apply_next_fixture'
        if kind!=wanted:return None
        return typed(shot['events'],'events')
    if r['kind']=='geometry':return TOKENS[platform]['minControlHeight']
    if rid=='surface-fill':return TOKENS['surface']
    if rid=='primary-fill':return TOKENS['accent' if values['submit-enabled'] else 'disabled']
    if rid=='first-option-fill':return TOKENS['selected' if s['root']==t['roots'][0][0] else 'row']
    if rid in QUESTIONS:
        if rid in FULL_VISUAL and st['coverage']!='full_content':return None
        return typed(True)
    if r['kind']=='text_layout':
        target=r['target'];prop=r['property'];long=f['title'].startswith('Extended review:')
        if prop=='font_sp':return TOKENS['android']['titleSize' if target=='title' else 'bodySize']
        if prop=='font_weight':return TOKENS['android']['weightTitle' if target=='title' else 'weightBody']
        if prop=='color_argb':return TOKENS['ink' if target=='title' else 'muted']
        if prop in ['overflow','ellipsized']:return typed(False)
        if prop=='lines':return typed((2 if target=='title' else 3) if long else 1)
    raise ValueError(rid)

def bindings(t):
    result={k:{'identifier':t['id']+'.'+k} for k in ['surface','title','context','notes','status','summary','receipt']}
    result['submit']={'label':t['submit'],'role':'button'};result['ack']={'label':t['ack'],'role':'button'}
    for category,prefix in [('roots','root'),('details','detail')]:
        for key,label in t[category]:result[prefix+':'+key]={'label':label,'role':'button'}
    return result

def bound_actions(actions,b):
    result=copy.deepcopy(actions)
    for a in result:
        if isinstance(a.get('target'),str):a['target']=copy.deepcopy(b[a['target']])
        for p in a.get('preconditions',[]):p['target']=copy.deepcopy(b[p['target']])
    return result

def write_all_inputs():
    for t in TASKS:
        public=ROOT/'public/tasks'/t['id']
        write(public/'API.md',api_doc(t));write(public/'BRIEF.md',brief(t));write(public/'DESIGN.md',DESIGN)
        write(public/'fixture.schema.json',schema(t));write(public/'tokens.json',TOKENS)
        pubflow=families(t,'public')
        for name,sid in [('blank','blank'),('ready','ready'),('long','long-retained')]:
            shot=pubflow['snapshots'][sid];write(public/('reference-'+name+'.svg'),svg(t,shot['fixture'],shot['local']))
        for family in ['public','private']:
            folder=ROOT/family/'tasks'/t['id'];flow=families(t,family)
            if family=='private':
                write(folder/'PRIVATE-INPUTS.md','# Heldout input family\n\nSame published business and styling rules as public/tasks/'+t['id']+'/BRIEF.md. Tests exact inclusive boundaries, idempotent root selection, same-pair detail invalidation, recorded long replacement, same-pair root invalidation, changed-entity zero eligibility, and published revision reset. No new rule or decision flag. Do not give these values, expected states, or this document to implementation workers.\n')
            write(folder/'flow.json',dict(scenario=family+'-flow',states=flow['states'],logical_actions=flow['actions']))
            write(folder/'outcomes.json',{k:dict(input_index=next(st['input_index'] for st in flow['states'] if st['id']==k),local=v['local'],visible=expected(t,v['fixture'],v['local']),callback_delta=v['events']) for k,v in flow['snapshots'].items()})
            for platform in ['ios','android']:
                p=folder/platform;b=bindings(t);rules=rules_for(t,platform)
                write(p/'bindings.json',b);write(p/'actions.json',bound_actions(flow['actions'],b));write(p/('ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt'),bridge(t,platform))
                config=dict(initial=flow['fixtures'][0],updates=flow['fixtures'][1:],width=390,height=600,theme='light',direction='ltr',canvas_color='#FFFFFF',max_scrolls=18,required_identifiers=[t['id']+'.title',t['id']+'.context',t['id']+'.summary',t['id']+'.receipt'])
                config.update(dynamic_type='large') if platform=='ios' else config.update(font_scale=1.0)
                write(p/'fixtures.json',config)
                environment=dict(width=390,height=600,direction='ltr',theme='light')
                environment.update(dynamic_type='large') if platform=='ios' else environment.update(font_scale=1.0,dimension_encoding='paparazzi-float32-screen-config-v1')
                write(p/'environment.json',environment)
                reference=dict(platform_scope={'intended_platform':platform,'opposite_slot':'Schema-only; forbidden for runtime compilation or admission','ios_native_typography':'N/A: public AX has no generic computed SwiftUI font/padding/color API'},tokens=TOKENS,questions={k:typed(v) for k,v in QUESTIONS.items()},states={},obligations=[],responsibilities=[])
                values={r['id']:{} for r in rules}
                denominator=[]
                for st in flow['states']:
                    sid=st['id'];reference['states'][sid]={}
                    for r in rules:
                        value=value_for(t,flow,st,r,platform)
                        if value is None:
                            reason='Different successful stimulus class or observation-only checkpoint.' if r['kind']=='event' else 'Full-component visual proposition reserved for declared full-content states; intermediate local facts remain required.'
                            values[r['id']][sid]={'not_applicable':reason}
                            denominator.append(dict(state=sid,rule_id=r['id'],platform=platform,disposition='N/A',reason=reason,kind=r['kind'],owner='component'))
                            continue
                        reference['states'][sid][r['id']]=value
                        if r['kind']=='geometry':
                            reference['states'][sid][r['id']+'-schema-opposite']=TOKENS['android' if platform=='ios' else 'ios']['minControlHeight']
                        own=expr('/states/'+sid+'/'+r['id']);other=expr('/states/'+sid+'/'+r['id']+'-schema-opposite') if r['kind']=='geometry' else own
                        values[r['id']][sid]={platform:own,('android' if platform=='ios' else 'ios'):other}
                        denominator.append(dict(state=sid,rule_id=r['id'],platform=platform,disposition='required',kind=r['kind'],owner='component',assertion_id=sid+'/'+r['id']))
                for r in rules:
                    selected=[st['id'] for st in flow['states'] if 'not_applicable' not in values[r['id']][st['id']]]
                    if selected:reference['obligations'].append(dict(id=r['id'],clause='Apply the independently published '+r['id']+' atom in each listed state.',priority='must',states=selected,risk='behavior' if r['kind']=='event' or r['id'].endswith(('-enabled','-selected')) else 'layout' if r['kind']=='geometry' else 'style' if r['kind'] in ['manual','text_layout'] else 'content'))
                for method,kind in er.NATIVE.items():
                    ids=[r['id'] for r in rules if r['kind']==kind and any('not_applicable' not in v for v in values[r['id']].values())]
                    if ids:reference['responsibilities'].append(dict(id='native-'+method,clause='Establish actual '+method+' facts for the real production component through the applicable compiled assertion IDs.',priority='must',owner='component',method=method,subject='production_component',rule_ids=ids))
                for cid,owner,subject,clause in [
                    ('production-api','component','production_api','The real production file exports the exact public immutable input and component API in API.md.'),
                    ('thin-bridge','bridge','thin_bridge','The actual bridge only decodes the typed fixture, applies the stock Android theme when applicable, and passes the same onEvent to the real production component; it owns no UI, decisions, state, identity reset, or callback rewriting.'),
                    ('production-placement','integration','production_placement','The additive component is placed in the documented production product/package and the actual bridge calls that production API, preserving stock host deployment and global theme.')]:
                    reference['responsibilities'].append(dict(id=cid,clause=clause,priority='must',owner=owner,method='source',subject=subject,rule_ids=[]))
                    denominator.append(dict(state='source-boundary',rule_id=cid,platform=platform,disposition='required-source-review',kind='source',owner=owner,actual='unassessed',placeholder_capability_only=True))
                if platform=='ios':
                    for st in flow['states']:
                        for target in ['title','context']:
                            for prop in ['font_sp','font_weight','color_argb','overflow','ellipsized','lines']:
                                denominator.append(dict(state=st['id'],rule_id=target+'-'+prop,platform=platform,disposition='N/A',kind='text_layout',owner='component',reason='Preimplementation iOS platform scope: generic SwiftUI computed TextLayout values are not exposed by public AX. Typography and wrapping have separately required Boolean visual atoms; this is not an evaluated pass.'))
                write(p/'reference.json',reference);write(p/'denominator.json',denominator)
                launch={platform:dict(scenario=family+'-flow',platform=platform,fixtures_sha256=digest(config),bridge_sha256=sha(p/('ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt')))}
                write(p/'launch.json',launch)
                contract=dict(version=1,design_owner='Independent new-business design context /root/v13_business_design2',approval_reference='business-design-cohort2-v2/AUTHOR-DECLARATION.md; pre-code Int transport-domain correction; final cohort seal after all twenty pure preflights; independent review still required',sources=[dict(id='reference',path='reference.json',sha256=sha(p/'reference.json')),dict(id='launch',path='launch.json',sha256=sha(p/'launch.json'))],required_rule_ids=[r['id'] for r in rules],rules=rules,scenarios={family+'-flow':dict(states=flow['states'],actions=flow['actions'],values=values)})
                write(p/'contract.json',contract)
                write(p/'routes.json',dict(version=1,index=dict(source='reference',pointer='/obligations'),routes={o['id']:dict(rule_ids=[o['id']],reason='Exact source-backed independently authored atom; source duties are separately retained by the responsibility contract and master denominator.',regression_obligations=[]) for o in reference['obligations']}))
                production=p/'pure-subjects/production'/((t['api']+'.swift') if platform=='ios' else (t['api']+'.kt'))
                write(production,'// PURE CAPABILITY PLACEHOLDER ONLY. No UI implementation.\n// Actual source API and behavior have not been observed or approved.\n// Required actual production path: '+('Sources/AlertToast/Business/' if platform=='ios' else 'app/src/main/java/com/example/reply/ui/components/business/')+production.name+'\n// Normative signatures: public/tasks/'+t['id']+'/API.md\n')
                write(p/'pure-subjects/integration/placement.json',dict(purpose='PURE CAPABILITY PLACEHOLDER: no actual integration source approval',required_production_path=('Sources/AlertToast/Business/' if platform=='ios' else 'app/src/main/java/com/example/reply/ui/components/business/')+production.name,product='AlertToast' if platform=='ios' else 'com.example.reply.ui.components.business',bridge_symbol='ObserverBridge.make' if platform=='ios' else 'org.nativeobserver.ObserverBridge.Content'))
    write(ROOT/'ALL-INPUTS-FIXED.json',dict(version=1,fixed_at_utc=datetime.now(timezone.utc).isoformat(),task_ids=[t['id'] for t in TASKS],family_counts={'public_states_each':11,'private_states_each':13,'public_actions_each':18,'private_actions_each':21},statement='All five business/API/fixture/action/outcome/style/denominator inputs are fixed together before any pure compilation or production implementation. These are independent authored requirements, not runtime results.'))

steps=[]
def run(label,args):
    argv=[sys.executable,'-B',*map(str,args)]
    assert '--run' not in argv
    c=subprocess.run(argv,cwd=REPO,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
    path=ROOT/'pure-receipts'/f'{len(steps):03d}-{label}.json';record=dict(label=label,argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,native_run=False,recorded_at_utc=datetime.now(timezone.utc).isoformat());write(path,record);steps.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
    if c.returncode:raise RuntimeError(label+' failed; original stdout/stderr preserved in '+str(path))
    return c.stdout

def pure_compile_all():
    profiles={};master=[];summary=[]
    for family in ['public','private']:
        for t in TASKS:
            for platform in ['ios','android']:
                p=ROOT/family/'tasks'/t['id']/platform;label=family+'-'+t['id']+'-'+platform
                run(label+'-seal',[TOOLS/'design_contract.py','seal','--contract',p/'contract.json','--root',p,'--output',p/'lock.json'])
                lock=load(p/'lock.json');locksha=digest(lock)
                run(label+'-compile',[TOOLS/'design_contract.py','compile','--lock',p/'lock.json','--lock-sha256',locksha,'--scenario',family+'-flow','--platform',platform,'--bindings',p/'bindings.json','--actions',p/'actions.json','--output',p/'generated'])
                plan=load(p/'generated/plan.json')
                atoms=[];ownership={}
                for r in lock['contract']['rules']:
                    if r['kind']!='manual':continue
                    target=r['target'];ownership[target]='component'
                    if r['allowed_methods']==['native_pixels']:
                        sampling=dict(region=[.02,.20,.035,.80] if r['id']=='surface-fill' else [.02,.25,.035,.75],minimum_pixels=12,minimum_support=.9,channel_tolerance=0,basis='semantic' if r['id']=='surface-fill' else 'control',visibility='visible_fragment' if r['id']=='surface-fill' else 'fully_visible')
                        atoms.append(dict(rule_id=r['id'],aspect='rendered_fill',method='native_pixels',sampling=sampling))
                    else:atoms.append(dict(rule_id=r['id'],aspect=r['property'],method='visual',question=expr('/questions/'+r['id'])))
                policy=dict(version=1,design_lock_sha256=locksha,approval_reference='Independent authored pixel/Boolean policy fixed before implementation; see cohort AUTHOR-DECLARATION.md',ownership=ownership,atoms=atoms)
                write(p/'policy.json',policy);policysha=digest(policy)
                run(label+'-catalog',[TOOLS/'review_contract.py','catalog','--plan',p/'generated/plan.json','--design-lock',p/'lock.json','--design-sha256',locksha,'--policy',p/'policy.json','--policy-sha256',policysha,'--platform',platform,'--output',p/'catalog.json'])
                routes=load(p/'routes.json');routessha=digest(routes)
                run(label+'-routes',[TOOLS/'requirement_routes.py','audit','--plan',p/'generated/plan.json','--design-lock',p/'lock.json','--design-sha256',locksha,'--routes',p/'routes.json','--routes-sha256',routessha,'--output',p/'route-audit.json'])
                audit=load(p/'route-audit.json');assert audit['must_route_gaps']==[] and audit['unowned_assertions']==[]
                bridgepath=p/('ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt')
                run(label+'-execution',[TOOLS/'execution_plan.py','--plan',p/'generated/plan.json','--design-lock',p/'lock.json','--design-sha256',locksha,'--fixtures',p/'fixtures.json','--bridge',bridgepath,'--launch-source','launch','--launch-pointer','/'+platform,'--output',p/'execution'])
                execution=load(p/'execution/execution.json');ep.verify_execution(execution,plan,lock,locksha,load(p/'fixtures.json'),sha(bridgepath));ag.compile_actions(execution['actions'])
                production=next((p/'pure-subjects/production').iterdir());placement=p/'pure-subjects/integration/placement.json'
                config=dict(version=1,purpose='pure_preimplementation_capability_only',platform=platform,design_lock=str(p/'lock.json'),design_sha256=locksha,plan=str(p/'generated/plan.json'),policy=str(p/'policy.json'),policy_sha256=policysha,routes=str(p/'routes.json'),routes_sha256=routessha,environment=str(p/'environment.json'),environment_sha256=digest(load(p/'environment.json')),fixtures=str(p/'fixtures.json'),bridge=str(bridgepath),launch_ref=dict(source='launch',pointer='/'+platform),responsibility_ref=dict(source='reference',pointer='/responsibilities'),source_roots=[str(production.parent)],source_review_store=str(p/'uncreated-source-review-store'),review_store=str(p/'uncreated-visual-review-store'),evidence_subjects=dict(production_api=[str(production)],thin_bridge=[str(bridgepath)],production_placement=[str(placement)]),profile_admission=dict(script=str(ROOT/'scripts/admit_profile.py'),actual_platform_required=True,opposite_slot_runtime_forbidden=True),native_options={})
                write(p/'profile.json',config)
                compiled=er.compile_contract(config,plan,lock)
                assert compiled['issues']==[],compiled['issues']
                for claim in compiled['claims']:
                    assert claim['supported']
                    if claim['method'] in er.NATIVE:
                        assert claim['assertion_ids'] and claim['rule_ids']
                        assert set(claim['rule_ids'])=={a['requirement_id'] for a in plan['assertions'] if a['id'] in claim['assertion_ids']}
                        assert all(a['kind']==er.NATIVE[claim['method']] for a in plan['assertions'] if a['id'] in claim['assertion_ids'])
                run(label+'-responsibility',[TOOLS/'evidence_responsibility.py','audit','--config',p/'profile.json','--output',p/'responsibility-capability.json'])
                paths={key:Path(config[key]).relative_to(ROOT).as_posix() for key in ['design_lock','plan','policy','routes','environment','fixtures','bridge']}
                entry=dict(task=t['id'],family=family,intended_platform=platform,paths=paths,hashes={key:sha(ROOT/path) if key=='bridge' else digest(load(ROOT/path)) for key,path in paths.items()},design_sha256=locksha,policy_sha256=policysha,routes_sha256=routessha,environment_sha256=config['environment_sha256'],launch_ref=config['launch_ref'],responsibility_ref=config['responsibility_ref'],profile_path=str((p/'profile.json').relative_to(ROOT)),scenario=family+'-flow',execution_sha256=execution['execution_sha256'],opposite_slot='schema_only_forbidden_runtime',actual_source_approval=False,native_execution=False)
                profiles[label]=entry
                den=load(p/'denominator.json');master.extend(dict(task=t['id'],family=family,**row) for row in den)
                summary.append(dict(profile=label,states=len(plan['states']),actions=execution['parent_action_count'],assertions=len(plan['assertions']),native_claims=sum(c['method'] in er.NATIVE for c in compiled['claims']),source_claims=3,responsibility_issues=[],must_route_gaps=[],scope='pure only; no observed actuals/source approvals/native run'))
    write(ROOT/'APPROVAL-MAPPING.json',dict(version=1,authored_intent_only=True,scope='Only each intended-platform projection is approved as authored intent; opposite typed slots are compiler schema-only. Independent design review remains outstanding.',profiles=profiles))
    write(ROOT/'MASTER-DENOMINATOR.json',dict(version=1,source_review_actuals='unassessed',native_actuals='not_run',cells=master,counts={key:sum(row['disposition']==key for row in master) for key in ['required','N/A','required-source-review']}))
    write(ROOT/'PURE-COMPILATION-SUMMARY.json',dict(version=1,profiles=summary,all_twenty_pure_chains_passed=len(summary)==20,pure_only=True,source_approvals=0,native_runs=0,cli_receipts=steps))

if __name__=='__main__':
    write_all_inputs()
    print(json.dumps({'phase':'all-five-inputs-fixed','tasks':len(TASKS),'production_ui_written':False}),flush=True)
    pure_compile_all()
    print(json.dumps({'phase':'twenty-pure-chains-passed','native_runs':0,'source_approvals':0}),flush=True)
