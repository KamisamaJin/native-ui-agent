import json,hashlib
from pathlib import Path
from datetime import datetime, timezone
submission=Path('review-records')
base=Path('own/native')
assets=submission/'review-assets'
def ref(p,**kwargs):
 p=Path(p);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),**kwargs}
def evidence(plat,case,snapshot):
 d=base/plat/case;o=json.loads((d/'observation.json').read_text());return [ref(d/'observation.json',snapshot=snapshot,state_id=o['snapshots'][snapshot].get('state_id')),ref(d/o['snapshots'][snapshot]['screenshot'],snapshot=snapshot)]
findings=[]
def finding(i,plat,case,cp,category,method,target,aspect,claim,expected,observed,ev):
 findings.append({'id':i,'platform':plat,'case':case,'checkpoint':cp,'category':category,'method':method,'target':target,'aspect':aspect,'certainty':'confirmed','claim':claim,'expected':expected,'observed':observed,'evidence':ev})
ev=evidence('ios','C04',3)+[ref(assets/'pixel-color-evidence.json')]
finding('WR4-01','ios','C04','initial / cp-initial.full','visual','native_pixels','waterRound.submit','disabled_surface_color','The disabled release surface receives a second fade and does not render the specified opaque disabled surface.','#293C2F','#1F3126; 101581 pixels in the inset control region.',ev)
finding('WR4-02','ios','C04','initial / cp-initial.full','visual','native_pixels','waterRound.submit','disabled_label_color','The disabled release label receives a second fade and is darker than the specified disabled text token.','#92A396','#596A5E; 2911 flat interior glyph pixels in the inset control region.',ev)
finding('WR4-03','ios','C04','initial / cp-initial.full','visual','native_pixels','waterRound.method.drip','selected_surface_color','The selected disabled method is faded instead of retaining its selected surface token.','#244F33','#1D3A28; 144378 pixels in the inset control region.',ev)
finding('WR4-04','ios','C04','initial / cp-initial.full','visual','native_pixels','waterRound.method.drip','method_name_foreground_color','The disabled method name is faded instead of retaining the required foreground color.','#E7F3E9','#829789; 2200 flat interior name glyph pixels in the inset control region.',ev)
finding('WR4-05','android','C02','initial / cp-initial.full','visual','visual','waterRound.method.drip','rate_visual_order','In RTL, the rate line places the number after the English words.','10 L per bed (English order, while the method arrangement mirrors).','L per bed 10 is drawn in snapshots 3 and 4.',evidence('android','C02',4)+[ref(base/'android/C02/fixtures.json')])
for i,case,idx,n in [('WR4-06','C02',11,20),('WR4-07','C03',18,8)]:
 finding(i,'android',case,'a03 / cp-a03.full','integration','native_ax','waterRound.reserveConsent','observable_control_label','The checked consent control includes its decorative checkmark in the observable label.',f'Use {n} L from the protected reserve',f'✓, Use {n} L from the protected reserve',evidence('android',case,idx)+[ref(assets/f'android-{case}-checks.json',assertion='cp-a03.full:reserveConsent:label')])
summary=json.loads((assets/'typed-checks-summary.json').read_text());counts={k:sum(s['counts'][k] for s in summary) for k in ['passed','failed','unassessed']}
inventory=[]
for plat in ['ios','android']:
 for case in ['C01','C02','C03','C04']:
  for filename in ['observation.json','fixtures.json','manifest.json']:inventory.append(ref(base/plat/case/filename,review_method='native facts / caller input / execution metadata'))
for case in ['C01','C02','C03','C04']:inventory.append(ref(Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/dispatch-forward/private/inputs/d0-v2')/case/'mapping.json',review_method='checkpoint mapping only'))
inventory+=json.loads((assets/'viewed-image-inventory.json').read_text())
for p in assets.glob('*.json'):
 if p.name!='viewed-image-inventory.json':inventory.append(ref(p,review_method='derived typed or pixel review artifact'))
for p in assets.glob('*.png'):inventory.append(ref(p,review_method='viewed viewport contact sheet of original state images'))
for name in ['brief.md','api.md','reference.svg','public-example.json']:inventory.append(ref(Path('public')/name,review_method='independent public requirement / design intention'))
implementation=json.loads((submission/'implementation.json').read_text());workspace=Path(implementation['workspace'])
source_unchanged=all(hashlib.sha256((workspace/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in implementation['changed_files'])
for f in implementation['changed_files']:inventory.append(ref(workspace/f['path'],review_method='source API / static review; never used to replace runtime assertions'))
inventory.append(ref(submission/'d0-corpus-seal.json',review_method='corpus integrity reference'))
record={
 'schema_version':1,'submission':'sample-716d41','tool':'opaque-collector','phase':'read_only_review',
 'started_at':'2026-10-20T01:19:33Z','finished_at':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),
 'status':'findings','production_source_unchanged':source_unchanged,'native_recaptures':0,
 'findings':findings,
 'related_clusters':[
  {'id':'ios-disabled-fade','findings':['WR4-01','WR4-02','WR4-03','WR4-04'],'root_cause_hypothesis':'PlainButtonStyle adds disabled opacity to the custom rendered label. Four atomic aspects share one likely cause; they are not four independent root causes.','related_observed_occurrences':[{'platform':'ios','case':'C02','checkpoint':'initial / cp-initial.full','target':'waterRound.submit','aspect':'disabled_surface_color','observed':'Same #1F3126 background and #596A5E glyph interiors in snapshot 5.','evidence':evidence('ios','C02',5)},{'platform':'ios','case':'C04','checkpoint':'a03 / cp-a03.full','target':'waterRound.submit','aspect':'disabled_surface_color','observed':'Same faded release palette in snapshot 13.','evidence':evidence('ios','C04',13)}]},
  {'id':'android-rtl-rate','findings':['WR4-05'],'root_cause_hypothesis':'A number-leading English rate inherits the RTL base direction.','related_observed_occurrences':[{'platform':'android','case':'C02','checkpoint':'initial / cp-initial.full','target':'waterRound.method.soak','aspect':'rate_visual_order','observed':'L per bed 14 is drawn in the same state; same text-direction cause, not independently counted.','evidence':evidence('android','C02',4)}]},
  {'id':'android-consent-decoration','findings':['WR4-06','WR4-07'],'root_cause_hypothesis':'The text checkmark remains a descendant native Text leaf in the exported control label. C03 repeats the same defect with a different amount, not a separate root cause.'}
 ],
 'typed_checks':{'runner':'opaque-collector/scripts/native_checks.py evaluate and callback_verdict','scope':'Supplied atomic review plan derived solely from public rules and allowed caller fixtures. No complete-requirements claim.','counts':counts,'per_case':summary},
 'checked_scope':[
  {'scope':'Both platforms C01-C04, initial and caller-replaced full-content states','methods':['native_ax','native_action','visual'],'checked':'Read 52 original full-sweep images via eight viewport contact sheets; assigned tool recomputed complete per-state interval unions for all 16 full-content states. Reviewed content order, wrapping/reachability, root surface, selections, conditional controls, summary amounts, status and release labels.'},
  {'scope':'Both platforms C01-C04 native controls and local selectors','methods':['native_ax'],'checked':'Typed labels, conditional presence, selected/checked state, native role and enabled state against current caller input. Post-request target observations also checked for no local consent/selection/release projection change.'},
  {'scope':'Both platforms C01-C04 action intervals','methods':['native_action'],'checked':'Exact callback payloads and caller-replacement quietness were checked only through successful same-input/same-instance dispatch with exact event intervals. Four disabled routes per platform remain U; no empty-event pass was claimed.'},
  {'scope':'Android C01-C04 plain native Text fields and native touch bounds','methods':['native_text_layout','native_bounds'],'checked':'Native font_sp for title/description/facts/notice/status where present, plus native exported touch_width/touch_height >=44 for observed controls. This is not an OS physical-touch execution claim.'},
  {'scope':'iOS C04 initial disabled colors and related original images','methods':['native_pixels'],'checked':'Original screenshot RGB histograms bound to actual observed control geometry; backgrounds and flat glyph interiors compared with the independent public palette.'},
  {'scope':'Public production API and data flow','methods':['source_review'],'checked':'Static public model/action signatures and controlled projection architecture; source declarations were not used as native behavior, typography, padding or physical hit-region evidence.'}
 ],
 'unassessed_scope':[
  {'scope':'iOS runtime typography, exact internal padding and physical hit regions','status':'unavailable','reason':'XCUI exports AX/control geometry, not these native facts. No screenshot or source substitution.'},
  {'scope':'Both platforms exact internal padding and exact native corner radius/border declarations','status':'unavailable','reason':'Visual appearance was inspected, but observer has no direct internal padding/radius/border attribute export.'},
  {'scope':'Android mixed summary span typography and monospaced digit feature; resolved regular font weight','status':'unavailable','reason':'Top-level native Text fields do not establish every annotated run or an unspecified resolved regular weight.'},
  {'scope':'Both platforms C04 a01,a02,a04,a05 disabled callback behavior','status':'unavailable','reason':'Native routes were blocked_disabled; eight callback verdicts are U. Native disabled state itself was observed.'},
  {'scope':'Unseen cases and unexecuted branches, including shortfall, soak disallowed, and selected-method activation no-op','status':'not_executed','reason':'These combinations/routes are absent from the assigned corpus; no runtime business pass inferred from source.'},
  {'scope':'iOS 14 and macOS 11 runtime; Android Activity/navigation/lifecycle or OS physical touch','status':'not_executed','reason':'Outside the captured native configurations.'},
  {'scope':'Full-content visual coverage after each individual tap','status':'unavailable','reason':'Action checkpoints provide target observations, not independent full sweeps; full claims limited to the 16 recorded full-content states.'}
 ],
 'evidence_inventory':inventory,
 'review_limits':'Seven atomic findings form three related root-cause clusters. Native typed checks and visual/pixel judgments are separate. No other submission, oracle, holdout or external grader findings were read. Production source was not modified.'
}
(submission/'review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'review':str(submission/'review.json'),'finished_at':record['finished_at'],'findings':len(findings),'root_cause_clusters':3,'typed_counts':counts,'production_source_unchanged':source_unchanged,'inventory_files':len(inventory)}))
