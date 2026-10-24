#!/usr/bin/env python3
"""Complete portable publication inventory and literal tracked dependency closure."""
import argparse,hashlib,json,subprocess,time,os
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
OMIT={'cache','__pycache__','.git','.build','DerivedData','checkouts'}
def sha(p):return hashlib.sha256(os.readlink(p).encode()if p.is_symlink()else p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dependencies():
 required={}
 for path in sorted((R/'gates').glob('*.json')):
  if path.name=='config.json':continue
  for values in read(path)['members'].values():
   for rel,h in values.items():
    key=str((R/rel).relative_to(REPO));assert key not in required or required[key]==h
    required[key]=h
 for folder in ['evaluation-inputs','source-evaluation-inputs']:
  for path in sorted((R/folder).rglob('inputs.json')):
   for rel,h in read(path)['original_files'].items():
    target=(R/rel).resolve();assert target.is_relative_to(R.resolve())
    key=str(target.relative_to(REPO));assert key not in required or required[key]==h
    required[key]=h
 return required
def inventory():
 required=dependencies()
 roots=[R,REPO/'native-ui-agent',REPO/'validation/publications/atomic-v8']
 files=[p for root in roots for p in root.rglob('*')]
 files += [REPO/v for v in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md','.gitignore','.github/workflows/test.yml','validation/publication_history.py','tools/native_environment.py','tools/implementation_audit.py']]
 result={}
 for path in sorted(set(files)):
  rel=path.relative_to(REPO)
  omitted=any(v in OMIT or v.endswith('.xcresult')for v in rel.parts)or path.name=='.DS_Store'or path.suffix in{'.pyc','.pyo'}
  if not(path.is_file()or path.is_symlink())or path==R/'ARTIFACTS.json'or(omitted and str(rel)not in required):continue
  result[str(rel)]={'sha256':sha(path),'bytes':len(os.readlink(path).encode())if path.is_symlink()else path.stat().st_size}
  if path.is_symlink():
   assert path.resolve().is_relative_to(REPO.resolve()),'Portable internal namespace link required'
   result[str(rel)].update(kind='directory-symlink'if path.is_dir()else'file-symlink',target=os.readlink(path))
 return result

def closure(files,tracked=False):
 required=dependencies()
 for key,h in required.items():assert key in files and files[key]['sha256']==h,'Unpublished sealed dependency: '+key
 if tracked:
  paths=set(filter(None,subprocess.check_output(['git','-C',str(REPO),'ls-files','-z']).decode().split('\0')))
  for key in set(files)|{str((R/'ARTIFACTS.json').relative_to(REPO))}:assert key in paths,'Missing literal tracked path: '+key
  folded={}
  for key in paths:
   folded.setdefault(key.casefold(),[]).append(key)
  assert all(len(v)==1 for v in folded.values()),'Tracked case-only path collision'
  index={}
  for entry in filter(None,subprocess.check_output(['git','-C',str(REPO),'ls-files','--stage','-z']).split(b'\0')):
   head,name=entry.split(b'\t',1);mode,oid,stage=head.decode().split();assert stage=='0','Unmerged index entry'
   index[name.decode()]={'mode':mode,'oid':oid}
  algorithm=subprocess.check_output(['git','-C',str(REPO),'rev-parse','--show-object-format'],text=True).strip()
  for key in files:
   path=REPO/key;data=os.readlink(path).encode()if path.is_symlink()else path.read_bytes()
   blob=hashlib.new(algorithm);blob.update(b'blob '+str(len(data)).encode()+b'\0');blob.update(data)
   assert index[key]['oid']==blob.hexdigest(),'Indexed bytes differ from sealed working bytes: '+key
   assert(index[key]['mode']=='120000')==path.is_symlink(),'Indexed link mode differs: '+key
 return {'sealedDependencies':len(required),'literalPathsChecked':tracked,'indexBlobBytesChecked':tracked,'sdkBundlesReferencedByGates':len({str(Path(key).parent)for key in required if any(v.endswith('.xcresult')for v in Path(key).parts)}),'sealedBuildMetadataFiles':sum('DerivedData'in Path(key).parts for key in required)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--audit-index',action='store_true');a=p.parse_args();files=inventory();proof=closure(files,tracked=a.audit_index or not a.write);path=R/'ARTIFACTS.json'
 if a.write:
  assert not path.exists();assert(R/'gates/reveal.json').is_file()
  path.write_text(json.dumps({'createdAtUnix':time.time(),'files':files,'closure':dict(proof,literalPathsChecked=True,indexBlobBytesChecked=True),'scope':'Original prospective methods, frozen tools, neutral performance/negative/independent proof, all initial/final/feedback source and portable native evidence, fixed public/hidden designs, complete original self/independent judgments, failures, metrics/costs. Unreferenced SDK/build caches excluded; any explicitly sealed original metadata is retained to preserve complete dependency closure. Prior v8 original bytes replay in historical view.'},indent=2)+'\n')
 else:
  value=read(path);assert value['files']==files and value['closure']==proof,'Published bytes or closure changed'
 print(json.dumps({'status':'PASS','files':len(files),'bytes':sum(v['bytes']for v in files.values()),'closure':proof}))
if __name__=='__main__':main()
