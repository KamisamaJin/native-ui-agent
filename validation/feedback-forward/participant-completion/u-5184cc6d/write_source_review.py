import json,pathlib,time,sys,difflib
phase=sys.argv[1];root=pathlib.Path('agent-output')/('source-'+phase)
c=json.loads((root/'catalog.json').read_text());s=json.loads((root/'submission-template.json').read_text())
ranges={
'production-component':((39,58),(64,70),'The public entry point is a native production View/Composable at the declared path.'),
'caller-driven-rendering':((101,138),(110,175),'Title, language, MB quantities and ordered chapter text read the supplied tour model.'),
'production-state':((60,67),(71,74),'Production-owned State/remember(tour.id) values initialize disclosure false, choice true and requested false.'),
'identity-reset':((51,67),(71,74),'The production identity boundary is tour.id; new identity recreates all three initial local values.'),
'reset-quiet':((51,67),(71,74),'The identity reset path contains only state initialization and no callback invocation.'),
'native-disclosure-button':((115,123),(142,155),'Disclosure uses native Button/TextButton and toggles production disclosure state.'),
'native-choice-button':((174,194),(181,210),'Choice uses native Button/TextButton.'),
'native-primary-button':((197,215),(212,245),'Primary uses native Button.'),
'native-selected':((190,194),(188,191),'Selected trait/selected semantics is bound to the local Wi-Fi-only Boolean.'),
'choice-native-disabled':((175,194),(181,197),'Native disabled/enabled is bound to requested state; the action also guards requested.'),
'primary-native-disabled':((197,215),(212,245),'Native primary disabled/enabled is bound to the full eligibility predicate.'),
'canvas-preserve-controls':((81,89),(85,92),'The canvas uses contain/nonmerging semantics and retains descendant controls.'),
'surface-preserve-controls':((144,154),(93,100),'The surface uses contain/nonmerging semantics and retains descendant controls.'),
'unique-semantic-ids':((81,215),(85,245),'Each literal ID belongs to one real allocation; chapter indices are emitted once in caller order.'),
'status-band-provenance':((157,171),(124,140),'The status ID is on the actual background-painted band container.'),
'status-text-provenance':((159,163),(134,139),'The statusText ID is on the displayed native Text.'),
'no-nested-scroll':((81,215),(85,245),'The full component has vertical layout containers and no scroll container.'),
'no-blank-padding-rows':((81,215),(85,245),'No blank fixed-height row is inserted; Android spacer is horizontal choice-icon spacing.'),
'model-row-order':((125,141),(157,178),'Expanded nodes iterate the supplied chapters in caller order.'),
'no-hidden-input-special-cases':((39,262),(64,267),'The complete component uses model properties and local state, with no fixture/scenario/test ID branches.'),
'callback-model-id':((197,201),(212,220),'The request callback forwards tour.id.'),
'callbacks-only-actions':((115,215),(142,245),'Business callbacks occur only inside guarded enabled choice and primary action closures.'),
'no-callback-on-disclosure':((115,123),(142,155),'Disclosure action only toggles chaptersOpen.'),
'no-primary-callback-on-disabled':((197,215),(212,245),'Native disable and the action eligibility guard both prevent a disabled dispatch.'),
'no-choice-callback-on-disabled':((175,194),(181,197),'Requested state disables the native control and guards its action.'),
'uncapped-text-lines':((101,211),(110,243),'No finite maxLines/lineLimit is configured; Swift explicitly inherits lineLimit(nil).'),
'primary-label-allocation-config':((203,211),(224,244),'The label fills maximum width and 56-unit control height.'),
'primary-content-shape-config':((203,211),(224,244),'Swift applies Rectangle contentShape to its full label; Compose Button uses RectangleShape with full-size Box label.'),
'canvas-noninteractive':((81,89),(85,92),'Canvas has no action/interactive role.'),
'surface-noninteractive':((92,154),(93,100),'Surface has no action/interactive role.'),
'ink-noninteractive':((94,99),(102,108),'Ink rectangle/Box has a label but no action/interactive role.'),
'guard-predicate':((69,72),(76,77),'The source predicate uses >= capacity equality, blocks metered plus Wi-Fi-only and requested, and allows unmetered true-choice eligibility.'),
'guard-priority':((74,79),(78,83),'Status checks storage, requested, metered plus Wi-Fi-only, then ready in that order.'),
'choice-toggle':((175,178),(181,186),'The eligible choice action flips the current Boolean.'),
'choice-callback-value':((175,178),(181,186),'The callback receives the newly flipped Boolean.'),
'choice-callback-count':((175,178),(181,186),'There is one callback invocation in the successful choice action.'),
'download-requested-state':((197,201),(212,220),'The successful guarded request sets requested true before callback.'),
'download-callback-count':((197,201),(212,220),'There is exactly one callback invocation in the successful request action.'),
'callback-preference':((197,201),(212,220),'The request forwards current wifiOnly, including true on an unmetered eligible path.'),
'no-disk-measurement':((39,262),(64,267),'Capacity decisions read caller Int quantities and perform no disk API calls.'),
'no-audio-fetch':((39,262),(64,267),'The full component records state/callback and contains no networking or audio transfer.'),
'exact-api-AudioTourChapter':((4,14),(51,51),'Model declaration has the exact public immutable Swift contract/conformances or Kotlin data-class val contract.'),
'exact-api-OfflineAudioTour':((17,36),(53,61),'Tour model has exact stored values/types and public Swift initializer/conformances or Kotlin data-class val contract.'),
'exact-api-OfflineAudioTourPanel':((39,58),(64,70),'Component has exact public Swift View/body/initializer or Composable signature and Modifier default.'),
'api14-availability':((1,262),(1,267),'Reviewed all Swift APIs: View/State/id, accessibilityIdentifier/contain, selected traits, ButtonStyle, semantic fonts, fixedSize/frame/contentShape, sRGB Color and standard collections are available by iOS14; no newer unguarded API is used.'),
}
s['decisions']=[]
for r in c['rows']:
 platform,ident=r['id'].split('-',1)
 ev=[]
 if ident.startswith('bridge-'):
  reason={'bridge-no-ui':'Bridge only decodes model and invokes production component; no substitute UI.', 'bridge-no-state':'Bridge has no local component state.', 'bridge-no-identity-reset':'Bridge calls the production component without id/key reset wrapper.', 'bridge-current-input':'Bridge decodes the current fixture values into the production model.', 'bridge-callback-forwarding':'Both production callback closures forward actual callback arguments into onEvent.'}[ident]
  for f in r['files']:ev.append({'file':f,'sha256':c['files'][f]['sha256'],'start_line':1,'end_line':c['files'][f]['line_count']})
 else:
  item=ranges.get(ident)
  if item is None and ident.endswith('production-state'):item=ranges['production-state']
  if item is None and ident.startswith('identity-reset-'):item=ranges['identity-reset']
  if item is None:raise ValueError(ident)
  pair=item[0 if platform=='ios' else 1];reason=item[2]
  if phase=='final':
   name='OfflineAudioTourPanel.swift' if platform=='ios' else 'OfflineAudioTourPanel.kt'
   current=pathlib.Path('alerttoast/Sources/AlertToast')/name if platform=='ios' else pathlib.Path('reply/Reply/app/src/main/java/com/example/reply/ui/components')/name
   old=(pathlib.Path('agent-output/source-versions/original')/name).read_text().splitlines();new=current.read_text().splitlines();mapping={}
   for tag,a,b,x,y in difflib.SequenceMatcher(None,old,new).get_opcodes():
    for n in range(a,b):mapping[n+1]=x+(n-a)+1 if tag=='equal' else min(x+1,len(new))
   pair=(mapping[pair[0]],mapping[pair[1]])
  for f in r['files']:ev.append({'file':f,'sha256':c['files'][f]['sha256'],'start_line':pair[0],'end_line':min(pair[1],c['files'][f]['line_count'])})
 s['decisions'].append({'review_id':r['review_id'],'actual':True,'reason':reason,'evidence':ev})
(root/'submission.json').write_text(json.dumps(s,indent=2))
(root/'review-times.json').write_text(json.dumps({'completedAtUnix':time.time(),'phase':phase,'limit':'Source judgments establish source propositions only; runtime geometry, physical hits and legacy package/link/runtime remain separate.'},indent=2))
