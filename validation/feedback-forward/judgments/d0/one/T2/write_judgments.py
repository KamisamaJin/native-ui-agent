from pathlib import Path
import json,sys,hashlib,time
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');OUT=BASE/'judgments/d0/one/T2'
sys.dont_write_bytecode=True;sys.path.insert(0,str(BASE/'candidate-v9/scripts'))
import native_checks
manifest=json.loads((OUT/'evidence-manifest.json').read_text())
REASONS={
 'title-wrapping':'The complete supplied current title is readable across its natural wrapped lines, with no ellipsis or truncated last line.',
 'subtitle-wrapping':'The complete current language/collection and supplied MB subtitle is visible, naturally wrapping where needed and with no ellipsis.',
 'status-wrapping':'The full current status string is readable in the band; narrow ready/requested strings wrap onto two lines without loss.',
 'disclosure-wrapping':'The complete current Review chapters or Hide chapters label is visible without clipping or ellipsis.',
 'choice-wrapping':'The visible words Wi-Fi only are complete beside the decorative selected/unselected square. The separate recorded native-label discrepancy is not a visible wrapping failure.',
 'primary-wrapping':'The full Get audio or Requested label is readable within the painted primary surface without truncation.',
 'horizontal-clipping':'Across the complete state sweep, all component text and painted blocks remain within its horizontal canvas/surface bounds. Viewport-edge cuts during vertical scrolling are restored in overlapping frames.',
 'row-overlap':'Across the complete state sweep, successive text rows, chapter pairs and controls remain visually separated without overlap.',
 'flow-order':'The complete state sweep shows ink accent, title, subtitle, status, disclosure, expanded material when open, choice and primary in that reading order.',
 'single-column':'The complete state sweep shows the main blocks in one vertical column.',
 'full-width-canvas':'The pale component canvas reaches both offered edges inside the host gutters; the white surface is inset within it. Native component bounds and original viewport pixels agree on this extent.',
 'collapsed-headings':'The complete closed-state sweep contains no chapter section headings between disclosure and choice.',
 'collapsed-bodies':'The complete closed-state sweep contains no chapter body paragraphs between disclosure and choice.',
 'status-rectangle':'The fully visible status band has straight sides and four square painted corners.',
 'status-no-border':'The fully visible status band has a continuous fill with no visible border stroke.',
 'primary-rectangle':'The fully visible primary painted surface has straight sides and four square corners.',
 'primary-no-border':'The fully visible primary painted surface has no visible perimeter border stroke.',
 'primary-painted-allocation':'The original visible primary fill reaches the four edges of its mapped rectangular native Button allocation; no uncovered strip is visible. This does not establish physical hit bounds.',
 'ink-rectangle':'The original top-of-content frame shows a solid narrow ink rectangle with four square corners.',
 'heading-wrapping':'All eight expanded supplied chapter headings are readable through the overlapping full state sweep, wrapping naturally without ellipsis or truncated text.',
 'body-wrapping':'All eight supplied chapter paragraphs are readable in full through overlapping sweep frames; their starts, continuing lines and endings wrap without ellipsis or horizontal loss.',
 'title-hierarchy':'The title has visibly larger, heavier type and stronger prominence than the expanded chapter headings in this actual state.',
 'expanded-order':'The complete expanded sweep shows all eight supplied heading/body pairs in caller order, from the first harbor/textile chapter through the final waterfront/contemporary-makers chapter.'}
global_keys={'horizontal-clipping','row-overlap','flow-order','single-column','full-width-canvas','collapsed-headings','collapsed-bodies','heading-wrapping','body-wrapping','title-hierarchy','expanded-order'}
for p in sorted((BASE/'evaluation-inputs/d0/T2').glob('*/*/*')):
 inp=json.loads((p/'inputs.json').read_text());cat=json.loads((p/'catalog.json').read_text());plan=json.loads((p/'plan.json').read_text());obs=json.loads((BASE/inp['observation']).read_text());auto=json.loads((p/'automatic.json').read_text());platform,case=p.parts[-2:];states={s['id']:s for s in plan['states']};dec=[];attrs=[]
 for row in cat['rows']:
  if row.get('method')!='visual':continue
  key=row['requirement_id'];found,complete,why,_=native_checks.bound_state_evidence(obs,states[row['state']]);indices=[i for i,_ in found]
  if key not in global_keys:
   eligible=[]
   for i,snap in found:
    resolved=native_checks.resolve(snap,row['target'],platform);node=resolved.get('semantic',{})
    if resolved['facts'].get('unique') and node.get('fully_within_viewport',node.get('fully_visible',False)):eligible.append(i)
   indices=eligible[:1]
  if key=='title-hierarchy':indices=[i for i,_ in found] # compare actual top and headings, not source font tokens
  known=bool(indices) and (key not in global_keys or complete)
  dec.append({'review_id':row['review_id'],'actual':True if known else None,'reason':REASONS[key] if known else 'The selected-state original frames do not establish the entire approved proposition; no other state or source rendering is substituted.','snapshot_indices':indices if known else []})
 for row in auto['assertions']:
  if row['status']=='failed':
   attrs.append({'id':row['id'],'cause':'uncertain','reason':'The coherent original frame records audio.choice label as “✓, Wi-Fi only” while the visible wording is complete. The frozen Android observer walks unmerged descendants and synthesizes its label by concatenating native Text (NativeObserverTest.kt lines 88–89 and 137); production source lines 199–208 clears semantics on the decorative Box. The raw strict label failure is retained. These inputs do not export the merged accessibility-service label, so they do not resolve observation aggregation versus an actual component accessibility-label defect. Host gutters and paint sampling do not explain this text discrepancy.','snapshot_indices':row['snapshot_indices']})
 dest=OUT/'initial'/platform/case/'judge.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps({'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':dec},'attributions':attrs},indent=2,ensure_ascii=False)+'\n')
 print(platform,case,'visual',len(dec),'known',sum(d['actual']is not None for d in dec),'null',sum(d['actual']is None for d in dec),'strict attributions',len(attrs))
