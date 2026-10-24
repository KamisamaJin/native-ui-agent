from pathlib import Path
import json,hashlib
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=B/'judgments/d0/one/T2'
cat=json.loads((B/'source-evaluation-inputs/d0/T2/initial/catalog.json').read_text());inp=json.loads((B/'source-evaluation-inputs/d0/T2/initial/inputs.json').read_text())
# Each item below is an independent reading of the exact proposition and declared original file.
sw={
'production-component':(39,58,'The public View and its initializer/body are implemented in the declared production Swift file; body constructs its private production content.'),
'caller-driven-rendering':(60,172,'The content receives the supplied tour, renders tour.title and tour.language/downloadSizeMB and enumerates tour.chapters; status derives from the supplied model and local state.'),
'disclosure-production-state':(60,67,'The private production content owns chaptersOpen as @State initialized false.'),
'choice-production-state':(60,67,'The private production content owns wifiOnly as @State initialized true.'),
'requested-production-state':(60,67,'The private production content owns requested as @State initialized false.'),
'identity-reset-disclosure':(51,67,'The production public View keys its own content by tour.id; new identity recreates chaptersOpen at false.'),
'identity-reset-choice':(51,67,'The production public View keys its own content by tour.id; new identity recreates wifiOnly at true.'),
'identity-reset-requested':(51,67,'The production public View keys its own content by tour.id; new identity recreates requested at false.'),
'reset-quiet':(51,67,'Identity reset is solely production .id(tour.id) plus initial @State values; the reset path calls no caller callback.'),
'native-disclosure-button':(115,123,'Disclosure uses SwiftUI Button(action:) and the actual native button receives its identifier.'),
'native-choice-button':(174,195,'Choice uses SwiftUI Button(action:) and the actual native button receives its identifier.'),
'native-primary-button':(197,215,'Primary uses SwiftUI Button(action:) and the actual native button receives its identifier.'),
'native-selected':(190,194,'The choice adds native .isSelected accessibility traits conditionally from its actual wifiOnly state.'),
'choice-native-disabled':(174,195,'The choice uses .disabled(requested), as well as its action guard.'),
'primary-native-disabled':(197,215,'The primary uses .disabled(!canDownload), as well as its action guard.'),
'canvas-preserve-controls':(81,90,'Canvas uses accessibilityElement(children: .contain) around the production subtree, retaining descendant Button controls.'),
'surface-preserve-controls':(92,155,'Surface uses accessibilityElement(children: .contain), with disclosure/choice/primary real Buttons inside.'),
'unique-semantic-ids':(81,215,'Each required literal identifier occurs once on its real semantic carrier; section identifiers are generated once per enumerated caller index and kind.'),
'status-band-provenance':(157,172,'The audio.status identifier is on the containing VStack after its status.fill background and actual band allocation.'),
'status-text-provenance':(157,172,'audio.statusText is on the actual Text(status.label) child before band padding, without a fabricated proxy.'),
'no-nested-scroll':(1,262,'The complete file constructs stacks, text, rectangles and Buttons, and no ScrollView/List or other scrolling container.'),
'no-blank-padding-rows':(81,217,'The layout contains only meaningful blocks, ordinary padding and stack spacing; no fixed blank row manufactures scroll length.'),
'model-row-order':(125,142,'ForEach enumerates tour.chapters directly; each iteration renders its chapter title then body in caller array order.'),
'no-hidden-input-special-cases':(1,262,'The complete file contains no observer imports, scenario/fixture selectors, fixture IDs or expected-value branches; only general model/state logic.'),
'callback-model-id':(197,215,'The enabled guarded primary callback calls onDownload(tour.id, wifiOnly) using the current content model.'),
'callbacks-only-actions':(51,215,'The only business callback invocations are inside guarded choice and primary Button actions; initialization, rendering, disclosure and reset do not call them.'),
'no-callback-on-disclosure':(115,123,'Disclosure action only toggles chaptersOpen, with no caller callback.'),
'no-primary-callback-on-disabled':(197,215,'Primary has native disabled state and guards canDownload before its sole callback invocation.'),
'no-choice-callback-on-disabled':(174,195,'Choice has native disabled state and guards !requested before mutation/callback.'),
'uncapped-text-lines':(101,215,'No finite line cap is configured on the relevant Text nodes; the surface applies lineLimit(nil), with vertically growing Text allocations.'),
'primary-label-allocation-config':(197,215,'The primary Text label explicitly fills maxWidth infinity and then height 56 before background and content shape.'),
'primary-content-shape-config':(197,215,'Rectangle contentShape is attached after the primary label full-width/56-height allocation and its background. This is construction evidence only.'),
'canvas-noninteractive':(81,90,'The canvas is a noninteractive VStack with contain semantics and identifier; it declares no activation action or interactive role.'),
'surface-noninteractive':(92,155,'The surface is a noninteractive VStack semantic container; only its descendant Buttons activate.'),
'ink-noninteractive':(94,99,'The ink is a labelled Rectangle with identifier and no button trait, gesture or action.'),
'guard-predicate':(69,72,'canDownload is exactly the conjunction of sufficient storage, not metered-plus-wifiOnly, and not requested.'),
'guard-priority':(74,79,'The status branches test insufficient storage, requested, metered plus wifiOnly, then ready in exactly that order.'),
'choice-toggle':(174,179,'The successful choice action guards !requested then invokes wifiOnly.toggle().'),
'choice-callback-value':(174,179,'The callback is passed wifiOnly after toggle, so forwards the resulting preference.'),
'choice-callback-count':(174,179,'The successful choice action has exactly one onWifiOnlyChange invocation and no loop or second branch.'),
'download-requested-state':(197,202,'After the eligibility guard, primary sets requested = true.'),
'download-callback-count':(197,202,'The successful primary action contains one onDownload call after setting requested, with no loop or second call.'),
'callback-preference':(197,202,'Primary forwards the current wifiOnly value directly to onDownload.'),
'no-disk-measurement':(1,262,'Whole Int values are supplied in the model and compared directly; the complete file imports only SwiftUI and makes no disk-capacity query.'),
'no-audio-fetch':(1,262,'The complete component only records local requested state and emits a callback; no networking, file transfer, audio fetch or download exists.'),
'exact-api-AudioTourChapter':(4,14,'The exact public stored String values, Equatable/Identifiable conformances and public initializer contract are present.'),
'exact-api-OfflineAudioTour':(17,36,'All exact public stored values/types, Equatable/Identifiable conformances and the public initializer parameter contract are present.'),
'exact-api-OfflineAudioTourPanel':(39,58,'The public View, exact public initializer with escaping callbacks, and public body getter match the declaration contract.'),
'api14-availability':(1,262,'The full production file uses SwiftUI APIs available by iOS 14: foundational Views/controls/modifiers, @State, ForEach, .id, custom ButtonStyle and accessibility traits. It introduces no unguarded post-iOS-14 API. This is source availability review, not older-OS launch or packaging proof.')}
kt={
'production-component':(51,70,'The declared models and real @Composable production function are defined in the exact Kotlin production file and package.'),
'caller-driven-rendering':(65,175,'The function consumes the supplied tour, renders title/language/downloadSizeMB and caller chapters, with general state/model-derived status.'),
'disclosure-production-state':(71,74,'Production owns chaptersOpen in remember(tour.id) initialized false.'),
'choice-production-state':(71,74,'Production owns wifiOnly in remember(tour.id) initialized true.'),
'requested-production-state':(71,74,'Production owns requested in remember(tour.id) initialized false.'),
'identity-reset-disclosure':(71,74,'remember is keyed by tour.id, so a changed caller identity reinitializes disclosure false.'),
'identity-reset-choice':(71,74,'remember is keyed by tour.id, so a changed caller identity reinitializes wifiOnly true.'),
'identity-reset-requested':(71,74,'remember is keyed by tour.id, so a changed caller identity reinitializes requested false.'),
'reset-quiet':(71,83,'The identity-keyed state initializers and derived guards contain no caller callback invocation.'),
'native-disclosure-button':(142,155,'Disclosure uses Material3 TextButton, a real Compose native Button semantic control.'),
'native-choice-button':(181,210,'Choice uses Material3 TextButton and puts its actual identifier and selected semantics on that control.'),
'native-primary-button':(212,245,'Primary uses Material3 Button, with enabled and identifier on the real control.'),
'native-selected':(188,191,'Choice sets semantics selected = wifiOnly directly from its current local state.'),
'choice-native-disabled':(181,191,'Choice sets the actual TextButton enabled argument to !requested.'),
'primary-native-disabled':(212,224,'Primary sets the actual Button enabled argument to canDownload.'),
'canvas-preserve-controls':(85,101,'Canvas uses semantics(mergeDescendants = false), with independently tagged controls in the contained production layout.'),
'surface-preserve-controls':(93,101,'Surface uses semantics(mergeDescendants = false), preserving independently tagged descendant controls.'),
'unique-semantic-ids':(85,245,'Each declared literal testTag is attached once to its real node. Section heading/body tags use each caller index once in the single forEachIndexed.'),
'status-band-provenance':(124,140,'audio.status tags the actual painted Box bearing status.fill before internal padding; there is no proxy allocation.'),
'status-text-provenance':(134,139,'audio.statusText tags the actual Text(status.label) child allocation.'),
'no-nested-scroll':(1,267,'The complete file constructs Columns, Box/Row, Text and native Buttons; no scrolling container or scroll modifier is introduced.'),
'no-blank-padding-rows':(85,248,'The only Spacer is the 8dp horizontal space between checkbox and label; layout has no blank fixed-height rows manufacturing scrolling.'),
'model-row-order':(157,179,'forEachIndexed directly enumerates tour.chapters, rendering each chapter title then body in caller order.'),
'no-hidden-input-special-cases':(1,267,'The complete file contains no observer/scenario/fixture-specific selectors, IDs or expected-result comparisons; only general supplied-model/state logic.'),
'callback-model-id':(212,222,'The guarded actual primary action directly passes current tour.id to onDownload.'),
'callbacks-only-actions':(65,248,'The only caller callback invocations occur in enabled choice/primary onClick lambdas, each with its own guard; render/reset/disclosure invoke none.'),
'no-callback-on-disclosure':(142,155,'Disclosure onClick only flips chaptersOpen; no caller callback occurs.'),
'no-primary-callback-on-disabled':(212,224,'The real Button enabled gate and repeated eligibility check protect the sole download callback.'),
'no-choice-callback-on-disabled':(181,191,'The native enabled gate and !requested guard protect the sole choice callback.'),
'uncapped-text-lines':(110,243,'No Text node in any required role sets maxLines to a finite value; all retain Compose Text uncapped defaults.'),
'primary-label-allocation-config':(212,245,'The real Button fills width at height 56dp; its label Box fills max size and Text fills width, constructing the full declared allocation.'),
'primary-content-shape-config':(212,245,'The Button uses RectangleShape on its full-width/56dp allocation, with no border/elevation and zero contentPadding; its label Box fills that same rectangle. This does not prove physical hit bounds.'),
'canvas-noninteractive':(85,101,'Canvas is a tagged nonmerging Column with no clickable modifier, activation action or interactive role.'),
'surface-noninteractive':(93,101,'Surface is a tagged nonmerging Column with no activation action or interactive role.'),
'ink-noninteractive':(102,108,'Ink is a solid tagged Box with only a contentDescription; no click action or interactive role is set.'),
'guard-predicate':(76,77,'canDownload exactly compares sufficient storage, rejects metered-plus-wifiOnly and rejects requested.'),
'guard-priority':(78,83,'The when branches follow insufficient storage, requested, metered-plus-wifiOnly, then ready.'),
'choice-toggle':(181,187,'Under !requested the successful choice action sets wifiOnly = !wifiOnly.'),
'choice-callback-value':(181,187,'onWifiOnlyChange receives wifiOnly after it has been inverted.'),
'choice-callback-count':(181,187,'The successful guarded choice action invokes onWifiOnlyChange exactly once, with no loop or extra call.'),
'download-requested-state':(212,222,'The successful eligible primary branch changes requested to true before its callback.'),
'download-callback-count':(212,222,'The eligible primary branch contains exactly one onDownload invocation; repeated calls are guarded by requested.'),
'callback-preference':(212,222,'onDownload is passed the current wifiOnly local Boolean directly.'),
'no-disk-measurement':(1,267,'The complete file takes Int availableMB/downloadSizeMB from the caller and compares them; it calls no disk-capacity API.'),
'no-audio-fetch':(1,267,'The complete component records state and invokes a callback only; no audio/network/file fetch or transfer exists.'),
'exact-api-AudioTourChapter':(51,51,'The data class has exactly the declared String val properties and constructor parameter names/order.'),
'exact-api-OfflineAudioTour':(53,61,'The data class has the declared seven val model properties, exact types and parameter order.'),
'exact-api-OfflineAudioTourPanel':(64,70,'The exact @Composable function parameters/callback types and modifier: Modifier = Modifier default are present.')}
bridge={
'bridge-no-ui':('The bridge only decodes the caller model and constructs the declared production component; it builds no substitute UI.',(4,17),(9,28)),
'bridge-no-state':('The complete thin bridge declares no local component business state or persistent local mutable preference.',(1,17),(1,28)),
'bridge-no-identity-reset':('The bridge calls the production component directly and adds no .id or key identity-reset wrapper.',(4,17),(9,28)),
'bridge-current-input':('The current fixture argument is decoded field-for-field into production models, including chapter order.',(5,12),(11,23)),
'bridge-callback-forwarding':('The actual production callbacks are forwarded to onEvent using supplied callback ID/preference values; no expected callbacks are fabricated.',(13,15),(24,26))}
dec=[]
for row in cat['rows']:
 plat,key=row['id'].split('-',1);file=row['files'][0]
 if key in bridge:
  reason,ir,ar=bridge[key];start,end=ir if plat=='ios' else ar
 else:start,end,reason=(sw if plat=='ios' else kt)[key]
 actualpath=B/'design/T2/public'/file[8:] if file.startswith('@design/') else B/'submissions/T2/d0/source'/file
 actualsha=hashlib.sha256(actualpath.read_bytes()).hexdigest()
 assert actualsha==cat['files'][file]['sha256'],file
 dec.append({'review_id':row['review_id'],'actual':True,'reason':reason,'evidence':[{'file':file,'sha256':actualsha,'start_line':start,'end_line':end}]})
value={'review':{'version':1,'catalog_sha256':inp['catalog_sha256'],'decisions':dec},'attributions':[]}
(O/'initial/source-judge.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
print('Wrote',len(dec),'source decisions with exact original SHA and proposition-specific line ranges.')
