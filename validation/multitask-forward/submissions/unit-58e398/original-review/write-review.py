import json,time,hashlib,collections,shutil
from pathlib import Path
from PIL import Image
out=Path(__file__).resolve().parent
w=out.parents[1]
root=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward')
corpus=root/'own-corpora/unit-58e398/d0'
submission=root/'submissions/unit-58e398'
design=root/'design-v2/T1/public'
states=['loaded','chosen','details','optioned','submitted','replaced']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evidence(*paths):return [{'path':str(p),'sha256':sha(p)} for p in dict.fromkeys(paths)]
findings=[];coverage=[];machine=[];unchanged=[];commands=[]
original=out/'original-records';original.mkdir(exist_ok=True)
# Compare every frozen production input, not only the newly added files.
for p in sorted((submission/'d0/source').rglob('*')):
 if not p.is_file():continue
 target=w/p.relative_to(submission/'d0/source')
 unchanged.append({'path':str(target),'frozenPath':str(p),'sha256':sha(target),'frozenSHA256':sha(p),'byteIdentical':target.read_bytes()==p.read_bytes()})
for p in sorted((submission/'initial-agent-output/plans').rglob('*.json')):
 target=w/'agent-output/plans'/p.relative_to(submission/'initial-agent-output/plans')
 unchanged.append({'path':str(target),'frozenPath':str(p),'sha256':sha(target),'frozenSHA256':sha(p),'byteIdentical':target.read_bytes()==p.read_bytes()})
(out/'immutability.json').write_text(json.dumps(unchanged,indent=2)+'\n')
assert all(x['byteIdentical'] for x in unchanged)
for case in ['P1','P2']:
 for platform in ['ios','android']:
  base=corpus/platform/case;op=base/'observation.json';obs=json.loads(op.read_text())
  rp=submission/'own-checks/d0'/case/platform/'report.json';report=json.loads(rp.read_text())
  pp=submission/'initial-agent-output/plans'/case/platform/'plan.json';plan=json.loads(pp.read_text());assertions={x['id']:x for x in plan['assertions']}
  for src,label in [(rp.parent/'command.json','check-command.json'),(rp.parent/'check.log','check.log'),(corpus/platform/f'{case}-command.json','capture-command.json'),(corpus/platform/f'{case}-wrapper.log','capture-wrapper.log')]:
   dest=original/f'{case}-{platform}-{label}';shutil.copyfile(src,dest);commands.append({'original':str(src),'copy':str(dest),'sha256':sha(src)})
  caps={x['state_id']:x for x in obs['state_captures']}
  reviewed=[]
  for state in states:
   cap=caps[state];indices=cap['snapshot_indices'];screens=[base/obs['snapshots'][i]['screenshot'] for i in indices];reviewed+=indices
   coverage.append({'case':case,'platform':platform,'state':state,'snapshotIndicesReviewed':indices,'coverageComplete':cap.get('complete'),'nativeStateCoverage':report['states'][state],'evidence':evidence(op,*screens)})
   va=assertions[f'{state}/visual-composition']
   findings.append({'case':case,'platform':platform,'state':state,'requirement_id':'visual-composition','aspect':'visible_hierarchy_wrapping_notes_and_control_layout','expected':va['expected'],'unit':va['unit'],'status':'passed','origin':'original_visual_review','reason':'Inspected every original state sweep frame: title/context remain separate, cards retain their two columns, summary and body copy wrap, details are present only when expanded, confirmation preserves disclosure, and all four notes paragraphs are reachable through overlapping frames. This assessment excludes the separately recorded disabled-palette, replacement-state, canvas-host and computed-native-style issues.','evidence':evidence(op,*screens,design/'BRIEF.md')})
   if platform=='ios':
    disabled=[]
    for idx in indices:
     snap=obs['snapshots'][idx];im=None
     for group in snap.get('control_groups',[]):
      control=group.get('control') or {};ident=group.get('selector',{}).get('identifier')
      if ident not in ['pack.choiceA','pack.choiceB','pack.extra','pack.primary'] or control.get('enabled') is not False or not control.get('fully_within_viewport'):continue
      if ident in [x['identifier'] for x in disabled]:continue
      if im is None:im=Image.open(base/snap['screenshot']).convert('RGB')
      f=control['frame'];scale=im.width/snap['app_frame']['width'];box=(round((f['x']+2)*scale),round((f['y']+2)*scale),round((f['x']+f['width']-2)*scale),round((f['y']+f['height']-2)*scale))
      top=collections.Counter(im.crop(box).getdata()).most_common(2)
      disabled.append({'identifier':ident,'snapshot':idx,'dominantInteriorRasterColors':['#%02X%02X%02X'%rgb for rgb,_ in top]})
    findings.append({'case':case,'platform':platform,'state':state,'requirement_id':'visual-composition','aspect':'disabled_control_palette','expected':{'fill':'#C9D7CC' if case=='P1' else '#456251','text':'#53645B' if case=='P1' else '#B7C7BD'},'unit':'sRGB_hex_roles','status':'failed','origin':'original_visual_review','root_cause_cluster':'ios_disabled_visual_attenuation','reason':'Original screenshots visibly attenuate disabled controls beyond the frozen palette. Light disabled fill/text appear #E4EBE5/#9BA7A0 and dark disabled fill/text #2B3E33/#718378 rather than the specified border fill and muted text. Enabled surface/ink colors in the same frames match the intended roles. Raster evidence supports this appearance contradiction; it does not establish generic computed SwiftUI color properties.','actualRasterSamples':disabled,'evidence':evidence(op,*[base/obs['snapshots'][x['snapshot']]['screenshot'] for x in disabled],design/'BRIEF.md')})
   for a in report['assertions']:
    if a['state']!=state or a['status']!='unassessed' or a['id'].endswith('/visual-composition'):continue
    src=assertions[a['id']]
    findings.append({'case':case,'platform':platform,'state':state,'requirement_id':src['requirement_id'],'aspect':src.get('property',src['kind']),'expected':src['expected'],'unit':src['unit'],'status':'unassessed','origin':'original_typed_native_check','original_assertion_id':a['id'],'reason':('Public AX does not expose generic computed SwiftUI typography/color or native ellipsis facts; the screenshot assessment is separate.' if platform=='ios' and src['kind']=='text_layout' else a['reason']),'evidence':evidence(op,rp,pp,*screens[:1])})
  for m in report['machine_findings']:
   idx=m.get('snapshot_indices',[])
   item={'case':case,'platform':platform,'state':m['state'],'requirement_id':m['requirement_id'],'aspect':m.get('property',m['kind']),'expected':m['expected'],'unit':m['unit'],'status':'failed','origin':'original_typed_native_check','machine_failure_id':m['id'],'root_cause_cluster':'ios_replacement_seed_selection','classification':'product_related','reason':'Confirmed original contradiction, not numerical noise: replacement input explicitly seeds the available stove, caller update succeeds on the same native instance, but the displayed state is empty (1500 g), with Choose shared equipment and disabled cover/confirm. Original expectations and all failures are retained.','originalFailure':m,'evidence':evidence(op,rp,*[base/obs['snapshots'][i]['screenshot'] for i in idx],design/'cases'/case/'fixtures.json')}
   findings.append(item);machine.append({'case':case,'platform':platform,'id':m['id'],'classification':'product_related','retained':True})
  if platform=='ios':
   idx=caps['replaced']['snapshot_indices'][0]
   findings.append({'case':case,'platform':platform,'state':'replaced','requirement_id':'request-id-reset','aspect':'replacement_seed_membership','expected':['stove'],'unit':'item_ids','status':'failed','origin':'original_native_and_visual_review','duplicate_of_original_typed_failure':True,'related_machine_failure_ids':['replaced/derived-summary','replaced/option-enabled','replaced/eligibility-status','replaced/primary-enabled'],'root_cause_cluster':'ios_replacement_seed_selection','reason':'The actual replacement choiceB is not selected and lacks its check mark even though the caller seed contains stove. The current context and base load prove the new request is displayed; disclosure collapses and no callback is emitted correctly. This is another aspect of the already typed replacement failure, not an additional independent detection.','evidence':evidence(op,base/obs['snapshots'][idx]['screenshot'],design/'cases'/case/'fixtures.json',design/'BRIEF.md')})
  else:
   idx=caps['loaded']['snapshot_indices'][0];host=base/'sources/NativeObserverTest.kt'
   findings.append({'case':case,'platform':platform,'state':'loaded','requirement_id':'visual-composition','aspect':'canvas_color','expected':'#FFFFFF' if case=='P1' else '#101A14','unit':'sRGB_hex','status':'unassessed','origin':'original_visual_review','classification':'observation_limited','reason':'All states show a canvas different from the public palette. The original native capture host explicitly supplies #EDF1F6 for light and #0D1420 for dark at NativeObserverTest.kt:262. The component has no outer background. Attribution to a component defect remains unassessed because the capture host violates the frozen canvas input; component controls retain their specified palette.','applies_to_states':states,'evidence':evidence(op,base/obs['snapshots'][idx]['screenshot'],host,design/'BRIEF.md')})
  (out/f'{case}-{platform}-typed-summary.json').write_text(json.dumps({'status':report['status'],'counts':report['counts'],'failed_assertion_ids':report['failed_assertion_ids'],'states':report['states'],'limits':report['limits'],'reportEvidence':evidence(rp),'observationEvidence':evidence(op)},indent=2)+'\n')
started=json.loads((out/'phase-start.json').read_text())['startedAtUnix']
review={'phase':'original_read_only_self_review','startedAtUnix':started,'finishedAtUnix':time.time(),'budgetWallSeconds':720,'designLockSHA256':'24a80e813cb3a2638499d9294fcacc0439891c680211ce85981a7a9b590c6b2c','status':'failed','coverage':coverage,'findings':findings,'machineFailures':machine,'sourceAndPlansByteIdentical':True,'immutabilityRecord':str(out/'immutability.json'),'originalCommandRecords':commands,'reviewCommands':[{'argv':['python3','agent-output/review/make-contact-sheets.py'],'result':'success; derives contact sheets only from original screenshots'},{'argv':['python3','agent-output/review/write-review.py'],'result':'success; read-only original evidence inspection and new review artifacts only'}],'failedReviewCommands':[],'limits':['No source, plan, action, design, bridge or original evidence edits. No new SDK, render, observer, preview or app launch commands.','All 24 public case/platform/state combinations reviewed through the exact original snapshot indices in coverage and contact-sheet-manifest.json. Complete native interval coverage is acquisition evidence, not blanket business/style acceptance.','All eight original typed failures retained and classified as product-related; the two replacement seed membership observations are marked duplicates.','Generic computed iOS font size, weight, ink and ellipsis remain unassessed in every state, regardless of visual review.','Both P2 optional activations are blocked_disabled with no successful native dispatch, so their empty callback intervals remain unassessed.','Android canvas attribution is limited by hardcoded original host colors. No hypothetical host repair or recapture was performed.','Only the two public cases and original action routes are observed. Removal, last-item cover clearing, overweight seeds, duplicate/unknown seed IDs and additional input combinations are not newly exercised.','No repairs until separately authorized after the complete review cohort seal.']}
review['elapsedWallSeconds']=review['finishedAtUnix']-started
(out/'review.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'elapsedWallSeconds':review['elapsedWallSeconds'],'findings':dict(collections.Counter(x['status'] for x in findings)),'machineFailureCount':len(machine),'immutableFiles':len(unchanged),'review':str(out/'review.json')},indent=2))
