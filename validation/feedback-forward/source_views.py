#!/usr/bin/env python3
"""Explicit upstream-relative namespace views; never alter source or assertions."""
import argparse,time
from pathlib import Path
import study as s

def install(root,mappings):
 root=Path(root).resolve();before=s.fingerprint(root);rows=[]
 for name,target in mappings.items():
  alias=root/name;actual=(root/target).resolve()
  if Path(name).is_absolute()or'..'in Path(name).parts or not actual.is_relative_to(root)or not actual.is_dir():raise ValueError('Safe existing internal source-directory mapping required')
  if alias.is_symlink():
   if alias.resolve()!=actual:raise ValueError('Existing namespace alias points at different bytes')
   created=False
  elif alias.exists():raise ValueError('Refusing to replace an existing source namespace')
  else:
   alias.parent.mkdir(parents=True,exist_ok=True);alias.symlink_to(target,target_is_directory=True);created=True
  rows.append({'alias':name,'target':target,'created':created})
 after=s.fingerprint(root);assert before==after,'Production bytes changed while installing directory views'
 return {'installedAtUnix':time.time(),'root':str(root),'mappings':rows,'source':before,'source_after':after,'source_unchanged':True,'scope':'Explicit upstream-relative namespace only. Original declarations, expectations, production bytes, native packets and frozen evaluator unchanged. Shared host/source-review compatibility, not a product fix or exclusive Skill benefit.'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--map',action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();mapping={}
 for item in a.map:
  name,target=item.split('=',1)
  if name in mapping:raise ValueError('Duplicate source namespace')
  mapping[name]=target
 s.save(a.output,install(a.root,mapping))
