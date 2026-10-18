from pathlib import Path
import json,hashlib,datetime,collections
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/fresh-blind');G=B/'design/grader';O=json.loads((B/'design/private/oracle.json').read_text());audit=json.loads((G/'final-android-native-audit.json').read_text());now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ev(p,ch,**kw):return {'channel':ch,'path':str(p),'sha256':sha(p),**kw}
base={
 'R02':'The native tree retains the exact full service, location, old appointment day/time and correct context/title for this mode.',
 'R03':'Native ordered group and whole-row labels match caller order and complete time/detail/availability/fee-or-reason. The viewport sweep also exposes the full long reasons and metadata.',
 'R04':'Native selected flags and settled radio glyphs agree with the current effective eligible selection at every required checkpoint; invalid IDs select nothing.',
 'R05':'The actual row activations produce exactly the required single select callback. Selected reactivation is a no-op where exercised; unavailable rows expose disabled state and denied activation produces no event.',
 'R06':'Native summary, warning and guidance content/presence follows the model at every required checkpoint, preserving the selected group day, time and exact fee amount.',
 'R07':'Native Checkbox state and label follow caller feeAccepted only for eligible fee selection. Off/on activations and conditional hiding match the frozen protocol with no cached approval.',
 'R08':'Native confirm enabled state matches eligibility/fee gate. Actual enabled activation records exactly the current ID; denied disabled attempts emit nothing; render and model updates add no unsolicited terminal callback.',
 'R09':'The same attached composition reflects echoed actions and full caller replacements immediately. Invalidation/removal clears effective selection/summary/consent and gates confirmation, then free selection recovers correctly where exercised.',
 'R10':'Actual screenshots show the small progress indicator and loading copy. The native tree exposes visit.loading and shared context while all stale choosing content and actions are absent; no event occurs.',
 'R11':'The exact unavailable heading/full message and enabled Check again are present, stale controls are absent, and actual activation yields one retry.',
 'R12':'The green success card preserves the new day/time, full reference/note and previous appointment context. Stale chooser controls are absent and actual Done activation yields one done.',
 'R13':'Actual unmerged native nodes have unique required tags, coherent radio-row labels, selected/disabled flags, Checkbox value and Button enabled state, without duplicate activatable row children. Fully visible enabled target bounds meet the 48dp minimum (rounding tolerance 0.5dp); native semantic activation scope is stated separately.',
 'R14':'Inspected original viewport/checkpoint screenshots preserve the reference hierarchy, native system type, state surfaces, row outlines/radios, readable full-opacity unavailable content and explicit disabled-button colors. Native typography metadata and source corroborate the supplied tokens; ordinary native line breaks are accepted.',
 'R15':'Original viewport sweeps and action checkpoints show complete wrapping without ellipsis, horizontal overflow, overlap or fixed-height text clipping. Native labels retain the supplied strings. Parent-viewport clipping while scrolling is not product truncation; raw TextLayoutResult.hasVisualOverflow alone is not treated as a visible defect.',
 'R16':'Continuous parent ScrollState movement and screenshots expose every row/detail/reason, summary/consent and final action. The panel grows intrinsically; source declares no nested or fixed vertical viewport. This is native parent-state scrolling, not an OS gesture claim.',
 'R17':'Recorded theme/font/direction match the fixture. Actual light/dark screenshots preserve contrast and full disabled palette. In RTL, row radio/checkbox positions mirror and numeric time endpoints and fee strings remain in their supplied readable order.'
}
for sub in ['submission-9e49d0','submission-3dd8b6','submission-4f1781']:
 old=json.loads((G/f'{sub}-d0-android.json').read_text());src=list((B/'implementations/final'/sub/'reply').rglob('VisitReschedule*.kt'));srcEv=[ev(p,'source_review') for p in src];cases=[]
 for c in O['cases']:
  cid=c['caseId'];p=B/'evidence/final'/sub/'android'/cid;a=json.loads((p/'observation.json').read_text());cap=json.loads((p/'capture.json').read_text());au=next(z for z in audit if z['submission']==sub and z['caseId']==cid);assert not au['issues'];screens=[];seen=set()
  for ix,z in enumerate(a['snapshots']):
   h=sha(p/z['screenshot'])
   if h not in seen:seen.add(h);screens.append(ev(p/z['screenshot'],'screenshot',checkpoint=z['name'],snapshotIndex=ix))
  ratings=[]
  for check in c['checks']:
   rid=check['ruleId'];evidence=[ev(p/'observation.json','native_semantics_and_trace',checkpoints=check['at'])]
   if rid in ['R02','R03','R04','R06','R07','R09','R10','R11','R12','R14','R15','R16','R17']:evidence+=screens if rid in ['R03','R14','R15','R16','R17'] else [s for s in screens if s['checkpoint'] in check['at']]
   if rid in ['R09','R13','R14','R15','R16','R17']:evidence+=srcEv
   rationale=base[rid]
   if cid=='repair_holdout_01' and rid in ['R04','R06','R07','R08','R09']:rationale+=' Specifically: accepted d08 becomes unavailable, then disappears; both replacements show no effective selection/summary/consent and disabled confirmation. Selecting d12 restores the free summary and confirm:d12.'
   if cid=='repair_holdout_02' and rid in ['R04','R05','R06','R07','R08','R09']:rationale+=' Specifically: accepted x10 toggles Off then On, producing fee_accepted:false then fee_accepted:true. Selecting x15 yields select_slot:x15, AED 975.50, Off consent and disabled confirmation. No confirm event occurs.'
   if rid=='R13':rationale+=f' Minimum observed fully visible enabled touch dimension in this case: {au["minFullyVisibleTouchDP"]}dp.' if au['minFullyVisibleTouchDP'] is not None else ' This loading case renders no actionable target.'
   ratings.append({'ruleId':rid,'status':'passed','evidence':evidence,'rationale':rationale,'clusterIds':[]})
  assert set(x['ruleId'] for x in ratings)==set(c['applicableRuleIds'])
  visual=5;vr='Original screenshots follow the independent reference hierarchy, spacing, palette and state affordances with readable full content; differences are ordinary native font/glyph and wrapping variation.'
  if sub=='submission-9e49d0' and cid=='repair_holdout_02':visual=4;vr='The 2× RTL sweep remains complete, readable and operable with correct mirrored affordances and intact time/amount strings. The two-column fee summary makes Rescheduling fee break inside the word and splits AED onto its own line; this is a minor cosmetic cramped treatment, with no clipping, overlap, loss of content or material hierarchy harm.'
  if sub=='submission-4f1781' and cid in ['initial_05','repair_holdout_02']:vr+=' Mixed English paragraphs use native content-directed line alignment within semantic RTL leading containers; controls mirror and numeric ranges remain intact.'
  cases.append({'caseId':cid,'applicableRuleIds':c['applicableRuleIds'],'ratings':ratings,'visualScore':visual,'visualRationale':vr,'visualEvidence':screens,'observationPath':str(p/'observation.json'),'observationSha256':sha(p/'observation.json'),'capturePath':str(p/'capture.json'),'captureSha256':sha(p/'capture.json'),'sourceHashesVerified':True,'actualEnvironment':{'configuration':a['configuration'],'logicalViewportDP':a['snapshots'][0]['logical_viewport_dp']},'observedEvents':a['events'],'observerStatus':'complete_supported_capture','observerIssues':[],'nativeAudit':{**au,'derivativeAuditPath':str(G/'final-android-native-audit.json'),'derivativeAuditSha256':sha(G/'final-android-native-audit.json')},'scopeNote':a['scope']})
 checks=[]
 rationales={
 'R01':'The public Kotlin model/enum/action types and Composable signature match the contract. Production imports use existing Compose/Foundation/Material APIs. Each final source-bound native test command completed with exit code 0; no new dependency declaration is introduced in the sealed production archive.',
 'R09':'Effective selection and all branches derive directly from current immutable model properties; no remembered competing selection or consent state. Native caller-update evidence is separately graded per case.',
 'R13':'Production declares whole-row selectable radio semantics, Checkbox/toggleable consent and native buttons with unique meaningful IDs and minimum 48dp targets. Native exposure and observed target dimensions are separately graded.',
 'R15':'Text expands and wraps with scaled sp typography; no ellipsis/line limit, shrink-to-fit or fixed text height is declared. Actual narrow/large-text screenshots are separately graded.',
 'R16':'Intrinsic non-lazy Column, no nested scroll or fixed panel height; actual parent scrolling is separately graded.',
 'R17':'Semantic layout follows LayoutDirection and supplied light/dark palette. TextDirection.ContentOrLtr preserves numeric-only ranges under RTL; actual RTL ranges and mirrored controls are separately checked in initial_05 and repair_holdout_02.'}
 for rid,why in rationales.items():
  es=srcEv.copy()
  if rid=='R01':es+=[ev(B/'evidence/final'/sub/'android/initial_01/capture.json','native_build_and_source_binding'),ev(B/'evidence/final'/sub/'android/initial_01/test.log','build_log')]
  checks.append({'ruleId':rid,'platform':'android','status':'passed','evidence':es,'rationale':why,'clusterIds':[]})
 def counts(cc):
  rs=[r for c in cc for r in c['ratings']];return {s:sum(r['status']==s for r in rs) for s in ['passed','failed','unassessed']}|{'applicableCaseRulePairs':len(rs),'distinctDefectClusters':0}
 summary=counts(cases)|{'observedCaseRulePairs':84,'sourceChecksCount':6,'sourcePassed':6,'sourceFailed':0,'sourceUnassessed':0,'visualScores':[c['visualScore'] for c in cases],'initial':counts(cases[:6]),'repairHoldout':counts(cases[6:])};assert summary['passed']==84 and summary['initial']['passed']==59 and summary['repairHoldout']['passed']==25
 report={'schemaVersion':1,'phase':'FINAL','submission':sub,'stage':'initial_and_repair_holdout','gradingStatus':'sealed_android_final','blinding':{'armMappingUnknown':True,'selfReviewFindingsAccessed':False,'reviewMatchingDeferredUntilD0AndFinalSeals':True},'frozenDesign':old['frozenDesign'],'platforms':{'android':{'scope':'One continuously attached native ComposeView in the common settled Paparazzi session. Actual native semantics, semantic OnClick callbacks, caller model replacements and parent ScrollState screenshots. No physical OS touch/Activity/navigation/lifecycle claim.','cases':cases,'summary':summary}},'sourceChecks':checks,'clusters':[],'missingEvidence':[{'channel':'physical_os_touch_and_activity','status':'out_of_scope','scope':'Common Android observer does not provide OS touch, Activity or navigation/lifecycle evidence.'},{'channel':'apple_final_runtime','status':'separate_platform_deferred','scope':'This sealed artifact assesses Android only. Apple FINAL grading remains separate and unsealed pending all eight supported cases.'},{'channel':'progress_specific_semantics_property','status':'not_exported','scope':'The common exporter does not record progress-range properties. R10 uses actual visible progress pixels plus native loading copy and inspected native CircularProgressIndicator source; no exported progress-role claim.'}],'commonObserver':{'sampling':'settled native sampler; decorative radio/checkbox state inspected in actual final images','sourceBinding':'All 24 platform/case capture source hashes independently match the sealed FINAL Kotlin bytes.'},'sealedAtUTC':now}
 out=G/f'{sub}-final-android.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(out.name,sha(out),now,summary)
