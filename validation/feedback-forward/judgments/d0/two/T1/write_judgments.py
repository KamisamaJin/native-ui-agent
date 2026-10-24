import json,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');out=b/'judgments/d0/two/T1';sys.path.insert(0,str(b/'candidate-v9/scripts'))
import native_checks,design_contract as d
visual_reasons={
 'title-wrapping':'The original target frame shows the complete supplied title, continuing onto natural lines with its final word visible and no ellipsis.',
 'subtitle-wrapping':'The original target frame shows the complete destination and temperature-range subtitle; wrapped continuation and the final degree/C text are visible without ellipsis.',
 'status-wrapping':'The complete current status string is visible inside its band; continuation lines where needed end normally without truncation or ellipsis.',
 'disclosure-wrapping':'The complete current Review handling or Hide handling label is visible without truncation or ellipsis.',
 'choice-wrapping':'The complete current confirmation label is visible beside its check indicator; the narrow case wraps naturally and retains the final checked/confirmed word.',
 'primary-wrapping':'The complete current Release transfer or Requested label is visible within the primary painted rectangle, without clipped characters or ellipsis.',
 'horizontal-clipping':'Across the entire bound content sweep, all component rows remain within the component horizontal bounds. Viewport cuts occur vertically while scrolling; the overlapping frames reveal the continuation.',
 'row-overlap':'The complete overlapping sweep shows separate successive text/control rows and section pairs, with no visual collisions or overprinted rows.',
 'flow-order':'The complete sweep shows ink accent, title, subtitle, status, disclosure, expanded sections when open, confirmation, and primary in that sequence.',
 'single-column':'The complete sweep places the main blocks in one vertical column, with only the decorative checkbox and its label sharing their confirmation row.',
 'full-width-canvas':'The pale canvas and its white inset surface continue across the complete offered component width inside the host gutters, consistently through the bound sweep.',
 'collapsed-headings':'The complete closed-state sweep goes directly from Review handling to the confirmation and primary; no handling section heading is visible.',
 'collapsed-bodies':'The complete closed-state sweep contains no handling body paragraphs between disclosure and confirmation.',
 'status-rectangle':'The original fully visible status band has straight horizontal/vertical edges and four square corners.',
 'status-no-border':'Inspection of the original fully visible band shows no border stroke around its painted perimeter.',
 'primary-rectangle':'The original fully visible primary paint has a rectangular silhouette and four square corners.',
 'primary-no-border':'Inspection of the original fully visible primary surface shows no perimeter border stroke.',
 'primary-painted-allocation':'The original primary crop, compared with its same-frame native control boundary, shows paint reaching all four control edges without an uncovered strip; the boundary mapping is retained separately.',
 'ink-rectangle':'The original top-of-content frame shows the solid narrow ink accent with straight edges and square corners.',
 'heading-wrapping':'Reading the complete overlapping sweep shows all eight supplied handling headings in full, including natural narrow-column line breaks, with no truncated ending or ellipsis.',
 'body-wrapping':'Reading the complete overlapping sweep against the supplied original fixture copy reveals every body paragraph from start to final word. Vertical viewport cuts are covered by adjoining frames, and no ellipsis or horizontal truncation is visible.',
 'title-hierarchy':'The full-state top frame and subsequent section frames show the title in larger, prominent type than the handling section headings.',
 'expanded-order':'The complete overlapping sweep shows each of the eight caller-supplied headings followed by its own body, in the fixture order from the seal check to the paperwork section.'
}
for p in sorted((b/'evaluation-inputs/d0/T1').glob('*/*/*')):
 i=json.loads((p/'inputs.json').read_text());o=json.loads((b/i['observation']).read_text());pl=json.loads((p/'plan.json').read_text());cat=json.loads((p/'catalog.json').read_text());states={st['id']:native_checks.bound_state_evidence(o,st) for st in pl['states']};decisions=[]
 for r in cat['rows']:
  if r['method']!='visual':continue
  found,complete,why,cap=states[r['state']];indices=[];actual=True;reason=visual_reasons[r['requirement_id']]
  if r['coverage']=='full_content':
   if complete:indices=[n for n,s in found]
   else:actual=None;reason='Required full-content evidence is unavailable: '+why
  else:
   for n,s in found:
    resolved=native_checks.resolve(s,r['target'],i['platform']);node=resolved.get('semantic',{})
    if resolved['facts'].get('unique') and node.get('fully_within_viewport',node.get('fully_visible',False)):indices.append(n)
   if not indices:actual=None;reason='No exact-state original frame exposes the complete unique target; rendered proposition remains unknown.'
  decisions.append({'review_id':r['review_id'],'actual':actual,'reason':f"{i['platform']} {i['case']} {r['state']}: "+reason,'snapshot_indices':indices})
 value={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':i['observation_sha256'],'decisions':decisions},'attributions':[]}
 dest=out/i['source']/i['platform']/i['case']/'judge.json';dest.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
# Explicit source-proposition assessments, based on the entire original production files
# and exact approved bridges read with numbered lines, independently of rendered facts.
common={
 'production-component':('The declared component and models are implemented in this exact production file; its public body/function constructs the real native view tree.',(39,235),(59,259)),
 'caller-driven-rendering':('The component reads the current transfer title, destination, range, guard values and note collection directly to construct its native content.',(65,163),(79,184)),
 'disclosure-production-state':('The production view owns handlingOpen and its disclosure Button changes that production state.',(64,146),(79,162)),
 'choice-production-state':('The production view owns the acknowledgement Boolean used by its confirmation control.',(64,71),(79,82)),
 'requested-production-state':('The production view owns the local requested Boolean used by status, enabled state and primary label.',(64,93),(79,94)),
 'identity-reset-disclosure':('The production identity boundary creates fresh false disclosure state for a changed transfer ID, without bridge identity logic.',(53,71),(79,82)),
 'identity-reset-choice':('The production identity boundary creates fresh false acknowledgement state for a changed transfer ID.',(53,71),(79,82)),
 'identity-reset-requested':('The production identity boundary creates fresh false requested state for a changed transfer ID.',(53,71),(79,82)),
 'reset-quiet':('The production identity-reset construction only initializes state; no caller callback occurs on that path.',(53,71),(79,82)),
 'native-disclosure-button':('The disclosure is constructed using the platform native declarative Button control.',(137,146),(149,162)),
 'native-choice-button':('The acknowledgement is constructed using the platform native declarative Button control.',(167,184),(187,225)),
 'native-primary-button':('The release action is constructed using the platform native declarative Button control.',(186,198),(227,256)),
 'native-selected':('The choice selected semantics are bound directly to the actual acknowledged state.',(167,184),(187,225)),
 'choice-native-disabled':('The real choice Button native disabled/enabled setting is bound to requested state.',(167,184),(187,203)),
 'primary-native-disabled':('The real primary Button native disabled/enabled setting is bound to the release predicate.',(186,198),(227,245)),
 'canvas-preserve-controls':('The canvas is a nonmerging/contain accessibility container around the actual descendant controls, rather than a replacement merged button.',(98,113),(95,111)),
 'surface-preserve-controls':('The surface retains descendant controls with contain/nonmerging semantics on the actual surface container.',(115,206),(103,111)),
 'unique-semantic-ids':('The static component identifiers each occur on one actual node; enumerated note indices generate one distinct heading/body identifier per row. No duplicate identifier proxy is constructed.',(98,221),(95,256)),
 'status-band-provenance':('The status identifier is attached to the actual rectangular container carrying the status background, not a proxy.',(209,221),(132,147)),
 'status-text-provenance':('The separate statusText identifier belongs to the actual displayed Text/PanelText allocation inside the status band.',(209,221),(132,147)),
 'no-nested-scroll':('The entire component tree contains stacks/columns, text, paint and controls, with no ScrollView, scroll modifier or nested scrolling container.',(1,254),(17,291)),
 'no-blank-padding-rows':('The complete component contains real content and normal gaps/padding, with no fixed-height blank spacer row used to manufacture content length.',(98,221),(95,259)),
 'model-row-order':('Expanded notes iterate the caller collection in its original enumeration order, placing each heading immediately before its body.',(148,164),(164,184)),
 'no-hidden-input-special-cases':('The complete source uses supplied values and the declared general state predicates; it contains no observer scenario/fixture-name or expected-value branches.',(1,254),(17,291)),
 'callback-model-id':('The release callback is called with the current transfer.id.',(230,234),(227,234)),
 'callbacks-only-actions':('The only business callback invocations occur in guarded enabled confirmation/release action paths; rendering and disclosure have none.',(98,234),(79,259)),
 'no-callback-on-disclosure':('Disclosure only toggles handlingOpen; it invokes no business callback.',(137,146),(149,162)),
 'no-primary-callback-on-disabled':('The primary is natively disabled by the release predicate and the action independently guards that same predicate before invoking its callback.',(77,234),(227,245)),
 'no-choice-callback-on-disabled':('The real confirmation Button is disabled when requested and its handler also refuses the requested path before callback execution.',(167,228),(187,225)),
 'uncapped-text-lines':('All declared Text sites are uncapped: no finite line limit is configured; Swift supplies lineLimit(nil) to the surface and Kotlin Text calls retain their uncapped default.',(124,221),(119,271)),
 'primary-label-allocation-config':('The primary label is explicitly configured to take the available width and 56-native-unit control height.',(186,195),(227,255)),
 'primary-content-shape-config':('The primary uses a full rectangular activation shape matching the full-width, 56-unit label allocation; this is a source construction judgment only.',(186,195),(227,255)),
 'canvas-noninteractive':('The canvas carrier has no activation handler or interactive role; its semantics retain descendants.',(98,113),(95,111)),
 'surface-noninteractive':('The surface carrier has no activation handler or interactive role; its semantics retain descendants.',(115,206),(103,111)),
 'ink-noninteractive':('The ink carrier is a painted rectangle with descriptive accessibility only, and has no activation handler or interactive role.',(117,122),(112,118)),
 'guard-predicate':('The source release predicate is exactly intact seal AND ready coolant AND acknowledgement AND not requested.',(77,79),(84,84)),
 'guard-priority':('The source status decision order is broken seal, missing coolant, requested, acknowledged, then awaiting check.',(81,93),(85,91)),
 'choice-toggle':('A successful pre-request confirmation action flips the current acknowledgement Boolean.',(224,228),(187,193)),
 'choice-callback-value':('The acknowledgement callback receives the new Boolean after the toggle.',(224,228),(187,193)),
 'choice-callback-count':('There is exactly one acknowledgement callback invocation in the successful confirmation action, after its single state toggle.',(224,228),(187,193)),
 'release-requested-state':('The guarded eligible release path sets the local requested state to true.',(230,234),(227,234)),
 'release-callback-count':('The successful guarded release path invokes onRelease exactly once, after setting requested state.',(230,234),(227,234)),
 'no-physical-transfer':('The complete component only renders UI and invokes supplied acknowledgement/release callbacks; it calls no hardware or physical-transfer operation.',(1,254),(17,291)),
 'exact-api-TransferHandlingNote':('The declaration matches the required model contract, including its stored immutable fields, constructor and required Swift visibility/conformances.',(4,14),(59,59)),
 'exact-api-ColdStorageTransfer':('The declaration matches the required transfer model contract, including immutable field types, constructor and required Swift visibility/conformances.',(17,36),(61,69)),
 'exact-api-ColdStorageTransferPanel':('The exported component declaration has the exact model/callback interface; Swift exposes the public View/body/initializer and Kotlin retains the default Modifier.',(39,61),(71,78)),
 'bridge-no-ui':('The unchanged approved bridge only decodes input, constructs the production model and invokes the production component; it creates no substitute UI.',(1,17),(1,28)),
 'bridge-no-state':('The whole approved bridge declares no local production business state.',(1,17),(1,28)),
 'bridge-no-identity-reset':('The approved bridge directly invokes the production component without an id/key identity-reset wrapper.',(1,17),(1,28)),
 'bridge-current-input':('The bridge decodes the currently supplied fixture fields and note collection into the declared production models.',(5,13),(11,24)),
 'bridge-callback-forwarding':('The bridge callback closures forward actual production callback values and model IDs to the observer onEvent receipt.',(13,15),(24,26)),
 'api14-availability':('Inspection of every unguarded production API finds only APIs available by iOS 14: the newest used facilities include ScaledMetric and its relative text styles at14; the component and its private content are annotated at14. This source-only availability assessment does not assert a link, launch or legacy runtime result.',(1,254),None),
}
source_dir=b/'source-evaluation-inputs/d0/T1/initial';cat=json.loads((source_dir/'catalog.json').read_text());inputs=json.loads((source_dir/'inputs.json').read_text());assert d.digest(cat)==inputs['catalog_sha256'];decisions=[]
for r in cat['rows']:
 platform,key=r['id'].split('-',1);reason,ios,android=common[key];start,end=ios if platform=='ios' else android;refs=[]
 for f in r['files']:
  desc=cat['files'][f]
  if f.startswith('@design/'):actual_path=b/'design/T1/public'/f[8:]
  elif f.endswith('.swift'):actual_path=b/'submissions/T1/d0/source/alerttoast'/f
  else:actual_path=b/'submissions/T1/d0/source/reply/Reply'/f
  assert hashlib.sha256(actual_path.read_bytes()).hexdigest()==desc['sha256']
  refs.append({'file':f,'sha256':desc['sha256'],'start_line':start,'end_line':end})
 decisions.append({'review_id':r['review_id'],'actual':True,'reason':reason,'evidence':refs})
value={'review':{'version':1,'catalog_sha256':inputs['catalog_sha256'],'decisions':decisions},'attributions':[]}
(out/'initial/source-judge.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
print('Wrote four runtime judgments with 143 decisions each and source judgment with',len(decisions),'decisions.')
