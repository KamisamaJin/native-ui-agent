#!/usr/bin/env python3
"""Check sealed anonymous cause/claim coverage and exact cited bytes; no rejudge."""
from pathlib import Path
import json
import study as s
R=s.R

def main():
 s.verify_dir(R/'adjudication');s.verify_dir(R/'adjudication-input')
 value=s.read(R/'adjudication/causes.json');mapping=s.read(R/'private/quality-map.json')['candidates'];assert set(value['candidates'])==set(mapping)
 initial=next(k for k,v in mapping.items()if v['version']=='initial');assert value['initial_candidate']==initial
 ids={c['id']for c in value['causes']};assert len(ids)==len(value['causes'])
 for c in value['causes']:
  assert set(c['present_by_candidate'])==set(mapping)and c['panel_consensus']is True
  assert c['initial_present']==c['present_by_candidate'][initial]and c['reason']and c['evidence']
 dispositions={v['key']:v for v in value['manifestation_dispositions']};assert len(dispositions)==len(value['manifestation_dispositions'])
 expected=set()
 for panel in ['panel-one','panel-two']:
  for name in ['alarm-judgments','extra-findings']:
   path=R/'quality-panels'/panel/(name+'.json');expected.update(str(path.relative_to(R))+'#/'+str(i)for i,_ in enumerate(s.read(path)))
 assert expected<=set(dispositions),'Unmapped original alarm/extra'
 for item in dispositions.values():
  if item.get('cause_id'):assert item['cause_id']in ids
  assert item['reason']and item['evidence']
 checked=set()
 def refs(v):
  if isinstance(v,dict):
   if isinstance(v.get('file'),str)and isinstance(v.get('sha256'),str):
    path=Path(v['file']);path=(s.REPO/path if v['file'].startswith('validation/')else R/path)if not path.is_absolute()else path
    path=path.resolve();assert path.is_relative_to(s.REPO),v['file'];assert s.sha(path)==v['sha256'],v['file'];checked.add(str(path))
   for item in v.values():refs(item)
  elif isinstance(v,list):
   for item in v:refs(item)
 refs(value)
 for candidate,meta in mapping.items():
  if meta['version']=='initial':continue
  original=s.read(R/'submissions'/meta['version']/'agent-output/claims.json');copy=s.read(R/'adjudication-input/participant-claims'/(candidate+'.json'))
  assert copy['findings']==original['findings']and copy['original_sha256']==s.sha(R/'submissions'/meta['version']/'agent-output/claims.json')
 print(json.dumps({'status':'PASS','confirmed_causes':len(ids),'original_manifestations_mapped':len(dispositions),'distinct_cited_files':len(checked),'scope':'Original closed independent judgments/claim matching and cited bytes only; no human-gold or invented precision truth.'}))
if __name__=='__main__':main()
