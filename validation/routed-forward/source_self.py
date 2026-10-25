#!/usr/bin/env python3
"""Common source-only actuals binding; expectations come from sealed typed sources."""
import argparse,importlib.util
from pathlib import Path
import study as s
import design_contract as d
spec=importlib.util.spec_from_file_location('source_review_binding',s.REPO/'tools/implementation_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
R=s.R

def catalog(scope,source):
 approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');d.validate_lock(lock,approval['design_lock_sha256'])
 index=s.read(scope/'audit-index.json');assert d.digest(index)==approval['audit_index_sha256']
 yes,yes_proof=d.expression({'source':'reference','pointer':'/booleans/yes'},lock['sources']);assert yes=={'value':True,'unit':'bool'}
 files={};rows=[]
 for item in index['items']:
  expected,proof=d.expression(item['expected'],lock['sources']);paths=[]
  for pl in item['platforms']:
   for path in approval['production_paths'][pl]:
    rel=('alerttoast/'if pl=='ios'else'reply/Reply/')+path;p=(source/rel).resolve();assert p.is_relative_to(source.resolve())and p.is_file()
    paths.append(rel);files[rel]={'sha256':s.sha(p),'bytes':p.stat().st_size,'line_count':len(p.read_text().splitlines())}
  identity={'lock':approval['design_lock_sha256'],'audit_index':approval['audit_index_sha256'],'id':item['id'],'files':{v:files[v]['sha256']for v in paths}}
  rows.append({'id':item['id'],'review_id':d.digest(identity),'clause':item['clause'],'priority':item['priority'],'files':paths,
               'proposition':'Source-only: '+item['clause']+'; approved typed datum '+d.canonical(expected).decode(),
               'proposition_provenance':proof,'expected':yes['value'],'unit':'bool','expectation_provenance':yes_proof,
               'approved_datum':expected,'method':'source_only'})
 return {'version':1,'mode':'source_bound','design_lock_sha256':approval['design_lock_sha256'],'audit_index_sha256':approval['audit_index_sha256'],
         'files':files,'rows':rows,'scope':'Source/file/line reviewer actuals against independent typed values. No computed style, runtime branch, transitive-data-flow or human-gold proof.'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','close']);p.add_argument('--unit',required=True);a=p.parse_args()
 source=R/'submissions'/a.unit/'final/source';out=R/'self-review'/a.unit/'source-only';scope=R/'design/public';cat=catalog(scope,source)
 if a.command=='prepare':
  out.mkdir(parents=True,exist_ok=False);s.save(out/'catalog.json',cat);s.save(out/'template.json',{'version':1,'catalog_sha256':d.digest(cat),'decisions':[{'review_id':r['review_id'],'actual':None,'reason':'REPLACE WITH ORIGINAL SOURCE OBSERVATION OR HONEST UNKNOWN','evidence':[]}for r in cat['rows']]})
 else:
  assert cat==s.read(out/'catalog.json'),'Source review catalog drift';bound=audit.bind(cat,s.read(out/'submission.json'));s.save(out/'bound.json',bound)
  print(bound['status'])
