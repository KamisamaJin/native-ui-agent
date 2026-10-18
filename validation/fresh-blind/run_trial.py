#!/usr/bin/env python3
"""Experiment operator: seal production state and execute frozen fixtures, never grade."""
import argparse,concurrent.futures,hashlib,json,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent

def seal(workspace:Path,output:Path):
 output.mkdir(parents=True,exist_ok=False);files={}
 for name,prefix in [('reply','Reply/app/src/main'),('alerttoast','Sources')]:
  repo=workspace/name
  paths=subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard'],cwd=repo,text=True).splitlines()
  for path in sorted(set(paths)):
   p=repo/path
   if not p.is_file()or not path.startswith(prefix+'/'):continue
   target=output/name/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);files[str(target.relative_to(output))]=hashlib.sha256(p.read_bytes()).hexdigest()
 (output/'manifest.json').write_text(json.dumps({'sealed_at':time.time(),'files':files},indent=2)+'\n')
 return files

def captures(workspace:Path,phase:str,output:Path,simulator:str,only_platform=None):
 oracle=json.loads((R/'design/private/oracle.json').read_text())
 fixtures=workspace/'operator-inputs'/phase;fixtures.mkdir(parents=True,exist_ok=True)
 inputs=[]
 for case in oracle['cases']:
  if phase=='d0'and case['phase']!='initial':continue
  value=dict(case['fixture']);value['actions']=[{k:v for k,v in action.items() if k in {'type','identifier','checkpoint','model','direction'}}for action in case['protocol']];p=fixtures/(case['caseId']+'.json');payload=json.dumps(value,indent=2)+'\n';assert not p.exists()or p.read_text()==payload,'Frozen fixture changed';p.write_text(payload);inputs.append((case['caseId'],p))
 def one_platform(platform):
  results=[]
  for case,path in inputs:
   dest=output/platform/case;dest.parent.mkdir(parents=True,exist_ok=True)
   capture_script=workspace/'harness/capture.py' if (workspace/'harness/capture.py').exists() else R/'harness/capture.py'
   args=['python3',str(capture_script),'--platform',platform,'--project',str(workspace/('reply/Reply'if platform=='android'else'alerttoast')),'--fixture',str(path),'--output',str(dest)]
   if platform=='ios':args+=['--simulator',simulator]
   t=time.monotonic();r=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   results.append({'case':case,'platform':platform,'exit_code':r.returncode,'seconds':round(time.monotonic()-t,3),'output':r.stdout})
   (output/(platform+'-progress.json')).write_text(json.dumps(results,indent=2)+'\n')
  return results
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:results=list(pool.map(one_platform,[only_platform]if only_platform else ['android','ios']))
 (output/((only_platform+'-operator-summary.json')if only_platform else 'operator-summary.json')).write_text(json.dumps({'phase':phase,'results':results},indent=2)+'\n')

def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
 s=sp.add_parser('seal');s.add_argument('--workspace',type=Path,required=True);s.add_argument('--output',type=Path,required=True)
 c=sp.add_parser('capture');c.add_argument('--workspace',type=Path,required=True);c.add_argument('--phase',choices=['d0','final'],required=True);c.add_argument('--output',type=Path,required=True);c.add_argument('--simulator',required=True);c.add_argument('--only-platform',choices=['android','ios'])
 a=p.parse_args()
 if a.cmd=='seal':print(json.dumps(seal(a.workspace.resolve(),a.output.resolve())))
 else:captures(a.workspace.resolve(),a.phase,a.output.resolve(),a.simulator,a.only_platform)
if __name__=='__main__':main()
