import collections,datetime,hashlib,json,pathlib,shutil,time
w=pathlib.Path(__file__).resolve().parents[2]
out=w/'agent-output/review'
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward')
corpus=b/'own-corpora/unit-df4422/d0'
checks=b/'submissions/unit-df4422/own-checks/d0'
plans=b/'submissions/unit-df4422/initial-agent-output/plans'
design=b/'design-v2/T1/public'
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ev=lambda p:{'path':str(p),'sha256':hashfile(p)}
manifest=json.loads((out/'contact-sheets.json').read_text())
contacts={(m['case'],m['platform'],m['state']):m for m in manifest}
samples={(s['case'],s['state']):s for s in json.loads((out/'palette-samples.json').read_text())}
findings=[];ledger=[];coverage=[];machine=[];counts=collections.Counter();source_records=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  observation=corpus/platform/case/'observation.json';ob=json.loads(observation.read_text())
  reportpath=checks/case/platform/'report.json';report=json.loads(reportpath.read_text())
  planpath=plans/case/platform/'plan.json';plan=json.loads(planpath.read_text());expected={x['id']:x for x in plan['assertions']}
  source_records.extend([ev(observation),ev(reportpath),ev(planpath)])
  target=out/'original-check-records'/case/platform;target.mkdir(parents=True,exist_ok=True)
  for filename in ['report.json','command.json','check.log']:shutil.copy2(checks/case/platform/filename,target/filename)
  counts.update(report['counts'])
  states={x['state_id']:x for x in ob['state_captures']}
  for assertion in report['assertions']:
   p=expected[assertion['id']];state=assertion['state'];rule=p['requirement_id'];contact=contacts[(case,platform,state)]
   evidence=[ev(observation),ev(reportpath)]+[{'path':s['path'],'sha256':s['sha256']} for s in contact['original_sources']]
   ledger.append({'case':case,'platform':platform,'state':state,'requirement_id':rule,'id':assertion['id'],'expected':p.get('expected'),'unit':p.get('unit'),'status':assertion['status'],'reason':assertion.get('reason'),'actual':assertion.get('actual'),'snapshot_indices':assertion.get('snapshot_indices',[])})
   if assertion['status']=='failed':
    original=next(x for x in report['machine_findings'] if x['id']==assertion['id']);machine.append({'case':case,'platform':platform,'original':original})
    findings.append({'case':case,'platform':platform,'state':state,'requirement_id':rule,'aspect':p.get('property',p['kind']),'expected':p.get('expected'),'unit':p.get('unit'),'status':'failed','origin':'original_typed_native_check','original_machine_failure_id':assertion['id'],'classification':'product-related','root_cause_cluster':'ios-replacement-seed-reset','reason':'Confirmed in the original native facts and corresponding original screenshots: the caller replacement is bound to fixture_index=1 with the same instance and no callback, and its public seed contains stove, but the UI has zero selected items. This contradicts this original expectation; the exact reset mechanism is not proven. No measurement-noise override is applied.','evidence':evidence})
   elif assertion['status']=='unassessed' and rule!='visual-composition':
    reason=assertion.get('reason','')
    if platform=='ios' and p['kind']=='text_layout':reason='Unsupported generic computed SwiftUI typography/color/ellipsis field. Original U is retained; visual review does not establish this native property.'
    findings.append({'case':case,'platform':platform,'state':state,'requirement_id':rule,'aspect':p.get('property',p['kind']),'expected':p.get('expected'),'unit':p.get('unit'),'status':'unassessed','origin':'original_typed_native_check','reason':reason,'evidence':evidence})
  for state in ['loaded','chosen','details','optioned','submitted','replaced']:
   sc=states[state];contact=contacts[(case,platform,state)];p=expected[state+'/visual-composition']
   evidence=[ev(observation)]+[{'path':s['path'],'sha256':s['sha256']} for s in contact['original_sources']]
   visual={'case':case,'platform':platform,'state':state,'requirement_id':'visual-composition','aspect':'native hierarchy, palette, typography appearance, wrapping, selected/disabled appearance and long notes','expected':p['expected'],'unit':p['unit'],'origin':'original_manual_visual','evidence':evidence,'expectation_provenance':p['expectation_provenance']}
   if platform=='ios':
    sample=samples[(case,state)]
    visual.update({'status':'failed','root_cause_cluster':'ios-disabled-palette-opacity','reason':f"Original screenshots show readable labels and complete ordered notes without overlap or truncation, but disabled controls are visibly faded away from the fixed border/disabled palette. In this state, {sample['target']} has an interior raster sample {sample['observedSRGB']} versus BRIEF.md's disabled fill {sample['expectedVisualFill']}. This is a confirmed visual palette contradiction. It is a PNG appearance finding, not a computed SwiftUI font/color measurement. Plain button styling combined with disabled state may be applying opacity; that cause is an inference.",'design_detail_source':ev(design/'BRIEF.md'),'raster_sample':sample})
   else:
    visual.update({'status':'passed','reason':'Reviewed every original state-capture viewport shown in the indexed contact sheet. Native hierarchy, both palette roles, check marks and selected outlines, disabled fills, full-width action, details state, complete summary and all four ordered note paragraphs are readable without clipping or overlap. The original Roboto/system metrics differ from the export font; no pixel identity or exact style claim is made here.'})
   findings.append(visual)
   coverage.append({'case':case,'platform':platform,'state':state,'capture':sc,'reviewed_original_snapshot_indices':sc['snapshot_indices'],'contact_sheet':contact['contactSheet'],'original_pngs':contact['original_sources'],'native_report_state':report['states'][state],'visual_scope':'All retained viewport images for this state were reviewed; native complete/interval coverage is retained from the original capture. Planned target-state visual scope is not expanded into an unrecorded device-level claim.','reviewed_aspects':['hierarchy','system typography appearance','palette','wrapping and readable choice names','selected check mark and border','disabled appearance','summary visibility','disclosure/detail consistency','confirmation presentation','notes order and bottom reach'],'caveats':['Native iOS computed style remains U.'] if platform=='ios' else ['Semantic invocation and continuous Paparazzi frames do not establish physical touch or Activity lifecycle.']})
  if platform=='ios':
   contact=contacts[(case,platform,'replaced')]
   findings.append({'case':case,'platform':platform,'state':'replaced','requirement_id':'replacement-seed-selection','aspect':'selected stove appearance','expected':['stove'],'unit':'caller selectedIDs string array','status':'failed','origin':'original_manual_visual','duplicate_of_original_typed_failure':True,'duplicate_machine_failure_ids':['replaced/derived-summary','replaced/option-enabled','replaced/eligibility-status','replaced/primary-enabled'],'root_cause_cluster':'ios-replacement-seed-reset','reason':'The replacement seed in the original public/captured fixture is stove. The real displayed stove has neither selected border/check mark nor selected native state, and summary is zero items. This is the same underlying contradiction already represented by the four original typed failures, so it is not counted as an independent manual detection.','evidence':[ev(observation),ev(corpus/platform/case/'fixtures.json')]+[{'path':s['path'],'sha256':s['sha256']} for s in contact['original_sources']]})
# A qualitative observation remains U because native readable wrapping is allowed.
contact=contacts[('P2','android','chosen')]
findings.append({'case':'P2','platform':'android','state':'chosen','requirement_id':'visual-composition','aspect':'choice-name word breaking','expected':'Wrap every label and note; labels remain readable.','unit':'string','status':'unassessed','origin':'original_manual_visual','reason':'The narrow selected card wraps Two-person inside the word. The complete name remains visible and the design permits native wrapping; a preferred word-break treatment is qualitative and is not a confirmed design violation.','evidence':[{'path':s['path'],'sha256':s['sha256']} for s in contact['original_sources']]+[ev(corpus/'android/P2/observation.json')]})
(out/'original-typed-ledger.json').write_text(json.dumps(ledger,indent=2))
(out/'original-machine-findings.json').write_text(json.dumps(machine,indent=2))
(out/'source-evidence-manifest.json').write_text(json.dumps(source_records,indent=2))
# Preserve the reviewer inspection failure exactly; it did not alter source or evidence.
error="Traceback (most recent call last):\n  File \"<stdin>\", line 12, in <module>\nP1 ios replacement seed ['stove'] p1-replacement\nSTATE FACTS\n  File \"<stdin>\", line 12, in <listcomp>\nAttributeError: 'int' object has no attribute 'get'\n"
(out/'inspection-error.log').write_text(error)
commands=[{'kind':'instruction read and clock','command':'clock curr_time; cat prompts/unit-df4422-review.txt','exitCode':0,'timeUtc':'2026-10-20T15:15:37+00:00'},
 {'kind':'original record acquisition','command':'Python json reads of own original observations, original typed reports/command records/check.log; no check rerun. find own assigned corpus and d0 sources only.','exitCode':0},
 {'kind':'contact sheets','command':['python3','agent-output/review/contact_sheets.py'],'exitCode':0},
 {'kind':'visual review','command':'view_image on all 24 original-state contact sheets, plus original android/P2/006-state_loaded_0.png at original detail.','exitCode':0},
 {'kind':'raster evidence','command':'Pillow opens original PNGs and samples native-identified disabled-control interior coordinates; palette-samples.json retains exact coordinates and colors.','exitCode':0},
 {'kind':'failed reviewer inspection','command':"v=a['actual']; v=[x.get('value') for x in v] if isinstance(v,list) else v",'exitCode':1,'errorLog':'agent-output/review/inspection-error.log','reason':'Some geometry actual arrays contain scalars, so the summary-only inspector failed. Original evidence and source were not changed.'},
 {'kind':'corrected reviewer inspection','command':"v=[x.get('value') if isinstance(x,dict) else x for x in v] if isinstance(v,list) else v",'exitCode':0},
 {'kind':'report write and seal','command':['python3','agent-output/review/write_review.py'],'exitCode':0}]
(out/'commands.json').write_text(json.dumps(commands,indent=2))
original_seal=json.loads((w/'agent-output/plans-seal.json').read_text());unchanged=[]
for p,want in {**original_seal['files'],**original_seal['source_files']}.items():
 actual=hashfile(w/p);unchanged.append({'path':p,'sha256':actual,'originalSHA256':want,'unchanged':actual==want})
assert all(x['unchanged'] for x in unchanged)
(out/'immutability-after.json').write_text(json.dumps(unchanged,indent=2))
start=json.loads((out/'phase-start.json').read_text());finished=time.time()
review={'version':1,'phase':'original_read_only_self_review','startedAtUnix':start['startedAtUnix'],'startedAtUtc':start['startedAtUtc'],'finishedAtUnix':finished,'finishedAtUtc':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat(),'elapsedSeconds':finished-start['startedAtUnix'],'budgetSeconds':720,'design_lock_sha256':'24a80e813cb3a2638499d9294fcacc0439891c680211ce85981a7a9b590c6b2c','coverage':coverage,'original_typed_counts':dict(counts),'machine_failure_ids':[{'case':x['case'],'platform':x['platform'],'id':x['original']['id'],'classification':'product-related','retained':True} for x in machine],'root_cause_clusters':[{'id':'ios-replacement-seed-reset','classification':'product-related','scope':'P1/P2 iOS replacement; eight original typed rows retained, exact reset cause not proven'},{'id':'ios-disabled-palette-opacity','classification':'product-related visual appearance','scope':'All twelve reviewed iOS states; each has its own original screenshot and observed disabled target; opacity cause is an inference.'}],'findings':findings,'limits':['Read-only review: no sources, original plans/actions, design or bridges changed; no SDK/render/observer commands executed.','Original typed report counts and every failure/U remain preserved in original-check-records and original-typed-ledger.json. No expected values or precision were changed.','Generic native iOS font size/weight/color/ellipsis remain unassessed even though pixels are available.','P2 optional action was blocked_disabled on both platforms; no successful dispatch means its callback behavior remains U.','Full original captured content and notes were inspected, but no hidden input, device touch behavior, navigation or Activity lifecycle claim is made.','Android long-name word breaking is a qualitative U, not a design failure; summary is fully visible without ellipsis in original PNG and native facts.','Host-owned outer canvas and observer sentinel typography are outside this component assessment.','Stop pending all-six review barrier; no repair authorized.'],'source_immutability':'all original sealed sources, plans, actions and initial scripts byte-identical','commands':'agent-output/review/commands.json','original_evidence_manifest':'agent-output/review/source-evidence-manifest.json','original_typed_ledger':'agent-output/review/original-typed-ledger.json','original_machine_findings':'agent-output/review/original-machine-findings.json'}
(out/'review.json').write_text(json.dumps(review,indent=2))
files={str(p.relative_to(w)):hashfile(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='review-seal.json'}
(out/'review-seal.json').write_text(json.dumps({'version':1,'sealedAtUnix':time.time(),'files':files,'original_source_plan_immutability':True},indent=2))
print(json.dumps({'elapsedSeconds':review['elapsedSeconds'],'originalTypedCounts':dict(counts),'originalMachineFailures':len(machine),'findings':dict(collections.Counter(x['status'] for x in findings)),'sealedReviewFiles':len(files)},indent=2))
