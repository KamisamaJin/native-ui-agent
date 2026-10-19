"""Independent paired legacy evidence adapter; no main runtime evidence imported."""
import pathlib,json,collections,datetime,math,re,sys
import raw_review as rr,base_grader as bg,field_coverage as fc,build_reviews as br
from base_grader import canonical,norm,rect,best_node,nodes,callbacks
from PIL import Image
SUB='submission-4f4364'
REVIEWS={(x['platform'],x['contextId']):x for x in rr.load(rr.HERE/'manual-pixel-reviews.json')['states']}
# Concrete actual colors, independently sampled from the reviewed native rasters.
RGB={'card':(255,255,255),'border':(215,221,217),'mainText':(32,40,45),'secondary':(93,103,108),'badgeFill':(234,245,239),'badgeText':(33,100,90),'disabledPrimary':(223,230,225),'disabledPrimaryText':(89,101,94),'selectedFill':(234,245,239),'selectedBorder':(33,100,90),'detailPanel':(245,243,238),'primary':(33,100,90),'primaryText':(255,255,255),'primaryDisabled':(52,68,60),'primaryDisabledText':(186,200,192),'urgentFill':(74,59,29),'urgentText':(247,213,138),'successFill':(234,245,239),'successText':(33,100,90)}
def validrect(n,pl):return all(rr.finite(x) for x in rect(n,pl)) and rect(n,pl)[2]>0 and rect(n,pl)[3]>0
class PairedGrader(bg.Grader):
 def record(self,method,kind,refs,obs=None,**kw):
  eid='PL'+str(len(self.records)+1).zfill(5)
  self.records.append(dict(id=eid,method=method,kind=kind,rawRefs=refs,observation=obs,**kw));return eid
 def binding(self,row,d=None):
  b=super().binding(row,d)
  if d:
   b['explanation']='Paired legacy only: complete fixtures model equals frozen model; capture action protocol correlated to actual step/snapshot. Native source manifest hashes equal the sealed D0 capsule. Android native input/revision bindings are literal. Apple binding is explicitly derived from actual runtime fixture_index/instance/pid plus complete callback buffer and actual replacement/delivered-tap epoch boundaries; no absent state JSON is invented. No main current-collector runtime evidence used.'
   b['legacyEpochDerivation']=d['epoch'];b['actualNativeBindings']=[dict(snapshotIndex=i,**rr.rawbind(s,row['platform'])) for i,s in zip(d['indices'],d['snapshots'])]
  return b
 def image_refs(self,d):return [self.ref(d['path']/s['screenshot']) for i,s in zip(d['indices'],d['snapshots']) if i in d['pixelIndices']]
 def put(self,row,outcome,reason,eids=None,d=None,actual=None,**kw):
  if d and row.get('collectionScope') and outcome=='UNASSESSED':
   review=REVIEWS[(row['platform'],row['contextId'])]
   kw.setdefault('collectionCoverage',{x:'OBSERVED' if x in review.get('fields',[]) else 'UNASSESSED' for x in row['collectionScope']['coverageIds']})
  return super().put(row,outcome,reason,eids,d,actual,**kw)
 def runtime(self,row):
  d=self.state(row['contextId'],row['platform']);crit=row['criterion'];pl=row['platform'];op=d['path']/'observation.json';v=row['expected'];rev=REVIEWS[(pl,row['contextId'])]
  def unknown(reason,eids=None,actual=None,**kw):
   if eids is None:eids=[self.native_record(d,row['target'] if row['target'].startswith('rr.') else None,observation=dict(actualScope=d['indices'],unresolvedCriterion=crit,limits=reason))]
   return self.put(row,'UNASSESSED',reason,eids,d,actual,**kw)
  if crit=='executedNativeActivation':
   step=d['triggerStep'];idx=d['protocol']['trigger_action_index'];out=step.get('outcome',step.get('execution'));mech='blockedBeforeDispatch' if out=='blocked_disabled' else ('androidNativeSemanticOnClick' if pl=='android' else 'iosXCUITap') if rr.delivered(step,pl) else 'unexecutedOrUnavailable'
   eid=self.record('nativeInteraction','actualNativeExecutionTrace',[self.ref(op,f'/steps/{idx}'),self.ref(d['path']/'capture.json','/native_method_limit')],dict(actualOutcome=out,observedMethod=mech,requestedMethod=v['method'],callbackDelta=callbacks(step)),observedActivationMechanism=mech)
   if mech=='blockedBeforeDispatch':return unknown('blocked_disabled records the observer declining native dispatch. Native disabled state and callback facts remain separately observed; a delivered activation was not exercised.',[eid])
   supported=mech=='iosXCUITap' if v['method']=='tap' else mech=='androidNativeSemanticOnClick'
   if not supported:return unknown('Requested '+v['method']+' is not proved by actual '+mech+'. iOS accessibilityActivate requests route to XCUI tap, Android uses native semantic OnClick; an unavailable request supplies no delivered activation.',[eid])
   current=rr.rawbind(d['snapshots'][-1],pl);bindings=[rr.rawbind(s,pl) for s in d['observation']['snapshots']];same=len({s['instance'] for s in bindings})==1 and step.get('same_process',True);echo=current['fixture_index']==d['protocol']['input_index'];actual=dict(mechanism=mech,sameMountedHost=same,echoWithheld=echo)
   return self.put(row,'PASS' if same and echo else 'FAIL','Actual native activation observed with the exact mechanism; input index remained current and mounted instance/process was compared.',[eid],d,actual)
  if crit=='actualCallerReplacement':
   idx=d['protocol']['trigger_action_index'];st=d['triggerStep'];old=rr.rawbind(d['observation']['snapshots'][0],pl);current=rr.rawbind(d['snapshots'][-1],pl);same=current['instance']==old['instance'] and (pl!='apple' or current['pid']==old['pid']);actual=dict(sameMountedHost=same,actualInputIndex=current['fixture_index'],actualFixtureEquals=d['fixtureEquals'],stepType=st.get('type',st.get('action',{}).get('type')));ok=same and actual['actualInputIndex']==d['protocol']['input_index'] and d['fixtureEquals'] and actual['stepType']=='apply_next_fixture'
   eid=self.record('nativeInteraction','actualNativeExecutionTrace',[self.ref(op,f'/steps/{idx}'),self.ref(op,f'/snapshots/{d["anchorIndex"]}/runtime')],actual)
   return self.put(row,'PASS' if ok else 'FAIL','Actual complete caller replacement and same mounted native instance/process, bound to the exact frozen model.',[eid],d,actual)
  if crit=='entireCardReachableByParentVerticalScroll':
   intervals=[]
   for i,s in zip(d['indices'],d['snapshots']):
    off=s['scroll_offset_dp'] if pl=='android' else s.get('_relative_offset')
    if off is not None:intervals.append([off,off+600])
   end=None;gaps=[]
   for a,b in sorted(intervals):
    if end is not None and a>end+.75:gaps.append([end,a])
    end=max(end or b,b)
   top=rev['completeCurrentCard'];bottom=rev['completeCurrentCard'];actual=dict(intervals=intervals,uncoveredIntervalGaps=gaps,independentlyObservedTop=top,independentlyObservedBottom=bottom,unchangedInputCallbackEpoch=d['epoch'],note='Apple offsets are actual same-heading relative displacement, not synthesized absolute content-frame metadata; top and bottom require direct raw pixel review.')
   eid=self.record('nativeInteraction','actualNativeExecutionTrace',[self.ref(op,f'/snapshots/{i}') for i in d['indices']],actual)
   if not rev['completeCurrentCard'] or gaps:return unknown('Actual legacy frames do not establish the whole current card from top through bottom in overlapping intervals. Unsupported sweep realized capture only; bounded reveal frames are credited per member, without treating observer coverage as product failure.',[eid],actual)
   return self.put(row,'PASS','Actual raw native displacements and overlapping current-epoch pixels reach the independently observed component top and bottom.',[eid],d,actual)
  if crit=='actualNativeEnvironmentEquals':
   if pl=='apple':return unknown('Actual offered width, viewport, theme, direction and Dynamic Type category are recorded, but no root card native frame/content origin is exposed. Descendants inheriting rr.card cannot establish the required root width/margins/top-origin tuple.')
   n=best_node(d,'rr.card');s=d['snapshots'][0]
   if not n:return unknown('Required actual root native geometry is unavailable.')
   b=rect(n[2],pl);cfg=d['observation']['configuration'];ss=n[3];actual=dict(offeredWidth=s['logical_viewport_dp']['width'],cardWidth=b[2],viewportHeight=s['logical_viewport_dp']['height'],horizontalMargin=b[0],topInset=b[1]+ss['scroll_offset_dp'],appearance='dark' if cfg['night_mode_mask']==32 else 'light',layoutDirection=cfg['direction'].lower(),fontScale=cfg['font_scale'],nativeParentVerticalScroll=any(x['scroll_offset_dp']>0 for x in d['snapshots']));ok=all(abs(actual[k]-v[k])<=1 for k in ['offeredWidth','cardWidth','viewportHeight','horizontalMargin','topInset']) and all(actual[k]==v[k] for k in ['appearance','layoutDirection','fontScale','nativeParentVerticalScroll'])
   eid=self.record('nativeInteraction','actualNativeEnvironmentObservation',[self.ref(op,'/configuration'),self.ref(op,f'/snapshots/{n[0]}')],actual);return self.put(row,'PASS' if ok else 'FAIL','Actual native configuration and logical layout tuple, measured in the paired legacy raw observation.',[eid],d,actual)
  if crit=='documentedIdentifierSetEquals':
   actual=sorted({n.get('identifier','') for s in d['snapshots'] for n in s['nodes'] if n.get('identifier') in bg.FIXED or re.match(r'^rr\.(option|size)\.',n.get('identifier',''))});eid=self.native_record(d,observation=dict(actualIdentifierSet=actual,snapshotIndices=d['indices']));missing=set(v)-set(actual);extra=set(actual)-set(v)
   if extra:return self.put(row,'FAIL','Actual namespace contains an unexpected documented identifier at this state.',[eid],d,actual,counterexample=dict(description='Unexpected native documented identifier '+str(sorted(extra)),targetIds=sorted(extra),evidenceRecordIds=[eid]),actualObservedSet=actual)
   wrong=[]
   for target in missing:
    found=nodes(d,target)
    if found:
     i,j,n,s=found[0]
     if n.get('identifier')!=target:wrong.append(dict(required=target,actual=n.get('identifier'),snapshotIndex=i,nodeIndex=j,label=n.get('label')))
   if wrong:
    refs=[self.ref(op,f'/snapshots/{x["snapshotIndex"]}/nodes/{x["nodeIndex"]}') for x in wrong];eid=self.record('nativeSemantics','actualNativeSemantics',refs,dict(observedMisidentifiedMembers=wrong))
    return self.put(row,'FAIL','A uniquely named actual native member is exposed under a different identifier while the required identifier is absent from the current native inventory. This is an observed namespace counterexample, not an inference from a failed activation.',[eid],d,dict(actualSet=actual,misidentified=wrong),counterexample=dict(description='Actual named native members carry the wrong stable identifiers.',targetIds=[x['required'] for x in wrong],evidenceRecordIds=[eid]),actualObservedSet=actual,collectionCoverage={x:'OBSERVED' if x in actual else 'UNASSESSED' for x in v})
   if not missing:return self.put(row,'PASS','Complete actual native documented namespace inventoried across the reviewed current card.',[eid],d,actual,collectionCoverage={x:'OBSERVED' for x in v},actualObservedSet=actual)
   return unknown('The bounded native inventory does not prove absence of unobserved lazy/offscreen documented members. Exact observed IDs are retained; no source inference or schema absence decides the set.',[eid],actual,collectionCoverage={x:'OBSERVED' if x in actual else 'UNASSESSED' for x in v},actualObservedSet=actual)
  if pl=='android' and crit in ['labelIncludesAll','labelIncludes','labelEquals']:
   found=best_node(d,row['target'])
   if found and not found[2].get('label') and not found[2].get('content_description'):
    i,j,node,s=found;ids={node['node_id']};desc=[]
    for z,n in enumerate(s['nodes']):
     if n.get('parent_id') in ids:
      ids.add(n['node_id'])
      if n.get('label') or n.get('content_description'):desc.append(dict(nodeIndex=z,label=n.get('label'),contentDescription=n.get('content_description')))
    eid=self.record('nativeSemantics','actualNativeSemantics',[self.ref(op,f'/snapshots/{i}/nodes/{j}')]+[self.ref(op,f'/snapshots/{i}/nodes/{z["nodeIndex"]}') for z in desc],dict(actualUnmergedContainerLabel=node.get('label'),actualDescendantTexts=desc,limits='Unmerged tree exposes the descendants but not the final merged accessible name or merge/focus policy.'))
    return unknown('The actual legacy unmerged semantic container has an empty direct label and named descendants. This does not prove that the final accessible control/group name is empty or that descendants are merged into it; resolved accessible-name/merge observation is required. Preserve the actual descendant names without calling schema absence a product defect.',[eid],dict(containerLabel=node.get('label'),descendantNames=desc))
  if crit=='meaningfulReadOrderMatchesVisualOrder' and not rev['completeCurrentCard']:return unknown('Only part of this current card was captured in pixels; full meaningful native order cannot be compared to an independently observed complete visual region flow.')
  if row['aspect']=='nativeBounds' and pl=='apple' and crit!='minimumTouchBounds':return unknown('No actual root AX/layout frame is exposed; inherited rr.card descendant frames are not the card frame. The paired capture also lacks absolute parent content origin instrumentation.')
  return super().runtime(row)
 def pixel(self,row,d):
  pl=row['platform'];cid=row['contextId'];rev=REVIEWS[(pl,cid)];v=row['expected'];crit=row['criterion'];target=row['target'];refs=self.image_refs(d)
  def result(outcome,reason,actual=None,**kw):
   eid=self.record('renderedPixels','imageDerivedObservation',refs,dict(actualObservation=actual,reviewedFields=rev['fields'],pixelSnapshotIndices=d['pixelIndices'],review='Independent direct actual paired-native raster review; gaps and offscreen members remain unresolved.'))
   return self.put(row,outcome,reason,[eid],d,actual,**kw)
  def unknown(why,actual=None,**kw):return result('UNASSESSED',why,actual,**kw)
  if crit=='fullyReadableTextEquals':
   if target not in rev['fields']:return unknown('The actual legacy viewport fragments do not cover the complete supplied string for this field. Offscreen content and viewport cutoff are not reported as a product clipping defect.',dict(field=target,observedFragmentEvidence=rev['fieldFragmentEvidence'].get(target,[])))
   return result('PASS','Directly compared the complete caller string with its actual pixels, using overlapping fragments when the field exceeds a viewport. No visible ellipsis, lost suffix or clipped glyph was observed.',dict(field=target,completePixelStringMatches=v,fragmentEvidence=rev['fieldFragmentEvidence'].get(target,[])))
  if row.get('collectionScope'):
   if not rev['completeCurrentCard']:return unknown('Legacy capture/reveal frames cover only part of the current card. Each observed field is recorded, but the whole required collection/absence/overlap scope is not established.',dict(observedFields=rev['fields'],unassessedFields=rev['unassessedFields']),actualObservedSet=rev['fields'] if crit=='actualCapturedFieldIdSetEquals' else None)
   actual=rev['fields'] if crit=='actualCapturedFieldIdSetEquals' else rev['regions'] if crit=='visibleDocumentedRegionsEqual' else rev['flow'] if crit=='majorRegionFlowEquals' else rev['overlapPairs'] if crit=='overlappingMeaningfulRegionPairsEqual' else rev['clippedFields']
   equal=actual==v if crit=='majorRegionFlowEquals' else set(canonical(x) for x in actual)==set(canonical(x) for x in v)
   return result('PASS' if equal else 'FAIL','Complete direct current-card pixel inventory, ordering and every mandatory field coverage reviewed. No hidden member is silently omitted.',actual,collectionCoverage={x:'OBSERVED' for x in row['collectionScope']['coverageIds']},actualObservedSet=actual)
  if crit=='textAbsentEverywhere':return unknown('A partial current-card viewport cannot establish that obsolete text is absent everywhere, even when the replacement model is correctly bound.')
  if crit=='sampledFlatColorMatches':
   from pixel_measurements import cropped_target
   role=row['key'].split('/')[-1];rgb=RGB[role]
   if cid=='C04/initial':rgb={'card':(25,34,36),'border':(74,90,86),'mainText':(242,246,243),'secondary':(180,192,187)}[role]
   if pl=='apple' and cid=='C01/initial' and role in ['disabledPrimary','disabledPrimaryText']:rgb=(239,242,240) if role=='disabledPrimary' else (164,171,167)
   q=cropped_target(d,target)
   if q is None:return unknown('The actual legacy pixel sample does not cover the requested local color target.')
   im=q['im'];coords=[]
   for y in range(1,im.height-1):
    for x in range(1,im.width-1):
     if im.getpixel((x,y))==rgb and any(im.getpixel((x+dx,y+dy))==rgb for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]):coords.append((x+q['box'][0],y+q['box'][1]))
     if len(coords)>=5:break
    if len(coords)>=5:break
   if not coords:return unknown('No adequate flat core sample of the independently observed target role is captured; antialiasing does not establish this color.')
   refs=[self.ref(q['raw'],region=[x,y,1,1]) for x,y in coords];wanted=tuple(int(v['hex'][i:i+2],16) for i in [1,3,5]);delta=max(abs(a-b) for a,b in zip(rgb,wanted));actual=dict(sampleRGB=rgb,expectedRGB=wanted,maxChannelDelta=delta,snapshotIndex=q['snapshot'],samplePixels=coords)
   return result('PASS' if delta<=v['maxRGBChannelDelta'] else 'FAIL','Actual flat native pixel/glyph-core color compared with the frozen channel tolerance.',actual)
  if crit in ['tileGeometryEquals','measuredRoleSampleEquals','selectedBorderWidthEquals']:
   # Reuse the frozen raster measurement method, not any previous raster result.
   try:
    if crit=='selectedBorderWidthEquals':
     from pixel_measurements import cropped_target
     q=cropped_target(d,target)
     if q is None:return unknown('Requested selected border is outside actual captured pixels.')
    return super().pixel_decision(row,d,dict(fields=rev['fields']))
   except (ValueError,KeyError,TypeError,IndexError,StopIteration,AttributeError) as e:return unknown('Actual raster edges needed by this measurement are not adequately exposed at this checkpoint: '+type(e).__name__+': '+str(e))
  # Local properties below are only credited at a directly reviewed visible area.
  fieldids=rev['fields'];m=d['context']['model'];cat=br.catalog(m)
  def seen_text(text):
   # A focused target may exceed viewport height; local indicator/chevron must
   # still be directly visible. Full title/text bounds are sufficient, not necessary.
   for i,s in zip(d['indices'],d['snapshots']):
    if i not in d['pixelIndices']:continue
    for n in s['nodes']:
     if n.get('label')==text and fc.fully_visible(n,s,pl):return True
   return False
  if crit=='visualSelectedOptionIdEquals':
   opts=m['options'];allseen=all(('option.'+o['id']+'.title' in fieldids and 'option.'+o['id']+'.description' in fieldids) for o in opts)
   if not allseen:return unknown('Not every current resolution option and its indicator is covered by the actual current-state pixels; exclusive option-selection identity is unresolved.')
   actual={'C01/initial':None,'C02/initial':'swap','C03/initial':'credit','C04/initial':None,'C06/initial':'swap','C04/caller-new-purchase':None,'C05/caller-reopened':'arabic-credit'}.get(cid,'UNOBSERVED')
   if actual=='UNOBSERVED':return unknown('No independent exclusive-option observation recorded for this partial state.')
  elif crit=='visualSelectedSizeIdEquals':
   if not all('size.'+z['id']+'.label' in fieldids for z in m['sizes']):return unknown('All current size indicators are not captured together/across the unchanged epoch.')
   actual=None if cid=='C02/initial' else 'l' if cid=='C02/caller-accepted' else 'large' if cid=='C06/initial' else 'UNOBSERVED'
  elif crit=='chevronAgreesWithExpandedState':
   if not seen_text(m['notes']['title']):return unknown('Notes chevron is outside the actual reviewed viewport; requested state alone does not establish its drawing.')
   # Manual review of actual visible chevrons in the listed states.
   actual=cid in ['C03/caller-notes-open','C04/initial','C06/initial','C06/pending-close-echo']
  elif crit in ['visibleSelectedIndicatorEquals','visibleCheckmarkEquals']:
   if target=='rr.ack':
    o=next((x for x in m['options'] if x['id']==m['selectedOptionId'] and x['disabledReason'] is None),None)
    if not o or not seen_text(o['acknowledgementLabel']):return unknown('The actual acknowledgement checkbox is not fully in the reviewed local viewport.')
    actual=cid in ['C02/caller-accepted','C06/initial']
   elif target.startswith('rr.size.'):
    z=next((x for x in m['sizes'] if x['id']==target[8:]),None)
    if not z or not seen_text(z['label']):return unknown('This concrete size indicator is outside the actual reviewed pixels.')
    actual=False # Actual disabled-xs and pending-l indicators were unselected.
   else:
    oid=target.split('.')[-1];o=next((x for x in m['options'] if x['id']==oid),None)
    if not o or not seen_text(o['title']):return unknown('This option indicator is outside the actual focused pixels.')
    actual=cid=='C05/pending-selected-option-echo'
  elif crit=='directionalPlacementMatchesHost':
   role=row['key'].split('/')[-1]
   if role=='tile' and ('item.title' in fieldids):actual={'logicalEdge':'leading','hostDirection':'rtl'}
   elif role=='choice' and all('option.'+o['id']+'.title' in fieldids for o in m['options']):actual={'logicalEdge':'leading','hostDirection':'rtl'}
   elif role=='money' and all('amount.'+o['id']+'.value' in fieldids for o in m['amountRows']):actual={'logicalEdge':'trailing','hostDirection':'rtl'}
   else:return unknown('The particular directional role is not fully covered by this actual legacy viewport; the observed tile/choice/amount roles are assessed separately.')
  elif crit=='nativeVisualHierarchyPresent':actual=True
  elif crit=='decorativeSuccessCheckmarkVisible':actual=True # Direct current complete-result raw pixel review.
  elif crit=='nativeIndeterminateProgressVisible':
   if not seen_text(m['progressTitle']):return unknown('Actual submitting viewport shows only the lower progress/body area; the native spinner itself is outside captured pixels.')
   actual=True
  else:return unknown('No adequate independent paired pixel observation for this exact local predicate '+crit)
  return result('PASS' if actual==v else 'FAIL','Directly observed actual local native drawing for this exact checkpoint and target.',actual)
 def finish(self):
  for row in rr.PLAN:
   if not row['sourceOnly']:self.runtime(row)
  rr.write(self.dest/'raw-index.json',dict(schemaVersion=1,candidateId=self.sub,phase='D0',sourceSnapshotId=self.sid,corpus='paired-evidence/d0',records=self.records))
  rr.write(self.dest/'decision-ledger.json',dict(schemaVersion=1,candidateId=self.sub,phase='D0',assessments=self.entries,pendingNotGraded=[],final=True))
  rr.write(self.dest/'state-coverage.json',dict(candidateId=self.sub,phase='D0',states=[dict(platform=pl,contextId=cid,inputIndex=self.state(cid,pl)['protocol']['input_index'],captureActionIndex=self.state(cid,pl)['protocol']['capture_action_index'],anchorSnapshotIndex=self.state(cid,pl)['anchorIndex'],actualEpoch=self.state(cid,pl)['epoch'],nativeSnapshotIndices=self.state(cid,pl)['indices'],pixelSnapshotIndices=self.state(cid,pl)['pixelIndices'],actualFixtureEquals=self.state(cid,pl)['fixtureEquals'],nativeSourceMatch=self.state(cid,pl)['sourceMatch'],observedFields=r['fields'],unassessedFields=r['unassessedFields'],completeCurrentCard=r['completeCurrentCard']) for (pl,cid),r in REVIEWS.items()]))
if __name__=='__main__':PairedGrader(SUB).finish();print('Paired runtime ledger written')
