#!/usr/bin/env python3
"""Typed native assertions and state-bound coverage; never infer styles from AX."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def same_selector(node, selector):
    value = selector.get('identifier')
    if value is not None and node.get('identifier') != value: return False
    if 'label' in selector and node.get('label') != selector['label']: return False
    if not value and 'label' not in selector: return False
    if 'role' in selector:
        aliases = {'button':9,'switch':40,'other':1,'statictext':48,'text':48}
        role = str(selector['role']).lower()
        if node.get('role_raw') != aliases.get(role) and str(node.get('role','')).lower() != role: return False
    return True


def android_group(snapshot, selector):
    nodes = snapshot.get('nodes',[]); found = [n for n in nodes if same_selector(n,selector)]
    if len(found)!=1: return {'resolution':'missing'if not found else'ambiguous_semantic','match_count':len(found),'selector':selector}
    semantic=found[0]; by_id={n.get('node_id'):n for n in nodes}; descendants=[]
    for node in nodes:
        cursor=node;visited=set()
        while cursor.get('parent_id') in by_id and cursor['parent_id'] not in visited:
            visited.add(cursor['parent_id']);cursor=by_id[cursor['parent_id']]
            if cursor is semantic:
                descendants.append(node);break
    clickable=[n for n in [semantic]+descendants if n.get('clickable')]
    # Each actual OnClick may be independently activatable, including a parent
    # with a clickable child. More than one requires a narrower selector.
    leaves=clickable
    return {'selector':selector,'semantic':semantic,'match_count':1,'native_control_count':len(leaves),'candidates':leaves,
            'resolution':'unique_native_control'if len(leaves)==1 else'ambiguous_native_controls'if leaves else'no_native_control',
            **({'control':leaves[0]}if len(leaves)==1 else{})}


def resolve(snapshot, selector, platform):
    if platform=='android': group=android_group(snapshot,selector)
    else:
        groups=[g for g in snapshot.get('control_groups',[])if g.get('selector')==selector]
        if len(groups)==1:group=groups[0]
        else:
            # Raw labels/presence can be read, but absence of native ancestry never
            # licenses a spatially guessed activation target.
            found=[n for n in snapshot.get('nodes',[])if same_selector(n,selector)]
            group={'selector':selector,'match_count':len(found),'resolution':'native_relation_unavailable'}
            if len(found)==1:group['semantic']=found[0]
    semantic=group.get('semantic',{});control=group.get('control',{})
    facts={'present':group.get('match_count',0)>0,'unique':group.get('match_count')==1}
    if semantic:
        facts['label']=semantic.get('label','');facts['semantic_role']=semantic.get('role');facts['semantic_selected']=semantic.get('selected')
    if group.get('resolution')=='unique_native_control' and control:
        facts['enabled']=control.get('enabled')
        facts['selected']=bool(semantic.get('selected') or control.get('selected'))
        facts['selection_sources']={'semantic_selected':semantic.get('selected'),'control_selected':control.get('selected')}
        facts['control_role']={9:'button',40:'switch',1:'other',48:'text'}.get(control.get('role_raw'),str(control.get('role','')).lower());facts['value']=control.get('value',control.get('toggle_state'))
        if facts['value']in ('0','Off','off'):facts['value']=False
        elif facts['value']in ('1','On','on'):facts['value']=True
        facts['hittable']=control.get('hittable',control.get('intersects_viewport'))
        frame=control.get('frame')
        if frame:
            facts['ax_width']=frame['width'];facts['ax_height']=frame['height']
        bounds=control.get('touch_bounds_dp')if platform=='android'else None
        if bounds:
            facts['touch_width']=bounds[2]-bounds[0];facts['touch_height']=bounds[3]-bounds[1]
    return {'resolution':group.get('resolution'),'facts':facts,'semantic':semantic,'control':control,
            'scope':'Native ancestry/control facts; selected trait may be on compound semantic container. AX bounds are not physical hit regions.'}


def validate_plan(plan):
    if plan.get('version')!=1 or not plan.get('states')or not isinstance(plan.get('assertions'),list)or not plan['assertions']:
        raise ValueError('Nonempty version1 states and atomic assertions required')
    states={};ids=set()
    for state in plan['states']:
        if not isinstance(state.get('id'),str)or state['id']in states:raise ValueError('Unique state IDs required')
        if not isinstance(state.get('input_index'),int):raise ValueError('Every state requires explicit input_index')
        if state.get('coverage','full_content')not in {'full_content','target'}:raise ValueError('Known state coverage scope required')
        states[state['id']]=state
    for item in plan['assertions']:
        if not item.get('id')or item['id']in ids:raise ValueError('Unique assertion IDs required')
        if item.get('state')not in states:raise ValueError('Assertion references unknown state')
        if item.get('kind')not in {'control','event','manual','text_layout'}:raise ValueError('Unknown assertion kind')
        if item.get('coverage','full_content')not in {'full_content','target'}:raise ValueError('Known coverage scope required')
        if item['kind']=='manual'and not set(item.get('allowed_methods',['visual']))<={'visual','native_pixels'}:raise ValueError('Manual review is visual/pixel interpretation, not native runtime facts')
        ids.add(item['id'])
    # Independent contract IDs catch plan omissions when a frozen contract exists.
    if 'required_assertion_ids'in plan and set(plan['required_assertion_ids'])!=ids:
        raise ValueError('Plan does not exactly cover frozen required assertion IDs')
    return states


def compare(actual, expected, op):
    if op=='eq':return actual==expected and (isinstance(actual,bool)==isinstance(expected,bool))
    if op=='contains':return isinstance(actual,str)and isinstance(expected,str)and expected in actual
    if op=='gte':return isinstance(actual,(int,float))and not isinstance(actual,bool)and actual>=expected
    if op=='lte':return isinstance(actual,(int,float))and not isinstance(actual,bool)and actual<=expected
    raise ValueError('Unknown comparison operator')


def state_evidence(observation,state):
    captures=[c for c in observation.get('state_captures',[])if c.get('state_id')==state['id']]
    if not captures and state.get('coverage')=='target':
        index=state.get('after_action');steps=observation.get('steps',[])
        if not isinstance(index,int)or not 0<=index<len(steps):return [],False,'missing native action checkpoint',None
        step=steps[index];snap_index=step.get('after',step.get('snapshot'));snapshots=observation.get('snapshots',[])
        if not isinstance(snap_index,int)or not 0<=snap_index<len(snapshots):return [],False,'invalid native action snapshot',None
        snapshot=snapshots[snap_index];binding=step.get('binding_after')
        if step.get('state_id')!=state['id']or snapshot.get('state_id')!=state['id']or not binding or snapshot.get('binding')!=binding:
            return [],False,'action checkpoint state/binding mismatch',None
        if binding.get('fixture_index',binding.get('input_index'))!=state['input_index']:return [],False,'action checkpoint has different input',None
        capture={'state_id':state['id'],'binding':binding,'snapshot_indices':[snap_index],'after_action':index,'source':'native_action_checkpoint','scope':'target_only'}
        return [(snap_index,snapshot)],False,'native action checkpoint; no full-content coverage claim',capture
    if len(captures)!=1:return [],False,'missing or duplicate state capture',None
    capture=captures[0];binding=capture.get('binding',{})
    actual_index=binding.get('fixture_index',binding.get('input_index'))
    if actual_index!=state['input_index']:return [],False,'state is bound to different caller input',capture
    if 'after_action'in state and capture.get('after_action')!=state['after_action']:
        return [],False,'state is bound to different action checkpoint',capture
    snapshots=observation.get('snapshots',[]);indices=capture.get('snapshot_indices',[])
    if not indices or any(not isinstance(i,int)or i<0 or i>=len(snapshots)for i in indices):return [],False,'invalid state snapshot indices',capture
    found=[(i,snapshots[i])for i in indices]
    if any(s.get('binding')!=binding for _,s in found):return [],False,'snapshot binding drift',capture
    # Recompute geometry coverage; the producer's complete:true alone is not proof.
    intervals=[];heights=[]
    for _,snapshot in found:
        runtime=snapshot.get('runtime',{});content=runtime.get('content_frame');vp=snapshot.get('viewport')
        if content and vp:
            h=content['height'];offset=vp['y']-content['y'];heights.append(h);intervals.append((max(0,offset),min(h,offset+vp['height'])))
        elif 'scroll_offset_dp'in snapshot:
            offset=snapshot['scroll_offset_dp'];h=snapshot['scroll_max_dp']+snapshot['viewport_height_dp'];heights.append(h);intervals.append((offset,min(h,offset+snapshot['viewport_height_dp'])))
    end=0;gap=0
    for a,b in sorted(intervals):gap=max(gap,a-end);end=max(end,b)
    complete=bool(intervals)and max(heights)-min(heights)<=1 and gap<=1 and end>=max(heights)-1 and capture.get('top_reached')is True and capture.get('bottom_reached')is True and capture.get('stable_binding')is True
    return found,complete,'native interval union complete'if complete else'incomplete per-state interval union',capture


def evaluate(plan, observation, platform, manual=None, root=None, observation_sha256=None):
    states=validate_plan(plan);manual=manual or {'decisions':[]};decisions={}
    if manual.get('decisions') and (not observation_sha256 or manual.get('observation_sha256')!=observation_sha256):raise ValueError('Manual review is not bound to this observation')
    for row in manual.get('decisions',[]):
        if row.get('id')in decisions:raise ValueError('Duplicate manual decision')
        decisions[row.get('id')]=row
    unknown=set(decisions)-{a['id']for a in plan['assertions']if a['kind']=='manual'}
    if unknown:raise ValueError('Unplanned manual decisions')
    evidence={sid:state_evidence(observation,spec)for sid,spec in states.items()};rows=[]
    for item in plan['assertions']:
        found,complete,why,capture=evidence[item['state']];status='unassessed';actual=None;reason=why;used=[]
        if found:
            kind=item['kind']
            if kind=='control':
                values=[]
                for index,snapshot in found:
                    resolved=resolve(snapshot,item['target'],platform);facts=resolved['facts'];prop=item['property']
                    semantic=resolved['semantic'];visible=semantic.get('intersects_viewport',False)
                    if prop in {'present','unique'}:
                        if facts.get('unique') and visible:values.append((index,facts[prop],resolved))
                        elif complete and not facts.get('present'):values.append((index,False,resolved))
                        elif facts.get('present')and not facts.get('unique'):values.append((index,facts[prop],resolved))
                    elif prop=='label' and visible and facts.get('unique'):values.append((index,facts.get('label'),resolved))
                    elif visible and resolved['resolution']=='unique_native_control'and prop in facts and facts[prop]is not None:
                        values.append((index,facts[prop],resolved))
                if values:
                    actual=[{'snapshot':i,'value':v,'resolution':r}for i,v,r in values];used=[i for i,_,_ in values]
                    checks=[compare(v,item['expected'],item.get('op','eq'))for _,v,_ in values]
                    # Conflicting real values inside one immutable epoch remain unknown.
                    if all(checks):status='passed';reason='typed native property matches expected'
                    elif not any(checks):status='failed';reason='typed native property contradicts expected'
                    else:reason='native values conflict within state; inspect changing UI or capture drift'
                else:reason='native property unavailable, target not observed, or ancestry ambiguous'
            elif kind=='event':
                index=item['action_index'];steps=observation.get('steps',[])
                if 0<=index<len(steps):
                    step=steps[index];actual=step.get('callback_delta');execution=step.get('outcome',step.get('execution'))
                    after=step.get('binding_after',{})
                    index_ok=after==capture.get('binding')
                    if execution in {'tapped','blocked_disabled','observed'}and actual is not None and index_ok:
                        events=[v.get('event')if isinstance(v,dict)else v for v in actual]
                        status='passed'if events==item['expected']else'failed';actual=events;reason='actual executed native callback delta'
                    else:reason='action not executed or wrong input binding; zero callbacks are not a product failure'
            elif kind=='text_layout':
                values=[]
                for index,snapshot in found:
                    matched=[n for n in snapshot.get('nodes',[])if same_selector(n,item['target'])]
                    if len(matched)==1 and matched[0].get('intersects_viewport')and item['property']in matched[0]:
                        values.append((index,matched[0][item['property']]))
                if values:
                    actual=[v for _,v in values];used=[i for i,_ in values];result=[compare(v,item['expected'],item.get('op','eq'))for _,v in values]
                    if all(result):status='passed';reason='native text layout result'
                    elif not any(result):status='failed';reason='native text layout contradiction'
                    else:reason='conflicting native layout values'
            elif kind=='manual':
                row=decisions.get(item['id']);actual=row
                if row:
                    indices=row.get('snapshot_indices',[]);allowed={i for i,_ in found};method=row.get('method')
                    valid=bool(indices)and set(indices)<=allowed and bool(row.get('reason'))and method in item.get('allowed_methods',['visual'])and bool(row.get('evidence'))and root is not None
                    if valid and root:
                        expected_images={(root/observation['snapshots'][i]['screenshot']).resolve()for i in indices}
                        declared={(root/ref['path']).resolve()for ref in row.get('evidence',[])}
                        if not expected_images<=declared:raise ValueError('Manual review lacks actual state screenshot artifacts')
                        for ref in row.get('evidence',[]):
                            path=(root/ref['path']).resolve()
                            if not path.is_relative_to(root.resolve())or not path.is_file()or sha(path)!=ref.get('sha256'):raise ValueError('Manual artifact missing, outside root, or changed')
                    if valid and row.get('status')in {'passed','failed'}:
                        if row['status']=='failed'or item.get('coverage','full_content')!='full_content'or complete:
                            status=row['status'];used=indices;reason=row['reason']
                        else:reason='manual pass withheld: this input state lacks full-content coverage'
                    else:reason='missing scoped manual method, snapshots or rationale'
        rows.append({'id':item['id'],'state':item['state'],'status':status,'actual':actual,'reason':reason,'snapshot_indices':sorted(set(used))})
    counts={s:sum(row['status']==s for row in rows)for s in ['passed','failed','unassessed']}
    return {'schema_version':1,'status':'failed'if counts['failed']else'needs_review'if counts['unassessed']else'passed',
            'coverage_contract':'required_id_set'if 'required_assertion_ids'in plan else'supplied_plan_only','complete_requirements_claim':bool(plan.get('required_assertion_ids'))and not counts['failed']and not counts['unassessed'],'assertions':rows,'counts':counts,'states':{k:{'complete':v[1],'reason':v[2],'binding':v[3].get('binding')if v[3]else None}for k,v in evidence.items()},
            'limits':'Native facts are typed and state-bound. Manual visual meaning remains reviewer judgment. AX dimensions do not establish internal padding/fonts/colors or complete physical hit regions.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--observation',type=Path,required=True);p.add_argument('--platform',choices=['ios','android'],required=True);p.add_argument('--manual',type=Path);p.add_argument('--root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Fresh output required')
    report=evaluate(read(a.plan),read(a.observation),a.platform,read(a.manual)if a.manual else None,a.root or a.observation.parent,sha(a.observation))
    report['input_hashes']={'plan':sha(a.plan),'observation':sha(a.observation),**({'manual':sha(a.manual)}if a.manual else{})}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':report['status'],'counts':report['counts']}));return 1 if report['status']=='failed'else 3 if report['status']=='needs_review'else 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError)as e:print('Invalid native assertion evidence: '+str(e),file=sys.stderr);raise SystemExit(2)
