#!/usr/bin/env python3
"""Operator-only source sealing and frozen input translation. Never grades UI."""
import argparse,concurrent.futures,hashlib,json,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seal(workspace,output):
 output.mkdir(parents=True,exist_ok=False);files={}
 for name,prefix in [('reply','Reply/app/src/main'),('alerttoast','Sources')]:
  repo=workspace/name
  paths=subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard'],cwd=repo,text=True).splitlines()
  for path in sorted(set(paths)):
   p=repo/path
   if not p.is_file()or not path.startswith(prefix+'/'):continue
   q=output/name/path;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);files[str(q.relative_to(output))]=sha(q)
 reports=output/'reports';reports.mkdir();
 for source in sorted((workspace/'reports').rglob('*')):
  if not source.is_file()or source.suffix.lower()not in {'.json','.png','.xml','.log','.txt','.md'}:continue
  relative=source.relative_to(workspace/'reports')
  if any(part in {'DerivedData','.build','build','project','Products','Index.noindex'}or part.endswith('.xcresult')for part in relative.parts):continue
  target=reports/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 (output/'manifest.json').write_text(json.dumps({'sealed_at':time.time(),'files':files,'reports':{str(p.relative_to(reports)):sha(p)for p in reports.rglob('*')if p.is_file()}},indent=2)+'\n');return files

def prepare(phase,destination):
 oracle=json.loads((R/'design/size-revision/private/oracle.json').read_text());destination.mkdir(parents=True,exist_ok=False);names=[]
 for c in oracle['cases']:
  if phase=='d0'and c['split']!='initial':continue
  actions=[];updates=[];mapping=[];targets={'rr.card','rr.header.title','rr.header.badge','rr.item','rr.deadline','rr.detail','rr.sizes','rr.ack','rr.notes.toggle','rr.notes.body','rr.breakdown','rr.summary','rr.gate','rr.primary','rr.keep','rr.progress','rr.result','rr.done'}
  # Public P06 selector vocabulary plus opaque IDs from actual input; no oracle
  # expected values, source implementation or outcomes participate in selection.
  for model in c['models'].values():
   targets.update('rr.option.'+x['id']for x in model['options'])
   targets.update('rr.size.'+x['id']for x in model['sizes'])
  for cp in c['checkpoints']:
   trigger=cp['trigger'];typ=trigger['type'];action_index=None
   if typ=='replaceModel':
    updates.append(c['models'][trigger['modelId']]);actions.append({'type':'apply_next_fixture','name':cp['stateId']});action_index=len(actions)-1
   elif typ=='activate':
    targets.add(trigger['target']);actions.append({'type':'tap','identifier':trigger['target'],'reveal':True,'allow_disabled':True,'max_steps':40,'name':cp['stateId']});action_index=len(actions)-1
   elif typ!='initial':raise ValueError('Unknown frozen trigger')
   capture_index=action_index
   if cp['fullVisualCheckpoint']:
    state_id=c['caseId']+'--'+cp['stateId'];actions.append({'type':'sweep','state_id':state_id,'max_steps':80,'name':cp['stateId']});capture_index=len(actions)-1
   else:state_id='action-'+str(action_index)
   mapping.append({'checkpoint':cp['stateId'],'modelId':cp['modelId'],'input_index':len(updates),'trigger_action_index':action_index,'capture_action_index':capture_index,'native_state_id':state_id,'coverage':'full_content'if cp['fullVisualCheckpoint']else'target','requested_trigger':trigger})
  assert len(actions)<=40
  spec={'environment':c['environment'],'model':c['models']['initial'],'updates':updates,'actions':actions,'state_capture':False,'observation_targets':[{'identifier':x}for x in sorted(targets)],'protocol':mapping,'caseId':c['caseId'],'split':c['split']}
  p=destination/(c['caseId']+'.json');p.write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n');names.append({'case':c['caseId'],'sha256':sha(p),'actions':len(actions),'checkpoints':len(mapping)})
 (destination/'manifest.json').write_text(json.dumps({'phase':phase,'oracle_sha256':sha(R/'design/size-revision/private/oracle.json'),'cases':names,'created_at':time.time()},indent=2)+'\n')
 return names

def capture(workspace,phase,output,simulator,capability,only_platform=None):
 source=R/'private/inputs'/phase
 assert source.is_dir(),'Prepare frozen phase inputs only after source seals'
 files=[source/(x['case']+'.json')for x in json.loads((source/'manifest.json').read_text())['cases']]
 output.mkdir(parents=True,exist_ok=True)
 def one(platform):
  results=[]
  for fixture in files:
   d=output/platform/fixture.stem;d.parent.mkdir(parents=True,exist_ok=True)
   if d.exists():raise ValueError('No silent overwrite/resume; retain attempt and use a fresh run')
   args=['python3',str(R/'harness/capture.py'),'--platform',platform,'--project',str(workspace/('reply/Reply'if platform=='android'else'alerttoast')),'--fixture',str(fixture),'--output',str(d),'--capability',str(capability)]
   if platform=='ios':args+=['--simulator',simulator]
   t=time.monotonic();r=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);results.append({'case':fixture.stem,'platform':platform,'exit_code':r.returncode,'seconds':round(time.monotonic()-t,3),'output':r.stdout});(output/(platform+'-progress.json')).write_text(json.dumps(results,indent=2)+'\n')
  return results
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:result=list(pool.map(one,[only_platform]if only_platform else['android','ios']))
 (output/((only_platform+'-operator-summary.json')if only_platform else'operator-summary.json')).write_text(json.dumps({'phase':phase,'results':result},indent=2)+'\n')

def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='command',required=True)
 s=sp.add_parser('seal');s.add_argument('--workspace',type=Path,required=True);s.add_argument('--output',type=Path,required=True)
 q=sp.add_parser('prepare');q.add_argument('--phase',choices=['d0','final'],required=True)
 c=sp.add_parser('capture');c.add_argument('--workspace',type=Path,required=True);c.add_argument('--phase',choices=['d0','final'],required=True);c.add_argument('--output',type=Path,required=True);c.add_argument('--simulator',required=True);c.add_argument('--capability',type=Path,required=True);c.add_argument('--only-platform',choices=['android','ios'])
 a=p.parse_args()
 if a.command=='seal':print(json.dumps(seal(a.workspace.resolve(),a.output.resolve())))
 elif a.command=='prepare':print(json.dumps(prepare(a.phase,R/'private/inputs'/a.phase)))
 else:capture(a.workspace.resolve(),a.phase,a.output.resolve(),a.simulator,a.capability.resolve(),a.only_platform)
if __name__=='__main__':main()
