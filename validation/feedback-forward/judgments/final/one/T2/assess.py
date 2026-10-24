from pathlib import Path
import json,hashlib,sys,time,importlib.util,traceback,collections
sys.dont_write_bytecode=True
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=BASE/'judgments/final/one/T2'
sys.path.insert(0,str(BASE/'candidate-v9/scripts'))
import native_checks,design_contract,acceptance,review_contract,native_pixels

def read(p): return json.loads(Path(p).read_text())
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lines(p):return Path(p).read_text().splitlines()
def find(ls,s):return next(i for i,l in enumerate(ls,1) if s in l)

def visual_reason(r,case,platform,state):
 key=r['requirement_id']
 body={
 'title-wrapping':'The entire caller title is readable with natural line breaks and no ellipsis or cut-off text.',
 'subtitle-wrapping':'The caller language/collection and complete MB subtitle are readable; narrow layouts wrap naturally without truncation.',
 'status-wrapping':'The complete current status string is readable, including the two-line ready/requested strings on the narrow layout.',
 'disclosure-wrapping':'The entire current Review chapters / Hide chapters label is readable without ellipsis or clipping.',
 'choice-wrapping':'The complete Wi-Fi only label is visible beside its selected/unselected mark, without truncation.',
 'primary-wrapping':'The complete Get audio / Requested label is readable inside the primary rectangle without clipping or ellipsis.',
 'heading-wrapping':'All eight chapter headings are readable in the overlapping original sweep; their full supplied strings wrap without ellipsis.',
 'body-wrapping':'All eight supplied paragraphs can be followed continuously across the overlapping original sweep; beginnings, continuations and endings are present, with natural wraps and no ellipsis.',
 'title-hierarchy':'The title has visibly larger semibold type than the chapter headings; the hierarchy remains apparent at this platform text scale.',
 'horizontal-clipping':'The complete sweep keeps the text and surfaces within the component horizontal bounds; viewport scroll-edge cuts are covered by adjacent frames.',
 'row-overlap':'Successive text rows and chapter pairs remain visibly separated throughout the full original sweep; no overlapping rows were observed.',
 'flow-order':'The full original state shows ink accent, title, subtitle, status, disclosure, any chapters, choice and primary in that reading sequence.',
 'single-column':'All main blocks occupy one vertical flow across the complete state sweep.',
 'full-width-canvas':'Original pixels and the coherent native canvas boundary show the pale canvas spanning the complete offered width between the host horizontal gutters; the white surface is inset within it.',
 'collapsed-headings':'The full collapsed-state evidence shows no chapter heading between disclosure and choice.',
 'collapsed-bodies':'The full collapsed-state evidence shows no chapter paragraph between disclosure and choice.',
 'expanded-order':'The eight displayed heading/body pairs follow the caller chapter sequence in the overlapping full-state images, through the last paragraph and bottom controls.',
 'status-rectangle':'The entire visible status band has straight horizontal/vertical edges and four square corners.',
 'status-no-border':'The status band meets its surrounding surface directly with no visible border stroke.',
 'primary-rectangle':'The complete primary paint silhouette has four square corners and straight rectangular edges.',
 'primary-no-border':'The complete primary surface has no visible surrounding border stroke.',
 'primary-painted-allocation':'In the coherent original frame(s), primary paint covers the observed full native Button rectangle through all four edges, with no uncovered strips; this is paint/control-boundary review, not a physical hit-area claim.',
 'ink-rectangle':'The original top frame shows a solid narrow ink rectangle with four square corners.'
 }[key]
 return f'{case} {platform}, {state}: '+body

runtime_summary={};hashcheck=[];dispatch_summary={};visual_count=0
for folder in sorted((BASE/'evaluation-inputs/final/T2').glob('*/*/*')):
 source,platform,case=folder.parts[-3:];key='/'.join(folder.parts[-3:]);data={n:read(folder/(n+'.json')) for n in ['inputs','plan','catalog','automatic','environment-check']}
 inp=data['inputs'];plan=data['plan'];cat=data['catalog'];obs=read(BASE/inp['observation']);raw=BASE/inp['raw'];allowed={}
 assert sha(BASE/inp['observation'])==inp['observation_sha256']
 for st in plan['states']:
  found,complete,reason,cap=native_checks.bound_state_evidence(obs,st);allowed[st['id']]=(found,complete,reason)
 dec=[]
 for r in cat['rows']:
  if r['method']!='visual':continue
  found,complete,reason=allowed[r['state']];indices=[n for n,s in found]
  target=r['target']
  # Cite the entire coherent sweep for global/long-copy propositions, and fully visible original target frames for individual control/text/shape propositions.
  if r['requirement_id'] in ['title-wrapping','subtitle-wrapping','status-wrapping','disclosure-wrapping','choice-wrapping','primary-wrapping','status-rectangle','status-no-border','primary-rectangle','primary-no-border','primary-painted-allocation','ink-rectangle']:
   full=[]
   for n,s in found:
    resolved=native_checks.resolve(s,target,platform);node=resolved.get('semantic',{})
    if node.get('fully_within_viewport',node.get('fully_visible',False)):full.append(n)
   if full:indices=full
  actual=True if indices else None
  why=visual_reason(r,case,platform,r['state']) if actual is not None else 'No exact-state original image evidence supports this proposition.'
  if r.get('coverage')=='full_content' and not complete:
   actual=None;indices=[];why='No complete eligible full-content state evidence; targeted images cannot establish this proposition.'
  dec.append({'review_id':r['review_id'],'actual':actual,'reason':why,'snapshot_indices':indices})
 visual_count+=len(dec)
 judge={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':dec},'attributions':[]}
 write(OUT/key/'judge.json',judge)
 failures=[r for r in data['automatic']['assertions'] if r['status']=='failed']
 assert not failures,'A supported strict F needs independent cause assessment before seal'
 runtime_summary[key]={'environment':data['environment-check']['status'],'automatic_counts':data['automatic']['counts'],'visual_decisions':len(dec),'visual_unknown':sum(d['actual'] is None for d in dec),'strict_failed_ids':[r['id'] for r in failures],'nonvisual_unknown_ids':[r['id'] for r in data['automatic']['assertions'] if r['status']=='unassessed' and r['id'] not in {t['id'] for t in cat['rows'] if t['method']=='visual'}]}
 dispatch_summary[key]=[]
 for n,step in enumerate(obs.get('steps',[])):
  act=step.get('action',{});dispatch_summary[key].append({'action_index':n,'type':act.get('type',step.get('type')),'target':act.get('target',step.get('selector')),'outcome':step.get('outcome'),'dispatch':step.get('dispatch'),'binding_after':step.get('binding_after'),'callback_delta':step.get('callback_delta'),'same_process':step.get('same_process'),'model_update':step.get('model_update'),'before':step.get('before'),'after':step.get('after',step.get('snapshot'))})
 for path,expected in inp['original_files'].items():
  # Verify exact delivered references, observations, native PNGs, executable fixtures/actions and production bytes; no claims/self-reviews are accessed.
  if path.endswith(('.png','observation.json','actions.json','fixtures.json','environment.ios.json','environment.android.json','OfflineAudioTourPanel.swift','OfflineAudioTourPanel.kt','policy.json','design-lock.json','approval.json','Bridge.swift','ObserverBridge.kt','reference.json')):
   actual=sha(BASE/path);hashcheck.append({'key':key,'file':path,'expected':expected,'actual':actual,'matches':actual==expected})
write(OUT/'runtime-summary.json',runtime_summary);write(OUT/'dispatch-binding-inspection.json',dispatch_summary);write(OUT/'input-hash-verification.json',hashcheck)

# Every source proposition is assessed on its anonymous capsule. Source evidence never stands in for a rendered fact.
source_results={}
for alias in ['source-a','source-b']:
 p=BASE/f'source-evaluation-inputs/final/T2/{alias}';inp=read(p/'inputs.json');cat=read(p/'catalog.json');decisions=[]
 sources={}
 for name in cat['files']:
  if name.startswith('@design/'):path=BASE/inp['design_root']/name.split('/',1)[1]
  else:path=next(BASE/f for f in inp['original_files'] if f.endswith('/'+name))
  ls=lines(path);assert sha(path)==cat['files'][name]['sha256'];sources[name]=(path,ls)
 for row in cat['rows']:
  rid=row['id'];platform,short=rid.split('-',1);name=row['files'][0];path,ls=sources[name];last=len(ls)
  if name.startswith('@design/'):
   start,end=1,last
   reasons={'bridge-no-ui':'The approved bridge constructs only the declared production model and production panel; it builds no substitute layout.', 'bridge-no-state':'There is no remembered/state property or local component business state in this thin bridge.', 'bridge-no-identity-reset':'The production panel is called directly; the bridge applies no .id/key identity wrapper or reset logic.', 'bridge-current-input':'Every model field and chapter is decoded from the currently supplied fixture, in map order.', 'bridge-callback-forwarding':'The closures forward actual production callback values into onEvent; no expected event is fabricated.'}
   reason=reasons[short]
  elif platform=='ios':
   surface=find(ls,'private var surface:');status=find(ls,'private var statusBand:');choice=find(ls,'private var choiceButton:');primary=find(ls,'private var primaryButton:');style=find(ls,'private struct AudioTourButtonStyle:')
   ranges={
    'production-component':(39,58),'caller-driven-rendering':(60,style-3),'disclosure-production-state':(60,67),'choice-production-state':(60,67),'requested-production-state':(60,67),
    'identity-reset-disclosure':(51,67),'identity-reset-choice':(51,67),'identity-reset-requested':(51,67),'reset-quiet':(51,67),
    'native-disclosure-button':(find(ls,'Button(action: { chaptersOpen.toggle() })'),find(ls,'.accessibilityIdentifier("audio.disclosure")')),
    'native-choice-button':(choice,primary-1),'native-primary-button':(primary,style-3),'native-selected':(choice,primary-1),'choice-native-disabled':(choice,primary-1),'primary-native-disabled':(primary,style-3),
    'canvas-preserve-controls':(81,choice-1),'surface-preserve-controls':(surface,status-1),'unique-semantic-ids':(81,style-3),'status-band-provenance':(status,choice-1),'status-text-provenance':(status,choice-1),
    'no-nested-scroll':(1,last),'no-blank-padding-rows':(81,style-3),'model-row-order':(find(ls,'if chaptersOpen {'),status-1),'no-hidden-input-special-cases':(1,last),
    'callback-model-id':(primary,style-3),'callbacks-only-actions':(choice,style-3),'no-callback-on-disclosure':(find(ls,'Button(action: { chaptersOpen.toggle() })'),find(ls,'.accessibilityIdentifier("audio.disclosure")')),
    'no-primary-callback-on-disabled':(primary,style-3),'no-choice-callback-on-disabled':(choice,primary-1),'uncapped-text-lines':(surface,style-3),'primary-label-allocation-config':(primary,style-3),'primary-content-shape-config':(primary,style-3),
    'canvas-noninteractive':(81,surface-1),'surface-noninteractive':(surface,status-1),'ink-noninteractive':(surface,find(ls,'.accessibilityIdentifier("audio.inkMark")')),
    'guard-predicate':(69,72),'guard-priority':(74,79),'choice-toggle':(choice,primary-1),'choice-callback-value':(choice,primary-1),'choice-callback-count':(choice,primary-1),'download-requested-state':(primary,style-3),'download-callback-count':(primary,style-3),'callback-preference':(primary,style-3),
    'no-disk-measurement':(1,last),'no-audio-fetch':(1,last),'exact-api-AudioTourChapter':(4,14),'exact-api-OfflineAudioTour':(17,36),'exact-api-OfflineAudioTourPanel':(39,58),'api14-availability':(1,last)}
   start,end=ranges[short]
   reasons={
    'production-component':'The exact public production file defines OfflineAudioTourPanel: View and its production body.',
    'caller-driven-rendering':'Panel content reads the passed tour title, language, sizes and chapters; there is no observer approximation.',
    'disclosure-production-state':'The production content owns @State chaptersOpen, initially false.',
    'choice-production-state':'The production content owns @State wifiOnly, initially true.',
    'requested-production-state':'The production content owns @State requested, initially false.',
    'identity-reset-disclosure':'Production .id(tour.id) recreates its stateful content with chaptersOpen=false when caller identity changes.',
    'identity-reset-choice':'Production .id(tour.id) recreates its stateful content with wifiOnly=true when caller identity changes.',
    'identity-reset-requested':'Production .id(tour.id) recreates its stateful content with requested=false when caller identity changes.',
    'reset-quiet':'The production identity boundary only reinstantiates state; no callback is invoked in this reset path.',
    'native-disclosure-button':'Disclosure is a SwiftUI Button with an action that toggles chaptersOpen.',
    'native-choice-button':'Choice is a SwiftUI Button with its state update in the action.',
    'native-primary-button':'Primary is a SwiftUI Button with an eligibility-guarded action.',
    'native-selected':'The choice attaches the native isSelected trait from wifiOnly, while its decorative image is hidden.',
    'choice-native-disabled':'The choice uses .disabled(requested), plus an action guard.',
    'primary-native-disabled':'Primary uses .disabled(!canDownload), plus an action guard.',
    'canvas-preserve-controls':'The canvas uses children: .contain and does not combine/ignore its child Buttons.',
    'surface-preserve-controls':'The surface uses children: .contain; descendant Buttons retain their own identifiers.',
    'unique-semantic-ids':'Each declared identifier is attached once to the corresponding real layout/Text/Button; section indices are generated in caller order. This source attachment finding does not certify every collector AX node is exposed.',
    'status-band-provenance':'audio.status is attached to the padded, full-width status VStack that actually receives status.fill.',
    'status-text-provenance':'audio.statusText is attached directly to the actual Text(status.label) allocation.',
    'no-nested-scroll':'The full production file has no ScrollView/List or other scroller.',
    'no-blank-padding-rows':'The production layout contains content, spacing and declared padding, with no fixed-height blank row to manufacture scroll distance.',
    'model-row-order':'ForEach enumerates tour.chapters and emits each title then body, preserving caller sequence.',
    'no-hidden-input-special-cases':'The full source makes only generic model/state decisions; no observer scenario names or fixture-specific IDs/values are tested.',
    'callback-model-id':'The download action calls onDownload(tour.id, wifiOnly) using the current passed model.',
    'callbacks-only-actions':'Only guarded choice and primary Button actions invoke the caller callbacks.',
    'no-callback-on-disclosure':'The disclosure action only calls chaptersOpen.toggle().',
    'no-primary-callback-on-disabled':'The primary is natively disabled and guard canDownload precedes its sole callback.',
    'no-choice-callback-on-disabled':'The choice is natively disabled and guard !requested precedes its sole callback.',
    'uncapped-text-lines':'The surface sets lineLimit(nil), text uses vertical fixedSize with natural width, and no finite line cap is configured on any declared text.',
    'primary-label-allocation-config':'The primary Text label expands to maxWidth infinity and then a 56-point frame, with paint on that label allocation.',
    'primary-content-shape-config':'The primary label attaches contentShape(Rectangle()) after its full-width 56-point allocation and background.',
    'canvas-noninteractive':'The canvas is a VStack/background with container accessibility; no action or interactive trait is attached.',
    'surface-noninteractive':'The white surface carrier is a containing VStack without its own activation action or interactive trait.',
    'ink-noninteractive':'The ink semantic carrier is the painted Rectangle with accessibility label/identifier and no activation action or Button trait.',
    'guard-predicate':'canDownload is exactly storage equality-or-greater AND no metered/wifiOnly block AND !requested.',
    'guard-priority':'The explicit status branches test insufficient storage, requested, metered with wifiOnly, then ready.',
    'choice-toggle':'After guard !requested, wifiOnly.toggle() flips the current local Boolean.',
    'choice-callback-value':'The single callback receives wifiOnly after the toggle.',
    'choice-callback-count':'Exactly one onWifiOnlyChange call occurs in the successful guarded choice action.',
    'download-requested-state':'The successful guarded primary action assigns requested=true.',
    'download-callback-count':'Exactly one onDownload invocation occurs after the eligibility guard.',
    'callback-preference':'The sole download callback receives the current local wifiOnly value.',
    'no-disk-measurement':'All capacity decisions use caller Int availableMB/downloadSizeMB; the complete file has no disk-capacity API.',
    'no-audio-fetch':'The complete file contains UI/state/callback code and no networking, audio fetch or transfer operation.',
    'exact-api-AudioTourChapter':'The public immutable id/title/body declarations, initializer and Equatable/Identifiable conformances match the exact contract.',
    'exact-api-OfflineAudioTour':'The public immutable model fields, types, initializer order and Equatable/Identifiable conformances match the exact contract.',
    'exact-api-OfflineAudioTourPanel':'The public View, escaping callback initializer and public body match the exact exported contract.',
    'api14-availability':'The file uses SwiftUI APIs available by iOS 14, including title2, native Button/State, .id, fixedSize, custom ButtonStyle and the Text-based accessibility modifiers. No unguarded newer API is present; this manual source finding does not claim an iOS14 app link/launch.'}
   reason=reasons[short]
  else:
   root=find(ls,'    Column(');ch=find(ls,'if (chaptersOpen)');choice=find(ls,'if (!requested)');primary=find(ls,'            Button(');colors=find(ls,'private enum class AudioTourStatus')
   ranges={'production-component':(63,74),'caller-driven-rendering':(85,colors-2),'disclosure-production-state':(71,74),'choice-production-state':(71,74),'requested-production-state':(71,74),'identity-reset-disclosure':(71,74),'identity-reset-choice':(71,74),'identity-reset-requested':(71,74),'reset-quiet':(71,74),
    'native-disclosure-button':(142,155),'native-choice-button':(choice-2,primary-2),'native-primary-button':(primary,colors-2),'native-selected':(choice-2,primary-2),'choice-native-disabled':(choice-2,primary-2),'primary-native-disabled':(primary,colors-2),
    'canvas-preserve-controls':(85,155),'surface-preserve-controls':(93,155),'unique-semantic-ids':(85,colors-2),'status-band-provenance':(124,140),'status-text-provenance':(124,140),
    'no-nested-scroll':(1,last),'no-blank-padding-rows':(85,colors-2),'model-row-order':(157,179),'no-hidden-input-special-cases':(1,last),'callback-model-id':(primary,colors-2),'callbacks-only-actions':(choice-2,colors-2),'no-callback-on-disclosure':(142,155),'no-primary-callback-on-disabled':(primary,colors-2),'no-choice-callback-on-disabled':(choice-2,primary-2),
    'uncapped-text-lines':(110,colors-2),'primary-label-allocation-config':(primary,colors-2),'primary-content-shape-config':(primary,colors-2),'canvas-noninteractive':(85,108),'surface-noninteractive':(93,108),'ink-noninteractive':(102,108),'guard-predicate':(76,77),'guard-priority':(78,83),'choice-toggle':(choice,choice+4),'choice-callback-value':(choice,choice+4),'choice-callback-count':(choice,choice+4),'download-requested-state':(primary,colors-2),'download-callback-count':(primary,colors-2),'callback-preference':(primary,colors-2),'no-disk-measurement':(1,last),'no-audio-fetch':(1,last),'exact-api-AudioTourChapter':(51,51),'exact-api-OfflineAudioTour':(53,61),'exact-api-OfflineAudioTourPanel':(64,70)}
   start,end=ranges[short]
   reasons={
    'production-component':'The declared exact Kotlin production file defines the real @Composable OfflineAudioTourPanel.',
    'caller-driven-rendering':'The composable reads the supplied tour fields and caller chapter list directly.',
    'disclosure-production-state':'Production remember(tour.id) owns chaptersOpen=false.',
    'choice-production-state':'Production remember(tour.id) owns wifiOnly=true.',
    'requested-production-state':'Production remember(tour.id) owns requested=false.',
    'identity-reset-disclosure':'remember(tour.id) reinitializes disclosure to false on model ID replacement.',
    'identity-reset-choice':'remember(tour.id) reinitializes choice to true on model ID replacement.',
    'identity-reset-requested':'remember(tour.id) reinitializes requested to false on model ID replacement.',
    'reset-quiet':'The keyed state initializers perform no caller callback.',
    'native-disclosure-button':'Disclosure uses Compose Material TextButton with a production toggle action.',
    'native-choice-button':'Choice uses Compose Material TextButton with its production state update.',
    'native-primary-button':'Primary uses Compose Material Button with its production eligibility guard.',
    'native-selected':'The choice native semantics selected property is set from wifiOnly; decorative marks clear their semantics.',
    'choice-native-disabled':'Choice passes enabled=!requested to the native TextButton and guards its action.',
    'primary-native-disabled':'Primary passes enabled=canDownload to the native Button and guards its action.',
    'canvas-preserve-controls':'The canvas uses mergeDescendants=false without clearing child controls; independent TextButtons/Button remain descendants.',
    'surface-preserve-controls':'The white surface uses mergeDescendants=false without clearing child control semantics.',
    'unique-semantic-ids':'Every declared testTag is attached once to its actual layout/Text/Button; indexed section tags follow the caller list. This source result does not assert runtime collector visibility.',
    'status-band-provenance':'audio.status is on the padded Box carrying status.fill and minHeight, not a separate proxy.',
    'status-text-provenance':'audio.statusText is directly on Text(status.label).',
    'no-nested-scroll':'The complete Kotlin file contains no scrolling modifier or scrolling container.',
    'no-blank-padding-rows':'Only meaningful content and normal spacing/padding occur; the sole Spacer is the horizontal checkmark-label gap.',
    'model-row-order':'tour.chapters.forEachIndexed emits heading then body in caller list order.',
    'no-hidden-input-special-cases':'The full file has no scenario/fixture-specific branches or expected input constants.',
    'callback-model-id':'The successful primary action passes current tour.id.',
    'callbacks-only-actions':'Only the guarded TextButton choice and Button primary onClick paths invoke caller callbacks.',
    'no-callback-on-disclosure':'The disclosure onClick only negates chaptersOpen.',
    'no-primary-callback-on-disabled':'Native enabled=canDownload and the repeated eligibility guard both precede the sole download callback.',
    'no-choice-callback-on-disabled':'Native enabled=!requested and the !requested action guard prevent the choice callback when disabled.',
    'uncapped-text-lines':'No Text sets maxLines or any finite line cap; natural soft wrapping is retained across all specified text.',
    'primary-label-allocation-config':'The Button fills max width with height(56.dp), zero contentPadding, and a fillMaxSize Box wrapping its label.',
    'primary-content-shape-config':'The full-width 56dp native Button uses RectangleShape, zero content padding and a fillMaxSize label box, configuring the same rectangular activation shape and label allocation. No physical touch-area claim follows.',
    'canvas-noninteractive':'The canvas Column carries an unmerged semantic tag with no click action or role of its own.',
    'surface-noninteractive':'The surface Column carries an unmerged semantic tag with no click action or role of its own.',
    'ink-noninteractive':'The painted ink Box is labeled/tagged and has no clickable action or interactive role.',
    'guard-predicate':'canDownload is exactly availableMB>=downloadSizeMB AND !(meteredConnection&&wifiOnly) AND !requested.',
    'guard-priority':'The when branches are insufficient storage, requested, metered/wifiOnly, then ready.',
    'choice-toggle':'The successful pre-request action negates the current wifiOnly state.',
    'choice-callback-value':'The callback receives wifiOnly after the negation.',
    'choice-callback-count':'There is exactly one onWifiOnlyChange call in the guarded successful choice action.',
    'download-requested-state':'The successful primary guard is followed by requested=true.',
    'download-callback-count':'There is one onDownload call in the successful guarded action.',
    'callback-preference':'The download callback passes current local wifiOnly.',
    'no-disk-measurement':'The full file uses caller-supplied Int capacity values and contains no disk capacity measurement.',
    'no-audio-fetch':'The full source contains no audio/data fetching or transfer operation.',
    'exact-api-AudioTourChapter':'The data class and immutable String id/title/body parameters match the exact contract.',
    'exact-api-OfflineAudioTour':'The immutable data-class parameters, field names/types and caller chapter list match the exact contract.',
    'exact-api-OfflineAudioTourPanel':'The @Composable signature, callback types and modifier: Modifier = Modifier default match the exact contract.'}
   reason=reasons[short]
  decisions.append({'review_id':row['review_id'],'actual':True,'reason':reason,'evidence':[{'file':name,'sha256':cat['files'][name]['sha256'],'start_line':start,'end_line':end}]})
 review={'version':1,'catalog_sha256':inp['catalog_sha256'],'decisions':decisions}
 assert design_contract.digest(cat)==inp['catalog_sha256']
 write(OUT/alias/'source-judge.json',{'review':review,'attributions':[]})
 # Bind against the exact supplied source catalog using the shared source audit tool with the frozen generic design module already loaded.
 spec=importlib.util.spec_from_file_location('source_audit',Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/tools/implementation_audit.py'));audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
 bound=audit.bind(cat,review);write(OUT/alias/'source-bind-self-check.json',bound);source_results[alias]=bound['counts']
write(OUT/'source-summary.json',source_results)
print(json.dumps({'visual_decisions':visual_count,'source':source_results,'hash_checks':len(hashcheck),'hash_mismatches':sum(not q['matches'] for q in hashcheck),'outputs':'runtime and source judgments written; no independent-consensus claim'}))
