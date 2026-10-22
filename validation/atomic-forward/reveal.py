#!/usr/bin/env python3
"""Disclose the pre-design assignment only after every prospective grade closes."""
import subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def main():
 receipt=ex.gate.authorize(R/'gates','grade-pair',R)
 assignment=R/'private/assignment.json';commitment=ex.read(R/'operators/assignment-commitment.json')
 assert ex.sha(assignment)==commitment['assignmentSHA256']
 target=R/'REVEAL.json';assert not target.exists()
 ex.save(target,{'revealedAtUnix':time.time(),'assignmentSHA256':ex.sha(assignment),'authorization':receipt,'assignment':ex.read(assignment),'scope':'Disclosure after complete independent quality, original-claim and same-evidence replay seals. No candidate receives post-reveal feedback or another repair.'})
 members=R/'operators/reveal-members.json';ex.save(members,{'assignment':['private/assignment.json','operators/assignment-commitment.json','REVEAL.json']})
 subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),'reveal','--members',str(members)],check=True,stdout=subprocess.DEVNULL)
 print('Revealed immutable pre-design assignment after all grade cohorts')
if __name__=='__main__':main()
