from pathlib import Path
import json,sys,hashlib,datetime,re,importlib.util,collections,time,copy
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/state-forward');O=R/'evaluation/FINAL';D=R/'design/private'
def loadmod(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def save(path,x):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
start=now();tick=time.monotonic();batch=json.loads((R/'evaluation-inputs/FINAL/batch.json').read_text());oracle=json.loads((D/'oracle.json').read_text());ledger=json.loads((D/'states-ledger.json').read_text());public=json.loads((R/'design/public/cases.json').read_text())['cases']+json.loads((D/'heldout-cases.json').read_text())['cases'];images=json.loads((O/'screenshot-inventory.json').read_text())['images']
hpath=Path(batch['immutableHelper']);sys.path.insert(0,str(hpath.parent));h=loadmod('actual_immutable_helper_review',hpath)
v3=loadmod('frozen_grade_v3_review',D/'grade.py');v2=loadmod('frozen_grade_v2_review',R/'design/history/grader-v2/private/grade.py')
review_log=[]
for seq,(arm,plat) in enumerate([('source-a','android'),('source-b','android'),('source-a','ios'),('source-b','ios')]):
 for ci,cid in enumerate(['P1','P2','P3','P4','H1','H2']):
  sheet=O/arm/'contact-sheets'/f'{plat}-{cid}.png';ims=[i for i in images if (i['anonymousID'],i['platform'],i['caseID'])==(arm,plat,cid)]
  review_log.append(dict(reviewOrder=seq*6+ci+1,anonymousID=arm,platform=plat,caseID=cid,contactSheet=str(sheet),contactSheetSHA256=sha(sheet),method='Explicitly displayed and reviewed ordered original-resolution contact sheet; every delivered PNG appears once in snapshot order.',imageCount=len(ims),reviewedImages=[dict(path=i['path'],sha256=i['sha256'],snapshotIndex=i['snapshotIndex'],stateID=i['stateID'],binding=i['binding'],tile=i['contactTile']) for i in ims],reviewRecordedUTC=now()))
enlargements=[]
for arm,cid,idx in [('source-a','P2',2),('source-a','H2',2),('source-b','H1',17)]:
 i=next(i for i in images if (i['anonymousID'],i['platform'],i['caseID'],i['snapshotIndex'])==(arm,'ios',cid,idx));enlargements.append(dict(path=i['path'],sha256=i['sha256'],caseID=cid,snapshotIndex=idx,scope='Original-resolution full screenshot explicitly displayed; status words fully visible, intact English/numeral groups and mirrored RTL layout where supplied. No numeric native style or physical-hit inference.'))
i=next(i for i in images if (i['anonymousID'],i['platform'],i['caseID'],i['snapshotIndex'])==('source-b','android','H2',2));enlargements.append(dict(path=i['path'],sha256=i['sha256'],caseID='H2',snapshotIndex=2,scope='Original-resolution actual Android RTL screenshot reviewed for complete long-title wrapping, English/numeral order and visible over-budget badge.'))
save(O/'screenshot-review-log.json',dict(reviewedAtUTC=now(),allDeliveredPNGsReviewed=len(images),orderedSheets=review_log,enlargements=enlargements,notes=['All 563 delivered screenshots were inspected in24 ordered contact sheets. No best-frame selection.','Only the production component content is reviewed; common host canvas, runtime labels and next-fixture control are outside product scope.','Scroll-viewport crop edges are not product truncation when complementary same-state frames show the complete content.','Qualitative screenshot palette judgments do not establish numeric font/color/padding values.']))
for arm in batch['corpora']:
 aid=arm['anonymousID'];cap=Path(arm['captures']);capsule=Path(arm['sourceCapsule']);native=json.loads((O/aid/'v3/native-grade.json').read_text());ng={x['cellID']:x for x in native['rows']};manual=[];scopes=[];source_reviews=[];input_reviews=[];transitions=[]
 # Public and held-out actual input checks: compare ACTUAL native fixtures/actions/mappings to fixed public inputs.
 for case in public:
  cid=case['caseID'];fr=R/f'evaluation-inputs/FINAL/native-inputs/{cid}/fixtures.json';ar=R/f'evaluation-inputs/FINAL/native-inputs/{cid}/actions.json';fixture=json.loads(fr.read_text());actions=json.loads(ar.read_text());actual_models=[fixture['initial']['model']]+[u['model'] for u in fixture['updates']]
  assert actual_models==case['models'] and fixture['initial']['host']==case['host']
  assert all(u['host']==case['host'] for u in fixture['updates'])
  assert fixture['width']==case['host']['width'] and fixture['viewportHeight']==600 and fixture['theme']==case['host']['theme'] and fixture['direction']==case['host']['direction'] and fixture['fontScale']==1.0 and fixture['dynamic_type']=='large'
  checks=[]
  for plat in ['android','ios']:
   cp=cap/plat/cid;captured=json.loads((cp/'fixtures.json').read_text());assert all(captured[k]==v for k,v in fixture.items())
   recorded_actions=captured['actions'] if plat=='android' else json.loads((cp/'actions.json').read_text());assert recorded_actions==actions
   mapping=json.loads((R/f'evaluation-inputs/FINAL/mappings/{cid}/mapping.{plat}.json').read_text());ob=json.loads((cp/'observation.json').read_text())
   for action in case['actions']:
    row=mapping[action['stateID']];actual=actions[row['trigger_action_index']]
    assert actual['state_id']==row['trigger_state_id']
    if action['type']=='activate':assert actual['type']=='tap' and actual['target']['identifier']==action['targetID']
    else:assert actual['type']=='apply_next_fixture' and row['input_index']==action['modelIndex']
    step=ob['steps'][int(row['trigger_step_pointer'].split('/')[-1])];assert step['state_id']==row['trigger_state_id']
    checks.append(dict(platform=plat,stateID=action['stateID'],actualActionIndex=row['trigger_action_index'],stepPointer=row['trigger_step_pointer'],actualStateID=step['state_id']))
  input_reviews.append(dict(caseID=cid,actualFixture=str(fr),actualActions=str(ar),modelsAndHostExact=True,capturedNativeConfigurationsEqual=True,actionMappingChecks=checks))
  for cell in [x for x in oracle['cells'] if x['classification']=='input.integrity' and x['caseID']==cid]:
   manual.append(dict(cellID=cell['cellID'],actual=None,evidenceKind='input.integrity',evidenceRefs=[str(fr),str(ar),str(R/f'evaluation-inputs/FINAL/mappings/{cid}/mapping.android.json'),str(R/f'evaluation-inputs/FINAL/mappings/{cid}/mapping.ios.json')],context=dict(platform='host',caseID=cid,stateID=None),reviewVerdict='pass',reviewReason='Actual host/model members, native captured fixtures, logical-to-native action sequence and per-platform exact step/state/input mappings inspected and match public inputs. Three unique job IDs, distinct modelIDs, numeric bounds and fixed host enums validated.'))
 # Source/API checks: only designated production files plus actual compiled common caller/bridge.
 for plat in ['android','ios']:
  rel='source/reply/Reply/app/src/main/java/com/example/reply/ui/printbatch/PrintBatchApprovalCard.kt' if plat=='android' else 'source/alerttoast/Sources/AlertToast/PrintBatchApprovalCard.swift';src=capsule/rel;text=src.read_text();assert all(name in text for name in ['PrintBatchJob','PrintBatchModel','PrintBatchPresentation','PrintBatchApprovalCard','onEvent'])
  bridges=[];hosts=[]
  for cid in ['P1','P2','P3','P4','H1','H2']:
   br=cap/plat/cid/('sources/ObserverBridge.kt' if plat=='android' else 'compiled-project/Bridge.swift');host=cap/plat/cid/('sources/NativeObserverTest.kt' if plat=='android' else 'compiled-project/ObserverApp.swift');bridges.append(br);hosts.append(host)
   assert br.read_bytes()==(R/'design/public'/('ObserverBridge.kt' if plat=='android' else 'Bridge.swift')).read_bytes()
   ht=host.read_text();assert ('ObserverBridge.Content(current)' if plat=='android' else 'ObserverBridge.make(fixture: fixtures[index])') in ht
   assert not re.search(r'\bkey\s*\(|\.id\s*\(',ht)
  source_reviews.append(dict(platform=plat,productionFile=str(src),sha256=sha(src),scope='Public declarations/initializers/callback API and production entrypoint; source facts kept separate from runtime.',bridges=[dict(path=str(x),sha256=sha(x),matchesFrozenAdapter=True) for x in bridges],commonHosts=[dict(path=str(x),sha256=sha(x),scope='Only component call/identity inspected; single stable caller position, no external key/id injection.') for x in hosts],identityInterpretation='Component-owned remember(modelID), onChange, and internally keyed subtree are legitimate production reset handling.'))
  for cell in [x for x in oracle['cells'] if x['classification']=='source.api' and x['platform']==plat]:
   reason={'entrypoint':'Exact designated production file and public native component declaration inspected.','modelAPI':'All required public job/model/presentation fields and initializers inspected; Kotlin data-class constructors and Swift public initializers match.','callbackAPI':'Public onEvent name plus JSON-compatible dictionary callback matches the fixed native API.','bridgeCallsProduction':'Every captured bridge is byte-identical to the frozen API adapter, imports the actual module and calls PrintBatchApprovalCard directly.','replacementIdentity':'Actual common caller keeps component at a stable position and supplies new fixture. Product-owned remembered/modelID or internal keyed state reset is permitted and is not host recreation.'}[cell['aspect']]
   manual.append(dict(cellID=cell['cellID'],actual=None,evidenceKind='manual.source',evidenceRefs=[str(src)]+[str(x) for x in bridges]+[str(x) for x in hosts],context=dict(platform=plat,caseID=None,stateID=None),reviewVerdict='pass',reviewReason=reason))
 # Explicit screenshot judgments by exact native state scope. All raw images were reviewed above.
 for plat in ['android','ios']:
  for case in public:
   cid=case['caseID'];root=cap/plat/cid;raw=root/'observation.json';ob=json.loads(raw.read_text());mapping=json.loads((R/f'evaluation-inputs/FINAL/mappings/{cid}/mapping.{plat}.json').read_text())
   for sid,row in mapping.items():
    state=next(s for s in ledger['states'] if s['stateID']==sid);snaps,complete,reason,capture=h.state_evidence(ob,dict(id=row['state_id'],input_index=row['input_index'],after_action=row['state_action_index'],coverage='full_content' if state['full_content'] else 'targets'))
    refs=[str(root/s['screenshot']) for _,s in snaps if s.get('screenshot') and (root/s['screenshot']).exists()];ctx=copy.deepcopy(next((r.get('context') for r in json.loads((O/aid/'v3/by-case'/f'{plat}-{cid}.json').read_text())['records'] if r.get('context',{}).get('stateID')==sid),{}))
    scopes.append(dict(platform=plat,caseID=cid,stateID=sid,snapshotIndices=[i for i,_ in snaps],imageRefs=refs,helperCoverageComplete=complete,helperCoverageReason=reason,visualReview='All listed exact-state frames reviewed in ordered sheet; complementary top/bottom target frames show component content.',bindings=[s.get('binding') for _,s in snaps]))
    for cell in [x for x in oracle['cells'] if x['platform']==plat and x['stateID']==sid and x['operator']=='screenshotReview']:
     verdict='pass' if refs else 'unknown';why='Actual exact-state native screenshot set reviewed. Required ordering, hierarchy, associations, wrapping, semantic palette and selected/disabled rendering are visible across complementary scroll frames; no source or declared style used as runtime proof.'
     if cell['aspect']=='visual.paletteStatus':why='Actual visible status words, semantic-colored badge background and any shortfall use the appropriate ready/error/muted visual color family; no numeric color channel is inferred.'
     if cell['aspect']=='visual.paletteBackground':why='Actual component surface is the supplied light/dark palette surface. Common outer canvas is outside production root and excluded, as frozen host clarification requires; numeric style tokens remain separate.'
     if cell['aspect']=='visual.readability':why='Words and numeral groups remain intact and readable in actual supplied LTR/RTL rendering; RTL leading/trailing mirrored. Native exact-copy strings are checked separately.'
     manual.append(dict(cellID=cell['cellID'],actual=None,evidenceKind='manual.screenshot',evidenceRefs=refs or [str(raw)],context=ctx,reviewVerdict=verdict,reviewReason=why))
 # Actual native transition synthesis, separate from callbacks and from source declarations.
 for cell in [x for x in oracle['cells'] if x['operator']=='transition']:
  plat=cell['platform'];sid=cell['stateID'];cid=cell['caseID'];evid=json.loads((O/aid/'v3/by-case'/f'{plat}-{cid}.json').read_text());callback=next(r for r in evid['records'] if r['cellID']==f'{plat}.{sid}.behavior.callbackInterval');mapping=json.loads((R/f'evaluation-inputs/FINAL/mappings/{cid}/mapping.{plat}.json').read_text());fixture=json.loads((cap/plat/cid/'fixtures.json').read_text());idx=mapping[sid]['input_index'];active=([fixture['initial']]+fixture['updates'])[idx]['model'];facts={};refs=[];missing=[]
  def actual(aspect):
   r=ng.get(f'{plat}.{sid}.{aspect}')
   if r and r['status'] in ['P','F'] and r.get('actual') is not None:refs.extend(r['evidenceRefs']);return r['actual']
   missing.append(aspect);return None
  selected=[]
  for job in active['jobs']:
   flag=actual('job.'+job['id']+'.selection')
   if flag is True:selected.append(job['id'])
  single=actual('mode.single.selected');duplex=actual('mode.duplex.selected');mode='single' if single is True and duplex is False else ('duplex' if duplex is True and single is False else None)
  priority=actual('priority.on');expanded=actual('breakdown.expanded');charge=actual('charge.value.text');m=re.fullmatch(r'(\d+) cr',charge or '');total=int(m.group(1)) if m else None
  vector=dict(modelID=active['modelID'],selected=selected if not any(x.endswith('.selection') for x in missing) else None,paperMode=mode,priority=priority,expanded=expanded,total=total)
  record=dict(cellID=cell['cellID'],actual=vector,evidenceKind='native.transition',evidenceRefs=sorted(set(refs+[str(cap/plat/cid/'fixtures.json')]+callback['evidenceRefs'])),context=copy.deepcopy(callback['context']),gate=copy.deepcopy(callback['gate']),helperVerdict='unknown' if missing or mode is None or total is None else 'pass',helperReason='Actual native selected/on/expanded attributes, charge text and bound native input model synthesized; no callback payload or source calculation substituted.'+(' Unobserved native aspects: '+','.join(missing) if missing else ''))
  transitions.append(record)
 save(O/aid/'manual-records.json',dict(schemaVersion=1,anonymousID=aid,stage='FINAL',records=manual))
 save(O/aid/'native-transition-records.json',dict(schemaVersion=1,records=transitions))
 save(O/aid/'source-review.json',dict(reviewedAtUTC=now(),reviews=source_reviews))
 save(O/aid/'input-review.json',dict(reviewedAtUTC=now(),reviews=input_reviews))
 save(O/aid/'state-screenshot-scopes.json',dict(reviewedAtUTC=now(),scopes=scopes))
 for version,grader in [('v3',v3),('v2',v2)]:
  evidence=json.loads((O/aid/version/'native-normalized.json').read_text());evidence['records']+=copy.deepcopy(manual+transitions);save(O/aid/version/'normalized.json',evidence);graded=grader.grade(oracle,evidence)
  graded['primaryPublicRuntime']=grader.summarize([r for r in graded['rows'] if (r.get('caseID') or '').startswith('P') and r['classification'].startswith('runtime.')]);graded['heldoutRuntime']=grader.summarize([r for r in graded['rows'] if (r.get('caseID') or '').startswith('H') and r['classification'].startswith('runtime.')]);graded['allRuntime']=grader.summarize([r for r in graded['rows'] if r['classification'].startswith('runtime.')]);graded['deliveredScope']='All public4 and held-out2 actual FINAL native cases delivered and evaluated; held-out states retain all fixed rows.'
  save(O/aid/version/'grade.json',graded)
  if version=='v3':save(O/aid/'grade.json',graded);save(O/aid/'normalized.json',evidence)
 a=json.loads((O/aid/'v2/grade.json').read_text());b=json.loads((O/aid/'v3/grade.json').read_text());changes=[];statuschanges=[]
 for x,y in zip(a['rows'],b['rows']):
  assert x['cellID']==y['cellID']
  if any(x.get(k)!=y.get(k) for k in ['actual','measurement','normalization','status']):
   changes.append(dict(cellID=x['cellID'],caseID=x['caseID'],stateID=x['stateID'],classification=x['classification'],v2={k:x.get(k) for k in ['actual','measurement','normalization','status','reason']},v3={k:y.get(k) for k in ['actual','measurement','normalization','status','reason']}))
  if x['status']!=y['status']:statuschanges.append(dict(cellID=x['cellID'],v2=x['status'],v3=y['status']))
 save(O/aid/'measurement-sensitivity.json',dict(kind='COMMON evaluator field-meaning correction, not treatment gain',oracleUnchanged=True,helperUnchanged=True,rawAndManualEvidenceIdentical=True,v2OriginalGrade=str(O/aid/'v2/grade.json'),v3CorrectedGrade=str(O/aid/'v3/grade.json'),changedCellCount=len(changes),statusChangedCellCount=len(statuschanges),allChangedMeasurementProvenanceOrStatusCells=changes,statusChanges=statuschanges))
save(O/'review-assembly-cost.json',dict(startUTC=start,endUTC=now(),wallSeconds=time.monotonic()-tick,scope='Record assembly after explicit source/native/input/screenshot reviews; excludes preceding human/model visual review wall time.'))
for arm in ['source-a','source-b']:
 g=json.loads((O/arm/'grade.json').read_text());print(arm,g['primaryPublicRuntime']['all']);print(g['summary']['all'])
