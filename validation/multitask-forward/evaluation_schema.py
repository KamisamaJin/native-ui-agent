#!/usr/bin/env python3
"""Pre-seal shape/accounting checks, scoped to one anonymous acceptance task."""
import argparse,json
from pathlib import Path
def read(p):return json.loads(p.read_text())
def ids(values):return{v if isinstance(v,str)else v['id']for v in values}
def main():
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--cases',nargs='+',required=True);a=p.parse_args();summary=read(a.output/'summary.json')
 for alias in ['source-a','source-b']:
  rows=[]
  for case in a.cases:
   for platform in ['ios','android']:
    d=a.output/alias/case/platform;path=d/'grade.json'
    if not path.is_file():path=d/'grade-unavailable.json'
    g=read(path);assert len(g['rows'])==132
    assert all(r['case']==case and r['platform']==platform and r['status']in['P','F','U','N/A']for r in g['rows']);rows+=g['rows']
    if(d/'native-base-grade.json').is_file():assert read(d/'native-base-grade.json')['native_report']==read(d/'native-base.json')
  assert len({r['id']for r in rows})==len(rows)
  s=summary['sources'][alias];counts={x:sum(r['status']==x for r in rows)for x in ['P','F','U','N/A']};assert s['counts']==counts,(alias,'summary counts',s['counts'],counts)
  groups=[ids(s[k])for k in ['product_failure_row_ids','non_product_f_rows','uncertain_f_rows']];failed={r['id']for r in rows if r['status']=='F'}
  assert set.union(*groups)==failed and sum(map(len,groups))==len(failed),(alias,'F cause partition')
  clusters=s['defect_clusters'];assert len({c['cluster_id']for c in clusters})==len(clusters);covered=set()
  for c in clusters:
   rr=ids(c['fixed_row_ids']);assert rr and rr<=groups[0]and c['description']and c['evidence'];covered|=rr
  assert covered==groups[0],(alias,'unclustered confirmed product F')
  assert'unasserted_scope'in s and'unsupported_scope'in s
 print('PASS: complete anonymous task denominator, cause partition and cluster provenance shape')
if __name__=='__main__':main()
