#!/usr/bin/env python3
"""Close a complete own-acquisition cohort, preserving every original check."""
import argparse,subprocess,sys
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['d0','final']);a=p.parse_args();assignment=ex.read(R/'private/assignment.json')
 assert all((R/'own-corpora'/u/a.phase/'corpus-seal.json').is_file()for u in assignment['units'])
 assert not(R/'gates'/('own-'+a.phase+'.json')).exists()
 log=R/'operators'/('original-checks-'+a.phase+'.log');assert not log.exists()
 with log.open('w')as stream:subprocess.run([sys.executable,'-B',str(R/'check_own.py'),a.phase],stdout=stream,stderr=subprocess.STDOUT,check=True)
 members={u:[str((R/'own-corpora'/u/a.phase).relative_to(R)),str((R/'submissions'/u/'own-checks'/a.phase).relative_to(R)),str((R/'submissions'/u/('own-checks-'+a.phase+'.json')).relative_to(R))]for u in assignment['units']};path=R/'operators'/('own-'+a.phase+'-members.json');ex.save(path,members)
 with(R/'operators'/('own-'+a.phase+'-seal.log')).open('w')as stream:subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),'own-'+a.phase,'--members',str(path)],stdout=stream,stderr=subprocess.STDOUT,check=True)
 print('All SIX original own-'+a.phase+' captures/checks are sealed')
if __name__=='__main__':main()
