#!/usr/bin/env python3
"""Literal portable inventory; file-link evidence is raw bytes, never dereferenced."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1];MANIFEST=R/'ARTIFACTS.json'
def data(p):return os.readlink(p).encode()if p.is_symlink()else p.read_bytes()
def descriptor(p):
 b=data(p);v={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if p.is_symlink():v['target']=os.readlink(p)
 return v
def inventory():
 roots=[R,REPO/'native-ui-agent',REPO/'validation/publications/feedback-v9-replay']
 files={str(p.relative_to(REPO)):descriptor(p)for root in roots for p in root.rglob('*')if(p.is_file()or p.is_symlink())and p!=MANIFEST and not any(v in p.parts for v in ['cache','__pycache__'])}
 for rel in ['README.md','.github/workflows/test.yml','LICENSE','THIRD_PARTY_NOTICES.md','.gitignore']:files[rel]=descriptor(REPO/rel)
 return files
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--tracked',action='store_true');a=p.parse_args();files=inventory()
 if a.write:
  with MANIFEST.open('x')as f:f.write(json.dumps({'createdAtUnix':time.time(),'files':files,'scope':'Entire new study, frozen tools, raw portable captures, failures, source capsules, blind judgments and publication files. SDK caches excluded and not gate members.'},indent=2)+'\n')
 else:assert json.loads(MANIFEST.read_text())['files']==files,'Inventory bytes/scope changed'
 if a.tracked:
  entries={}
  for row in filter(None,subprocess.check_output(['git','ls-files','--stage','-z'],cwd=REPO).split(b'\0')):
   head,rel=row.split(b'\t',1);mode,oid,stage=head.decode().split();assert stage=='0';entries[rel.decode()]=(mode,oid)
  algorithm=subprocess.check_output(['git','rev-parse','--show-object-format'],cwd=REPO,text=True).strip()
  for rel in list(files)+[str(MANIFEST.relative_to(REPO))]:
   assert rel in entries,'Missing literal indexed file: '+rel
   path=REPO/rel;b=data(path);h=hashlib.new(algorithm);h.update(b'blob '+str(len(b)).encode()+b'\0'+b)
   assert entries[rel][1]==h.hexdigest(),'Indexed bytes differ: '+rel
   assert(entries[rel][0]=='120000')==path.is_symlink()
 print(json.dumps({'status':'PASS','files':len(files),'bytes':sum(v['bytes']for v in files.values()),'indexed':a.tracked}))
if __name__=='__main__':main()
