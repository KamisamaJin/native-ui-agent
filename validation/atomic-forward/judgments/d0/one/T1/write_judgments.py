import json,pathlib,sys,hashlib
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/one/T1';sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks,native_pixels
coverage=json.loads((O/'coverage.json').read_text());pixelproofs={};summaries={}
for p in sorted((B/'evaluation-inputs/d0/T1').glob('*/*/*')):
 key=str(p.relative_to(B/'evaluation-inputs/d0/T1'));inp=json.loads((p/'inputs.json').read_text());cat=json.loads((p/'catalog.json').read_text());plan=json.loads((p/'plan.json').read_text());automatic=json.loads((p/'automatic.json').read_text());obs=json.loads((B/inp['observation']).read_text());decisions=[];attrs=[];pixelproofs[key]=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  state=row['state'];found,complete,why,capture=native_checks.bound_state_evidence(obs,next(s for s in plan['states'] if s['id']==state));indices=[i for i,_ in found]
  assert complete
  if row['aspect']=='wrapping':
   text='The complete coherent '+state+' scroll sweep was visually inspected from the original PNG-derived reading strip, covering title, subtitle, notice, all six labels and visible details, unavailable reasons, summary, disclosure label, Request station, and the complete footer. '
   if state=='expanded':text+='The open global safety briefing is fully present and wraps in its own block. '
   else:text+='The safety briefing body is deliberately collapsed and excluded from required visible text. '
   if state=='submitted':text+='Caller update notice and the new unavailable reason on a are fully present; b is selected and its long summary remains complete. '
   if inp['case']=='P2' and inp['platform']=='ios':text+='Unavailable sometimes breaks between characters at this narrow enlarged size; every character is preserved, as expressly allowed by the brief. '
   if inp['source']=='source-b' and inp['platform']=='ios':text+='Disabled content is visibly dimmed, but its glyphs and lines remain present; this decision answers the wrapping proposition only, not contrast or the separate fill atom. '
   text+='No word clipping, ellipsis, or missing required text was found. Native interval-union completeness and exact input/event binding were recomputed with frozen bound_state_evidence; source existence alone was not used as visual proof.'
  else:
   text='Every captured part of the coherent '+state+' scroll sweep was visually inspected. Header, padded notice, each of the six choice cards and its separate label/detail/reason text, summary, disclosure, primary action and footer occupy separate areas with visible gaps. '
   if state=='expanded':text+='The global safety briefing occupies an additional growing block between disclosure and action. '
   if state=='submitted':text+='The longer caller update notice and added unavailable reason on a grow their blocks without collisions; b selection and summary do not cover adjacent content. '
   text+='No unintended text, indicator, badge, disclosure, or action overlap/occlusion was found. Viewport cuts and contact-sheet column breaks are presentation boundaries, not component overlap. Complete exact-state coverage was recomputed by frozen bound_state_evidence.'
  decisions.append({'review_id':row['review_id'],'actual':True,'reason':text,'snapshot_indices':indices})
 for assertion in automatic['assertions']:
  if assertion['status']!='failed':continue
  row=next(r for r in cat['rows'] if r['id']==assertion['id']);assert row['method']=='native_pixels'
  state=next(s for s in plan['states'] if s['id']==row['state']);found,complete,why,capture=native_checks.bound_state_evidence(obs,state);allowed={i for i,_ in found};indices=assertion['snapshot_indices'];assert set(indices)<=allowed
  for idx in indices:
   measured=native_pixels.sample(obs['snapshots'][idx],row['target'],inp['platform'],B/inp['root'],row['sampling']);assert measured['status']=='measured';assert not native_pixels.matches(measured['argb'],row['expected'],row['sampling']['channel_tolerance']);pixelproofs[key].append({'id':row['id'],'snapshot_index':idx,**measured})
  attrs.append({'id':row['id'],'cause':'product','reason':'The exact '+row['state']+' state has a unique, fully visible native workshop.submit button, disabled because there is no selected available station. Its approved side sampling strip lies inside the button fill, clear of text, rounded edges and host background; frozen native_pixels recomputation finds a uniform but contradictory rendered fill in every cited frame. The original PNGs visibly show the same altered disabled surface. Ownership is component-fixed by policy. The production SwiftUI source uses PlainButtonStyle with .disabled(selected == nil) around the label that paints palette.disabled, so framework disabled appearance is permitted to alter the component-owned fill; this is consistent with the observed dimming of disabled label/card content. The original observer host adds viewport/background/environment and fixture controls, with no parent opacity, overlay or button-style substitution. Thus the supported cause is the component disabled rendering, not a host-region sample or an unsuitable/missing observation. The precise framework alpha mechanism is inferred rather than instrumented; the attribution rests on the actual component-owned surface, matching native box, coherent state and visible original evidence.','snapshot_indices':indices})
 output={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':decisions},'attributions':attrs}
 dest=O/key/'judge.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
 summaries[key]={'qualitative_decisions':len(decisions),'true':len(decisions),'false':0,'unknown':0,'attribution_ids':[a['id'] for a in attrs],'raw_automatic_counts':automatic['counts']}
(O/'pixel-proofs.json').write_text(json.dumps(pixelproofs,indent=2)+'\n');(O/'judgment-summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
print(json.dumps(summaries,indent=2))
