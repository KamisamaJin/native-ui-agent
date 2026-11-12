"""Finite metadata-only original alarm coordination; no agent/SDK/grading API."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
R = HERE.parents[3]
C = R/'operators/cohort2/coordination'
ORDER = ['Case%02d-I'%i for i in range(1,6)]+['Case%02d-%s'%(i,v) for i in range(1,6) for v in ['X','Y']]
PINS = {'wrapper':('operators/run_original_alarm_dispatch.py','b3bf17c47b4b9170ec196590638dd6b08d0b664b1c0c1f36232500f256da772d'),
        'records':('business-quality-tools/grade_records.py','691ab8b1ca698fdcac235b6c79041684f90434abe47d5a235e838c8d4052f8e4'),
        'clock':('business-quality-tools/quality_clock.py','8a91e9d25574483b7c3275350c0b04b90cdb8f6cba5b91da041968a0a5e5a45c'),
        'assemble':('business-quality-tools/assemble_grade_index.py','96a07afef8a7252f4b44fd37e398ff29992e8c4ca543eba9fff0f43f3ad88fc9'),
        'actors':('operators/cohort2/coordination/ORIGINAL-ROLE-CONTEXT-REGISTRY-v1.json','61fd5f600cf4d07d791a866d1376f8f3d6cf4ab75af7671c0608c8a9357b6bd1')}


def need(ok,why):
    if not ok:raise ValueError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(path):return {'path':str(path),'sha256':sha(path.read_bytes())}
def load(path):return json.loads(path.read_bytes())
def pinned(key):
    relative,wanted=PINS[key];path=R/relative;need(ref(path)['sha256']==wanted,'Frozen coordinator dependency differs: '+key);return path
clock_path=pinned('clock');spec=importlib.util.spec_from_file_location('coordination_frozen_clock',clock_path);clock=importlib.util.module_from_spec(spec);spec.loader.exec_module(clock)


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True,ensure_ascii=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    path.chmod(0o444);return ref(path)


def progress(kind,group,record):
    with (HERE/'PROGRESS.jsonl').open('a') as stream:
        stream.write(json.dumps({'version':1,'kind':kind,'group':group,'record':record,**clock.point('recorded')},sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())


def entries(group):
    need(group in ORDER,'Original fixed-order group required')
    path=C/'alarm-dispatches-v4'/group/'PREPARED.json';value=load(path)
    need(value.get('group')==group and value.get('version')==4 and len(value['entries'])==2,'Frozen v4 PREPARED context differs')
    actors=load(pinned('actors'))['groups'][group]['actors']
    need({x['judge'] for x in value['entries']}=={'J1','J2'},'Exactly two original roles required')
    for row in value['entries']:
        need(row['actor']==actors[row['judge']],'Original actor identity differs')
        prompt=Path(row['prompt']['path']);need(ref(prompt)==row['prompt'],'Original prompt bytes differ')
        need(row['output']==str(R/'cache/business/blind-quality/grades'/group/row['judge']/'alarm'),'Original output path differs')
    return path,value['entries']


def own_previous(group):
    index=ORDER.index(group);need(index>0,'First pair was already prepared/dispatched by root')
    prev=ORDER[index-1];record=load(HERE/prev/'close/END.json');need(record['exit_code']==0,'Previous original pair not closed')
    result=record['result'];previous=Path(result['end']['path']);need(ref(previous)==result['end'],'Original prior END bytes differ')
    return result['end']


def command(folder,argv,group,extra=None):
    folder.mkdir(parents=True,exist_ok=False)
    entry={'version':1,'kind':'mechanical-original-alarm-command-entry','group':group,'argv':argv,'coordinator':ref(Path(__file__).resolve()),**clock.point('started'),'scope':'Mechanical metadata/provenance only; frozen child may parse grade context identities, never product interpretation.'}
    if extra:entry.update(extra)
    entry_ref=save(folder/'ENTRY.json',entry)
    with (folder/'stdout').open('xb') as stdout,(folder/'stderr').open('xb') as stderr:
        child=subprocess.run(argv,stdout=stdout,stderr=stderr,check=False)
    for name in ['stdout','stderr']:(folder/name).chmod(0o444)
    end={'version':1,'entry':entry_ref,'exit_code':child.returncode,**clock.point('finished'),'stdout':ref(folder/'stdout'),'stderr':ref(folder/'stderr'),'quality_adjudicated':False,'mapping_accessed':False}
    if child.returncode==0:end['result']=load(folder/'stdout')
    end_ref=save(folder/'END.json',end);progress('command-closed',group,end_ref)
    return end,end_ref


def inspect(group):
    path,rows=entries(group)
    return {'prepared':ref(path),'entries':rows,'seals':[{'judge':j,'present':(R/'cache/business/blind-quality/grades'/group/j/'alarm/SEAL.json').is_file()} for j in ['J1','J2']]}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['adopt-first','inspect','prepare','dispatch-record','close','barrier']);parser.add_argument('--group',choices=ORDER);parser.add_argument('--judge',choices=['J1','J2']);a=parser.parse_args()
    if a.action=='adopt-first':
        need(a.group==ORDER[0],'Only original already-dispatched first pair can be adopted');path,rows=entries(a.group)
        need(ref(path)['sha256']=='f04ede0ed6660e3b0f7e0d82bade17a467a7de029ad09df4f826bb2cb14b6153','Original first PREPARED pin differs')
        result=save(HERE/'ADOPTED-FIRST.json',{'version':1,'kind':'adopted-already-dispatched-original-first-pair','group':a.group,'prepared':ref(path),'entries':rows,'root_already_dispatched_both':True,'redispatched':False,**clock.point('recorded')});progress('adopted-root-original-dispatch',a.group,result)
    elif a.action=='inspect':result=inspect(a.group)
    elif a.action=='prepare':
        previous=own_previous(a.group);argv=['/usr/bin/python3','-B',str(pinned('wrapper')),'--root',str(R),'--group',a.group,'--previous-end',previous['path'],'--previous-end-sha256',previous['sha256']]
        end,record=command(HERE/a.group/'prepare',argv,a.group,{'previous_original_pair_end':previous})
        result={'exit_code':end['exit_code'],'record':record}
        if end['exit_code']==0:result.update(inspect(a.group))
    elif a.action=='dispatch-record':
        need(a.judge is not None,'Exact original role delivery required');path,rows=entries(a.group);row=next(x for x in rows if x['judge']==a.judge)
        result=save(HERE/a.group/('DISPATCH-'+a.judge+'.json'),{'version':1,'kind':'recorded-original-role-prompt-followup','group':a.group,'prepared':ref(path),'entry':row,'operator_attestation':'Explicit followup_task tool returned for this exact original actor and pinned prompt; no product hints supplied.',**clock.point('sent')});progress('original-role-prompt-followup',a.group,result)
    elif a.action=='close':
        path,rows=entries(a.group);seals={j:ref(R/'cache/business/blind-quality/grades'/a.group/j/'alarm/SEAL.json') for j in ['J1','J2']}
        episode=R/'cache/business/blind-quality/episodes'/a.group/'alarm';need(not (episode/'END.json').exists(),'Original END already exists; do not overwrite')
        if a.group!=ORDER[0]:own_previous(a.group)
        argv=['/usr/bin/python3','-B',str(pinned('records')),'close-pair','--episode',str(episode),'--group',a.group,'--phase','alarm']
        for judge in ['J1','J2']:argv+=['--'+judge.lower()+'-seal',seals[judge]['path'],'--'+judge.lower()+'-sha256',seals[judge]['sha256']]
        end,record=command(HERE/a.group/'close',argv,a.group,{'prepared':ref(path),'start':ref(episode/'START.json'),'original_alarm_seals':seals})
        result={'exit_code':end['exit_code'],'record':record}
        if end['exit_code']==0:result.update(end['result'])
    else:
        for group in ORDER:need(load(HERE/group/'close/END.json')['exit_code']==0,'Every original pair must close before barrier')
        argv=['/usr/bin/python3','-B',str(pinned('assemble')),'--root',str(R),'--phase','alarm','--actors',str(pinned('actors')),'--actors-sha256',PINS['actors'][1],'--cause-index',str(C/'cause-barrier-v1/INDEX.json'),'--cause-index-sha256','798c543cb040be1f743413c572be3d3ed9a810659e7bac950f484ccf2ec87680','--output',str(C/'alarm-barrier-v1')]
        end,record=command(HERE/'barrier',argv,'all15')
        result={'exit_code':end['exit_code'],'record':record}
        if end['exit_code']==0:result.update(end['result'])
    print(json.dumps(result))


if __name__=='__main__':main()
