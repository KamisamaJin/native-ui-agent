#!/usr/bin/env python3
"""Run synthetic controls while preserving timestamped historical reports."""
import argparse,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args();base=R/'design/private/evaluator-prep'
 runs=[(base/'v3','regression-v1-controls',43),(base/'v3','encoding-controls',40),(base/'v3','geometry-controls',29),(base/'report-conventions','synthetic-controls',11)]
 old={(root/(name+'-report.json')):(root/(name+'-report.json')).read_bytes()for root,name,_ in runs}
 if a.output:a.output.mkdir(parents=True,exist_ok=False)
 try:
  for root,name,count in runs:
   r=subprocess.run([sys.executable,'-B',str(root/(name+'.py'))],capture_output=True,text=True)
   if r.returncode:raise AssertionError(name+'\n'+r.stdout+'\n'+r.stderr)
   path=root/(name+'-report.json');fresh=json.loads(path.read_text());historical=json.loads(old[path]);assert fresh['status']=='PASS'and fresh['control_count']==count
   for d in [fresh,historical]:d.pop('tested_at_utc',None)
   assert fresh==historical,('Synthetic control results changed',name)
   if a.output:(a.output/(name+'-report.json')).write_bytes(path.read_bytes())
   print(json.dumps({'suite':name,'status':'PASS','controls':count}),flush=True)
 finally:
  for path,raw in old.items():path.write_bytes(raw)
 print('PASS: 123 synthetic controls; original sealed reports preserved byte for byte')
if __name__=='__main__':main()
