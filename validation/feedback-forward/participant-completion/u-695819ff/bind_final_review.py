import pathlib,json,hashlib,subprocess,time
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');d=b/'design/T2/public';a=json.load(open(d/'approval.json'));root=pathlib.Path('agent-output/final-self')
reasons={
 'title-wrapping':'The complete caller title is readable across its natural wrapped lines, with no ellipsis or cut-off text.',
 'subtitle-wrapping':'Language and the complete supplied whole-MB subtitle are visible on natural lines without truncation.',
 'status-wrapping':'The complete current status string is visible, wrapping in the narrow case where needed.',
 'disclosure-wrapping':'The complete Review chapters or Hide chapters label is visible without truncation.',
 'choice-wrapping':'Wi-Fi only is fully readable beside the decorative square, with no cut-off label.',
 'primary-wrapping':'The full Get audio or Requested label is visible within the primary rectangle.',
 'heading-wrapping':'All eight chapter headings are readable across the overlapping full sweep, including wrapped narrow-case headings; there is no ellipsis.',
 'body-wrapping':'All eight supplied chapter bodies are readable through overlapping sweep frames down to the final paragraph; natural viewport edges are filled by the next overlapping image.',
 'title-hierarchy':'The main tour title is visibly larger and more prominent than the section headings, which remain distinct from regular body copy.',
 'horizontal-clipping':'The inspected full sweep shows text and controls contained horizontally inside the white surface; no text is clipped at either side.',
 'row-overlap':'Successive title, subtitle, band, disclosure, chapter, choice and primary rows remain visually separated throughout the sweep.',
 'flow-order':'The visible top-to-bottom order is ink mark, title, subtitle, status, disclosure, expanded chapters when present, choice, primary.',
 'single-column':'All component blocks remain in one vertical reading column across the complete sweep.',
 'full-width-canvas':'The visible pale component canvas extends across the offered component width inside the host margins; its white surface is inset within it. Exact fill remains a separate pixel check.',
 'collapsed-headings':'The complete closed-state capture shows no chapter headings.',
 'collapsed-bodies':'The complete closed-state capture shows no chapter body paragraphs.',
 'expanded-order':'The full sweep shows all eight heading/body pairs in caller order from harbor gate to changing waterfront for P1, or first spinning wheel to makers working today for P2.',
 'status-rectangle':'The visible status paint has square corners and a rectangular silhouette, including the taller wrapped bands.',
 'status-no-border':'The visible painted status perimeter has no border stroke.',
 'primary-rectangle':'The visible primary painted surface has four square corners and a rectangular silhouette.',
 'primary-no-border':'No border stroke is visible around the primary painted surface.',
 'primary-painted-allocation':'The visible primary painted rectangle fills the observed control allocation edge to edge, with no uncovered strips. This is a visual allocation judgment, not a physical hit-area claim.',
 'ink-rectangle':'The visible solid ink accent is a narrow rectangle with four square corners.',
}
for platform in ['ios','android']:
 for case in ['P1','P2']:
  out=root/platform/case;c=json.load(open(out/'catalog.json'));p=b/'corpora/u-695819ff/final-public'/platform/case/'native/observation.json';o=json.load(open(p));groups=json.load(open(root/'contact'/f'{platform}-{case}-indices.json'));decisions=[]
  for r in c['rows']:
   if r['method']!='visual':continue
   ids=groups.get(r['state'],[]);aspect=r['id'].split('/')[-1];actual=True if ids else None;reason=reasons[aspect] if ids else 'No post-state original image was available for this visual atom; unknown.'
   if ids:reason+=' Inspected the labeled final original PNGs in final-self/contact; judgments cover this state only.'
   if platform=='ios':reason+=' The run separately reports missing audio.surface native visibility; this qualitative image judgment does not resolve that marker or its pixel measurement.'
   decisions.append({'review_id':r['review_id'],'actual':actual,'reason':reason,'snapshot_indices':ids})
  sub={'version':1,'catalog_sha256':c['catalog_sha256'],'observation_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'decisions':decisions};sp=out/'submission.json';sp.write_text(json.dumps(sub,indent=2))
  cmd=['python3',str(b/'candidate-v9/scripts/review_contract.py'),'review','--plan',str(d/'compiled'/case/platform/'plan.json'),'--design-lock',str(d/'design-lock.json'),'--design-sha256',a['design_lock_sha256'],'--policy',str(d/'policy.json'),'--policy-sha256',a['policy_sha256'],'--platform',platform,'--observation',str(p),'--submission',str(sp.resolve()),'--output',str((out/'bound').resolve())]
  st=time.time();r=subprocess.run(cmd,capture_output=True,text=True);(out/'review-run.json').write_text(json.dumps({'startedAtUnix':st,'finishedAtUnix':time.time(),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2));print(platform,case,len(decisions),r.returncode,r.stderr[:250])
phase=json.load(open(root/'phase.json'));phase.update({'completedAtUnix':time.time(),'reviewedContactSheets':[str(p) for p in sorted((root/'contact').glob('*.jpg'))],'limits':['All full representative state_captures report complete=true and bottom_reached=true, and their full overlapping PNGs were inspected.','Both iOS run results remain invalid_or_incomplete_capture because required audio.surface was never visible in native observations. Visible white paint does not resolve its marker or pixel measurement.','Only qualitative Boolean decisions are submitted; original expected values/units and native pixel unknowns remain unchanged.','No source edits or further native requests after final source close.']});(root/'phase.json').write_text(json.dumps(phase,indent=2))
