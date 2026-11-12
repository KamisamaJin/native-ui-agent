#!/usr/bin/env python3
"""Replay the predeclared four native episodes and enforce the unchanged gate.

No SDK calls. Native, source, environment, coverage and resource gates have
separate denominators. Raw facts/reasons remain beside normalized P/F/U rows.
"""
import argparse
import hashlib
import inspect
import json
import math
from pathlib import Path
import subprocess
import sys
import time

R = Path(__file__).resolve().parent
ORDER = [('block-1','A'),('block-1','B'),('block-2','B'),('block-2','A')]
STEPS = [('C0-android','android'),('C0-ios','ios-cold'),
         ('R0-android','android'),('R0-ios-cold','ios-cold'),
         ('W1-ios','ios-warm'),('F2-ios-warm','ios-warm'),('F2-android','android')]
COMMANDS = [('C0-android','android','C0'),('C0-ios','ios-cold','C0'),
            ('R0-source-android','android','R0'),('R0-android','android','R0'),
            ('R0-source-ios-cold','ios-cold','R0'),('R0-ios-cold','ios-cold','R0'),
            ('W1-ios','ios-warm','W1'),('F2-ios-warm','ios-warm','F2'),('F2-android','android','F2')]


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x')as f:json.dump(v,f,indent=2)


def number(value,positive=False):
    return type(value)in{int,float}and math.isfinite(value)and(value>0 if positive else value>=0)


def command_receipts(root,block,arm,admission,result,check):
    """Every declared public request has one successful, nested raw receipt."""
    expected={name for name,_,_ in COMMANDS};prefix=block+'-'+arm+'-'
    drivers={p.name.removesuffix('.driver.json')for p in(root/'commands').glob('*.driver.json')}
    receipts={p.parent.name.removeprefix(prefix)for p in(root/'commands').glob('*/result.json')}
    check(drivers==expected and receipts==expected,block+'/'+arm+' missing/extra raw command or driver')
    stages={v['stage']:v for v in result['stages']};items=[];last=result['clock_start']
    for name,case,stage in COMMANDS:
        record=root/'commands'/(prefix+name)
        if not(record/'result.json').is_file()or not(root/'commands'/(name+'.driver.json')).is_file():continue
        try:
            command=load(record/'result.json');request=load(record/'request.json')
            driver=load(root/'commands'/(name+'.driver.json'));config=root/'profiles'/(case+'.json');bound=stages[stage]
            good=(command['clock_basis']=='clock_gettime(CLOCK_MONOTONIC)'
                  and all(number(command.get(k),True)for k in ['clock_start','clock_end','wall_seconds'])
                  and command['clock_end']>command['clock_start']
                  and command['wall_seconds']==command['clock_end']-command['clock_start']
                  and bound['clock_start']<=command['clock_start']and command['clock_end']<=bound['clock_end']
                  and command['clock_start']>=last)
            check(good,block+'/'+arm+'/'+name+' invalid, overlapping or wrong-stage command clock')
            last=command['clock_end']
            request_keys={'started_at_unix','argv','config_sha256','skill','source_before','envelope_sha256',
                          'meter_spec_sha256','purpose','clock_start','clock_basis'}
            check(set(request)==request_keys and all(command.get(k)==v for k,v in request.items()),block+'/'+arm+'/'+name+' raw request differs or missing fields')
            check(command['exit_code']==command.get('wrapper_exit_code')==driver['exit_code']==0
                  and command['error']is None and command['recovery']is None and command['source_unchanged']
                  and command['source_before']==command['source_after']
                  and command['config_sha256']==sha(config)
                  and command['skill']==str((R/admission['arms'][arm]['skill']).resolve())
                  and command['envelope_sha256']==admission['envelope_sha256'],
                  block+'/'+arm+'/'+name+' failed or changed source/config/tool identity')
            outer=driver['argv'];child=outer[outer.index('--')+1:]
            skill=(R/admission['arms'][arm]['skill']).resolve()
            action='bind-source-review'if name.startswith('R0-source-')else'native'
            wanted=[admission['python_executable'],'-B',str(skill/'scripts/ui_loop.py'),action,'--config',str(config)]
            if action=='bind-source-review':
                wanted+=['--submission',str(root/'reviews'/(name+'.json')),'--output',str(root/'reviews'/(name+'-bound.json'))]
            else:
                wanted+=['--output',str(root/'evidence'/name)]
                if name.startswith('F2-'):wanted+=['--final']
                prior={'R0-android':'C0-android','R0-ios-cold':'C0-ios','F2-ios-warm':'W1-ios','F2-android':'C0-android'}
                if arm=='A'and name in prior:
                    packet=root/'evidence'/prior[name]/'capture/result.json'
                    wanted+=['--previous',str(packet),'--previous-sha256',sha(packet)]
            wanted_outer=[admission['python_executable'],'-B',str(R/'native_envelope.py'),'--config',str(config),
                          '--skill',str(skill),'--record',str(record),'--timeout','1200','--']+wanted
            check(child==command['argv']==wanted and outer==wanted_outer,
                  block+'/'+arm+'/'+name+' public request or driver differs')
            items.append(command)
        except (KeyError,ValueError,TypeError,OSError)as exc:
            check(False,block+'/'+arm+'/'+name+' malformed command: '+str(exc))
    check(len(items)==9,block+'/'+arm+' nine bound public commands required')
    for stage in stages.values():
        check(stage.get('new_commands')==sum(s==stage['stage']for _,_,s in COMMANDS),block+'/'+arm+'/'+stage['stage']+' command denominator differs')
    return items


def replay(a):
    sys.path.insert(0,str(Path(a.skill)/'scripts'))
    import design_contract as d
    import feedback_loop as feedback
    import execution_plan as xp
    import acceptance
    import evidence_responsibility as er
    c=load(a.config); plan=load(c['plan']); packet=Path(a.packet).resolve()
    original=load(packet)
    assert original['tool_files']and all(sha(Path(a.skill)/rel)==h for rel,h in original['tool_files'].items()),'Original native tool bytes differ from frozen arm'
    kwargs={'policy':load(c['policy']),'policy_sha':c['policy_sha256']}
    if 'source_config' in inspect.signature(feedback.load_previous).parameters:
        kwargs['source_config']=c
    before,report,obs,execution,receipt=feedback.load_previous(
        packet,sha(packet),plan,load(c['design_lock']),c['design_sha256'],
        load(c['fixtures']),Path(c['bridge']),c['source_roots'],**kwargs)
    cov=xp.coverage_receipt(execution,obs,packet.parent/'native')
    assert d.digest(cov)==d.digest(load(packet.parent/'execution-coverage.json')),'Coverage receipt did not reproduce'
    env=acceptance.environment(obs,load(c['environment']),plan['design_contract']['platform'])
    assert env==load(packet.parent/'environment-check.json'),'Environment did not reproduce'
    expected={r['id']:r for r in plan['assertions']}
    rows=report['assertions'];assert len(rows)==len(expected)==104
    assert len({r['id']for r in rows})==len(rows) and {r['id']for r in rows}==set(expected)
    assert report['matrix_contract']==plan['matrix_contract']
    assert receipt['source_unchanged'] and receipt['inputs_unchanged'] and receipt['native_exit_code']==0
    assert receipt['status']=='verified_capture' and cov['satisfied'] and env['status']=='P'
    manifest=load(packet.parent/'native/manifest.json')
    assert manifest['native_test_count']>0
    compiled=er.compile_contract(c,plan,load(c['design_lock']))
    duties=er.evaluate(c,compiled,report)
    source_claims=[v for v in compiled['claims']if v['method']=='source'and v['priority']=='must']
    assert len(source_claims)==1 and source_claims[0]['id']=='thin-bridge-decodes-calls'
    # Recompute from original images/hierarchy, never from a count-only summary.
    result={'packet':str(packet),'packet_sha256':sha(packet),'source_map':before,
            'platform':plan['design_contract']['platform'],'design_sha256':c['design_sha256'],
            'plan_sha256':d.digest(plan),'fixtures_sha256':sha(c['fixtures']),
            'bridge_sha256':sha(c['bridge']),'environment_sha256':c['environment_sha256'],
            'rows':[{**{k:r[k] for k in ['id','state','status','reason']},
                     'requirement_id':expected[r['id']]['requirement_id'],
                     'property':expected[r['id']].get('property'),
                     'kind':expected[r['id']]['kind'],
                     'unit':expected[r['id']]['unit'],
                     'expected':expected[r['id']]['expected'],
                     'op':expected[r['id']].get('op','eq')}for r in rows],
            'native_counts':report['counts'],'coverage':cov,'environment':env,
            'responsibility':duties,'source_must_claim_ids':[v['id']for v in source_claims],
            'native_tests':manifest['native_test_count'],'passed':True}
    save(a.output,result)


def evaluate(a):
    output=Path(a.output);output.mkdir(parents=True,exist_ok=False)
    admission=load(a.admission)
    assert admission['order']==[list(x)for x in ORDER]
    assert admission['threshold']==0.20 and admission['required_native_atoms']==104
    assert admission['verifier_sha256']==sha(__file__)
    for arm in ['A','B']:
        spec=admission['arms'][arm];freeze=R/spec['freeze'];skill=R/spec['skill']
        assert sha(freeze)==spec['freeze_sha256'],'Frozen arm manifest changed'
        expected=load(freeze)['files']
        assert {str(p.relative_to(skill)):sha(p)for p in sorted(skill.rglob('*'))if p.is_file()and'__pycache__'not in p.parts}==expected,'Frozen replay arm source changed'
    episodes=[]; errors=[]; replays={}
    def check(good,message):
        if not good:errors.append(message)
    for block,arm in ORDER:
        root=R/'cache/benchmark'/block/arm
        if not(root/'result.json').is_file():
            errors.append('Missing episode '+block+'/'+arm);continue
        result=load(root/'result.json'); entry=load(root/'ADMISSION.json')
        check(result['failed']is None,block+'/'+arm+' failed: '+str(result['failed']))
        check(result['source_unchanged'],block+'/'+arm+' changed production source')
        check(entry['skill_seal_sha256']==admission['arms'][arm]['freeze_sha256'],block+'/'+arm+' arm identity changed')
        check(entry['source_map']==admission['production_files'],block+'/'+arm+' application differs')
        check(entry['driver_sha256']==admission['driver_sha256'] and entry['envelope_sha256']==admission['envelope_sha256'],block+'/'+arm+' operator differs')
        check([s['stage']for s in result['stages']]==['C0','R0','W1','F2'],block+'/'+arm+' stage mismatch')
        timing_ok=(result.get('collection_clock_basis')=='clock_gettime(CLOCK_MONOTONIC)'
                   and all(number(result.get(k),True)for k in ['clock_start','clock_end','collection_wall_seconds'])
                   and result['clock_end']>result['clock_start']
                   and result['collection_wall_seconds']==result['clock_end']-result['clock_start'])
        check(timing_ok,block+'/'+arm+' invalid collection clock/duration')
        stage_sum=0;last_clock=result.get('clock_start',0)
        for stage in result['stages']:
            name=stage['stage'];clock_ok=(all(number(stage.get(k),True)for k in ['clock_start','clock_end','wall_seconds'])
                and stage['clock_end']>stage['clock_start']and stage['wall_seconds']==stage['clock_end']-stage['clock_start']
                and stage['clock_start']>=last_clock and stage['clock_end']<=result.get('clock_end',-1))
            check(clock_ok,block+'/'+arm+'/'+name+' invalid or overlapping stage clock')
            if number(stage.get('wall_seconds')):stage_sum+=stage['wall_seconds']
            last_clock=stage.get('clock_end',last_clock)
            check(load(root/('stage-'+name+'.json'))==stage,block+'/'+arm+'/'+name+' raw stage record differs')
        check(number(result.get('operator_and_meter_seconds'))and result.get('collection_stage_seconds')==stage_sum
              and number(result.get('collection_wall_seconds'),True)and result['collection_wall_seconds']>=stage_sum
              and result['operator_and_meter_seconds']==result['collection_wall_seconds']-stage_sum,
              block+'/'+arm+' enclosing duration omits stage/operator costs')
        peak=load(root/'meter.summary.json')
        check(not peak['budget_exceeded'] and peak['sampling_error']is None,block+'/'+arm+' resource budget or sampling failure')
        commands=command_receipts(root,block,arm,admission,result,check)
        for command in commands:
            check(number(command.get('wall_seconds'),True)and command['exit_code']==0 and command.get('wrapper_exit_code')==0 and command['error']is None
                  and command['source_unchanged']and command['envelope_sha256']==admission['envelope_sha256'],
                  block+'/'+arm+' command failure, changed identity or invalid duration')
        check(sum(v['wall_seconds']for v in commands if number(v.get('wall_seconds')))<=stage_sum,
              block+'/'+arm+' raw command walls exceed measured stages')
        episodes.append({'block':block,'arm':arm,'wall_seconds':result['collection_wall_seconds'],
                         'started_at_unix':result['collection_started_at_unix'],'finished_at_unix':result['finished_at_unix'],
                         'clock_start':result.get('clock_start'),'clock_end':result.get('clock_end'),
                         'stages':result['stages'],'native_collections':sum(load(p)['native_executed']for p in(root/'evidence').glob('*/cycle.json')),
                         'observed_peak_allocated_bytes':peak['observed_total_peak_allocated_bytes'],
                         'actual_command_count':len(commands),'failed':result['failed']})
        previous={}
        for step,case in STEPS:
            path=root/'evidence'/step/'cycle.json'
            if not path.is_file():errors.append(block+'/'+arm+'/'+step+' missing');continue
            cycle=load(path); config=root/'profiles'/(case+'.json');pl='android'if case=='android'else'ios'
            if cycle.get('capture_result'):previous[pl]=Path(cycle['capture_result'])
            packet=previous.get(pl)
            if packet is None:errors.append(block+'/'+arm+'/'+step+' no original packet');continue
            dst=output/(block+'-'+arm+'-'+step+'.json')
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'replay','--skill',str(R/admission['arms'][arm]['skill']),
                     '--config',str(config),'--packet',str(packet),'--output',str(dst)]
            proc=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            save(dst.with_suffix('.driver.json'),{'argv':command,'exit_code':proc.returncode,'stdout':proc.stdout})
            if proc.returncode:
                errors.append(block+'/'+arm+'/'+step+' original replay failed');continue
            replayed=load(dst)
            duties=cycle.get('evidence_responsibility',{});duty_rows=duties.get('rows',[])
            identities={'component-native-controls','component-native-callbacks','thin-bridge-decodes-calls'}
            check(len(duty_rows)==3 and {v.get('id')for v in duty_rows}==identities
                  and all(v.get('priority')=='must'and v.get('status')in{'passed','failed','unassessed'}for v in duty_rows),
                  block+'/'+arm+'/'+step+' original responsibility denominator differs')
            replayed['original_responsibility_rows']=sorted([{k:v.get(k)for k in ['id','priority','owner','method','status','expected','unit']}for v in duty_rows],key=lambda v:v['id'])
            replays[(block,arm,step)]=replayed
            check(replayed['native_counts']=={'passed':104,'failed':0,'unassessed':0},block+'/'+arm+'/'+step+' mandatory native discrepancy')
            if step.startswith('F2-'):
                check(cycle['status']=='accepted',block+'/'+arm+'/'+step+' not accepted')
                resources=load(path.parent/'resources.json')
                check(not(resources['remaining_devices']or resources['remaining_directories']or resources['cleanup_errors']),block+'/'+arm+'/'+step+' retirement incomplete')
                duties=cycle['evidence_responsibility']
                check(duties==replayed['responsibility'] and duties['status']=='passed'and not duties['blocking_claims']
                      and replayed['source_must_claim_ids']==['thin-bridge-decodes-calls']
                      and len(duties['rows'])==3 and all(v['status']=='passed'for v in duties['rows']),
                      block+'/'+arm+'/'+step+' responsibility/source denominator missing or does not reproduce')
    comparisons=[]
    for block in ['block-1','block-2']:
        for step,_ in STEPS:
            pair=[replays.get((block,arm,step))for arm in ['A','B']]
            if any(v is None for v in pair):continue
            x,y=pair
            def facts(v):return sorted([{k:r[k]for k in r if k!='reason'}for r in v['rows']],key=lambda r:r['id'])
            same=facts(x)==facts(y)
            check(same,block+'/'+step+' mandatory P/F/U or approved oracle differs')
            source_same=x['original_responsibility_rows']==y['original_responsibility_rows']
            check(source_same,block+'/'+step+' original mandatory responsibility P/F/U differs')
            check(all(x[k]==y[k]for k in ['design_sha256','plan_sha256','fixtures_sha256','bridge_sha256','environment_sha256']),block+'/'+step+' input identity differs')
            comparisons.append({'block':block,'step':step,'same_mandatory_pfu':same,
                'A':x['native_counts'],'B':y['native_counts'],
                'same_original_responsibility_pfu':source_same,
                'original_responsibility_A':x['original_responsibility_rows'],'original_responsibility_B':y['original_responsibility_rows'],
                'raw_reason_differences':[{'id':p['id'],'A':p['reason'],'B':q['reason']}for p,q in zip(sorted(x['rows'],key=lambda r:r['id']),sorted(y['rows'],key=lambda r:r['id']))if p['reason']!=q['reason']]})
    check(len(episodes)==4,'All four episodes required')
    for first,second in zip(episodes,episodes[1:]):
        check(first['finished_at_unix']<=second['started_at_unix'],'AB/BA order overlapped or changed')
        check(number(first.get('clock_end'),True)and number(second.get('clock_start'),True)
              and first['clock_end']<=second['clock_start'],'AB/BA monotonic order overlapped or changed')
    aw=sum(e['wall_seconds']for e in episodes if e['arm']=='A');bw=sum(e['wall_seconds']for e in episodes if e['arm']=='B')
    check(aw+bw<=7200,'120 minute collection budget exceeded')
    speedup=1-bw/aw if aw and len(episodes)==4 else None
    check(speedup is not None and speedup>=0.20,'Measured reduction below 20% or missing')
    blocks=[]
    for block in ['block-1','block-2']:
        e={v['arm']:v for v in episodes if v['block']==block}
        if set(e)=={'A','B'}:blocks.append({'block':block,'A_seconds':e['A']['wall_seconds'],'B_seconds':e['B']['wall_seconds'],'reduction':1-e['B']['wall_seconds']/e['A']['wall_seconds']})
    save(output/'RESULT.json',{'at_unix':time.time(),'admission_sha256':sha(a.admission),'passed':not errors,
        'errors':errors,'episodes':episodes,'comparisons':comparisons,'A_seconds':aw,'B_seconds':bw,'reduction':speedup,
        'blocks':blocks,'business_tasks_may_start':not errors,
        'denominators':{'native_atoms_per_packet':104,'source_must_claims_separate':1,'environment_gate_separate':1,'state_coverage_separate':5},
        'scope':'Four sealed local same-code episodes. Frozen native replay overhead is research validation outside default service walls; all service validation/SDK/retirement is inside episode walls. Sampled disk is a lower bound, shared SDK caches are common.'})
    print(json.dumps({'passed':not errors,'reduction':speedup,'errors':errors}));return 0 if not errors else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest='action',required=True)
    replay_parser=subs.add_parser('replay')
    for name in ['skill','config','packet','output']:replay_parser.add_argument('--'+name,required=True)
    gate=subs.add_parser('gate');gate.add_argument('--admission',required=True);gate.add_argument('--output',required=True)
    a=p.parse_args();return replay(a)if a.action=='replay'else evaluate(a)


if __name__=='__main__':raise SystemExit(main())
