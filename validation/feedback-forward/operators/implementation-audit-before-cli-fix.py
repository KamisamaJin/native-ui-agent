#!/usr/bin/env python3
"""Bind source-review actuals to independent propositions and exact source bytes.

This is shared implementation-review infrastructure, not native observation or an
AST proof. A reviewer supplies actual/unknown, never expected values or statuses.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native-ui-agent/scripts'))
import design_contract as d

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bridge_hashes(value,platform):
 found=set()
 if isinstance(value,dict):
  if value.get('platform')==platform and 'bridge_sha256'in value:found.add(value['bridge_sha256'])
  for v in value.values():found|=bridge_hashes(v,platform)
 elif isinstance(value,list):
  for v in value:found|=bridge_hashes(v,platform)
 return found

def catalog(lock,lock_sha,policy,policy_sha,source_root,design_root,*,definition_only=False):
 d.validate_lock(lock,lock_sha)
 if d.digest(policy)!=policy_sha or set(policy)!={'version','index'}or policy['version']!=1:raise ValueError('Pinned independent source-audit policy required')
 anchor=policy['index']
 if set(anchor)!={'source','pointer'}:raise ValueError('Exact independent audit index required')
 items=d.pointer(lock['sources'][anchor['source']]['document'],anchor['pointer'])
 if not isinstance(items,list)or not items:raise ValueError('Nonempty independent source-only audit index required')
 source_root=Path(source_root).resolve();design_root=Path(design_root).resolve();rows=[];files={}
 for item in items:
  if set(item)!={'id','clause','priority','files','proposition','expected'}or item['priority']not in{'must','advisory'}or not item['clause'].strip():raise ValueError('Exact atomic source-only obligation schema required')
  proposition,provenance=d.expression(item['proposition'],lock['sources']);expected,proof=d.expression(item['expected'],lock['sources'])
  if proposition['unit']!='string'or not proposition['value'].strip()or expected['unit']!='bool'or type(expected['value'])is not bool:raise ValueError('One source proposition and independent Boolean expected required')
  if not item['files']or len(set(item['files']))!=len(item['files']):raise ValueError('Explicit unique source evidence scope required')
  for rel in item['files']:
   if not isinstance(rel,str)or Path(rel).is_absolute()or'..'in Path(rel).parts:raise ValueError('Safe relative source identity required')
   if rel.startswith('@design/'):
    name=rel[len('@design/'):]
    if name not in{'Bridge.swift','ObserverBridge.kt'}:raise ValueError('Only independently approved thin bridge code belongs to design evidence')
    path=design_root/name;platform='ios'if name=='Bridge.swift'else'android'
    approved=set().union(*(bridge_hashes(v['document'],platform)for v in lock['sources'].values()))
    if approved!={sha(path)}:raise ValueError('Thin bridge differs from independent launch approval')
   else:
    path=(source_root/rel).resolve()
    if not path.is_relative_to(source_root)or path.suffix not in{'.swift','.kt','.java','.m','.mm','.h'}:raise ValueError('Actual production code evidence required')
    if definition_only:
     files[rel]={'sha256':None,'bytes':None,'line_count':None};continue
   if not path.is_file():raise ValueError('Required implementation source missing: '+rel)
   files[rel]={'sha256':sha(path),'bytes':path.stat().st_size,'line_count':len(path.read_text().splitlines())}
  identity={'design_lock_sha256':lock_sha,'policy_sha256':policy_sha,'audit_id':item['id']}
  rows.append({'id':item['id'],'review_id':d.digest(identity),'clause':item['clause'],'priority':item['priority'],'files':list(item['files']),'proposition':proposition['value'],'proposition_provenance':provenance,'expected':expected['value'],'unit':'bool','expectation_provenance':proof})
 if len({r['id']for r in rows})!=len(rows):raise ValueError('Unique source-only obligation IDs required')
 return {'version':1,'mode':'definition_only'if definition_only else'source_bound','design_lock_sha256':lock_sha,'policy_sha256':policy_sha,'files':files,'rows':rows,'method':'source_review','scope':'Declared original production/approved bridge bytes. Reviewer judgment, not native visual/computed-style evidence or an automatic transitive-code proof.'}

def bind(cat,submission):
 if cat.get('mode')!='source_bound':raise ValueError('Definition-only review cannot establish actual implementation acceptance')
 if set(submission)!={'version','catalog_sha256','decisions'}or submission['version']!=1 or submission['catalog_sha256']!=d.digest(cat):raise ValueError('Original source-bound audit submission required')
 decisions={}
 for item in submission['decisions']:
  if set(item)!={'review_id','actual','reason','evidence'}or item['review_id']in decisions or(type(item['actual'])is not bool and item['actual']is not None)or not isinstance(item['reason'],str)or not item['reason'].strip():raise ValueError('Submit only unique audit actual/unknown, rationale and original source ranges')
  row=next((r for r in cat['rows']if r['review_id']==item['review_id']),None)
  if row is None:raise ValueError('Unknown or cross-source audit identity')
  seen=set()
  for ref in item['evidence']:
   if set(ref)!={'file','sha256','start_line','end_line'}or ref['file']not in row['files']:raise ValueError('Declared original source evidence only')
   descriptor=cat['files'][ref['file']]
   if ref['sha256']!=descriptor['sha256']or type(ref['start_line'])is not int or type(ref['end_line'])is not int or not(1<=ref['start_line']<=ref['end_line']<=descriptor['line_count']):raise ValueError('Changed source hash or invalid original line interval')
   seen.add(ref['file'])
  if item['actual']is not None and seen!=set(row['files']):raise ValueError('Known source judgment must cite every declared source file')
  decisions[item['review_id']]=item
 rows=[]
 for row in cat['rows']:
  item=decisions.get(row['review_id']);actual=item['actual']if item else None
  status='unassessed'if actual is None else'passed'if actual==row['expected']else'failed'
  rows.append(dict(row,actual=actual,status=status,reason=item['reason']if item else'No original source judgment supplied',evidence=item['evidence']if item else[]))
 blockers=[r['id']for r in rows if r['priority']=='must'and r['status']!='passed']
 return {'version':1,'catalog_sha256':d.digest(cat),'rows':rows,'counts':{v:sum(r['status']==v for r in rows)for v in ['passed','failed','unassessed']},'status':'accepted'if not blockers else'not_accepted','blocking_obligations':blockers,'scope':cat['scope']}

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['definitions','catalog','bind'])
 for name in ['design-lock','policy','source-root','design-root','output']:p.add_argument('--'+name,type=Path,required=True)
 for name in ['design-sha256','policy-sha256']:p.add_argument('--'+name,required=True)
 p.add_argument('--submission',type=Path);a=p.parse_args()
 cat=catalog(d.load(a.design_lock),a.design_sha256,d.load(a.policy),a.policy_sha256,a.source_root,a.design_root,definition_only=a.command=='definitions')
 value=cat if a.command in{'definitions','catalog'}else bind(cat,d.load(a.submission))
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x')as stream:stream.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
