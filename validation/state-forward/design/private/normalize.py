#!/usr/bin/env python3
"""Thin source-free adapter for the immutable native helper's delivered API.
Unknown raw fields stay unassessed. Never dispatches, scrolls, or modifies evidence.
"""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
STATUS={'passed':'pass','failed':'fail','unassessed':'unknown'}

def pointer(obj,path):
    if not path.startswith('/'):raise ValueError('Explicit trigger_step_pointer must be an absolute JSON pointer')
    for piece in path[1:].split('/'):
        piece=piece.replace('~1','/').replace('~0','~')
        obj=obj[int(piece)] if isinstance(obj,list) else obj[piece]
    return obj

def canon_event(event):
    if isinstance(event,str):
        try:event=json.loads(event)
        except (ValueError,TypeError):return event
    return json.dumps(event,sort_keys=True,separators=(',',':'),ensure_ascii=False)

def canonical_step(raw):
    step=deepcopy(raw)
    if isinstance(step.get('callback_delta'),list):
        for i,item in enumerate(step['callback_delta']):
            if isinstance(item,dict) and 'event' in item:item['event']=canon_event(item['event'])
            elif isinstance(item,str):step['callback_delta'][i]=canon_event(item)
    return step

def parsed_event(event):
    if isinstance(event,dict) and 'event' in event:event=event['event']
    if isinstance(event,str):
        try:return json.loads(event)
        except (ValueError,TypeError):return event
    return event

def boolean(value):
    if type(value) is bool:return value
    if value in ['Selected','On','on','selected','1']:return True
    if value in ['Not selected','Off','off','not selected','0']:return False
    return None

def context(snapshot,platform,caseid,stateid,mappingref):
    b=snapshot.get('binding',{})
    instance=b.get('instance');pid=b.get('pid')
    process=str(instance) if instance is not None else (str(pid) if pid is not None else None)
    if instance is not None and pid is not None:process=str(instance)+':'+str(pid)
    return dict(platform=platform,caseID=caseid,stateID=stateid,processID=process,inputRevision=b.get('input_sha256',b.get('fixture_index')),eventRevision=b.get('event_revision'),mappingRef=mappingref)

def rec(cell,kind,actual,ctx,refs,**extra):
    return dict(cellID=cell['cellID'],evidenceKind=kind,actual=actual,context=ctx,evidenceRefs=refs,**extra)

def style_node(resolution,snapshot,field):
    semantic=resolution.get('semantic') or {}
    if semantic.get(field) is not None:
        return semantic,dict(measurementNodePath=[semantic.get('node_id')],measurementCandidates=[])
    root=semantic.get('node_id')
    nodes=snapshot.get('nodes',[])
    if isinstance(nodes,dict):nodes=list(nodes.values())
    by_id={n.get('node_id'):n for n in nodes if isinstance(n,dict) and n.get('node_id') is not None}
    if root is None:return None,{}
    label=resolution.get('facts',{}).get('label')
    candidates=[]
    for node in by_id.values():
        if node.get(field) is None or not isinstance(node.get('native_text'),str):continue
        if ' '.join(node['native_text'].splitlines())!=label:continue
        path=[node.get('node_id')];seen=set(path);parent=node.get('parent_id')
        while parent is not None and parent not in seen:
            path.append(parent);seen.add(parent)
            if parent==root:
                candidates.append((node,list(reversed(path))));break
            parent=by_id.get(parent,{}).get('parent_id')
    detail=dict(measurementCandidates=[dict(node_id=n.get('node_id'),path=path,actual=n.get(field),native_text=n.get('native_text')) for n,path in candidates])
    if len(candidates)==1:
        detail['measurementNodePath']=candidates[0][1]
        return candidates[0][0],detail
    return None,detail

def native_value(cell,resolution,platform,snapshot=None):
    f=resolution.get('facts',{});s=resolution.get('semantic') or {};ctl=resolution.get('control') or {}
    if not f.get('unique') or not isinstance(s,dict) or not s.get('intersects_viewport',False):return None
    op=cell['operator'];asp=cell['aspect'];cls=cell['classification'];extra={}
    if op=='name':return 'native.name',f.get('label'),extra
    if op=='enabled':
        if type(f.get('enabled')) is bool:return 'native.enabled',f['enabled'],extra
    if op=='selected':
        # Native selected=false is a default on many controls, not a checked/off assertion.
        # Explicit checked/on or documented accessibilityValue alternatives carry the logical value.
        sources=[]
        value=f.get('value',s.get('value'))
        role=str(f.get('control_role',f.get('semantic_role',ctl.get('role',s.get('role',''))))).lower()
        checklike=asp=='priority.on' or asp.startswith('job.') or any(x in role for x in ['switch','checkbox','check box','toggle'])
        custom=value in ['Selected','Not selected']
        if custom:sources.append(('explicitSelectedValue',value=='Selected'))
        if checklike:
            checked=boolean(value)
            if checked is not None:sources.append(('checkedValue',checked))
            for owner,node in [('semantic',s),('control',ctl)]:
                if 'toggle_state' in node:
                    checked=boolean(node['toggle_state'])
                    if checked is not None:sources.append((owner+'.toggle_state',checked))
        # A nondefault selected=true conflicts with an explicit off/not-selected assertion.
        flagged_true=f.get('selected') is True or f.get('semantic_selected') is True
        if sources:
            values={v for _,v in sources}
            if len(values)>1 or (values=={False} and flagged_true):
                return 'native.selected',None,dict(selectionCandidates=sources+[('nondefaultSelectedFlag',True)] if flagged_true else sources)
            return 'native.selected',sources[0][1],dict(selectionCandidates=sources)
        selected=boolean(f.get('selected'))
        if selected is None:selected=boolean(f.get('semantic_selected'))
        if selected is not None:return 'native.selected',selected,extra
    if op=='expanded':
        value=f.get('value',s.get('value'))
        if value in ['Expanded','Collapsed']:return 'native.expanded',value=='Expanded',extra
        if type(s.get('expanded')) is bool:return 'native.expanded',s['expanded'],extra
    if op=='equal' and cls=='runtime.business.current':return 'native.text',f.get('label'),extra
    if op=='presence':return 'native.presence',True,extra
    if op=='minimum':
        visible_key='fully_visible' if platform=='android' else 'fully_within_viewport'
        if ctl.get(visible_key) is not True and s.get(visible_key) is not True:return None
        dim=cell['dimension']
        if platform=='android':
            # Semantic layout and expanded action bounds have different meanings.
            if resolution.get('resolution')!='unique_native_control':return None
            rect=ctl.get('unclipped_bounds_dp')
            if not isinstance(rect,(list,tuple)) or len(rect)!=4 or not all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in rect):return None
            value=rect[2]-rect[0] if dim=='width' else rect[3]-rect[1]
            return 'native.bounds',value,dict(unit='dp',uncertainty=2.0,nativeProperty='unclipped_bounds_dp',measurementSourcePath='control.unclipped_bounds_dp',measurementNodePath=[ctl.get('node_id')],nativeRectangles={'unclipped_bounds_dp':deepcopy(rect),'touch_bounds_dp':deepcopy(ctl.get('touch_bounds_dp'))})
        key='ax_'+dim
        if isinstance(f.get(key),(int,float)):
            return 'native.bounds',f[key],dict(unit=cell['unit'],uncertainty=2.0)
    if cls=='runtime.style.native' and platform=='android':
        field='font_sp' if asp.endswith('.fontSize') else ('font_weight' if asp.endswith('.fontWeight') else ('color_argb' if op=='color' and not asp.endswith('.fill') and not asp.startswith('tokens.') else None))
        if field is None:return None
        measured,detail=style_node(resolution,snapshot or {},field)
        kind={'font_sp':'native.fontSize','font_weight':'native.fontWeight','color_argb':'native.color'}[field]
        if measured is None:
            if detail.get('measurementCandidates'):return kind,None,detail
            return None
        if field=='font_sp' and isinstance(measured.get(field),(int,float)):
            return kind,measured[field],dict(detail,unit='sp',uncertainty=0)
        if field=='font_weight':
            w=measured[field]
            if isinstance(w,str) and w.isdigit():w=int(w)
            names={100:'ultralight',200:'thin',300:'light',400:'regular',500:'medium',600:'semibold',700:'bold',800:'heavy',900:'black'}
            if isinstance(w,(int,float)):w=names.get(w)
            if w not in names.values():return None
            return kind,w,detail
        if field=='color_argb':return kind,measured[field],dict(detail,nativeProperty='textColor')
    return None

def stimulus_provenance(rawstep,row,platform,expected_target,replacement=False):
    """Actual receipt facts first; expected values are only validation operands."""
    reasons=[];candidates=[]
    if platform=='ios':
        action=rawstep.get('action') or {}
        if isinstance(action,dict):
            target=action.get('target')
            if isinstance(target,dict) and isinstance(target.get('identifier'),str):candidates.append(dict(path='action.target.identifier',identifier=target['identifier']))
            if isinstance(action.get('identifier'),str):candidates.append(dict(path='action.identifier',identifier=action['identifier']))
    elif platform=='android':
        selector=rawstep.get('selector')
        if isinstance(selector,dict) and isinstance(selector.get('identifier'),str):candidates.append(dict(path='selector.identifier',identifier=selector['identifier']))
    identifiers={c['identifier'] for c in candidates if c['identifier']}
    actual_target=next(iter(identifiers)) if len(identifiers)==1 else None
    actual_state=rawstep.get('state_id');mapped_state=row.get('trigger_state_id')
    if not isinstance(mapped_state,str) or not mapped_state:reasons.append('mapping lacks explicit trigger_state_id from native actions')
    elif actual_state!=mapped_state:reasons.append('raw action state_id does not match mapped trigger_state_id')
    binding_after=rawstep.get('binding_after')
    actual_input=binding_after.get('fixture_index') if isinstance(binding_after,dict) else None
    mapped_input=row.get('input_index')
    if type(actual_input) is not int or type(mapped_input) is not int or actual_input!=mapped_input:reasons.append('actual immediate binding fixture_index does not match mapped input_index')
    dispatch=rawstep.get('dispatch') or {}
    if not isinstance(dispatch,dict):dispatch={}
    actual_method=dispatch.get('method')
    before=dispatch.get('binding_before')
    if not isinstance(before,dict):before=rawstep.get('binding_before')
    before_input=before.get('fixture_index') if isinstance(before,dict) else None
    if replacement:
        if actual_method!='caller_fixture_update':reasons.append('caller replacement lacks actual caller_fixture_update method')
        if type(before_input) is not int or type(actual_input) is not int or actual_input<=before_input:reasons.append('caller replacement lacks actual fixture-index advance')
    else:
        if actual_target is None:reasons.append('actual requested native selector is missing or contradictory')
        elif actual_target!=expected_target:reasons.append('actual requested native identifier differs from expected target')
    return dict(verified=not reasons,reasons=reasons,actualTargetID=actual_target,selectorCandidates=candidates,actualStateID=actual_state,mappedTriggerStateID=mapped_state,actualInputIndex=actual_input,mappedInputIndex=mapped_input,actualMethod=actual_method,beforeInputIndex=before_input)

def normalize(oracle,ledger,observation,mapping,platform,caseid,anonymousid,stage,helper,rawref,mappingref):
    records=[];diagnostics=[];states={s['stateID']:s for s in ledger['states'] if s['caseID']==caseid}
    cells=[c for c in oracle['cells'] if c.get('caseID')==caseid and c['platform']==platform]
    for stateid,state in states.items():
        row=mapping.get(stateid)
        if not row:continue
        specs=dict(id=row['state_id'],input_index=row['input_index'],after_action=row['state_action_index'],coverage='full_content' if state['full_content'] else 'targets')
        try:
            snaps,complete,reason,capture=helper.state_evidence(observation,specs)
        except Exception as exc:
            # A later observation failure does not invalidate a separately demonstrated immediate callback.
            snaps=[];complete=False;reason='state_evidence unavailable: '+type(exc).__name__+': '+str(exc);capture=None
            diagnostics.append(dict(stateID=stateid,kind='nativeStateObservationUnavailable',reason=reason))
        refs=[rawref+'#state_evidence_snapshot_index='+str(i) for i,_ in snaps]
        mapref=mappingref+'#/'+stateid
        this=[c for c in cells if c['stateID']==stateid]
        resolution_cache={}
        for cell in this:
            if cell['classification'] in ['notApplicable.absent','runtime.style.visual','runtime.capability.physicalHit','runtime.business.stimulus','stimulus.execution'] or cell['operator']=='screenshotReview':continue
            if cell['operator']=='completeCoverage':continue
            found=False
            for index,snapshot in snaps:
                key=(index,cell['targetID'])
                if key not in resolution_cache:resolution_cache[key]=helper.resolve(snapshot,{'identifier':cell['targetID']},platform)
                resolved=resolution_cache[key]
                value=native_value(cell,resolved,platform,snapshot)
                if value is None:continue
                kind,actual,extras=value
                if actual is None and not extras.get('measurementCandidates') and not extras.get('selectionCandidates'):continue
                ctx=context(snapshot,platform,caseid,stateid,mapref)
                records.append(rec(cell,kind,actual,ctx,[rawref+'#state_evidence_snapshot_index='+str(index)+';identifier='+cell['targetID']],**extras));found=True
            # Conservative: absence needs a completed full-content frame set.
            if not found and complete and state['full_content'] and snaps and cell['operator'] in ['presence','equal'] and cell['classification']=='runtime.business.current':
                missing=all((resolution_cache.get((i,cell['targetID'])) or helper.resolve(s,{'identifier':cell['targetID']},platform)).get('resolution')=='missing' for i,s in snaps)
                if missing:records.append(rec(cell,'native.presence' if cell['operator']=='presence' else 'native.text',False if cell['operator']=='presence' else None,context(snaps[-1][1],platform,caseid,stateid,mapref),refs,completeCoverage=True))
        # A coverage record is emitted only when the immutable helper establishes completed full content.
        coverage=next((c for c in this if c['operator']=='completeCoverage'),None)
        if coverage and complete and state['full_content'] and snaps:
            business=[c for c in this if c['classification']=='runtime.business.current']
            required={c['targetID'] for c in business if not (c['operator']=='presence' and c['expected'] is False)}
            absent={c['targetID'] for c in business if c['operator']=='presence' and c['expected'] is False}
            def seen(target):
                return any((resolution_cache.get((i,target)) or helper.resolve(s,{'identifier':target},platform)).get('facts',{}).get('unique') and ((resolution_cache.get((i,target)) or helper.resolve(s,{'identifier':target},platform)).get('semantic') or {}).get('intersects_viewport',False) for i,s in snaps)
            all_targets=all(seen(t) for t in required) and not any(seen(t) for t in absent)
            records.append(rec(coverage,'native.coverage',all_targets,context(snaps[-1][1],platform,caseid,stateid,mapref),refs,helperVerdict='pass' if all_targets else 'fail',helperReason=reason+'; independent required exact-target and absence membership checked'))
        if state['actionIndex']==0 or not row.get('trigger_step_pointer'):continue
        try:
            rawstep=pointer(observation,row['trigger_step_pointer'])
            if not isinstance(rawstep,dict):raise TypeError('trigger pointer does not resolve a native step object')
        except (KeyError,IndexError,TypeError,ValueError) as exc:
            diagnostics.append(dict(stateID=stateid,kind='invalidTriggerStepPointer',pointer=row['trigger_step_pointer'],reason=str(exc)))
            rawstep={}
        step=canonical_step(rawstep)
        callback=next(c for c in this if c['operator']=='eventSequence')
        expected=[canon_event(e) for e in callback['expected']]
        stimulus='caller_update' if state['trigger']=='replaceModel' else 'activation'
        replacement=state['trigger']=='replaceModel'
        try:
            verdict=helper.callback_verdict(step,expected,platform,required_method='caller_fixture_update' if replacement else None,stimulus=stimulus)
        except Exception as exc:
            diagnostics.append(dict(stateID=stateid,kind='nativeCallbackHelperUnavailable',reason=type(exc).__name__+': '+str(exc)))
            verdict=dict(status='unassessed',stimulus_established=False,interval_facts=None,reason='native callback helper unavailable')
        native_established=verdict.get('stimulus_established') is True
        provenance=stimulus_provenance(rawstep,row,platform,callback['targetID'],replacement)
        established=native_established and provenance['verified']
        gate=dict(verdict='pass' if established else 'unknown',kind=callback['gate'],evidenceRefs=[rawref+'#'+row['trigger_step_pointer'],mappingref+'#/'+stateid],attempts=1 if native_established and not replacement else None,intervalComplete=established and verdict.get('status') in ['passed','failed'] and isinstance(verdict.get('interval_facts'),list),targetID=None if replacement else provenance['actualTargetID'],nativeHelperStimulusEstablished=native_established,provenance=provenance)
        # immediate_after/after are snapshot indices. The receipt's explicit binding_after
        # is the authoritative immediate binding; never treat an integer as a snapshot dict.
        binding_after=rawstep.get('binding_after')
        after={'binding':binding_after} if isinstance(binding_after,dict) else {}
        ctx=context(after,platform,caseid,stateid,mapref)
        interval=verdict.get('interval_facts')
        events=[parsed_event(e) for e in interval] if isinstance(interval,list) else None
        records.append(rec(callback,'native.events',events,ctx,[rawref+'#'+row['trigger_step_pointer']],gate=gate,helperVerdict=STATUS.get(verdict.get('status'),'unknown'),helperReason=verdict.get('reason','')+'; '+('; '.join(provenance['reasons']) if provenance['reasons'] else 'actual receipt target/state/input validated')))
        execution=next(c for c in this if c['operator']=='stimulus')
        records.append(rec(execution,'native.stimulus',provenance,ctx,[rawref+'#'+row['trigger_step_pointer']],helperVerdict='pass' if established else 'unknown',helperReason=verdict.get('reason','')+'; '+('; '.join(provenance['reasons']) if provenance['reasons'] else 'actual receipt target/state/input validated')))
        # Transition vectors need a separate explicit native-state synthesis review. No callback payload inference.
    return dict(schemaVersion=1,anonymousID=anonymousid,stage=stage,rawEvidence=[rawref,mappingref],records=records,adapterDiagnostics=diagnostics)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--helper',type=Path,required=True);ap.add_argument('--observation',type=Path,required=True);ap.add_argument('--mapping',type=Path,required=True);ap.add_argument('--platform',choices=['android','ios'],required=True);ap.add_argument('--case',required=True);ap.add_argument('--anonymous-id',required=True);ap.add_argument('--stage',choices=['D0','FINAL','paired-D0'],required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    sys.path.insert(0,str(a.helper.parent));spec=importlib.util.spec_from_file_location('immutable_native_checks',a.helper);helper=importlib.util.module_from_spec(spec);sys.modules[spec.name]=helper;spec.loader.exec_module(helper)
    output=normalize(json.loads((HERE/'oracle.json').read_text()),json.loads((HERE/'states-ledger.json').read_text()),json.loads(a.observation.read_text()),json.loads(a.mapping.read_text()),a.platform,a.case,a.anonymous_id,a.stage,helper,str(a.observation),str(a.mapping))
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(records=len(output['records']),output=str(a.out))))

if __name__=='__main__':main()
