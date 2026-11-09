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
        native_text = role in {'text','statictext'} and bool(node.get('native_text')) and not node.get('role')
        if node.get('role_raw') != aliases.get(role) and str(node.get('role','')).lower() != role and not native_text: return False
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
        if type(state.get('input_index'))is not int or state['input_index']<0:raise ValueError('Every state requires explicit nonnegative input_index')
        if state.get('coverage','full_content')not in {'full_content','target','targets'}:raise ValueError('Known state coverage scope required')
        states[state['id']]=state
    for item in plan['assertions']:
        if not item.get('id')or item['id']in ids:raise ValueError('Unique assertion IDs required')
        if item.get('state')not in states:raise ValueError('Assertion references unknown state')
        if item.get('kind')not in {'control','event','manual','text_layout','geometry'}:raise ValueError('Unknown assertion kind')
        if item['kind']in {'control','text_layout','geometry'}:
            target=item.get('target',{})
            if not isinstance(target,dict)or sum(isinstance(target.get(k),str)and bool(target[k])for k in ['identifier','label'])!=1:
                raise ValueError('Typed assertion needs one exact native target')
            if not isinstance(item.get('property'),str)or not item['property']or 'expected'not in item:
                raise ValueError('Typed assertion needs property and explicit expectation')
            if item.get('op','eq')not in {'eq','contains','gte','lte','near'}:raise ValueError('Known comparison operator required')
            if item.get('op')in {'gte','lte'}and(type(item['expected'])not in {int,float}):raise ValueError('Numeric bounds require numeric expectations')
            if item.get('op')=='near':
                import math
                if any(type(item.get(k))not in {int,float}or not math.isfinite(item[k])for k in ['expected','tolerance'])or item['tolerance']<0:raise ValueError('Near needs finite numerical expected and nonnegative tolerance')
            if item['kind']=='geometry':
                from design_contract import GEOMETRY
                from observation_contract import validate_selector
                if item['property']not in GEOMETRY or item.get('basis','semantic')not in {'semantic','control'}:raise ValueError('Explicit native-bound geometry required')
                if item['property']not in {'width','height'}:validate_selector(item.get('reference_target'))
        if item.get('coverage','full_content')not in {'full_content','target'}:raise ValueError('Known coverage scope required')
        if item['kind']=='manual'and not set(item.get('allowed_methods',['visual']))<={'visual','native_pixels'}:raise ValueError('Manual review is visual/pixel interpretation, not native runtime facts')
        if item['kind']=='event':
            if type(item.get('action_index')) is not int or item['action_index'] < 0 or not isinstance(item.get('expected'), list):
                raise ValueError('Callback assertion requires explicit nonnegative action_index and expected event list')
            if item.get('stimulus','activation') not in {'activation','caller_update'}:
                raise ValueError('Callback assertion must name activation or caller_update')
        ids.add(item['id'])
    # Independent contract IDs catch plan omissions when a frozen contract exists.
    if 'required_assertion_ids'in plan and set(plan['required_assertion_ids'])!=ids:
        raise ValueError('Plan does not exactly cover frozen required assertion IDs')
    return states


def compare(actual, expected, op, tolerance=None):
    if op=='eq':return actual==expected and (isinstance(actual,bool)==isinstance(expected,bool))
    if op=='contains':return isinstance(actual,str)and isinstance(expected,str)and expected in actual
    if op=='gte':return isinstance(actual,(int,float))and not isinstance(actual,bool)and actual>=expected
    if op=='lte':return isinstance(actual,(int,float))and not isinstance(actual,bool)and actual<=expected
    if op=='near':return type(actual)in {int,float}and abs(actual-expected)<=tolerance
    raise ValueError('Unknown comparison operator')


def callback_verdict(step, expected, platform, required_method=None, stimulus='activation'):
    """Behavior verdict, not a literal empty-interval comparison.

    Exported for evaluators so an independent grade cannot bypass the same
    successful-stimulus precondition used by the shipped assertion runner.
    """
    delta = step.get('callback_delta')
    events = [v.get('event') if isinstance(v, dict) else v for v in delta] if isinstance(delta, list) else None
    result = {'status': 'unassessed', 'reason': 'native stimulus not established',
              'interval_facts': events, 'stimulus_established': False}
    proof = step.get('dispatch', {})
    if stimulus not in {'activation', 'caller_update'}:
        raise ValueError('Callback behavior requires activation or caller_update stimulus')
    method = required_method or ('caller_fixture_update' if stimulus == 'caller_update'
                                 else 'xcui_tap' if platform == 'ios' else 'compose_onclick')
    result.update(required_method=method, actual_method=proof.get('method'))
    if proof.get('attempted') is not True or proof.get('succeeded') is not True:
        result['reason'] = 'no demonstrated successful native dispatch; interval facts are not behavior'
        return result
    if proof.get('method') != method or proof.get('stimulus') != stimulus:
        result['reason'] = 'actual native stimulus/method differs from required method'
        return result
    before, after = proof.get('binding_before', {}), step.get('binding_after', {})
    index = lambda value: value.get('fixture_index', value.get('input_index'))
    if (not before.get('instance') or before.get('instance') != after.get('instance')
            or ('pid' in before and before.get('pid') != after.get('pid'))
            or (platform == 'ios' and (type(before.get('pid')) is not int or before['pid'] <= 0))
            or not isinstance(index(before), int) or isinstance(index(before), bool)
            or not isinstance(index(after), int) or isinstance(index(after), bool)
            or not before.get('input_sha256') or not after.get('input_sha256')):
        result['reason'] = 'native stimulus lacks same-process/input provenance'
        return result
    if stimulus == 'activation':
        if (step.get('outcome') != 'tapped' or proof.get('matches') != 1
                or proof.get('native_controls') != 1 or proof.get('enabled') is not True
                or type(proof.get('matches')) is not int or type(proof.get('native_controls')) is not int
                or index(before) != index(after) or before['input_sha256'] != after['input_sha256']):
            result['reason'] = 'activation not uniquely dispatched in one caller-input epoch'
            return result
    elif index(after) != index(before) + 1 or step.get('outcome') != 'updated':
        result['reason'] = 'caller replacement did not demonstrably advance one input'
        return result
    start, end = before.get('event_revision'), after.get('event_revision')
    if (events is None or type(start) is not int or type(end) is not int
            or end < start or end - start != len(events)
            or proof.get('event_start') != start or proof.get('event_end') != end):
        result['reason'] = 'callback interval does not exactly bind successful stimulus'
        return result
    receipt_index = index(before) if stimulus == 'activation' else index(after)
    if any(isinstance(v, dict) and v.get('fixture_index', receipt_index) != receipt_index for v in delta):
        result['reason'] = 'callback receipt belongs to another caller input'
        return result
    result.update(status='passed' if events == expected else 'failed',
                  reason='callback behavior after demonstrated requested native stimulus',
                  stimulus_established=True)
    return result


def state_evidence(observation,state):
    captures=[c for c in observation.get('state_captures',[])if c.get('state_id')==state['id']]
    if not captures and state.get('coverage')=='targets':
        index=state.get('after_action');steps=observation.get('steps',[])
        if type(index)is not int or not 0<=index<len(steps):return [],False,'missing native action checkpoint',None
        step=steps[index];bundle=step.get('observation_set')
        if not bundle:
            # Legacy raw data still earns the facts actually visible in its one
            # bound action frame; it cannot borrow frames from other actions.
            legacy=dict(state,coverage='target')
            return state_evidence(observation,legacy)
        binding=step.get('binding_after',{});snapshots=observation.get('snapshots',[])
        capture=dict(bundle,after_action=index,source='native_post_action_targets',scope='targets_only')
        if (bundle.get('state_id')!=state['id']or step.get('state_id')!=state['id']or bundle.get('after_action')!=index
                or not binding or bundle.get('binding')!=binding
                or bundle.get('binding_after_observation')!=binding
                or bundle.get('binding_stable')is not True):
            return [],False,'target observation input/process/event binding drift',capture
        if binding.get('fixture_index',binding.get('input_index'))!=state['input_index']:
            return [],False,'target observation has different caller input',capture
        if not binding.get('instance')or not binding.get('input_sha256')or type(binding.get('event_revision'))is not int:
            return [],False,'target observation lacks native epoch identity',capture
        indices=bundle.get('snapshot_indices',[]);immediate=step.get('immediate_after')
        last=step.get('after',step.get('snapshot'))
        if (not isinstance(indices,list)or not indices or any(type(i)is not int for i in indices)
                or len(indices)!=len(set(indices))or type(immediate)is not int
                or type(last)is not int or immediate not in indices
                or any(type(i)is not int or not 0<=i<len(snapshots)or not immediate<=i<=last for i in indices)):
            return [],False,'invalid target observation snapshot interval',capture
        found=[(i,snapshots[i])for i in indices]
        if any(s.get('state_id')!=state['id']or s.get('binding')!=binding
               or s.get('capture_consistent')is False
               or s.get('binding_after_capture',binding)!=binding for _,s in found):
            return [],False,'target snapshot state/epoch/image mismatch',capture
        return found,False,'bound multi-target evidence; no full-content coverage claim',capture
    if not captures and state.get('coverage')=='target':
        index=state.get('after_action');steps=observation.get('steps',[])
        if not isinstance(index,int)or not 0<=index<len(steps):return [],False,'missing native action checkpoint',None
        step=steps[index];snap_index=step.get('after',step.get('snapshot'));snapshots=observation.get('snapshots',[])
        if not isinstance(snap_index,int)or not 0<=snap_index<len(snapshots):return [],False,'invalid native action snapshot',None
        snapshot=snapshots[snap_index];binding=step.get('binding_after')
        if snapshot.get('capture_consistent') is False:return [],False,'native image/hierarchy epoch changed during capture',None
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
    if any(s.get('capture_consistent') is False for _,s in found):return [],False,'native image/hierarchy epoch changed during capture',capture
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


def bound_state_evidence(observation,state):
    """Strict source/epoch/image identity for the new independently pinned review mode."""
    found,complete,reason,capture=state_evidence(observation,state)
    if not found:return found,complete,reason,capture
    binding=capture.get('binding',{})if capture else{}
    valid=(isinstance(binding.get('instance'),str)and bool(binding['instance'])and
           isinstance(binding.get('input_sha256'),str)and len(binding['input_sha256'])==64 and
           type(binding.get('event_revision'))is int and binding['event_revision']>=0)
    if not valid or any(s.get('state_id')!=state['id']or s.get('binding')!=binding or
                        s.get('capture_consistent')is not True or s.get('binding_after_capture')!=binding for _,s in found):
        return [],False,'strict state/input/epoch/image identity missing or changed',capture
    return found,complete,reason,capture


def legacy_geometry_value(snapshot, item, platform):
    """Distances between observed native bounds, not inferred style attributes.

    Both boxes must be in the same coherent frame. Subtracting screen positions
    across separately scrolled screenshots would produce false spacing results.
    """
    if item.get('measurement')=='layout_box':return None
    def box(selector):
        r=resolve(snapshot,selector,platform)
        node=r.get(item.get('basis','semantic'),{})
        if not r['facts'].get('unique')or not node.get('intersects_viewport'):return None
        if not node.get('fully_within_viewport',node.get('fully_visible',False)):return None
        if platform=='ios':
            f=node.get('frame',{});return [f.get('x',0),f.get('y',0),f.get('x',0)+f.get('width',0),f.get('y',0)+f.get('height',0)]if f else None
        return node.get('unclipped_bounds_dp')
    a=box(item['target'])
    if not a:return None
    p=item['property']
    if p=='width':return a[2]-a[0]
    if p=='height':return a[3]-a[1]
    b=box(item['reference_target'])
    if not b:return None
    return {'gap_x':a[0]-b[2],'gap_y':a[1]-b[3],
            'inset_left':a[0]-b[0],'inset_right':b[2]-a[2],
            'inset_top':a[1]-b[1],'inset_bottom':b[3]-a[3]}[p]


def geometry_measurement(snapshot, item, platform):
    import native_geometry
    try:
        measured = native_geometry.measure(snapshot, item, platform, resolve)
    except (ValueError, TypeError, KeyError, OverflowError):
        return None
    if measured is not None:
        return measured
    # A malformed/present native packet must never fall back to rounded bounds.
    if platform == 'android':
        for selector in [item.get('target'), item.get('reference_target')]:
            if selector and 'native_geometry' in resolve(snapshot, selector, platform).get(item.get('basis', 'semantic'), {}):
                return None
    value = legacy_geometry_value(snapshot, item, platform)
    return None if value is None else {'value': value, 'method': 'legacy_rounded_bounds', 'policy': 'Original strict comparator; no claimed precision repair.'}


def geometry_value(snapshot, item, platform):
    result = geometry_measurement(snapshot, item, platform)
    return result['value'] if result else None


def evaluate(plan, observation, platform, manual=None, root=None, observation_sha256=None, design_lock=None, design_sha256=None, review_policy=None, review_policy_sha256=None):
    if (design_lock is None)!=(design_sha256 is None):raise ValueError('Trusted design requires both external lock and pinned digest')
    if design_lock is not None and 'design_contract'not in plan:raise ValueError('Trusted design mode rejects a stripped or legacy unverified plan')
    if 'design_contract'in plan:
        from design_contract import verify_generated
        if design_lock is None:raise ValueError('Generated assertions require the separately pinned design lock')
        verify_generated(plan,design_lock,design_sha256,platform)
    states=validate_plan(plan);manual=manual or {'decisions':[]};decisions={}
    if (review_policy is None)!=(review_policy_sha256 is None):raise ValueError('Atomic review needs policy and separately pinned digest')
    if review_policy is not None or 'review_contract'in manual:
        if review_policy is None or 'review_contract'not in manual or design_lock is None or root is None or not observation_sha256:
            raise ValueError('Bound atomic review cannot be stripped or used without independently pinned sources')
        from review_contract import verify_manual
        verify_manual(manual,plan,design_lock,design_sha256,review_policy,review_policy_sha256,observation,observation_sha256,root,platform)
    if manual.get('decisions') and (not observation_sha256 or manual.get('observation_sha256')!=observation_sha256):raise ValueError('Manual review is not bound to this observation')
    for row in manual.get('decisions',[]):
        if row.get('id')in decisions:raise ValueError('Duplicate manual decision')
        decisions[row.get('id')]=row
    unknown=set(decisions)-{a['id']for a in plan['assertions']if a['kind']=='manual'}
    if unknown:raise ValueError('Unplanned manual decisions')
    evidence={sid:(bound_state_evidence if review_policy is not None else state_evidence)(observation,spec)for sid,spec in states.items()};rows=[]
    for item in plan['assertions']:
        found,complete,why,capture=evidence[item['state']];status='unassessed';actual=None;reason=why;used=[];geometry_proofs=None
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
                    checks=[compare(v,item['expected'],item.get('op','eq'),item.get('tolerance'))for _,v,_ in values]
                    # Conflicting real values inside one immutable epoch remain unknown.
                    if all(checks):status='passed';reason='typed native property matches expected'
                    elif not any(checks):status='failed';reason='typed native property contradicts expected'
                    else:reason='native values conflict within state; inspect changing UI or capture drift'
                else:reason='native property unavailable, target not observed, or ancestry ambiguous'
            elif kind=='event':
                index=item['action_index'];steps=observation.get('steps',[])
                if 0<=index<len(steps):
                    step=steps[index]
                    after=step.get('binding_after',{})
                    index_ok=after==capture.get('binding')
                    actual=callback_verdict(step,item['expected'],platform,item.get('required_method'),item.get('stimulus','activation'))
                    if index_ok:
                        status=actual['status'];reason=actual['reason']
                    else:reason='successful stimulus and assessed state have different bindings'
            elif kind=='text_layout':
                values=[]
                for index,snapshot in found:
                    matched=[n for n in snapshot.get('nodes',[])if same_selector(n,item['target'])]
                    if len(matched)==1 and matched[0].get('intersects_viewport')and item['property']in matched[0]:
                        values.append((index,matched[0][item['property']]))
                if values:
                    actual=[v for _,v in values];used=[i for i,_ in values];result=[compare(v,item['expected'],item.get('op','eq'),item.get('tolerance'))for _,v in values]
                    if all(result):status='passed';reason='native text layout result'
                    elif not any(result):status='failed';reason='native text layout contradiction'
                    else:reason='conflicting native layout values'
            elif kind=='geometry':
                values=[(i,geometry_measurement(s,item,platform))for i,s in found]
                values=[(i,v)for i,v in values if v is not None]
                if values:
                    actual=[v['value'] for _,v in values];used=[i for i,_ in values]
                    import native_geometry
                    result=[native_geometry.compare(v,item['expected'],item.get('op','eq'),item.get('tolerance')) if 'ratio' in v else compare(v['value'],item['expected'],item.get('op','eq'),item.get('tolerance')) for _,v in values]
                    geometry_proofs=[dict(v,snapshot=i)for i,v in values]
                    if all(result):status='passed';reason='same-frame native-bound geometry matches design'
                    elif not any(result):status='failed';reason='same-frame native-bound geometry contradicts design'
                    else:reason='conflicting native geometry inside one state'
                else:reason='layout-box measurement unsupported by current AX/semantic collector'if item.get('measurement')=='layout_box'else'unique fully visible native boxes unavailable in a shared coherent frame'
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
        rows.append({'id':item['id'],'state':item['state'],'status':status,'actual':actual,'reason':reason,'snapshot_indices':sorted(set(used)),**({'geometry_evidence':geometry_proofs}if geometry_proofs is not None else{})})
    counts={s:sum(row['status']==s for row in rows)for s in ['passed','failed','unassessed']}
    planned={item['id']:item for item in plan['assertions']}
    machine_findings=[{'id':row['id'],'state':row['state'],'requirement_id':planned[row['id']].get('requirement_id'),
                       'origin':'typed_native_check','kind':planned[row['id']]['kind'],
                       'target':planned[row['id']].get('target'),'property':planned[row['id']].get('property'),
                       'expected':planned[row['id']].get('expected'),'actual':row['actual'],
                       'unit':planned[row['id']].get('unit'),'measurement':planned[row['id']].get('measurement'),
                       'expectation_provenance':planned[row['id']].get('expectation_provenance'),
                       'reason':row['reason'],'snapshot_indices':row['snapshot_indices'],
                       'action_index':planned[row['id']].get('action_index')}
                      for row in rows if row['status']=='failed'and planned[row['id']]['kind']!='manual']
    return {'schema_version':1,'status':'failed'if counts['failed']else'needs_review'if counts['unassessed']else'passed',
            'coverage_contract':'required_id_set'if 'required_assertion_ids'in plan else'supplied_plan_only','complete_requirements_claim':bool(plan.get('required_assertion_ids'))and not counts['failed']and not counts['unassessed'],'assertions':rows,'counts':counts,'states':{k:{'complete':v[1],'reason':v[2],'binding':v[3].get('binding')if v[3]else None}for k,v in evidence.items()},
            'machine_findings':machine_findings,'failed_assertion_ids':[row['id']for row in rows if row['status']=='failed'],
            'matrix_contract':plan.get('matrix_contract'),
            'expectation_provenance':{'status':'verified_typed_source_derivation','design_lock_sha256':design_sha256}if 'design_contract'in plan else{'status':'unverified_supplied_expectations'},
            'limits':'Native facts are typed and state-bound. Manual visual meaning remains reviewer judgment. AX dimensions do not establish internal padding/fonts/colors or complete physical hit regions.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--observation',type=Path,required=True);p.add_argument('--platform',choices=['ios','android'],required=True);p.add_argument('--manual',type=Path);p.add_argument('--root',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--design-lock',type=Path);p.add_argument('--design-sha256');p.add_argument('--review-policy',type=Path);p.add_argument('--review-policy-sha256');a=p.parse_args()
    if a.output.exists():raise ValueError('Fresh output required')
    report=evaluate(read(a.plan),read(a.observation),a.platform,read(a.manual)if a.manual else None,a.root or a.observation.parent,sha(a.observation),read(a.design_lock)if a.design_lock else None,a.design_sha256,read(a.review_policy)if a.review_policy else None,a.review_policy_sha256)
    report['input_hashes']={'plan':sha(a.plan),'observation':sha(a.observation),**({'manual':sha(a.manual)}if a.manual else{})}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':report['status'],'counts':report['counts']}));return 1 if report['status']=='failed'else 3 if report['status']=='needs_review'else 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError)as e:print('Invalid native assertion evidence: '+str(e),file=sys.stderr);raise SystemExit(2)
