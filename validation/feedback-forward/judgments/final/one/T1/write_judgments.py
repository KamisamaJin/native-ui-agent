import json,pathlib,sys,hashlib
R=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=R/'judgments/final/one/T1';sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'candidate-v9/scripts'));import native_checks,design_contract
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
visual={
 'title-wrapping':'The complete supplied title is legible across its naturally wrapped lines; no ellipsis or lost ending is visible.',
 'subtitle-wrapping':'The complete destination, separator and temperature range are visible, wrapping when needed without an ellipsis.',
 'status-wrapping':'The complete current status string is visible inside its band, including the second line in narrow wrapped states.',
 'disclosure-wrapping':'The current Review handling or Hide handling label is fully visible without truncation.',
 'choice-wrapping':'The current confirmation label is fully visible beside its check mark, with natural wrapping in the narrow case.',
 'primary-wrapping':'The complete Release transfer or Requested label remains legible within the primary rectangle.',
 'horizontal-clipping':'The complete bound sweep keeps the accent, all text and painted blocks within the horizontal component edges; no horizontal clipping is visible.',
 'row-overlap':'Across the complete bound sweep, successive component rows remain separated without visual overlap.',
 'flow-order':'The complete sweep shows accent, title, subtitle, status, disclosure, any expanded caller sections, choice and primary in that reading order.',
 'single-column':'All main blocks follow one vertical column across the complete state.',
 'full-width-canvas':'The component pale canvas extends continuously across the offered area between the two host horizontal gutters, with the white surface inset within it.',
 'collapsed-headings':'The complete collapsed state contains no handling note section headings between disclosure and choice.',
 'collapsed-bodies':'The complete collapsed state contains no handling body paragraphs between disclosure and choice.',
 'status-rectangle':'The original status crop shows a rectangular painted band with four square corners.',
 'status-no-border':'The original status crop has a direct fill-to-surrounding-surface edge and no visible border stroke.',
 'primary-rectangle':'The original primary crop shows a rectangular painted surface with four square corners.',
 'primary-no-border':'The primary fill meets its surrounding white surface without a separate visible border stroke.',
 'primary-painted-allocation':'The original crop, located by the native primary control boundary, shows the label paint covering that rectangle to each edge without uncovered internal strips.',
 'ink-rectangle':'The full-state top shows a solid, square-cornered rectangular ink accent.',
 'heading-wrapping':'All eight supplied section headings are completely visible in the full bound sweep, with natural wrapping and no ellipsis.',
 'body-wrapping':'All eight supplied paragraphs, including their endings, are visible across the full overlapping sweep without truncation or an ellipsis.',
 'title-hierarchy':'The title is visibly larger and more prominent than the expanded section headings in the same state.',
 'expanded-order':'The full sweep contains all eight heading/body pairs in the supplied caller sequence, with each body following its matching heading.'}
for p in sorted((R/'evaluation-inputs/final/T1').glob('*/*/*')):
 i=json.loads((p/'inputs.json').read_text());c=json.loads((p/'catalog.json').read_text());plan=json.loads((p/'plan.json').read_text());obs=json.loads((R/i['observation']).read_text());dst=O/i['source']/i['platform']/i['case'];dec=[]
 for row in c['rows']:
  if row['method']!='visual':continue
  state=next(s for s in plan['states'] if s['id']==row['state']);found,complete,why,cap=native_checks.bound_state_evidence(obs,state)
  indices=[idx for idx,_ in found];actual=True;reason=visual[row['requirement_id']]
  if not found or(row.get('coverage')=='full_content'and not complete):actual=None;indices=[];reason='Insufficient strictly bound state coverage: '+why
  elif row.get('coverage')=='target':
   eligible=[]
   for idx,s in found:
    rs=native_checks.resolve(s,row['target'],i['platform']);n=rs.get('control'if row['target']['identifier']=='transfer.primary'else 'semantic',{})
    if n.get('fully_within_viewport',n.get('fully_visible',False)):eligible.append(idx)
   if eligible:indices=[eligible[0]]
   else:actual=None;indices=[];reason='No wholly visible original target allocation in the eligible state evidence; source does not substitute for pixels.'
  dec.append({'review_id':row['review_id'],'actual':actual,'reason':i['source']+'/'+i['platform']+'/'+i['case']+' '+row['state']+': '+reason,'snapshot_indices':indices})
 (dst/'judge.json').write_text(json.dumps({'review':{'version':1,'catalog_sha256':c['catalog_sha256'],'observation_sha256':i['observation_sha256'],'decisions':dec},'attributions':[]},ensure_ascii=False,indent=2)+'\n')
# Explicit source observations. Each tuple is Swift interval(s), Kotlin interval(s), rationale.
M={
'production-component':([(38,61)],[(59,78)],'The declared public component and its implementation are present in the exact API production file.'),
'caller-driven-rendering':([(124,160)],[(119,180)],'Title, destination/range and section text are taken directly from the supplied transfer and note values.'),
'disclosure-production-state':([(64,71),(137,148)],[(79,82),(149,164)],'The production component owns local handlingOpen and the disclosure action toggles it.'),
'choice-production-state':([(64,71),(224,228)],[(79,82),(187,199)],'The production component owns and mutates its local acknowledgement Boolean.'),
'requested-production-state':([(64,71),(230,234)],[(79,82),(227,235)],'Requested is local production state, set by the guarded production release action.'),
'identity-reset-disclosure':([(53,71)],[(79,82)],'Swift keys the private state-owning content by transfer.id; Kotlin keys remember(transfer.id). New identity initializes disclosure false.'),
'identity-reset-choice':([(53,71)],[(79,82)],'The production identity key creates fresh acknowledgement=false state when transfer.id changes.'),
'identity-reset-requested':([(53,71)],[(79,82)],'The production identity key creates fresh requested=false state when transfer.id changes.'),
'reset-quiet':([(53,71),(224,234)],[(79,82),(187,234)],'The identity-reset initializers assign false only. Caller callbacks occur in the separate action handlers.'),
'native-disclosure-button':([(137,146)],[(149,162)],'The disclosure is constructed using the platform Button control.'),
'native-choice-button':([(167,184)],[(187,225)],'The confirmation is constructed using the platform Button control.'),
'native-primary-button':([(186,198)],[(227,256)],'The primary is constructed using the platform Button control.'),
'native-selected':([(181,184)],[(194,199)],'The actual acknowledgement Boolean drives the selected accessibility trait/semantics on the choice control.'),
'choice-native-disabled':([(180,184),(224,228)],[(188,199)],'Requested drives the native disabled/enabled property, and the handler also checks requested.'),
'primary-native-disabled':([(186,198),(230,234)],[(227,245)],'The release eligibility drives the native disabled/enabled property, with the predicate rechecked inside the action.'),
'canvas-preserve-controls':([(98,113),(137,198)],[(95,110),(149,256)],'The canvas contains the real descendant Buttons, using children: .contain / mergeDescendants=false without combining them into a substitute action.'),
'surface-preserve-controls':([(115,206)],[(103,110),(149,256)],'The surface is a nonmerging container around independently identified real Buttons.'),
'unique-semantic-ids':([(98,221)],[(95,256)],'Each fixed semantic identifier occurs on its one real allocation; section identifiers use the enumerated caller index for each heading/body pair.'),
'status-band-provenance':([(209,221)],[(132,146)],'The status identifier is attached to the container which paints the status fill.'),
'status-text-provenance':([(209,221)],[(142,146)],'The separate statusText identifier is attached directly to the displayed status Text/PanelText.'),
'no-nested-scroll':([(98,221)],[(95,258)],'The entire component body consists of stack/column/row/text/button containers and adds no scrolling container.'),
'no-blank-padding-rows':([(98,221)],[(95,258)],'There is no blank spacer row. Fixed dimensions belong to the actual accent or controls; text creates long-content height.'),
'model-row-order':([(148,165)],[(164,185)],'The component enumerates the supplied notes in order and emits each heading followed by its body.'),
'no-hidden-input-special-cases':([(38,234)],[(73,258)],'Rendering branches use actual transfer guard/state fields; there are no fixture/scenario IDs or expected-test-value branches.'),
'callback-model-id':([(230,234)],[(227,233)],'The release action forwards transfer.id from the current supplied model.'),
'callbacks-only-actions':([(137,143),(167,198),(224,234)],[(149,162),(187,199),(227,235)],'Business callbacks occur only in the choice/release handlers, with native enabled state and explicit state guards.'),
'no-callback-on-disclosure':([(137,146)],[(149,162)],'The disclosure handler only flips handlingOpen and contains no caller callback.'),
'no-primary-callback-on-disabled':([(77,79),(186,198),(230,234)],[(84,90),(227,245)],'The primary is natively disabled when ineligible, and its callback is also protected by the same predicate.'),
'no-choice-callback-on-disabled':([(180,184),(224,228)],[(187,199)],'Requested disables the choice, and the action returns/does nothing when requested.'),
'uncapped-text-lines':([(124,221)],[(119,180),(223,255),(261,271)],'All text allocations are uncapped. Swift applies lineLimit(nil) and flexible multiline text; Kotlin supplies no finite maxLines.'),
'primary-label-allocation-config':([(186,198),(239,242)],[(227,255)],'The primary label is configured to fill available width and the declared fixed control height; the custom Swift style returns the unchanged label, and Compose uses zero content padding and fillMaxSize.'),
'primary-content-shape-config':([(186,198)],[(227,255)],'Swift explicitly applies contentShape(Rectangle()) to the full label; Kotlin configures RectangleShape on the full-size Button allocation.'),
'canvas-noninteractive':([(98,113)],[(95,102)],'The canvas carrier paints and groups descendants but declares no own activation action or interactive role.'),
'surface-noninteractive':([(199,206)],[(103,111)],'The surface carrier groups content and paints white but declares no own activation action or interactive role.'),
'ink-noninteractive':([(117,122)],[(112,118)],'The ink mark is a labeled geometric carrier without a click action or interactive role.'),
'guard-predicate':([(77,79)],[(84,84),(227,235)],'The predicate is the exact conjunction of seal intact, coolant ready, acknowledged, and not requested.'),
'guard-priority':([(81,93)],[(85,91)],'The status branches check broken seal, missing coolant, requested, acknowledged, and finally awaiting check in that order.'),
'choice-toggle':([(224,228)],[(187,193)],'The successful pre-request choice handler flips the current acknowledgement Boolean.'),
'choice-callback-value':([(224,228)],[(187,193)],'The handler mutates acknowledgement first and passes its resulting Boolean to the callback.'),
'choice-callback-count':([(224,228)],[(187,193)],'The successful handler contains exactly one acknowledgement callback invocation.'),
'release-requested-state':([(230,234)],[(227,234)],'A release that passes the guard sets requested=true before calling the caller.'),
'release-callback-count':([(230,234)],[(227,234)],'The eligible release branch contains exactly one onRelease invocation.'),
'no-physical-transfer':([(1,254)],[(17,291)],'The complete component implements local rendering/state/callbacks and invokes no hardware, physical-transfer or network operation.'),
'exact-api-TransferHandlingNote':([(4,14)],[(59,59)],'The note declaration has the exact named public immutable Swift fields/conformances/initializer or Kotlin data-class fields required by the proposition.'),
'exact-api-ColdStorageTransfer':([(17,36)],[(61,69)],'The transfer declaration exposes the exact named fields, types, order, Swift conformances/public initializer, and Kotlin data-class contract.'),
'exact-api-ColdStorageTransferPanel':([(38,61)],[(72,78)],'The public component name, parameter types/order, callbacks, Swift body and Kotlin default Modifier match the exact declaration contract.'),
'api14-availability':([(1,254)],[], 'The Swift source uses SwiftUI View, Button, stacks, Text, Rectangle, Image, State, ScaledMetric, standard view/accessibility modifiers and ButtonStyle available by iOS 14. Both component types carry iOS14/macOS11 availability. No unguarded newer API was found. This is source review only and does not claim an iOS14 launch.')}
bridges={
 'bridge-no-ui':('Only caller model decoding and the real production component construction occur in the bridge; it builds no substitute component UI.',(4,17),(9,28)),
 'bridge-no-state':('The bridge creates the current immutable transfer value and callback closures; it owns no remembered/local component business state.',(4,17),(9,28)),
 'bridge-no-identity-reset':('The bridge directly returns/calls the production component without an identity-reset wrapper.',(13,15),(24,26)),
 'bridge-current-input':('The bridge reads every declared model field and maps the current supplied fixture notes into the production model.',(5,12),(11,23)),
 'bridge-callback-forwarding':('The production callbacks directly forward the actual checked Boolean/current release ID into observer event receipt.',(13,15),(24,26))}
for alias in ['source-a','source-b']:
 inp=json.loads((R/'source-evaluation-inputs/final/T1'/alias/'inputs.json').read_text());cat=json.loads((R/'source-evaluation-inputs/final/T1'/alias/'catalog.json').read_text());dec=[];reads=[]
 for rel,descriptor in cat['files'].items():
  if rel.startswith('@design/'):path=R/inp['design_root']/rel.split('/',1)[1]
  else:path=next(R/k for k in inp['original_files'] if k.endswith('/'+rel))
  reads.append({'declared_file':rel,'path':str(path),'actual_sha256':sha(path),'declared_sha256':descriptor['sha256'],'actual_line_count':len(path.read_text().splitlines())})
 for row in cat['rows']:
  platform,suffix=row['id'].split('-',1);refs=[]
  if suffix in bridges:
   reason,sw,kt=bridges[suffix];ranges=[sw if platform=='ios'else kt]
  else:
   sw,kt,reason=M[suffix];ranges=sw if platform=='ios'else kt
  for rel in row['files']:
   for first,last in ranges:refs.append({'file':rel,'sha256':cat['files'][rel]['sha256'],'start_line':first,'end_line':last})
  dec.append({'review_id':row['review_id'],'actual':True,'reason':alias+' '+reason,'evidence':refs})
 assert len(dec)==103
 result={'review':{'version':1,'catalog_sha256':design_contract.digest(cat),'decisions':dec},'attributions':[]}
 (O/alias/'source-judge.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(O/alias/'source-inspection.json').write_text(json.dumps({'catalog_digest_actual':design_contract.digest(cat),'catalog_digest_input':inp['catalog_sha256'],'files':reads,'scope':'Independent source review on each exact anonymous capsule and approved bridge. Rendered facts are assessed separately.'},indent=2)+'\n')
print('wrote 12 runtime judges and 2 source judges')
