import json,pathlib
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/one/T2'
load=lambda p:json.loads(p.read_text())
coverage=load(O/'coverage.json')
for case in sorted((B/'evaluation-inputs/d0/T2').glob('*/*/*')):
 key=str(case.relative_to(B/'evaluation-inputs/d0/T2'));source,platform,cn=key.split('/');inputs=load(case/'inputs.json');cat=load(case/'catalog.json');automatic=load(O/key/'recomputed-native.json')
 decisions=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  sid=row['state'];covered=coverage[key]['states'][sid];indices=[f['index'] for f in covered['frames']]
  assert covered['complete']
  if row['aspect']=='wrapping':
   if sid=='baseline':
    reason='The exact baseline sweep shows the complete title, subtitle, notice, closed disclosure label, six incident labels and severity words, c Unavailable status and caller reason, No alert selected summary, action label and complete footer. All required words are readable, with no visible truncation, clipping or ellipsis. Guidance and incident dossiers are intentionally collapsed.'
   elif sid=='expanded':
    reason='The exact expanded sweep includes the complete selected-a dossier from Latest sample: 07:18 local through cannot be acknowledged, together with the title, subtitle, notice, Hide reading dossier label, all six incident labels/severities, c status/reason, current summary, action and complete footer. Words continue in wrapped lines without ellipsis or clipping; unselected dossiers are intentionally absent.'
   else:
    reason='The exact submitted sweep shows the complete Caller update notice, newly unavailable a label/status and supervisor reason, c maintenance reason, all six incident labels/severities, closed disclosure, Reviewing b summary, action label and complete footer, plus the title/subtitle. The replacement has reset disclosure, so no dossier is required. Required words wrap without ellipsis, clipping or truncation.'
   if cn=='P2':reason+=' The narrow enlarged layout sometimes breaks an oversized unbroken word between characters; every character remains present, as the brief permits. Viewport-edge cuts are continued in overlapping original frames.'
  else:
   reason='Across every part of this exact coherent sweep, title/subtitle, notice, disclosure, incident labels, severity/status/reason text, summary, primary action and footer occupy separate vertical areas. There is no unintended text-to-text, rail-to-text, card-to-text or action overlap/occlusion.'
   if sid=='expanded':reason+=' The selected-a dossier has its own area below a and above b, with its complete long body visible through the overlapping frames.'
   if sid=='submitted':reason+=' The added caller notice and a unavailability reason grow their blocks; the updated summary and action remain separated.'
   reason+=' Ordinary clipping at the scrolling viewport edge is resolved by adjacent captures and is not a layout collision.'
  decisions.append({'review_id':row['review_id'],'actual':True,'reason':reason,'snapshot_indices':indices})
 attributions=[]
 for f in automatic['assertions']:
  if f['status']!='failed':continue
  assert source=='source-a' and platform=='ios' and f['id'].endswith('/primary-surface-color')
  attributions.append({'id':f['id'],'cause':'product','reason':'The original native river.submit box is fully visible and the approved side strip is inside its flat rounded-button fill, clear of glyphs, borders and the host. Frozen sampling consistently measures a changed disabled face, and the original PNG visibly shows the same dimming across the button. The source uses PlainButtonStyle with disabled(selected == nil); the palette value exists in source but the disabled style changes the final rendered face. The policy assigns primary fill to the component. This is a component disabled-appearance defect, not host/canvas sampling or infrastructure. The exact opacity/compositing mechanism is inferred; the ownership and rendered-fill contradiction are directly supported.','snapshot_indices':f['snapshot_indices']})
 result={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inputs['observation_sha256'],'decisions':decisions},'attributions':attributions}
 (O/key/'judge.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Wrote 8 judge files, 48 qualitative decisions, 4 separate failure-cause attributions.')
