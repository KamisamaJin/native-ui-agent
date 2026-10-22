import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/two/T3'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks,native_pixels,design_contract
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
index=json.loads((O/'evidence-index.json').read_text());hashes=json.loads((O/'input-hashes.json').read_text())
clip={'source-a':{'baseline':[25,26,27],'expanded':[59,60],'submitted':[141,142]},'source-b':{'baseline':[24,25],'expanded':[56,57],'submitted':[135,136]}}
audit={};checks=[]
for p in sorted((B/'evaluation-inputs/d0/T3').glob('*/*/*')):
 key=str(p.relative_to(B/'evaluation-inputs/d0/T3'));src,plat,case=key.split('/')
 inp=json.loads((p/'inputs.json').read_text());plan=json.loads((p/'plan.json').read_text());cat=json.loads((p/'catalog.json').read_text());auto=json.loads((p/'automatic.json').read_text());env=json.loads((p/'environment-check.json').read_text());root=B/inp['root'];obs=json.loads((B/inp['observation']).read_text());states={s['id']:native_checks.bound_state_evidence(obs,s)for s in plan['states']}
 decisions=[];attrs=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  state=row['state'];found,complete,why,cap=states[state];indices=[n for n,s in found]
  if src=='source-a' and plat=='ios' and case=='P2' and state=='submitted':
   actual=None;indices=[];reason='Unknown: exact submitted binding is coherent but frozen bound_state_evidence reports incomplete full-content interval union. The 5805-unit content is covered only through 5800; bottom sentinel visibility does not establish the missing tail. Inspected captured content, including new notice, six service cards, current summary, closed disclosure, action and footer; observed portions show no relevant defect, but cannot certify this whole-state proposition.'
  elif plat=='android' and case=='P2':
   actual=False;indices=clip[src][state];label='Hide handover notes'if state=='expanded'else'Show handover notes'
   if row['aspect']=='wrapping':
    reason=f'False: in fully on-screen disclosure "{label}", the leading H/S and the leading n of its wrapped "notes" line have visibly shaved left portions. This is present in original PNGs at multiple scroll offsets, away from viewport edges. Remaining required title/subtitle, notice, service labels/reason/details, summary, visible guidance, action and footer were inspected across the exact-state sweep; no other lost text was found. The approved question explicitly treats visible word clipping as false.'
   else:
    reason=f'False: the disclosure "{label}" is locally occluded at its curved left boundary: portions of the first letter and of the n on the next line disappear although the control is fully within the viewport. This is boundary occlusion of text, not merely a short wrapped line. The rest of the exact-state sweep shows separated cards, indicators, notes, summary, action and footer without collisions.'
   attrs.append({'id':row['id'],'cause':'product','reason':'Original fully visible disclosure text is cut by its own curved control boundary at multiple scroll offsets; the host viewport is clear of the affected letters. The production component uses a TextButton with zero content padding and full-width copy at enlarged P2 text. This supports component-owned text masking/occlusion, not a torn capture or scroll-edge artifact. The wrapping and overlap observations describe the same local defect, not independent bugs.','snapshot_indices':indices})
  else:
   actual=True
   if row['aspect']=='wrapping':
    reason='True: inspected all exact-state original viewport content from title to final footer, including caller notice replacement where applicable, all six service labels, unavailable status/reason, visible item details, current summary, disclosure label, visible global guidance and action. Required words remain readable across overlapping scroll frames without ellipsis or word clipping. Collapsed global guidance is intentionally absent.'
    if state=='expanded':reason=reason.replace('Collapsed global guidance is intentionally absent.','Expanded model.guidance is readable in its global position.')
    if plat=='ios' and case=='P2':reason+=' Oversized individual label words break between characters while preserving all characters, as BRIEF explicitly permits when an unbroken segment cannot fit.'
    if src=='source-a' and plat=='ios' and state=='submitted':reason+=' The displayed summary incorrectly omits the incoming b selection (separately attributed native-state failure); the actually displayed summary is itself fully readable, and this answer does not certify its business value.'
   else:
    reason='True: across the complete exact-state sweep, text blocks, selection indicators, unavailable status/reason, service details, summary, disclosure and any open guidance, primary action and footer occupy separate areas without collisions or occlusion. Viewport-edge cuts are recovered in adjacent coherent scroll frames; they are not component overlap.'
  decisions.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
 for f in auto['assertions']:
  if f['status']!='failed':continue
  state=f['state'];found,complete,why,cap=states[state];allowed=[n for n,s in found]
  if not allowed:continue
  indices=[n for n in f.get('snapshot_indices',[])if n in allowed]
  rid=f['id']
  if not indices:indices=[allowed[-1]]
  if rid=='baseline/primary-surface-color':
   reason='The native submit box and original PNG place the approved side strip entirely inside the disabled component button, away from text and host background. Frozen sampling recomputes a stable solid fill that contradicts the approved role, and the originals visibly show the whole disabled fill dimmed. The production code chooses the approved disabled palette but applies native .disabled with PlainButtonStyle, whose rendering changes it; the component owns final opaque fill under policy. This supports a product rendering failure, not sampling of a host-owned canvas. Exact platform style mechanism is an inference; measured mismatch remains authoritative.'
  elif rid=='replaced/primary-surface-color':
   reason='The fully visible component button is rendered in the same dimmed disabled fill as baseline, whereas the authoritative new input seeds available b and requires an enabled action. Raw native enablement is false and the summary is empty after fixture 1 arrives. This follows the component selection-replacement failure, with disabled styling also changing its final rendered palette. Original strip is internal solid fill, so observation suitability does not explain this F.'
  elif rid=='replaced/current-summary':
   reason='Caller replacement is demonstrated in the same native instance with fixture index 1, new input hash, successful caller_fixture_update and no business callback. The original changed notice is visible, but native/current summary reads No work selected and b is visibly unselected. Actual delivered fixtures seed available b; the compiled bridge only decodes and forwards that model. The component failed to restore incoming selection on revision change. The precise SwiftUI closure/state mechanism is not established; product state failure is supported independently of that mechanism.'
  elif rid=='replaced/primary-action-enabled':
   reason='After the successfully advancing same-instance caller update, raw native submit enablement is false and the original button is visibly disabled. Delivered fixture 1 seeds available b, which should make the primary action enabled. New notice and correct input binding establish delivery. This is downstream of the component dropping its incoming b selection, not missing native activation or a stale-input screenshot.'
  elif rid in ['reselected/current-summary','submitted/current-summary']:
   reason='Exact-state originals and native summary report only Brake inspection / 20 min after reselection of a; b remains visibly unselected despite fixture 1 specifying initial b. Successful reselection callback and stable current input/event bindings are present. This persists from the component replacement-selection defect and explains the missing Wheel alignment / 35 min contribution. It is not a text-wrapping defect or an old caller input.'
  elif rid=='submitted/successful-activation-callback':
   reason='Original step 8 records successful xcui_tap dispatch on enabled submit and exactly bicycle:submit:a in its callback interval, under fixture 1; the subsequent exact submitted screenshots retain only a and its 20-minute summary. Delivered fixture 1 seeded b, so the expected current draft was a,b. The component forwards its erroneous current set after dropping incoming b during revision replacement. This is a downstream product-state failure, not an undemonstrated tap or observer sorting difference.'
  else:raise RuntimeError(rid)
  attrs.append({'id':rid,'cause':'product','reason':reason,'snapshot_indices':indices})
 result={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':decisions},'attributions':attrs}
 out=O/key/'judge.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
 # Original native box evidence and state bindings, not judge-entered geometry values.
 stateaudit={}
 for state,(found,complete,why,cap)in states.items():
  targets={tuple(sorted(r['target'].items())) for r in plan['assertions']if r['state']==state and r.get('target')}
  targets.add((('identifier','bicycle.choice.b'),))
  targetfacts=[]
  for n,s in found:
   for target in sorted(targets):
    resolved=native_checks.resolve(s,dict(target),plat)
    if resolved['facts'].get('present'):
     targetfacts.append({'snapshot_index':n,'target':dict(target),'resolution':resolved})
  stateaudit[state]={'complete':complete,'reason':why,'binding':cap.get('binding')if cap else None,'indices':[n for n,s in found],'target_facts':targetfacts}
 pixelproofs={}
 for row in cat['rows']:
  if row['method']=='native_pixels':pixelproofs[row['id']]=[dict(native_pixels.sample(s,row['target'],plat,root,row['sampling']),snapshot_index=n)for n,s in states[row['state']][0]]
 steps=[]
 for n,s in enumerate(obs['steps']):
  steps.append({k:s.get(k)for k in ['action_index','action','type','target','state_id','outcome','dispatch','callback_delta','binding_after','same_process','before','after']})
 audit[key]={'states':stateaudit,'steps':steps,'pixel_recomputation':pixelproofs,'environment':{'status':env['status'],'expected':env['expected']},'inputs':index[key]['inputs']}
 for q in [root/'fixtures.json',root/'actions.json',B/inp['environment'],B/inp['design_root']/'design-lock.json',B/inp['design_root']/'approval.json',B/inp['design_root']/'policy.json']:
  if q.is_file():hashes[str(q.relative_to(B))]=sha(q)
 for name,claimed in inp['original_files'].items():
  relevant=(name.startswith(inp['design_root']+'/') and '/compiled/'not in name and '/validation-logs/'not in name)or name.endswith('/BicycleServiceIntake.swift')or name.endswith('/BicycleServiceIntake.kt')or(name.startswith(inp['root']+'/')and(name.endswith('/Bridge.swift')or name.endswith('/ObserverApp.swift')or name.endswith('/ObserverBridge.kt')))
  if relevant:
   q=B/name;actualsha=sha(q);hashes[name]=actualsha;checks.append({'path':name,'claimed_sha256':claimed,'actual_sha256':actualsha,'matches':claimed==actualsha})
for q in (B/'candidate-v8/scripts').glob('*.py'):hashes[str(q.relative_to(B))]=sha(q)
for q in [B/'candidate-v8/references/atomic-review.md',B/'candidate-v8/references/state-evidence.md'] :hashes[str(q.relative_to(B))]=sha(q)
(O/'native-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
(O/'hash-verification.json').write_text(json.dumps({'checked_relevant_source_artifacts':checks,'all_match':all(x['matches']for x in checks)},indent=2)+'\n')
(O/'input-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
with(O/'commands.log').open('a')as log:log.write('Read both production Swift and Kotlin components; approved fixture/API/BRIEF/bindings/policy/contract/approval; original compiled iOS bridge and host; delivered original fixtures. A rejected exploratory rg used nonexistent ios/P1/sources/* and exited before read; corrected to referenced compiled-project. Viewed every one of the 56 original-viewport contact sheets (all 652 selected frames, 422 unique viewport pixel groups) and direct original PNG checks of disabled-fill F, replacement state, and P2 clipped disclosure (baseline, expanded, submitted for both anonymous sources). Recomputed frozen native_pixels.sample for every catalog pixel atom and bound_state_evidence for every state; saved raw targets, steps, proof histograms in native-audit.json. Wrote 8 scoped judge.json via write_reviews.py. No external content, other judge, assignment or arm identity read.\n')
print('Wrote 8 judges;',sum(len(json.loads((O/k/'judge.json').read_text())['review']['decisions'])for k in index),'visual decisions;',sum(len(json.loads((O/k/'judge.json').read_text())['attributions'])for k in index),'failure attributions; hashes match',all(x['matches']for x in checks))
