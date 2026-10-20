import pathlib,json,hashlib,time,datetime,collections,shutil
from PIL import Image
ROOT=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward')
WORK=ROOT/'cache/unit-ade847'; OUT=WORK/'agent-output/review'; DESIGN=ROOT/'design-v2/T2/public'
CORPUS=ROOT/'own-corpora/unit-ade847/d0'; SUB=ROOT/'submissions/unit-ade847'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def evidence(p):return {'path':str(p),'sha256':sha(p)}
def png_paths(ob,indices,folder):return [folder/ob['snapshots'][i]['screenshot'] for i in indices]
findings=[]; summaries=[]; originals=[]; samples=[]; all_unchanged={}
refs=json.load(open(DESIGN/'reference.json'))
for case in ['P1','P2']:
 for platform in ['ios','android']:
  folder=CORPUS/platform/case; obpath=folder/'observation.json'; ob=json.load(open(obpath))
  checkdir=SUB/'own-checks/d0'/case/platform; reportpath=checkdir/'report.json'; report=json.load(open(reportpath))
  planpath=SUB/'initial-agent-output/plans'/case/platform/'plan.json'; plan=json.load(open(planpath)); expected={a['id']:a for a in plan['assertions']}
  originals.append({'case':case,'platform':platform,'counts':report['counts'],'failed_assertion_ids':report['failed_assertion_ids'],'unassessed_assertion_ids':[a['id'] for a in report['assertions'] if a['status']=='unassessed'],'report':evidence(reportpath),'plan':evidence(planpath),'observation':evidence(obpath),'command':json.load(open(checkdir/'command.json')),'command_evidence':evidence(checkdir/'command.json'),'error_log':evidence(checkdir/'check.log'),'error_text':(checkdir/'check.log').read_text()})
  dest=OUT/'original-check-records'/case/platform; dest.mkdir(parents=True,exist_ok=True)
  for filename in ['command.json','check.log']:shutil.copy2(checkdir/filename,dest/filename)
  for a in report['assertions']:
   if a['status'] not in ['failed','unassessed'] or a['id'].endswith('/visual-composition'):continue
   spec=expected[a['id']]; indices=a.get('snapshot_indices',[])
   ev=[evidence(obpath),evidence(reportpath)]+[evidence(p) for p in png_paths(ob,indices,folder)]
   findings.append({'case':case,'platform':platform,'state':spec['state'],'requirement_id':spec['requirement_id'],'aspect':spec.get('property',spec['kind']),'expected':spec['expected'],'unit':spec['unit'],'status':a['status'],'origin':'original_typed_native_check','reason':a['reason']+(' The original same-instance replacement has current context/max but old channel seeds; this is product-related, corroborated in original PNG/native labels.' if a['status']=='failed' else ' Unsupported SwiftUI computed style or unsuccessful disabled stimulus stays unassessed; visual review does not turn it into a computed native measurement.'),'machine_failure_id':a['id'] if a['status']=='failed' else None,'classification':'product_related' if a['status']=='failed' else 'observation_limited','actual':a.get('actual'),'root_cause_cluster':'ios-replacement-seeding' if a['status']=='failed' else None,'evidence':ev})
  states=[]
  for state in ['loaded','leveled','previewed','muted','submitted','replaced']:
   capture=next(s for s in ob['state_captures'] if s['state_id']==state)
   indices=capture['snapshot_indices']
   step=next((s for s in ob['steps'] if s.get('state_id',s.get('action',{}).get('state_id'))==state),{})
   target_indices=step.get('observation_set',{}).get('snapshot_indices',[])
   scoped_indices=indices if state in ['loaded','replaced'] else target_indices or indices[:2]
   states.append({'state':state,'full_content_selected':state in ['loaded','replaced'],'original_capture':capture,'reviewed_full_sweep_indices':indices if state in ['loaded','replaced'] else [],'reviewed_target_indices':scoped_indices,'dispatch':step.get('dispatch'),'callback_delta':step.get('callback_delta',[])})
   findings.append({'case':case,'platform':platform,'state':state,'requirement_id':'visual-composition','aspect':'readable hierarchy and wrapping in selected capture scope','expected':'Wrap notes, labels, summaries and inspection text; never truncate them. All supplied long note paragraphs appear in order below the primary action under Operator notes.','unit':'string','status':'passed','origin':'original_manual_visual_review','reason':('Original overlapping loaded/replaced sweep includes the entire panel, all four note paragraphs and bottom sentinel; headings, stacked channel labels, control strips, monitor and primary remain readable without visible overlap or ellipsis.' if state in ['loaded','replaced'] else 'Original target frames show readable labels, current numbers, mode/mute markers, monitor and primary in their captured regions. Offscreen content is not included in this pass.')+' This narrow layout/readability result does not override the separately recorded business, palette or unavailable computed-style findings.','design_source':str(DESIGN/'BRIEF.md'),'evidence':[evidence(obpath)]+[evidence(p) for p in png_paths(ob,scoped_indices,folder)]})
   if platform=='ios':
    found=None
    for identifier in ['mixer.primary','mixer.musicPlus','mixer.voiceMinus']:
     for i in indices:
      s=ob['snapshots'][i]
      n=next((n for n in s['nodes'] if n.get('identifier')==identifier and n.get('enabled')==False and n.get('fully_within_viewport')),None)
      if n:
       p=folder/s['screenshot']; im=Image.open(p).convert('RGB'); factor=im.width/s['app_frame']['width']; f=n['frame']
       box=tuple(round(v*factor) for v in [f['x']+3,f['y']+3,f['x']+f['width']-3,f['y']+f['height']-3])
       rgb,count=collections.Counter(im.crop(box).getdata()).most_common(1)[0]; actual='#FF%02X%02X%02X'%rgb
       found={'case':case,'platform':platform,'state':state,'identifier':identifier,'snapshot_index':i,'frame':f,'crop_pixels':box,'dominant_fill':actual,'dominant_pixel_count':count,'original_png':evidence(p)};break
     if found:break
    if found:
     samples.append(found); color='#FFC8D7E5' if case=='P1' else '#FF405971'
     if found['dominant_fill']!=color:
      findings.append({'case':case,'platform':platform,'state':state,'requirement_id':'visual-composition','aspect':'disabled control rendered border-fill color','expected':color,'unit':'argb','status':'failed','origin':'original_manual_visual_review','reason':f"BRIEF specifies disabled controls use the border fill. The disabled {found['identifier']} has a broad flat rendered fill {found['dominant_fill']}, visibly dimmer than the specified {color}; the original screenshot is corroborated by dominant interior pixel sampling. This is a rendered color-role contradiction, not a computed SwiftUI style measurement. Native enabled=false is retained. Extra disabled opacity is a plausible source cause, not yet repaired.",'root_cause_cluster':'ios-disabled-style-opacity','actual':found['dominant_fill'],'design_source':str(DESIGN/'BRIEF.md'),'evidence':[evidence(obpath),found['original_png']]})
  summaries.append({'case':case,'platform':platform,'states':states,'issues':ob.get('issues',[]),'configuration':ob.get('configuration',ob.get('original_runtime'))})
  if platform=='ios':
   capture=next(s for s in ob['state_captures'] if s['state_id']=='replaced'); actual=[]
   for i in capture['snapshot_indices']:
    for n in ob['snapshots'][i]['nodes']:
     if n.get('identifier')=='mixer.roomMute' and n.get('fully_within_viewport'):actual.append({'snapshot':i,'label':n.get('label'),'selected':n.get('selected')})
   ev=[evidence(obpath)]+[evidence(p) for p in png_paths(ob,sorted({a['snapshot'] for a in actual}),folder)]
   findings.append({'case':case,'platform':platform,'state':'replaced','requirement_id':'replacement-restores-every-mute-flag','aspect':'Room tone mute seed and selected semantics','expected':True,'unit':'bool','status':'failed','origin':'original_manual_native_review','reason':'Public replacement fixture sets room.muted=true. Original replacement PNGs still show Mute without the selected marker, and the unique mixer.roomMute native node has selected=false. The same instance/updated input binding and visible new context/max establish the caller update. This is an additional observed aspect of the replacement-seeding root cause; original derived-load/headroom/overload failures remain separately preserved.','actual':actual,'root_cause_cluster':'ios-replacement-seeding','related_original_typed_failure_ids':report['failed_assertion_ids'],'duplicate_of_original_typed_failure':False,'design_source':str(DESIGN/'cases'/case/'fixtures.json')+'#/updates/0/channels/2/muted','evidence':ev})
  if platform=='android':
   first=next(s for s in ob['state_captures'] if s['state_id']=='loaded')['snapshot_indices'][0]; p=folder/ob['snapshots'][first]['screenshot']; im=Image.open(p).convert('RGB');rgb=im.getpixel((3,3));actual='#FF%02X%02X%02X'%rgb
   findings.append({'case':case,'platform':platform,'state':'loaded','requirement_id':'visual-composition','aspect':'canvas backdrop ownership and exact palette','expected':'#FFFFFFFF' if case=='P1' else '#FF101B29','unit':'argb','status':'unassessed','origin':'original_manual_visual_review','reason':'The original Android parent backdrop appears different from the design canvas. The component is transparent and the capture includes the surrounding host padding, so these original facts do not isolate component-owned canvas from host theme behavior. Retain as observation/ownership-limited; do not classify it as a confirmed production contradiction.','actual':actual,'evidence':[evidence(obpath),evidence(p)]})
for rel in ['alerttoast/Sources/AlertToast/BroadcastCueMixerPanel.swift','reply/Reply/app/src/main/java/com/example/reply/ui/components/BroadcastCueMixerPanel.kt']:
 own=WORK/rel; original=SUB/'d0/source'/rel;all_unchanged[rel]={'workspace_sha256':sha(own),'original_sha256':sha(original),'byte_identical':own.read_bytes()==original.read_bytes()}
for original in sorted((SUB/'initial-agent-output/plans').rglob('*.json')):
 rel=original.relative_to(SUB/'initial-agent-output');own=WORK/'agent-output'/rel;all_unchanged[str(rel)]={'workspace_sha256':sha(own),'original_sha256':sha(original),'byte_identical':own.read_bytes()==original.read_bytes()}
assert all(v['byte_identical'] for v in all_unchanged.values())
(OUT/'pixel-samples.json').write_text(json.dumps(samples,indent=2)+'\n')
(OUT/'native-summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
(OUT/'immutability-check.json').write_text(json.dumps(all_unchanged,indent=2)+'\n')
start=json.load(open(OUT/'phase-start.json')); now=time.time()
report={'version':1,'status':'read_only_review_complete','startedAtUnix':start['startedAtUnix'],'finishedAtUnix':now,'startedAtUtc':start['startedAtUtc'],'finishedAtUtc':datetime.datetime.fromtimestamp(now,datetime.timezone.utc).isoformat(),'wallSeconds':now-start['startedAtUnix'],'budgetSeconds':720,'coverage':{'cases':['P1','P2'],'platforms':['ios','android'],'selected_states':['loaded','leveled','previewed','muted','submitted','replaced'],'contact_sheets':evidence(OUT/'contact-sheet-index.json'),'scope':'Read original full loaded/replaced overlapping sweeps and original post-action target frames. Reviewed state/native reports and successful callback intervals, not only machine failures. All original machine failures and unsupported checks preserved.','immutable_source_and_plans_verified':True,'immutability':evidence(OUT/'immutability-check.json')},'limits':['No source, plan, action, design or bridge edit; no SDK/render/app-launch/check rerun commands.','Unsupported iOS computed font/color/weight/ellipsis remain unassessed; rendered pixel color comparison does not expose generic native styles.','P2 leveled music-plus dispatch is blocked_disabled on both platforms: no successful stimulus, so empty callback interval remains unassessed.','Android used a continuously mounted native ComposeView/Paparazzi and semantic compose_onclick, not physical device touches or Activity lifecycle.','iOS original runtime has the same process/instance across caller replacement, but the reset values contradict the replacement input.','Non-sweep visual passes are scoped to original target frames; offscreen visual appearance is not generalized from nearby regions.','Reference Arial export and native SF/Roboto line wrapping are not treated as pixel-identical typography.','No repair attempted; wait for all-six original review barrier.'],'original_typed_reports':originals,'findings':findings,'confirmed_failure_clusters':['ios-replacement-seeding','ios-disabled-style-opacity'],'manual_detection_note':'Typed failed rows use origin=original_typed_native_check. New Room tone selected-state observation shares the replacement root cause; disabled fill is a separate visible palette contradiction. Repeated state observations are not independent root causes.','commands_and_errors':{'original_check_commands_and_logs':'original-check-records/ retains exact original commands, timestamps, exit codes and check.log, including every original failed status.','review_commands':['Read assigned review prompt and immediately wrote phase-start.json','Read original observations/reports/commands and public original plans','Ran contact_sheets.py on existing PNGs only and inspected all 24 generated sheets','Read original PNG pixel colors with PIL, using existing native rectangles; wrote write_review.py report','Compared original source/plans byte-for-byte; no SDK commands'],'review_command_failures':[]},'pixel_sampling':evidence(OUT/'pixel-samples.json'),'native_summary':evidence(OUT/'native-summary.json')}
(OUT/'review.json').write_text(json.dumps(report,indent=2)+'\n')
seal={'sealedAtUnix':time.time(),'files':{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='review-seal.json'}}
(OUT/'review-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'wallSeconds':report['wallSeconds'],'findings':dict(collections.Counter(f['status'] for f in findings)),'confirmed_failure_clusters':report['confirmed_failure_clusters'],'original_machine_failure_count':sum(len(r['failed_assertion_ids']) for r in originals),'all_sources_and_plans_identical':True,'review_sha256':sha(OUT/'review.json')},indent=2))
