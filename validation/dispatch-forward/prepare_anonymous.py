#!/usr/bin/env python3
"""Prepare the next blind batch only after the previous BOTH-grade barrier."""
import argparse,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
from trial_operator import R,read,save,sha
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['d0','final','selfreview','paired-d0']);a=p.parse_args();mapping=read(R/'private/grade-assignment.json')['mapping'];evaluation=R/'design/private/evaluation'
 previous={'final':'d0','selfreview':'final','paired-d0':'selfreview'}.get(a.phase)
 if previous:assert all((evaluation/previous/anon/'SEAL.json').is_file()for anon in mapping),'Previous blind batch not sealed for BOTH sources'
 assert all((R/'private/submissions'/sid/'final-corpus-seal.json').is_file()for sid in mapping.values()),'Both primary measured loops must finish first'
 output=R/'private/grade-deliveries'/(a.phase+'.json');assert not output.exists();rows=[]
 for anon,sid in sorted(mapping.items()):
  dest=R/'private/grade-capsules'/a.phase/anon
  if a.phase=='selfreview':
   w='unit-59af93'if sid=='submission-e572b1'else'unit-c9034d'
   cmd=[sys.executable,str(R/'anonymize_review.py'),'--submission',sid,'--anonymous-id',anon,'--workspace',w,'--destination',str(dest)]
  else:
   phase='final'if a.phase=='final'else'd0'
   family='audit-v3-d0'if a.phase=='paired-d0'and sid=='submission-3d6389'else'own-d0'if a.phase=='paired-d0'else('audit-v4-'+phase if sid=='submission-e572b1'else'own-'+phase)
   corpus=R/'evidence'/family/sid;assert all((corpus/pl/'corpus.json').is_file()for pl in ['ios','android'])
   cmd=[sys.executable,str(R/'make_grade_capsule.py'),'--phase',phase,'--anonymous-id',anon,'--source-capsule',str(R/'private/submissions'/sid/phase),'--corpus',str(corpus),'--inputs',str(R/'private/inputs'/('d0-v2'if phase=='d0'else'final')),'--destination',str(dest)]
  subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
  seal=dest/('SEAL.json'if a.phase=='selfreview'else'capsule-seal.json')
  rows.append({'anonymous_id':anon,'capsule':str(dest.relative_to(R)),'sealSHA256':sha(seal)})
 save(output,{'phase':a.phase,'preparedAtUTC':datetime.now(timezone.utc).isoformat(),'previousBothSeals':previous,'capsules':rows})
 print(json.dumps({'phase':a.phase,'anonymous_capsules':[x['capsule']for x in rows]}))
if __name__=='__main__':main()
