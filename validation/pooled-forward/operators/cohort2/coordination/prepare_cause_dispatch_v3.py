#!/usr/bin/env python3
"""Prepare uniform minimum-input independent roles, without reading grades/map."""
import argparse
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import time

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def ref(p):return {'path':str(p),'sha256':sha(p)}
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    p.chmod(0o444)

def clock_point(root):
    path=root/'business-quality-tools/quality_clock.py'
    assert sha(path)=='8a91e9d25574483b7c3275350c0b04b90cdb8f6cba5b91da041968a0a5e5a45c', 'Shared clock helper pin differs'
    spec=importlib.util.spec_from_file_location('shared_quality_clock',path)
    clock=importlib.util.module_from_spec(spec);spec.loader.exec_module(clock)
    return clock.point('started')

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--group',required=True);p.add_argument('--input-ledger',required=True,type=Path);a=p.parse_args()
    assert re.fullmatch(r'Case0[1-5]-[IXY]',a.group)
    root=a.root.resolve();coord=root/'operators/cohort2/coordination';order=load(coord/'POST-PUBLIC-ACQUISITION-ORDER.json')['grade_group_order'];i=order.index(a.group)
    for before in order[:i]:assert (root/f'cache/business/blind-quality/episodes/{before}/cause/END.json').is_file(),'Previous independent pair must close before next group'
    ledger=a.input_ledger.resolve()
    assert ledger.parent==coord/'blind-packet-ledgers' and ledger.name in {a.group+'-complete-v2',a.group+'-complete-v3'}, 'Explicit matching immutable input revision required'
    complete=load(ledger/'COMPLETE-INPUT.json');assert complete['anonymous_group']==a.group
    packet=Path(complete['base_packet_seal']['path']).parent
    assert sha(packet/'SEAL.json')==complete['base_packet_seal']['sha256']
    integrity=load(ledger/'INTEGRITY-LIVE.json');assert integrity['status']=='passed'
    supplement=Path(complete['anonymous_supplement_directory']);supp_digest=complete['anonymous_supplement_content_sha256']
    episode=root/f'cache/business/blind-quality/episodes/{a.group}/cause'
    save(episode/'START.json',{'version':2,'kind':'parallel-independent-cause-episode-start','anonymous_group':a.group,**clock_point(root),
         'packet_seal':ref(packet/'SEAL.json'),'complete_input':ref(ledger/'COMPLETE-INPUT.json'),'integrity':ref(ledger/'INTEGRITY-LIVE.json'),'judges':['J1','J2'],
         'scope':'Two fresh independent AI contexts, own version and identical original contract supplement. Record concurrent episode union wall, not summed actor times.'})
    entries=[]
    for judge in ['J1','J2']:
        output=root/f'cache/business/blind-quality/grades/{a.group}/{judge}/cause';output.mkdir(parents=True,exist_ok=False)
        text=f'''You are independent AI judge {judge} for one fixed anonymous dual-platform UI version, group {a.group}.
Read ONLY this exact instruction file, base packet {packet}, and original source-contract supplement {supplement}. Do not open the supplement's parent/operator folders. Write ONLY {output}.
Verify base SEAL.json SHA {sha(packet/'SEAL.json')} and every member. Supplement has153 regular files including FILES.txt; canonical digest of {{relative:{{sha256,bytes}}}} is {supp_digest} (sorted keys, compact separators, ensure_ascii=False).
The supplement contains unchanged original source/API/design docs and pre-business stock/placement raw bytes. Reference SVGs are specifications, not native evidence. Follow base INSTRUCTIONS.md and GRADE-TEMPLATE.json with both original input sets.
Independently inspect source/contracts/native actuals/original PNGs; identify genuine deduplicated causes, source observations, private manual-image actuals, coverage/measurement limits, and actual inspection ledgers. Query large JSON by state/field. Byte-identical PNG aliases may share one visual inspection only after identical-SHA proof; retain separate actual native state/epoch bindings and record viewed path plus aliases. No P from expected/source or unseen image content. Missing/full-content-unsupported facts stay null/U, N/A separate.
No SDK, source/oracle edits, sibling versions, operator/original paths, tool identity, arm mapping, costs, selfclaims, alarms or another judge result. You have one version only. Do not infer comparison or desired findings.
Seal all own output files as instructed and deliver exact SEAL path/SHA with a concise coverage statement. Inherit configured parent model without overrides or subagents. This first cause pass precedes the global cause barrier; no alarm adjudication yet.
'''
        prompt=coord/f'grader-dispatches/{a.group}/{judge}-PROMPT.txt';prompt.parent.mkdir(parents=True,exist_ok=True)
        with prompt.open('x') as f:f.write(text);f.flush();os.fsync(f.fileno())
        prompt.chmod(0o444);entries.append({'judge':judge,'prompt':ref(prompt),'output':str(output)})
    save(coord/f'grader-dispatches/{a.group}/PREPARED.json',{'version':1,'at_unix':time.time(),'group':a.group,'entries':entries,'fork_turns':'none','model_override':None,'mapping_revealed':False})
    print(json.dumps({'group':a.group,'entries':entries}))

if __name__=='__main__':main()
