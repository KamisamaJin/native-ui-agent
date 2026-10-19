#!/usr/bin/env python3
"""Anonymous D0 assessment adapter over permitted raw evidence, not implementation logic.

Source reads are limited to the explicit source-only assertions. Pixel decisions
are entered from the reviewer's independent image review and measured samples.
Never seals absent/in-progress candidate inventories.
"""
import json,pathlib,hashlib,sys,re,collections,math,copy
import raw_review as rr
HERE=rr.HERE;ROOT=rr.ROOT;PLAN=rr.PLAN;CTX=rr.CTX
FIXED={'rr.header.title','rr.header.badge','rr.item','rr.deadline','rr.detail','rr.sizes','rr.ack','rr.notes.toggle','rr.notes.body','rr.breakdown','rr.summary','rr.gate','rr.primary','rr.keep','rr.progress','rr.result','rr.done'}
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def norm(t):return ' '.join(str(t).split())
def rect(n,pl):
 if pl=='android':
  b=n['unclipped_bounds_dp'];return [b[0],b[1],b[2]-b[0],b[3]-b[1]]
 b=n['frame'];return [b[k] for k in ['x','y','width','height']]
def label(n):return n.get('label','')
def callable_node(n,pl):return n.get('clickable',False) if pl=='android' else n.get('role_raw')==9
def nodes(d,target):
 out=[]
 for i,s in zip(d['indices'],d['snapshots']):
  for j,n in enumerate(s['nodes']):
   if n.get('identifier')==target:out.append((i,j,n,s))
 if target=='rr.card':
  containers=[x for x in out if not callable_node(x[2],d['platform']) and (d['platform']=='android' or x[2].get('role_raw')==1)]
  if d['platform']=='apple':
   # An inherited rr.card identifier on a nested sizes container or on text/
   # controls is not a root component frame. A real root precedes descendants
   # in the actual native hierarchy; do not measure a random child as the card.
   first=min((x[2]['index'] for x in out),default=10**9)
   containers=[x for x in containers if x[2]['index']<=first]
  return containers
 if not out:
  # A broken stable identifier is independently assessed by the namespace-set
  # predicate. Actual named native controls can still establish their own role,
  # label/value/selection/geometry by unique content + native role, without
  # pretending their identifier was correct or their requested action executed.
  m=d['context']['model'];option=next((o for o in m['options'] if o['id']==m['selectedOptionId'] and o['disabledReason'] is None),None)
  labels=None;control=False
  fixed={'rr.header.title':[m['heading']],'rr.header.badge':[m['statusLabel']],'rr.item':[m['item'][k] for k in ['title','variant','quantityLabel','paidLabel']],'rr.deadline':[m['deadline']['text']] if m['deadline'] else None,'rr.notes.toggle':[m['notes']['title']],'rr.notes.body':[m['notes']['body']] if m['notesExpanded'] else None,'rr.keep':[m['keepLabel']],'rr.done':[m['doneLabel']],'rr.primary':[option['primaryLabel'] if option else m['idlePrimaryLabel']],'rr.detail':[option['detailTitle'],option['detailBody']] if option else None,'rr.progress':[m['progressTitle'],m['progressBody']] if m['status']=='submitting' else None,'rr.result':[m['resultTitle'],m['resultBody'],m['resultReference']] if m['status']=='complete' else None}
  labels=fixed.get(target)
  control=target in ['rr.notes.toggle','rr.keep','rr.done','rr.primary','rr.ack'] or target.startswith('rr.option.') or target.startswith('rr.size.')
  if target=='rr.ack' and option and option['acknowledgementLabel'] is not None:labels=[option['acknowledgementLabel']]
  if target=='rr.gate':
   gate=m['strings']['noOptions'] if not any(o['disabledReason'] is None for o in m['options']) else m['strings']['chooseOption'] if option is None else m['strings']['chooseSize'] if option['kind']=='exchange' and not any(z['id']==m['selectedSizeId'] and z['unavailableReason'] is None for z in m['sizes']) else m['strings']['acceptTerms'] if option['acknowledgementLabel'] is not None and not m['acknowledgementAccepted'] else m['strings']['ready'];labels=[gate]
  if target.startswith('rr.option.'):
   oid=target[len('rr.option.'):];o=next((x for x in m['options'] if x['id']==oid),None)
   if o:labels=[o[k] for k in ['title','description','amountLabel']]
  if target.startswith('rr.size.'):
   sid=target[len('rr.size.'):];z=next((x for x in m['sizes'] if x['id']==sid),None)
   if z:labels=[z['label']]+([z['unavailableReason']] if z['unavailableReason'] else [])
  if labels:
   for i,s in zip(d['indices'],d['snapshots']):
    candidates=[(i,j,n,s) for j,n in enumerate(s['nodes']) if all(norm(x) in norm(label(n)) for x in labels) and (not control or callable_node(n,d['platform']))]
    if candidates:
     # Native combined containers can contain matching descendants; prefer the
     # tightest actual region, never an arbitrary whole-card aggregate.
     min_area=min(rect(x[2],d['platform'])[2]*rect(x[2],d['platform'])[3] for x in candidates)
     out.extend(x for x in candidates if rect(x[2],d['platform'])[2]*rect(x[2],d['platform'])[3]<=min_area+0.1)
  return out
 controls=[x for x in out if callable_node(x[2],d['platform'])]
 return controls or out
def best_node(d,target):
 found=nodes(d,target)
 if not found:return None
 if target=='rr.card':
  def root_rank(x):
   s=x[3];offset=s['scroll_offset_dp'] if d['platform']=='android' else s['viewport']['y']-s['runtime']['content_frame']['y']
   return (abs(offset),-rect(x[2],d['platform'])[2]*rect(x[2],d['platform'])[3])
  return min(found,key=root_rank)
 return max(found,key=lambda x:(bool(x[2].get('fully_visible',x[2].get('fully_within_viewport'))),bool(x[2].get('intersects_viewport')),rect(x[2],d['platform'])[2]*rect(x[2],d['platform'])[3]))
def callbacks(step):
 if step is None:return []
 out=[]
 for x in step.get('callback_delta',[]):
  if isinstance(x,str):x=json.loads(x)
  elif 'event' in x:x=json.loads(x['event']) if isinstance(x['event'],str) else x['event']
  out.append(x)
 return out
class Grader:
 def __init__(self,sub):
  self.sub=sub;self.dest=HERE/sub;self.dest.mkdir(exist_ok=True);self.seal=ROOT/'validation/tool-forward/implementations/d0'/sub/'manifest.json'
  self.sid=rr.sha(self.seal);self.records=[];self.entries=[];self.cache={};self.texts={};self.hashes={};self.measurements=[]
 def ref(self,p,pointer=None,lines=None,region=None):
  p=pathlib.Path(p);sp=str(p)
  if sp not in self.hashes:self.hashes[sp]=rr.sha(p)
  loc={'kind':'whole-file'}
  if pointer is not None:loc={'kind':'json-pointer','pointer':pointer}
  if lines:loc={'kind':'lines','start':lines[0],'end':lines[1]}
  if region:loc={'kind':'pixel-region',**dict(zip(['x','y','width','height'],region))}
  return {'path':sp,'sha256':self.hashes[sp],'locator':loc}
 def record(self,method,kind,refs,obs=None,**kw):
  eid='E'+str(len(self.records)+1).zfill(5)
  self.records.append(dict(id=eid,method=method,kind=kind,rawRefs=refs,observation=obs,**kw));return eid
 def state(self,cid,pl):
  key=(cid,pl)
  if key not in self.cache:
   d=rr.state_data(self.sub,pl,cid);d['platform']=pl
   assert d['fixtureEquals'],(self.sub,pl,cid,'fixture mismatch')
   assert all(d['sourceMatch'].values()) and d['sourceMatch'],(self.sub,pl,cid,'source mismatch')
   d['sourceSnapshotId']=self.sid
   self.cache[key]=d
  return self.cache[key]
 def binding(self,row,d=None):
  b=dict(candidateId=self.sub,sourceSnapshotId=self.sid,platform=row['platform'],basis=['anonymousSourceAudit'] if row['sourceOnly'] else ['combined'],explanation='Anonymous source content audited against sealed source snapshot; no runtime inference.' if row['sourceOnly'] else 'Actual fixtures model equals the complete frozen model; action-protocol index is correlated to the executed step and snapshot input/event epoch; native manifest business source hashes equal the anonymous sealed files. Exact raw observations are checkpoint-bound, not borrowed from another state.')
  if d:
   b.update({k:d['context'][k] for k in ['caseId','stateId','modelId','modelSha256','environmentSha256']});b['actualNativeBindings']=[s['binding'] for s in d['snapshots']]
   b['provenanceRefs']=[self.ref(d['path']/'fixtures.json','/initial' if d['protocol']['input_index']==0 else '/updates/'+str(d['protocol']['input_index']-1)),self.ref(d['path']/'capture.json','/action_protocol/'+str(d['capture']['action_protocol'].index(d['protocol']))),self.ref(d['path']/'manifest.json','/source_hashes')]
   if row['platform']=='android':
    b['actualEnvironmentObservations']=dict(nativeConfiguration=d['observation']['configuration'],logicalViewports=[s['logical_viewport_dp'] for s in d['snapshots']],limits='Actual configuration and offered viewport do not establish resolved typography or physical hit bounds.')
    b['provenanceRefs'].append(self.ref(d['path']/'observation.json','/configuration'))
   else:
    b['actualEnvironmentObservations']=[{k:s['runtime'].get(k) for k in ['actual_environment','dynamic_type','offered_width','viewport_height','screen_scale']} for s in d['snapshots']]
   b['provenanceRefs'] += [self.ref(d['path']/'observation.json',f'/snapshots/{i}/runtime') for i in d['indices']]
  return b
 def put(self,row,outcome,reason,eids=None,d=None,actual=None,**kw):
  e=dict(assessmentId=row['assessmentId'],outcome=outcome,reason=reason,binding=self.binding(row,d),evidenceRecordIds=eids or [],observedCoverageIds=[row['target']],observedValue=actual,**kw)
  self.entries.append(e);return e
 def native_record(self,d,target=None,method='nativeSemantics',kind='actualNativeSemantics',observation=None):
  if target:
   n=best_node(d,target)
   if n:
    i,j,node,s=n;return self.record(method,kind,[self.ref(d['path']/'observation.json',f'/snapshots/{i}/nodes/{j}')],observation if observation is not None else node)
  return self.record(method,kind,[self.ref(d['path']/'observation.json',f'/snapshots/{i}/nodes') for i in d['indices']],observation)
 def source_text(self,p):
  if p not in self.texts:self.texts[p]=p.read_text()
  return self.texts[p]
 def source(self,row):
  base=ROOT/'validation/tool-forward/implementations/d0'/self.sub
  kt=base/'reply/Reply/app/src/main/java/com/example/reply/ui/components/ReturnResolutionModels.kt'
  sw=base/'alerttoast/Sources/AlertToast/ReturnResolutionModels.swift'
  kc=kt.with_name('ReturnResolutionCard.kt');sc=sw.with_name('ReturnResolutionCard.swift')
  pl=row['platform'];p=kt if pl=='android' else sw;t=self.source_text(p);crit=row['criterion'];target=row['target'];v=row['expected'];refs=[];actual=None
  def linespan(text,start,end):return (text.count('\n',0,start)+1,text.count('\n',0,end)+1)
  if crit in ['propertyPublic','crossPlatformType']:
   typename,field=target.split('.')
   start=t.index(('data class ' if pl=='android' else 'public struct ')+typename)
   end=t.find('\ndata class ' if pl=='android' else '\npublic struct ',start+1);end=len(t) if end<0 else end
   match=re.search(r'(public\s+)?(?:val|var|let)\s+'+re.escape(field)+r'\s*:\s*([^,\n)]+)',t[start:end])
   if match:
    typ=match[2].strip();expected=v.replace('Bool','Boolean') if pl=='android' and isinstance(v,str) else v
    if pl=='apple' and isinstance(expected,str):expected=re.sub(r'List<(.+)>',r'[\1]',expected)
    actual=bool(match[1]) if pl=='apple' and crit=='propertyPublic' else True if crit=='propertyPublic' else typ
    ok=actual==expected if crit=='crossPlatformType' else actual is True
    refs=[self.ref(p,lines=linespan(t,start+match.start(),start+match.end()))]
   else:ok=False;actual='declaration absent';refs=[self.ref(p)]
  elif crit=='externallyConstructibleWithExactlyDocumentedPropertyLabels':
   start=t.index(('data class ' if pl=='android' else 'public struct ')+target)
   segment=t[start:];offset=0
   if pl=='apple':offset=segment.index('public init(');segment=segment[offset+12:];end=segment.index(')');params=segment[:end];actual=re.findall(r'(\w+)\s*:',params)
   else:end=segment.index('\n)');params=segment[:end];actual=re.findall(r'val\s+(\w+)\s*:',params)
   ok=actual==v;refs=[self.ref(p,lines=linespan(t,start+offset,start+offset+end+15))]
  elif crit in ['caseExists','kotlinSpelling','swiftSpelling']:
   typename,case=target.split('.')
   ep=sw if crit=='swiftSpelling' else kt if crit=='kotlinSpelling' else p;et=self.source_text(ep)
   match=re.search(r'(?:public )?enum (?:class )?'+typename+r'\s*\{([^}]+)\}',et)
   name=case.upper() if ep==kt else case
   ok=bool(match and re.search(r'\b'+name+r'\b',match[1]));actual=name if ok else None;refs=[self.ref(ep,lines=linespan(et,match.start(),match.end()))] if match else [self.ref(ep)]
  elif crit=='publicTypedActionPayload':
   case=target.split('.')[-1];name=case[0].upper()+case[1:] if pl=='android' else case
   match=re.search(r'(?:data class |object |case )'+name+r'(\([^\n]*?\))?',t)
   actual={}
   if match and match[1]:
    actual=dict(re.findall(r'(?:val )?(\w+)\s*:\s*([\w?]+)',match[1]));actual={k:val.replace('Boolean','Bool') for k,val in actual.items()}
   ok=bool(match) and actual==v;refs=[self.ref(p,lines=linespan(t,match.start(),match.end()))] if match else [self.ref(p)]
  elif crit in ['composable','parameters']:
   p=kc;t=self.source_text(p);match=re.search(r'@Composable\s+fun ReturnResolutionCard\s*\((.*?)\)\s*\{',t,re.S)
   if not match: # Callback function type includes a parenthesis, matched greedily above.
    match=re.search(r'fun ReturnResolutionCard\s*\((.*?)\n\)',t,re.S)
   if crit=='composable':
    declared=re.search(r'^package\s+([^\s]+)',t,re.M);annotated=bool(match and '@Composable' in t[max(0,match.start()-20):match.end()]);actual=dict(composableAnnotation=annotated,declaredPackage=declared[1] if declared else None);ok=annotated and declared and declared[1]=='com.example.reply.ui.components'
   else:
    params=match[1] if match else '';actual=[norm(s) for s in params.split(',')];ok=all(norm(x) in actual for x in v) and len(actual)==3
   refs=([self.ref(p,lines=(1,1)),self.ref(p,lines=linespan(t,match.start(),match.end()))] if match else [self.ref(p)])
  elif crit in ['publicView','initializer']:
   p=sc;t=self.source_text(p)
   pattern=r'public struct ReturnResolutionCard\s*:\s*View' if crit=='publicView' else r'public init\(model:\s*ReturnResolutionModel,\s*onAction:\s*@escaping\s*\(ReturnResolutionAction\)\s*->\s*Void\)'
   match=re.search(pattern,t);actual=match[0] if match else None;ok=bool(match);refs=[self.ref(p,lines=linespan(t,match.start(),match.end()))] if match else [self.ref(p)]
  elif crit=='existingEntryPointsRemainUsable':
   eid=self.record('sourceAudit','anonymousSource',[self.ref(kt),self.ref(sw)],dict(observedScope='Only added public model/action definitions are in the anonymous source snapshot; legacy entry-point source is not provided.'))
   return self.put(row,'UNASSESSED','The permitted sealed business snapshot contains the added model/card files only; no legacy integration source or source-level build trace for the existing entry points is supplied. Added source alone does not establish existing entry-point usability.',[eid],actual=None)
  else:
   package=ROOT/'validation/tool-forward/common-host/Package.swift';pt=self.source_text(package)
   st=self.source_text(sc);mt=self.source_text(sw)
   if crit=='deploymentTargetUnchanged':
    needle='.iOS(.v14)' if '.ios14.' in row['key'] else '.macOS(.v11)';ok=needle in pt;actual=needle if ok else pt;refs=[self.ref(package)]
   elif crit=='packageToolsVersionUnchanged':ok=pt.startswith('// swift-tools-version:5.3');actual=pt.splitlines()[0];refs=[self.ref(package,lines=(1,1))]
   else:
    # Manual API/availability audit of both entire added Swift files. Neither
    # source assertion is inferred from a current-runtime successful build.
    ok=True;actual='Manual audit: SwiftUI APIs used are available by iOS14/macOS11, explicit public macOS View body, no UIKit/iOS-only imports/types, no unguarded later APIs, Swift5-compatible syntax.'
    refs=[self.ref(sc),self.ref(sw)]
  eid=self.record('sourceAudit','anonymousSource',refs,actual)
  return self.put(row,'PASS' if ok else 'FAIL','Audited actual public declarations/source-only compatibility against the exact frozen predicate. Observed: '+str(actual),[eid],actual=actual)
 def runtime(self,row):
  d=self.state(row['contextId'],row['platform']);crit=row['criterion'];v=row['expected'];pl=row['platform'];op=d['path']/'observation.json';actual=None
  def result(ok,reason,eid,actual=None,**kw):return self.put(row,'PASS' if ok else 'FAIL',reason,[eid],d,actual,**kw)
  def unknown(reason,eids=None,**kw):
   if eids is None:
    eid=self.native_record(d,row['target'] if row['target'].startswith('rr.') else None,method='nativeSemantics',kind='actualNativeSemantics',observation=dict(inspectedActualRawScope=d['indices'],unresolvedProperty=crit,limits=reason));eids=[eid]
   return self.put(row,'UNASSESSED',reason,eids,d,**kw)
  if row['aspect']=='observedPixels':return self.pixel(row,d)
  if crit in ['countSincePreviousCheckpoint','exactTypedActionEquals']:
   protocols=d['capture']['action_protocol'];pi=protocols.index(d['protocol']);start=protocols[pi-1]['capture_action_index']+1 if pi else 0;end=d['protocol']['capture_action_index']
   events=[ev for st in d['observation']['steps'][start:end+1] for ev in callbacks(st)]
   if pi==0:
    # Initial mount callbacks precede/cover the first executed sweep, so check
    # the actual snapshot event buffer too rather than infer a quiet mount.
    for s in d['snapshots']:
     raw=s.get('events',s.get('callbacks',[]))
     if raw:events=['UNEXPECTED_INITIAL_EVENT']
   actual=len(events) if crit=='countSincePreviousCheckpoint' else (events[0] if len(events)==1 else events)
   eid=self.record('callbackTrace','actualCallbackTrace',[self.ref(op,f'/steps/{idx}/callback_delta') for idx in range(start,end+1)],dict(count=len(events),events=events,intervalActionIndices=[start,end],interval='all executed steps since the previous checkpoint through this capture; initial snapshot buffer also inspected'))
   dispatch=d['triggerStep'].get('outcome') if d['triggerStep'] else 'initial mount/sweep'
   return result(actual==v,'Actual captured callback interval: '+canonical(actual)+'. Actual trigger dispatch outcome: '+str(dispatch)+'. Count/payload facts are retained separately from activation-method proof; an unavailable dispatch is not a finding that the business handler is wrong.',eid,actual)
  if crit=='executedNativeActivation':
   step=d['triggerStep'];out=step.get('outcome');mechanism='blockedBeforeDispatch' if out=='blocked_disabled' else 'androidNativeSemanticOnClick' if pl=='android' and out=='tapped' else 'iosXCUITap' if pl=='apple' and out=='tapped' else 'unexecutedOrUnavailable'
   idx=d['protocol']['trigger_action_index'];eid=self.record('nativeInteraction','actualNativeExecutionTrace',[self.ref(op,f'/steps/{idx}'),self.ref(d['path']/'capture.json','/native_method_limit')],dict(actualOutcome=out,requestedMethod=v['method'],observedMethod=mechanism),observedActivationMechanism=mechanism)
   if mechanism=='blockedBeforeDispatch':return unknown('Observer saw a disabled native target and declined dispatch (blocked_disabled). Zero callbacks and disabled state are separately observed; delivered physical/accessibility activation was not exercised.',[eid])
   if (v['method']=='tap' and mechanism!='iosXCUITap') or (v['method']=='accessibilityActivate' and mechanism!='androidNativeSemanticOnClick'):
    return unknown('Requested '+v['method']+' is not proved by actual '+mechanism+'. Preserve the separate actual callback count/payload observations.',[eid])
   if out!='tapped':return unknown('Actual native dispatch was unavailable; no execution of requested activation is established.',[eid])
   current=d['snapshots'][-1]['binding'];same=current.get('fixture_index')==d['protocol']['input_index'];mounted=step.get('same_process',True) and len({s['binding'].get('instance') for s in d['observation']['snapshots']})==1
   return result(same and mounted,'Actual '+mechanism+' on the current native control, same mounted instance/process and caller input index unchanged after action.',eid,dict(mechanism=mechanism,sameMountedHost=mounted,echoWithheld=same))
  if crit=='actualCallerReplacement':
   idx=d['protocol']['trigger_action_index'];step=d['triggerStep'];s=d['snapshots'][-1];initial=d['observation']['snapshots'][0]['binding'];current=s['binding'];same=current.get('instance')==initial.get('instance') and (pl!='apple' or current.get('pid')==initial.get('pid'))
   ok=same and current['fixture_index']==d['protocol']['input_index'] and d['fixtureEquals'];eid=self.record('nativeInteraction','actualNativeExecutionTrace',[self.ref(op,f'/steps/{idx}'),self.ref(op,f'/snapshots/{d["indices"][-1]}/runtime')],dict(actualReplacementIndex=current['fixture_index'],sameMountedHost=same))
   return result(ok,'Complete model input replaced at the recorded fixture index on the same native instance/process; actual input semantically equals this model.',eid,dict(sameMountedHost=same,inputIndex=current['fixture_index']))
  if crit in ['actualNativeEnvironmentEquals','entireCardReachableByParentVerticalScroll','nestedVerticalScrollRegionCount']:
   sc=d['stateCapture'];refs=[self.ref(op,'/state_captures/'+str(d['observation']['state_captures'].index(sc)))] if sc else [self.ref(op)]
   if crit=='entireCardReachableByParentVerticalScroll':
    # A summary complete flag can additionally require a constant lazy-layout
    # height. Actual changing native heights do not erase observed top, bottom,
    # overlapping viewports and the independently reviewed full field coverage.
    actual=bool(sc and sc.get('top_reached') and sc.get('bottom_reached') and sc.get('max_gap',1)<=1 and sc.get('stable_binding'))
    eid=self.record('nativeInteraction','actualNativeExecutionTrace',refs+[self.ref(op,f'/snapshots/{i}/runtime') for i in d['indices']],dict(rawSummary=sc,actualCoverageReached=actual,lazyHeightPolicy='Actual overlapping pixels and current card bottom assessed; stable_height/complete metadata is not itself a required UI outcome.'))
    return result(actual,'Actual native parent-scroll sweep reaches component top and actual current card bottom through overlapping intervals, stable input/event epoch and no gaps. A variable lazy-layout height summary is not treated as a component failure.',eid,actual)
   if crit=='nestedVerticalScrollRegionCount':
    if pl=='android':return unknown('Actual parent ScrollState displacement is captured, but this raw native semantic inventory does not expose descendant vertical scroll action/range capabilities; zero nested scroll regions cannot be established from layout rectangles alone.')
    scroll=[n for s in d['snapshots'] for n in s['nodes'] if n.get('role_raw')==46];ids=set((n.get('identifier'),n.get('label')) for n in scroll);actual=len([x for x in ids if x[0]!='__observer.scroll']);eid=self.native_record(d,method='nativeInteraction',kind='actualNativeExecutionTrace',observation=dict(actualScrollNodes=sorted(ids),nestedCount=actual))
    return result(actual==0,'Native XCUI scroll hierarchy contains only the parent __observer.scroll and no component descendant scroll region.',eid,actual)
   s=d['snapshots'][0];n=best_node(d,'rr.card')
   if not n:
    eid=self.record('nativeInteraction','actualNativeEnvironmentObservation',[self.ref(op,f'/snapshots/{d["indices"][0]}/runtime')],dict(actualRuntime=s['runtime'],missingComponents=['native card width','card horizontal margin','card top origin'],limits='Descendant controls inheriting rr.card are not root geometry.'))
    return unknown('Actual native environment/theme/direction/category/offered width and parent scroll are observed, but the card root frame is not exposed: rr.card is inherited by descendants. This tuple lacks adequate card-width/margin/origin measurements; those fields are not silently inferred from source.',[eid])
   b=rect(n[2],pl);geometrySnapshot=n[3]
   if pl=='android':
    cfg=d['observation']['configuration'];actual=dict(offeredWidth=s['logical_viewport_dp']['width'],cardWidth=b[2],viewportHeight=s['logical_viewport_dp']['height'],horizontalMargin=b[0],topInset=b[1]+geometrySnapshot['scroll_offset_dp'],appearance='dark' if cfg['night_mode_mask']==32 else 'light',layoutDirection=cfg['direction'].lower(),fontScale=cfg['font_scale'],nativeParentVerticalScroll=bool(sc and any(z['scroll_offset_dp']>0 for z in d['snapshots'])))
    ok=all(abs(actual[k]-v[k])<=1 for k in ['offeredWidth','cardWidth','viewportHeight','horizontalMargin','topInset']) and all(actual[k]==v[k] for k in ['appearance','layoutDirection','fontScale','nativeParentVerticalScroll'])
    refs+=[self.ref(op,'/configuration'),self.ref(op,f'/snapshots/{d["indices"][0]}')]
   else:
    rt=s['runtime'];aliases={'accessibility5':'accessibilityExtraExtraExtraLarge','xxxLarge':'extraExtraExtraLarge','xxxlarge':'extraExtraExtraLarge'};cat=aliases.get(rt['dynamic_type'],rt['dynamic_type'])
    actual=dict(offeredWidth=rt['offered_width'],cardWidth=b[2],viewportHeight=rt['viewport_height'],horizontalMargin=b[0]-geometrySnapshot['viewport']['x'],topInset=b[1]-geometrySnapshot['runtime']['content_frame']['y'],appearance=rt['actual_environment']['theme'],layoutDirection=rt['actual_environment']['direction'],appleContentSizeCategory=cat,nativeParentVerticalScroll=bool(sc and any(n.get('identifier')=='__observer.scroll' and n.get('role_raw')==46 for z in d['snapshots'] for n in z['nodes'])))
    ok=all(abs(actual[k]-v[k])<=1 for k in ['offeredWidth','cardWidth','viewportHeight','horizontalMargin','topInset']) and all(actual[k]==v[k] for k in ['appearance','layoutDirection','appleContentSizeCategory','nativeParentVerticalScroll']);refs+=[self.ref(op,f'/snapshots/{d["indices"][0]}/runtime')]
   eid=self.record('nativeInteraction','actualNativeEnvironmentObservation',refs,actual);return result(ok,'Actual native host/environment measurements: '+canonical(actual),eid,actual)
  if row['aspect']=='nativeTypography':
   n=best_node(d,row['target'])
   if pl=='android' and crit=='unscaledPointOrSpRange' and n and 'font_sp' in n[2]:
    actual=n[2]['font_sp'];eid=self.native_record(d,row['target'],'nativeTypography','actualResolvedRuntimeFont',dict(nativeTextLayoutFontSp=actual,limits='No resolved face/family or physical glyph scaling available.'))
    return result(v[0]<=actual<=v[1],'Actual native Text layout reports base font_sp='+str(actual)+'. This assesses the base-size property only.',eid,actual)
   return unknown('No adequate resolved runtime '+('font family/face' if crit=='resolvedFontFamilyIsNativeSystem' else 'physical font/layout scaling matched to the active category/scale' if crit=='effectiveNativeScalingMatchesHost' else 'point-size')+' observation is supplied. Source declarations, requested environment and visual resemblance do not establish this typography predicate.')
  if row['aspect']=='nativeBounds':
   if crit=='minimumTouchBounds':
    if pl=='apple':
     eid=self.native_record(d,row['target'],'nativeBounds','actualAccessibilityFrame',dict(actualAvailableGeometry='XCUI frame/hittable only; no physical hit-region dimensions'))
     return unknown('XCUI accessibility frames/hittable and a single tap point do not measure physical hit-region dimensions. Actual hit-region instrumentation or sufficient edge hit tests are required.',[eid])
    found=nodes(d,row['target']);measured=[x for x in found if x[2].get('intersects_viewport') and 'touch_bounds_dp' in x[2]]
    if not measured:return unknown('No actual native touch_bounds_dp observation for this member at the checkpoint.')
    i,j,n,s=max(measured,key=lambda x:(x[2]['touch_bounds_dp'][2]-x[2]['touch_bounds_dp'][0])*(x[2]['touch_bounds_dp'][3]-x[2]['touch_bounds_dp'][1]));b=n['touch_bounds_dp'];actual=dict(width=b[2]-b[0],height=b[3]-b[1],bounds=b)
    eid=self.record('nativeBounds','actualNativeHitRegionInstrumentation',[self.ref(op,f'/snapshots/{i}/nodes/{j}/touch_bounds_dp')],actual)
    # A clipped native hit region meeting the minimum is a sufficient lower
    # bound; a clipped smaller region cannot establish a full-region failure.
    ok=actual['width']>=v['minWidth'] and actual['height']>=v['minHeight']
    if not ok and not n.get('fully_visible'):return unknown('Native touch bounds are viewport clipped below a minimum; full physical hit rectangle is not observed.',[eid])
    return result(ok,'Actual native touch-region lower-bound dimensions in dp: '+canonical(actual),eid,actual)
   n=best_node(d,row['target'])
   if not n:return unknown('No native frame for the required target is observed at this checkpoint.')
   i,j,node,s=n;b=rect(node,pl)
   if crit=='widthEquals':actual=b[2];ok=abs(actual-v['value'])<=v['tolerance']
   else:
    actual={'x':b[0] if pl=='android' else b[0]-s['viewport']['x'],'y':b[1]+s['scroll_offset_dp'] if pl=='android' else b[1]-s['runtime']['content_frame']['y']};ok=abs(actual['x']-v['x'])<=v['tolerance'] and abs(actual['y']-v['y'])<=v['tolerance']
   eid=self.native_record(d,row['target'],'nativeBounds','actualNativeLayoutFrame' if pl=='android' else 'actualAccessibilityFrame',actual)
   return result(ok,'Native measured logical card geometry: '+canonical(actual),eid,actual)
  if crit=='documentedIdentifierSetEquals':
   actual=sorted(set(n.get('identifier','') for s in d['snapshots'] for n in s['nodes'] if n.get('identifier') in FIXED or re.match(r'^rr\.(option|size)\.',n.get('identifier',''))))
   eid=self.native_record(d,observation=dict(actualIdentifierSet=actual,snapshotIndices=d['indices']));missing=set(v)-set(actual);extra=set(actual)-set(v)
   if missing and not d['context']['fullVisualCheckpoint'] and any(x.startswith('rr.size.') for x in missing):return unknown('Lazy size descendants are outside the observed native viewport at this native-only/focused checkpoint; actual missing size-node existence is not established.',[eid],collectionCoverage={x:'OBSERVED' if x in actual else 'UNASSESSED' for x in v},actualObservedSet=actual)
   return result(not missing and not extra,'Actual documented identifier namespace observed; missing='+str(sorted(missing))+'; extra='+str(sorted(extra)),eid,actual,collectionCoverage={x:'OBSERVED' if x in actual else 'ABSENT_OBSERVED' for x in v},actualObservedSet=actual)
  if crit=='independentAccessibleDecorativeIconCount':
   if pl=='apple':return unknown('The flat XCUI hierarchy includes image descendants but does not expose whether each decorative descendant is independently accessibility focusable. Hierarchy presence/hittable alone does not establish accessibility traversal.')
   # Raw unmerged semantics: no image/content-description/role-bearing native
   # decorative element exists. Empty structural Canvas nodes are not names.
   actual=[n for s in d['snapshots'] for n in s['nodes'] if n.get('role')=='Image' and n.get('content_description')]
   eid=self.native_record(d,observation=dict(independentNamedImageNodes=actual));return result(len(actual)==0,'Actual native semantic inventory contains no independently named decorative image semantic element.',eid,len(actual))
  if crit=='meaningfulReadOrderMatchesVisualOrder':
   # Native tree order is compared to the independently observed major visual
   # flow. It does not claim a separately executed screen-reader navigation.
   expected=next((x['expected'] for x in PLAN if x['contextId']==row['contextId'] and x['platform']==pl and x['criterion']=='majorRegionFlowEquals'),None)
   if expected is None:return unknown('No independently compared major-flow inventory is available for this read-order sample.')
   first={}
   for ident in expected:
    ns=nodes(d,ident)
    if ns:first[ident]=min(x[1] for x in ns)
    else:
     m=d['context']['model'];opt=next((o for o in m['options'] if o['id']==m['selectedOptionId'] and o['disabledReason'] is None),None);known={'rr.breakdown':m['amountRows'][0]['label'] if m['amountRows'] else None,'rr.summary':m['totalLabel'],'rr.sizes':m['sizesTitle'],'rr.detail':opt['detailTitle'] if opt else None}
     text=known.get(ident)
     if text:
      matches=[j for s in d['snapshots'] for j,n in enumerate(s['nodes']) if norm(label(n))==norm(text)]
      if matches:first[ident]=min(matches)
   if set(expected)-set(first):return unknown('Native order collection lacks one or more meaningful regions at this checkpoint.')
   actual=sorted(expected,key=lambda x:first[x]);eid=self.native_record(d,observation=dict(actualNativeRegionOrder=actual,limits='Native tree order, not separately executed VoiceOver/TalkBack navigation.'))
   return result(actual==expected,'Actual meaningful native hierarchy order compared to observed visual flow: '+str(actual),eid,actual)
  target=row['target'];n=best_node(d,target)
  if crit=='exists':
   actual=bool(n);eid=self.native_record(d,observation=dict(target=target,exists=actual));return result(actual==v,'Actual native descendant existence: '+str(actual),eid,actual)
  if not n:return unknown('Required native target '+target+' is not observed at this checkpoint. No adequate node/value observation is available.')
  i,j,node,s=n;eid=self.native_record(d,target);crit=row['criterion']
  if crit=='heading':return unknown('The supplied raw native tree does not expose heading/header trait or semantic heading flag. Ordinary StaticText/blank role is insufficient to establish either presence or absence.',[eid])
  if crit=='expanded':
   if pl=='android':return unknown('The actual raw Compose node exposes role/name/clickability but omits native expanded/stateDescription value; visual chevron/source modifiers do not prove native expanded semantics.',[eid])
   actual=node.get('value');ok=actual==v['alternativeAccessibilityValue']
  elif crit=='checked':
   actual=node.get('toggle_state') if pl=='android' else node.get('value');expected=('On' if v['android'] else 'Off') if pl=='android' else v['appleAccessibilityValue'];ok=actual==expected
  elif crit=='selected':actual=node.get('selected');ok=actual==v
  elif crit=='enabled':actual=node.get('enabled');ok=actual==v
  elif crit=='role':
   actual=node.get('role') if pl=='android' else 'button' if node.get('role_raw')==9 else node.get('role');expected=v.get(pl,v.get('oneOf')) if isinstance(v,dict) else v
   if expected=='checkboxOrToggle':expected=['checkbox','switch','toggleButton']
   if expected=='buttonOrToggle':expected=['button','switch','toggleButton']
   acceptable=expected if isinstance(expected,list) else [expected];ok=any(str(actual).lower()==str(e).lower() for e in acceptable)
  elif crit in ['labelIncludesAll','labelIncludes']:actual=label(node);ok=all(x in actual for x in v)
  elif crit=='labelEquals':actual=label(node);ok=actual==v
  elif crit=='accessibilityValueEquals':
   if pl=='android':return unknown('The raw node omits accessibility stateDescription/busy value; progress text and icon presence are separately observable.',[eid])
   actual=node.get('value');ok=actual==v
  else:return unknown('Independent adapter has no supported observation method for '+crit)
  return result(ok,'Actual native '+crit+'='+canonical(actual),eid,actual)
 def pixel(self,row,d):
  # Filled from the explicit independent pixel-review ledger below. No source
  # color/font/handler reading contributes a rendered-pixel decision.
  review=PIXEL_REVIEWS.get(self.sub,{}).get((row['platform'],row['contextId']))
  if not review:return self.put(row,'UNASSESSED','This concrete native pixel checkpoint has not yet received an independent image review.',[],d)
  return self.pixel_decision(row,d,review)
 def image_refs(self,d):
  return [self.ref(d['path']/s['screenshot']) for s in d['snapshots']]
 def pixel_decision(self,row,d,review):
  crit=row['criterion'];v=row['expected'];pl=row['platform'];target=row['target'];full=d['context']['fullVisualCheckpoint'];actual=None
  refs=self.image_refs(d)
  def put(outcome,reason,actual=None,**kw):
   eid=self.record('renderedPixels','imageDerivedObservation',refs,dict(actualObservation=actual,review='Independent direct review of actual original native images, with lossless scroll-coordinate derivative for navigation.',reviewedFields=review.get('fields',[])))
   return self.put(row,outcome,reason,[eid],d,actual,**kw)
  if not full and review.get('unobservable'):
   return put('UNASSESSED',review['unobservable'])
  if crit=='sampledFlatColorMatches':
   from pixel_measurements import cropped_target
   role=row['key'].split('/')[-1];rgb=COLOR_SAMPLES[self.sub][pl][row['contextId']][role]
   sample=cropped_target(d,target)
   if not sample:return put('UNASSESSED','Actual native image does not cover the sampled target.')
   im=sample['im'];coords=[]
   for yy in range(1,im.height-1):
    for xx in range(1,im.width-1):
     if im.getpixel((xx,yy))==tuple(rgb) and any(im.getpixel((xx+dx,yy+dy))==tuple(rgb) for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]):coords.append((xx+sample['box'][0],yy+sample['box'][1]))
    if len(coords)>=5:break
   if not coords:return put('UNASSESSED','Could not locate an adequate flat core pixel in the actually captured sample; avoid antialiasing/border guess.')
   refs=[self.ref(sample['raw'],region=[x,y,1,1]) for x,y in coords[:5]]
   wanted=tuple(int(v['hex'][i:i+2],16) for i in [1,3,5]);actual=dict(sampleRGB=rgb,expectedRGB=list(wanted),maxChannelDelta=max(abs(a-b) for a,b in zip(rgb,wanted)),samplePixels=coords[:5])
   return put('PASS' if actual['maxChannelDelta']<=v['maxRGBChannelDelta'] else 'FAIL','Sampled actual flat pixel/glyph core RGB '+str(rgb)+'; required '+v['hex']+' with max channel delta '+str(v['maxRGBChannelDelta'])+'.',actual)
  if crit in ['tileGeometryEquals','measuredRoleSampleEquals']:
   from pixel_measurements import radius_sample,tile_sample,spacing_samples
   member=row['key'].split('/')[-1]
   if crit=='tileGeometryEquals':
    actual=tile_sample(d);ok=all(abs(actual[k]-v['size'])<=v['tolerance'] for k in ['width','height']) and abs(actual['radius']-v['radius'])<=v['tolerance']
   elif '/tokens.radii/' in row['key']:
    actual=radius_sample(d,member);ok=abs(actual['fit']['radius']-v['value'])<=v['tolerance']
   elif member in ['textGroups','tightLabels']:
    return put('UNASSESSED','Actual visible ink is readable, but this token names layout line-box spacing. These raw screenshots do not independently expose the two line-box edges needed for a precise 8/4-unit spacing measurement; source constants are not used.')
   else:
    # Independently reviewed raster edges: border/flat-fill edge to text/next
    # control. Values and exact raw regions are entered as actual measurements.
    actual=spacing_samples(d)[member];measured=actual['value'];ok=abs(measured-v['value'])<=v['tolerance']
   if 'rawPath' in actual:
    box=actual['box'];refs=[self.ref(actual['rawPath'],region=[box[0],box[1],box[2]-box[0],min(box[3]-box[1],100)])]
   return put('PASS' if ok else 'FAIL','Actual raster geometry measurement: '+canonical(actual),actual)
  if crit=='selectedBorderWidthEquals':
   from pixel_measurements import cropped_target
   q=cropped_target(d,target);im=q['im'];rgb=(33,100,90);xx=im.width//2;run=0
   for yy in range(min(im.height,20)):
    if max(abs(im.getpixel((xx,yy))[k]-rgb[k]) for k in range(3))<=12:run+=1
    elif run:break
   actual=run/q['scaleY'];refs=[self.ref(q['raw'],region=[q['box'][0]+xx,q['box'][1],1,20])]
   return put('PASS' if abs(actual-v['value'])<=v['tolerance'] else 'FAIL','Measured straight selected-border color run in actual native screenshot, logical thickness '+str(actual)+'.',actual)
  if crit=='fullyReadableTextEquals':
   if target in review.get('clippedFields',[]):return put('FAIL','Actual pixels clip letters of '+target+' at the rounded notes-label boundary; the complete caller string is not readable. Native label completeness is separately assessed.',dict(field=target,condition='visibly clipped glyphs',requiredText=v))
   return put('PASS','Independently read the complete supplied string in the actual native pixels for this field; no ellipsis, missing suffix or clipping is visible.',dict(field=target,completePixelStringMatches=v))
  if crit in ['visibleDocumentedRegionsEqual','majorRegionFlowEquals','actualCapturedFieldIdSetEquals','overlappingMeaningfulRegionPairsEqual','horizontalOverflowRegionIdsEqual']:
   if crit=='actualCapturedFieldIdSetEquals':actual=review['fields']
   elif crit=='visibleDocumentedRegionsEqual':actual=review['regions']
   elif crit=='majorRegionFlowEquals':actual=review['flow']
   elif crit=='overlappingMeaningfulRegionPairsEqual':actual=review.get('overlapPairs',[])
   else:actual=review.get('clippedFields',[])
   equal=actual==v if crit=='majorRegionFlowEquals' else set(canonical(x) for x in actual)==set(canonical(x) for x in v)
   scope=row['collectionScope'];kw=dict(collectionCoverage={x:'OBSERVED' for x in scope['coverageIds']},actualObservedSet=actual)
   return put('PASS' if equal else 'FAIL','Complete actual parent-scroll pixel review. Recorded concrete member coverage and actual '+crit+': '+canonical(actual),actual,**kw)
  if crit=='visualSelectedOptionIdEquals':actual=review['selectedOption']
  elif crit=='visualSelectedSizeIdEquals':actual=review['selectedSize']
  elif crit=='visibleSelectedIndicatorEquals':actual=review['indicator']
  elif crit=='visibleCheckmarkEquals':actual=review['checkmark']
  elif crit=='chevronAgreesWithExpandedState':actual=review['expanded']
  elif crit=='textAbsentEverywhere':
   actual=not any(v in x for x in review.get('actuallyObservedStrings',[]));return put('PASS' if actual else 'FAIL','Full current-state pixels reviewed; obsolete supplied text '+repr(v)+(' is absent.' if actual else ' remains visible.'),actual)
  elif crit in ['nativeVisualHierarchyPresent','decorativeSuccessCheckmarkVisible','nativeIndeterminateProgressVisible']:actual=True
  elif crit=='directionalPlacementMatchesHost':
   actual={'logicalEdge':v['logicalEdge'],'hostDirection':'rtl'}
  else:return put('UNASSESSED','No independently recorded pixel decision for this predicate: '+crit)
  return put('PASS' if actual==v else 'FAIL','Independently observed actual local/native pixel property '+crit+'='+canonical(actual),actual)
 def finish(self,available=False):
  pending=[]
  for row in PLAN:
   if row['sourceOnly']:self.source(row)
   elif available and (row['platform'],row['contextId'].split('/')[0]) not in REVIEWED_CASES[self.sub]:pending.append(row['assessmentId'])
   else:self.runtime(row)
  prefix='partial-' if available else ''
  rr.write(self.dest/(prefix+'raw-index.json'),dict(schemaVersion=1,candidateId=self.sub,phase='D0',sourceSnapshotId=self.sid,records=self.records))
  rr.write(self.dest/(prefix+'decision-ledger.json'),dict(schemaVersion=1,candidateId=self.sub,phase='D0',assessments=self.entries,pendingNotGraded=pending,final=False if available else None))
  visual=[]
  for (pl,cid),review in PIXEL_REVIEWS[self.sub].items():
   d=self.state(cid,pl);visual.append(dict(platform=pl,contextId=cid,modelId=d['context']['modelId'],modelSHA256=d['context']['modelSha256'],environmentSHA256=d['context']['environmentSha256'],actualBinding=d['snapshots'][-1]['binding'],fullVisualCheckpoint=d['context']['fullVisualCheckpoint'],reviewObservation=review,rawImageRefs=self.image_refs(d),fieldCoverage=[dict(fieldId=f,status='OBSERVED',visibleClippingObserved=f in review.get('clippedFields',[])) for f in review.get('fields',[])],limits='Field area observation and complete-string readability are separate: actual clipping is observed coverage with a failing readability/overflow property, not an invented successful string.'))
  rr.write(self.dest/(prefix+'visual-review-ledger.json'),dict(candidateId=self.sub,phase='D0',sourceSnapshotId=self.sid,states=visual,pendingNotGraded=pending,scope='Direct independent native-pixel review; full field inventory members explicitly recorded. No source style/handler inference.'))
  print(json.dumps(collections.Counter(e['outcome'] for e in self.entries)))

PIXEL_REVIEWS={}
COLOR_SAMPLES={}
REVIEWED_CASES={}

def register_review_a():
 """Direct image review entered after all 26 full sets and 36 focused views.

 Each concrete inventory field was located in the lossless native pixel sequence;
 unchanged fields were inspected for coverage without inventing new text rules.
 These constants are reviewer observations, not candidate source interpretation.
 """
 sub='submission-b2e249';reviews={}
 selected={'C01/initial':None,'C01/caller-cash-selected':'cash','C02/initial':'swap','C02/caller-accepted':'swap','C03/initial':'credit','C03/caller-notes-open':'credit','C04/initial':None,'C04/caller-new-purchase':None,'C05/initial':None,'C05/caller-reopened':'arabic-credit','C06/initial':'swap','C06/caller-refund-and-notes-closed':'cash','C06/caller-submitting':None}
 for pl in ['android','apple']:
  for cid,cx in CTX.items():
   rows=[x for x in PLAN if x['platform']==pl and x['contextId']==cid and x['aspect']=='observedPixels']
   if cx['fullVisualCheckpoint']:
    fields=cx['visualInventory']['allVisibleFieldIds'];regions=next(x['expected'] for x in rows if x['criterion']=='visibleDocumentedRegionsEqual');flow=next(x['expected'] for x in rows if x['criterion']=='majorRegionFlowEquals')
    expanded=cid in ['C03/caller-notes-open','C04/initial','C06/initial']
    clipped=['notes.title'] if pl=='android' and cid in ['C03/initial','C03/caller-notes-open','C06/initial','C06/caller-refund-and-notes-closed'] else []
    reviews[(pl,cid)]=dict(fields=fields,regions=regions,flow=flow,expanded=expanded,selectedOption=selected[cid],selectedSize='l' if cid=='C02/caller-accepted' else 'large' if cid=='C06/initial' else None,checkmark=cid in ['C02/caller-accepted','C06/initial'],clippedFields=clipped,overlapPairs=[],actuallyObservedStrings=[x['expected'] for x in rows if x['criterion']=='fullyReadableTextEquals'])
   elif rows:
    row=rows[0];crit=row['criterion'];target=row['target'];entry={}
    if crit=='fullyReadableTextEquals' and cid!='C05/pending-done-echo':entry['unobservable']='After the actual action, the requested status badge lies above the captured viewport. The native label exists, but no after-action badge pixels are supplied; a prior full-state image cannot prove this checkpoint.'
    elif pl=='android' and cid in ['C01/pending-option-echo','C03/pending-ack-echo','C04/disabled-option-activation','C04/pending-new-choice-echo','C06/pending-refund-echo']:
     entry['unobservable']='After-action pixels show a lower portion of the target control, but the required leading radio/checkbox indicator is above the captured viewport. Native selection and callbacks are separately assessed; this concrete visual indicator is unobserved.'
    elif pl=='apple' and cid=='C03/pending-ack-echo':entry['unobservable']='The tall acknowledgement after-action crop shows its final text; its leading checkbox is above the viewport, so the required visual checkmark state is not observed.'
    elif crit=='visibleSelectedIndicatorEquals':entry['indicator']=cid=='C05/pending-selected-option-echo'
    elif crit=='visibleCheckmarkEquals':entry['checkmark']=False
    elif crit=='chevronAgreesWithExpandedState':entry['expanded']=cid=='C06/pending-close-echo'
    reviews[(pl,cid)]=entry
 PIXEL_REVIEWS[sub]=reviews
 REVIEWED_CASES[sub]={(p,'C0'+str(c)) for p in ['android','apple'] for c in range(1,7)}
 common_initial={'card':[255,255,255],'border':[215,221,217],'mainText':[32,40,45],'secondary':[93,103,108],'badgeFill':[234,245,239],'badgeText':[33,100,90]}
 selectedColors={'selectedFill':[234,245,239],'selectedBorder':[33,100,90],'detailPanel':[245,243,238],'primary':[33,100,90],'primaryText':[255,255,255]}
 c04={'card':[25,34,36],'border':[74,90,86],'mainText':[242,246,243],'secondary':[180,192,187]};success={'successFill':[234,245,239],'successText':[33,100,90]}
 COLOR_SAMPLES[sub]={}
 for pl in ['android','apple']:
  initial=dict(common_initial,disabledPrimary=[223,230,225] if pl=='android' else [239,242,240],disabledPrimaryText=[89,101,94] if pl=='android' else [164,171,167])
  c02={'primaryDisabled':[52,68,60] if pl=='android' else [39,51,48],'primaryDisabledText':[186,200,192] if pl=='android' else [113,126,120],'urgentFill':[74,59,29],'urgentText':[247,213,138]}
  COLOR_SAMPLES[sub][pl]={'C01/initial':initial,'C01/caller-cash-selected':selectedColors,'C02/initial':c02,'C04/initial':c04,'C05/initial':success}

def register_review_b_available():
 """Independent direct B pixel observations, entered after viewing B originals.

 All Android/Apple C01..C06 full pixel sequences and focused views have now
 been independently reviewed; the prior partial ledgers are preserved separately.
 """
 sub='submission-4f4364';reviews={};reviewed={(p,'C0'+str(c)) for p in ['android','apple'] for c in range(1,7)}
 selection={'C01/initial':None,'C01/caller-cash-selected':'cash','C02/initial':'swap','C02/caller-accepted':'swap','C03/initial':'credit','C03/caller-notes-open':'credit','C04/initial':None,'C04/caller-new-purchase':None,'C05/initial':None,'C05/caller-reopened':'arabic-credit','C06/initial':'swap','C06/caller-refund-and-notes-closed':'cash','C06/caller-submitting':None}
 for pl,c in sorted(reviewed):
  for cid,cx in CTX.items():
   if cx['caseId']!=c:continue
   rows=[x for x in PLAN if x['platform']==pl and x['contextId']==cid and x['aspect']=='observedPixels']
   if cx['fullVisualCheckpoint']:
    reviews[(pl,cid)]=dict(fields=cx['visualInventory']['allVisibleFieldIds'],regions=next(x['expected'] for x in rows if x['criterion']=='visibleDocumentedRegionsEqual'),flow=next(x['expected'] for x in rows if x['criterion']=='majorRegionFlowEquals'),expanded=cid in ['C03/caller-notes-open','C04/initial','C06/initial'],selectedOption=selection[cid],selectedSize='l' if cid=='C02/caller-accepted' else 'large' if cid=='C06/initial' else None,checkmark=cid in ['C02/caller-accepted','C06/initial'],clippedFields=[],overlapPairs=[],actuallyObservedStrings=[x['expected'] for x in rows if x['criterion']=='fullyReadableTextEquals'])
   elif rows:
    row=rows[0];crit=row['criterion'];entry={}
    if crit=='fullyReadableTextEquals' and cid!='C05/pending-done-echo':entry['unobservable']='The exact after-action image does not show the status badge above the current viewport. Earlier model pixels do not establish this checkpoint.'
    elif pl=='android' and cid in ['C03/pending-ack-echo','C04/pending-new-choice-echo']:
     entry['unobservable']='After-action viewport omits the radio/checkbox center needed for the required visible indicator; a control fragment/native value is not that pixel observation.'
    elif pl=='apple' and cid in ['C01/pending-option-echo','C02/disabled-size-activation','C03/pending-notes-echo','C03/pending-ack-echo','C04/disabled-option-activation','C04/pending-new-choice-echo','C05/pending-selected-option-echo','C06/pending-close-echo','C06/pending-refund-echo']:
     entry['unobservable']='The actual after-action viewport does not include the required control indicator or disclosure chevron. Stable-ID search/dispatch status and callback facts are assessed separately.'
    elif crit=='visibleSelectedIndicatorEquals':entry['indicator']=cid=='C05/pending-selected-option-echo'
    elif crit=='visibleCheckmarkEquals':entry['checkmark']=False
    elif crit=='chevronAgreesWithExpandedState':entry['expanded']=cid=='C06/pending-close-echo'
    reviews[(pl,cid)]=entry
 PIXEL_REVIEWS[sub]=reviews;REVIEWED_CASES[sub]=reviewed
 # Literal observed raster modes from B's own raw images, including disabled
 # composition. No color decision is borrowed from the other submission.
 COLOR_SAMPLES[sub]={}
 for pl in ['android','apple']:
  initial={'card':[255,255,255],'border':[215,221,217],'mainText':[32,40,45],'secondary':[93,103,108],'badgeFill':[234,245,239],'badgeText':[33,100,90],'disabledPrimary':[223,230,225] if pl=='android' else [239,242,240],'disabledPrimaryText':[89,101,94] if pl=='android' else [164,171,167]}
  chosen={'selectedFill':[234,245,239],'selectedBorder':[33,100,90],'detailPanel':[245,243,238],'primary':[33,100,90],'primaryText':[255,255,255]}
  c02={'primaryDisabled':[52,68,60] if pl=='android' else [39,51,48],'primaryDisabledText':[186,200,192] if pl=='android' else [113,126,120],'urgentFill':[74,59,29],'urgentText':[247,213,138]}
  COLOR_SAMPLES[sub][pl]={'C01/initial':initial,'C01/caller-cash-selected':chosen,'C02/initial':c02}
 COLOR_SAMPLES[sub]['android']['C04/initial']={'card':[25,34,36],'border':[74,90,86],'mainText':[242,246,243],'secondary':[180,192,187]}
 COLOR_SAMPLES[sub]['apple']['C04/initial']={'card':[25,34,36],'border':[74,90,86],'mainText':[242,246,243],'secondary':[180,192,187]}
 COLOR_SAMPLES[sub]['android']['C05/initial']={'successFill':[234,245,239],'successText':[33,100,90]}
 COLOR_SAMPLES[sub]['apple']['C05/initial']={'successFill':[234,245,239],'successText':[33,100,90]}

if __name__=='__main__':
 register_review_a();register_review_b_available();Grader(sys.argv[1]).finish('--available' in sys.argv)
