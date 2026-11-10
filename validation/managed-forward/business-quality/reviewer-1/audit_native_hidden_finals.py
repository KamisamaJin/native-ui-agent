from pathlib import Path
from fractions import Fraction
import json,hashlib,collections
P=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/packet-public');O=P.parent/'reviewer-1'
res=[]
for arm in ['A','B']:
 for stage in ['Final']:
  for plat in ['ios','android']:
   cohort=f'{arm}/hidden/Final/{plat}';b=P.parent/'packet-hidden-finals'/arm/plat;obs=json.loads((b/'native/observation.json').read_text());auto=json.loads((b/'automatic.json').read_text());plan=json.loads((P/f'design/private/compiled/evening-service/{plat}/plan.json').read_text());byid={a['id']:a for a in auto['assertions']};rows=[]
   for a in plan['assertions']:
    if a['kind'] not in ['control','geometry','event']:continue
    ar=byid[a['id']];error=[];values=[];citations=[]
    if a['kind']=='control':
     for v in ar.get('actual',[]):
      ix=v['snapshot'];s=obs['snapshots'][ix];rn=v['resolution'];sem=rn.get('semantic',{});con=rn.get('control',{});facts=rn.get('facts',{})
      for name,n in [('semantic',sem),('control',con)]:
       if not n:continue
       key='index' if plat=='ios' else 'node_id';match=[x for x in s['nodes'] if x.get(key)==n.get(key)]
       if len(match)!=1:error.append(f'{ix} {name} raw node missing/nonunique');continue
       for k,x in n.items():
        if k in match[0] and match[0][k]!=x:error.append(f'{ix} {name} raw mismatch {k}')
      if sem.get('identifier')!=a['target']['identifier']:error.append(f'{ix} wrong semantic target')
      prop=a['property']
      if prop=='label':val=sem.get('label')
      elif prop=='enabled':val=con.get('enabled') if con else sem.get('enabled')
      elif prop=='selected':val=bool(sem.get('selected') or con.get('selected'))
      elif prop=='value':
       raw=(con or sem).get('value') if plat=='ios' else (con or sem).get('toggle_state');val=True if raw in ['1','on','On',True] else False if raw in ['0','off','Off',False] else None
      else:val=None;error.append('unknown property')
      if val!=v['value']:error.append(f'{ix} rederived value differs from automatic')
      values.append(val);citations.append({'observation_snapshot':ix,'native_semantic_index':sem.get('index',sem.get('node_id')),'native_control_index':con.get('index',con.get('node_id'))})
     if not values:error.append('no actuals')
     if any(v!=a['expected'] for v in values):error.append('independent fixed expected mismatch')
    elif a['kind']=='geometry':
     for e in ar.get('geometry_evidence',[]):
      src=e['sources'][0];s=src['sample'];v=Fraction(str(s['height'])) if plat=='ios' else Fraction(s['size_px'][1])/Fraction(str(s['density']));values.append(float(v))
      if v<Fraction(str(a['expected'])):error.append('below exact approved minimum')
      if float(v)!=e['value']:error.append('automatic geometry differs from exact sample')
      citations.append({'observation_snapshot':e['snapshot'],'native_provider':src['provider'],'native_sample':s})
     if not values:error.append('no geometry samples')
    else:
     ps=next(s for s in plan['states'] if s['id']==a['state']);step=obs['steps'][ps['after_action']];raw_delta=step.get('callback_delta');val=[x['event'] if isinstance(x,dict) else x for x in raw_delta];values=val
     if val!=a['expected']:error.append('callback delta differs from fixed interval expected')
     method='caller_fixture_update' if a['requirement_id']=='update-event' else 'xcui_tap' if plat=='ios' else 'compose_onclick'
     if not step['dispatch'].get('succeeded') or step['dispatch'].get('method')!=method:error.append('requested stimulus not demonstrated')
     citations=[{'step_index':ps['after_action'],'raw_callback_delta':raw_delta,'method':step['dispatch'].get('method'),'binding_before':step['dispatch'].get('binding_before'),'binding_after':step.get('binding_after')}]
    rows.append({'assertion_id':a['id'],'kind':a['kind'],'observed_values':values,'status':'P' if not error else 'U','errors':error,'citations':citations})
   captures=[]
   for st in plan['states']:
    c=next(x for x in obs['state_captures'] if x['state_id']==st['id']);snap=[obs['snapshots'][ix] for ix in c['snapshot_indices']];captures.append({'state':st['id'],'complete':c.get('complete'),'stable_binding':c.get('stable_binding'),'snapshot_indices':c['snapshot_indices'],'all_capture_consistent':all(x.get('capture_consistent') for x in snap),'same_instance_through_captures':len({x['binding']['instance'] for x in snap})==1})
   result={'cohort':cohort,'typed_required':len(rows),'counts':dict(collections.Counter(r['status'] for r in rows)),'errors':[r for r in rows if r['status']!='P'],'observation_sha256':hashlib.sha256((b/'native/observation.json').read_bytes()).hexdigest(),'plan_sha256_file':hashlib.sha256((P/f'design/private/compiled/evening-service/{plat}/plan.json').read_bytes()).hexdigest(),'captures':captures,'typed_actuals':rows};res.append(result);print(cohort,result['counts'],result['errors'][:1])
(O/'hidden-finals-native-independent-audit.json').write_text(json.dumps(res,indent=2)+'\n')
