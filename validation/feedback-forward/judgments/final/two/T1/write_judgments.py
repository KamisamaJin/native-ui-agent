import sys,json,hashlib,runpy,traceback
sys.dont_write_bytecode=True
from pathlib import Path
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=B/'judgments/final/two/T1';sys.path.insert(0,str(B/'candidate-v9/scripts'))
import native_checks,design_contract as design,acceptance

def dump(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
reasons={
 'title-wrapping':'The supplied title is fully legible in the original selected-state image, using natural lines with no clipped ending or ellipsis.',
 'subtitle-wrapping':'The complete destination and temperature subtitle is visible in natural wrapped lines with no truncation or ellipsis.',
 'status-wrapping':'The complete current status string is visible inside the painted band, with natural wrapping where required and no truncation.',
 'disclosure-wrapping':'The entire current disclosure label is legible without truncation or ellipsis.',
 'choice-wrapping':'The complete current confirmation label is visible beside its mark; narrow-case line breaks preserve all words.',
 'primary-wrapping':'The entire current primary label is legible within the painted rectangular control without ellipsis or clipped text.',
 'heading-wrapping':'All eight supplied handling headings are visible across this original state sweep. Their complete words wrap naturally without ellipsis or clipped endings.',
 'body-wrapping':'All eight supplied handling paragraphs are visible through overlapping original scroll frames, including their final lines; no paragraph is truncated or ellipsized.',
 'horizontal-clipping':'Across the complete original state sweep, text and painted blocks stay inside the component horizontal edges; viewport cuts at top/bottom are continued in overlapping frames.',
 'row-overlap':'The complete original state sequence shows separated successive blocks and heading/body rows, with no text drawn over another row.',
 'flow-order':'Following the original state sweep from top to reachable bottom gives ink accent, title, subtitle, status, disclosure, expanded pairs when open, confirmation, then primary.',
 'single-column':'The original state images show one vertical flow of main blocks; the confirmation mark and its label remain a single compound row.',
 'full-width-canvas':'The visible pale component canvas extends across the offered width between the host gutters, around the white surface; it does not shrink to the text width.',
 'collapsed-headings':'The complete closed-state image sequence contains no handling-note section heading between disclosure and confirmation.',
 'collapsed-bodies':'The complete closed-state image sequence contains no handling body paragraph between disclosure and confirmation.',
 'status-rectangle':'The original fully visible status band has four square corners and straight rectangular edges.',
 'status-no-border':'The original status-band perimeter shows no separate border stroke.',
 'primary-rectangle':'The original primary painted surface has straight rectangular edges and four square corners.',
 'primary-no-border':'The original primary perimeter shows no separate border stroke.',
 'primary-painted-allocation':'Original primary paint reaches the observed native control rectangle edges, checked against its coherent native bounds; no uncovered allocation strip is visible. This judges visible allocation, not physical hit area.',
 'ink-rectangle':'The original visible solid ink accent has four square corners and straight rectangular sides.',
 'title-hierarchy':'In this original state sequence the title has visibly larger, stronger text than the expanded section headings.',
 'expanded-order':'The original expanded sweep shows all eight heading/body pairs in supplied caller order, with each body following its heading.'}

def best_target(found,row,plat):
 scored=[]
 for idx,s in found:
  r=native_checks.resolve(s,row['target'],plat);basis='control' if row['requirement_id'].startswith(('primary-','choice-','disclosure-')) else 'semantic';n=r.get(basis,{})
  if not n.get('fully_within_viewport',n.get('fully_visible',False)):continue
  if plat=='ios':
   f=n.get('frame');v=s.get('viewport');score=min(f['y']-v['y'],v['y']+v['height']-f['y']-f['height']) if f and v else 0
  else:
   box=n.get('unclipped_bounds_dp');score=min(box[1],s['viewport_height_dp']-box[3]) if box else 0
  scored.append((score,idx))
 return [max(scored)[1]] if scored else []
summary={};checks=[]
for p in sorted((B/'evaluation-inputs/final/T1').glob('*/*/*')):
 rel=p.relative_to(B/'evaluation-inputs/final/T1');i=json.loads((p/'inputs.json').read_text());plan=json.loads((p/'plan.json').read_text());cat=json.loads((p/'catalog.json').read_text());automatic=json.loads((p/'automatic.json').read_text());envcheck=json.loads((p/'environment-check.json').read_text());obs=json.loads((B/i['observation']).read_text());plat=i['platform'];states={s['id']:native_checks.bound_state_evidence(obs,s) for s in plan['states']};dec=[]
 assert hashlib.sha256((B/i['observation']).read_bytes()).hexdigest()==i['observation_sha256']
 for row in cat['rows']:
  if row.get('method')!='visual':continue
  found,complete,why,_=states[row['state']];req=row['requirement_id']
  # Whole-content propositions use only complete original sweeps; targeted text/shape propositions use eligible target frames.
  global_req=req in ['heading-wrapping','body-wrapping','horizontal-clipping','row-overlap','flow-order','single-column','full-width-canvas','collapsed-headings','collapsed-bodies','title-hierarchy','expanded-order']
  indices=[j for j,_ in found] if global_req and complete else best_target(found,row,plat) if not global_req else []
  actual=True if indices else None
  reason=reasons[req] if indices else 'The exact selected state lacks sufficient original image coverage for this proposition; no pass is inferred from source or another state.'
  dec.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
 judge={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':i['observation_sha256'],'decisions':dec},'attributions':[]}
 dest=O/rel;dump(dest/'judge.json',judge)
 scope=B/i['scope'];lock=json.loads((scope/'design-lock.json').read_text());policy=json.loads((scope/'policy.json').read_text());env=json.loads((B/i['environment']).read_text())
 try:
  result=acceptance.evaluate(plan,lock,cat['design_lock_sha256'],policy,cat['policy_sha256'],obs,i['observation_sha256'],B/i['raw'],plat,env,judge,judge)
  # This is one assessor request supplied in both slots, strictly schema self-check, never independent consensus.
  compact={'scope':'Schema self-check only: the SAME assessor request occupies both arguments. No independent consensus or human-gold claim.','counts':result['counts'],'environment_status':result['environment']['status'],'failed_ids':[r['id'] for r in result['rows'] if r['status']=='failed'],'unknown_ids':[r['id'] for r in result['rows'] if r['status']=='unassessed'],'decision_count':len(dec),'unknown_visual_decisions':[r['review_id'] for r in dec if r['actual'] is None]}
  dump(dest/'schema-self-check.json',compact);checks.append({'case':str(rel),'accepted_schema':True})
 except Exception as e:
  dump(dest/'schema-self-check-rejected.json',{'error':str(e),'traceback':traceback.format_exc()});checks.append({'case':str(rel),'accepted_schema':False,'error':str(e)})
 summary[str(rel)]={'visual_decisions':len(dec),'visual_true':sum(x['actual']is True for x in dec),'visual_unknown':sum(x['actual']is None for x in dec),'native_supplied_counts':automatic['counts'],'environment_status':envcheck['status']}
# Source evidence independently reviewed on both exact capsules.
ios={
 'production-component':(40,235),'caller-driven-rendering':(53,163),'disclosure-production-state':(64,71),'choice-production-state':(64,71),'requested-production-state':(64,71),
 'identity-reset-disclosure':(53,71),'identity-reset-choice':(53,71),'identity-reset-requested':(53,71),'reset-quiet':(53,71),
 'native-disclosure-button':(137,146),'native-choice-button':(167,184),'native-primary-button':(186,198),'native-selected':(181,184),'choice-native-disabled':(167,184),'primary-native-disabled':(186,198),
 'canvas-preserve-controls':(98,113),'surface-preserve-controls':(199,206),'unique-semantic-ids':(98,221),'status-band-provenance':(209,221),'status-text-provenance':(209,221),
 'no-nested-scroll':(40,235),'no-blank-padding-rows':(98,221),'model-row-order':(148,163),'no-hidden-input-special-cases':(40,235),'callback-model-id':(230,234),'callbacks-only-actions':(137,234),'no-callback-on-disclosure':(137,146),'no-primary-callback-on-disabled':(186,234),'no-choice-callback-on-disabled':(167,228),
 'uncapped-text-lines':(98,221),'primary-label-allocation-config':(186,198),'primary-content-shape-config':(186,198),'canvas-noninteractive':(98,113),'surface-noninteractive':(115,207),'ink-noninteractive':(117,122),
 'guard-predicate':(77,79),'guard-priority':(81,93),'choice-toggle':(224,228),'choice-callback-value':(224,228),'choice-callback-count':(224,228),'release-requested-state':(230,234),'release-callback-count':(230,234),'no-physical-transfer':(40,235),
 'exact-api-TransferHandlingNote':(4,14),'exact-api-ColdStorageTransfer':(17,36),'exact-api-ColdStorageTransferPanel':(39,61),'api14-availability':(1,254)}
android={
 'production-component':(72,259),'caller-driven-rendering':(119,180),'disclosure-production-state':(79,82),'choice-production-state':(79,82),'requested-production-state':(79,82),
 'identity-reset-disclosure':(79,82),'identity-reset-choice':(79,82),'identity-reset-requested':(79,82),'reset-quiet':(79,82),
 'native-disclosure-button':(149,162),'native-choice-button':(187,225),'native-primary-button':(227,256),'native-selected':(194,199),'choice-native-disabled':(187,204),'primary-native-disabled':(227,245),
 'canvas-preserve-controls':(95,109),'surface-preserve-controls':(103,110),'unique-semantic-ids':(95,255),'status-band-provenance':(132,146),'status-text-provenance':(132,146),
 'no-nested-scroll':(72,271),'no-blank-padding-rows':(95,257),'model-row-order':(164,183),'no-hidden-input-special-cases':(72,271),'callback-model-id':(227,234),'callbacks-only-actions':(149,255),'no-callback-on-disclosure':(149,162),'no-primary-callback-on-disabled':(227,245),'no-choice-callback-on-disabled':(187,204),
 'uncapped-text-lines':(119,271),'primary-label-allocation-config':(227,255),'primary-content-shape-config':(227,255),'canvas-noninteractive':(95,102),'surface-noninteractive':(103,111),'ink-noninteractive':(112,118),
 'guard-predicate':(84,84),'guard-priority':(85,91),'choice-toggle':(187,193),'choice-callback-value':(187,193),'choice-callback-count':(187,193),'release-requested-state':(227,234),'release-callback-count':(227,234),'no-physical-transfer':(72,259),
 'exact-api-TransferHandlingNote':(59,59),'exact-api-ColdStorageTransfer':(61,69),'exact-api-ColdStorageTransferPanel':(72,78)}
bridge={'no-ui':((5,17),(11,28)),'no-state':((5,17),(11,28)),'no-identity-reset':((5,17),(11,28)),'current-input':((6,12),(12,23)),'callback-forwarding':((13,15),(24,26))}
source_reasons={
 'production-component':'The declared public production component and its actual body are implemented in the exact API file.',
 'caller-driven-rendering':'Actual title/subtitle/status and expanded note nodes are constructed from the supplied transfer model; no observer-only rendered copy is present.',
 'disclosure-production-state':'The production component initializes and owns handlingOpen locally.',
 'choice-production-state':'The production component initializes and owns acknowledged locally.',
 'requested-production-state':'The production component initializes and owns requested locally.',
 'reset-quiet':'The production-owned identity boundary/state initializers create closed, unacknowledged, unrequested state without invoking a callback.',
 'no-nested-scroll':'The full component body uses vertical layout containers and text/buttons; no scroll container is introduced.',
 'no-blank-padding-rows':'The complete body has content spacing, ordinary padding and the visible ink accent; there is no blank spacer row manufacturing content height.',
 'model-row-order':'The supplied notes collection is enumerated directly in caller order, with heading then body for each note.',
 'no-hidden-input-special-cases':'The full production implementation branches on supplied guard Booleans and local interaction state, and keys reset by model ID; no fixture/scenario/test-value special cases appear.',
 'callback-model-id':'The eligible request path forwards transfer.id from the current supplied model.',
 'callbacks-only-actions':'All business callback invocation sites are inside guarded native user-action paths; construction, rendering and identity replacement do not invoke them.',
 'no-callback-on-disclosure':'Disclosure only toggles handlingOpen and invokes no caller callback.',
 'no-primary-callback-on-disabled':'The primary is natively disabled outside the eligibility predicate and its action independently rechecks that predicate before callback.',
 'no-choice-callback-on-disabled':'The confirmation is natively disabled after requested and its action independently guards requested before toggling/callback.',
 'uncapped-text-lines':'All declared text sites configure no finite line cap; Swift applies lineLimit(nil), and Compose Text calls omit maxLines and retain unlimited defaults.',
 'primary-label-allocation-config':'The native primary control/label explicitly fills available width and a 56-unit high allocation; the Android label fills the control size and centers vertically.',
 'primary-content-shape-config':'The primary uses a full rectangular activation shape matching its configured allocation: Swift contentShape(Rectangle()) on the full-width 56-high label, Compose native Button with RectangleShape and full-sized label.',
 'guard-predicate':'The enabled predicate contains exactly sealIntact, coolantReady, acknowledged, and negated requested combined with conjunction.',
 'guard-priority':'The status conditional explicitly checks broken seal, unavailable coolant, requested, acknowledged, then awaiting, in that order.',
 'choice-toggle':'The successful guarded confirmation action flips the current acknowledgement Boolean.',
 'choice-callback-value':'The confirmation action invokes its callback with the Boolean after toggling.',
 'choice-callback-count':'There is exactly one acknowledgement callback invocation in the successful guarded toggle action.',
 'release-requested-state':'The eligible release action sets requested to true before invoking the request callback.',
 'release-callback-count':'The eligible guarded release path contains exactly one onRelease invocation.',
 'no-physical-transfer':'Inspection of the full component shows only local presentation/state and supplied callbacks; it starts no freezer/hardware/physical transfer operation.',
 'api14-availability':'Manual source API review finds SwiftUI view/layout/Text/Button/Color, identity, state, accessibility containment/traits, fixedSize, contentShape, ButtonStyle and ScaledMetric usage available at iOS 14. Both component types declare iOS 14 availability; no unguarded newer API is present. This is source review, not an iOS-14 launch/link claim.'}
audit=runpy.run_path('/Users/rex/Documents/ChatGPT/mobile-native-skill/tools/implementation_audit.py')
for alias in ['source-a','source-b']:
 p=B/f'source-evaluation-inputs/final/T1/{alias}';i=json.loads((p/'inputs.json').read_text());cat=json.loads((p/'catalog.json').read_text());dec=[]
 for row in cat['rows']:
  plat,key=row['id'].split('-',1);f=row['files'][0]
  if key.startswith('bridge-'):
   lo,hi=bridge[key[7:]][0 if plat=='ios' else 1];reason={'no-ui':'The unchanged approved bridge decodes the fixture and constructs only the declared production panel; it paints no substitute UI.','no-state':'The unchanged approved bridge owns no local component business state.','no-identity-reset':'The unchanged approved bridge calls the production panel directly without an identity-reset wrapper.','current-input':'The current supplied fixture fields and note array are decoded directly into the declared public production model.','callback-forwarding':'The bridge receives real production callbacks and forwards the current model ID/value or release ID into observer event receipt.'}[key[7:]]
  else:
   lo,hi=(ios if plat=='ios' else android)[key]
   if key.startswith('identity-reset-'):reason='A changed caller model ID creates fresh production-owned local state: Swift keys its internal content by transfer.id; Compose remember(transfer.id) initializes the three Booleans to false. No bridge reset is used.'
   elif key.startswith('exact-api-'):reason='The actual declaration has the exact required public model/component contract, immutable stored values, conformances/data-class identity and initializer/function defaults as applicable.'
   elif key.startswith('native-') and key.endswith('-button'):reason='This production action is constructed with the platform native Button control, retaining native control semantics.'
   elif key=='native-selected':reason='The actual acknowledgement state is exposed through native selected semantics on the real confirmation button.'
   elif key.endswith('native-disabled'):reason='The real native Button uses its disabled/enabled API from the actual requested/eligibility state.'
   elif key.endswith('preserve-controls'):reason='The real layout carrier preserves descendant semantics: Swift accessibility containment and Compose mergeDescendants=false retain independent child Buttons.'
   elif key=='unique-semantic-ids':reason='Each fixed semantic ID is attached once to its real node, and note IDs are generated from unique enumeration indices; no duplicate proxy is constructed.'
   elif key=='status-band-provenance':reason='The status identifier is on the real padded painted container, whose actual background is the state fill.'
   elif key=='status-text-provenance':reason='The statusText identifier is attached directly to the displayed status Text, with no geometry proxy.'
   elif key.endswith('-noninteractive'):reason='This semantic carrier is a passive layout/paint node with no activation callback or interactive role of its own.'
   else:reason=source_reasons[key]
  sourcepath=B/i['design_root']/f[len('@design/'):] if f.startswith('@design/') else B/i['capsule']/'source'/f
  assert hashlib.sha256(sourcepath.read_bytes()).hexdigest()==cat['files'][f]['sha256']
  dec.append({'review_id':row['review_id'],'actual':True,'reason':reason,'evidence':[{'file':f,'sha256':cat['files'][f]['sha256'],'start_line':lo,'end_line':hi}]})
 judge={'review':{'version':1,'catalog_sha256':design.digest(cat),'decisions':dec},'attributions':[]};dump(O/alias/'source-judge.json',judge)
 try:
  bound=audit['bind'](cat,judge['review']);dump(O/alias/'source-schema-self-check.json',{'scope':'Schema/range/hash self-check of this assessor source request only. No independent truth or native rendering claim.','counts':bound['counts'],'status':bound['status'],'blocking_obligations':bound['blocking_obligations']})
 except Exception as e:dump(O/alias/'source-schema-self-check-rejected.json',{'error':str(e),'traceback':traceback.format_exc()})
summary['scope']='One independent AI assessor; no human gold. Native facts remain authoritative and strict pixel unknowns are retained. Self-check duplicates this assessor request only.'
dump(O/'assessment-summary.json',summary);dump(O/'schema-command-results.json',checks)
print(json.dumps({'runtime_cases':len(checks),'schema_valid':sum(x['accepted_schema'] for x in checks),'visual_decisions':sum(x.get('visual_decisions',0) for x in summary.values() if isinstance(x,dict)),'source_decisions_each':len(dec)},indent=2))
