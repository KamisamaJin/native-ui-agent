from pathlib import Path
import json,sys,hashlib,time
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=B/'judgments/d0/two/T2'
sys.path.insert(0,str(B/'candidate-v9/scripts'))
import native_checks, design_contract as design

def load(p):return json.loads(p.read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reasons={
 'title-wrapping':'The complete supplied title is visible with natural line breaks and no cropped ending or ellipsis.',
 'subtitle-wrapping':'The complete language/collection and MB subtitle is visible with natural wrapping and no ellipsis.',
 'status-wrapping':'The complete current status string is visible inside the band, wrapping where needed without an ellipsis.',
 'disclosure-wrapping':'The complete Review chapters or Hide chapters label is visible without truncation.',
 'choice-wrapping':'The complete Wi-Fi only text is readable beside the decorative choice indicator, without truncation.',
 'primary-wrapping':'The complete Get audio or Requested label is visible inside the primary surface without truncation.',
 'heading-wrapping':'All eight supplied chapter headings are visible across this original overlapping sweep; their full text wraps naturally without ellipses.',
 'body-wrapping':'All eight supplied body paragraphs, including each ending, are visible across this original overlapping sweep without ellipses or missing text.',
 'title-hierarchy':'The title has a visibly larger, heavier presentation than the expanded chapter headings.',
 'horizontal-clipping':'Across the full original sweep, all component text and painted rows remain within the horizontal component allocation; viewport scroll-edge cuts are vertical.',
 'row-overlap':'Across the original full sweep, successive title, subtitle, band, disclosure, chapter pairs, choice and primary allocations have visible separation and no row collision.',
 'flow-order':'The original sweep shows ink accent, title, subtitle, status, disclosure, expanded chapters when open, choice and primary in the stated reading order.',
 'single-column':'The original sweep shows the component blocks in one vertical column.',
 'full-width-canvas':'The pale canvas and its observed native allocation span the width offered within the host gutters; the white inset surface is narrower inside it.',
 'collapsed-headings':'The full closed component is visible and contains no chapter heading.',
 'collapsed-bodies':'The full closed component is visible and contains no chapter paragraph.',
 'expanded-order':'Reading the complete overlapping original sweep shows all eight supplied heading/body pairs in their caller order.',
 'status-rectangle':'The whole visible status band has straight horizontal/vertical edges and four square corners.',
 'status-no-border':'No border stroke is visible around the fully visible status band.',
 'primary-rectangle':'The whole visible primary painted surface has straight edges and four square corners.',
 'primary-no-border':'No border stroke is visible around the primary painted surface.',
 'primary-painted-allocation':'The original primary paint reaches all four sides of the co-located observed native control rectangle, with no visible uncovered strip.',
 'ink-rectangle':'The fully visible solid ink accent has four square corners and straight rectangular sides.'}
targets={'title':'audio.title','subtitle':'audio.subtitle','status':'audio.status','disclosure':'audio.disclosure','choice':'audio.choice','primary':'audio.primary','ink':'audio.inkMark'}
coverage=[]
for platform in ['android','ios']:
 for case in ['P1','P2']:
  src=B/'evaluation-inputs/d0/T2/initial'/platform/case;inp=load(src/'inputs.json');plan=load(src/'plan.json');cat=load(src/'catalog.json');auto=load(src/'automatic.json');env=load(src/'environment-check.json');obs=load(B/inp['observation']);assert sha(B/inp['observation'])==inp['observation_sha256']
  eligible={s['id']:native_checks.bound_state_evidence(obs,s) for s in plan['states']};decisions=[]
  for row in cat['rows']:
   if row['method']!='visual':continue
   sid=row['state'];atom=row['id'].split('/',1)[1];found,complete,why,capture=eligible[sid];indices=[i for i,_ in found];actual=True;reason=reasons[atom]
   prefix=atom.split('-',1)[0]
   if prefix in targets and atom not in ['title-hierarchy']:
    full=[]
    for i,snap in found:
     r=native_checks.resolve(snap,{'identifier':targets[prefix]},platform);node=r.get('control' if prefix=='primary' else 'semantic',{})
     if node.get('fully_within_viewport',node.get('fully_visible',False)):full.append(i)
    indices=full
   if not indices:
    actual=None;indices=[];reason='The exact state-eligible original frames do not show the complete target allocation. Source configuration and other states cannot establish this visual proposition.'
   decisions.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
  attrs=[]
  for row in auto['assertions']:
   if row['status']!='failed':continue
   assert platform=='android' and row['id'].endswith('/choice-label')
   sid=row['state'];found=eligible[sid][0];indices=[]
   for i,snap in found:
    r=native_checks.resolve(snap,{'identifier':'audio.choice'},platform)
    if r.get('semantic',{}).get('fully_visible') and r['facts'].get('label')=='✓, Wi-Fi only':indices.append(i)
   assert indices
   attrs.append({'id':row['id'],'cause':'observation','reason':'The original collector records “✓, Wi-Fi only” by synthesizing a label from unmerged descendant Text (NativeObserverTest.kt raw() at line 89 and label() at line 137), rather than an Android accessibility-service label. The production choice explicitly clears semantics on the decorative mark Box (OfflineAudioTourPanel.kt lines 200–205) and exposes selected separately at lines 189–191. The visible Wi-Fi only text is complete. Preserve the strict native F; this unmerged-label construction supports an observation cause and does not establish a product accessibility-label defect or a TalkBack pass.','snapshot_indices':indices})
  dest=OUT/'initial'/platform/case
  save(dest/'judge.json',{'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':decisions},'attributions':attrs})
  coverage.append({'source':'initial','platform':platform,'case':case,'observation':inp['observation'],'observation_sha256':inp['observation_sha256'],'environment_status':env['status'],'visual_decisions':len(decisions),'unknown_visuals':[r['review_id'] for r in decisions if r['actual'] is None],'eligible_states':{sid:{'indices':[i for i,_ in v[0]],'complete':v[1],'reason':v[2],'binding':(v[3] or {}).get('binding')} for sid,v in eligible.items()},'steps':[{ 'index':i,'type':s.get('action',s).get('type'),'outcome':s.get('outcome'),'dispatch':s.get('dispatch'),'callback_delta':s.get('callback_delta'),'binding_after':s.get('binding_after')} for i,s in enumerate(obs['steps'])]})
save(OUT/'coverage.json',coverage)
# Source judgments are based on the complete original files read with numbered lines.
source_dir=B/'source-evaluation-inputs/d0/T2/initial';cat=load(source_dir/'catalog.json');inp=load(source_dir/'inputs.json');assert design.digest(cat)==inp['catalog_sha256']
paths={
 'Sources/AlertToast/OfflineAudioTourPanel.swift':B/'submissions/T2/d0/source/alerttoast/Sources/AlertToast/OfflineAudioTourPanel.swift',
 'app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt':B/'submissions/T2/d0/source/reply/Reply/app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt',
 '@design/Bridge.swift':B/'design/T2/public/Bridge.swift',
 '@design/ObserverBridge.kt':B/'design/T2/public/ObserverBridge.kt'}
for rel,p in paths.items():assert sha(p)==cat['files'][rel]['sha256']
# Each tuple is (Swift line ranges, Kotlin line ranges, source-only explanation).
m={
 'production-component':([(39,58),(60,217)],[(64,248)],'The declared production file defines the exported native component and its complete rendering implementation.'),
 'caller-driven-rendering':([(39,56),(101,140)],[(65,83),(110,175)],'The component stores/receives the supplied model and reads title, language, size and chapter values directly from it.'),
 'disclosure-production-state':([(60,67),(115,125)],[(71,74),(142,157)],'The production component owns the local disclosure Boolean and its action toggles that state.'),
 'choice-production-state':([(60,67),(174,194)],[(71,74),(181,209)],'The production component owns the local Wi-Fi-only Boolean and renders its selection.'),
 'requested-production-state':([(60,78),(197,215)],[(71,83),(212,244)],'The requested Boolean belongs to the production component and is changed in its primary action.'),
 'identity-reset-disclosure':([(51,67)],[(71,74)],'Identity is keyed by the current model ID and initializes disclosure closed on replacement.'),
 'identity-reset-choice':([(51,67)],[(71,74)],'Identity is keyed by the current model ID and initializes Wi-Fi only true on replacement.'),
 'identity-reset-requested':([(51,67)],[(71,74)],'Identity is keyed by the current model ID and initializes requested false on replacement.'),
 'reset-quiet':([(51,67)],[(71,74)],'The identity/reset construction only creates local initial state and invokes no business callback.'),
 'native-disclosure-button':([(115,123)],[(142,155)],'Disclosure is authored with the platform native Button/TextButton control.'),
 'native-choice-button':([(174,194)],[(181,210)],'Choice is authored with the platform native Button/TextButton control.'),
 'native-primary-button':([(197,215)],[(212,245)],'Primary is authored with the platform native Button control.'),
 'native-selected':([(191,194)],[(188,191)],'The actual local preference feeds native selected accessibility semantics.'),
 'choice-native-disabled':([(174,194)],[(181,191)],'Choice uses the native disabled/enabled control property derived from requested.'),
 'primary-native-disabled':([(197,215)],[(212,224)],'Primary uses the native disabled/enabled control property derived from the download predicate.'),
 'canvas-preserve-controls':([(81,90)],[(85,99)],'The canvas declares a containing/nonmerging semantic container, preserving descendant controls in source construction.'),
 'surface-preserve-controls':([(92,155)],[(93,100),(142,245)],'The surface declares a containing/nonmerging semantic container around the separately authored controls.'),
 'unique-semantic-ids':([(81,215)],[(85,245)],'Each literal identifier is attached once to its real carrier; enumerated chapter IDs are generated once per row index.'),
 'status-band-provenance':([(157,171)],[(124,139)],'The status identifier is on the band allocation that receives the background, separate from its child Text.'),
 'status-text-provenance':([(157,171)],[(124,139)],'The statusText identifier is on the displayed native Text, with no geometry proxy.'),
 'no-nested-scroll':([(1,262)],[(11,267)],'Inspection of the whole component finds no scrolling container; rendering is a vertical stack/column.'),
 'no-blank-padding-rows':([(81,217)],[(85,248)],'The entire layout contains real content and ordinary gutters/gaps; no fixed blank row manufactures scroll length.'),
 'model-row-order':([(125,141)],[(157,178)],'Chapter views are generated by enumerating the supplied caller chapters in their list order.'),
 'no-hidden-input-special-cases':([(1,262)],[(11,267)],'Whole-file inspection finds no observer scenario, fixture value or expected-output special case. ID is used for the declared identity reset and callback.'),
 'callback-model-id':([(197,202)],[(212,220)],'The download action forwards the current supplied tour.id.'),
 'callbacks-only-actions':([(51,217)],[(65,248)],'Business callback invocations occur only inside enabled button actions with current-state guards.'),
 'no-callback-on-disclosure':([(115,123)],[(142,155)],'Disclosure only changes the local disclosure Boolean and calls no business callback.'),
 'no-primary-callback-on-disabled':([(197,215)],[(212,224)],'The native disabled state and matching action guard prevent an ineligible primary callback.'),
 'no-choice-callback-on-disabled':([(174,194)],[(181,191)],'The native disabled state and requested guard prevent a disabled choice callback.'),
 'uncapped-text-lines':([(92,215)],[(110,244)],'All relevant Text constructions have no finite max-line cap; Swift sets lineLimit(nil) and vertical fixed sizing. This is configuration only.'),
 'primary-label-allocation-config':([(197,215)],[(212,244)],'The primary label container fills available width and the 56-unit control height; this source statement does not certify rendered dimensions.'),
 'primary-content-shape-config':([(203,215)],[(223,244)],'Swift gives the full label a Rectangle contentShape; Compose configures a RectangleShape Button and a full-size label Box with zero content padding.'),
 'canvas-noninteractive':([(81,90)],[(85,92)],'The canvas has only layout/background/identifier/container semantics and no activation action or interactive role.'),
 'surface-noninteractive':([(92,99),(147,155)],[(93,100)],'The surface carrier has layout/background/identifier/container semantics and no activation action or interactive role.'),
 'ink-noninteractive':([(94,99)],[(102,107)],'The ink rectangle/Box has paint, size, label and identifier only, with no activation action or interactive role.'),
 'guard-predicate':([(69,72),(197,215)],[(76,77),(212,224)],'The predicate includes capacity equality, the metered-and-Wi-Fi-only exclusion and not requested, exactly as the proposition states.'),
 'guard-priority':([(74,79)],[(78,83)],'Status branches test insufficient storage, then requested, then metered Wi-Fi-only, then ready.'),
 'choice-toggle':([(174,179)],[(181,186)],'A successful pre-request choice action negates the current local Boolean.'),
 'choice-callback-value':([(174,179)],[(181,186)],'The callback receives the preference after the local toggle.'),
 'choice-callback-count':([(174,179)],[(181,186)],'The guarded successful choice action contains exactly one caller callback invocation.'),
 'download-requested-state':([(197,202)],[(212,221)],'The eligible download action changes requested to true.'),
 'download-callback-count':([(197,202)],[(212,221)],'The eligible download action contains exactly one onDownload invocation and guards repeated requests.'),
 'callback-preference':([(197,202)],[(212,221)],'The download action passes the current local Wi-Fi-only Boolean.'),
 'no-disk-measurement':([(1,262)],[(11,267)],'The component compares caller-provided integer MB quantities and includes no disk-capacity measurement.'),
 'no-audio-fetch':([(1,262)],[(11,267)],'The complete file contains UI/local state and callback recording only, with no audio/network/download operation.'),
 'exact-api-AudioTourChapter':([(4,14)],[(51,51)],'The exact required exported chapter type, immutable values, conformances where applicable, and initializer/signature are present.'),
 'exact-api-OfflineAudioTour':([(17,36)],[(53,61)],'The exact required exported tour type, immutable model values, conformances where applicable, and initializer/signature are present.'),
 'exact-api-OfflineAudioTourPanel':([(39,58)],[(64,70)],'The exact required native component declaration and public initializer/body or Kotlin Modifier default contract are present.'),
 'api14-availability':([(1,262)],[],'The file uses SwiftUI APIs available by iOS 14, including title2 typography and accessibility identifiers/traits; no unguarded newer API is present. This manual source/API review is not an iOS-14 link or runtime claim.'),
 'bridge-no-ui':([(4,17)],[(9,28)],'The immutable approved bridge only constructs model values and invokes the production component; it authors no substitute component UI.'),
 'bridge-no-state':([(4,17)],[(9,28)],'The approved bridge has no stored local component business state.'),
 'bridge-no-identity-reset':([(4,17)],[(9,28)],'The approved bridge applies no id/key reset wrapper; identity reset resides in production.'),
 'bridge-current-input':([(5,15)],[(11,26)],'Each model field and chapter is decoded from the currently supplied fixture before the production component call.'),
 'bridge-callback-forwarding':([(13,15)],[(24,26)],'The callbacks received from the production component are forwarded directly to observer event receipt with their actual arguments.')}
source_dec=[]
for row in cat['rows']:
 platform,suffix=row['id'].split('-',1);assert suffix in m,row['id'];sr,ar,reason=m[suffix];ranges=sr if platform=='ios' else ar;assert ranges
 evidence=[]
 for rel in row['files']:
  for start,end in ranges:evidence.append({'file':rel,'sha256':cat['files'][rel]['sha256'],'start_line':start,'end_line':end})
 source_dec.append({'review_id':row['review_id'],'actual':True,'reason':reason,'evidence':evidence})
save(OUT/'initial/source-judge.json',{'review':{'version':1,'catalog_sha256':inp['catalog_sha256'],'decisions':source_dec},'attributions':[]})
print('Written runtime decisions:',sum(x['visual_decisions'] for x in coverage),'source:',len(source_dec))
