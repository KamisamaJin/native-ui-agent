#!/usr/bin/env python3
"""Replay immutable v11 source/evidence in a disposable original index view."""
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;REPO=P.parents[2];OLD='validation/routed-forward/';NEW=REPO/'validation/managed-forward'
def raw(p):return os.readlink(p).encode()if p.is_symlink()else p.read_bytes()
def main():
 inventory=json.loads((REPO/OLD/'ARTIFACTS.json').read_text())
 with tempfile.TemporaryDirectory(prefix='native-v11-original-')as folder:
  root=Path(folder);copied={}
  def put(rel,expected=None):
   source=REPO/rel
   if rel.startswith('native-ui-agent/'):source=NEW/'baseline-v11'/rel.removeprefix('native-ui-agent/')
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
  for argv in [[OLD+'test_metrics.py'],[OLD+'replay_controls.py'],[OLD+'run_operation.py',OLD+'verify_publication.py','--tracked']]:
   p=subprocess.run([sys.executable,'-B',*argv],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   sys.stdout.buffer.write(p.stdout);p.check_returncode()
 print('PASS immutable v11 source, original failures, data, metrics and indexed publication bytes')
if __name__=='__main__':main()
