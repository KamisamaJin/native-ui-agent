#!/usr/bin/env python3
"""Independent design authoring. Does not read implementation or run native SDKs."""
from pathlib import Path
import json, hashlib, datetime, copy, html, textwrap, shutil
import fitz
ROOT=Path(__file__).resolve().parent
TOOLS=ROOT.parent/'candidate-v8'/'scripts'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists(): raise RuntimeError('Preserve original: '+str(p))
 p.write_text(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def typed(v,u): return {'value':v,'unit':u}
def expr(ptr): return {'source':'reference','pointer':ptr}
def both(ptr): return {'ios':expr(ptr),'android':expr(ptr)}
TASKS=[
 dict(id='T1',name='WorkshopSlotPlanner',model='WorkshopSlotPlannerModel',item='WorkshopSlot',list='slots',domain='Makerspace workshop station booking',structure='Responsive station/time grid',prefix='workshop',verb='reserve',on='onReserve',select='onSelect',title='Book a workshop station',subtitle='Choose one supervised station and review the safety briefing before requesting a place.',details='Safety briefing',button='Request station',summary0='No station selected',summaryPrefix='Draft station: ',multi=False,
  labels=[['09:00 · Wood bench','11:30 · Electronics bench','14:00 · Welding bay','15:00 · Textile table','16:00 · Print studio','17:30 · Quiet assembly'],['09:00 · Long-form furniture restoration bench','11:30 · Accessible electronics and precision soldering bench','14:00 · Supervised metal joining bay','15:00 · Textile restoration table','16:00 · Large-format print studio','17:30 · Quiet hand assembly'],['08:15 · Ceramic repair bench','10:45 · Optical instrument table','13:15 · Laser safety induction bay','14:45 · Pattern cutting station','16:15 · Bookbinding press','18:00 · Quiet handwork']],
  detail='Bring closed shoes. Staff will check tool training at arrival. Dust extraction runs throughout the session; tell staff about any access needs.',notice='Supervised sessions only. A request does not confirm a place.',footer='Station requests are reviewed by the duty maker. Your selected time remains a draft until staff confirm availability.'),
 dict(id='T2',name='RiverSensorTriageBoard',model='RiverSensorTriageModel',item='RiverSensorIncident',list='incidents',domain='River monitoring incident triage',structure='Chronological alert timeline with inline expanded reading dossier',prefix='river',verb='acknowledge',on='onAcknowledge',select='onSelect',title='Review river sensor alerts',subtitle='Select one incoming alert, inspect its readings, and acknowledge it for a field team.',details='Reading dossier',button='Acknowledge alert',summary0='No alert selected',summaryPrefix='Reviewing: ',multi=False,
  labels=[['06:40 · North weir level rise','06:55 · East culvert battery low','07:10 · South reach signal lost','07:25 · Mill bridge turbidity','07:40 · Reed bank temperature','07:55 · Ferry gauge drift'],['06:40 · Northern overflow weir rapid water-level rise','06:55 · Eastern culvert auxiliary battery capacity warning','07:10 · Southern conservation reach telemetry unavailable','07:25 · Mill footbridge optical turbidity advisory','07:40 · Reed restoration bank temperature advisory','07:55 · Ferry approach pressure-gauge drift'],['08:05 · Estuary gate salinity change','08:20 · Orchard drain battery warning','08:35 · West spillway maintenance hold','08:50 · Meadow ford turbidity rise','09:05 · Old quay temperature change','09:20 · Marsh inlet gauge offset']],
  detail='Latest sample: 07:18 local. Compare the three recorded readings before sending a field crew. Maintenance-held alerts remain visible for context and cannot be acknowledged.',notice='Readings are advisory. Follow the field team protocol before intervention.',footer='Acknowledgement assigns review responsibility only. The monitoring service keeps the original readings and the incident chronology.'),
 dict(id='T3',name='BicycleServiceIntake',model='BicycleServiceIntakeModel',item='BicycleServiceOption',list='services',domain='Community bicycle workshop repair intake',structure='Grouped multi-select checklist with live work estimate and expandable handover notes',prefix='bicycle',verb='submit',on='onSubmit',select='onToggle',title='Prepare a bicycle service',subtitle='Choose the work to request, review the handover notes, and send the draft to the workshop.',details='Handover notes',button='Send service draft',summary0='No work selected · 0 min',summaryPrefix='Work: ',multi=True,
  labels=[['Brake inspection','Wheel alignment','Hydraulic fork rebuild','Chain care','Gear indexing','Lighting check'],['Brake inspection for a cargo bicycle with a front carrier','Wheel alignment and spoke tension check for a touring bicycle','Hydraulic suspension fork full rebuild','Chain cleaning and weather protection','Rear gear indexing and cable review','Integrated dynamo lighting inspection'],['Rim brake inspection','Rear wheel alignment','Carbon fork structural repair','Drivetrain cleaning','Front derailleur adjustment','Battery lighting check']],
  detail='Remove loose luggage before handover. The mechanic will confirm parts and labour after inspection. Bring the key for any wheel locks and note noises that occur only under load.',notice='Estimates describe workshop time, not a fixed collection promise.',footer='Sending a service draft requests a mechanic review. No payment or repair authorisation is created by this component.')
]
COLORS={'light':{'canvas':'#FFF5F2EB','notice':'#FFE7DED0','enabled':'#FF315F68','disabled':'#FFAAA99F','ink':'#FF172D32','surface':'#FFFFFFFF','selected':'#FFD6E6E5','onAction':'#FFF8FBFA'},'dark':{'canvas':'#FF14282D','notice':'#FF2D4245','enabled':'#FF8CC7C7','disabled':'#FF52666A','ink':'#FFE6F1EF','surface':'#FF20383D','selected':'#FF31575C','onAction':'#FF102D30'}}
CASES={'P1':dict(width=390,theme='light',dynamic_type='large',fontScale=1.0,direction='ltr',data=0),'P2':dict(width=248,theme='dark',dynamic_type='accessibility2',fontScale=1.45,direction='ltr',data=1),'H1':dict(width=312,theme='dark',dynamic_type='xxLarge',fontScale=1.2,direction='rtl',data=2)}
def input_model(t,c,rev):
 labels=t['labels'][c['data']]; items=[]
 for i,label in enumerate(labels):
  x=dict(id=chr(97+i),label=label,detail=[t['detail'],'Staff-assisted access is available on request.'][i%2],available=i!=2 and not(rev==1 and i==0 and not t['multi']))
  if t['id']=='T2': x['severity']=['watch','service','hold','watch','info','info'][i]
  if t['multi']:x['minutes']=[20,35,90,15,25,10][i]+(5 if c['data']==2 else 0)
  x['unavailableReason']=({'T1':'Training supervisor is unavailable for this station.','T2':'Sensor is on a maintenance hold; field acknowledgement is paused.','T3':'This specialist repair is not offered at the community workshop.'}[t['id']] if i==2 else ('Availability changed: the duty supervisor paused new requests.' if not x['available'] else ''))
  items.append(x)
 d=dict(revision=f'{t["prefix"]}-{rev}',title=t['title'],subtitle=t['subtitle'],notice=t['notice'] if rev==0 else 'Caller update: '+t['notice'],footer=t['footer'],initialDetailsExpanded=False)
 d['guidance']=t['detail']
 d[t['list']]=items
 d['initialSelectedIDs' if t['multi'] else 'initialSelectedID']=['b'] if rev and t['multi'] else ([] if t['multi'] else None)
 return d

def route(t):
 a=[dict(type='sweep',state_id='baseline',max_steps=24),dict(type='tap',target='choiceA',reveal=True,state_id='selected')]
 if t['multi']:a.append(dict(type='tap',target='choiceB',reveal=True))
 expand_i=len(a);a.append(dict(type='tap',target='disclosure',reveal=True))
 exp_s=len(a);a.append(dict(type='sweep',state_id='expanded',max_steps=24))
 block_i=len(a);a.append(dict(type='tap',target='locked',reveal=True,allow_disabled=True,state_id='blocked'))
 replace_i=len(a);a.append(dict(type='apply_next_fixture',state_id='replaced'))
 reselect_i=len(a);a.append(dict(type='tap',target='choiceA' if t['multi'] else 'choiceB',reveal=True,state_id='reselected'))
 submit_i=len(a);a.append(dict(type='tap',target='submit',reveal=True))
 end_i=len(a);a.append(dict(type='sweep',state_id='submitted',max_steps=24))
 s=[dict(id='baseline',input_index=0,after_action=0,coverage='full_content'),dict(id='selected',input_index=0,after_action=1,coverage='targets'),dict(id='expanded',input_index=0,after_action=exp_s,stimulus_action=expand_i,coverage='full_content'),dict(id='blocked',input_index=0,after_action=block_i,coverage='targets'),dict(id='replaced',input_index=1,after_action=replace_i,coverage='targets'),dict(id='reselected',input_index=1,after_action=reselect_i,coverage='targets'),dict(id='submitted',input_index=1,after_action=end_i,stimulus_action=submit_i,coverage='full_content')]
 return a,s

def rules():
 return [dict(id='current-summary',kind='control',target='summary',property='label',coverage='target'),dict(id='first-choice-selected',kind='control',target='choiceA',property='selected',coverage='target'),dict(id='locked-choice-disabled',kind='control',target='locked',property='enabled',coverage='target'),dict(id='primary-action-enabled',kind='control',target='submit',property='enabled',coverage='target'),dict(id='disclosure-current-label',kind='control',target='disclosure',property='label',coverage='target'),dict(id='successful-activation-callback',kind='event',coverage='target'),dict(id='replacement-callback-quiet',kind='event',stimulus='caller_update',coverage='target'),dict(id='primary-control-height',kind='geometry',target='submit',property='height',op='gte',basis='control',measurement='accessibility_box',coverage='target'),dict(id='title-native-weight',kind='text_layout',target='title',property='font_weight',coverage='target'),dict(id='component-canvas-color',kind='manual',target='canvas',property='rendered_canvas_argb',allowed_methods=['native_pixels'],coverage='target'),dict(id='notice-surface-color',kind='manual',target='notice',property='rendered_fill_argb',allowed_methods=['native_pixels'],coverage='target'),dict(id='primary-surface-color',kind='manual',target='submit',property='rendered_fill_argb',allowed_methods=['native_pixels'],coverage='target'),dict(id='content-wrapping',kind='manual',target='canvas',property='wrapping',allowed_methods=['visual'],coverage='full_content'),dict(id='content-overlap',kind='manual',target='canvas',property='overlap',allowed_methods=['visual'],coverage='full_content')]

def summaries(t,m0,m1):
 def summary(m,ids):
  if not ids:return t['summary0']
  li=m[t['list']]; items=[x for x in li if x['id'] in ids]
  if t['multi']:return 'Work: '+' + '.join(x['label'] for x in items)+' · '+str(sum(x['minutes'] for x in items))+' min'
  return t['summaryPrefix']+items[0]['label']
 sels={'baseline':[],'selected':['a'],'expanded':['a','b'] if t['multi'] else ['a'],'blocked':['a','b'] if t['multi'] else ['a'],'replaced':['b'] if t['multi'] else [],'reselected':['a','b'] if t['multi'] else ['b'],'submitted':['a','b'] if t['multi'] else ['b']}
 return {s:summary(m1 if s in ['replaced','reselected','submitted'] else m0,ids) for s,ids in sels.items()}

def reference(t,case_ids):
 r={'identity':t['domain'],'geometry':{'ios':{'primaryMinHeight':typed(56,'pt')},'android':{'primaryMinHeight':typed(56,'dp')}},'typography':{'titleWeight':typed(600,'scalar')},'booleans':{'yes':typed(True,'bool'),'no':typed(False,'bool')},'questions':{'wrapping':typed('Considering only text required to be visible by this exact state's current selection and disclosure rules, are all visible title, subtitle, notice, choice labels, visible item details/reasons, visible disclosure content, summary, action label and footer words readable in natural wrapped lines without truncation or ellipsis? Deliberately collapsed guidance and unselected incident dossiers are excluded. If required text is missing, answer unknown and identify it; missing text cannot count as correct wrapping. Visible word clipping or ellipsis answers false. Evaluate wrapping only; spacing collisions have their own atom. A true answer still requires complete exact-state coverage.','string'),'overlap':typed('Across every captured part of this exact state, do text, choice indicators, status badges, disclosure content and primary action occupy separate areas without unintended overlap or occlusion? Evaluate overlap only; line breaking has its own atom.','string')},'visual':{'wrapping':typed(True,'bool'),'overlap':typed(True,'bool')},'cases':{}}
 for cid in case_ids:
  c=CASES[cid];m0=input_model(t,c,0);m1=input_model(t,c,1);sums=summaries(t,m0,m1)
  r['cases'][cid]={'colors':{k:typed(v,'argb') for k,v in COLORS[c['theme']].items()},'states':{}}
  for s,summary in sums.items():
   changed=s in ['replaced','reselected','submitted'];expanded=s in ['expanded','blocked']
   selectedA=s in ['selected','expanded','blocked'] or t['multi'] and s in ['reselected','submitted']
   enabled=s!='baseline' and (s!='replaced' or t['multi'])
   evt=[f'{t["prefix"]}:select:a'] if s=='selected' else ([f'{t["prefix"]}:details:open'] if s=='expanded' else ([f'{t["prefix"]}:toggle:a:true' if t['multi'] else f'{t["prefix"]}:select:b'] if s=='reselected' else [f'{t["prefix"]}:{t["verb"]}:a,b' if t['multi'] else f'{t["prefix"]}:{t["verb"]}:b']))
   if t['multi'] and s=='selected':evt=[f'{t["prefix"]}:toggle:a:true']
   if s in ['baseline','blocked','replaced']:evt=[]
   r['cases'][cid]['states'][s]={'summary':typed(summary,'string'),'selectedA':typed(bool(selectedA),'bool'),'submitEnabled':typed(enabled,'bool'),'disclosure':typed(('Hide ' if expanded else 'Show ')+t['details'].lower(),'string'),'activationEvents':typed(evt,'events'),'updateEvents':typed([],'events'),'primaryColor':typed(COLORS[c['theme']]['enabled' if enabled else 'disabled'],'argb')}
 return r

def contract(t,case_ids,ref_path):
 rr=rules();scenarios={};a,states=route(t)
 for cid in case_ids:
  vals={}
  for rule in rr:
   rid=rule['id'];vals[rid]={}
   for s in states:
    sid=s['id'];b=f'/cases/{cid}/states/{sid}';ptr={'current-summary':b+'/summary','first-choice-selected':b+'/selectedA','locked-choice-disabled':'/booleans/no','primary-action-enabled':b+'/submitEnabled','disclosure-current-label':b+'/disclosure','successful-activation-callback':b+'/activationEvents','replacement-callback-quiet':b+'/updateEvents','title-native-weight':'/typography/titleWeight','component-canvas-color':f'/cases/{cid}/colors/canvas','notice-surface-color':f'/cases/{cid}/colors/notice','primary-surface-color':b+'/primaryColor','content-wrapping':'/visual/wrapping','content-overlap':'/visual/overlap'}.get(rid)
    if rid=='successful-activation-callback' and sid not in ['selected','expanded','reselected','submitted']:cell={'not_applicable':'This checkpoint has no successful native activation stimulus. Disabled observation is never a callback success.'}
    elif rid=='replacement-callback-quiet' and sid!='replaced':cell={'not_applicable':'Only the explicit caller replacement advances the model input and owns this quietness requirement.'}
    elif rid in ['content-wrapping','content-overlap'] and sid not in ['baseline','expanded','submitted']:cell={'not_applicable':'Selected scope here is target observation; full-page visual requirements remain in the brief but are selected only at the baseline, expanded and submitted full-content sweeps.'}
    elif rid=='primary-control-height':cell={p:expr(f'/geometry/{p}/primaryMinHeight') for p in ['ios','android']}
    else:cell=both(ptr)
    vals[rid][sid]=cell
  scenarios[cid]={'states':copy.deepcopy(states),'actions':copy.deepcopy(a),'values':vals}
 return {'version':1,'design_owner':'Independent blind task designer, cohort design-v2','approval_reference':'approval.json; preimplementation source identity approval, pending fresh design review','sources':[{'id':'reference','path':'reference.json','sha256':sha(ref_path)}],'required_rule_ids':[x['id'] for x in rr],'rules':rr,'scenarios':scenarios}

def bindings(t):
 return {k:{'identifier':t['prefix']+'.'+v} for k,v in {'canvas':'canvas','title':'title','summary':'summary','choiceA':'choice.a','choiceB':'choice.b','locked':'choice.c','submit':'submit','disclosure':'disclosure','notice':'notice'}.items()}

def policy(lock_sha):
 sample=lambda reg,vis='fully_visible':dict(region=reg,minimum_pixels=24,minimum_support=0.95,channel_tolerance=0,basis='semantic',visibility=vis)
 return dict(version=1,design_lock_sha256=lock_sha,approval_reference='approval.json; independently fixed role gutters, not glyph boxes',ownership={k:'component' for k in ['canvas','notice','submit']},atoms=[dict(rule_id='component-canvas-color',aspect='rendered_canvas',method='native_pixels',sampling=sample([.02,.05,.03,.95],'visible_fragment')),dict(rule_id='notice-surface-color',aspect='rendered_fill',method='native_pixels',sampling=sample([.025,.2,.045,.8])),dict(rule_id='primary-surface-color',aspect='rendered_fill',method='native_pixels',sampling=sample([.025,.2,.045,.8])),dict(rule_id='content-wrapping',aspect='wrapping',method='visual',question=expr('/questions/wrapping')),dict(rule_id='content-overlap',aspect='overlap',method='visual',question=expr('/questions/overlap'))])

def bridges(t):
 # Public model decoding only; all interaction and state belong to the real component.
 closures=(f'onToggle: {{ id, selected in onEvent("{t["prefix"]}:toggle:\\(id):\\(selected ? "true" : "false")") }},' if t['multi'] else f'onSelect: {{ id in onEvent("{t["prefix"]}:select:\\(id)") }},')
 final=(f'onSubmit: {{ ids in onEvent("{t["prefix"]}:submit:\\(ids.sorted().joined(separator: ","))") }}' if t['multi'] else f'{t["on"]}: {{ id in onEvent("{t["prefix"]}:{t["verb"]}:\\(id)") }}')
 sw=f'''import SwiftUI
import AlertToast

// Adapter only: no local business state, styling, semantic IDs, or replacement UI.
enum ObserverBridge {{
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {{
        do {{
            let data = try JSONSerialization.data(withJSONObject: fixture)
            let model = try JSONDecoder().decode({t['model']}.self, from: data)
            return AnyView({t['name']}(model: model,
                {closures}
                onDetailsChange: {{ expanded in onEvent("{t['prefix']}:details:\\(expanded ? "open" : "closed")") }},
                {final}))
        }} catch {{ fatalError("Invalid approved fixture: \\(error)") }}
    }}
}}
'''
 itemargs='id = s("id"), label = s("label"), detail = s("detail"), unavailableReason = s("unavailableReason"), available = this["available"]!!.jsonPrimitive.boolean'
 if t['id']=='T2': itemargs+=', severity = s("severity")'
 if t['multi']:itemargs+=', minutes = this["minutes"]!!.jsonPrimitive.int'
 selectargs='initialSelectedIDs = input["initialSelectedIDs"]!!.jsonArray.map { it.jsonPrimitive.content }' if t['multi'] else 'initialSelectedID = input["initialSelectedID"]?.jsonPrimitive?.contentOrNull'
 kselect=f'onToggle = {{ id, selected -> onEvent("{t["prefix"]}:toggle:$id:$selected") }},' if t['multi'] else f'onSelect = {{ id -> onEvent("{t["prefix"]}:select:$id") }},'
 kfinal=f'onSubmit = {{ ids -> onEvent("{t["prefix"]}:submit:${{ids.sorted().joinToString(",")}}") }}' if t['multi'] else f'{t["on"]} = {{ id -> onEvent("{t["prefix"]}:{t["verb"]}:$id") }}'
 kt=f'''package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.{t['name']}
import com.example.reply.ui.components.{t['model']}
import com.example.reply.ui.components.{t['item']}
import kotlinx.serialization.json.*

// Adapter only. The production component owns all state and semantics.
object ObserverBridge {{
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {{
        fun JsonObject.s(key: String): String = this[key]!!.jsonPrimitive.content
        val model = {t['model']}(
            revision = input.s("revision"), title = input.s("title"), subtitle = input.s("subtitle"),
            notice = input.s("notice"), footer = input.s("footer"), guidance = input.s("guidance"),
            initialDetailsExpanded = input["initialDetailsExpanded"]!!.jsonPrimitive.boolean,
            {selectargs},
            {t['list']} = input["{t['list']}"]!!.jsonArray.map {{ item ->
                with(item.jsonObject) {{ {t['item']}({itemargs}) }}
            }})
        {t['name']}(model = model,
            {kselect}
            onDetailsChange = {{ expanded -> onEvent("{t['prefix']}:details:${{if (expanded) "open" else "closed"}}") }},
            {kfinal})
    }}
}}
'''
 return sw,kt

def docs(t):
 checklist='Multiple available services can be selected independently. Tapping again deselects that service. The estimate is the sum of selected minutes, and summary order always follows the service list.' if t['multi'] else 'Exactly one available item can be selected. Tapping the current selection is idempotent and emits its selection callback once; it does not clear the selection.'
 reset='replace the selected ID set with valid available incoming initialSelectedIDs' if t['multi'] else 'replace selection with the valid available incoming initialSelectedID, or clear it when null/unavailable'
 structure={'T1':'Place six station slots in a two-column eager grid when child width is at least320 native units and text size is at most iOS DynamicTypeSize.large or Android fontScale<=1.0, respectively. At smaller width or enlarged text, use one column. Each slot shows its time/station label above its detail. Header, notice, grid, summary, disclosure, expanded safety briefing, action and footer form one vertical reading order. No horizontal scrolling.','T2':'Use one eager vertical timeline with six chronological incident cards, not a tile grid. Only the non-interactive leading rail sits outside each select button. The time-bearing item label and uppercase severity are both inside the single colored selection button, matching the reference; there is no separate external time/severity marker. The selected incident has an inline dossier immediately below its card when disclosure is expanded. The global disclosure appears above the timeline; summary, primary action and footer follow it. Each card shows its severity text. The selected incident detail appears only in the expanded inline dossier, so closed rows stay compact. RTL mirrors leading rail placement.','T3':'Use an eager multi-select checklist grouped as Inspection (a,b), Specialist work (c), and Care and adjustments (d,e,f). A check indicator is a visual child of each single native select button, not a nested second action. The live estimate is a separate full-width summary panel below the checklist. The handover disclosure and its expanded notes follow the estimate, then action and footer. All groups stack vertically.'}[t['id']]
 brief=f'''# {t['name']} — new native component requirement

Domain: {t['domain']}. Interaction structure: {t['structure']}.
This is an independent new design fixed before any implementation. Implement SwiftUI in alerttoast/Sources/AlertToast/{t['name']}.swift and Compose in reply/Reply/app/src/main/java/com/example/reply/ui/components/{t['name']}.kt. Keep pinned upstream source/build settings. Do not copy a reference drawing into a replacement view.

## Product behaviour

{structure}

{checklist} Unavailable entries remain visible with the literal status “Unavailable”, their nonempty caller-supplied unavailableReason, and a real disabled control. available=true requires unavailableReason=""; available=false requires a nonempty reason. The component displays that reason verbatim below the item label (and severity on T2), never invents a reason and never substitutes ordinary detail for it. Entry c is unavailable in all public examples. The model can disable any entry at replacement. A disabled interaction does not invoke a handler. The primary action is enabled exactly when there is at least one available selected item. It sends the current selected ID (or ordered-independent set) without clearing the draft. The component never confirms a reservation, field intervention or repair itself.

The disclosure is a real native button. Its visible/native label is exactly “Show {t['details'].lower()}” when closed and “Hide {t['details'].lower()}” when open. It toggles the detail block and emits one Boolean callback. Selecting a new incident while open moves the dossier to that incident (T2); the other components retain their global detail block. T1 and T3 global disclosure content is exactly model.guidance. T2 opening with no selection shows model.guidance in a full-width block immediately below the disclosure; with a selection it instead shows only that incident's detail inline below its selected card. Collapsed content and unselected incident details are intentionally hidden. Each item label, item detail, notice, subtitle and footer must remain fully readable.

The caller replaces the model in the same live component. A changed revision is authoritative: {reset}, replace all labels/availability/details, reset disclosure to initialDetailsExpanded, recompute summary and enablement, and emit no business callback. Recomposition with the same revision must preserve user state. No network, clock, random value, animation, keyboard, permission dialog or navigation is required.

## Layout and visual ownership

The component owns its full canvas, notice panel, selection treatment, action fill, typography and all internal layout. The outer host owns its background, 16-unit horizontal inset, 24-unit top inset and 600-unit scrolling viewport. The offered width is 248 or 390 units in public cases; component child width is offered width minus 32. These are native pt on iOS and requested dp on Android, subject to the pinned Paparazzi screen encoding. Do not paint the outer host to satisfy the canvas atom.

Use the palette in reference.json for the active host theme. Solid opaque colors; no gradients/shadows over measured surfaces. Canvas fills the actual component width and full content height, rounded radius12. Keep a continuous empty canvas gutter at least12 units on both sides; children never cross it. Notice and primary buttons have corner radius10 and at least16-unit internal horizontal padding. Their normalized side sampling strips (policy.json) must be solid fill, clear of glyphs/icons/borders. This is ordinary breathing room around actual content, not hidden test patches. The full canvas keeps a semantic container with its own box; never use a text leaf as the canvas.

Internal vertical spacing is12 units; section transitions20; card inset16; card gap12; title22 base native units, semibold600; body16 regular400; supporting text14. Use palette ink for text on canvas/cards/notice, and onAction for primary action text. iOS fonts scale with Dynamic Type; Compose uses sp/host fontScale. No fixed text height, line limit, ellipsis or clipping. Wrap naturally at spaces and hyphens; if one unbroken segment exceeds the available text width, break between characters while preserving every character. Grow the surrounding block for every added line. Primary control native semantic/activation box height is at least56pt/dp and grows for wrapped content. Interactive cards also have at least56-unit height. Leading/trailing placement follows native layout direction. Match layout hierarchy and specified spacing intentions in the independently drawn SVG/PNG; vector font metrics are not a native pixel baseline.

References show the expanded state as a complete scroll strip, including content beyond the600-unit host. Public P1 is ordinary light; P2 is narrow, dark, enlarged text. Support both LTR and RTL, other valid incoming data, arbitrary item label lengths, all item availability combinations and incoming valid selections under these same rules. Full-page content is eager, without an internal ScrollView/LazyColumn. The host supplies scrolling. Do not shrink content to fit600.

## Selected ledger and limits

Fourteen independent rules, seven selected states per case. The contract fixes the exact original route and all98 cells/platform/case. Baseline, expanded and submitted are full-content sweeps. Other states observe selected targets. Wrapping and overlap are separate source-backed Boolean questions selected only for full sweeps; their target-only state cells are explicitly N/A for selected-scope reasons. Full-brief behaviour still applies there. Incomplete/fragmented native coverage stays U: a footer or bottom sentinel alone never proves the entire component. Missing or ambiguous boxes, unsuitable color support and unavailable mappings stay U.

Callbacks apply only after demonstrated successful native activation, or after the explicitly advancing caller replacement. Blocked disabled observations are not successful callback stimuli. The locked-disabled rule independently assesses enablement. Selected values/summary/enablement are current business facts, not callback proxies.

The ledger deliberately does not numerically certify every spacing, card dimension, body font size/ink, group heading, secondary choice callback, deselection path, idempotent reselect, every intermediate state, accessibility pronunciation/order, physical touch hit area, parent app navigation/lifecycle or arbitrary data not in P1/P2. Also outside this selected ledger are T1 grid column count/breakpoint; T2 rail/severity/dossier placement and moving an open dossier on selection; T3 grouping and deselecting one item while preserving others; selected-background treatment, every unsampled canvas region and remaining typography hierarchy. Wrapping/overlap atoms cannot certify these features. Those remain full brief requirements outside this selected denominator. Title weight is native style on Android; generic computed SwiftUI weight is unavailable, so the iOS title-native-weight cells are selected U, never a visual substitute. Geometry is native accessibility/control box only; no claim of framework padding or glyph geometry.

See API.md for exact public production signatures and semantic IDs, cases/* for original caller fixtures/actions, policy.json for color/proposition method/ownership, and approval.json for canonical lock/policy/environment digests. compiled/* are evaluator artifacts: builders generate original plans from public requirements and cannot consume compiled acceptance plans as their implementation answer. Schema compilation is not design-quality approval; a fresh independent design review is still required.
'''
 multi_field='initialSelectedIDs: [String]' if t['multi'] else 'initialSelectedID: String?'
 kfield='initialSelectedIDs: List<String>' if t['multi'] else 'initialSelectedID: String?'
 cb='onToggle: (String, Bool) -> Void; onSubmit: ([String]) -> Void' if t['multi'] else f'onSelect: (String) -> Void; {t["on"]}: (String) -> Void'
 kcb='onToggle: (String, Boolean) -> Unit, onSubmit: (List<String>) -> Unit' if t['multi'] else f'onSelect: (String) -> Unit, {t["on"]}: (String) -> Unit'
 itemextra='; severity: String' if t['id']=='T2' else ('; minutes: Int' if t['multi'] else '')
 api=f'''# Public production API — {t['name']}

Swift module `AlertToast`: public `struct {t['item']}: Codable, Identifiable` with `id: String`, `label: String`, `detail: String`, `available: Bool`, `unavailableReason: String`{itemextra}. Public `struct {t['model']}: Codable` contains `revision: String`, `title: String`, `subtitle: String`, `notice: String`, `footer: String`, `guidance: String`, `{multi_field}`, `initialDetailsExpanded: Bool`, `{t['list']}: [{t['item']}]`. unavailableReason is a nonoptional String: empty iff available, otherwise the exact visible caller-supplied reason. Model guidance is the exact global/no-selection disclosure body; selected T2 dossier uses the selected item detail. T2 label includes its time; uppercase severity is inside the same selection button, only its rail is external. Synthesized Codable keys exactly match fixtures (camelCase); nullable selection is JSON null. Provide public memberwise initializers and public Codable decoding. Public `struct {t['name']}: View` has `init(model: {t['model']}, {cb.split('; ')[0]}, onDetailsChange: (Bool) -> Void, {cb.split('; ')[1]})`; closure parameters escaping. Initializer parameter order used by Bridge.swift is authoritative: selection callback, onDetailsChange, submission callback.

Kotlin package `com.example.reply.ui.components`: public `data class {t['item']}(id: String, label: String, detail: String, available: Boolean, unavailableReason: String{itemextra.replace(';', ',')})`. Public `data class {t['model']}(revision: String, title: String, subtitle: String, notice: String, footer: String, guidance: String, {kfield}, initialDetailsExpanded: Boolean, {t['list']}: List<{t['item']}>)`. Public `@Composable fun {t['name']}(model: {t['model']}, {kcb}, onDetailsChange: (Boolean) -> Unit)`. All parameters are named by ObserverBridge.kt. Types in Kotlin use Boolean, not Swift Bool. The component reads Material/native theme or system light/dark environment and native direction/font scale; the bridge adds no alternate visual theme.

The real component owns transient state keyed by model.revision, callback dispatch, disabled semantics, and all semantic IDs. Bridges only decode approved inputs, invoke this API and map callbacks into event strings. No bridge state/reducer or reconstructed tested view is allowed. IDs below belong on actual production controls/text/container. Use a containing semantics group for canvas without merging away descendants. Use selected semantics on each single native choice control, and native disabled semantics on unavailable controls. A visual-only checkmark cannot substitute for selected semantics. No independently actionable nested indicator inside a choice.

| Logical target | Exact semantic ID | Role / meaning |
|---|---|---|
| canvas | {t['prefix']}.canvas | Component-owned container spanning all content; children retained |
| title | {t['prefix']}.title | Actual heading text, native weight600 |
| notice | {t['prefix']}.notice | Actual padded notice panel; label is notice text |
| choiceA/choiceB/locked | {t['prefix']}.choice.a / .b / .c | Actual selection buttons; c disabled |
| all entries | {t['prefix']}.choice.<id> | Same rule for d,e,f and any incoming ID |
| summary | {t['prefix']}.summary | Actual summary text; exact native label below |
| disclosure | {t['prefix']}.disclosure | Actual detail toggle button |
| submit | {t['prefix']}.submit | Actual primary button incl native activation box |
| footer | {t['prefix']}.footer | Actual final body copy |

Summary is `{t['summary0']}` with no valid selection. {'With selection it is `Work: <labels joined by + in model order> · <sum minutes> min`; the join has one space around +.' if t['multi'] else 'With selection it is `'+t['summaryPrefix']+'<selected label>`.'} Prefixes/punctuation/spacing are exact. Action visible label is `{t['button']}`. Never change the summary after submission alone. A new revision resets disclosure and selection even when the view instance survives.

Callback event map (exact lowercase IDs): {t['prefix']}:details:open|closed; {t['prefix']}:{'toggle:<id>:true|false' if t['multi'] else 'select:<id>'}; {t['prefix']}:{t['verb']}:{'sorted comma-joined IDs' if t['multi'] else '<id>'}. Submission forwards the current selected IDs; bridge sorts set IDs only to normalize event order. Exactly one callback for each successful action. No callback on mere recomposition or model replacement. Do not emit fixture-update acknowledgements as business callbacks.

Host/component boundary: canvas and internal surfaces/semantic bounds are component responsibility. Outer600-unit viewport, padding, screen conversion, host controls and surrounding background are observer responsibility. There is no fixed internal component height. SwiftUI import is `import AlertToast`; Kotlin bridge package is `org.nativeobserver` and imports only the newly specified production types from `com.example.reply.ui.components`.
'''
 return brief,api

# Independent SVG drawing and render, no candidate screenshot/code involved.
def draw(t,cid,folder,r):
 c=CASES[cid];m=input_model(t,c,0);cols=COLORS[c['theme']];w=c['width']-32;scale=1 if cid=='P1' else (1.42 if cid=='P2' else 1.18);fs=16*scale
 rgb=lambda k:cols[k][3:]
 fonts={False:fitz.Font('helv'),True:fitz.Font('hebo')};elements=[];audit=[]
 def wrap(value,width,size,weight=400):
  font=fonts[weight>=600];limit=width-2;lines=[]
  for para in value.split('\n'):
   line=''
   for word in para.split():
    if line and font.text_length(line+' '+word,fontsize=size)<=limit:line+=' '+word;continue
    if line:lines.append(line);line=''
    # Prefer wrapping a hyphenated word at its existing hyphens, then characters.
    segments=[];part=''
    for char in word:
     part+=char
     if char=='-':segments.append(part);part=''
    if part:segments.append(part)
    for seg in segments:
     if font.text_length(line+seg,fontsize=size)<=limit:line+=seg;continue
     if line:lines.append(line);line=''
     for char in seg:
      if line and font.text_length(line+char,fontsize=size)>limit:lines.append(line);line=''
      line+=char
   lines.append(line)
  return lines
 def h(s,width,size,weight=400):return len(wrap(s,width,size,weight))*size*1.3
 def rect(x,y,ww,hh,color):elements.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" rx="10" fill="#{rgb(color)}"/>')
 def txt(value,x,y,ww,size=None,weight=400,ink='ink'):
  size=size or fs;lines=wrap(value,ww,size,weight)
  for j,line in enumerate(lines):
   tw=fonts[weight>=600].text_length(line,fontsize=size);right=c['direction']=='rtl';xx=x+ww if right else x;anchor='end' if right else 'start'
   elements.append(f'<text x="{xx:.3f}" y="{y+size+j*size*1.3:.3f}" font-size="{size:.3f}" font-family="Arial, sans-serif" font-weight="{weight}" fill="#{rgb(ink)}" text-anchor="{anchor}">{html.escape(line)}</text>')
   audit.append(dict(text=line,x_min=xx-tw if right else xx,x_max=xx if right else xx+tw,y_top=y+j*size*1.3,y_bottom=y+(j+1)*size*1.3,available_width=ww))
  return len(lines)*size*1.3
 y=16;y+=txt(m['title'],16,y,w-32,22*scale,600)+12;y+=txt(m['subtitle'],16,y,w-32)+12
 nh=h(m['notice'],w-64,fs)+32;rect(16,y,w-32,nh,'notice');txt(m['notice'],32,y+16,w-64);y+=nh+20
 if t['id']=='T2':y+=txt('Hide '+t['details'].lower(),16,y,w-32,fs,600)+16
 grid=t['id']=='T1' and cid=='P1';cw=(w-44)/2 if grid else w-32
 def label(item):return ('☑ ' if t['multi'] and item['id'] in ['a','b'] else '☐ ' if t['multi'] else '')+item['label']+(' · Unavailable' if not item['available'] else '')
 def card_h(item,ww):
  z=32+h(label(item),ww-40,fs,600)+10
  if t['id']=='T2':z+=h(item['severity'].upper(),ww-40,12*scale,600)+6
  if item['unavailableReason']:z+=h(item['unavailableReason'],ww-40,14*scale)+10
  if t['id']!='T2':z+=h(item['detail'],ww-40,14*scale)
  return max(80,z)
 gy=y
 for i,item in enumerate(m[t['list']]):
  if t['multi'] and i in [0,2,3]:y+=txt({0:'Inspection',2:'Specialist work',3:'Care and adjustments'}[i],16,y,w-32,fs,600)+10
  xx=16+(i%2)*(cw+12) if grid else (28 if t['id']=='T2' and c['direction']=='ltr' else 16);ww=cw if t['id']!='T2' else w-44;yy=gy if grid else y
  hh=max(card_h(z,ww) for z in m[t['list']][i//2*2:i//2*2+2]) if grid else card_h(item,ww)
  rect(xx,yy,ww,hh,'selected' if i in ([0,1] if t['multi'] else [0]) else 'surface');ty=yy+16;ty+=txt(label(item),xx+20,ty,ww-40,fs,600)+10
  if t['id']=='T2':ty+=txt(item['severity'].upper(),xx+20,ty,ww-40,12*scale,600)+6
  if item['unavailableReason']:ty+=txt(item['unavailableReason'],xx+20,ty,ww-40,14*scale)+10
  if t['id']!='T2':txt(item['detail'],xx+20,ty,ww-40,14*scale)
  if t['id']=='T2':
   rail=21 if c['direction']=='ltr' else w-21;elements.append(f'<path d="M {rail} {yy} V {yy+hh+12}" stroke="#{rgb("enabled")}" stroke-width="2"/>')
  if grid:
   if i%2==1:gy+=hh+12;y=gy
  else:y+=hh+12
  if t['id']=='T2' and i==0:y+=txt(item['detail'],40,y+12,w-68)+28
 y+=8;y+=txt(r['cases'][cid]['states']['expanded']['summary']['value'],16,y,w-32,fs,600)+20
 if t['id']!='T2':y+=txt('Hide '+t['details'].lower(),16,y,w-32,fs,600)+12;y+=txt(m['guidance'],16,y,w-32)+20
 bh=max(56,h(t['button'],w-68,fs,600)+32);rect(16,y,w-32,bh,'enabled');txt(t['button'],34,y+16,w-68,fs,600,'onAction');y+=bh+20;y+=txt(m['footer'],16,y,w-32,14*scale)+16
 assert all(z['x_min']>=12 and z['x_max']<=w-12 for z in audit),audit
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{int(y)+1}" viewBox="0 0 {w} {int(y)+1}"><rect width="{w}" height="{int(y)+1}" rx="12" fill="#{rgb("canvas")}"/>'+''.join(elements)+'</svg>'
 path=folder/f'reference-{cid}-expanded.svg';write(path,svg);doc=fitz.open(stream=svg.encode(),filetype='svg');pdf=fitz.open('pdf',doc.convert_to_pdf());pdf[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(str(folder/f'reference-{cid}-expanded.png'))
 write(folder/f'reference-{cid}-expanded.meta.json',{'case':cid,'state':'expanded','input_index':0,'source':'Independent SVG authoring, revised from v1 design review; no implementation','width_native':w,'content_height_design':int(y)+1,'host_viewport_height':600,'scope':'Structural reference, not native font pixel baseline','svg_sha256':sha(path),'png_sha256':sha(folder/f'reference-{cid}-expanded.png')})
 write(folder/f'reference-{cid}-text-fit-audit.json',{'metrics':'MuPDF Helvetica/Helvetica-Bold mapped from SVG Arial; conservative2-unit width reserve; literal hyphens retained and overly long segments broken between characters','empty_canvas_gutter':12,'all_text_inside_canvas_gutter':True,'lines':audit})

def generate():
 for t in TASKS:
  start='2026-10-22T01:37:31Z';root=ROOT/t['id'];pub=root/'public';priv=root/'private';pub.mkdir(parents=True);priv.mkdir()
  for folder,ids in [(pub,['P1','P2']),(priv,['H1'])]:
   r=reference(t,ids);write(folder/'reference.json',r);co=contract(t,ids,folder/'reference.json');write(folder/'contract.json',co);b=bindings(t);write(folder/'bindings.json',b)
   for cid in ids:
    c=CASES[cid];m0=input_model(t,c,0);m1=input_model(t,c,1);f={'initial':m0,'updates':[m1],'width':c['width'],'viewportHeight':600,'theme':c['theme'],'dynamic_type':c['dynamic_type'],'fontScale':c['fontScale'],'direction':c['direction'],'state_capture':True,'required_identifiers':[t['prefix']+'.choice.f',t['prefix']+'.footer'],'max_scrolls':24,'canvas_color':'#B8B7B4'}
    case=folder/'cases'/cid;write(case/'fixtures.json',f)
    aa,ss=route(t);bound=copy.deepcopy(aa)
    for a in bound:
     if isinstance(a.get('target'),str):a['target']=b[a['target']]
    for platform in ['ios','android']:
     write(case/f'actions.{platform}.json',bound)
     env={'width':c['width'],'height':600,'direction':c['direction'],'theme':c['theme']}
     if platform=='ios':env['dynamic_type']=c['dynamic_type']
     else:env.update(font_scale=c['fontScale'],dimension_encoding='paparazzi-float32-screen-config-v1')
     write(case/f'environment.{platform}.json',env)
    write(case/'checkpoint-map.json',{'case':cid,'model_inputs':[{'index':0,'revision':m0['revision'],'canonical_input_sha256':hashlib.sha256(json.dumps(m0,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()},{'index':1,'revision':m1['revision'],'canonical_input_sha256':hashlib.sha256(json.dumps(m1,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()}],'states':ss,'route_notes':'Use original actions through design_contract compile. Compiled action state_id/after_targets bind runtime evidence to exactly these states. Sweep stimulus_action preserves the original activation interval; never substitute sweep event deltas.'})
    draw(t,cid,folder,r)
  brief,api=docs(t);write(pub/'BRIEF.md',brief);write(pub/'API.md',api);sw,kt=bridges(t);write(pub/'Bridge.swift',sw);write(pub/'ObserverBridge.kt',kt)
  write(priv/'HELDOUT.md','H1 changes only data, availability/selection combinations, width, theme, font size and direction within the public brief. Rule IDs, methods, ownership and action meanings are identical. Keep this directory private until all public implementation FINAL seals.\n')
  write(root/'design-times.json',{'actual_task_design_started_at':start,'actual_task_design_finished_at':now(),'overall_design_started_at':'2026-10-22T01:37:31Z','status':'Authored, not sealed; compilation and fresh independent design review pending'})
 write(ROOT/'authored-at.json',{'actual_all_design_authored_at':now(),'tasks':[{'id':t['id'],'domain':t['domain'],'component':t['name'],'structure':t['structure']} for t in TASKS]})
if __name__=='__main__':generate()
