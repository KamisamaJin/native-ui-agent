#!/usr/bin/env python3
"""Independent preimplementation design-v2 authoring; no implementation imports."""
import copy,hashlib,html,json,subprocess,sys,time
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parent
sys.path.insert(0,str(R/'candidate-v7/scripts'))
import design_contract as dc

def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n' if not isinstance(v,str) else v)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def typed(v,u='string'):return dict(value=v,unit=u)

NOTES2=[
'Check the live load before sending the mix to the desk. Each unmuted channel with a level above zero contributes its displayed units. Muted channels retain their stored levels so that an engineer can restore them without rebuilding the balance.',
'Preview mode lets the engineer prepare a mix that exceeds the live unit limit. The warning remains visible because switching that mix to live would require reducing levels or muting channels. Applying a preview mix does not automatically switch the desk to live.',
'Locked channels are supplied by the producer. Their increase, decrease and mute controls remain disabled while the channel is locked, but their current audible levels still count in the load. Changing mode does not unlock a channel or alter any stored level.',
'A replacement session restores all channel levels, mute flags and mode from the new request on the existing mounted component. Applying a mix reports the real current values to the caller. This panel does not access an audio device, start recording or change system volume.'
]
NOTES3=[
'Inspect each object in the queue and record its condition before submitting the review. Stable means no follow-up category is needed. Needs care requires a category so that the collection team can direct the object to the appropriate conservator.',
'Surface care covers visible finish and surface concerns; structure covers the support or physical assembly. This review records a routing category only. It does not prescribe a treatment, authorize cleaning or replace inspection by the collection’s conservation staff.',
'Moving between queue rows keeps decisions already entered for other objects. Read-only objects show their supplied condition and cannot be edited. An optional object may remain pending; every required object must have a complete decision before submission is enabled.',
'A new review request replaces all local decisions and focuses the caller’s requested object, or the first object when that identifier is unknown. The summary always counts the current complete decisions and care follow-ups across the entire queue, including objects outside the inspector.'
]

def mix_fixture(case,new=False):
 n=case=='P2';h=case=='H1'
 return dict(id=case.lower()+('-replacement' if new else '-session'),title='Broadcast cue mixer',context='Evening bulletin • Studio B' if not new else 'Morning interview • Studio C',maxLiveUnits=4 if new else 6,maxLevel=5,mode='live',stepperWidth=48,notes=NOTES2,channels=[
  dict(id='voice',name='Presenter',caption='Speech bus • producer locked' if n or h else 'Speech bus',level=3 if not h else 0,muted=False,locked=n or h),
  dict(id='music',name='Music bed',caption='Underscore bus',level=2 if new else 5 if n else 0 if h else 2,muted=False,locked=False),
  dict(id='room',name='Room tone',caption='Ambience bus',level=1 if not h else 2,muted=new,locked=False)])

def mix_calc(x,channels,mode):
 load=sum(c['level'] for c in channels if not c['muted']);audible=sum(c['level']>0 and not c['muted'] for c in channels);by={c['id']:c for c in channels};over=load>x['maxLiveUnits'];head=x['maxLiveUnits']-load
 return dict(title=x['title'],music=str(by['music']['level']),voice=str(by['voice']['level']),plus=(not by['music']['locked'] and by['music']['level']<x['maxLevel']),voiceMinus=(not by['voice']['locked'] and by['voice']['level']>0),muted=by['music']['muted'],preview=mode=='preview',summary=f'{audible} audible • {load} / {x["maxLiveUnits"]} units',headroom=f'Headroom: {head} unit'+('' if head==1 else 's'),warning=over,warningCopy=(f'Over live limit by {load-x["maxLiveUnits"]} unit'+('' if load-x['maxLiveUnits']==1 else 's')) if over else '',ready=audible>0 and (mode=='preview' or not over),modeLabel='Preview mode' if mode=='preview' else 'Live mode',mode=mode)

def mix_states(case):
 x=mix_fixture(case);cs=copy.deepcopy(x['channels']);mode=x['mode'];out=[]
 def push(s,e=None):out.append((s,mix_calc(x,cs,mode),e,copy.deepcopy(cs),copy.deepcopy(x)))
 push('loaded');m=next(c for c in cs if c['id']=='music')
 if not m['locked'] and m['level']<x['maxLevel']:m['level']+=1
 push('leveled',[]);mode='preview';push('previewed',[]);m['muted']=not m['muted'];push('muted',[])
 v=mix_calc(x,cs,mode);payload=','.join(f'{c["id"]}={c["level"]}/{str(c["muted"]).lower()}' for c in sorted(cs,key=lambda c:c['id']))
 push('submitted',[f'mix:{x["id"]}:{mode}:{payload}'] if v['ready'] else [])
 x=mix_fixture(case,True);cs=copy.deepcopy(x['channels']);mode=x['mode'];push('replaced',[]);return out

OBJECTS=[('folio','Botanical folio','Paper and cloth','Check the spine and page edges under normal gallery lighting. Keep the folio supported on the supplied cradle. Record the visible condition without opening sections that the collection team has marked as restricted.'),('bowl','Ceramic bowl','Glazed ceramic','View the rim and base without lifting the object from its support. Record any concern as a routing category and leave detailed treatment decisions to the conservator. Supplied read-only records remain visible in the queue.'),('sketch','Harbor sketch','Graphite on paper','Inspect the exposed sheet and frame from the viewing position. Keep the protective glazing in place. Note the appropriate care route if the visible condition needs follow-up from the collection team.')]

def review_fixture(case,new=False):
 n=case=='P2';h=case=='H1';objects=[]
 for idx,(identity,title,material,note) in enumerate(OBJECTS):
  status='stable' if idx==2 else 'pending';reason=None;editable=True;required=True
  if n and idx in [0,1]:status='stable';editable=idx!=1
  if h and idx==0:status='care'
  if h and idx==2:status='pending';required=False
  if new:
   status=['stable','care','pending'][idx];reason='structure' if idx==1 else None;editable=idx!=1;required=True
  objects.append(dict(id=identity,title=title,material=material,inspectionNote=note,status=status,reason=reason,editable=editable,required=required))
 return dict(id=case.lower()+('-replacement' if new else '-review'),title='Collection condition review',context='North gallery • weekly inspection' if not new else 'Study room • intake inspection',focusID='sketch' if new else 'folio',queueWidth=288 if n else 358,notes=NOTES3,objects=objects)

def review_calc(x,objects,focus):
 by={o['id']:o for o in objects};f=by[focus];complete=lambda o:o['status']=='stable' or (o['status']=='care' and o['reason'] in ['surface','structure'])
 completed=sum(complete(o) for o in objects);follow=sum(o['status']=='care' for o in objects);pending=sum(o['required'] and not complete(o) for o in objects);missingReason=any(o['required'] and o['status']=='care' and not complete(o) for o in objects)
 statusLabel=lambda o:'Needs care' if o['status']=='care' else 'Stable' if o['status']=='stable' else 'Pending'
 validation='Choose a care category' if missingReason else f'{pending} required decision'+('' if pending==1 else 's')+' remaining' if pending else 'Ready to submit'
 return dict(title=x['title'],focused=f['title'],queueSecond=focus=='bowl',stable=f['status']=='stable',care=f['status']=='care',editable=f['editable'],reasonPresent=f['status']=='care',surface=f['reason']=='surface',summary=f'{completed} of {len(objects)} reviewed • {follow} follow-up'+('' if follow==1 else 's'),validation=validation,ready=pending==0,queueSecondLabel=f'{by["bowl"]["title"]}, {statusLabel(by["bowl"])}',focus=focus)

def review_states(case):
 x=review_fixture(case);os=copy.deepcopy(x['objects']);focus=x['focusID'];out=[]
 def push(s,e=None):out.append((s,review_calc(x,os,focus),e,copy.deepcopy(os),copy.deepcopy(x)))
 push('loaded');f=os[0]
 if f['editable']:f.update(status='care',reason=None)
 # care-marked is an actual intermediate action; six independently selected states follow.
 if f['editable'] and f['status']=='care':f['reason']='surface'
 push('reasoned',[]);focus='bowl';push('advanced',[]);f=os[1]
 if f['editable']:f.update(status='stable',reason=None)
 push('classified',[]);v=review_calc(x,os,focus);payload=','.join(f'{o["id"]}={o["status"]}/{o["reason"] or "-"}' for o in sorted(os,key=lambda o:o['id']))
 push('submitted',[f'condition:{x["id"]}:{payload}'] if v['ready'] else []);x=review_fixture(case,True);os=copy.deepcopy(x['objects']);focus=x['focusID'];push('replaced',[]);return out

MIX_RULES=[
('title','control','title','label'),('mode-copy','control','modeLabel','label'),('music-level','control','musicLevel','label'),('presenter-level','control','voiceLevel','label'),('music-increase-enabled','control','musicPlus','enabled'),('presenter-decrease-enabled','control','voiceMinus','enabled'),('music-muted','control','musicMute','selected'),('preview-selected','control','preview','selected'),('derived-load','control','summary','label'),('derived-headroom','control','headroom','label'),('overload-presence','control','warning','present'),('overload-copy','control','warning','label'),('apply-enabled','control','primary','enabled'),('stepper-width','geometry','musicPlus','width'),('primary-height','geometry','primary','height'),('title-font-size','text_layout','title','font_sp'),('title-font-weight','text_layout','title','font_weight'),('title-ink','text_layout','title','color_argb'),('summary-wrap','text_layout','summary','ellipsized'),('activation-callback','event',None,None),('replacement-callback','event',None,None),('visual-composition','manual','title',None)]
REV_RULES=[
('title','control','title','label'),('focused-object','control','focused','label'),('queue-second-selected','control','queue2','selected'),('stable-selected','control','stable','selected'),('care-selected','control','care','selected'),('classification-enabled','control','stable','enabled'),('care-category-presence','control','reasonGroup','present'),('surface-category-selected','control','surface','selected'),('completion-summary','control','summary','label'),('validation-copy','control','validation','label'),('submit-enabled','control','primary','enabled'),('second-object-status','control','queue2','label'),('primary-height','geometry','primary','height'),('queue-width','geometry','queue2','width'),('care-control-height','geometry','surface','height'),('title-font-size','text_layout','title','font_sp'),('title-font-weight','text_layout','title','font_weight'),('title-ink','text_layout','title','color_argb'),('inspector-wrap','text_layout','inspectionNote','ellipsized'),('activation-callback','event',None,None),('replacement-callback','event',None,None),('visual-composition','manual','title',None)]
MIX_MAP=dict(zip([r[0] for r in MIX_RULES[:13]],['title','modeLabel','music','voice','plus','voiceMinus','muted','preview','summary','headroom','warning','warningCopy','ready']))
REV_MAP=dict(zip([r[0] for r in REV_RULES[:12]],['title','focused','queueSecond','stable','care','editable','reasonPresent','surface','summary','validation','ready','queueSecondLabel']))

SPEC={
'T2':dict(name='BroadcastCueMixerPanel',model='BroadcastCueMixerRequest',item='BroadcastMixChannel',prefix='mixer',rules=MIX_RULES,mapping=MIX_MAP,fixture=mix_fixture,states=mix_states,notes=NOTES2,primary='Apply mix',lightInk='#FF1E3652',darkInk='#FFE1EDFA'),
'T3':dict(name='CollectionConditionReviewPanel',model='CollectionConditionReviewRequest',item='CollectionConditionObject',prefix='condition',rules=REV_RULES,mapping=REV_MAP,fixture=review_fixture,states=review_states,notes=NOTES3,primary='Submit review',lightInk='#FF432D58',darkInk='#FFEADDF6')}

def route(task):
 if task=='T2':return [dict(type='sweep',state_id='loaded',max_steps=24),dict(type='tap',target='musicPlus',reveal=True,allow_disabled=True,state_id='leveled'),dict(type='tap',target='preview',reveal=True,state_id='previewed'),dict(type='tap',target='musicMute',reveal=True,state_id='muted'),dict(type='tap',target='primary',reveal=True,allow_disabled=True,state_id='submitted'),dict(type='apply_next_fixture',state_id='caller-applied'),dict(type='sweep',state_id='replaced',max_steps=24)]
 return [dict(type='sweep',state_id='loaded',max_steps=24),dict(type='tap',target='care',reveal=True,allow_disabled=True,state_id='care-marked'),dict(type='tap',target='surface',reveal=True,allow_disabled=True,state_id='reasoned'),dict(type='tap',target='queue2',reveal=True,state_id='advanced'),dict(type='tap',target='stable',reveal=True,allow_disabled=True,state_id='classified'),dict(type='tap',target='primary',reveal=True,allow_disabled=True,state_id='submitted'),dict(type='apply_next_fixture',state_id='caller-applied'),dict(type='sweep',state_id='replaced',max_steps=24)]

PALETTES={
'T2':dict(light=['#FFFFFF','#F0F5FA','#1E3652','#556B82','#245F9A','#C8D7E5','#FFFFFF'],dark=['#101B29','#17283C','#E1EDFA','#B4C7DD','#A0CCFA','#405971','#101B29']),
'T3':dict(light=['#FFFFFF','#F6F1FA','#432D58','#746181','#7750A6','#DACDE5','#FFFFFF'],dark=['#1C1424','#2A1D36','#EADDF6','#C8B5D9','#D5B6F5','#634E75','#1C1424'])}

class Canvas:
 def __init__(self,task,case):
  self.W=320 if case=='P2' else 390;self.scale=1.6 if case=='P2' else 1.;self.palette=PALETTES[task]['dark' if case=='P2' else 'light'];self.bg,self.surface,self.ink,self.muted,self.accent,self.border,self.actionInk=self.palette;self.els=[];self.y=24
 def font(self,size,bold=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',round(size*self.scale))
 def text(self,st,x=16,y=None,size=14,bold=False,color=None,width=None):
  y=self.y if y is None else y;f=self.font(size,bold);size=round(size*self.scale);lh=round(size*1.32);maxw=width or self.W-x-16;lines=[];line=''
  for word in st.split():
   test=(line+' '+word).strip()
   if f.getlength(test)>maxw and line:lines.append(line);line=word
   else:line=test
  if line:lines.append(line)
  for i,line in enumerate(lines):self.els.append(('text',x,y+i*lh,line,size,bold,color or self.ink))
  return max(1,len(lines))*lh
 def flow(self,st,size=14,bold=False,color=None,gap=12):self.y+=self.text(st,size=size,bold=bold,color=color)+gap
 def rect(self,x,y,w,h,fill=None,stroke=None,r=10):self.els.append(('rect',x,y,w,h,fill or self.surface,stroke or self.border,r))
 def button(self,label,x,y,w,h=48,selected=False,enabled=True,size=16):
  self.rect(x,y,w,h,self.surface if enabled else self.border,self.accent if selected else self.border);self.text(label,x+12,y+max(4,(h-round(size*1.32*self.scale))/2),size,True,self.ink if enabled else self.muted,w-24)
  if selected:self.rect(x+w-8,y+4,4,4,self.accent,self.accent,r=2)
 def notes(self,notes):
  self.y+=24;self.flow('Operator notes' if 'audio' in '' else 'Review notes',16,True)
  for note in notes:self.flow(note,color=self.muted,gap=16)
 def save(self,path):
  H=int(self.y+24);im=Image.new('RGB',(self.W,H),self.bg);dr=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{H}" viewBox="0 0 {self.W} {H}"><rect width="100%" height="100%" fill="{self.bg}"/>']
  for e in self.els:
   if e[0]=='rect':
    _,x,y,w,h,fill,stroke,r=e;dr.rounded_rectangle((x,y,x+w,y+h),r,fill=fill,outline=stroke);svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
   else:
    _,x,y,st,size,bold,color=e;font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',size);dr.text((x,y),st,font=font,fill=color);svg.append(f'<text x="{x}" y="{y+size}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(st)}</text>')
  svg.append('</svg>');write(path.with_suffix('.svg'),'\n'.join(svg));path.parent.mkdir(parents=True,exist_ok=True);im.save(path.with_suffix('.png'))

def render(task,case,state,path):
 s=SPEC[task];name,v,events,items,x=state;c=Canvas(task,case);W=c.W;scale=c.scale;c.flow(x['title'],22,True,gap=8);c.flow(x['context'],14,color=c.muted,gap=20)
 if task=='T2':
  bw=(W-40)/2;c.button('Live',16,c.y,bw,48,selected=v['mode']=='live');c.button('Preview',24+bw,c.y,bw,48,selected=v['preview']);c.y+=64;c.flow('Channels',16,True)
  for item in items:
   c.flow(item['name']+(' • Locked' if item['locked'] else ''),16,True,gap=4);c.flow(item['caption'],13,color=c.muted,gap=10)
   yy=c.y;c.button('−',16,yy,48,48,enabled=not item['locked'] and item['level']>0);c.text(str(item['level']),72,yy+8,16,True,width=32);c.button('+',104,yy,48,48,enabled=not item['locked'] and item['level']<x['maxLevel']);c.button('Muted' if item['muted'] else 'Mute',W-106,yy,90,48,selected=item['muted'],enabled=not item['locked'],size=14);c.y+=64
  c.y+=4;my=c.y;mi=len(c.els);c.rect(16,my,W-32,1);c.y+=12;c.y+=c.text(v['summary'],28,c.y,18,True,width=W-56)+8;c.y+=c.text(v['headroom'],28,c.y,14,color=c.muted,width=W-56)+8;c.y+=c.text(v['modeLabel'],28,c.y,14,True,c.accent,width=W-56)+12;c.els[mi]=('rect',16,my,W-32,c.y-my,c.surface,c.border,10);c.y+=16
  if v['warning']:c.flow(v['warningCopy'],14,True,color=c.accent,gap=16)
 else:
  c.flow('Inspection queue',16,True)
  for item in items:
   status='Needs care' if item['status']=='care' else 'Stable' if item['status']=='stable' else 'Pending';label=item['title']+', '+status;h=max(64,round(62*scale));c.button(label,16,c.y,W-32,h,selected=item['id']==v['focus']);c.y+=h+8
  c.y+=12;f=next(o for o in items if o['id']==v['focus']);c.flow('Object inspector',13,True,color=c.accent,gap=8);c.flow(f['title'],20,True,gap=8);c.flow(f['material']+(' • Read only' if not f['editable'] else ''),14,color=c.muted,gap=12);c.flow(f['inspectionNote'],14,color=c.muted,gap=16)
  c.button('Stable',16,c.y,W-32,48,selected=v['stable'],enabled=v['editable']);c.y+=56;c.button('Needs care',16,c.y,W-32,48,selected=v['care'],enabled=v['editable']);c.y+=64
  if v['reasonPresent']:
   c.flow('Care category',14,True,gap=8);c.button('Surface',16,c.y,W-32,48,selected=f['reason']=='surface',enabled=f['editable']);c.y+=56;c.button('Structure',16,c.y,W-32,48,selected=f['reason']=='structure',enabled=f['editable']);c.y+=64
  c.flow(v['summary'],18,True,gap=10);c.flow(v['validation'],14,True,color=c.accent,gap=16)
 c.rect(16,c.y,W-32,56,c.accent if v['ready'] else c.border);c.text(s['primary'],28,c.y+15,16,True,c.actionInk if v['ready'] else c.muted);c.y+=80;c.flow('Operator notes' if task=='T2' else 'Review notes',16,True,gap=12)
 for note in x['notes']:c.flow(note,14,color=c.muted,gap=16)
 c.save(path)

FIELDS={
'T2':dict(request='id:String,title:String,context:String,maxLiveUnits:Int,maxLevel:Int,mode:String,stepperWidth:Double,notes:[String],channels:[BroadcastMixChannel]',item='id:String,name:String,caption:String,level:Int,muted:Bool,locked:Bool'),
'T3':dict(request='id:String,title:String,context:String,focusID:String,queueWidth:Double,notes:[String],objects:[CollectionConditionObject]',item='id:String,title:String,material:String,inspectionNote:String,status:String,reason:String?,editable:Bool,required:Bool')}

def struct(name,fs):
 pairs=[f.split(':',1) for f in fs.split(',')];return 'public struct '+name+': Codable {\n'+''.join(f'    public let {n}: {ty}\n' for n,ty in pairs)+'    public init('+', '.join(f'{n}: {ty}' for n,ty in pairs)+') {\n'+''.join(f'        self.{n} = {n}\n' for n,_ in pairs)+'    }\n}\n'

def api_bridges(task,pub):
 s=SPEC[task];fs=FIELDS[task];callback='(String, String, [BroadcastMixChannel]) -> Void' if task=='T2' else '(String, [CollectionConditionAssessment]) -> Void';kcallback='(String, String, List<BroadcastMixChannel>) -> Unit' if task=='T2' else '(String, List<CollectionConditionAssessment>) -> Unit'
 types=struct(s['item'],fs['item'])+'\n'+struct(s['model'],fs['request'])
 if task=='T3':types+='\n'+struct('CollectionConditionAssessment','id:String,status:String,reason:String?')
 write(pub/'API.md',f'''# {s['name']} public API

Production paths: `alerttoast/Sources/AlertToast/{s['name']}.swift` and `reply/Reply/app/src/main/java/com/example/reply/ui/components/{s['name']}.kt`.

```swift
{types}
public struct {s['name']}: View {{
    public init(request: {s['model']}, onConfirm: @escaping {callback})
    public var body: some View {{ get }}
}}
```

Kotlin package is `com.example.reply.ui.components`. Supply public data classes with the same field names and constructor order. Swift String/Int/Double/Bool map to Kotlin String/Int/Double/Boolean; arrays map to List<T>; String? maps to String?. No required additional parameters.

```kotlin
@Composable
fun {s['name']}(request: {s['model']}, onConfirm: {kcallback})
```

Callbacks contain the current request id and actual local business data, sorted by item id. Mixer callback additionally contains the actual mode. Collection callback contains every object's actual id/status/reason, including optional pending objects. Only enabled confirmation emits a callback. Editing controls never emit confirmation. Caller replacement never emits confirmation and resets local state from the new request on the same mounted component. Do not add expected labels, grading flags or observation state to the production API. All UI/eligibility/derivation logic belongs in production; bridges only decode input and format callback receipts.
''')
 swbody='''{ id, mode, channels in
            let payload = channels.sorted { $0.id < $1.id }.map { "\\($0.id)=\\($0.level)/\\($0.muted ? "true" : "false")" }.joined(separator: ",")
            onEvent("mix:\\(id):\\(mode):\\(payload)")
        }''' if task=='T2' else '''{ id, decisions in
            let payload = decisions.sorted { $0.id < $1.id }.map { "\\($0.id)=\\($0.status)/\\($0.reason ?? "-")" }.joined(separator: ",")
            onEvent("condition:\\(id):\\(payload)")
        }'''
 write(pub/'Bridge.swift',f'''import SwiftUI
import Foundation
import AlertToast

enum ObserverBridge {{
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {{
        let data = try! JSONSerialization.data(withJSONObject: fixture)
        let request = try! JSONDecoder().decode({s['model']}.self, from: data)
        return AnyView({s['name']}(request: request, onConfirm: {swbody}))
    }}
}}
''')
 def kval(n,ty,obj='input'):
  if ty=='String?':return f'{obj}["{n}"]?.jsonPrimitive?.contentOrNull'
  if ty in ['String','Int','Double','Bool']:return f'{obj}["{n}"]!!.jsonPrimitive.'+{'String':'content','Int':'int','Double':'double','Bool':'boolean'}[ty]
  if ty=='[String]':return f'{obj}["{n}"]!!.jsonArray.map {{ it.jsonPrimitive.content }}'
  return f'{obj}["{n}"]!!.jsonArray.map {{ value -> val item = value.jsonObject; {s["item"]}('+', '.join(nn+' = '+kval(nn,tt,'item') for nn,tt in [f.split(':',1) for f in fs['item'].split(',')])+') }'
 args=',\n            '.join(n+' = '+kval(n,ty) for n,ty in [f.split(':',1) for f in fs['request'].split(',')])
 kbody='''{ id, mode, channels ->
            val payload = channels.sortedBy { it.id }.joinToString(",") { "${it.id}=${it.level}/${it.muted}" }
            onEvent("mix:$id:$mode:$payload")
        }''' if task=='T2' else '''{ id, decisions ->
            val payload = decisions.sortedBy { it.id }.joinToString(",") { "${it.id}=${it.status}/${it.reason ?: "-"}" }
            onEvent("condition:$id:$payload")
        }'''
 write(pub/'ObserverBridge.kt',f'''package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*

object ObserverBridge {{
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {{
        val request = {s['model']}(
            {args}
        )
        {s['name']}(request = request, onConfirm = {kbody})
    }}
}}
''')

BUSINESS={
'T2':'''This is a three-channel mixing desk, not a product-choice card. Render a Live/Preview segmented control, followed by a channel ledger in caller order. Each channel row has name, caption, a minus button, numerical level, plus button and Mute/Muted button. Minus/plus change level by exactly one within 0...maxLevel. Locked channels disable all three row controls. Muting retains the stored level. Mode changes retain every level and mute flag. Seeds clamp levels to 0...maxLevel and preserve caller mute/lock flags. Live load sums the level of every unmuted channel; audible count counts unmuted channels with level>0. Headroom is maxLiveUnits minus load and may be negative. The grouped monitor shows `N audible • LOAD / MAX units`, `Headroom: N unit[s]` (singular only when N=1), and Live mode/Preview mode. When load exceeds maxLiveUnits, show a separate warning `Over live limit by N unit[s]`; otherwise that warning node is absent. Apply mix requires at least one audible channel and either preview mode or a load within the live limit. Preview permits applying an overloaded mix but never hides the live-limit warning. Confirmation sends every current channel and mode without resetting local values. Replacement request.id restores every channel level/mute flag and mode from the new caller seed. No nested disclosure is used.''',
'T3':'''This is a master/detail condition-review workflow. Render a vertical three-object inspection queue in caller order, then an inspector for the selected object. Every queue row shows exact accessible label `TITLE, Pending`, `TITLE, Stable` or `TITLE, Needs care`; the active row exposes selected state. Selecting a row changes focus and preserves all object decisions. The inspector shows the focused title, material, long inspectionNote, a Read only indication when editable=false, then vertically stacked Stable and Needs care choices. A Stable decision clears reason. A Needs care decision retains an existing reason only if that object was already care, otherwise starts with no reason. While care is selected, reveal a Care category group with Surface and Structure choices. Only a focused editable care object may change its reason. Read-only records disable classification/reason controls, never queue navigation. Current object seed statuses are pending/stable/care; a care seed may intentionally have an empty reason and needs validation. Ignore a reason unless status is care. Unknown focusID falls back to first object. A complete decision is stable, or care with surface/structure reason. Summary counts all complete objects and all care records: `N of TOTAL reviewed • M follow-up[s]` (singular only when M=1). Submission requires every required object complete; optional pending objects are allowed and included in callback. Validation priority: Choose a care category if any required care record lacks a valid reason; otherwise `N required decision[s] remaining` if any required record is incomplete; otherwise Ready to submit. Confirmation sends all actual decisions without changing focus. Replacement request.id restores all decisions from the new seed and sets focus from the new caller focusID. No item steppers or optional upgrade control are used.'''}

def build(task):
 s=SPEC[task];base=D/task;pub=base/'public';priv=base/'private';pub.mkdir(parents=True,exist_ok=True);priv.mkdir(exist_ok=True);api_bridges(task,pub)
 palette=PALETTES[task]
 write(pub/'BRIEF.md',f'''# {s['name']}

Build the production native component using API.md. This independent task was selected before any implementation or candidate rendering. Parent host owns padding16 horizontally, top24 and a600-unit native ScrollView viewport. Do not add duplicate outer padding or nested vertical scrolling. Only the production component may implement UI, state, conditional validation, derived values or business callbacks. Do not modify an existing app screen/build configuration to substitute this UI.

## Composition and business workflow

{BUSINESS[task]}

All supplied long note paragraphs appear in order below the primary action under {'Operator notes' if task=='T2' else 'Review notes'}. Assign the heading identifier `{s['prefix']}.notes`. Title and context use caller values. Primary label is `{s['primary']}`. Native controls expose exact unique identities from bindings.json, real disabled state and selected semantics for selected modes, muted controls, active queue rows and classification/reason choices. Native selected trait: SwiftUI accessibility selected trait; Compose selectable semantics. Keep dedicated text nodes for title, current level/summary, focused title and inspection note where present. Do not nest a native OnClick inside another OnClick control.

## Native style and geometry

Title system sans22 weight700; context/body/notes14 regular; row names16 weight600; row captions13 regular; numerical level16 weight600; mixer mute button14 weight600; monitor/summary18 weight600; inspector title20 weight600; primary16 weight600. iOS scales base fonts relative to Dynamic Type; Android uses sp under caller fontScale. Native title22sp/700/color measurements on Android are exact. Generic iOS computed style stays U and is visually judged separately. Wrap notes, labels, summaries and inspection text; never truncate them.

Light roles canvas/surface/ink/muted/accent/border/primary-ink: {', '.join(palette['light'])}. Dark roles: {', '.join(palette['dark'])}. Surfaces radius10 and internal inset12; major sections16 gap, title/context8, stacked controls8. Selected controls use accent border and a visible selected marker; disabled controls use border fill and muted text. Ordinary controls use surface fill. Primary uses accent fill when enabled and border fill when disabled. Do not replace system fonts with an export font.

{'Row controls: the minus and plus native accessible button boxes are exactly request.stepperWidth by48 (fixtures48); counter allocation40; right Mute/Muted allocation90. Stack channel name/caption above its control strip at both widths; each row grows naturally for scaled text. The monitor is a full-width grouped surface with its three text lines, followed by the conditional overload banner and primary action. Segments have minimum height48 and divide available width with gap8. The primary accessible control has exact height56.' if task=='T2' else 'Queue rows use exact request.queueWidth (fixtures358 at390,288 at320), minimum height64 and grow for scaled wrapping. Inspector and decisions follow the queue vertically. Stable and Needs care controls span content width with minimum height48 and may grow; conditional Surface and Structure controls have exact accessible height48 and span content width. Primary has exact accessible height56. The Care category heading has identifier condition.reasonGroup, with the two choices as sibling buttons below it. The group heading is absent whenever focused status is not care.'}

P1 offered width390/light/normal type. P2 width320/dark/xxxLarge (Android1.6). H1 is another ordinary caller combination under these same rules. Every case starts with an original loaded full-content sweep, includes real native taps, updates the caller fixture on the same mounted component, and ends with a replaced full-content sweep. There are exactly two explicit sweeps. allow_disabled means an actual disabled observation is permitted; callback behavior remains U unless dispatch succeeds. See cases/<case>/expected-states.json for every selected-state expected value. The {'care-marked action is an unselected intermediate state before the selected reasoned state; its actual action route remains fixed.' if task=='T3' else 'leveled state can be blocked at maxLevel; this does not establish a successful callback interval.'}

Reference SVG/PNG sets show loaded and {'muted' if task=='T2' else 'reasoned'} states, including full long content. Reference exports use Arial as a stand-in for native SF/Roboto; do not require pixel identity. Check actual native metrics and the visual scope in STYLE-PRECISION.md. Builders must compile their own plans from public typed contract/lock/approval/bindings/actions and must not read public/compiled or private material. There are no hidden business requirements or deliberate production defects.
''')
 write(pub/'STYLE-PRECISION.md','''# Independent measurement policy

Accessible native control boxes are intentional measurement targets. No assertion claims effective framework padding, glyph-ink bounds, physical hit regions or an invisible allocation. Primary height56 fits the concise large-text primary label. The mixer stepper width48 is a deliberate discrete-level control allocation; the collection queue width is explicitly caller-offered width minus host horizontal padding32. Collection care-category control height48 fits each short large-text label. Geometry uses near0.75 pt/dp, independently selected before SDK feedback to permit subpixel AX serialization and density rounding below one layout unit. All other native typography, ARGB color, weight and ellipsis values use exact equality with no tolerance.

Android title font_sp22 and font_weight700 are base text-layout values under the caller font scale; ink is exact packed ARGB. iOS generic SwiftUI font/color/weight/ellipsis are unexposed by the collector and remain U. Visual judgments separately assess complete readable hierarchy, selected/disabled appearance, palette roles, wrapping, all note paragraphs and absence of overlaps/clipping. loaded/replaced full-layout passes require original complete state sweep evidence. Other selected states are scoped to actually captured target regions and must preserve offscreen uncertainty. Visual P cannot replace native_style U.
''')
 rules=[]
 for rid,kind,target,prop in s['rules']:
  rule=dict(id=rid,kind=kind)
  if target:rule['target']=target
  if prop:rule['property']=prop
  if kind=='geometry':rule.update(op='near',basis='control',measurement='accessibility_box')
  if rid=='replacement-callback':rule['stimulus']='caller_update'
  if kind=='manual':rule.update(allowed_methods=['visual'],coverage='target')
  rules.append(rule)
 logical={r['target'] for r in rules if 'target' in r}|{a['target'] for a in route(task) if 'target' in a}
 bindings={k:dict(identifier=s['prefix']+'.'+k) for k in sorted(logical)};write(pub/'bindings.json',bindings)
 actionIndices=[0,1,2,3,4,6] if task=='T2' else [0,2,3,4,5,7];updateIndex=5 if task=='T2' else 6
 refdoc=dict(geometry={p:dict(primary_height=typed(56,u),stepper_width=typed(48,u),queue_normal=typed(358,u),queue_narrow=typed(288,u),care_height=typed(48,u),tolerance=typed(.75,u)) for p,u in [('ios','pt'),('android','dp')]},native_style=dict(font=typed(22,'sp'),weight=typed(700,'scalar'),light_ink=typed(s['lightInk'],'argb'),dark_ink=typed(s['darkInk'],'argb'),no_ellipsis=typed(False,'bool')),scenarios={})
 scenarios={}
 for case in ['P1','P2','H1']:
  root=priv if case=='H1' else pub;cp=root/'cases'/case;x=s['fixture'](case);env=dict(initial=x,updates=[s['fixture'](case,True)],width=320 if case=='P2' else 390,theme='dark' if case=='P2' else 'light',dynamic_type='xxxLarge' if case=='P2' else 'large',fontScale=1.6 if case=='P2' else 1.,direction='ltr',canvas_color=palette['dark' if case=='P2' else 'light'][0],viewportHeight=600,max_scrolls=24,state_capture=True,required_identifiers=[s['prefix']+'.primary',s['prefix']+'.notes']);write(cp/'fixtures.json',env)
  acts=route(task);bound=copy.deepcopy(acts)
  for a in bound:
   if 'target' in a:a['target']=bindings[a['target']]
  write(cp/'actions.json',bound);records=s['states'](case);write(cp/'expected-states.json',{n:dict(v,callback_delta=e) for n,v,e,items,inp in records})
  states=[dict(id=rec[0],input_index=1 if rec[0]=='replaced' else 0,after_action=i,coverage='full_content' if rec[0] in ['loaded','replaced'] else 'targets',**({'stimulus_action':updateIndex} if rec[0]=='replaced' else {})) for rec,i in zip(records,actionIndices)]
  values={r['id']:{} for r in rules};sourceStates={}
  for name,v,e,items,inp in records:
   sourceStates[name]={}
   for r in rules:
    rid=r['id'];datum=None;unit='string';special=None
    if rid in s['mapping']:
     datum=v[s['mapping'][rid]];unit='bool' if isinstance(datum,bool) else 'string'
     if (rid=='overload-copy' and not v['warning']) or (rid=='surface-category-selected' and not v['reasonPresent']):special='Conditional control/text is absent in this focused business state; its presence is independently asserted.'
    elif r['kind']=='geometry':
     key={'primary-height':'primary_height','stepper-width':'stepper_width','queue-width':'queue_narrow' if case=='P2' else 'queue_normal','care-control-height':'care_height'}[rid]
     if rid=='care-control-height' and not v['reasonPresent']:special='Care category control is absent unless focused status is care.'
     else:
      special={p:dict(source='reference',pointer=f'/geometry/{p}/{key}') for p in ['ios','android']};special['tolerance']={p:dict(source='reference',pointer=f'/geometry/{p}/tolerance') for p in ['ios','android']}
    elif r['kind']=='text_layout':
     key={'title-font-size':'font','title-font-weight':'weight','title-ink':'dark_ink' if case=='P2' else 'light_ink','summary-wrap':'no_ellipsis','inspector-wrap':'no_ellipsis'}[rid];special={p:dict(source='reference',pointer='/native_style/'+key) for p in ['ios','android']}
    elif rid=='activation-callback':
     if name in ['loaded','replaced']:special='No user activation is the selected stimulus for this state.'
     else:datum=e;unit='events'
    elif rid=='replacement-callback':
     if name!='replaced':special='Caller replacement is not this selected stimulus.'
     else:datum=[];unit='events'
    elif r['kind']=='manual':datum=f'{case}/{name}: composition, all palette/font roles, readable wrapping, native selected/disabled appearance and long content per brief/references. Non-sweep states cover captured target regions only.'
    if isinstance(special,str):values[rid][name]=dict(not_applicable=special)
    elif isinstance(special,dict):values[rid][name]=special
    else:
     sourceStates[name][rid]=typed(datum,unit);expr=dict(source='reference',pointer=f'/scenarios/{case}/{name}/{rid}');values[rid][name]=dict(ios=expr,android=expr)
  refdoc['scenarios'][case]=sourceStates;scenarios[case]=dict(states=states,actions=acts,values=values)
  for record in [records[0],records[3] if task=='T2' else records[1]]:render(task,case,record,root/'references'/f'{case}-{record[0]}')
 for visibility,cases in [('public',['P1','P2']),('private',['H1'])]:
  root=base/visibility;ref=copy.deepcopy(refdoc);ref['scenarios']={c:refdoc['scenarios'][c] for c in cases};write(root/'reference.json',ref)
  contract=dict(version=1,design_owner='Independent blind design-v2 context',approval_reference='approval.json; frozen before all six implementations',sources=[dict(id='reference',path='reference.json',sha256=sha(root/'reference.json'))],required_rule_ids=[r['id'] for r in rules],rules=rules,scenarios={c:scenarios[c] for c in cases});write(root/'contract.json',contract)
  if visibility=='private':write(root/'bindings.json',bindings)
  lock=dc.seal(root/'contract.json',root);write(root/'design-lock.json',lock);digest=dc.digest(lock);write(root/'approval.json',dict(design_lock_sha256=digest,approved_at_unix=time.time(),owner='Independent blind design-v2 context',basis='Business/native style reference fixed with no implementation, candidate rendering or suspected defect.',scope=cases))
  for case in cases:
   dest=root/'compiled'/case;write(dest/'fixtures.json',read(root/'cases'/case/'fixtures.json'))
   for platform in ['ios','android']:
    plan,enriched=dc.compile_contract(lock,digest,case,platform,bindings,read(root/'cases'/case/'actions.json'));write(dest/platform/'plan.json',plan);write(dest/platform/'actions.json',enriched);write(dest/f'actions.{platform}.json',enriched)
 table=[]
 for case in ['P1','P2','H1']:
  root=priv if case=='H1' else pub
  for platform in ['ios','android']:
   plan=read(root/'compiled'/case/platform/'plan.json');checks={a['id']:a for a in plan['assertions']}
   for cell in plan['matrix_contract']['cells']:
    rule=next(r for r in rules if r['id']==cell['requirement_id']);a=checks.get(cell['id'],{});cl={'control':'business_current','event':'business_transition','geometry':'geometry','text_layout':'native_style','manual':'visual'}[rule['kind']]
    table.append(dict(id=f'{case}/{platform}/{cell["id"]}',case=case,platform=platform,state=cell['state'],requirement=cell['requirement_id'],aspect=rule.get('property',rule['kind']),**{'class':cl},applicable=cell['disposition']=='required',reason=cell.get('reason','Required by the independent business/style brief'),expected=a.get('expected'),unit=a.get('unit'),op=a.get('op','eq'),tolerance=a.get('tolerance'),plan_assertion_id=cell['id']))
 write(priv/'acceptance-table.json',dict(version=1,rows=table,total_cells=len(table),scope='Complete rule × state × platform × case denominator, including explicit N/A and unmeasurable applicable U.'))
 write(priv/'grader.py','''from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from oracle_common import grade_task, match_claims, compare_pair

def grade(case, platform, observation_path, root=None, manual=None, source_root=None, api_review=None):
    return grade_task(Path(__file__).resolve().parents[1], case, platform, observation_path, root, manual, source_root, api_review)
''')
 print(task,len(rules),len(table),read(pub/'approval.json')['design_lock_sha256'])

if __name__=='__main__':
 for task in ['T2','T3']:build(task)
 write(D/'COMPILER-REVISIONS.json',dict(errors=[],revisions=[],scope='Original cohort untouched. Both new tasks authored from domain/workflow requirements before implementation.'))
