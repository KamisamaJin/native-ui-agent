import copy,json,pathlib
b=pathlib.Path(__file__).parent
content={
 'ready':'Across the fresh final sweep, the initial heading, introduction, all rain/garden/harbor title-detail pairs, quiet note, off acknowledgement, ready status, Start listening, Cancel and footer are complete. No error or summary is displayed.',
 'validation':'The complete initial content is retained. The exact error Choose a soundscape and confirm the quiet-space note. appears below ready status and above Start listening; Cancel and the full footer follow. No summary is shown.',
 'started':'All initial caller copy remains. Rain is selected and acknowledgement is on; Your listening break is ready. and Ready to begin: Rain on the conservatory roof are readable, followed by Choose again, Cancel and the complete footer. No error is visible.',
 'renewed':'The fresh post-Choose-again sweep shows all initial caller fields, off acknowledgement, ready status, Start listening, Cancel and full footer, with no validation error or success summary.',
 'canceled':'After the successfully dispatched Cancel, the fresh sweep shows all initial caller fields, off acknowledgement, ready status, Start listening, Cancel and full footer. No validation error or success summary remains.',
 'replaced':'The fresh replacement sweep shows A fresh collection for your next pause, the updated introduction, Rain beneath the glass canopy, Evening garden after the volunteers leave, Harbor bells — still unavailable and their complete details, updated note and footer. Acknowledgement is off; ready status, Start listening and Cancel are present without error or summary.'}
for pl in ['ios','android']:
 p=b/pl/'quiet-library';cat=json.loads((p/'catalog.json').read_text());t=copy.deepcopy(json.loads((p/'template.json').read_text()));rmap={r['review_id']:r for r in cat['rows'] if r.get('method')=='visual'};req=json.loads((p/'request.json').read_text());obs=json.loads((pathlib.Path(req['capture'])/'native/observation.json').read_text());ix={r['state_id']:r for r in obs['state_captures']}
 for d in t['decisions']:
  r=rmap[d['review_id']];state,aspect=r['id'].split('/',1);sc=ix[state];assert sc['complete']
  if aspect=='content-complete':reason=content[state]
  elif aspect=='vertical-order':reason='The complete fresh sweep shows heading, introduction, caller-ordered rain/garden/harbor title-detail pairs, quiet note, acknowledgement switch row, status, applicable error or success summary, primary action, Cancel and footer in that vertical sequence. Each option title is above its detail.'
  elif aspect=='text-wrap':reason='All caller copy and fixed/action labels are readable across this full fresh sweep. Long lines wrap; no ellipsis, horizontal overflow, clipping inside a control/text block, or apparent scaling down is visible. Content cut by the viewport edge is covered by another indexed frame.'
  elif aspect=='content-overlap':reason='The fresh sweep shows separate regions with gaps for option title/detail pairs, note, acknowledgement label and trailing switch, status, applicable validation/success text, actions and footer. No component text or controls visibly overlap.'
  elif aspect=='replacement-exclusion':reason='Only the replacement logical fields appear in the complete fresh replacement sweep. No separate superseded initial heading, introduction, option title/detail matched by ID, note or footer instance is retained. Shared phrases inside legitimate complete replacement fields, including Harbor bells, are not counted as stale copy.'
  else:raise ValueError(aspect)
  d.update(actual=True,reason=reason,snapshot_indices=sc['snapshot_indices'])
 assert len(t['decisions'])==25
 (p/'submission.json').write_text(json.dumps(t,indent=2)+'\n')
 print(pl,len(t['decisions']),'original final image decisions written')
