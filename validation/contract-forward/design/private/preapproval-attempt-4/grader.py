#!/usr/bin/env python3
"""SDK-free, design-owned oracle. Never reads a candidate or self-review plan."""
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def normalize_expected(value,unit):
 if unit=='argb':
  if isinstance(value,str) and len(value)==9 and value.startswith('#'):
   try:return int(value[1:],16)
   except ValueError:return value
  if type(value) is int and 0<=value<=0xFFFFFFFF:return value
 return value

def cfroot(root=None):
 p=Path(root).resolve() if root else HERE.parents[1]
 if (p/'design/private/acceptance-table.json').is_file():return p
 if (p/'validation/contract-forward/design/private/acceptance-table.json').is_file():return p/'validation/contract-forward'
 raise ValueError('root must contain design/ or validation/contract-forward/design/')
def remap(p,root):
 p=Path(p)
 if p.exists():return p.resolve()
 marker='/validation/contract-forward/'
 if marker in str(p):return root/str(p).split(marker,1)[1]
 return root/p

def grade(case,platform,observation_path,root=None,manual=None,source_root=None,api_review=None):
 root=cfroot(root);d=root/'design';sys.path.insert(0,str(root/'candidate-v6/scripts'))
 import native_checks as n
 public=case.startswith('P');base=d/('public' if public else 'private')
 plan=load(base/'compiled'/case/platform/'plan.json');lock=load(base/('design-lock.json' if public else 'design-lock.hidden.json'));digest=load(base/('seal.log' if public else 'seal.hidden.log'))['design_lock_sha256']
 table=[r for r in load(d/'private/acceptance-table.json')['rows'] if r['case']==case and r['platform']==platform]
 by={a['id']:a for a in plan['assertions']}
 # Refuse changed plans even when no builder supplied one. Validate the private
 # denominator's exact expectations against the independently sealed design.
 for r in table:
  if r['applicable']:
   expected=r['expected'];expected=int(expected[1:],16) if r['unit']=='argb' else expected
   if canonical(by[r['state']+'/'+r['requirement']]['expected'])!=canonical(expected):raise ValueError('Frozen acceptance/design mismatch')
 observation_path=remap(observation_path,root);obs=load(observation_path)
 if manual:
  mp=remap(manual,root);manual=load(mp)
 result=n.evaluate(plan,obs,platform,manual=manual,root=observation_path.parent,observation_sha256=sha(observation_path),design_lock=lock,design_sha256=digest)
 actual={r['id']:r for r in result['assertions']};rows=[]
 for r in table:
  spec={k:r[k] for k in ('id','case','platform','state','requirement','aspect','class','expected','unit','op','tolerance')}
  evidence={'design':r['source_file']+'#'+r['source_pointer'],'observation':str(observation_path),'observation_sha256':sha(observation_path)}
  if not r['applicable']:row=dict(status='N/A',actual=None,snapshot_indices=[],reason=r['na_reason'])
  else:
   a=actual[r['state']+'/'+r['requirement']];row={k:a[k] for k in ('actual','snapshot_indices','reason')};row['status']={'passed':'P','failed':'F','unassessed':'U'}[a['status']]
   # Public iOS AX cannot expose these generic SwiftUI computed styles.
   if platform=='ios' and r['kind']=='text_layout':row.update(status='U',reason='Public iOS computed text style/layout is unsupported; pixels cannot substitute.',actual=None,snapshot_indices=[])
   evidence['native_assertion']=a['id'];evidence['action_index']=r['action_index']
   evidence['screenshots']=[obs['snapshots'][i].get('screenshot') for i in row['snapshot_indices']]
   if r['kind']=='event':evidence['dispatch_pointer']=f'/steps/{r["action_index"]}/dispatch'
  rows.append(dict(spec,**row,evidence=evidence))
 # Separate input/source/API checks. Native rows never become API evidence.
 checks=[];manifest=observation_path.parent/'manifest.json';run=load(manifest) if manifest.is_file() else {}
 fixture=base/'cases'/case/'fixtures.json';actions=base/'compiled'/case/platform/'actions.json'
 for name,path in [('fixtures',fixture),('actions',actions)]:
  expected=sha(path);value=run.get('input_hashes',{}).get(name)
  checks.append(dict(id=f'{case}/{platform}/input/{name}',case=case,platform=platform,state='input',requirement='fixed-'+name,aspect='fixed-'+name,**{'class':'input'},status='U' if value is None else 'P' if value==expected else 'F',expected=expected,actual=value,snapshot_indices=[],reason='Observer acquisition manifest hash vs approved exact input; not runtime business evidence.',evidence={'manifest':str(manifest),'design_file':str(path.relative_to(root))}))
 sourcefile=('Sources/AlertToast/WorkshopEnrollmentCard.swift' if platform=='ios' else 'app/src/main/java/com/example/reply/ui/components/WorkshopEnrollmentCard.kt')
 source=Path(source_root)/sourcefile if source_root else None
 exists=source.is_file() if source else None
 checks.append(dict(id=f'{case}/{platform}/api/production-file',case=case,platform=platform,state='api',requirement='production-file',aspect='production-file',**{'class':'api'},status='U' if exists is None else 'P' if exists else 'F',expected=sourcefile,actual=str(source) if exists else None,snapshot_indices=[],reason='Production file placement only; does not establish compilation or runtime behavior.',evidence={'source':str(source) if source else None,'sha256':sha(source) if exists else None}))
 checks.append(dict(id=f'{case}/{platform}/api/public-signature',case=case,platform=platform,state='api',requirement='public-signature',aspect='public-signature',**{'class':'api'},status='U',expected='Production public types and callable signature match public/API.md and compile in pinned host.',actual=None,snapshot_indices=[],reason='Requires actual source/API review and successful pinned host compile evidence; runtime tree alone cannot establish it.',evidence={'reference':'design/public/API.md'}))
 if api_review:
  review=load(remap(api_review,root));decisions={r['id']:r for r in review.get('decisions',[])}
  for check in checks:
   decision=decisions.get(check['id'])
   if check['class']=='api' and decision:
    proofs=decision.get('evidence',[]);valid=bool(proofs) and bool(decision.get('reason')) and decision.get('status') in ('P','F') and canonical(decision.get('expected'))==canonical(check['expected'])
    for proof in proofs:
     fp=remap(proof['path'],root);valid=valid and fp.is_file() and sha(fp)==proof.get('sha256')
    if valid:check.update(status=decision['status'],actual=decision.get('actual'),reason=decision['reason'],evidence={'review':str(api_review),'artifacts':proofs})
 return dict(schema_version=1,case=case,platform=platform,rows=rows,checks=checks,counts={s:sum(r['status']==s for r in rows) for s in ['P','F','U','N/A']},design_lock_sha256=digest,observation_sha256=sha(observation_path),scope='Native current facts, gated callback transitions, native styles, semantic box geometry, and explicitly evidenced visual judgment. Compose activation is semantic OnClick, not physical touch.')

def match_claims(grade,claims):
 """Same exact matching for machine failed rows and manual self-review findings."""
 truth={r['id']:r for r in grade['rows']};out=[];seen=set()
 for c in claims:
  key=c.get('id')
  if key not in truth:
   matches=[r for r in truth.values() if all(c.get(k)==r[k] for k in ('case','platform','state','aspect'))]
   key=matches[0]['id'] if len(matches)==1 else None
  r=truth.get(key);metadata_ok=bool(r and all(k not in c or c[k]==r[k] for k in ('case','platform','state','aspect')))
  exact=bool(r and metadata_ok and 'expected' in c and canonical(normalize_expected(c['expected'],r['unit']))==canonical(normalize_expected(r['expected'],r['unit'])) and (c.get('unit') is None or c['unit']==r['unit']))
  if not exact:category='uncertain_unmapped_or_wrong_expectation'
  elif key in seen:category='duplicate'
  elif r['status']=='F':category='TP';seen.add(key)
  elif r['status']=='P':category='FP';seen.add(key)
  else:category='uncertain_'+r['status'];seen.add(key)
  out.append({'claim':c,'fixed_row_id':key,'category':category})
 tp=sum(r['category']=='TP' for r in out);fp=sum(r['category']=='FP' for r in out);natural=sum(r['status']=='F' for r in truth.values())
 metrics={}
 for klass in sorted({r['class'] for r in truth.values()}):
  ids={r['id'] for r in truth.values() if r['class']==klass};fails=sum(r['status']=='F' for r in truth.values() if r['class']==klass);ctp=sum(x['category']=='TP' and x['fixed_row_id'] in ids for x in out);cfp=sum(x['category']=='FP' and x['fixed_row_id'] in ids for x in out)
  metrics[klass]=dict(natural_failures=fails,TP=ctp,FP=cfp,recall=ctp/fails if fails else 'N/A',conditional_FDR=cfp/(ctp+cfp) if ctp+cfp else 'N/A')
 return dict(by_class=metrics,claims=out,TP=tp,FP=fp,natural_failures=natural,recall=tp/natural if natural else 'N/A',conditional_FDR=fp/(tp+fp) if tp+fp else 'N/A',classical_FPR='N/A: no complete negative claim universe',uncertain=sum(r['category'].startswith('uncertain') for r in out))

def repair(before,after):
 final={r['id']:r for r in after['rows']};out=[]
 for r in before['rows']:
  if r['status']!='F':continue
  later=final.get(r['id']);status=later['status'] if later and canonical(later['expected'])==canonical(r['expected']) else 'U'
  out.append(dict(id=r['id'],**{'class':r['class']},before='F',after=status))
 return dict(rows=out,counts={s:sum(r['after']==s for r in out) for s in ['P','F','U','N/A']},success=sum(r['after']=='P' for r in out)/len(out) if out else 'N/A')

def main():
 a=argparse.ArgumentParser();a.add_argument('--root');a.add_argument('--case',choices=['P1','P2','H1'],required=True);a.add_argument('--platform',choices=['ios','android'],required=True);a.add_argument('--observation',required=True);a.add_argument('--manual');a.add_argument('--source-root');a.add_argument('--api-review');a.add_argument('--output',required=True);args=a.parse_args()
 output=Path(args.output)
 if output.exists():raise ValueError('Fresh output required; preserve every grade attempt')
 result=grade(args.case,args.platform,args.observation,args.root,args.manual,args.source_root,args.api_review);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result['counts']))
if __name__=='__main__':main()
