#!/usr/bin/env python3
"""Replay immutable v10 bytes in a temporary source/index view; no SDK."""
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;REPO=P.parents[2];OLD='validation/default-forward/';NEW=REPO/'validation/routed-forward'
def raw(p):return os.readlink(p).encode()if p.is_symlink()else p.read_bytes()
def main():
 inventory=json.loads((REPO/OLD/'ARTIFACTS.json').read_text())
 with tempfile.TemporaryDirectory(prefix='native-v10-original-')as folder:
  root=Path(folder);copied={}
  def put(rel,expected=None):
   source=REPO/rel
   if rel.startswith('native-ui-agent/'):source=NEW/'baseline-v10'/rel.removeprefix('native-ui-agent/')
   elif (NEW/'historical-root'/rel).is_file():source=NEW/'historical-root'/rel
   if expected:assert hashlib.sha256(raw(source)).hexdigest()==expected,rel
   target=root/rel;target.parent.mkdir(parents=True,exist_ok=True)
   if source.is_symlink():target.symlink_to(os.readlink(source))
   else:
    try:os.link(source,target)
    except OSError:shutil.copyfile(source,target)
   copied[rel]=target
  for rel,item in inventory['files'].items():put(rel,item['sha256'])
  put(OLD+'ARTIFACTS.json')
  release=json.loads((REPO/OLD/'RELEASE.json').read_text())
  for rel,h in release['repository_files'].items():
   if rel not in copied:put(rel,h)
  env=dict(os.environ,GIT_DIR=str(REPO/'.git'),GIT_WORK_TREE=str(root),GIT_INDEX_FILE=str(root/'.historical-index'),PYTHONDONTWRITEBYTECODE='1')
  subprocess.run(['git','read-tree','--empty'],cwd=root,env=env,check=True)
  algorithm=subprocess.check_output(['git','rev-parse','--show-object-format'],cwd=REPO,text=True).strip();entries=[]
  for rel,path in copied.items():
   data=raw(path);h=hashlib.new(algorithm);h.update(b'blob '+str(len(data)).encode()+b'\0'+data)
   entries.append(('120000'if path.is_symlink()else'100644')+' '+h.hexdigest()+'\t'+rel+'\0')
  subprocess.run(['git','update-index','-z','--index-info'],input=''.join(entries).encode(),cwd=root,env=env,check=True)
  def run(args):return subprocess.check_output([sys.executable,'-B',*args],cwd=root,env=env)
  for script in ['test_metrics.py','design/verify_design.py','verify.py','verify_quality.py']:sys.stdout.buffer.write(run([OLD+script]))
  for script,name in [('execution_audit','execution-audit'),('costs','costs'),('derive_results','results')]:assert run([OLD+script+'.py'])==(root/OLD/(name+'.json')).read_bytes(),script
  sys.stdout.buffer.write(run([OLD+'build_docs.py','--check']));sys.stdout.buffer.write(run([OLD+'artifacts.py','--tracked']))
 print('PASS immutable v10 source, evidence, metrics and indexed publication bytes')
if __name__=='__main__':main()
