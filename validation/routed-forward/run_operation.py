#!/usr/bin/env python3
"""Explicit shared study-only environment-path adapter; frozen tools unchanged."""
import json,runpy,sys
from pathlib import Path
import study as s
original_read=s.read;original_configuration=s.configuration

def approved_environment(path):
 p=Path(path)
 if p.is_file():return p
 if p.name not in {'environment.ios.json','environment.android.json'}or p.parent.parent.name!='cases':return p
 scope=p.parents[2];approval=original_read(scope/'approval.json');pl=p.name.split('.')[1];case=p.parent.name
 candidate=scope/p.name
 if not candidate.is_file()or s.d.digest(original_read(candidate))!=approval['environment_sha256'][case][pl]:raise ValueError('Shared environment alias lacks exact independent approval')
 return candidate

def read(path):return original_read(approved_environment(path))
def configuration(*args,**kwargs):
 c=original_configuration(*args,**kwargs);c['environment']=str(approved_environment(c['environment']));return c

def install():s.read=read;s.configuration=configuration

def main():
 install();script=Path(sys.argv[1]).resolve()
 if not script.is_relative_to(s.R):raise ValueError('Study operation only')
 sys.argv=[str(script),*sys.argv[2:]];runpy.run_path(str(script),run_name='__main__')
if __name__=='__main__':main()
