#!/usr/bin/env python3
"""Replay v9 in its immutable source view while newer default tools evolve."""
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;REPO=P.parents[2];NEW=REPO/'validation/default-forward';OLD=REPO/'validation/feedback-forward';PUB=REPO/'validation/publications/feedback-v9'
def read(p):return json.loads(p.read_text())
def raw(p):return os.readlink(p).encode()if p.is_symlink()else p.read_bytes()
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def main():
 original=read(OLD/'ARTIFACTS.json');completion=read(PUB/'MANIFEST.json');meta=read(PUB/'original-publication.json')
 with tempfile.TemporaryDirectory(prefix='native-v9-original-')as folder:
  root=Path(folder);copied={}
  def put(rel,source,expected=None):
   if expected is not None:assert sha(source)==expected,rel
   target=root/rel;target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists()or target.is_symlink():target.unlink()
   if source.is_symlink():target.symlink_to(os.readlink(source))
   else:
    try:os.link(source,target)
    except OSError:shutil.copyfile(source,target)
   copied[rel]=target
  for rel,item in original['files'].items():
   source=REPO/meta['mutableAliases'].get(rel,rel)
   if rel.startswith('native-ui-agent/'):source=NEW/'baseline-v9'/rel.removeprefix('native-ui-agent/')
   put(rel,source,item['sha256'])
  for rel,item in completion['files'].items():
   source=NEW/'historical-root'/rel if(NEW/'historical-root'/rel).is_file()else REPO/rel
   put(rel,source,item['sha256'])
  for rel in ['validation/feedback-forward/ARTIFACTS.json','validation/publications/feedback-v9/MANIFEST.json']:put(rel,REPO/rel)
  # Build only a temporary metadata index. Blob OIDs are computed from archived
  # bytes; no objects, real index, commits or original inventory are modified.
  env=dict(os.environ,GIT_DIR=str(REPO/'.git'),GIT_WORK_TREE=str(root),GIT_INDEX_FILE=str(root/'.historical-index'),PYTHONDONTWRITEBYTECODE='1')
  subprocess.run(['git','read-tree','--empty'],cwd=root,env=env,check=True)
  algorithm=subprocess.check_output(['git','rev-parse','--show-object-format'],cwd=REPO,text=True).strip()
  entries=[]
  for rel,path in copied.items():
   data=raw(path);h=hashlib.new(algorithm);h.update(b'blob '+str(len(data)).encode()+b'\0'+data)
   entries.append(('120000'if path.is_symlink()else'100644')+' '+h.hexdigest()+'\t'+rel+'\0')
  subprocess.run(['git','update-index','-z','--index-info'],input=''.join(entries).encode(),cwd=root,env=env,check=True)
  commands=[['validation/feedback-forward/verify.py']]
  commands += [['validation/feedback-forward/'+name+'.py','--check']for name in ['benchmark_summary','build_summary','build_failure_index','build_tables','build_gallery']]
  commands += [['validation/publications/feedback-v9/verify.py']]
  for command in commands:subprocess.run([sys.executable,'-B',*command],cwd=root,env=env,check=True)
 print('PASS: immutable v9 sources, raw evidence, metrics and original publication index bytes')
if __name__=='__main__':main()
