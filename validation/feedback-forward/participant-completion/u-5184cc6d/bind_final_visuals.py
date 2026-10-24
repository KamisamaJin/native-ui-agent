import json,pathlib,hashlib,subprocess,time,sys
sys.path.insert(0,"/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward/baseline-v8/scripts")
from native_checks import bound_state_evidence
w=pathlib.Path.cwd();out=w/'agent-output/final-self';base=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward/corpora/u-5184cc6d/final-public');design=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward/design/T2/public');approval=json.loads((design/'approval.json').read_text());script='/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward/baseline-v8/scripts/review_contract.py'
reasons={
 'title-wrapping':'The entire caller title is visible across natural lines, with no ellipsis or missing ending.',
 'subtitle-wrapping':'Language and MB subtitle is complete and wraps within the content column.',
 'status-wrapping':'The complete status string fits its painted band through natural wrapping.',
 'disclosure-wrapping':'The complete Review/Hide chapters label is visible without truncation.',
 'choice-wrapping':'Wi-Fi only is fully visible next to the separate decorative choice mark.',
 'primary-wrapping':'Get audio/Requested is fully visible and centered within its rectangular primary surface.',
 'horizontal-clipping':'The original overlapping viewport images keep visible content within the column; viewport-edge continuation is visible in adjacent samples.',
 'row-overlap':'Successive text, band and control allocations stay visually separate throughout the original sweep.',
 'flow-order':'The sweep shows accent, title, subtitle, status, disclosure, expanded chapters when open, choice, then primary.',
 'single-column':'All component blocks follow one vertical content column.',
 'full-width-canvas':'Pale component paint spans the complete offered content width between the parent horizontal gutters.',
 'collapsed-headings':'The full closed-state sweep contains no chapter heading between disclosure and choice.',
 'collapsed-bodies':'The full closed-state sweep contains no chapter body between disclosure and choice.',
 'status-rectangle':'The fully visible painted status band has four square corners.',
 'status-no-border':'The original status band has no visible surrounding border stroke.',
 'primary-rectangle':'The primary paint has four square corners in the original frame.',
 'primary-no-border':'The original primary surface has no visible surrounding border stroke.',
 'primary-painted-allocation':'Original primary paint fills the observed native control rectangle. A separately derived magenta native-boundary overlay aligns with all painted edges; the overlay is only a review aid, not replacement evidence.',
 'ink-rectangle':'The solid ink accent is visibly a narrow rectangle with four square corners.',
 'heading-wrapping':'Every chapter heading is complete in the overlapping full sweep and uses natural wrapping without ellipsis.',
 'body-wrapping':'All eight body paragraphs are readable through overlapping samples, including their endings and the final paragraph above bottom controls; no ellipsis or truncation is visible.',
 'title-hierarchy':'The title is visibly larger and more prominent than the expanded section headings.',
 'expanded-order':'The full sweep shows all eight supplied heading/body pairs in their caller order.'}
results=[]
for plat in ['ios','android']:
 for case in ['P1','P2']:
  p=out/plat/case;c=json.loads((p/'catalog.json').read_text());ob=base/plat/case/'native/observation.json';o=json.loads(ob.read_text());dec=[]
  for row in c['rows']:
   if row['method']!='visual':continue
   state=row['state'];atom=row['id'].split('/',1)[1];plan=json.loads((design/'compiled'/case/plat/'plan.json').read_text());definition=next(x for x in plan['states'] if x['id']==state);found,complete,why,capture=bound_state_evidence(o,definition);indices=[i for i,s in found]
   target=row.get('target',{}).get('identifier')
   if row['coverage']=='target' and target and target!='audio.canvas':
    indices=[i for i in indices if any(n.get('identifier')==target and (n.get('fully_within_viewport') or n.get('fully_visible')) for n in o['snapshots'][i]['nodes'])]
   known=bool(indices);reason=f'{plat} {case}, {state}: '+reasons[atom] if known else 'No fully visible original target frame is available; retain unknown.'
   dec.append({'review_id':row['review_id'],'actual':True if known else None,'reason':reason,'snapshot_indices':indices})
  submission={'version':1,'catalog_sha256':c['catalog_sha256'],'observation_sha256':hashlib.sha256(ob.read_bytes()).hexdigest(),'decisions':dec};(p/'submission.json').write_text(json.dumps(submission,indent=2))
  cmd=['python3',script,'review','--plan',str(design/'compiled'/case/plat/'plan.json'),'--design-lock',str(design/'design-lock.json'),'--design-sha256',approval['design_lock_sha256'],'--policy',str(design/'policy.json'),'--policy-sha256',approval['policy_sha256'],'--platform',plat,'--observation',str(ob),'--submission',str(p/'submission.json'),'--output',str(p/'bound-review')]
  r=subprocess.run(cmd,capture_output=True,text=True);(p/'review.log').write_text(r.stdout+r.stderr);results.append({'platform':plat,'case':case,'exit_code':r.returncode,'visual_decisions':len(dec),'unknown':sum(x['actual'] is None for x in dec),'log':str(p/'review.log')});print(results[-1])
phase=json.loads((out/'phase.json').read_text());phase['completedAtUnix']=time.time();phase['review_results']=results;phase['reviewed_artifacts']=['Each case images/manifest.json lists every reviewed representative-state/approved-target original PNG.','Original iOS P2 snapshot80 and Android P2 snapshots30,61,64 additionally inspected individually to resolve composite-sheet readability.','All forty state/platform/case primary native-boundary crops inspected.'];phase['limits']+=['Attempt 1 review binding rejected extra immediate/reveal frames outside the exact approved state epoch. Rejected submissions/logs are retained in attempt-1-rejected; revised bindings use the assigned bound_state_evidence selection with unchanged qualitative observations.','Strict native-pixel status-strip unknowns remain unchanged; no numeric color/support overrides were submitted.','Qualitative actuals are one assigned self-review; no independent external agreement is claimed.'];(out/'phase.json').write_text(json.dumps(phase,indent=2))
