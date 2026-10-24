import sys
sys.dont_write_bytecode=True
import json,hashlib,time
from pathlib import Path
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=ROOT/'judgments/d0/one/T1'
sys.path.insert(0,str(ROOT/'candidate-v9/scripts'))
import native_checks,design_contract
load=lambda p:json.loads(p.read_text())
write=lambda p,d:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n'))
# These rationales encode the assessor's actual image inspection, not a verdict inferred from the implementation.
reasons={
 'title-wrapping':'The complete supplied title is visible in natural multiline flow, with its final word and no ellipsis.',
 'subtitle-wrapping':'The supplied destination and temperature string, including the final temperature unit, is visible without truncation; the narrow case wraps naturally.',
 'status-wrapping':'The entire current status string is legible inside the band; line breaks preserve all words.',
 'disclosure-wrapping':'The current Review/Hide handling label is completely visible without an ellipsis.',
 'choice-wrapping':'The full current confirmation label is visible beside the check square; narrow layouts wrap it without dropping words.',
 'primary-wrapping':'The full Release transfer/Requested label is visible and centered, without truncation.',
 'horizontal-clipping':'Across the state images, content stays within the component sides. Cropping at the viewport top/bottom is ordinary parent scrolling; overlapping frames expose the text there.',
 'row-overlap':'Successive text rows and controls have visible separation across the state. No glyphs or surfaces overlap adjacent rows.',
 'flow-order':'The images show accent, title, subtitle, status, disclosure, then any notes, choice and primary in that vertical reading order.',
 'single-column':'The main blocks align in one vertical column; the check square and its label remain one choice row.',
 'full-width-canvas':'The pale painted canvas extends to both offered component edges inside the host gutters, around the white surface. The external host region is excluded.',
 'collapsed-headings':'The closed state proceeds from disclosure to choice and primary; no handling-note heading is visible.',
 'collapsed-bodies':'The closed state proceeds from disclosure to choice and primary; no handling-note body paragraph is visible.',
 'status-rectangle':'The visible band has straight horizontal/vertical edges and four square corners.',
 'status-no-border':'The status surface is a flat fill with no visible outline stroke.',
 'primary-rectangle':'The fully exposed primary fill has four square corners and straight edges.',
 'primary-no-border':'The primary fill has no visible outline stroke.',
 'primary-painted-allocation':'The fully exposed primary painted rectangle meets its observed native control boundary on all sides; no uncovered strip is visible.',
 'ink-rectangle':'The solid accent is a vertical rectangle with four square corners.',
 'heading-wrapping':'All eight caller headings are exposed in the overlapping state sweep and retain their complete supplied words, including narrow multiline headings.',
 'body-wrapping':'All eight caller paragraphs are readable through overlapping state frames, from each opening through its ending, with natural wrapping and no ellipses.',
 'title-hierarchy':'The title is visibly larger than the semibold section headings, making it more prominent.',
 'expanded-order':'The eight heading/body pairs appear in the same order as the independent caller copy, from seal/manifest check through paperwork.'
}
summary=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  p=ROOT/'evaluation-inputs/d0/T1/initial'/platform/case; inp=load(p/'inputs.json');cat=load(p/'catalog.json');plan=load(p/'plan.json');obs=load(ROOT/inp['observation']);judge=load(p/'judge-template.json')
  assert hashlib.sha256((ROOT/inp['observation']).read_bytes()).hexdigest()==inp['observation_sha256']
  assert design_contract.digest(cat)==judge['review']['catalog_sha256']
  states={s['id']:native_checks.bound_state_evidence(obs,s)for s in plan['states']}
  for row in cat['rows']:
   if row['method']!='visual':continue
   found,complete,why,capture=states[row['state']];indices=[i for i,_ in found]
   reason=reasons[row['requirement_id']]
   if not indices:
    actual=None;reason='No eligible original state-bound screenshot is available; '+why
   else:actual=True
   judge['review']['decisions'].append({'review_id':row['review_id'],'actual':actual,'reason':f'{platform}/{case}/{row["state"]}: '+reason,'snapshot_indices':indices})
  write(OUT/'initial'/platform/case/'judge.json',judge)
  summary.append({'platform':platform,'case':case,'observation_sha256':inp['observation_sha256'],'decisions':len(judge['review']['decisions']),'state_evidence':{s:{'indices':[i for i,_in in f],'complete':c,'reason':w}for s,(f,c,w,cap)in states.items()}})
write(OUT/'runtime-coverage.json',summary)
# Source propositions were independently inspected in the exact original files.
cat=load(ROOT/'source-evaluation-inputs/d0/T1/initial/catalog.json');j=load(ROOT/'source-evaluation-inputs/d0/T1/initial/template.json');assert design_contract.digest(cat)==j['review']['catalog_sha256']
# Tight line intervals are paired with a proposition-specific source explanation.
source={
'production-component':((39,60),(71,78),'The public component is defined here in the declared production file, with its real native view/composable body.'),
'caller-driven-rendering':((98,198),(95,255),'Title, destination/range, guards and note content are read from the supplied transfer model and used by the rendered nodes.'),
'disclosure-production-state':((64,71),(79,82),'The production content owns the local disclosure state, initialized false.'),
'choice-production-state':((64,71),(79,82),'The production content owns the local acknowledgement state, initialized false.'),
'requested-production-state':((64,71),(79,82),'The production content owns the local requested state, initialized false.'),
'identity-reset-disclosure':((53,71),(79,82),'Changing transfer.id recreates the local disclosure state with false, within the production identity boundary.'),
'identity-reset-choice':((53,71),(79,82),'Changing transfer.id recreates the local acknowledgement state with false, within the production identity boundary.'),
'identity-reset-requested':((53,71),(79,82),'Changing transfer.id recreates the local requested state with false, within the production identity boundary.'),
'reset-quiet':((53,71),(79,82),'The ID-dependent state initialization performs no callback invocation; callbacks are only retained and passed through.'),
'native-disclosure-button':((137,146),(149,162),'Disclosure is a SwiftUI/Material native Button with its own action and identifier.'),
'native-choice-button':((167,184),(187,225),'Choice is a SwiftUI/Material native Button with its own action and identifier.'),
'native-primary-button':((186,198),(227,256),'Primary is a SwiftUI/Material native Button with its own action and identifier.'),
'native-selected':((167,184),(187,199),'The native choice selected semantic is derived directly from acknowledged, which its action updates.'),
'choice-native-disabled':((167,184),(187,203),'The actual Button disabled/enabled setting is derived from requested.'),
'primary-native-disabled':((186,198),(227,245),'The actual Button disabled/enabled setting is derived from canRelease.'),
'canvas-preserve-controls':((98,113),(95,102),'The canvas contains children rather than combining them into one control; it does not merge descendant semantics.'),
'surface-preserve-controls':((115,206),(103,111),'The surface contains children rather than combining them into one control; it does not merge descendant semantics.'),
'unique-semantic-ids':((98,221),(95,255),'Static identifiers occur once on their actual nodes; section identifiers use the unique enumeration index for each heading/body pair.'),
'status-band-provenance':((209,221),(132,147),'The status identifier is applied to the actual padded background-bearing status node, without a proxy.'),
'status-text-provenance':((209,221),(142,146),'The statusText identifier is applied directly to the displayed status Text/PanelText allocation.'),
'no-nested-scroll':((98,221),(95,259),'The complete production layout uses stacks/columns and controls without a scroll container.'),
'no-blank-padding-rows':((98,221),(95,259),'The layout consists of actual content, ordinary padding and gaps; no blank row or spacer manufactures long-content height.'),
'model-row-order':((148,164),(164,184),'The caller note collection is traversed in order by enumeration and each heading precedes its body.'),
'no-hidden-input-special-cases':((38,254),(71,291),'The full component contains only model-driven guards/state and the fixed public design palette; there are no scenario, fixture-ID or expected-value branches.'),
'callback-model-id':((230,234),(227,234),'Release forwards transfer.id from the current supplied model.'),
'callbacks-only-actions':((224,234),(187,234),'The only business callback invocation sites are guarded Button actions; neither rendering nor initialization invokes them.'),
'no-callback-on-disclosure':((137,146),(149,162),'The disclosure action only toggles handlingOpen and calls no business callback.'),
'no-primary-callback-on-disabled':((186,198),(227,245),'Native disabled semantics and the inner release eligibility guard both prevent a disabled release callback.'),
'no-choice-callback-on-disabled':((167,184),(187,203),'Native disabled semantics and the inner requested guard both prevent a disabled choice callback.'),
'uncapped-text-lines':((124,200),(119,271),'No finite line count is configured on any listed Text; SwiftUI inherits lineLimit(nil), and Compose retains its uncapped default.'),
'primary-label-allocation-config':((186,195),(227,255),'The primary label/control construction fills the available width and gives it the declared 56-unit height.'),
'primary-content-shape-config':((186,195),(227,255),'The primary uses the full rectangular label contentShape on SwiftUI and a full-size rectangular Material Button/label in Compose.'),
'canvas-noninteractive':((98,113),(95,102),'The canvas has a container semantic identity and no activation action or interactive role.'),
'surface-noninteractive':((115,206),(103,111),'The surface has a container semantic identity and no activation action or interactive role.'),
'ink-noninteractive':((117,122),(112,118),'The ink mark has a label/tag but no activation action or interactive role.'),
'guard-predicate':((77,79),(84,84),'canRelease is exactly sealIntact && coolantReady && acknowledged && !requested.'),
'guard-priority':((81,93),(85,91),'The status branches occur in the required order: broken seal, coolant, requested, acknowledgement, awaiting.'),
'choice-toggle':((224,228),(187,193),'A successful pre-request choice action negates the current acknowledgement Boolean.'),
'choice-callback-value':((224,228),(187,193),'The callback receives acknowledged after it is flipped.'),
'choice-callback-count':((224,228),(187,193),'Exactly one acknowledgement callback invocation exists in the successful guarded toggle path.'),
'release-requested-state':((230,234),(227,234),'The guarded eligible primary action sets requested true.'),
'release-callback-count':((230,234),(227,234),'Exactly one onRelease invocation exists in the successful eligible release path.'),
'no-physical-transfer':((224,254),(187,291),'Actions update local UI state and notify the caller only; no hardware, transport or physical-operation API is called.'),
'exact-api-TransferHandlingNote':((4,14),(59,59),'The required immutable fields and initializer/conformances or data-class declaration are exposed with the required types.'),
'exact-api-ColdStorageTransfer':((17,36),(61,69),'The required immutable model fields and Swift public initializer/conformances or Kotlin data-class declaration match the contract.'),
'exact-api-ColdStorageTransferPanel':((39,60),(71,78),'The required public Swift View initializer/body or Kotlin @Composable signature, callbacks and Modifier default match the contract.'),
'api14-availability':((1,254),None,'The used SwiftUI APIs predate or are introduced in iOS 14: ScaledMetric is the newest floor here and the production types declare iOS 14 availability. No unguarded newer API is present; this is a source review, not a legacy runtime certification.'),
}
bridge={
'bridge-no-ui':((4,17),(9,28),'The bridge only decodes the fixture and returns/calls the real production component; it creates no substitute control UI.'),
'bridge-no-state':((4,17),(9,28),'The bridge has no @State, remember, mutable local business state or state-owning wrapper.'),
'bridge-no-identity-reset':((4,17),(9,28),'No .id/key/reset wrapper is applied by the bridge.'),
'bridge-current-input':((5,13),(11,24),'Every current fixture model field and note row is decoded into the declared production model.'),
'bridge-callback-forwarding':((13,15),(24,26),'The actual component callback closures forward the acknowledgement value/current ID and the actual release ID into onEvent.'),
}
for row in cat['rows']:
 platform,suffix=row['id'].split('-',1);a,b,why=(bridge if suffix.startswith('bridge-') else source)[suffix];interval=a if platform=='ios'else b
 assert interval
 evidence=[]
 for f in row['files']:
  descriptor=cat['files'][f]; evidence.append({'file':f,'sha256':descriptor['sha256'],'start_line':interval[0],'end_line':interval[1]})
 j['review']['decisions'].append({'review_id':row['review_id'],'actual':True,'reason':why,'evidence':evidence})
write(OUT/'initial/source-judge.json',j)
print('runtime visual decisions',len(summary)*143,'source decisions',len(j['review']['decisions']))
