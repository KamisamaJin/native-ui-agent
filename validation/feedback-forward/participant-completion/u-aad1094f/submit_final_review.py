import pathlib,json,subprocess,hashlib,sys,time
r=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');w=r/'cache/u-aad1094f';scope=r/'design/T1/public';a=json.loads((scope/'approval.json').read_text());tool=r/'baseline-v8/scripts/review_contract.py';sys.path.insert(0,str(tool.parent));import native_checks
reasons={
 'title-wrapping':'The complete title is visible over natural word-wrapped lines; no ellipsis or lost characters are visible.',
 'subtitle-wrapping':'The destination, separator and complete temperature range remain readable, with natural wrapping where needed.',
 'status-wrapping':'The complete current status is readable within its band; wrapped status lines remain fully visible.',
 'disclosure-wrapping':'The complete Review/Hide handling label is visible without truncation.',
 'choice-wrapping':'The complete current confirmation label is visible next to its decorative square/check mark; larger text wraps cleanly.',
 'primary-wrapping':'The complete Release transfer/Requested label is readable within the painted control.',
 'horizontal-clipping':'Across the fresh overlapping sweep, content stays within the horizontal component surface; no side-clipped text is visible.',
 'row-overlap':'The fresh sweep shows distinct successive rows and paragraphs with no visual overlap.',
 'flow-order':'The fresh full sweep shows accent, title, subtitle, status, disclosure, expanded notes when open, choice, then primary.',
 'single-column':'All main blocks form one vertical column throughout the fresh full sweep.',
 'full-width-canvas':'The pale component canvas spans the offered width between the host gutters, surrounding the white surface consistently.',
 'collapsed-headings':'The complete closed-state sweep has no visible handling section heading.',
 'collapsed-bodies':'The complete closed-state sweep has no visible handling body paragraphs.',
 'status-rectangle':'The painted status band has straight edges and four visible square corners.',
 'status-no-border':'No stroke border is visible around the solid painted status rectangle.',
 'primary-rectangle':'The painted primary surface has straight edges and four visible square corners.',
 'primary-no-border':'No stroke border is visible around the painted primary surface.',
 'primary-painted-allocation':'The original crop and directed native-boundary guide show paint filling the whole observed rectangular control allocation without an uncovered strip. This does not establish physical touch area.',
 'ink-rectangle':'The solid ink accent is visibly a straight-sided rectangle with square corners.',
 'heading-wrapping':'All eight supplied headings are readable in the overlapping sweep, including headings wrapped over multiple lines, without ellipsis or lost text.',
 'body-wrapping':'All eight supplied body paragraphs are readable across the overlapping sweep through their final lines, without ellipsis or lost text.',
 'title-hierarchy':'The title is visibly larger and more prominent than the semibold handling headings.',
 'expanded-order':'The full sweep shows all eight supplied heading/body pairs in caller order, ending with the paperwork pair before confirmation and primary.'}
logs=[]
for pl in ['ios','android']:
 for case in ['P1','P2']:
  dst=w/f'agent-output/final-self/{pl}/{case}';base=r/f'corpora/u-aad1094f/final-public/{pl}/{case}/native';op=base/'observation.json';obs=json.loads(op.read_text());plan=json.loads((scope/f'compiled/{case}/{pl}/plan.json').read_text());common=['--plan',str(scope/f'compiled/{case}/{pl}/plan.json'),'--design-lock',str(scope/'design-lock.json'),'--design-sha256',a['design_lock_sha256'],'--policy',str(scope/'policy.json'),'--policy-sha256',a['policy_sha256'],'--platform',pl]
  v=subprocess.run(['python3',str(tool),'catalog',*common,'--output',str(dst/'catalog.json')],capture_output=True,text=True);logs.append({'platform':pl,'case':case,'phase':'catalog','exit_code':v.returncode,'stdout':v.stdout,'stderr':v.stderr});assert v.returncode==0
  cat=json.loads((dst/'catalog.json').read_text());state={s['id']:native_checks.bound_state_evidence(obs,s) for s in plan['states']};sub={'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':hashlib.sha256(op.read_bytes()).hexdigest(),'decisions':[]}
  for row in cat['rows']:
   if row['method']!='visual':continue
   found,complete,why,capture=state[row['state']];indices=[i for i,_ in found]
   if row.get('coverage')=='target':
    identifier=row['target']['identifier'];indices=[i for i,s in found if any(n.get('identifier')==identifier and (n.get('fully_within_viewport') is True if pl=='ios' else n.get('fully_visible') is True) for n in s['nodes'])]
   actual=True if indices else None
   reason=reasons[row['requirement_id']] if actual is True else 'No fully visible original target frame was available for this exact post-action state; actual remains unknown.'
   sub['decisions'].append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
  (dst/'submission.json').write_text(json.dumps(sub,indent=2))
  v=subprocess.run(['python3',str(tool),'review',*common,'--observation',str(op),'--submission',str(dst/'submission.json'),'--output',str(dst/'bound-review')],capture_output=True,text=True);logs.append({'platform':pl,'case':case,'phase':'review','exit_code':v.returncode,'stdout':v.stdout,'stderr':v.stderr});print(pl,case,v.returncode,len(sub['decisions']),sum(x['actual'] is None for x in sub['decisions']));assert v.returncode==0,v.stderr
(w/'agent-output/final-self/review-tool-log.json').write_text(json.dumps(logs,indent=2));p=w/'agent-output/final-self/phase.json';phase=json.loads(p.read_text());phase['completedAtUnix']=time.time();phase['limits']=['Qualitative decisions are AI visual judgments on the fresh original evidence, not independent external gold.','All approved full-state sweeps and post-action target images were inspected; native boundary guides supplement original primary crops.','No rendered computed SwiftUI font/color/padding or physical touch area is inferred.','Initial source path mapping failure and common directory-view compatibility recovery remain recorded separately from product findings.','No production edits or extra SDK requests after close.'];p.write_text(json.dumps(phase,indent=2))
