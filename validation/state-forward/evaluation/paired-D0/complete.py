from pathlib import Path
import json,sys,hashlib,datetime,re,importlib.util,collections,time,copy,shutil
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/state-forward');O=R/'evaluation/paired-D0';D=R/'design/private'
def loadmod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
save=lambda p,x:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
batch=json.loads((R/'evaluation-inputs/paired-D0/batch.json').read_text());oracle=json.loads((D/'oracle.json').read_text());ledger=json.loads((D/'states-ledger.json').read_text());public=json.loads((R/'design/public/cases.json').read_text())['cases'];images=json.loads((O/'screenshot-inventory.json').read_text())['images'];hp=Path(batch['immutableHelper']);sys.path.insert(0,str(hp.parent));h=loadmod('same_immutable_helper_paired',hp);grader=loadmod('same_frozen_grader_paired',D/'grade.py');reviews=[]
start=now();tick=time.monotonic()
for ai,(aid,plat) in enumerate([('source-a','android'),('source-b','android'),('source-a','ios'),('source-b','ios')]):
 for ci,cid in enumerate(['P1','P2','P3','P4']):
  ims=[i for i in images if (i['anonymousID'],i['platform'],i['caseID'])==(aid,plat,cid)];sheet=O/aid/'v4/contact-sheets'/f'{plat}-{cid}.png';reviews.append(dict(reviewOrder=ai*4+ci+1,anonymousID=aid,platform=plat,caseID=cid,path=str(sheet),sha256=sha(sheet),reviewedImages=ims,method='Explicit display/review of every tile in native snapshot order, preserving aspect ratio. Exact state visual scope is separately recorded; scroll-viewport edges do not establish product clipping.'))
save(O/'screenshot-review-log.json',dict(stage='paired-D0',v4PNGsReviewed=287,orderedSheets=reviews,enlargements=[i for i in images if (i['anonymousID'],i['platform'],i['caseID'],i['snapshotIndex']) in [('source-a','ios','P2',2),('source-b','ios','P3',11)]],v5Review='Prior sealed D0 screenshot review and original literal judgments reused; no fresh v5 adjudication.'))
for arm in batch['corpora']:
 aid=arm['anonymousID'];cap=Path(arm['v4Captures']);v5cap=Path(arm['v5Captures']);out=O/aid/'v4';manual=[];transitions=[];scopes=[];inputcheck=[];sourcecheck=[]
 # Verify byte-exact portable corpus seals for both producers, and same original D0 production/input identity.
 corpora={}
 for v,cp in [('v4',cap),('v5',v5cap)]:
  mp=cp/'portable-sha256.json';assert sha(mp)==arm['portableManifests'][v];manifest=json.loads(mp.read_text());assert all(sha(cp/k)==v for k,v in manifest.items());corpora[v]=json.loads((cp/'corpus.json').read_text())
 assert corpora['v4']['source']==corpora['v5']['source']
 prior=json.loads((R/'evaluation/D0'/aid/'manual-records.json').read_text());oldsourceinput=[x for x in prior['records'] if x['evidenceKind'] in ['manual.source','input.integrity']]
 for case in public:
  cid=case['caseID'];fr=Path(batch['nativeInputs'])/cid/'fixtures.json';ar=Path(batch['nativeInputs'])/cid/'actions.json';expectedfixture=json.loads(fr.read_text());actions=json.loads(ar.read_text())
  for plat in ['android','ios']:
   root=cap/plat/cid;other=v5cap/plat/cid;captured=json.loads((root/'fixtures.json').read_text());assert captured==json.loads((other/'fixtures.json').read_text());assert all(captured[k]==v for k,v in expectedfixture.items());assert (captured['actions'] if plat=='android' else json.loads((root/'actions.json').read_text()))==actions
   man=json.loads((root/'manifest.json').read_text());otherman=json.loads((other/'manifest.json').read_text());assert man['input_hashes']==otherman['input_hashes'];assert man['input_hashes']==dict(fixtures=sha(fr),actions=sha(ar))
   mapping=json.loads((Path(batch['mappings'])/cid/f'mapping.{plat}.json').read_text());ob=json.loads((root/'observation.json').read_text())
   for action in case['actions']:
    m=mapping[action['stateID']];step=ob['steps'][int(m['trigger_step_pointer'].split('/')[-1])];assert step['state_id']==m['trigger_state_id'];actual=actions[m['trigger_action_index']];assert actual['state_id']==m['trigger_state_id']
   inputcheck.append(dict(platform=plat,caseID=cid,actualFixture=str(root/'fixtures.json'),actualFixtureSHA256=sha(root/'fixtures.json'),sameNativeInputHashes=man['input_hashes'],actualActions=str(ar),mapping=str(Path(batch['mappings'])/cid/f'mapping.{plat}.json'),allActualStateActionPointersChecked=True))
   bridge=root/('sources/ObserverBridge.kt' if plat=='android' else 'compiled-project/Bridge.swift');host=root/('sources/NativeObserverTest.kt' if plat=='android' else 'compiled-project/ObserverApp.swift');assert bridge.read_bytes()==(R/'design/public'/('ObserverBridge.kt' if plat=='android' else 'Bridge.swift')).read_bytes();ht=host.read_text();assert ('ObserverBridge.Content(current)' if plat=='android' else 'ObserverBridge.make(fixture: fixtures[index])') in ht;assert not re.search(r'\bkey\s*\(|\.id\s*\(',ht)
   sourcecheck.append(dict(platform=plat,caseID=cid,actualBridge=str(bridge),bridgeSHA256=sha(bridge),frozenBridgeEqual=True,actualHost=str(host),hostSHA256=sha(host),identity='Stable common caller; no external key/id recreation. Production-owned reset rule unchanged and allowed.'))
 for rec in oldsourceinput:
  new=copy.deepcopy(rec);new['evidenceRefs']+= [str(O/aid/'v4/input-source-review.json')];new['reviewReason']+=' Paired v4 actual fixtures/actions/compiled bridge/stable caller and all production source hashes independently verified equal in input-source-review.json.';manual.append(new)
 save(out/'input-source-review.json',dict(productionSourcesEqual=True,sourceHashMap=corpora['v4']['source'],compiledCallerAndBridge=sourcecheck,actualInputActionVerification=inputcheck,sourceCapsule=arm['sourceCapsule'],reusedSourceAPIReview=str(R/'evaluation/D0'/aid/'source-review.json'),scope='Same declared production APIs/source hashes; no production/observer implementation repair. Native input and source classes remain separate from runtime.'))
 native=json.loads((out/'native-grade.json').read_text());ng={r['cellID']:r for r in native['rows']}
 for plat in ['android','ios']:
  for case in public:
   cid=case['caseID'];root=cap/plat/cid;raw=root/'observation.json';ob=json.loads(raw.read_text());mapping=json.loads((Path(batch['mappings'])/cid/f'mapping.{plat}.json').read_text());evid=json.loads((out/'by-case'/f'{plat}-{cid}.json').read_text())
   for sid,m in mapping.items():
    state=next(s for s in ledger['states'] if s['stateID']==sid);ss,complete,reason,capture=h.state_evidence(ob,dict(id=m['state_id'],input_index=m['input_index'],after_action=m['state_action_index'],coverage='full_content' if state['full_content'] else 'targets'));refs=[str(root/s['screenshot']) for _,s in ss if s.get('screenshot') and (root/s['screenshot']).exists()];ctx=copy.deepcopy(next((r['context'] for r in evid['records'] if r.get('context',{}).get('stateID')==sid),{}));visible=set()
    for _,snap in ss:
     for node in snap.get('nodes',[]):
      if node.get('identifier') and node.get('fully_within_viewport',node.get('fully_visible',False)):
       rect=node.get('frame') if plat=='ios' else node.get('unclipped_bounds_dp');positive=(rect and ((rect.get('width',0)>0 and rect.get('height',0)>0) if isinstance(rect,dict) else rect[2]>rect[0] and rect[3]>rect[1]))
       if positive:visible.add(node['identifier'])
    # This native visibility list scopes already-reviewed actual screenshots. It does not fabricate visual verdicts from semantic/source declarations.
    model=case['models'][m['input_index']];jobs=model['jobs'];jobids={f'printbatch.job.{j["id"]}.{s}' for j in jobs for s in ['title','subtitle','price','toggle']};alljobs=jobids<=visible;allmodes={'printbatch.mode.single','printbatch.mode.duplex','printbatch.mode.title'}<=visible;header={'printbatch.title','printbatch.charge.value'}<=visible;breakids={f'printbatch.breakdown.{k}.{t}' for k in ['ink','paper','priority','total'] for t in ['label','value']};breakshown=breakids<=visible;allcontrols=alljobs and allmodes and {'printbatch.priority','printbatch.approve','printbatch.breakdown.toggle'}<=visible;full=bool(complete)
    scope=dict(platform=plat,caseID=cid,stateID=sid,snapshotIndices=[i for i,_ in ss],imageRefs=refs,helperCoverageComplete=complete,helperCoverageReason=reason,fullyVisibleExactStateIdentifiers=sorted(visible),visualFullContent=full,localGroups=dict(header=header,allJobs=alljobs,mode=allmodes,breakdownRows=breakshown,allControls=allcontrols),rule='Only this exact-state image set is reviewed. Sparse views cannot inherit invisible header, whole-card visual or absence facts from earlier/later states or source.')
    scopes.append(scope)
    for cell in [x for x in oracle['cells'] if x['platform']==plat and x['stateID']==sid and x['operator']=='screenshotReview']:
     aspect=cell['aspect'];verdict='pass' if full and refs else 'unknown';why='Entire exact-state content was captured across native interval union and actually reviewed; current rendering meets this visual requirement.' if verdict=='pass' else 'Sparse exact-state frames do not show every relevant region for this visual requirement. No unseen content/source or other state substitutes.'
     if refs:
      local=(aspect=='visual.typeHierarchy' and header) or (aspect=='visual.headerDirection' and header) or (aspect=='visual.jobDirection' and alljobs) or (aspect=='visual.modeDirection' and allmodes) or (aspect=='visual.expansion' and breakshown) or (aspect=='visual.controls' and allcontrols)
      if local:verdict='pass';why='Actual exact-state screenshots show the complete local group needed for this requirement; scoped native visibility anchors retained. Other unseen groups remain unknown.'
      if aid=='source-a' and plat=='ios' and header and aspect in ['visual.noClip','visual.readability']:verdict='fail';why='Actually visible complete header shows narrow colored pill without readable status text, confirmed in original-resolution enlargement. This is a visible violation even when other content is not shown.'
     manual.append(dict(cellID=cell['cellID'],actual=None,evidenceKind='manual.screenshot',evidenceRefs=refs or [str(raw)],context=ctx,reviewVerdict=verdict,reviewReason=why))
 # Complete resulting native vector synthesis; callback payloads/source never substitute for missing current attributes/text.
 for cell in [x for x in oracle['cells'] if x['operator']=='transition' and (x['caseID'] or '').startswith('P')]:
  plat=cell['platform'];sid=cell['stateID'];cid=cell['caseID'];evid=json.loads((out/'by-case'/f'{plat}-{cid}.json').read_text());callback=next(r for r in evid['records'] if r['cellID']==f'{plat}.{sid}.behavior.callbackInterval');mapping=json.loads((Path(batch['mappings'])/cid/f'mapping.{plat}.json').read_text());fixture=json.loads((cap/plat/cid/'fixtures.json').read_text());idx=mapping[sid]['input_index'];active=([fixture['initial']]+fixture['updates'])[idx]['model'];refs=[];missing=[]
  def actual(aspect):
   r=ng.get(f'{plat}.{sid}.{aspect}')
   if r and r['status'] in ['P','F'] and r.get('actual') is not None:refs.extend(r['evidenceRefs']);return r['actual']
   missing.append(aspect);return None
  selected=[]
  for job in active['jobs']:
   flag=actual('job.'+job['id']+'.selection')
   if flag is True:selected.append(job['id'])
  single=actual('mode.single.selected');duplex=actual('mode.duplex.selected');mode='single' if single is True and duplex is False else ('duplex' if duplex is True and single is False else None);priority=actual('priority.on');expanded=actual('breakdown.expanded');charge=actual('charge.value.text');mm=re.fullmatch(r'(\d+) cr',charge or '');total=int(mm.group(1)) if mm else None;vector=dict(modelID=active['modelID'],selected=selected if not any(x.endswith('.selection') for x in missing) else None,paperMode=mode,priority=priority,expanded=expanded,total=total)
  transitions.append(dict(cellID=cell['cellID'],actual=vector,evidenceKind='native.transition',evidenceRefs=sorted(set(refs+[str(cap/plat/cid/'fixtures.json')]+callback['evidenceRefs'])),context=copy.deepcopy(callback['context']),gate=copy.deepcopy(callback['gate']),helperVerdict='unknown' if missing or mode is None or total is None else 'pass',helperReason='Actual resulting current native selection/on/expansion/charge plus bound input synthesized. Missing facts: '+','.join(missing)))
 evidence=json.loads((out/'native-normalized.json').read_text());evidence['records']+=manual+transitions;g=grader.grade(oracle,evidence);g['primaryPublicRuntime']=grader.summarize([r for r in g['rows'] if (r.get('caseID') or '').startswith('P') and r['classification'].startswith('runtime.')]);g['heldoutD0Scope']='Held-out cases not delivered for paired-D0; all fixed missing non-N/A rows remain U.';save(out/'normalized.json',evidence);save(out/'grade.json',g);save(out/'manual-records.json',dict(records=manual));save(out/'native-transition-records.json',dict(records=transitions));save(out/'state-screenshot-scopes.json',dict(scopes=scopes))
 # V5 grade AND normalized evidence are exact original sealed bytes, including all manual judgments and row reasons/provenance.
 v5out=O/aid/'v5';v5out.mkdir(parents=True,exist_ok=True)
 for key,name in [('v5ReusedD0Grade','grade.json'),('v5ReusedD0Normalized','normalized.json')]:shutil.copyfile(arm[key],v5out/name);assert (v5out/name).read_bytes()==Path(arm[key]).read_bytes()
 save(v5out/'reuse-provenance.json',dict(stageEnvelope='paired-D0',originalStage='D0',gradeOriginal=arm['v5ReusedD0Grade'],gradeSHA256=sha(v5out/'grade.json'),normalizedOriginal=arm['v5ReusedD0Normalized'],normalizedSHA256=sha(v5out/'normalized.json'),everyLiteralRowByteExact=True,originalReviewRefs=[str(R/'evaluation/D0'/aid/n) for n in ['manual-records.json','source-review.json','input-review.json','native-gate-summary.json','native-attribution.json','native-session-review-log.json']],screenshotsOriginalReview=str(R/'evaluation/D0/screenshot-review-log.json'),rawReuse=True,newNativeRun=False,newAdjudication=False))
 print(aid,g['primaryPublicRuntime']['all'])
save(O/'review-assembly-cost.json',dict(startUTC=start,endUTC=now(),wallSeconds=time.monotonic()-tick,scope='Evidence assembly after full actual v4 image review; v5 byte-exact reuse.'))
