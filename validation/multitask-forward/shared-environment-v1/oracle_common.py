"""Frozen SDK-free independent business/native oracle. Does not read builder plans."""
import copy,hashlib,json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/"design-v2"
sys.path.insert(0,str(R.parents[1]/"tools"))
from native_environment import direction, ENCODING
sys.path.insert(0,str(R/'candidate-v7/scripts'))
sys.dont_write_bytecode=True
import design_contract as dc
import native_checks as nc
NATIVE_CLASSES={'business_current','business_transition','geometry','native_style'}

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p).resolve()
 try:return str(p.relative_to(R))
 except ValueError:return str(p)
def check(identity,status,expected=None,actual=None,reason='',evidence=None):return dict(id=identity,status=status,expected=expected,actual=actual,reason=reason,evidence=evidence or [])
def status(s):return {'passed':'P','failed':'F','unassessed':'U'}.get(s,'U')

def api_checks(task,platform,source_root,api_review):
 if source_root is None:return [check('source-api','U',reason='No source root/API review supplied; native results stay separate.')]
 source_root=Path(source_root);pub=task/'public';api=(pub/'API.md').read_text();name=re.search(r'# (\w+) public API',api).group(1)
 rel=('alerttoast/Sources/AlertToast/'+name+'.swift') if platform=='ios' else ('reply/Reply/app/src/main/java/com/example/reply/ui/components/'+name+'.kt')
 p=source_root/rel
 # The caller may pass the platform checkout itself.
 if not p.is_file():
  alt=source_root/('/'.join(rel.split('/')[1:]) if platform=='ios' else '/'.join(rel.split('/')[2:]))
  if alt.is_file():p=alt
 if not p.is_file():return [check('production-source','F',rel,None,'Required production source missing.')]
 text=p.read_text();pattern=(r'public\s+struct\s+'+name+r'\b') if platform=='ios' else (r'fun\s+'+name+r'\s*\(')
 rows=[check('production-source','P',rel,ref(p),'Required production source exists.',[{'path':ref(p),'sha256':sha(p)}]),check('public-symbol','P' if re.search(pattern,text) else 'F',name,name if re.search(pattern,text) else None,'Lexical public-symbol precheck; not complete type/API conformance.')]
 review=read(api_review) if isinstance(api_review,(str,Path)) else api_review
 if not review:rows.append(check('source-api-review','U',reason='Full API/business-in-production review requires explicit source-bound reviewer record.'))
 elif review.get('source_sha256')!=sha(p) or not review.get('reviewer') or not review.get('reason') or review.get('status') not in {'P','F'}:
  rows.append(check('source-api-review','U',reason='API review lacks exact source hash, reviewer, rationale or P/F disposition.'))
 else:rows.append(check('source-api-review',review['status'],'Public API; business logic in production; thin bridges',review.get('findings',[]),review['reason'],[{'path':ref(p),'sha256':sha(p)}]))
 return rows

def grade_task(task,case,platform,observation_path,root=None,manual=None,source_root=None,api_review=None):
 task=Path(task).resolve();op=Path(observation_path).resolve();artifact_root=Path(root).resolve() if root is not None else op.parent
 if case not in {'P1','P2','H1'} or platform not in {'ios','android'}:raise ValueError('Exact approved case and native platform required')
 
 for name,expected_hash in read(D/'TOOL-PINS.json').items():
  if sha(R/'candidate-v7/scripts'/name)!=expected_hash:raise ValueError('Frozen evaluator tool changed: '+name)
 seal=task/'SEAL.json'
 if seal.is_file():
  for rel,expected_hash in read(seal)['files'].items():
   if sha(D/rel)!=expected_hash:raise ValueError('Sealed design/oracle file changed: '+rel)
 source=task/('private' if case=='H1' else 'public');approval=read(source/'approval.json');lock=read(source/'design-lock.json');digest=approval['design_lock_sha256'];dc.validate_lock(lock,digest)
 plan=read(source/'compiled'/case/platform/'plan.json');dc.verify_generated(plan,lock,digest,platform)
 table=[r for r in read(task/'private/acceptance-table.json')['rows'] if r['case']==case and r['platform']==platform]
 inputs=[];obs=read(op);evidence=[{'path':ref(op),'sha256':sha(op)}]
 # The adapter writes the exact fixture at the observation sibling; Android injects actions.
 supplied=op.parent/'fixtures.json';approved=read(source/'compiled'/case/'fixtures.json')
 if supplied.is_file():
  got=read(supplied);embedded=got.pop('actions',None);ok=got==approved
  inputs.append(check('caller-fixture','P' if ok else 'F',approved,got,'Exact public/hidden caller fixture identity after removing only adapter-injected actions.',[{'path':ref(supplied),'sha256':sha(supplied)}]))
  if embedded is not None:inputs.append(check('embedded-actions','P' if embedded==read(source/'compiled'/case/platform/'actions.json') else 'F',reason='Android injected action route must equal the frozen compiled route.'))
 else:inputs.append(check('caller-fixture','U',reason='Adapter fixture copy absent; caller input identity not independently available.'))
 if platform=='android':
  conf=obs.get('configuration',{});exp={'font_scale':approved['fontScale'],'night_mode_mask':32 if approved['theme']=='dark' else 16,'direction':approved['direction']}
  got={k:conf.get(k) for k in exp};direction_proof=direction(got['direction'],encoding=ENCODING);got['direction']=direction_proof['canonical'];st='U' if any(v is None for v in got.values()) else 'P' if got==exp else 'F'
 else:
  envs=[s.get('runtime',{}).get('actual_environment') for s in obs.get('snapshots',[])];envs=[e for e in envs if e];exp={k:approved[k] for k in ['theme','dynamic_type','direction']};got=[{k:e.get(k) for k in exp} for e in envs];st='U' if not got else 'P' if all(e==exp for e in got) else 'F'
 inputs.append(check('native-environment',st,exp,got,'Actual native caller environment; absence remains U.'))
 if platform=='android':inputs[-1]['direction_encoding_proof']=direction_proof
 manual_data=read(manual) if isinstance(manual,(str,Path)) else manual
 # native_checks enforces original observation hashes, exact state indices and PNG hashes.
 try:
  if manual_data:
   for decision in manual_data.get('decisions',[]):
    for image in decision.get('evidence',[]):
     image_path=(artifact_root/image['path']).resolve()
     if not image_path.is_relative_to(artifact_root) or image_path.suffix.lower()!='.png' or not image_path.is_file() or image_path.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Manual evidence must be an original state PNG within artifact root')
  report=nc.evaluate(plan,obs,platform,manual_data,artifact_root,sha(op),lock,digest)
 except (ValueError,KeyError,TypeError,OSError,IndexError) as exc:
  report={'assertions':[],'status':'needs_review','error':str(exc)}
  inputs.append(check('native-evidence-validity','F',reason='Frozen native evaluator rejected evidence: '+str(exc)))
 results={r['id']:r for r in report.get('assertions',[])}
 rows=[];invalid=any(r['status']=='F' for r in inputs if r['id'] in {'caller-fixture','embedded-actions','native-environment','native-evidence-validity'})
 for required in table:
  row=copy.deepcopy(required);row.pop('applicable');row.pop('plan_assertion_id');row['actual']=None;row['snapshot_indices']=[];row['evidence']=evidence
  if not required['applicable']:row.update(status='N/A',reason=required['reason'])
  else:
   result=results.get(required['plan_assertion_id'],{});row.update(status=status(result.get('status')),actual=result.get('actual'),snapshot_indices=result.get('snapshot_indices',[]),reason=result.get('reason','Native assertion not assessed'))
   if invalid:row.update(status='U',reason='Input/native evidence integrity failed; applicable row remains in denominator.')
   if row['class']=='visual' and row['state'] in {'loaded','replaced'} and row['status']=='P' and not report.get('states',{}).get(row['state'],{}).get('complete'):
    row.update(status='U',reason='Full-layout visual pass withheld: original state lacks complete native interval coverage.')
   if platform=='ios' and row['class']=='native_style':row.update(status='U',actual=None,reason='Generic computed SwiftUI typography/color/text layout is not exposed by public native collector; visual judgment is separate.')
  for index in row['snapshot_indices']:
   image_path=obs.get('snapshots',[])[index].get('screenshot')
   if image_path:
    path=(artifact_root/image_path).resolve()
    if path.is_file() and path.is_relative_to(artifact_root):row['evidence']=row['evidence']+[{'path':ref(path),'sha256':sha(path),'snapshot_index':index}]
  rows.append(row)
 counts={s:sum(r['status']==s for r in rows) for s in ['P','F','U','N/A']}
 return dict(schema_version=1,task=task.name,case=case,platform=platform,design_lock_sha256=digest,rows=rows,counts=counts,input_checks=inputs,api_checks=api_checks(task,platform,source_root,api_review),native_report=report,evidence=evidence,scope='Complete approved denominator. U and N/A are not passes. Input/API checks do not enter acceptance denominator.')

def match_claims(grade,claims):
 """Claims: exact case/platform/state/requirement, expected, unit, status F/P/U."""
 entries=claims.get('claims',[]) if isinstance(claims,dict) else claims
 index={(r['case'],r['platform'],r['state'],r['requirement']):r for r in grade['rows']};out=[]
 for i,c in enumerate(entries):
  key=tuple(c.get(k) for k in ['case','platform','state','requirement']);row=index.get(key)
  verdict='F';reason='No exact approved case/platform/state/requirement match'
  if row:
   if 'expected' not in c or 'unit' not in c or c['expected']!=row['expected'] or c['unit']!=row['unit']:reason='Claim expected value/unit differs from the frozen requirement'
   elif c.get('status') not in {'P','F','U'}:reason='Claim requires explicit P/F/U status'
   elif c['status']=='U' or row['status']=='U':verdict='U';reason='Claim or independent applicable observation remains uncertain'
   elif c['status']==row['status']:verdict='P';reason='Exact scoped claim is supported by independent native/visual disposition'
   else:reason='Independent row contradicts the scoped claim or marks it N/A'
  out.append(dict(claim_index=i,status=verdict,reason=reason,oracle_status=row['status'] if row else None,key=dict(zip(['case','platform','state','requirement'],key))))
 return {'claims':out,'counts':{s:sum(c['status']==s for c in out) for s in ['P','F','U']}}

def compare_pair(a,b):
 def indexed(g):
  out={}
  for r in g['rows']:
   if r['class'] not in NATIVE_CLASSES:continue
   k=tuple(r[x] for x in ['case','platform','state','requirement'])
   if k in out:raise ValueError('Duplicate native denominator cell')
   out[k]=r
  return out
 aa,bb=indexed(a),indexed(b)
 if set(aa)!=set(bb):raise ValueError('Pair must include the same complete native denominator')
 paired=[]
 for k,ar in aa.items():
  br=bb[k]
  if (ar['expected'],ar['unit'],ar['op'],ar['tolerance'])!=(br['expected'],br['unit'],br['op'],br['tolerance']):raise ValueError('Pair expected value/precision differs')
  paired.append(dict(case=k[0],platform=k[1],state=k[2],requirement=k[3],**{'class':ar['class']},a=ar['status'],b=br['status']))
 return dict(rows=paired,denominator=len(paired),counts={alias:{s:sum(r[alias]==s for r in paired) for s in ['P','F','U','N/A']} for alias in ['a','b']},scope='Native classes only; visual and separate input/API integrity are excluded from pair acceptance counts.')
