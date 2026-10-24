#!/usr/bin/env python3
"""Verify the original v9 publication bytes without following archived file links."""
import argparse,hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parent;REPO=P.parents[2];R=REPO/'validation/feedback-forward'
def read(p):return json.loads(p.read_text())
def data(p):return os.readlink(p).encode()if p.is_symlink()else p.read_bytes()
def sha(p):return hashlib.sha256(data(p)).hexdigest()
def descriptor(p):
 value={'sha256':sha(p),'bytes':len(data(p))}
 if p.is_symlink():value['target']=os.readlink(p)
 return value
def index():
 result={}
 for entry in filter(None,subprocess.check_output(['git','-C',str(REPO),'ls-files','--stage','-z']).split(b'\0')):
  header,name=entry.split(b'\t',1);mode,oid,stage=header.decode().split();assert stage=='0'
  result[name.decode()]={'mode':mode,'oid':oid}
 return result
def indexed(path,entries,algorithm):
 rel=str(path.relative_to(REPO));assert rel in entries,'Untracked literal path: '+rel
 blob=data(path);h=hashlib.new(algorithm);h.update(b'blob '+str(len(blob)).encode()+b'\0');h.update(blob)
 assert entries[rel]['oid']==h.hexdigest(),'Indexed bytes differ: '+rel
 assert(entries[rel]['mode']=='120000')==path.is_symlink(),'Wrong indexed link mode: '+rel
def original(entries,algorithm):
 meta=read(P/'original-publication.json');manifest=REPO/meta['originalManifest'];assert sha(manifest)==meta['originalManifestSHA256'];value=read(manifest)
 aliases=meta['mutableAliases'];files=value['files'];link_count=0;archived=0
 for key,expected in files.items():
  actual=REPO/aliases.get(key,key);assert actual.is_file()or actual.is_symlink(),key
  got=descriptor(actual)
  for field in ['sha256','bytes']:assert got[field]==expected[field],(key,field)
  if'kind'in expected:
   assert actual.is_symlink()and got['target']==expected['target'];link_count+=1
   if expected['kind']=='directory-symlink':
    assert not Path(got['target']).is_absolute()and actual.resolve().is_relative_to(REPO)and actual.is_dir(),'Invalid portable namespace: '+key
   else:
    assert expected['kind']=='file-symlink';archived+=1
    # A negative-control file link is data. Never dereference its author-machine
    # target or require it to exist on the verifier's machine.
  else:assert not actual.is_symlink(),key
  indexed(actual,entries,algorithm)
 roots=['validation/feedback-forward/','native-ui-agent/','validation/publications/atomic-v8/']
 extra={key for key in files if not any(key.startswith(root)for root in roots)}
 observed={key for key in entries if any(key.startswith(root)for root in roots)or key in extra}
 observed.discard(meta['originalManifest']);assert observed==set(files),'Original publication literal scope changed'
 indexed(manifest,entries,algorithm)
 spec=importlib.util.spec_from_file_location('original_v9_inventory',R/'artifacts.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);required=module.dependencies()
 for key,h in required.items():assert key in files and files[key]['sha256']==h,'Sealed dependency mismatch: '+key
 assert len(required)==value['closure']['sealedDependencies']
 return {'originalFiles':len(files),'sealedDependencies':len(required),'links':link_count,'archivedFileLinksNotDereferenced':archived,'indexedOriginalBytes':True}
def completion_files():
 files={str(p.relative_to(REPO)):descriptor(p)for p in P.rglob('*')if(p.is_file()or p.is_symlink())and p.name!='MANIFEST.json'and'__pycache__'not in p.parts}
 for key in read(P/'original-publication.json')['mutableAliases']:files[key]=descriptor(REPO/key)
 return files
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');a=parser.parse_args();entries=index();algorithm=subprocess.check_output(['git','rev-parse','--show-object-format'],cwd=REPO,text=True).strip();proof=original(entries,algorithm);files=completion_files();path=P/'MANIFEST.json'
 if a.write:
  with path.open('x')as f:f.write(json.dumps({'createdAtUnix':time.time(),'files':files,'originalProof':proof,'scope':'Portable publication amendment only. Preserves original v9 manifest and primary experimental bytes, failure, and original mutable root files. Archived file links are raw evidence; active directory namespaces remain relative/internal.'},indent=2)+'\n')
 else:
  expected=read(path);assert expected['files']==files and expected['originalProof']==proof
  for key in files:indexed(REPO/key,entries,algorithm)
  indexed(path,entries,algorithm)
 print(json.dumps({'status':'PASS',**proof,'completionFiles':len(files),'completionIndexed':not a.write}))
if __name__=='__main__':main()
