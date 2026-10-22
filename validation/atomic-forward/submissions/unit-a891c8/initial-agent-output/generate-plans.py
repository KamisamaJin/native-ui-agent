from pathlib import Path
import datetime, hashlib, json, subprocess, time
workspace = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-a891c8')
public = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T2/public')
skill = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/baseline-v7')
output = workspace/'agent-output'
logs = output/'logs'; logs.mkdir(exist_ok=True)
digest='c21f3c012a188c7c39e8017dc92e8749b821a74aa3ad84d007732cfffa48e000'
def run(name,args):
    started=time.time()
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,cwd=workspace)
    (logs/(name+'.log')).write_text(result.stdout)
    record={'name':name,'argv':args,'startedAtUnix':started,'finishedAtUnix':time.time(),'returncode':result.returncode,'log':str((logs/(name+'.log')).relative_to(output))}
    with (output/'commands.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
    print(name,result.returncode,result.stdout[:1000])
    if result.returncode:raise SystemExit(result.returncode)
run('seal-original-lock',['python3',str(skill/'scripts/design_contract.py'),'seal','--contract',str(public/'contract.json'),'--root',str(public),'--output',str(output/'approved-lock.json')])
for case in ['P1','P2']:
    for platform in ['ios','android']:
        run('compile-'+case+'-'+platform,['python3',str(skill/'scripts/design_contract.py'),'compile','--lock',str(output/'approved-lock.json'),'--lock-sha256',digest,'--scenario',case,'--platform',platform,'--bindings',str(public/'bindings.json'),'--actions',str(public/'cases'/case/('actions.'+platform+'.json')),'--output',str(output/'plans'/case/platform)])
paths=[public/n for n in ['BRIEF.md','API.md','reference.json','contract.json','policy.json','bindings.json','approval.json','reference-P1-expanded.svg','reference-P2-expanded.svg','reference-P1-expanded.png','reference-P2-expanded.png']]
paths+=sorted((public/'cases').rglob('*.json'))
(output/'public-inputs.json').write_text(json.dumps({'approvedLockSha256':digest,'inputs':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]},indent=2)+'\n')
