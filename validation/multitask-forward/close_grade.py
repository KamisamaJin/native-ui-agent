#!/usr/bin/env python3
"""Seal complete independent task grades with their exact delivered raw inputs."""
import argparse,subprocess,sys
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['D0','FINAL','selfreview','paired-D0']);a=p.parse_args();stage={'D0':'grade-d0','FINAL':'grade-final','selfreview':'grade-selfreview','paired-D0':'grade-pair'}[a.stage];members={}
 for task in ['T1','T2','T3']:
  output=R/'evaluation'/a.stage/task;seal=ex.read(output/'SEAL.json');actual={str(p.relative_to(output)):ex.sha(p)for p in sorted(output.rglob('*'))if p.is_file()and p!=output/'SEAL.json'and'__pycache__'not in p.parts and p.suffix!='.pyc'};assert seal['files']==actual,task
  paths=['evaluation/'+a.stage+'/'+task,'evaluation-inputs/'+a.stage+'/'+task,'evaluation-inputs/'+a.stage+'/DELIVERY-SEAL.json']
  if a.stage in ['D0','FINAL']:paths += ['common-corpora/'+task+'/'+alias+'/'+a.stage.lower()for alias in ['source-a','source-b']]
  if a.stage=='paired-D0':paths += ['paired-corpora/'+task,'precision-replay/'+task]
  members[task]=paths
 path=R/'operators'/(stage+'-members.json');ex.save(path,members)
 with(R/'operators'/(stage+'-seal.log')).open('w')as stream:subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),stage,'--members',str(path)],stdout=stream,stderr=subprocess.STDOUT,check=True)
 print('All THREE independent task outputs/deliveries sealed:',stage)
if __name__=='__main__':main()
