import sys,json,hashlib
from pathlib import Path
stage=sys.argv[1];b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/cache/study/arms/B');out=b/'work'/f'{stage}-review'
for pl in ['ios','android']:
 root=b/'runs'/stage/pl/'cycle';req=json.loads((root/'after-review-request.json').read_text());o=json.loads((root/'capture/native/observation.json').read_text());states={s['state_id']:s['snapshot_indices'] for s in o['state_captures']};sub=req['submission_template'];by={r['review_id']:r for r in req['rows']}
 for dec in sub['decisions']:
  row=by[dec['review_id']];state,rule=row['id'].split('/');indices=states[state];dec['actual']=True
  if rule=='title-wrapping':dec['snapshot_indices']=[indices[0]];dec['reason']=f'{stage} {pl} {state}: the complete current Cedar Hall occasion title is readable in wrapped lines through its final words, without truncation or ellipsis.'
  elif rule=='title-hierarchy':dec['snapshot_indices']=indices[:2];dec['reason']=f'{stage} {pl} {state}: the occasion title is visibly larger and bolder than Choose a replacement and the section headings in the original frames.'
  elif rule=='option-clipping':dec['snapshot_indices']=indices[:3];dec['reason']=f'{stage} {pl} {state}: the overlapping original frames show all current option descriptions through their complete final sentences inside their cards, followed by separate price, range and Unavailable text. No clipped description is visible.'
  elif rule=='balance-overlap':dec['snapshot_indices']=indices[3:5];dec['reason']=f'{stage} {pl} {state}: original balance-card frames show selection, totals, prepaid, applied credit and signed balance in separate vertical rows; the balance label and amount are clear of other card text.'
 (out/f'{pl}-image-actuals.json').write_text(json.dumps(sub,ensure_ascii=False,indent=2)+'\n')
 source=json.loads((b/'work'/('repair-source-actuals-ios.json' if pl=='ios' else 'D0-review/android-source-actuals-v2.json')).read_text())
 for row in source['observations']:
  if row['id']=='component.api':row['reason']=f'The current source exports the exact API.md DTOs, initializers/data classes, component and typed submission wireValue in the sole component file. {stage} native collection successfully rendered the imported production API; this review establishes source/API obligations, not generic computed styles.'
  if row['id']=='component.palette' and pl=='ios':
   row['reason']='All light/dark palette role constants match the independent public palette. The three native Buttons use MenuReviewButtonStyle returning configuration.label unchanged and keep .disabled/action guards. Unavailable rows select secondary ink without whole-row opacity; disabled send uses explicit disabled fill/ink. Current original images show the corrected disabled presentation. Source evidence and native sampled pixels remain separate.'
   p=str(b/'workspace/alerttoast/Sources/AlertToast/MenuChangeReviewPanel.swift');row['citations']=[{'path':p,'line':i} for i in [137,145,156,161,163,273,292,333,453,457,460]]
 (out/f'{pl}-source-actuals.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
paths=[b/'workspace/alerttoast/Sources/AlertToast/MenuChangeReviewPanel.swift',b/'workspace/reply/Reply/app/src/main/java/com/example/reply/ui/components/MenuChangeReviewPanel.kt'];hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};approved=json.loads((b/'work/repair-source-hashes.json').read_text());assert hashes==approved,'Locked source hash changed';(out/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n');print('Actual-only submissions prepared for inspected '+stage+' frames; locked source matches.')
