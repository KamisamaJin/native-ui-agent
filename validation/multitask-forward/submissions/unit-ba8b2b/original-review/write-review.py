from pathlib import Path
import time,json,hashlib,datetime
root=Path(__file__).resolve().parent.parent.parent
out=root/'agent-output/review'
base=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward')
corpus=base/'own-corpora/unit-ba8b2b/d0'
submission=base/'submissions/unit-ba8b2b'
design=base/'design-v2/T3/public'

def evidence(path):
 path=Path(path)
 return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

findings=[];coverage=[];machine=[]
reference=json.loads((design/'reference.json').read_text())
color_states={'P1':{'loaded','reasoned','advanced','replaced'},'P2':{'advanced','classified','submitted'}}
for case in ['P1','P2']:
 for platform in ['ios','android']:
  report_path=submission/'own-checks/d0'/case/platform/'report.json'
  obs_path=corpus/platform/case/'observation.json'
  obs=json.loads(obs_path.read_text());report=json.loads(report_path.read_text())
  plan_path=submission/'initial-agent-output/plans'/case/platform/'plan.json'
  plan=json.loads(plan_path.read_text());byid={a['id']:a for a in plan['assertions']}
  coverage.append({'case':case,'platform':platform,'original_counts':report['counts'],'states':report['states'],'original_observation':evidence(obs_path),'original_report':evidence(report_path),'original_command':evidence(report_path.with_name('command.json')),'original_check_log':evidence(report_path.with_name('check.log')),'reviewed_state_screenshots':['loaded','reasoned','advanced','classified','submitted','replaced'],'care_marked_native_facts_read':True})
  for a in report['assertions']:
   spec=byid[a['id']];state=a['state'];status=a['status'];reason=a['reason']
   ev=[evidence(report_path),evidence(obs_path),evidence(plan_path)]
   for i in a.get('snapshot_indices',[]):
    ev.append(evidence(obs_path.parent/obs['snapshots'][i]['screenshot']))
   if status=='failed':
    reason+='; product-related: replacement context changes to Study room, same mounted instance/input revision is retained, but focus and decisions reproduce the initial seed. This is not a geometry rounding or absent observation case.'
    machine.append({'case':case,'platform':platform,'id':a['id'],'classification':'product_related','retained':True})
   if platform=='ios' and spec['kind']=='text_layout':
    reason='Unassessed: generic SwiftUI computed typography/color/ellipsis unavailable; screenshots do not replace these native measurements.'
   findings.append({'case':case,'platform':platform,'state':state,'requirement_id':spec['requirement_id'],'assertion_id':a['id'],'aspect':spec.get('property',spec['kind']),'expected':spec.get('expected'),'unit':spec.get('unit'),'status':status,'origin':'original_typed_native_check','reason':reason,'original_actual':a.get('actual'),'evidence':ev})
  for state in ['loaded','reasoned','advanced','classified','submitted','replaced']:
   cap=next(s for s in obs['state_captures'] if s['state_id']==state)
   ev=[evidence(obs_path)]+[evidence(obs_path.parent/obs['snapshots'][i]['screenshot']) for i in cap['snapshot_indices']]
   expected=reference['scenarios'][case][state]['visual-composition']
   fail_replacement=platform=='ios' and state=='replaced'
   fail_color=platform=='ios' and state in color_states[case]
   status='failed' if fail_replacement or fail_color else 'passed'
   reason='Read original indexed PNGs. Text wraps readably; queue, inspector, classifications, summary, validation and primary are separated without observed overlaps. '
   if state in ['loaded','replaced']:
    reason+='Original native interval sweep is complete and the four supplied note paragraphs are visible in order through the bottom sentinel. '
   else:
    reason+='Judgment is scoped to the captured target regions for this selected state; it does not upgrade the action to a planned full-layout sweep. '
   if fail_replacement:reason+='Replacement presentation contradicts the approved replacement state: Botanical folio and original seed decisions remain instead of Harbor sketch and replacement seed. This duplicates the listed original typed failures.'
   if fail_color:reason+=' Disabled iOS controls visibly blend their specified border fill and muted ink with the canvas: the light disabled primary is pale (#ECE6F2 sample) rather than #DACDE5, and dark read-only controls are dimmer than #634E75/#C8B5D9. This is a visible palette contradiction, not a claimed native computed-style reading.'
   f={'case':case,'platform':platform,'state':state,'requirement_id':'visual-composition','aspect':'captured_visual_composition','expected':expected['value'],'unit':expected['unit'],'status':status,'origin':'original_manual_screenshot_review','reason':reason,'evidence':ev}
   if fail_replacement:f['duplicate_of_original_typed_failure']=True
   findings.append(f)
  if case=='P2':
   findings.append({'case':case,'platform':platform,'state':'classified','requirement_id':'activation-callback','aspect':'disabled_action_behavior','expected':[],'unit':'events','status':'unassessed','origin':'original_manual_native_review','reason':'Stable is correctly observed disabled and selected on the read-only bowl, but the native action is blocked_disabled with no successful dispatch. The empty callback interval cannot establish handler behavior.','evidence':[evidence(obs_path),evidence(report_path)]})

# Explicit evidence for the two independently inspected palette variants.
pixels=json.loads((out/'pixel-samples.json').read_text())
for item in pixels:
 case=item['case'];dark=case=='P2'
 findings.append({'case':case,'platform':'ios','state':item['state'],'requirement_id':'visual-composition','aspect':'disabled_visible_palette','expected':'Disabled controls use border fill and muted text: '+('#634E75 and #C8B5D9 in dark appearance.' if dark else '#DACDE5 and #746181 in light appearance.'),'unit':'string','status':'failed','origin':'original_manual_screenshot_review','reason':'Original screenshot interior sample confirms the disabled visible palette is composited to '+str(item['rgb_frequency'][:2])+'. Expected roles come directly from BRIEF.md. This concerns final visible pixels only; generic iOS computed color remains unassessed.','evidence':[evidence(item['screenshot']),evidence(corpus/'ios'/case/'observation.json'),evidence(design/'BRIEF.md'),evidence(out/'pixel-samples.json')]})

seal=json.loads((submission/'d0/seal.json').read_text());immutability=[]
for path,digest in seal['files'].items():
 p=root/path
 if p.is_file():immutability.append({'path':path,'expected':digest,'actual':hashlib.sha256(p.read_bytes()).hexdigest(),'unchanged':hashlib.sha256(p.read_bytes()).hexdigest()==digest})
for p in (submission/'initial-agent-output/plans').rglob('*.json'):
 local=root/'agent-output/plans'/p.relative_to(submission/'initial-agent-output/plans')
 immutability.append({'path':str(local.relative_to(root)),'expected':hashlib.sha256(p.read_bytes()).hexdigest(),'actual':hashlib.sha256(local.read_bytes()).hexdigest(),'unchanged':local.read_bytes()==p.read_bytes()})
(out/'immutability.json').write_text(json.dumps(immutability,indent=2)+'\n')
start=json.loads((out/'phase-start.json').read_text())
record={'version':1,'startedAtUnix':start['startedAtUnix'],'finishedAtUnix':time.time(),'coverage':coverage,'limits':['Read-only review; no source, plans, actions, bridge, design or build configuration edits.','No SDK, observer, render, preview, emulator or app-launch command executed.','All original typed failures and unsupported checks retained, with 10 original iOS replacement failures classified product-related.','P2 disabled classification dispatch is unassessed on both platforms.','iOS generic computed typography/color/ellipsis remain unassessed.','Android uses native semantic OnClick in the original continuous Compose host; this does not prove OS physical gestures or Activity lifecycle.','Contact sheets derive only from original actual PNGs and retain original indices/state labels.','Canvas outside the Android component belongs to the capture host; its visible theme difference is not attributed to production outer padding.','Only P1/P2 public fixtures/actions were exercised; unknown focus, optional pending and invalid care seed combinations outside these routes remain source-reviewed, not runtime-proven.'],'machine_failure_ids':machine,'root_cause_clusters':[{'id':'ios-replacement-seed','classification':'confirmed_product_contradiction','description':'New caller context appears while local state resets to initial caller seed; ten typed state/aspect failures across P1/P2.'},{'id':'ios-disabled-visible-palette','classification':'confirmed_visible_product_contradiction','description':'Disabled button appearance blends the specified fill and text into the canvas, confirmed in original light and dark screenshots. Native computed styles remain U.'}],'immutability':{'all_unchanged':all(x['unchanged'] for x in immutability),'record':evidence(out/'immutability.json')},'findings':findings,'commands':{'review_operations':['Read authorized review prompt and original own reports/observation JSON','Generated original-index contact sheets with agent-output/review/contact-sheets.py','Viewed all 24 case/platform/selected-state contact sheets','Read care-marked native facts and original dispatch/callback records','Sampled original PNG pixels within original native control frames','Compared workspace source and plan SHA256 with sealed original submissions','Generated this report using agent-output/review/write-review.py'],'errors':[],'original_check_command_records':[str(submission/'own-checks/d0'/c/p/'command.json') for c in ['P1','P2'] for p in ['ios','android']]},'contact_sheet_index':evidence(out/'contact-sheet-index.json')}
record['elapsedSeconds']=record['finishedAtUnix']-record['startedAtUnix']
(out/'review.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'elapsedSeconds':record['elapsedSeconds'],'findings':len(findings),'machine_failures':len(machine),'all_source_and_plans_unchanged':record['immutability']['all_unchanged']},indent=2))
