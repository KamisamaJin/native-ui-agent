from pathlib import Path
import json,hashlib,copy,collections,datetime
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/fresh-blind');G=B/'design/grader';O=json.loads((B/'design/private/oracle.json').read_text());READY_BY_SUB={sub:['initial_01','initial_02','initial_03','initial_04','initial_05','initial_06','repair_holdout_01'] for sub in ['submission-9e49d0','submission-3dd8b6','submission-4f1781']}
for final_sub in READY_BY_SUB:READY_BY_SUB[final_sub].append('repair_holdout_02')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ev(p,ch,**k):return {'channel':ch,'path':str(p),'sha256':sha(p),**k}
base={
'R02':'Actual native labels retain the full supplied service, location and old appointment day/time, with the correct mode titles.',
'R03':'Actual native group/row sequence and coherent row labels match caller order and preserve every time, detail, availability and fee-or-reason; original screenshots expose the corresponding text.',
'R04':'The actual selected trait and radio pixels identify exactly the current eligible ID; no selection appears initially where nil. Caller echo immediately changes the native selection.',
'R05':'Actual row activations match the required callback deltas. Selected reactivation and unavailable disabled attempts are assessed only where the case exercises them.',
'R06':'Actual native combined summaries and guidance/warning labels match the effective selection and fee state at every required checkpoint.',
'R07':'Conditional native consent presence and supplied value match this case at all required checkpoints.',
'R08':'Native confirmation presence/enabled state and actual callback deltas follow the frozen branch checks. Enabled choosing activation emits exactly its current ID and disabled attempts add no event where exercised. Rendering or stale input in other modes produces no unsolicited confirm/retry/done.',
'R09':'The actual native tree follows the current mode/model, ignoring stale fields in non-choosing modes. Same-process callback echoes immediately update row selection, summary, fee state/presence, guidance and confirmation gate where exercised. Source ownership is separately reviewed.',
'R10':'The native loading label/progress screenshot and absence of all stale chooser/action controls follow the loading branch; no callback occurs.',
'R11':'Actual unavailable heading/message, absent stale controls and enabled Check again are correct; real native activation yields one retry.',
'R12':'Actual green success card preserves the new appointment, full reference/note and previous context, with stale controls absent and one done callback.',
'R13':'Actual native IDs are unique and meaningful, including the panel container; the rendered branch exposes the required context/content IDs and native states. Where rows are rendered, coherent Button labels and selected/disabled traits are exposed without duplicate activatable rows. Rendered Switch/Button states and real actions are assessed where exercised; source declares minimum target layout. Expanded UIKit hit regions are not inferred from AX visual frames.',
'R14':'Original native screenshots follow the reference hierarchy, system type and appropriate surfaces/controls for this rendered branch. Choosing rows retain readable full-opacity unavailable content and explicit disabled-button colors where present. Native antialiasing and wrapping differences are allowed.',
'R15':'Original viewport/action screenshots show complete wrapping with no ellipsis, shrink-to-fit, overlap or horizontal/fixed-height clipping. Native labels retain complete content. Clipping by the ordinary parent viewport while scrolling is not a product truncation defect.',
'R16':'Actual parent scroll screenshots reveal full long content and the final action. Inspected production grows intrinsically without nested fixed/lazy viewport.',
'R17':'Actual recorded theme/direction/dynamic-type environment matches the supplied configuration. Screenshots preserve readable theme/disabled contrast, intact date/time/amount strings and semantic direction/affordances.'}
all_audits=[]
for sub in ['submission-9e49d0','submission-3dd8b6','submission-4f1781']:
 READY=READY_BY_SUB[sub]
 existing=G/f'{sub}-final-ios.json'
 if existing.exists() and json.loads(existing.read_text()).get('gradingStatus')=='sealed_ios_final':
  print(sub,'preserved existing sealed iOS FINAL');continue
 old=json.loads((G/f'{sub}-d0-ios.json').read_text());src=list((B/'implementations/final'/sub/'alerttoast').rglob('VisitReschedule*.swift'));srcEv=[ev(p,'declarative_source_review') for p in src];comp=B/'build-evidence/final'/sub/'compatibility.json';compat=json.loads(comp.read_text());assert all(sha(B/'implementations/final'/sub/k)==v for k,v in compat['sourceFiles'].items());assert all(z['exitCode']==0 and sha(comp.parent/z['log'])==z['logSha256'] for z in compat['commands']);cases=[]
 for c in O['cases']:
  cid=c['caseId']
  if cid not in READY:
   cases.append({'caseId':cid,'applicableRuleIds':c['applicableRuleIds'],'ratings':[{'ruleId':r,'status':'unassessed','evidence':[],'rationale':'Supported FINAL iOS capture not yet supplied for independent grading. No pass/fail inference from source or another case.','clusterIds':[]} for r in c['applicableRuleIds']],'visualScore':None,'visualRationale':'Missing supported FINAL screenshot evidence.','visualEvidence':[],'observerStatus':'missing_pending_capture'});continue
  p=B/'evidence/final'/sub/'ios'/cid;a=json.loads((p/'observation.json').read_text());cap=json.loads((p/'capture.json').read_text());assert all(sha(B/'implementations/final'/sub/'alerttoast'/k)==v for k,v in cap['sources'].items());issues=[];tests=0
  def ck(cond,detail,ix=None):
   global tests
   tests+=1
   if not cond:issues.append({'detail':detail,'snapshotIndex':ix})
  exp=[e for q in c['protocol'] for e in q.get('expectedEvents',[])];actual=[x['event'] for z in a['steps'] for x in z['callback_delta']];unexecuted=[(i,z) for i,z in enumerate(a['steps']) if z['action']['type']=='tap' and z['outcome']=='unavailable'];ck(actual==(exp[:len(actual)] if unexecuted else exp),'Exact observed callback stream; omitted unexecuted activation is missing evidence');ck(all(z.get('same_process') for z in a['steps']),'Same process')
  for ix,z in enumerate(a['snapshots']):
   fixture_index=z.get('runtime',{}).get('fixture_index',0)
   fixtures=[c['fixture']]+c.get('updates',[])
   ck(0<=fixture_index<len(fixtures),'Observed fixture index',ix)
   m=copy.deepcopy(fixtures[fixture_index]['model'])
   ck(z['runtime']['instance']==a['original_runtime']['instance'] and z['runtime']['pid']==a['original_runtime']['pid'],'Retained actual component host/process',ix)
   for cb in z.get('callbacks',[]):
    if cb.get('fixture_index',0)!=fixture_index:continue
    e=cb['event']
    if e.startswith('select_slot:'):
     selected=e.split(':',1)[1]
     if selected!=m.get('selectedSlotId'):m['selectedSlotId']=selected;m['feeAccepted']=False
    if e.startswith('fee_accepted:'):m['feeAccepted']=e.endswith('true')
   nodes=z['nodes'];nd={n['identifier']:n for n in nodes if n['identifier'].startswith('visit.')};count=collections.Counter(n['identifier'] for n in nodes if n['identifier'].startswith('visit.'))
   ck(all(n==1 for n in count.values()),'Unique native IDs',ix)
   for ident in ['visit.panel','visit.title','visit.service','visit.location','visit.current']:ck(ident in nd,'Required ID '+ident,ix)
   def label(i):return nd.get(i,{}).get('label','')
   ck(label('visit.title')==('Visit rescheduled' if m['mode']=='confirmed' else 'Reschedule visit'),'Mode title',ix)
   ck(m['serviceTitle'] in label('visit.service') and m['location'] in label('visit.location'),'Shared full content',ix)
   ck(all(v in label('visit.current') for v in ['Previous appointment' if m['mode']=='confirmed' else 'Current appointment',m['currentAppointment']['dayLabel'],m['currentAppointment']['timeLabel']]),'Old appointment',ix)
   pairs=[(g,s) for g in m['groups'] for s in g['slots']] if m['mode']=='choosing' else [];eligible=next(((g,s) for g,s in pairs if s['id']==m.get('selectedSlotId') and s['availability']!='unavailable'),None)
   ck([n['identifier'] for n in nodes if n['identifier'].startswith('visit.group.')]==(['visit.group.'+g['id'] for g in m['groups']] if m['mode']=='choosing' else []),'Group order',ix)
   ck([n['identifier'] for n in nodes if n['identifier'].startswith('visit.slot.')]==['visit.slot.'+s['id'] for g,s in pairs],'Row order',ix)
   for g,s in pairs:
    ident='visit.slot.'+s['id'];n=nd[ident];avail={'available':'Available','limited':'Few left','unavailable':'Unavailable'}[s['availability']];meta=s['unavailableReason'] if s['availability']=='unavailable' else s['feeLabel']+' fee' if s.get('feeLabel') else 'No fee'
    ck(all(v in n['label'] for v in [g['dayLabel'],s['timeLabel'],s['detail'],avail,meta]),'Full row '+ident,ix);ck(n['role_raw']==9 and n['enabled']==(s['availability']!='unavailable'),'Native row Button/enabled '+ident,ix);ck(n['selected']==bool(eligible and eligible[1]['id']==s['id']),'Native selection '+ident,ix)
   fee=bool(eligible and eligible[1].get('feeLabel'));ck(('visit.fee_consent'in nd)==fee,'Consent presence',ix);ck(('visit.selection_summary'in nd)==bool(eligible),'Summary presence',ix)
   if eligible:
    ck(all(v in label('visit.selection_summary') for v in ['New appointment',eligible[0]['dayLabel'],eligible[1]['timeLabel'],eligible[1]['feeLabel'] if fee else 'No rescheduling fee']),'Summary content',ix)
   if fee:
    n=nd['visit.fee_consent'];ck(n['role_raw']==40 and n['value']==('1' if m['feeAccepted'] else '0') and n['label']=='I agree to the rescheduling fee of '+eligible[1]['feeLabel']+'.','Native Switch label/value',ix)
   ck(('visit.confirm'in nd)==(m['mode']=='choosing'),'Confirm presence',ix)
   if m['mode']=='choosing':ck(nd['visit.confirm']['enabled']==bool(eligible and (not fee or m['feeAccepted'])),'Confirm gate',ix)
   for ident,mode in [('visit.loading','loading'),('visit.unavailable','unavailable'),('visit.confirmation','confirmed'),('visit.retry','unavailable'),('visit.done','confirmed'),('visit.reference','confirmed')]:ck((ident in nd)==(m['mode']==mode),'Mode presence '+ident,ix)
   if m['mode']=='loading':ck('Checking available appointments' in label('visit.loading') and nd['visit.loading']['role_raw']==36,'Native progress/copy',ix)
   if m['mode']=='unavailable':ck(all(v in label('visit.unavailable') for v in ['No appointments available',m['unavailableMessage']]) and nd['visit.retry']['enabled'],'Unavailable content/action',ix)
   if m['mode']=='confirmed':
    conf=m['confirmation'];full=' '.join(n['label'] for n in nodes);ck(all(v in full for v in ['New appointment confirmed',conf['appointment']['dayLabel'],conf['appointment']['timeLabel'],conf['note']]) and label('visit.reference')=='Reference: '+conf['reference'] and nd['visit.done']['enabled'],'Full confirmation/reference/action',ix)
   invalid=m['mode']=='choosing' and m.get('selectedSlotId') is not None and not eligible
   ck(('visit.selection_warning'in nd)==invalid,'Warning presence',ix)
   if invalid:ck('That appointment is no longer available. Choose another time.' in label('visit.selection_warning'),'Invalid warning',ix)
   guidance=m['mode']=='choosing' and not invalid;ck(('visit.guidance'in nd)==guidance,'Guidance presence',ix)
   if guidance:
    val='Choose one appointment to continue.' if not eligible else 'Agree to the fee to continue.' if fee and not m['feeAccepted'] else 'Your current time stays reserved until you confirm.';ck(val in label('visit.guidance'),'Guidance copy',ix)
  env=a['original_runtime']['actual_environment'];ck(env['direction']==c['fixture']['environment']['direction'] and env['theme']==c['fixture']['environment']['theme'],'Actual environment');assert not issues,(sub,cid,issues)
  audit={'submission':sub,'caseId':cid,'sourceHashesVerified':True,'observationSha256':sha(p/'observation.json'),'tests':tests,'issues':issues,'actualEvents':actual,'nativeUniqueIds':True};all_audits.append(audit)
  screens=[ev(p/z['screenshot'],'screenshot',checkpoint=z['name'],snapshotIndex=ix) for ix,z in enumerate(a['snapshots'])];ratings=[]
  for ch in c['checks']:
   rid=ch['ruleId'];e=[ev(p/'observation.json','actual_native_xcui_and_receipts',publicCheckpoints=ch['at'],initialCheckpointAlias='top',pointers=['/snapshots','/steps','/original_runtime'])]
   if rid in ['R02','R03','R04','R06','R07','R09','R10','R11','R12','R14','R15','R16','R17']:e+=screens if rid in ['R03','R14','R15','R16','R17'] else [z for z in screens if z['checkpoint'] in ch['at'] or z['checkpoint']=='top' and 'initial' in ch['at']]
   if rid in ['R09','R13','R14','R15','R16','R17']:e+=srcEv
   r={'ruleId':rid,'status':'passed','evidence':e,'rationale':base[rid],'clusterIds':[]}
   caseDetails={
    ('initial_01','R05'):'Disabled s10 is denied with no callback; f09 yields select_slot:f09 once; retapping f09 yields no event.',
    ('initial_01','R07'):'Consent is absent both with nil selection and after the free f09 caller echo.',
    ('initial_01','R08'):'Initial confirmation is natively disabled and denied with zero callback; free f09 enables it and real activation yields confirm:f09 once.',
    ('initial_02','R05'):'Activating the free e08 row yields exactly select_slot:e08.',
    ('initial_02','R07'):'The native Switch has exact €32.50 consent label/value 0, native leaf tap yields fee_accepted:true, caller echo changes value to 1, and free e08 selection removes consent.',
    ('initial_02','R08'):'Initial confirm is disabled/denied. Consent echo enables confirm:e17 once; subsequent free e08 selection leaves confirmation enabled.',
    ('initial_03','R07'):'Consent stays absent for free t09 despite supplied feeAccepted=true.',
    ('initial_03','R08'):'The enabled footer is exposed by ordinary parent scrolling and real activation yields exactly confirm:t09.',
    ('initial_04','R08'):'No actions are rendered and the actual callback trace remains empty.',
    ('initial_04','R09'):'The loading tree ignores stale chooser fields; no row, summary, warning, consent, guidance or action is exposed.',
    ('initial_05','R08'):'Rendering emits no terminal action; the sole retry is bound to the real Check again activation.',
    ('initial_06','R08'):'Rendering emits no terminal action; the sole done is bound to the real Done activation.',
    ('repair_holdout_01','R07'):'Initially accepted d08 consent is On; unavailable/removal caller replacements hide it, and subsequent free d12 selection keeps it absent.',
    ('repair_holdout_02','R07'):'Accepted x10 toggles Off then On through native leaf taps, emitting fee_accepted:false then fee_accepted:true. Selecting x15 changes the label to AED 975.50 and caller echo resets value Off.'}
   if (cid,rid) in caseDetails:r['rationale']=caseDetails[(cid,rid)]
   if cid=='repair_holdout_01' and rid in ['R03','R04','R06','R07','R08','R09']:
    r['rationale']+=' The actual same-instance/process fixture indices progress 0→1→2. d08 is initially eligible/selected/accepted, then disabled with the full new reason, then absent; the two invalid updates clear native selection/summary/consent, show the warning without guidance, and disable confirmation. d12 activation then yields select_slot:d12, free summary/selection and confirm:d12; each forbidden disabled attempt and each caller replacement adds no event.'
   if cid=='repair_holdout_01' and rid in ['R14','R15']:
    r['status']='unassessed'
    r['rationale']='Visible initial top and later invalid/free screenshots are readable and match the specified treatment. Initial accepted-fee summary footer, consent, guidance and enabled confirmation are below the viewport and never scrolled into a screenshot before the first caller replacement. Native AX exposes their complete labels/value/enabled state, but initial footer pixel wrapping/palette is unobserved; do not infer a production defect or a complete visual pass.'
    r.setdefault('unassessedMethods',[]).append({'method':'initial_accepted_fee_footer_screenshot','reason':'No ordinary initial footer capture before apply_next_fixture; later bottom screenshots depict invalid/free replacement states.'})
   if cid=='repair_holdout_02' and unexecuted and rid in ['R04','R05','R06','R07','R08','R09']:
    r['status']='unassessed'
    supported={
      'R04':'Initial/current x10 is selected in native AX; x15 selection after activation is unobserved.',
      'R05':'The x15 row tap is never executed. The bounded reveal search stops after 24 steps with native_target_present=true and zero callback, so select_slot:x15 cannot be graded as a callback failure or pass.',
      'R06':'The AED 1,250.00 summary and Off/On guidance are observed correctly; new AED 975.50 summary/guidance after x15 selection is unobserved.',
      'R07':'Both actual native Switch leaf taps succeed, yielding exactly fee_accepted:false then fee_accepted:true and values 0 then 1. The changed paid-slot consent label/value reset is unobserved because x15 tap never executes.',
      'R08':'Initial confirmation enabled, Off-disabled/no-callback attempt, and On-enabled are directly observed; the post-x15 disabled gate is unobserved. No forbidden confirm event occurs.',
      'R09':'Consent echoes update the current model immediately. The replacement selection/price/reset branch is unobserved because x15 activation was not executed.'}
    r['rationale']=supported[rid]+' The x15 native Button is actually fully within the viewport and hittable during earlier sweep snapshot 10; later reveal snapshots alternate partial frames and stop at the search limit. This is missing action/dependent-state evidence, not proof of product absence or a production callback defect.'
    r.setdefault('unassessedMethods',[]).append({'method':'x15_native_activation_and_dependent_after_select_state','reason':'Actual step 6 outcome unavailable/reveal_step_limit_reached; activation_target empty; callback_delta empty. Earlier snapshot 10 proves present, fully-visible/hittable native row.'})
   if cid=='repair_holdout_02' and unexecuted and rid in ['R13','R15','R16']:
    r['rationale']+=' The x15 native row is actually fully visible and hittable at sweep snapshot 10 and all content/footer are pictured. Its later bounded reveal search does not execute a tap, so no x15 callback or changed-selection behavior is claimed by this native/layout verdict.'
    r.setdefault('unassessedMethods',[]).append({'method':'x15_actual_callback_activation','reason':'Later reveal search ends without activation; native presence/hittability and visual/scroll assertions are supported separately.'})
   if rid=='R13':r.setdefault('unassessedMethods',[]).extend([{'method':'expanded_native_hit_region_measurement','reason':'AX frame is a visual/semantic element frame; it does not expose expanded UIKit hit regions. Source minimum frames and successful actual native activation are separately evidenced.'}])
   if rid in ['R14','R15']:r.setdefault('unassessedMethods',[]).extend([{'method':'generic_swiftui_font_and_style_metadata','reason':'XCUI exporter does not expose generic SwiftUI font/padding/style values. Visual pixels and declarative source are used; no runtime metadata claim.'}])
   ratings.append(r)
  vscore=4 if sub=='submission-9e49d0' and cid=='repair_holdout_02' else 5
  vdetail=' At the largest type, the equal-width fee columns split Rescheduling fee inside the word and AED 1,250.00 across three lines including a split decimal fraction. All characters/order remain readable and no text overlaps or clips, but the cramped summary is a minor cosmetic deviation.' if vscore==4 else ''
  cases.append({'caseId':cid,'applicableRuleIds':c['applicableRuleIds'],'ratings':ratings,'visualScore':vscore,'visualRationale':('Partial visual score: initial accepted-fee footer pixels are unobserved before caller replacement; score applies to actually pictured initial top and invalid/free checkpoints. ' if cid=='repair_holdout_01' else '')+'Actual original top, reveal/action and bottom screenshots match the reference hierarchy and palette for the '+c['fixture']['model']['mode']+' branch. Complete content wraps readably and rendered controls use appropriate native/state treatment. Normal native typography, icons and line breaks do not materially alter hierarchy.'+vdetail,'visualEvidence':screens,'observationPath':str(p/'observation.json'),'observationSha256':sha(p/'observation.json'),'capturePath':str(p/'capture.json'),'captureSha256':sha(p/'capture.json'),'sourceHashesVerified':True,'actualEnvironment':a['original_runtime'],'observedEvents':actual,'observerStatus':a['status'],'observerIssues':a['issues'],'nativeIdentifierAudit':audit,'scopeNote':'Real production SwiftUI View in simulator app; actual XCUI native controls/taps, Switch leaf target trace, callback deltas and same-process caller echo. Screenshot viewport is 600 logical points.'})
 sourceRationales={'R01':'Public Codable model properties/initializers, enum raw spellings, action cases and View initializer match the contract. Only existing native SwiftUI/Foundation APIs are imported. Independent source-bound iOS14/macOS11 target typechecks both pass; this does not establish behavior on old operating-system runtimes.','R09':'Effective selection derives from the current model and excludes unavailable IDs/non-choosing modes; no local competing selection/fee state or caller-data mutation.','R13':'Whole native Button rows carry coherent labels and selected traits; Toggle uses supplied Binding and actual disabled/enabled modifiers. The panel establishes an accessibility containment boundary before its identifier. Target minimum layout declarations are 44pt or larger; runtime reachability/state are separately graded.','R15':'ScaledMetric, expanding multiline Text and no line limits/shrink-to-fit/fixed text heights. Narrow/large native runtime evidence remains independently graded per supplied case.','R16':'Intrinsic VStack and ForEach, no nested vertical ScrollView, fixed panel height or bounded lazy container.','R17':'Environment color scheme selects explicit light/dark palette; leading alignments and native HStack mirror with layout direction. Custom ButtonStyle preserves explicit disabled row/button colors. Runtime contrast/direction remains independently graded.'}
 checks=[{'platform':'ios','ruleId':rid,'status':'passed','evidence':srcEv+([ev(comp,'independent_minimum_os_typecheck')]+[ev(comp.parent/z['log'],'typecheck_log',target=z['target']) for z in compat['commands']] if rid=='R01' else []),'rationale':why,'clusterIds':[]} for rid,why in sourceRationales.items()]
 def count(cs):
  rs=[r for c in cs for r in c['ratings']];return {s:sum(r['status']==s for r in rs) for s in ['passed','failed','unassessed']}|{'applicableCaseRulePairs':len(rs),'distinctDefectClusters':0}
 summary=count(cases)|{'observedCaseRulePairs':sum(r['status']!='unassessed' for c in cases for r in c['ratings']),'availableCaptureCaseRulePairs':sum(len(c['ratings']) for c in cases if c['caseId']in READY),'sourceChecksCount':6,'sourcePassed':6,'sourceFailed':0,'sourceUnassessed':0,'visualScores':[c['visualScore'] for c in cases],'initial':count(cases[:6]),'repairHoldout':count(cases[6:])}
 report={'schemaVersion':1,'phase':'FINAL','submission':sub,'stage':'initial_and_repair_holdout','gradingStatus':'draft_ios_final_pending_supported_cases','sealedAtUTC':None,'assessedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'blinding':{'armMappingUnknown':True,'selfReviewFindingsAccessed':False,'reviewMatchingDeferredUntilD0AndFinalSeals':True},'frozenDesign':old['frozenDesign'],'platforms':{'ios':{'scope':'Actual production SwiftUI View in app, native XCUI AX/control activation/callback traces and same-process caller updates; minimumOS source checks are separate from current simulator runtime.','cases':cases,'summary':summary}},'sourceChecks':checks,'clusters':[],'missingEvidence':[{'channel':'initial_accepted_fee_footer_screenshot','caseId':'repair_holdout_01','ruleIds':['R14','R15'],'status':'unassessed','scope':'Initial AX state is observed, but its accepted-fee footer is below viewport until first caller replacement; later footer images show invalid/free replacement states.'},{'channel':'supported_final_runtime_pending','caseIds':[c['caseId'] for c in O['cases'] if c['caseId']not in READY],'status':'unassessed_pending_capture'},{'channel':'expanded_native_hit_region_measurement','status':'not_exposed_by_xcui','scope':'Actual AX frames do not prove expanded UIKit hit region. Source declares minimum layout; actual activation establishes recorded targets are reachable.'},{'channel':'generic_swiftui_font_padding_style_metadata','status':'not_exposed_by_xcui','scope':'Use actual screenshots plus separate declarative source; do not fabricate generic runtime style values.'},{'channel':'ios14_macos11_runtime','status':'not_supplied','scope':'Source-bound minimum-target typechecks pass, but old-runtime visual/behavior observation is unavailable.'}]}
 for ready_case in cases:
  if ready_case.get('observerStatus')=='failed' and ready_case['caseId']=='repair_holdout_02':
   report['missingEvidence'].append({'channel':'x15_native_activation_and_dependent_after_select_state','caseId':'repair_holdout_02','checkpoint':'after_select','ruleIds':['R04','R05','R06','R07','R08','R09'],'status':'unassessed','scope':'Primary bounded native reveal search did not execute x15 tap; actual row exists and is fully visible/hittable in earlier sweep snapshot 10. No product callback failure is inferred.','evidence':ev(Path(ready_case['observationPath']),'actual_native_xcui_and_receipts',pointers=['/steps/6','/snapshots/10','/snapshots/31','/snapshots/32','/reveal_diagnostics'])})
 if len(READY)==len(O['cases']):
  assert report['platforms']['ios']['summary']['applicableCaseRulePairs']==84
  assert sum(report['platforms']['ios']['summary'][x] for x in ['passed','failed','unassessed'])==84
  report['gradingStatus']='sealed_ios_final';report['sealedAtUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
  report['missingEvidence']=[x for x in report['missingEvidence'] if not(x['channel']=='supported_final_runtime_pending' and not x['caseIds'])]
 out=G/f'{sub}-final-ios.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(sub,summary,'SHA256',sha(out),'sealedAtUTC',report['sealedAtUTC'])
(G/'final-ios-native-audit.json').write_text(json.dumps(all_audits,ensure_ascii=False,indent=2)+'\n')
