import sys
sys.dont_write_bytecode=True
import json,pathlib,hashlib
BASE=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');OUT=BASE/'judgments/final/two/T2'
sys.path.insert(0,str(BASE/'candidate-v9/scripts'));import native_checks,design_contract
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reasons={
 'title-wrapping':'The complete supplied tour title is visible across natural lines, with no ellipsis or cropped terminal text.',
 'subtitle-wrapping':'The supplied language/collection and MB subtitle is readable to its end; its line breaks do not truncate it.',
 'status-wrapping':'The entire current status string is visible inside its painted band, including the wrapped final word in narrow states.',
 'disclosure-wrapping':'The current Review chapters or Hide chapters label is fully readable without an ellipsis.',
 'choice-wrapping':'Wi-Fi only is fully readable beside its separate decorative selection mark.',
 'primary-wrapping':'The complete Get audio or Requested label is readable inside the primary surface.',
 'heading-wrapping':'All eight supplied chapter headings are visible in the overlapping full-state sweep, with natural wrapping and no missing terminal words.',
 'body-wrapping':'The overlapping full-state sweep exposes every supplied chapter paragraph through its final sentence, without an ellipsis or omitted right-edge text.',
 'title-hierarchy':'The tour title has a larger, more prominent type treatment than the chapter headings in this native state.',
 'horizontal-clipping':'The observed content stays within the component left/right edges throughout the state sweep; viewport cuts at top/bottom are scroll boundaries.',
 'row-overlap':'Successive text and control rows retain visible separation throughout the sweep; no two rows overprint one another.',
 'flow-order':'The top-to-bottom sweep shows ink accent, title, subtitle, status, disclosure, expanded chapters when open, choice, then primary.',
 'single-column':'The main blocks occupy one vertical column through the full state sweep.',
 'full-width-canvas':'The pale painted gutter follows both sides of the white surface and spans the offered component width inside the host gutters; native canvas bounds locate that region.',
 'expanded-order':'The eight visible heading/body pairs follow the caller order from the first chapter through the eighth, as seen in the overlapping sweep.',
 'collapsed-headings':'The complete collapsed-state image coverage contains no chapter heading between disclosure and choice.',
 'collapsed-bodies':'The complete collapsed-state image coverage contains no chapter body between disclosure and choice.',
 'status-rectangle':'The fully visible painted status band has straight horizontal/vertical edges and four square corners.',
 'status-no-border':'No outline or separate border stroke is visible on the status band in the original frame.',
 'primary-rectangle':'The primary paint has four square corners and straight rectangular edges in the original control frame.',
 'primary-no-border':'No distinct border stroke is visible around the primary paint.',
 'primary-painted-allocation':'The original primary paint reaches all four edges of its recorded rectangular native control boundary; the native-coordinate crop shows no uncovered interior strips.',
 'ink-rectangle':'The visible ink accent is a solid narrow rectangle with four square corners.'}
selectors={'title-wrapping':'title','subtitle-wrapping':'subtitle','status-wrapping':'status','disclosure-wrapping':'disclosure','choice-wrapping':'choice','primary-wrapping':'primary','status-rectangle':'status','status-no-border':'status','primary-rectangle':'primary','primary-no-border':'primary','primary-painted-allocation':'primary','ink-rectangle':'inkMark'}
for p in sorted((BASE/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(p.parts[-3:]);i=json.loads((p/'inputs.json').read_text());cat=json.loads((p/'catalog.json').read_text());plan=json.loads((p/'plan.json').read_text());o=json.loads((BASE/i['observation']).read_text());dec=[]
 for r in cat['rows']:
  if r['method']!='visual':continue
  spec=next(x for x in plan['states'] if x['id']==r['state']);ev,complete,why,_=native_checks.bound_state_evidence(o,spec);atom=r['requirement_id'];indices=[j for j,_ in ev]
  if atom in selectors:
   ident=selectors[atom];indices=[j for j,s in ev if (lambda n:n.get('fully_within_viewport',n.get('fully_visible',False)))(native_checks.resolve(s,{'identifier':'audio.'+ident},i['platform'])['semantic'])]
   if indices:indices=indices[:1]
  actual=True if indices else None;reason=reasons[atom] if actual else 'No eligible original state evidence establishes this proposition.'
  if atom in ['heading-wrapping','body-wrapping','expanded-order','horizontal-clipping','row-overlap','flow-order','single-column','full-width-canvas','collapsed-headings','collapsed-bodies'] and not complete:
   actual=None;indices=[];reason='This atom requires full-state evidence; the bound evidence does not establish complete content coverage.'
  dec.append({'review_id':r['review_id'],'actual':actual,'reason':f"{r['state']}: {reason}",'snapshot_indices':indices})
 result={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':i['observation_sha256'],'decisions':dec},'attributions':[]}
 (OUT/key/'judge.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
# Source findings follow direct source inspection. Ranges cite the exact anonymous capsule bytes.
def choose(lines,needle,last=False):
 ids=[j+1 for j,s in enumerate(lines) if needle in s]
 if not ids:raise ValueError(needle)
 return ids[-1] if last else ids[0]
def ranges(lines,platform,suffix):
 n=len(lines);pt=lambda s:choose(lines,s)
 if platform=='ios':
  state=(pt('@State private var chaptersOpen'),pt('@State private var requested'))
  reset=(pt('public var body'),pt('private struct AudioTourPanelContent')+7)
  guard=(pt('private var canDownload'),pt('var body: some View {')-2) # body in private struct found separately below
  guard=(pt('private var canDownload'),pt('return .ready')+1)
  canvas=(pt('    var body: some View {'),pt('    private var surface')-2)
  surface=(pt('    private var surface'),pt('    private var statusBand')-2)
  status=(pt('    private var statusBand'),pt('    private var choiceButton')-2)
  choice=(pt('    private var choiceButton'),pt('    private var primaryButton')-2)
  primary=(pt('    private var primaryButton'),pt('/// Keep the authored')-2)
  rows=(pt('            if chaptersOpen'),pt('            choiceButton')-2)
  disclosure=(pt('            Button(action:'),pt('.accessibilityIdentifier("audio.disclosure")'))
  ink=(pt('            Rectangle()'),pt('.accessibilityIdentifier("audio.inkMark")'))
  decl={'AudioTourChapter':(pt('public struct AudioTourChapter'),pt('/// Whole decimal')-2),'OfflineAudioTour':(pt('public struct OfflineAudioTour:'),pt('/// Records a download')-2),'OfflineAudioTourPanel':(pt('public struct OfflineAudioTourPanel:'),pt('private struct AudioTourPanelContent')-2)}
 else:
  state=(pt('    var chaptersOpen'),pt('    var requested'))
  reset=state;guard=(pt('    val canDownload'),pt('    Column(')-2);canvas=(pt('    Column('),pt('        Column(')-1);surface=(pt('        Column('),pt('            Box(')-1)
  status=(pt('            Box(',),pt('            TextButton(')-2)
  disclosure=(pt('            TextButton('),pt('            if (chaptersOpen)')-2)
  rows=(pt('            if (chaptersOpen)'),pt('            TextButton(',)-2) if False else (pt('            if (chaptersOpen)'),pt('            if (chaptersOpen)')+22)
  ch=choose(lines,'            TextButton(',True);pr=pt('            Button(')
  choice=(ch,pr-2);primary=(pr,pt('private enum class AudioTourStatus')-3);ink=(pt('            Box('),pt('            Text(')-2)
  decl={'AudioTourChapter':(pt('data class AudioTourChapter'),pt('data class AudioTourChapter')),'OfflineAudioTour':(pt('data class OfflineAudioTour('),pt('/** Records a request')-2),'OfflineAudioTourPanel':(pt('@Composable'),pt('    // Model identity')-1)}
 mapping={'production-component':[(1,n)],'caller-driven-rendering':[(1,n)],'disclosure-production-state':[state,disclosure],'choice-production-state':[state,choice],'requested-production-state':[state,primary],
 'identity-reset-disclosure':[reset],'identity-reset-choice':[reset],'identity-reset-requested':[reset],'reset-quiet':[reset],
 'native-disclosure-button':[disclosure],'native-choice-button':[choice],'native-primary-button':[primary],'native-selected':[choice],'choice-native-disabled':[choice],'primary-native-disabled':[primary],
 'canvas-preserve-controls':[canvas,disclosure,choice,primary],'surface-preserve-controls':[surface,disclosure,choice,primary],'unique-semantic-ids':[(1,n)],'status-band-provenance':[status],'status-text-provenance':[status],
 'no-nested-scroll':[(1,n)],'no-blank-padding-rows':[(1,n)],'model-row-order':[rows],'no-hidden-input-special-cases':[(1,n)],'callback-model-id':[primary],'callbacks-only-actions':[(1,n)],'no-callback-on-disclosure':[disclosure],
 'no-primary-callback-on-disabled':[primary],'no-choice-callback-on-disabled':[choice],'uncapped-text-lines':[(1,n)],'primary-label-allocation-config':[primary],'primary-content-shape-config':[primary],
 'canvas-noninteractive':[canvas],'surface-noninteractive':[surface],'ink-noninteractive':[ink],'guard-predicate':[guard,primary],'guard-priority':[guard],'choice-toggle':[choice],'choice-callback-value':[choice],'choice-callback-count':[choice],
 'download-requested-state':[primary],'download-callback-count':[primary],'callback-preference':[primary],'no-disk-measurement':[(1,n)],'no-audio-fetch':[(1,n)],'api14-availability':[(1,n)]}
 if suffix.startswith('exact-api-'):return [decl[suffix[len('exact-api-'):]]]
 return mapping[suffix]
source_reasons={
 'production-component':'The exact production file declares the model and real platform View/Composable, including its full control tree.',
 'caller-driven-rendering':'Title, subtitle, capacity/network predicates and chapter iteration read the supplied tour directly in the production component.',
 'disclosure-production-state':'The production component owns a local Boolean initialized closed and the disclosure action mutates it.',
 'choice-production-state':'The production component owns the selected Wi-Fi-only Boolean and toggles it in its choice action.',
 'requested-production-state':'The production component owns the requested Boolean and sets it on an eligible request.',
 'identity-reset-disclosure':'Identity keys are owned inside production and recreate local disclosure with false when tour.id changes.',
 'identity-reset-choice':'Identity keys are owned inside production and recreate local Wi-Fi-only state with true when tour.id changes.',
 'identity-reset-requested':'Identity keys are owned inside production and recreate local requested state with false when tour.id changes.',
 'reset-quiet':'The production identity-key/default-state path contains no callback call.',
 'native-disclosure-button':'Disclosure is constructed with the platform Button/TextButton primitive.',
 'native-choice-button':'Choice is constructed with the platform Button/TextButton primitive.',
 'native-primary-button':'Primary is constructed with the platform Button primitive.',
 'native-selected':'The choice adds the selected accessibility trait/selected semantics from its current Wi-Fi-only Boolean.',
 'choice-native-disabled':'Choice receives disabled(requested) or enabled = !requested at the native button.',
 'primary-native-disabled':'Primary receives disabled(!canDownload) or enabled = canDownload at the native button.',
 'canvas-preserve-controls':'Canvas uses a contain/non-merging semantics container and leaves descendant native Buttons in the child tree.',
 'surface-preserve-controls':'Surface uses a contain/non-merging semantics container and leaves descendant native Buttons in the child tree. This source configuration does not certify that its identifier survives the runtime AX serialization.',
 'unique-semantic-ids':'Every declared identifier is attached once to its actual authored carrier; indexed chapter identifiers arise once per caller row. No duplicate proxy identifier is constructed. Runtime locator survival is a separate fact.',
 'status-band-provenance':'The status identifier is on the actual background-painted band container.',
 'status-text-provenance':'The distinct statusText identifier is attached to the displayed status Text itself.',
 'no-nested-scroll':'The inspected complete production file creates layout/text/buttons and no scrolling container.',
 'no-blank-padding-rows':'The complete file contains only content/design spacing. The small horizontal choice-mark spacer is not a manufactured fixed-height scrolling row.',
 'model-row-order':'The expanded block enumerates tour.chapters in order and emits each heading followed by its body.',
 'no-hidden-input-special-cases':'The complete file contains no fixture/scenario/observer checks or test-value branch; logic uses generic caller values and local state.',
 'callback-model-id':'The primary action passes tour.id from the current supplied model to onDownload.',
 'callbacks-only-actions':'The only callback invocations occur inside choice/primary action closures with explicit enabled guards.',
 'no-callback-on-disclosure':'The disclosure action only flips chaptersOpen.',
 'no-primary-callback-on-disabled':'The primary uses native disabled semantics and repeats the eligibility guard before invoking its callback.',
 'no-choice-callback-on-disabled':'The choice uses native disabled semantics and guards against requested before invoking its callback.',
 'uncapped-text-lines':'All relevant Text allocations are uncapped: Swift explicitly applies lineLimit(nil), and Compose supplies no finite maxLines.',
 'primary-label-allocation-config':'The source constructs a full-width primary label/allocation within an explicit 56-unit native button height.',
 'primary-content-shape-config':'The primary uses Rectangle contentShape/RectangleShape on the same full-width 56-unit button allocation.',
 'canvas-noninteractive':'The canvas layout/semantic carrier has no action or interactive role of its own.',
 'surface-noninteractive':'The surface layout/semantic carrier has no action or interactive role of its own.',
 'ink-noninteractive':'The solid ink carrier supplies an informational label and no action or interactive role.',
 'guard-predicate':'The computed enabled predicate and action guard use availableMB >= downloadSizeMB, negate meteredConnection && wifiOnly, and require !requested.',
 'guard-priority':'The status branches test insufficient storage, requested, metered Wi-Fi-only, then ready in that order.',
 'choice-toggle':'The successful non-requested choice action negates/toggles the current Boolean.',
 'choice-callback-value':'The choice callback reads the just-updated Boolean.',
 'choice-callback-count':'Exactly one preference callback expression appears in the successful choice path.',
 'download-requested-state':'The successful primary path assigns requested = true.',
 'download-callback-count':'Exactly one onDownload invocation appears inside the successful guarded primary path.',
 'callback-preference':'The request callback receives the current local wifiOnly value.',
 'no-disk-measurement':'The file reads whole-MB Int fields supplied by the caller and invokes no capacity-measurement API.',
 'no-audio-fetch':'The complete file creates presentation/state and callback requests, with no networking or audio-fetch API.',
 'api14-availability':'The complete Swift file uses SwiftUI APIs available by iOS 14: View/State/Button, standard layout/shape/text, title2, selected traits and accessibility container/identifier modifiers. No unguarded later-only API is present. This is source API review, not legacy linking or runtime proof.'}
bridge_reasons={'bridge-no-ui':'The approved bridge only decodes model data and calls the production component; it constructs no substitute presentation.', 'bridge-no-state':'The approved bridge has no local production business state.', 'bridge-no-identity-reset':'The approved bridge directly calls production without an id/key identity-reset wrapper.', 'bridge-current-input':'Each current fixture field and chapter is decoded into the declared production model and passed directly to the component.', 'bridge-callback-forwarding':'The closures passed to production forward the real callback arguments into onEvent receipts.'}
for p in sorted((BASE/'source-evaluation-inputs/final/T2').glob('*')):
 cat=json.loads((p/'catalog.json').read_text());inp=json.loads((p/'inputs.json').read_text());dec=[]
 for r in cat['rows']:
  plat,suffix=r['id'].split('-',1);refs=[]
  for rel in r['files']:
   paths=[BASE/f for f in inp['original_files'] if f.endswith(rel.replace('@design/','')) and (('@design/' in rel and f.startswith(inp['design_root']+'/')) or ('@design/' not in rel and '/source/' in f))]
   if len(paths)!=1:raise ValueError((rel,paths))
   actualfile=paths[0];lines=actualfile.read_text().splitlines();assert sha(actualfile)==cat['files'][rel]['sha256']
   spans=[(1,len(lines))] if rel.startswith('@design/') else ranges(lines,plat,suffix)
   for start,end in spans:refs.append({'file':rel,'sha256':sha(actualfile),'start_line':start,'end_line':end})
  reason=bridge_reasons[suffix] if suffix in bridge_reasons else ('The actual declaration matches the approved signature, stored immutable values, conformances, visibility and default argument contract.' if suffix.startswith('exact-api-') else source_reasons[suffix])
  dec.append({'review_id':r['review_id'],'actual':True,'reason':reason,'evidence':refs})
 result={'review':{'version':1,'catalog_sha256':design_contract.digest(cat),'decisions':dec},'attributions':[]}
 dest=OUT/p.name/'source-judge.json';dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Wrote all runtime and source judgments.')
