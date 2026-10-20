#!/usr/bin/env python3
"""Prospective thin input translation, immutable capsules and timestamped captures.

No business expected values, UI decisions, or builder source changes.
"""
import argparse, concurrent.futures, hashlib, json, os, shutil, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
R=Path(__file__).resolve().parent
JAVA='/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home'
SDK='/Users/rex/Library/Android/sdk'
DEV='/Applications/Xcode.app/Contents/Developer'
def stamp():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def read(p):return json.loads(p.read_text())
def fingerprint(w):
 return {str(p.relative_to(w)):sha(p) for d in ['alerttoast/Sources','reply/Reply/app/src/main/java/com/example/reply/ui/waterround'] for p in sorted((w/d).rglob('*')) if p.is_file()}
def capsule(w,out):
 assert not out.exists();out.mkdir(parents=True)
 for rel in fingerprint(w):
  dst=out/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(w/rel,dst)
 save(out/'seal.json',{'sealedAtUTC':stamp(),'files':fingerprint(w),'sourceRoot':'source'})
def translate(phase,output=None):
 out=output.resolve() if output else R/'private/inputs'/phase;assert not out.exists()
 o=read(R/'design/private/oracle.json')
 for case in o['cases']:
  if phase=='d0' and case['split']!='initial':continue
  env=case['environment'];models=case['models'];cps=case['checkpoints'];initial=next(c['model'] for c in cps if c['trigger']['type']=='initial');updates=[];actions=[];mapping={};index=0
  for cp in cps:
   trigger=cp['trigger'];kind=trigger['type'];action_index=None
   base='cp-'+cp['id'];action_state=base+'.trigger' if cp.get('full_content') else base;state_id=action_state
   if kind=='activate':
    action_index=len(actions);actions.append({'type':'tap','target':trigger['target'],'reveal':True,'allow_disabled':True,'max_steps':24,'state_id':action_state})
   elif kind=='replaceModel':
    action_index=len(actions);updates.append(models[trigger['model']]);index+=1
    actions.append({'type':'apply_next_fixture','state_id':action_state})
   state_index=action_index
   if cp.get('full_content'):
    state_index=len(actions);state_id=base+'.full';actions.append({'type':'sweep','state_id':state_id,'max_steps':24})
   mapping[cp['id']]={'trigger_action_index':action_index,'state_action_index':state_index,'after_action':state_index,'state_id':state_id,'input_index':index,'full_content':bool(cp.get('full_content')),'trigger_type':kind}
  # All selectors come from the public API; conditional absence remains absence.
  ids=['root','title','description','notice','beds','tank','reserve','dripPrime','method.drip','method.soak','required','spendable','reserveNeeded','remaining','shortfall','reserveConsent','status','submit','progress']
  config={'initial':models[initial],'updates':updates,'width':env['width'],'theme':env['theme'],'direction':env['direction'],'dynamic_type':env['dynamic_type'],'fontScale':env['font_scale'],'state_capture':False,'max_scrolls':24,'observation_targets':[{'identifier':'waterRound.'+i} for i in ids]}
  d=out/case['id'];save(d/'fixtures.json',config);save(d/'actions.json',actions);save(d/'mapping.json',mapping)
 save(out/'seal.json',{'createdAtUTC':stamp(),'phase':phase,'files':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*.json'))}})
def argv(tool,w,platform,fixtures,actions,sim,out,cache):
 base=['python3',str(R/tool/'scripts'/f'{platform}_observe.py'),'run','--bridge',str(R/'bridges'/('Bridge.swift' if platform=='ios' else 'ObserverBridge.kt')),'--fixtures',str(fixtures),'--actions',str(actions),'--output',str(out)]
 if platform=='ios':
  base+=['--package',str(w/'alerttoast'),'--product','AlertToast','--simulator',sim,'--developer-dir',DEV]
  if tool=='candidate-v4':base+=['--build-cache',str(cache)]
 else:base+=['--project',str(w/'reply/Reply'),'--java-home',JAVA,'--android-sdk',SDK]
 return base
def capture(args):
 w=args.workspace.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);before=fingerprint(w);save(out/'started.json',{'atUTC':stamp(),'atUnix':time.time(),'source':before,'tool':args.tool,'phase':args.phase,'platform':args.platform})
 inputs=args.inputs.resolve() if args.inputs else R/'private/inputs'/args.phase
 cases=[R/'public-integration'] if args.public else sorted(p for p in inputs.iterdir() if p.is_dir())
 rows=[]
 for case in cases:
  dest=out/case.name;cmd=argv(args.tool,w,args.platform,case/'fixtures.json',case/'actions.json',args.simulator,dest,w/'ios-build-cache')
  record={'case':case.name,'startedAtUTC':stamp(),'startedAtUnix':time.time(),'argv':cmd}
  save(out/(case.name+'-command.json'),record)
  with (out/(case.name+'-wrapper.log')).open('w') as log:code=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,DEVELOPER_DIR=DEV)).returncode
  record.update(exitCode=code,finishedAtUTC=stamp(),finishedAtUnix=time.time());record['wallSeconds']=record['finishedAtUnix']-record['startedAtUnix'];save(out/(case.name+'-command.json'),record);rows.append(record)
  assert fingerprint(w)==before,'Production source changed during collection'
 save(out/'corpus.json',{'finishedAtUTC':stamp(),'finishedAtUnix':time.time(),'source':before,'runs':rows,'platform':args.platform,'phase':args.phase,'tool':args.tool})
 print(json.dumps({'output':str(out),'attempts':len(rows),'exits':[r['exitCode'] for r in rows]}))
def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
 t=sub.add_parser('translate');t.add_argument('phase',choices=['d0','final']);t.add_argument('--output',type=Path)
 c=sub.add_parser('capsule');c.add_argument('workspace',type=Path);c.add_argument('output',type=Path)
 c=sub.add_parser('capture');c.add_argument('--workspace',type=Path,required=True);c.add_argument('--output',type=Path,required=True);c.add_argument('--tool',choices=['common-v3','candidate-v4'],required=True);c.add_argument('--phase',choices=['d0','final'],required=True);c.add_argument('--platform',choices=['ios','android'],required=True);c.add_argument('--simulator',default='');c.add_argument('--public',action='store_true');c.add_argument('--inputs',type=Path)
 a=p.parse_args()
 if a.cmd=='translate':translate(a.phase,a.output)
 elif a.cmd=='capsule':capsule(a.workspace.resolve(),a.output.resolve())
 else:capture(a)
if __name__=='__main__':main()
