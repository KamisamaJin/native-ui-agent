from pathlib import Path
import json
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/one/T2'
m=json.loads((O/'input-hashes-and-state-coverage.json').read_text())
for d in sorted((B/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(d.parts[-3:]);i=json.loads((d/'inputs.json').read_text());cat=json.loads((d/'catalog.json').read_text());decisions=[];atts=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  st=row['state'];indices=m['cases'][key]['states'][st]['snapshot_indices'];actual=True
  context={'baseline':'The closed baseline shows all six incident labels and c’s exact unavailable reason, plus title, subtitle, notice, summary, primary label and entire footer. Collapsed guidance and incident dossiers are intentionally excluded.', 'expanded':'The open state shows a selected with its complete latest-sample dossier immediately below it, the other five labels and c’s exact unavailable reason, plus the complete header, notice, summary, primary label and footer.', 'submitted':'The replacement model is present: Caller update notice, a’s Unavailable status and supervisor reason, c’s maintenance reason, b selected, closed dossier, current b summary, primary label and complete footer. No now-collapsed detail is required.'}[st]
  if row['aspect']=='wrapping':
   reason=context+' In the original overlapping viewport PNGs, all required characters remain readable; lines expand vertically without clipping or ellipsis. Character fallback in narrow text is accepted for segments that exceed the available width. Exact-state native interval coverage is complete.'
  else:
   reason=context+' Across the original overlapping viewport PNGs, the text blocks, severity/status content, rail, disclosure, dossier when applicable, summary and action occupy separate areas; no unintended overlap or occlusion is visible. Exact-state native interval coverage is complete.'
  if i['platform']=='android' and i['case']=='P2' and row['aspect']=='wrapping':
   actual=False
   example='approach pre / ssure-gauge / drift' if i['source']=='source-a' else 'pressure-gau / ge drift'
   reason=context+f' All required text is present and not ellipsized, but the f label breaks pressure-gauge as “{example}”. The approved brief requires natural breaks at spaces and hyphens before character fallback for an overwide segment. Here the existing hyphen is bypassed and a segment is split even though that short segment can occupy a line. This fails the natural-wrapping proposition; this is not an overlap or missing-text finding. The complete coherent sweep was inspected.'
   issue={'source-a':{'baseline':[16,17],'expanded':[37,38],'submitted':[95,96]},'source-b':{'baseline':[16,17],'expanded':[38,39],'submitted':[97,98]}}[i['source']][st]
   assert set(issue)<=set(indices)
   atts.append({'id':row['id'],'cause':'product','reason':f'The original exact-state f-card PNGs show the same mid-segment break ({example}) inside the component text area. The label’s characters and hyphen are intact in the supplied model/native labels, and the approved Android environment passes. Neighboring content is stable and there is no viewport-edge clipping at this label. The source capsule owns this label’s Text layout (RiverCopy/RiverText); the host owns only viewport/inset. This is a component line-breaking behavior, not an unsuitable color sample or a capture boundary. This attribution is limited to the supported natural-wrapping failure.','snapshot_indices':issue})
  if key=='source-b/ios/H1' and st=='submitted':
   actual=None;indices=[]
   reason='The captured submitted frames show the caller update, b selection/current summary, expanded block absence and a readable footer with no obvious collision. However frozen bound_state_evidence reports incomplete per-state interval union: the last interval ends at 1640 while native content height is 1646. Complete exact-state coverage is required for a true full-content judgment; I do not turn the visible bottom sentinel/footer into proof of the unobserved remainder. Unknown is retained; this is not a supported F and receives no failure-cause attribution.'
  decisions.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
 assert len(decisions)==6
 result={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':i['observation_sha256'],'decisions':decisions},'attributions':atts}
 path=O/key/'judge.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('wrote 12 judge files; 72 decisions')
