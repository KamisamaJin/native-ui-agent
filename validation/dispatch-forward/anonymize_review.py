#!/usr/bin/env python3
"""Identity/path-only projection of every original self-review claim and artifact.

Originals remain immutable. This projection is not new review evidence. Only
identity/path strings and hashes of redacted derived files may change; native
observations/images and business claim text remain original bytes/values.
"""
import argparse,json,hashlib,shutil,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--submission',required=True);p.add_argument('--anonymous-id',required=True);p.add_argument('--workspace',required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args();out=a.destination.resolve();assert not out.exists();out.mkdir(parents=True)
 src=R/'private/submissions'/a.submission;original=read(src/'review.json');assert sha(src/'review.json')==read(src/'review-seal.json')['reviewSHA256']
 subprocess.run([sys.executable,str(R/'make_grade_capsule.py'),'--phase','d0','--anonymous-id',a.anonymous_id,'--source-capsule',str(src/'d0'),'--corpus',str(R/'evidence/own-d0'/a.submission),'--inputs',str(R/'private/inputs/d0-v2'),'--destination',str(out/'own')],check=True,stdout=subprocess.DEVNULL)
 aliases={}
 for prefix in ['evidence/own-d0','cache/own-d0','cache/own-d0-retry']:
  aliases[str(R/prefix/a.submission)]='own/native';aliases['validation/dispatch-forward/'+prefix+'/'+a.submission]='own/native'
 aliases[str(src/'review-assets')]='review-assets';aliases[str(src)]='review-records';aliases[str(R/'cache'/a.workspace)]='own/source';aliases[str(R/'design/public')]='public'
 aliases[a.submission]=a.anonymous_id
 for name in ['common-v3','candidate-v4']:aliases[name]='opaque-collector'
 def transform(v):
  if isinstance(v,str):
   for before,after in sorted(aliases.items(),key=lambda t:-len(t[0])):v=v.replace(before,after)
   return v
  if isinstance(v,list):return [transform(x)for x in v]
  if isinstance(v,dict):return {k:transform(x)for k,x in v.items()}
  return v
 artifacts=[];json_sources={}
 for f in sorted((src/'review-assets').rglob('*')):
  if not f.is_file():continue
  assert f.stat().st_size<30_000_000,'Unexpected review artifact size'
  dest=out/'review-assets'/f.relative_to(src/'review-assets');dest.parent.mkdir(parents=True,exist_ok=True)
  if f.suffix=='.json':json_sources[dest]=transform(read(f));save(dest,json_sources[dest])
  elif f.suffix in {'.py','.md','.txt','.log'}:dest.write_text(transform(f.read_text()))
  else:shutil.copy2(f,dest)
  artifacts.append((f,dest))
 for f in sorted((R/'design/public').glob('*')):
  if f.is_file():(out/'public').mkdir(exist_ok=True);shutil.copy2(f,out/'public'/f.name)
 projection=transform(original)
 # Change a digest only when its referenced derived file was identity-redacted.
 # Iterate the small dependency DAG; original native/PNG hashes never change.
 for _ in range(len(artifacts)+2):
  hashes={sha(srcfile):sha(dst)for srcfile,dst in artifacts if sha(srcfile)!=sha(dst)}
  def refs(v):
   if isinstance(v,str):return hashes.get(v,v)
   if isinstance(v,list):return [refs(x)for x in v]
   if isinstance(v,dict):return {k:refs(x)for k,x in v.items()}
   return v
  changed=False
  for dst,base in json_sources.items():
   d=refs(base);encoded=json.dumps(d,indent=2,ensure_ascii=False)+'\n'
   if dst.read_text()!=encoded:dst.write_text(encoded);changed=True
  projection=refs(transform(original))
  if not changed:break
 else:raise AssertionError('Cyclic derived hash references cannot be safely projected')
 assert len(projection.get('findings',[]))==len(original.get('findings',[]))
 for raw,projected in zip(original.get('findings',[]),projection.get('findings',[])):
  for key in ['id','platform','case','checkpoint','category','method','target','aspect','certainty','claim','expected','observed']:
   if key in raw:assert projected[key]==raw[key],('Semantic finding field changed',key)
 save(out/'review.json',projection)
 save(out/'projection-provenance.json',{'anonymous_id':a.anonymous_id,'originalReviewSHA256':sha(src/'review.json'),'projectedReviewSHA256':sha(out/'review.json'),'allFindingsPreserved':len(original.get('findings',[])),'allowedChanges':'Identity/path strings and hashes of corresponding redacted derived artifacts only. Claim/expected/observed/uncertainty/aspect fields are exactly equal. Original native and PNG bytes unchanged. Original report and private alias table are published after release.','derivedArtifacts':[{'path':str(dst.relative_to(out)),'originalSHA256':sha(f),'projectedSHA256':sha(dst)}for f,dst in artifacts]})
 save(out/'SEAL.json',{'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'files':{str(f.relative_to(out)):sha(f)for f in sorted(out.rglob('*'))if f.is_file()}})
 save(src/'review-anonymization-private.json',{'anonymous_id':a.anonymous_id,'aliases':aliases,'projectionSealSHA256':sha(out/'SEAL.json')})
 print(json.dumps({'anonymous_id':a.anonymous_id,'findingsPreserved':len(original.get('findings',[])),'destination':str(out)}))
if __name__=='__main__':main()
