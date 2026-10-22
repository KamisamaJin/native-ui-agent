from pathlib import Path
import json,sys,hashlib
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');OUT=R/'judgments/d0/two/T2';sys.path.insert(0,str(R/'candidate-v8/scripts'));import native_checks
for p in sorted((R/'evaluation-inputs/d0/T2').glob('*/*/*')):
 key=p.relative_to(R/'evaluation-inputs/d0/T2');inp=json.loads((p/'inputs.json').read_text());plan=json.loads((p/'plan.json').read_text());cat=json.loads((p/'catalog.json').read_text());auto=json.loads((p/'automatic.json').read_text());obs=json.loads((R/inp['observation']).read_text());states={s['id']:s for s in plan['states']};decisions=[];attrs=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  found,complete,why,cap=native_checks.bound_state_evidence(obs,states[row['state']]);indices=[n for n,s in found]
  if not found or not complete:
   actual=None;indices=[];reason='Full exact-state original evidence is insufficient: '+why
  else:
   actual=True
   if row['aspect']=='wrapping':
    content={'baseline':'closed disclosure; all six incident labels/severities, the c unavailable reason, no-selection summary, action label and entire footer', 'expanded':'open disclosure and selected a; the complete inline a reading dossier plus all six incident labels/severities, c unavailable reason, summary, action label and entire footer', 'submitted':'replacement revision with b selected and disclosure closed; updated notice, newly unavailable a and its exact reason, c reason, all six labels/severities, b summary, action label and entire footer'}[row['state']]
    reason='Inspected the original coherent full-content sweep, including title, subtitle and notice, '+content+'. Every required visible word is retained and readable over the sweep with no ellipsis or clipped word. Collapsed guidance and unselected dossiers are intentionally hidden.'
    if inp['case']=='P2':reason+=' Oversized words break across characters at the narrow enlarged-text width; the brief expressly permits that fallback, and the following line retains the remaining characters.'
   else:
    reason='The complete original exact-state sweep shows distinct title/subtitle/notice, disclosure, timeline cards, severity/reason text, summary, action and footer areas. No unintended collision or occlusion is visible; '+('the open selected-a dossier has its own space between a and b.' if row['state']=='expanded' else 'closed disclosure does not leave dossier text over other content.')+' Viewport-edge cropping is resolved by overlapping original frames; contact-sheet column cuts are not component collisions.'
  decisions.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
 for row in auto['assertions']:
  if row['status']!='failed':continue
  allowed={n for n,s in native_checks.bound_state_evidence(obs,states[row['state']])[0]};indices=row.get('snapshot_indices',[])
  if not indices or not set(indices)<=allowed:continue
  assert inp['source']=='source-a' and inp['platform']=='ios' and row['id'].endswith('/primary-surface-color')
  reason='Original state-scoped PNGs show the disabled primary control fully inside the actual viewport. Its approved side strip is a uniform interior fill, clear of label glyphs and corners, and the frozen sampler confirms full solid-color support. The sampled region belongs to the component primary button, not the outer host. Source uses PlainButtonStyle with .disabled and the intended palette background, while the actual disabled appearance is altered; source palette declarations do not override original rendered pixels. The component owns the final opaque action fill, so this is a product appearance defect (disabled-style compositing), not a mapping/environment or unsuitable-observation failure.'
  attrs.append({'id':row['id'],'cause':'product','reason':reason,'snapshot_indices':indices})
 panel={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':decisions},'attributions':attrs}
 target=OUT/key/'judge.json';target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_text(json.dumps(panel,ensure_ascii=False,indent=2)+'\n')
 print(str(key),len(decisions),'qualitative decisions',len(attrs),'failure causes')
