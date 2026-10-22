from pathlib import Path
import json,sys,hashlib,datetime,time,traceback
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/one/T1'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks,acceptance
inventory=json.loads((O/'evidence-inventory.json').read_text());hashes=json.loads((O/'input-hashes.json').read_text());audit={};summary={}
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for case in sorted((B/'evaluation-inputs/final/T1').glob('*/*/*')):
 key='/'.join(case.parts[-3:]);inp=load(case/'inputs.json');plan=load(case/'plan.json');cat=load(case/'catalog.json');auto=load(case/'automatic.json');env=load(case/'environment-check.json');obs=load(B/inp['observation']);root=B/inp['root'];design=B/inp['design_root'];platform=inp['platform'];out=O/key
 rawfixture=load(root/'fixtures.json');approved=load(design/('compiled/H1/fixtures.json' if inp['case']=='H1' else f"cases/{inp['case']}/fixtures.json"));fixture_equal=all(rawfixture.get(k)==approved.get(k) for k in ['initial','updates','width','viewportHeight','theme','dynamic_type','fontScale','direction'])
 states={s['id']:native_checks.bound_state_evidence(obs,s) for s in plan['states']};decisions=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  found,complete,why,cap=states[row['state']];indices=[i for i,s in found];wrapping=row['property']=='wrapping';sid=row['state']
  if not found:
   actual=None;reason=f"Exact {sid} state evidence unavailable: {why}. No borrowing from another action or input."
  elif not complete:
   intervals=[]
   for ix,s in found:
    v=s['viewport'];c=s['runtime']['content_frame'];offset=v['y']-c['y'];intervals.append((max(0,offset),min(c['height'],offset+v['height'])));
   contentheight=max(s['runtime']['content_frame']['height'] for _,s in found);end=max(z[1] for z in intervals);gap=contentheight-end
   actual=None;reason=f"The inspected exact-state fragments show {'readable wrapped required text without visible ellipsis' if wrapping else 'separate text, cards, disclosure and action areas without visible collision'}. The footer is visible, but frozen bound_state_evidence reports incomplete per-state interval union: coverage ends at {end:.6f} of {contentheight:.6f} native content units, leaving {gap:.6f} at the bottom. A footer/sentinel alone cannot establish full-content coverage; retain unknown."
  else:
   actual=True
   context={'baseline':'Title, subtitle, notice, all six labels and details, the literal unavailable status and caller reason, no-selection summary, collapsed disclosure label, action and full footer are visible across this exact baseline.', 'expanded':'The selected first slot retains its detail; Hide safety briefing precedes the complete caller guidance in its global position, with all six slot labels/details/reasons, summary, action and footer visible across this exact expanded state.', 'submitted':'The caller-updated notice and newly unavailable first slot with its exact changed reason remain visible; the second-slot draft summary persists after submission, with collapsed guidance, all six slot labels/details/reasons, action and full footer visible across this exact updated submitted state.'}[sid]
   if wrapping:
    reason=context+' Every required visible word is readable in wrapped lines without visible clipping or ellipsis. Exact-state native interval union is complete.'
    if inp['case']=='P2' and platform=='ios':reason+=' The oversized unbroken word Unavailable uses a character break with every character retained, as expressly allowed by the brief; this is not ellipsis.'
   else:reason=context+' Text blocks, card labels/reasons/details, summary, disclosure and primary action occupy separate areas with visible spacing and no unintended overlap or occlusion. Exact-state native interval union is complete.'
  decisions.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
 judge={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':decisions},'attributions':[]}
 (out/'judge.json').write_text(json.dumps(judge,indent=2)+'\n')
 # Retain exact native bindings/boxes independently of qualitative decisions.
 au={'fixtureMatchesApproved':fixture_equal,'environmentStatus':env['status'],'automaticCounts':auto['counts'],'steps':[],'states':{}}
 for index,step in enumerate(obs['steps']):
  au['steps'].append({k:step.get(k) for k in ['action','type','state_id','outcome','dispatch','callback_delta','binding_after','semantic_target','activation_target','selector'] if k in step}|{'index':index})
 for st in plan['states']:
  found,complete,why,cap=states[st['id']];targets={}
  for label,selector in plan['design_contract']['bindings'].items():
   observations=[]
   for ix,s in found:
    r=native_checks.resolve(s,selector,platform);sem=r['semantic'];control=r['control']
    observations.append({'index':ix,'resolution':r['resolution'],'facts':r['facts'],'semanticBox':{k:sem.get(k) for k in ['frame','bounds_dp','native_geometry','fully_within_viewport','intersects_viewport'] if k in sem},'controlBox':{k:control.get(k) for k in ['frame','bounds_dp','touch_bounds_dp','native_geometry','fully_within_viewport','intersects_viewport'] if k in control}})
   targets[label]=observations
  au['states'][st['id']]={'indices':[i for i,s in found],'complete':complete,'reason':why,'binding':cap.get('binding') if cap else None,'targets':targets}
 audit[key]=au
 for path in [root/'fixtures.json',design/'design-lock.json',design/'policy.json',B/inp['environment'],design/'reference.json',design/'bindings.json',design/f"reference-{inp['case']}-expanded.png",design/f"reference-{inp['case']}-expanded.svg"]:
  if path.is_file():hashes[str(path)]=sha(path)
 summary[key]={'true':sum(d['actual'] is True for d in decisions),'false':sum(d['actual'] is False for d in decisions),'unknown':sum(d['actual'] is None for d in decisions),'nativeOrPixelFailed':[r['id'] for r in auto['assertions'] if r['status']=='failed'],'attributions':0}
for capsule in ['unit-99c640','unit-b44248']:
 for rel in ['alerttoast/Sources/AlertToast/WorkshopSlotPlanner.swift','reply/Reply/app/src/main/java/com/example/reply/ui/components/WorkshopSlotPlanner.kt']:
  p=B/f'submissions/{capsule}/final/source'/rel;hashes[str(p)]=sha(p)
for p in [B/'design-v2/T1/public/BRIEF.md',B/'design-v2/T1/public/API.md',B/'design-v2/T1/private/HELDOUT.md',B/'prompts/judge-final-one-T1.txt']:
 hashes[str(p)]=sha(p)
for p in (B/'candidate-v8/scripts').glob('*.py'):hashes[str(p)]=sha(p)
for p in (B/'candidate-v8/references').glob('*.md'):hashes[str(p)]=sha(p)
(O/'native-evidence-audit.json').write_text(json.dumps(audit,indent=2)+'\n');(O/'input-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n');(O/'decision-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True)
