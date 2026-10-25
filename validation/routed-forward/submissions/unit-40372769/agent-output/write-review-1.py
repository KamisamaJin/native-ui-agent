import copy,json,pathlib
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/routed-forward/feedback/unit-40372769/request-1')
content={
 'ready':'The full sweep shows the complete initial heading, introduction, rain/garden/harbor title and detail pairs, quiet note, off acknowledgement, ready status, Start listening, Cancel and footer. No error or summary is present.',
 'validation':'The complete initial copy remains visible; the exact both-condition error Choose a soundscape and confirm the quiet-space note. follows ready status, followed by Start listening, Cancel and the full footer.',
 'started':'The complete initial copy remains visible. Rain is selected, acknowledgement is on, status is Your listening break is ready., and Ready to begin: Rain on the conservatory roof appears before Choose again, Cancel and the footer. No validation error is visible.',
 'renewed':'After the successful Choose again activation the sweep returns to the complete initial editing content, off acknowledgement, ready status, Start listening and Cancel, with no error or summary.',
 'canceled':'After the successful Cancel activation the complete initial caller copy remains, acknowledgement is off, ready status and Start listening return, and no error or summary is visible.',
 'replaced':'The full replacement heading A fresh collection for your next pause, updated introduction, rain/garden/harbor title-detail pairs, quiet note and footer are readable, with off acknowledgement, ready status, Start listening and Cancel and no error or summary.'}
for pl in ['ios','android']:
 r=json.loads((b/'review-tasks'/pl/'quiet-library/request.json').read_text());t=copy.deepcopy(r['submission_template']);rows={x['review_id']:x for x in r['rows']};ix=json.loads((b/'review-tasks'/pl/'quiet-library/state-image-index.json').read_text())
 for d in t['decisions']:
  row=rows[d['review_id']];state,aspect=row['id'].split('/',1)
  if pl=='ios' and state in ['started','renewed','canceled']:
   d.update(actual=None,reason='The required option setup was unavailable: its named node is a generic wrapper and the requested native button dispatch did not occur. The Start attempt remained editing with Choose an available soundscape.; Choose again was never reached. Cancel itself succeeded but its required second-option setup was unavailable. This does not qualify the full requested action-state route for this visual judgment.',snapshot_indices=[]);continue
  if aspect=='content-complete': reason=content[state]
  elif aspect=='vertical-order':reason='The full indexed sweep shows heading, introduction, all caller-ordered option title/detail pairs, quiet note, acknowledgement, status, applicable error or summary, primary, Cancel and footer in the specified order; every option title precedes its detail.'
  elif aspect=='text-wrap':reason='Across the indexed full sweep all caller copy and fixed labels are readable with wrapping. No ellipsis, horizontal overflow, clipping inside a text/control, or apparent size reduction is visible. Viewport-edge cuts are covered by another sweep frame.'
  elif aspect=='content-overlap':reason='The full sweep shows separate regions and gaps for option title/detail pairs, quiet note, acknowledgement label and trailing switch, status, applicable error/summary, both actions and footer; no component content overlaps.'
  elif aspect=='replacement-exclusion':reason='The replacement sweep contains the new complete logical heading, introduction, corresponding option title/detail fields, quiet note and footer. No separately retained superseded initial field instance is visible. Shared phrases in legitimate updated fields, including Harbor bells, are not counted as stale.'
  else:raise ValueError(aspect)
  if pl=='ios' and state=='replaced':reason+=' Caller replacement succeeded in the same process. The prior selection setup was unavailable, so this only judges the replacement visuals, not reset of a selected option.'
  d.update(actual=True,reason=reason,snapshot_indices=ix[state]['indices'])
 pathlib.Path('agent-output/'+pl+'-request-1-actuals.json').write_text(json.dumps(t,indent=2)+'\n')
