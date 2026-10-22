from pathlib import Path
import json,hashlib,time,datetime,shutil,collections
O=Path(__file__).resolve().parent;W=O.parents[1]
C=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/own-corpora/unit-99c640/d0')
S=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/submissions/unit-99c640')
D=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T1/public')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evidence(p):return {'path':str(p),'sha256':sha(p)}
manifest=json.loads((O/'contact-sheet-manifest.json').read_text());mm={(m['case'],m['platform'],m['state']):m for m in manifest}
pixels=json.loads((O/'pixel-review.json').read_text());pm={(r['case'],r['platform'],r['state'],r['requirement_id']):r for r in pixels['results']}
findings=[];summaries=[];coverage=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  base=C/platform/case;obs_path=base/'observation.json';obs=json.loads(obs_path.read_text())
  rp=S/'own-checks/d0'/case/platform/'report.json';report=json.loads(rp.read_text())
  planpath=S/'initial-agent-output/plans'/case/platform/'plan.json';plan=json.loads(planpath.read_text());plans={a['id']:a for a in plan['assertions']}
  copydir=O/'original-check-records'/case/platform;copydir.mkdir(parents=True,exist_ok=True)
  for n in ['report.json','command.json','check.log']:shutil.copy2(rp.parent/n,copydir/n)
  command=json.loads((rp.parent/'command.json').read_text())
  summaries.append({'case':case,'platform':platform,'status':report['status'],'counts':report['counts'],'failed_assertion_ids':report['failed_assertion_ids'],'machine_findings':report['machine_findings'],'failure_classification':[],'original_command':command,'evidence':[evidence(rp),evidence(rp.parent/'command.json'),evidence(rp.parent/'check.log')]})
  for cap in obs['state_captures']:
   if cap['state_id'] in ['baseline','selected','expanded','blocked','replaced','reselected','submitted']:
    coverage.append({'case':case,'platform':platform,'state':cap['state_id'],'complete':cap['complete'],'max_gap':cap.get('max_gap'),'top_reached':cap.get('top_reached'),'bottom_reached':cap.get('bottom_reached'),'stable_binding':cap.get('stable_binding'),'snapshot_indices':cap['snapshot_indices'],'contact_sheet':mm[case,platform,cap['state_id']]['contact_sheet'],'evidence':[evidence(obs_path)]})
  for a in report['assertions']:
   original=plans[a['id']];state=a['state'];rid=original['requirement_id'];m=mm[case,platform,state]
   ev=[evidence(obs_path),evidence(rp)];status=a['status'];origin='original_typed_native_check';reason=f"Original typed assertion {a['id']} remains {a['status']}."
   if original['kind']=='manual':
    if rid in ['component-canvas-color','notice-surface-color','primary-surface-color']:
     pr=pm[case,platform,state,rid];status=pr['status'];origin='original_read_only_native_pixels_review'
     ev=[evidence(obs_path),evidence(O/'pixel-review.json')]+[{'path':s['image'],'sha256':s['sha256']} for s in pr['samples']]
     reason=f"Exact original policy strip read from {len(pr['samples'])} original native-bound image fragments; all valid samples satisfy support >= 0.95, zero channel tolerance and minimum 24 pixels. Applies only to the sampled strips."
    else:
     status='passed';origin='original_visual_self_review'
     ev=[evidence(obs_path)]+[{'path':s['path'],'sha256':s['sha256']} for s in m['sources']]
     if rid=='content-wrapping':reason='All required title, subtitle, notice, six labels, item details/reasons, summary, disclosure label, action and footer are readable across the complete exact-state original sweep. Guidance appears only when expanded. No clipping, ellipsis or missing required text observed. Narrow iOS Unavailable splits between characters because its unbroken segment exceeds available width, explicitly allowed by the brief.'
     else:reason='Inspected every original frame in this complete exact-state sweep; no unintended text/control collision or occlusion observed. Scroll viewport edges are not component clipping. This does not certify grid columns or other unsampled layout rules.'
   elif rid=='title-native-weight' and platform=='ios':
    status='unassessed';reason='Original typed check remains unassessed: public SwiftUI accessibility facts do not expose computed native font weight; screenshot appearance is not an exact native weight measurement.'
   findings.append({'case':case,'platform':platform,'state':state,'requirement_id':rid,'aspect':original.get('property',original['kind']),'expected':original['expected'],'unit':original['unit'],'status':status,'origin':origin,'original_typed_assertion_id':a['id'],'duplicate_of_original_typed_failure':a['id'] in report['failed_assertion_ids'],'reason':reason,'expectation_provenance':original['expectation_provenance'],'evidence':ev})
  findings.append({'case':case,'platform':platform,'state':'blocked','requirement_id':'disabled-activation-callback','aspect':'interaction_callback','expected':[],'unit':'events','status':'unassessed','origin':'original_native_stimulus_limit','reason':'Original action 4 is blocked_disabled with dispatch.succeeded=false. Empty callback_delta does not prove a successful disabled activation/handler test. The separate locked-choice-disabled typed rule passed; selected callback matrix intentionally marks this stimulus N/A.','evidence':[evidence(obs_path)],'source':str(D/'BRIEF.md')})
# This full-brief requirement is intentionally outside the selected 14-rule ledger.
allstates=['baseline','selected','expanded','blocked','replaced','reselected','submitted']
ev=[evidence(C/'ios/P1/observation.json')]
for state in allstates:
 first=mm['P1','ios',state]['sources'][0];ev.append({'path':first['path'],'sha256':first['sha256']})
findings.append({'case':'P1','platform':'ios','state':'baseline','affected_states':allstates,'requirement_id':'responsive-grid','aspect':'grid_column_count','expected':2,'unit':'columns','actual':1,'status':'failed','origin':'original_visual_self_review','duplicate_of_original_typed_failure':False,'root_cause_cluster':'ios-wide-grid-stays-single-column','reason':'The approved brief requires two columns at component child width >= 320pt and ordinary large Dynamic Type. Original runtime records offered width 390pt, actual component canvas width 358pt and large Dynamic Type. In all seven inspected states, choices a and b have the same x position and each spans the full inner 326pt, appearing one below the other. Original reference P1 draws two columns. This is a confirmed product contradiction outside the selected atomic denominator; no source repair was performed.','source':{'path':str(D/'BRIEF.md'),'sha256':sha(D/'BRIEF.md'),'section':'Product behaviour, first paragraph'},'evidence':ev})
initial=json.loads((W/'agent-output/implementation.json').read_text());source_checks=[]
for rel,expected in initial['source_sha256'].items():
 p=W/rel;name=p.name;sealed=list((S/'d0/source').rglob(name));source_checks.append({'path':str(p),'sha256':sha(p),'initial_sha256':expected,'unchanged':sha(p)==expected,'sealed_paths':[{'path':str(q),'sha256':sha(q),'identical':sha(q)==sha(p)} for q in sealed]})
seal=json.loads((W/'agent-output/plans-seal.json').read_text());unchanged_plans={rel:sha(W/rel)==v for rel,v in seal['files'].items()}
start=json.loads((O/'phase-start.json').read_text());finish=time.time()
review={'version':1,'phase':'original_read_only_self_review','status':'failed','startedAtUnix':start['startedAtUnix'],'startedAtUTC':start['startedAtUTC'],'finishedAtUnix':finish,'finishedAtUTC':datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat(),'elapsedSeconds':finish-start['startedAtUnix'],'wallBudgetSeconds':720,'coverage':{'cases':['P1','P2'],'platforms':['ios','android'],'states':allstates,'state_records':coverage,'original_frames_visually_inspected':sum(len(x['sources']) for x in manifest),'contact_sheet_manifest':str(O/'contact-sheet-manifest.json'),'manual_full_sweeps_reviewed':12,'policy_color_cells_reviewed':84,'business_trace':'All four routes show successful a selection, disclosure open, caller fixture replacement with no callback, b selection and b reservation; no reservation clears the draft. Action 4 was blocked_disabled.','source_identity':source_checks,'original_plan_and_script_hash_checks':unchanged_plans},'machine_reports':summaries,'machine_failure_ids':[],'machine_failure_classification':'All four original typed reports have zero failed_assertion_ids/machine_findings. Original exitCode 3 (needs_review) and U outcomes are retained unchanged, not relabeled as passing execution.','findings':findings,'counts':dict(collections.Counter(f['status'] for f in findings)),'limits':['Only original own-D0 captures, own typed reports and assigned public design were inspected. No hidden/evaluation/other candidate or version data accessed.','No SDK, app launch, observer, renderer, new screenshot, source edit, plan edit, bridge edit or repair was performed. Contact sheets crop/resize original PNGs only and retain original indices/state provenance.','Pixel results certify approved strips with suitable original semantic image mappings, not every pixel or computed SwiftUI styles.','The visual grid failure is outside the selected fourteen-rule atomic ledger. Other selected passes cannot erase it.','Both public cases are LTR. RTL, other incoming data, all-availability variants, incoming valid selections, physical touch regions, parent navigation/lifecycle and arbitrary font/width combinations remain unassessed.','Native disabled activation never succeeded; no absence-of-callback business pass is inferred from a blocked action. iOS computed title weight remains U in all fourteen state cells.','No source or plan changes after review; await all-six original review seal and explicit resume.'],'review_commands':[{'command':'python3 agent-output/review/make_contact_sheets.py','exitCode':0,'result':'28 sheets / 274 original state frames'},{'command':'python3 agent-output/review/pixel_review.py','exitCode':0,'result':'84 policy cells passed; no SDK execution'},{'command':'python3 agent-output/review/finalize_review.py','exitCode':0,'note':'Actual finish recorded within this command; shell reads and original-image view calls preserved in task tool history.'}],'errors':[]}
(O/'review.json').write_text(json.dumps(review,indent=2)+'\n')
artifacts=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='review-seal.json')
(O/'review-seal.json').write_text(json.dumps({'version':1,'sealedAtUnix':time.time(),'files':{str(p.relative_to(W)):sha(p) for p in artifacts}},indent=2)+'\n')
print(json.dumps({'elapsedSeconds':review['elapsedSeconds'],'counts':review['counts'],'source_unchanged':all(s['unchanged'] for s in source_checks),'plans_unchanged':all(unchanged_plans.values()),'review':str(O/'review.json')},indent=2))
