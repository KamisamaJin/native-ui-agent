#!/usr/bin/env python3
"""Independent preimplementation specification generator. No production imports."""
import json,hashlib,time,subprocess,sys,textwrap,html,copy
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent
R=D.parent
TOOLS=R/'candidate-v7/scripts'
sys.path.insert(0,str(TOOLS))
sys.dont_write_bytecode=True
import design_contract as dc

def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n' if not isinstance(v,str) else v)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(v,u='string'):return {'value':v,'unit':u}
def money(c):return f'${c//100}.{c%100:02d}'
NOTES={
'T1':[
'Packing order: place dense equipment close to your back and keep the route map reachable. Check the actual pack before departure. This planning card records the chosen shared equipment; it does not replace the group leader’s final equipment inspection.',
'Weather changes quickly along the exposed ridge. Keep the optional weather cover at the top of the bag when selected. The cover protects equipment from brief rain and is not a substitute for the overnight shelter required by this route.',
'Each listed weight is the total carried weight for one shared item. The base load already includes personal clothing, food and the filled bottle. Do not add those items a second time when discussing the displayed total with the group.',
'Before leaving the meeting point, check straps, buckles and the tent poles with another member of the group. Record any damaged equipment with the trip coordinator. Availability shown here comes from the caller and may change when a new trip request arrives.'
],
'T2':[
'Publication scope: the selected channels apply to this one asset and the named publication only. Website use includes the publication’s own article pages. A printed edition covers one edition and does not include merchandise, packaging or unrelated promotional campaigns.',
'An exclusive license is offered only when the asset owner has made it available for this quote. Its surcharge is added once to the channel total. The eligibility message and quoted amount should be reviewed together before creating the license request.',
'Attribution must remain visible wherever the asset appears. Keep the creator credit with the image or in the publication’s credits section. Cropping may preserve the subject and must not remove a visible signature. These notes travel with the editorial handoff.',
'A new quote replaces the current channel selection and exclusive choice with its own supplied starting values. Creating a request sends the chosen channel identifiers to the caller. It does not charge a card, publish an asset or automatically grant additional usage rights.'
],
'T3':[
'Group order notes: each selected drink represents one serving. Review the drinks with the group before placing the order. Availability and serving limits are supplied by the café for this order; a replacement order starts with its own supplied selection.',
'Reusable cup credit is available only for eligible drinks when the counter accepts reusable cups. Every selected drink must support that option. Bring clean cups to the collection counter and tell the barista which drinks belong to each person in the group.',
'Member savings are applied once when the number of selected drinks meets the displayed threshold. Cup credit is calculated separately per selected drink. The summary shows the final quoted total after both reductions, with a minimum total of zero.',
'Please check ingredients directly with café staff if anyone has an allergy. Ingredient notes on this planning card are informational. The order callback contains the selected drink identifiers and the cup choice; it does not collect payment or schedule collection.'
]}
SPEC={
'T1':dict(name='ExpeditionPackPanel',model='ExpeditionPackRequest',item='ExpeditionPackItem',file='ExpeditionPackPanel',prefix='pack',title='Ridge expedition pack',context='North ridge • shared equipment',a='Two-person tent',b='Trail stove',extra='Weather cover',primary='Confirm pack',foot='Before departure',kind='pack'),
'T2':dict(name='PublicationRightsPanel',model='PublicationRightsRequest',item='PublicationRightsChannel',file='PublicationRightsPanel',prefix='rights',title='Publication rights',context='Field Journal • autumn feature',a='Website',b='Print edition',extra='Exclusive license',primary='Create license',foot='Usage notes',kind='rights'),
'T3':dict(name='CafeGroupOrderPanel',model='CafeGroupOrderRequest',item='CafeGroupDrink',file='CafeGroupOrderPanel',prefix='cafe',title='Café group order',context='Design team • afternoon break',a='Oat latte',b='Cold brew',extra='Reusable cups',primary='Place order',foot='Collection notes',kind='cafe')}

def fixture(task,case,new=False):
 s=SPEC[task]; narrow=case=='P2';hidden=case=='H1'
 x=dict(id=f'{case.lower()}-'+('replacement' if new else 'request'),title=s['title'],context=s['context'] if not new else {'T1':'Woodland loop • day equipment','T2':'Harbor Notes • spring issue','T3':'Research team • morning break'}[task],choiceWidth=138 if narrow else 173,notes=NOTES[task])
 if task=='T1':
  x.update(baseGrams=1500 if new else 1200,maxGrams=2500 if new else 3150 if narrow else 3500,requiresShelter=not new,coverGrams=200,selectedIDs=['stove'] if new else ['tent','stove'] if hidden else [],cover=False,items=[dict(id='tent',name=s['a'],grams=1800,available=True,providesShelter=True,note='Overnight shelter • 1800 g'),dict(id='stove',name=s['b'],grams=800,available=not narrow or new,providesShelter=False,note='Shared cooking • 800 g')])
 elif task=='T2':
  x.update(baseCents=800 if new else 1200,exclusiveCents=4000 if new else 3000,exclusiveAllowed=not narrow and not new,selectedIDs=['print'] if hidden and not new else ['web'] if new else [],exclusive=hidden and not new,channels=[dict(id='web',name=s['a'],cents=900 if new else 800,available=True,note='Own publication pages'),dict(id='print',name=s['b'],cents=1800 if new else 2000,available=not narrow,note='One printed edition')])
 else:
  x.update(maxServings=1 if new else 2,member=hidden or new,discountThreshold=2,discountCents=200,reuseCreditCents=50,reuseAllowed=not narrow,selectedIDs=['cold'] if hidden and not new else ['latte'] if new else [],reuse=False,drinks=[dict(id='latte',name=s['a'],cents=450,available=True,supportsReuse=True,note='Oat milk • espresso'),dict(id='cold',name=s['b'],cents=400,available=not narrow or new,supportsReuse=False,note='Black coffee • chilled')])
 return x

def evaluate(task,x,selected,extra,expanded):
 s=SPEC[task];items=x[{'T1':'items','T2':'channels','T3':'drinks'}[task]];by={i['id']:i for i in items};chosen=[by[i] for i in selected];n=len(chosen)
 if task=='T1':
  total=x['baseGrams']+sum(i['grams'] for i in chosen)+(x['coverGrams'] if extra else 0)
  ready=n>0 and total<=x['maxGrams'] and (not x['requiresShelter'] or any(i['providesShelter'] for i in chosen))
  status='Capacity exceeded' if total>x['maxGrams'] else 'Choose shared equipment' if not n else 'Shelter required' if x['requiresShelter'] and not any(i['providesShelter'] for i in chosen) else 'Ready for departure'
  summary=f'{n} item'+('' if n==1 else 's')+f' • {total} g / {x["maxGrams"]} g'
  extraenabled=n>0 and (extra or total+x['coverGrams']<=x['maxGrams'])
  secondary=items[1]['available'] and (items[1]['id'] in selected or total+items[1]['grams']<=x['maxGrams'])
  detail='Shelter needed for this route.' if x['requiresShelter'] else 'Day route: no shelter required.'
 elif task=='T2':
  total=x['baseCents']+sum(i['cents'] for i in chosen)+(x['exclusiveCents'] if extra else 0)
  ready=n>0;status='Choose a publication channel' if not n else 'Exclusive use' if extra else 'Standard use'
  summary=f'{n} channel'+('' if n==1 else 's')+f' • {money(total)}'
  extraenabled=x['exclusiveAllowed'] and n>0;secondary=items[1]['available'];detail='Exclusive rights available.' if x['exclusiveAllowed'] else 'Exclusive rights unavailable for this quote.'
 else:
  saving=x['discountCents'] if x['member'] and n>=x['discountThreshold'] else 0
  total=max(0,sum(i['cents'] for i in chosen)-saving-(x['reuseCreditCents']*n if extra else 0))
  ready=0<n<=x['maxServings'];status=f'Member saving {money(saving)}' if saving else 'No member saving'
  summary=f'{n} drink'+('' if n==1 else 's')+f' • {money(total)}'
  extraenabled=x['reuseAllowed'] and n>0 and all(i['supportsReuse'] for i in chosen)
  secondary=items[1]['available'] and (items[1]['id'] in selected or n<x['maxServings'])
  detail=f'Member offer: {money(x["discountCents"])} off {x["discountThreshold"]} drinks.' if x['member'] else 'Guest order: member savings unavailable.'
 return dict(title=x['title'],context=x['context'],choice=items[0]['id'] in selected,secondary=secondary,extraenabled=extraenabled,extra=extra,summary=summary,status=status,ready=ready,primary=s['primary'],expanded=expanded,detail=detail,toggle='Hide details' if expanded else 'Show details')

def business_states(task,case):
 x=fixture(task,case); selected=list(x['selectedIDs']);extra=x[{'T1':'cover','T2':'exclusive','T3':'reuse'}[task]]; expanded=False
 keys=['packed','licensed','ordered']; itemkey={'T1':'items','T2':'channels','T3':'drinks'}[task]
 states=[]
 def push(name,event=None):states.append((name,copy.deepcopy(evaluate(task,x,selected,extra,expanded)),event))
 push('loaded')
 aid=x[itemkey][0]['id'];selected.remove(aid) if aid in selected else selected.append(aid)
 # Each fixture has an available first choice, removable even when seeded overweight.
 if task=='T1' and extra and evaluate(task,x,selected,extra,expanded)['summary']:pass
 if task=='T3' and extra and not evaluate(task,x,selected,extra,expanded)['extraenabled']:extra=False
 push('chosen',[]);expanded=True;push('details',[])
 if evaluate(task,x,selected,extra,expanded)['extraenabled']:extra=not extra
 push('optioned',[])
 v=evaluate(task,x,selected,extra,expanded)
 event=[f'{keys[int(task[-1])-1]}:{x["id"]}:{",".join(sorted(selected))}:{str(extra).lower()}'] if v['ready'] else []
 push('submitted',event)
 x=fixture(task,case,True);selected=list(x['selectedIDs']);extra=x[{'T1':'cover','T2':'exclusive','T3':'reuse'}[task]];expanded=False;push('replaced',[])
 return states

RULES=[
 dict(id='title',kind='control',target='title',property='label'),dict(id='context',kind='control',target='context',property='label'),dict(id='first-choice-selected',kind='control',target='choiceA',property='selected'),dict(id='second-choice-enabled',kind='control',target='choiceB',property='enabled'),dict(id='option-enabled',kind='control',target='extra',property='enabled'),dict(id='option-selected',kind='control',target='extra',property='selected'),dict(id='derived-summary',kind='control',target='summary',property='label'),dict(id='eligibility-status',kind='control',target='status',property='label'),dict(id='primary-enabled',kind='control',target='primary',property='enabled'),dict(id='primary-label',kind='control',target='primary',property='label'),dict(id='details-presence',kind='control',target='detail',property='present'),dict(id='details-copy',kind='control',target='detail',property='label'),dict(id='disclosure-label',kind='control',target='disclosure',property='label'),dict(id='primary-height',kind='geometry',target='primary',property='height',basis='control',measurement='accessibility_box',op='near'),dict(id='choice-width',kind='geometry',target='choiceA',property='width',basis='control',measurement='accessibility_box',op='near'),dict(id='title-font-size',kind='text_layout',target='title',property='font_sp'),dict(id='title-font-weight',kind='text_layout',target='title',property='font_weight'),dict(id='title-ink',kind='text_layout',target='title',property='color_argb'),dict(id='summary-wrap',kind='text_layout',target='summary',property='ellipsized'),dict(id='activation-callback',kind='event'),dict(id='replacement-callback',kind='event',stimulus='caller_update'),dict(id='visual-composition',kind='manual',target='title',allowed_methods=['visual'],coverage='target')]
MAP={'title':'title','context':'context','first-choice-selected':'choice','second-choice-enabled':'secondary','option-enabled':'extraenabled','option-selected':'extra','derived-summary':'summary','eligibility-status':'status','primary-enabled':'ready','primary-label':'primary','details-presence':'expanded','details-copy':'detail','disclosure-label':'toggle'}

def actions(prefix):return [dict(type='sweep',state_id='loaded',max_steps=24),dict(type='tap',target='choiceA',reveal=True,state_id='chosen'),dict(type='tap',target='disclosure',reveal=True,state_id='details'),dict(type='tap',target='extra',reveal=True,allow_disabled=True,state_id='optioned'),dict(type='tap',target='primary',reveal=True,allow_disabled=True,state_id='submitted'),dict(type='apply_next_fixture',state_id='caller-applied'),dict(type='sweep',state_id='replaced',max_steps=24)]

def render_reference(task,case,x,v,path):
 s=SPEC[task];W=320 if case=='P2' else 390;scale=1.6 if case=='P2' else 1.;ink='#E9F2EC' if case=='P2' else '#18251F';bg='#101A14' if case=='P2' else '#FFFFFF';surface='#16231C' if case=='P2' else '#F4F7F3';accent='#94D6AC' if case=='P2' else '#276145';muted='#B7C7BD' if case=='P2' else '#53645B';border='#456251' if case=='P2' else '#C9D7CC'
 fontpath='/System/Library/Fonts/Supplemental/Arial.ttf';boldpath='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
 try:f=ImageFont.truetype(fontpath,14)
 except OSError:fontpath=boldpath=None
 elements=[];y=24
 def rect(x,y,w,h,fill,stroke=None,r=12):elements.append(('rect',x,y,w,h,fill,stroke,r))
 def text(st,x,yy,size=14,bold=False,color=ink,width=None):
  size=round(size*scale);font=ImageFont.truetype((boldpath if bold else fontpath),size) if fontpath else ImageFont.load_default();maxw=width or W-x-16
  words=st.split();lines=[];line=''
  for word in words:
   test=(line+' '+word).strip()
   if font.getlength(test)>maxw and line:lines.append(line);line=word
   else:line=test
  if line:lines.append(line)
  lh=round(size*1.32)
  for i,line in enumerate(lines):elements.append(('text',x,yy+i*lh,line,size,bold,color))
  return len(lines)*lh
 y+=text(v['title'],16,y,22,True)+8;y+=text(v['context'],16,y,14,color=muted)+20
 items=x[{'T1':'items','T2':'channels','T3':'drinks'}[task]];cw=x['choiceWidth'];h=max(90,round(95*scale))
 for i,item in enumerate(items):
  xx=16+i*(cw+12);rect(xx,y,cw,h,surface if item['available'] else border,accent if item['id'] in x['selectedIDs'] else border);text(item['name'],xx+12,y+12,16,True,color=ink if item['available'] else muted,width=cw-24);text(item['note'],xx+12,y+round(44*scale),12,color=muted,width=cw-24)
 y+=h+16
 rect(16,y,W-32,round(52*scale),surface if v['extraenabled'] else border,accent if v['extra'] else border);text(s['extra'],28,y+12,16,True,color=ink if v['extraenabled'] else muted);y+=round(52*scale)+16
 y+=text(v['summary'],16,y,18,True)+16;y+=text(v['status'],16,y,14,True,color=accent)+12
 rect(16,y,W-32,48,surface,border);text(v['toggle'],28,y+12,14,True);y+=64
 if v['expanded']:y+=text(v['detail'],16,y,14,color=muted)+16
 rect(16,y,W-32,56,accent if v['ready'] else border);text(s['primary'],28,y+15,16,True,color=(('#101A14' if case=='P2' else '#FFFFFF') if v['ready'] else muted));y+=80
 y+=text(s['foot'],16,y,16,True)+12
 for note in x['notes']:y+=text(note,16,y,14,color=muted)+16
 H=y+24;img=Image.new('RGB',(W,H),bg);draw=ImageDraw.Draw(img);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="{bg}"/>']
 for e in elements:
  if e[0]=='rect':
   _,xx,yy,w,h,fill,stroke,r=e;draw.rounded_rectangle((xx,yy,xx+w,yy+h),r,fill=fill,outline=stroke,width=1);svg.append(f'<rect x="{xx}" y="{yy}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or fill}"/>')
  else:
   _,xx,yy,st,size,bold,color=e;font=ImageFont.truetype((boldpath if bold else fontpath),size) if fontpath else ImageFont.load_default();draw.text((xx,yy),st,font=font,fill=color);svg.append(f'<text x="{xx}" y="{yy+size}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(st)}</text>')
 svg.append('</svg>');write(path.with_suffix('.svg'),'\n'.join(svg));img.save(path.with_suffix('.png'))

FIELDS={
'T1':('baseGrams:Int,maxGrams:Int,requiresShelter:Bool,coverGrams:Int,selectedIDs:[String],cover:Bool,items:[ExpeditionPackItem]','id:String,name:String,grams:Int,available:Bool,providesShelter:Bool,note:String'),
'T2':('baseCents:Int,exclusiveCents:Int,exclusiveAllowed:Bool,selectedIDs:[String],exclusive:Bool,channels:[PublicationRightsChannel]','id:String,name:String,cents:Int,available:Bool,note:String'),
'T3':('maxServings:Int,member:Bool,discountThreshold:Int,discountCents:Int,reuseCreditCents:Int,reuseAllowed:Bool,selectedIDs:[String],reuse:Bool,drinks:[CafeGroupDrink]','id:String,name:String,cents:Int,available:Bool,supportsReuse:Bool,note:String')}

def api_and_bridges(task,pub):
 s=SPEC[task];fields,items=FIELDS[task];fields='id:String,title:String,context:String,choiceWidth:Double,notes:[String],'+fields
 def swiftstruct(name,fs):
  pairs=[f.split(':',1) for f in fs.split(',')];return 'public struct '+name+': Codable {\n'+''.join(f'    public let {n}: {ty}\n' for n,ty in pairs)+'    public init('+', '.join(f'{n}: {ty}' for n,ty in pairs)+') {\n'+''.join(f'        self.{n} = {n}\n' for n,_ in pairs)+'    }\n}\n'
 swift=swiftstruct(s['item'],items)+'\n'+swiftstruct(s['model'],fields)
 write(pub/'API.md',f'''# {s['name']} public API

Implement Swift in `alerttoast/Sources/AlertToast/{s['file']}.swift` and Compose in `reply/Reply/app/src/main/java/com/example/reply/ui/components/{s['file']}.kt`.

```swift
{swift}
public struct {s['name']}: View {{
    public init(request: {s['model']}, onConfirm: @escaping (String, [String], Bool) -> Void)
    public var body: some View {{ get }}
}}
```

Kotlin uses `package com.example.reply.ui.components` and public data classes with identical field names. Swift `Int`→Kotlin `Int`, `Double`→`Double`, `Bool`→`Boolean`, `[String]`→`List<String>`, item arrays→`List<Item>`. Define every model constructor argument in the exact order shown above, with no required extra parameters.

```kotlin
@Composable
fun {s['name']}(request: {s['model']}, onConfirm: (String, List<String>, Boolean) -> Unit)
```

`onConfirm` receives the current request id, selected item ids sorted lexicographically, and the current optional choice. Call only when enabled. Other controls update local UI state without caller callbacks. Request id replacement resets local selection, optional choice and disclosure on the existing mounted component. Never emit a confirm callback during caller replacement. Models are business inputs only; do not add observation state, expected labels, grading flags or evidence props.
''')
 prefix={'T1':'packed','T2':'licensed','T3':'ordered'}[task]
 write(pub/'Bridge.swift',f'''import SwiftUI
import Foundation
import AlertToast

enum ObserverBridge {{
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {{
        let data = try! JSONSerialization.data(withJSONObject: fixture)
        let request = try! JSONDecoder().decode({s['model']}.self, from: data)
        return AnyView({s['name']}(request: request) {{ id, ids, option in
            onEvent("{prefix}:\\(id):\\(ids.sorted().joined(separator: ",")):\\(option ? "true" : "false")")
        }})
    }}
}}
''')
 def kval(n,ty,obj='input'):
  if ty=='String':return f'{obj}["{n}"]!!.jsonPrimitive.content'
  if ty=='Int':return f'{obj}["{n}"]!!.jsonPrimitive.int'
  if ty=='Double':return f'{obj}["{n}"]!!.jsonPrimitive.double'
  if ty=='Bool':return f'{obj}["{n}"]!!.jsonPrimitive.boolean'
  if ty=='[String]':return f'{obj}["{n}"]!!.jsonArray.map {{ it.jsonPrimitive.content }}'
  return f'{obj}["{n}"]!!.jsonArray.map {{ value -> val item = value.jsonObject; {s["item"]}('+', '.join(nn+' = '+kval(nn,tt,'item') for nn,tt in (f.split(':',1) for f in items.split(',')))+') }'
 args=',\n            '.join(n+' = '+kval(n,ty) for n,ty in (f.split(':',1) for f in fields.split(',')))
 write(pub/'ObserverBridge.kt',f'''package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*

object ObserverBridge {{
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {{
        val request = {s['model']}(
            {args}
        )
        {s['name']}(request = request, onConfirm = {{ id, ids, option ->
            onEvent("{prefix}:$id:${{ids.sorted().joinToString(",")}}:$option")
        }})
    }}
}}
''')

BUSINESS={
'T1':'''The shared-item choices toggle membership in the pack. Adding is allowed only for an available item whose projected total fits maxGrams; removing a selected item is always allowed. Initial selected IDs retain known available items even if the seed is overweight, allowing the user to remove equipment. Total grams = baseGrams + selected grams + coverGrams when cover is on. Weather cover is enabled only when there is a selected item and either it is already on or adding it fits the limit. Removing the last selected item clears cover. Confirmation requires at least one selected item, total at or below maxGrams and a shelter item when requiresShelter is true. Status priority is Capacity exceeded, Choose shared equipment, Shelter required, Ready for departure. Summary is `N item[s] • TOTAL g / MAX g`. Detail text is `Shelter needed for this route.` or `Day route: no shelter required.`''',
'T2':'''Each available publication channel toggles selection. Unavailable channels cannot be added and are removed from caller seeds. Standard price = baseCents + selected channel cents, even with no channels. Exclusive price adds exclusiveCents once. Exclusive is enabled only when exclusiveAllowed and at least one channel is selected. Clearing the last channel clears exclusive. Initial exclusive is kept only when eligible. Confirmation requires at least one channel. Status is Choose a publication channel when empty, otherwise Exclusive use or Standard use. Summary is `N channel[s] • $D.CC`. Detail text is `Exclusive rights available.` or `Exclusive rights unavailable for this quote.`''',
'T3':'''Each available drink toggles one serving. Adding is allowed only below maxServings; removal is always allowed. Initial known available drink IDs are retained even if the seed exceeds maxServings. Reusable cups is enabled only when reuseAllowed, at least one drink is selected and every selected drink supportsReuse. Incompatible selection clears reuse. Base price is selected drink cents. Apply discountCents once if member and selected count is at least discountThreshold. Subtract reuseCreditCents per selected drink when reuse is on; clamp the final price to zero. Confirmation requires selected count from one through maxServings. Summary is `N drink[s] • $D.CC`. Status is Member saving $D.CC when a saving applies, otherwise No member saving. Detail is `Member offer: $D.CC off N drinks.` for members or `Guest order: member savings unavailable.`'''}

def build_task(task):
 s=SPEC[task];base=D/task;pub=base/'public';priv=base/'private';pub.mkdir(parents=True,exist_ok=True);priv.mkdir(exist_ok=True)
 api_and_bridges(task,pub)
 write(pub/'BRIEF.md',f'''# {s['name']}

Build a native {s['kind']} component from this frozen design. All UI state, derived summaries, enablement and callback routing belong in the production component. The bridge only decodes caller inputs and maps the real confirm callback. Do not alter an existing screen, theme, build system or project to replace this component. Both platforms use the public API in API.md.

## Business rules

{BUSINESS[task]}

Display the title and context from the caller. Render the two choices in input order; each shows its name and note. Selected choices and the optional control expose native selected state (SwiftUI selected accessibility trait, Compose selectable semantics). Disabled controls expose native disabled state. Optional control label is `{s['extra']}`. The optional choice is local. Disclosure starts collapsed, toggles `Show details` / `Hide details` and reveals exactly the task-specific detail text. Confirmation label is `{s['primary']}`. Confirmation does not clear selection or close details. The long notes section heading is `{s['foot']}`; display every supplied paragraph in order without truncation. Replacing request.id resets local state to the new seed and collapses details on the same mounted component, with no callback. Ignore unknown seed ids; de-duplicate seeds. No hidden additional eligibility rules apply.

## Fixed native presentation

Host owns horizontal padding 16 and top padding 24; do not add another outer horizontal inset. Host viewport height is 600. Component lays out vertically with 16-unit major gaps, 8 between title and context, and 12 between two equal-width choices. Each choice width is request.choiceWidth (173 at offered width390;138 at320); do not infer width from device size. Choices have minimum height90 and may grow for large text. Optional and disclosure controls have minimum height48; main confirm control has exact native accessibility/control height56. Main action spans component width. Native corner radius12; card internal inset12. Wrap every label and note; never ellipsize summary. All controls remain available to the host ScrollView, with no nested vertical scroll.

Title: system sans22, weight700; summary18 weight600; choice name16 weight600; body/context/detail14 weight400; action16 weight600; note heading16 weight600. iOS uses Dynamic Type relative scaling for these base sizes and Android uses sp with caller fontScale. Native iOS computed font/color is unmeasurable by the observer and must remain U; visual review is separate. Light palette: canvas #FFFFFF, surface #F4F7F3, ink #18251F, muted #53645B, accent #276145, border/disabled #C9D7CC, primary ink #FFFFFF. Dark palette: canvas #101A14, surface #16231C, ink #E9F2EC, muted #B7C7BD, accent #94D6AC, border/disabled #456251, primary ink #101A14. Selected choice border uses accent and a check mark; other choice borders use border. Disabled controls use border fill and muted text. Use the caller theme and text scale.

## Native identities and state routes

Use the exact identifiers in bindings.json on real displayed nodes. The long-notes section also has identifier `{s['prefix']}.notes` on its section heading (required by fixture coverage). `choiceA`/`choiceB` denote the first/second option. `extra` is the optional control. `detail` exists only while expanded. Preserve separate native text nodes for title, summary, context and detail. Do not put a child OnClick/Button inside another clickable control.

Each public case contains six selected states: loaded (original full sweep), chosen (first choice toggle), details (expand), optioned (attempt optional toggle), submitted (attempt confirm), replaced (caller replacement then full sweep). The two explicit sweeps are original stimuli. Actions marked allow_disabled explicitly permit blocked observation; absence of successful dispatch makes callback evidence U, while independent current-state facts still count. Each case uses five non-sweep actions. P1 is light/normal; P2 is narrow/dark/large text. H1 supplies another ordinary input combination and caller update under these same rules.

SVG and PNG reference canvases show the loaded state and full content; additional state labels/values are fixed in cases/<case>/expected-states.json and typed reference.json. References illustrate native system typography using an export font; acceptance requires SF/Roboto metrics and readable wrapping rather than pixel identity to the export font. Scope and precision are fixed in STYLE-PRECISION.md. Builders must run the frozen compiler using contract.json, design-lock.json, approval.json, bindings.json and their own fresh output. Builders must not read public/compiled or any private directory.
''')
 write(pub/'STYLE-PRECISION.md','''# Measurement and visual scope

Geometry assertions measure actual accessible control boxes, not inferred layout attributes or physical hit areas. Primary control height56 is deliberate stable geometry at both text scales: its concise label fits the approved56-unit box. Choice width uses the caller's explicit equal-column allocation; 390−32−12 divided by2 =173 and 320−32−12 divided by2 =138. Near tolerance0.75 native pt/dp allows subpixel rounding and AX float serialization, smaller than one layout unit; it is fixed before any SDK or screenshot feedback. No geometry tolerance is applied to colors, weights or text sizes. Android native title font_sp=22, weight700 and packed ARGB ink are exact properties, not screenshot estimates. SF base font22 scales under Dynamic Type; generic iOS computed font/color/weight remain unsupported U. Android ellipsized=false is exact native text-layout evidence; iOS equivalent remains U if absent. Visual review independently judges hierarchy, selected/disabled appearance, all palette roles, font sizing, wrapping, notes completeness and freedom from clipping/overlap at each state. Full-layout P requires complete state coverage; target-state visual rows may only judge captured target regions and must document remaining offscreen scope. No visual P can replace native_style U.
''')
 bindings={r[k]:{'identifier':s['prefix']+'.'+r[k]} for r in RULES for k in ['target','reference_target'] if k in r};write(pub/'bindings.json',bindings)
 states=[dict(id=n,input_index=1 if n=='replaced' else 0,after_action=i,coverage='full_content' if n in ['loaded','replaced'] else 'targets',**({'stimulus_action':5} if n=='replaced' else {})) for n,i in [('loaded',0),('chosen',1),('details',2),('optioned',3),('submitted',4),('replaced',6)]]
 reference={'geometry':{p:{'height':t(56,u),'width_normal':t(173,u),'width_narrow':t(138,u),'tolerance':t(.75,u)} for p,u in [('ios','pt'),('android','dp')]},'native_style':{'font':t(22,'sp'),'weight':t(700,'scalar'),'light_ink':t('#FF18251F','argb'),'dark_ink':t('#FFE9F2EC','argb'),'no_ellipsis':t(False,'bool')},'scenarios':{}}
 scenarios={}
 for case in ['P1','P2','H1']:
  root=pub if case!='H1' else priv;cp=root/'cases'/case
  f=fixture(task,case);nf=fixture(task,case,True)
  env=dict(initial=f,updates=[nf],width=320 if case=='P2' else 390,theme='dark' if case=='P2' else 'light',dynamic_type='xxxLarge' if case=='P2' else 'large',fontScale=1.6 if case=='P2' else 1.,direction='ltr',canvas_color='#101A14' if case=='P2' else '#FFFFFF',viewportHeight=600,max_scrolls=24,state_capture=True,required_identifiers=[s['prefix']+'.primary',s['prefix']+'.notes'])
  write(cp/'fixtures.json',env)
  acts=actions(s['prefix']);bound=copy.deepcopy(acts)
  for a in bound:
   if isinstance(a.get('target'),str):a['target']=bindings[a['target']]
  write(cp/'actions.json',bound)
  expected=business_states(task,case);write(cp/'expected-states.json',{n:dict(v,callback_delta=e) for n,v,e in expected})
  refstates={};values={r['id']:{} for r in RULES}
  for n,v,event in expected:
   refstates[n]={}
   for r in RULES:
    rid=r['id'];datum=None;unit='string';special=None
    if rid in MAP:
     datum=v[MAP[rid]];unit='bool' if isinstance(datum,bool) else 'string'
     if rid=='details-copy' and not v['expanded']:special='Detail text is deliberately absent while disclosure is collapsed; details-presence checks absence separately.'
    elif rid=='primary-height' or rid=='choice-width':
     key='height' if rid=='primary-height' else 'width_narrow' if case=='P2' else 'width_normal';special={p:{'source':'reference','pointer':f'/geometry/{p}/{key}'} for p in ['ios','android']};special['tolerance']={p:{'source':'reference','pointer':f'/geometry/{p}/tolerance'} for p in ['ios','android']}
    elif rid in ['title-font-size','title-font-weight','title-ink','summary-wrap']:
     key={'title-font-size':'font','title-font-weight':'weight','title-ink':'dark_ink' if case=='P2' else 'light_ink','summary-wrap':'no_ellipsis'}[rid];special={p:{'source':'reference','pointer':'/native_style/'+key} for p in ['ios','android']}
    elif rid=='activation-callback':
     if n not in ['chosen','details','optioned','submitted']:special='No user activation is the independently selected stimulus for this state.'
     else:datum=event;unit='events'
    elif rid=='replacement-callback':
     if n!='replaced':special='Caller replacement is not the selected stimulus for this state.'
     else:datum=[];unit='events'
    elif rid=='visual-composition':datum=f'{case}: {n}; native hierarchy, palette, typography, selection, readable wrapping and long notes per BRIEF and reference PNG; only captured regions in target states.'
    if isinstance(special,str):values[rid][n]={'not_applicable':special}
    elif isinstance(special,dict):values[rid][n]=special
    else:
     refstates[n][rid]=t(datum,unit);expr={'source':'reference','pointer':f'/scenarios/{case}/{n}/{rid}'};values[rid][n]={'ios':expr,'android':expr}
  reference['scenarios'][case]=refstates;scenarios[case]=dict(states=states,actions=acts,values=values)
  render_reference(task,case,f,expected[0][1],root/'references'/f'{case}-loaded')
 # Public reference excludes hidden combination entirely. Private reference is a separately typed document, not a hidden override.
 pubref=copy.deepcopy(reference);del pubref['scenarios']['H1'];privref=copy.deepcopy(reference);privref['scenarios']={'H1':reference['scenarios']['H1']}
 for root,ref,cases in [(pub,pubref,['P1','P2']),(priv,privref,['H1'])]:
  write(root/'reference.json',ref)
  contract=dict(version=1,design_owner='Independent blind design context / multitask-forward',approval_reference='approval.json; sealed before all six implementations',sources=[dict(id='reference',path='reference.json',sha256=sha(root/'reference.json'))],required_rule_ids=[r['id'] for r in RULES],rules=RULES,scenarios={c:scenarios[c] for c in cases})
  write(root/'contract.json',contract)
  if root==priv:write(root/'bindings.json',bindings)
  lock=dc.seal(root/'contract.json',root);write(root/'design-lock.json',lock);digest=dc.digest(lock)
  write(root/'approval.json',dict(design_lock_sha256=digest,approved_at_unix=time.time(),owner='Independent blind design context',basis='Business brief, typed source and reference fixed without candidate source, rendered output or suspected defects.',precision='STYLE-PRECISION.md',scope=cases))
  for case in cases:
   dest=root/'compiled'/case;write(dest/'fixtures.json',json.loads((root/'cases'/case/'fixtures.json').read_text()))
   for platform in ['ios','android']:
    out=dest/platform;plan,enriched=dc.compile_contract(lock,digest,case,platform,bindings,json.loads((root/'cases'/case/'actions.json').read_text()));write(out/'plan.json',plan);write(out/'actions.json',enriched);write(dest/f'actions.{platform}.json',enriched)
 # Complete independently enumerated denominator, including all N/A rows.
 table=[]
 for case in ['P1','P2','H1']:
  for platform in ['ios','android']:
   root=pub if case!='H1' else priv;plan=json.loads((root/'compiled'/case/platform/'plan.json').read_text());checks={a['id']:a for a in plan['assertions']}
   for cell in plan['matrix_contract']['cells']:
    rule=next(r for r in RULES if r['id']==cell['requirement_id']);kind=rule['kind'];cl={'control':'business_current','event':'business_transition','geometry':'geometry','text_layout':'native_style','manual':'visual'}[kind]
    a=checks.get(cell['id'],{})
    table.append(dict(id=f'{case}/{platform}/{cell["id"]}',case=case,platform=platform,state=cell['state'],requirement=cell['requirement_id'],aspect=rule.get('property',kind),**{'class':cl},applicable=cell['disposition']=='required',reason=cell.get('reason','Required by the independent brief'),expected=a.get('expected'),unit=a.get('unit'),op=a.get('op','eq'),tolerance=a.get('tolerance'),plan_assertion_id=cell['id']))
 write(priv/'acceptance-table.json',dict(version=1,rows=table,total_cells=len(table),scope='Every selected rule × state × platform × case, including U and explicit N/A; input/API checks are separate.'))
 write(priv/'METHODOLOGY.md','''# Independent oracle methodology

The design context received only the task charter and frozen tool schema. It did not read assignments/private, earlier trials, generic probes, candidates, screenshots or reported bugs. Three unrelated domains were selected before production implementation. H1 changes ordinary seed/input and caller replacement under the same public rules and adds no requirement. No deliberate production defects or mutation testing are used.

The complete acceptance table is generated from independently authored typed expectations and includes every case × platform × state × rule. The SDK-free grader imports the frozen candidate-v7 native evaluator and reads only the exact precompiled approved plan and canonical lock digest from this sealed design. Implementation plans are never read. The oracle tests use synthetic SDK-free observation controls, never production mutations. Unsupported native observations stay U. Manual visual evidence must identify original state PNGs with matching SHA256 and exact observation binding. Pair comparison includes business_current, business_transition, geometry and native_style only, with P/F/U/N/A denominator shown; visual decisions and input/API integrity stay separate. Claim matching requires exact case/platform/state/requirement and expected/unit identity. A claim of a defect requires oracle F; P cannot substantiate a defect, and U remains uncertain.
''')
 write(priv/'grader.py',f'''from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from oracle_common import grade_task, match_claims, compare_pair

def grade(case, platform, observation_path, root=None, manual=None, source_root=None, api_review=None):
    return grade_task(Path(__file__).resolve().parents[1], case, platform, observation_path, root, manual, source_root, api_review)
''')
 print(task,dc.digest(json.loads((pub/'design-lock.json').read_text())),len(table))

if __name__=='__main__':
 for task in SPEC:build_task(task)
 write(D/'COMPILER-REVISIONS.json',{'errors':[],'revisions':['Before seal: reference disabled fills/selected borders and explicit notes heading identifier clarified during independent visual QA; no SDK or implementation accessed.'],'note':'No compiler schema error occurred during independent initial authoring. All seal and compile functions are the frozen design_contract.py functions; no SDK run.'})
