import os,json,hashlib,time,datetime
from pathlib import Path
R=Path(__file__).resolve().parent
excluded={'seal.json','seal.sha256','seal-verification.json'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prefix=json.loads((R/'original-prefix-seal.json').read_text());prefixcheck={k:sha(R/k)==v for k,v in prefix['files'].items()};assert all(prefixcheck.values())
files={};links={}
for base,dirs,names in os.walk(R,followlinks=False):
 here=Path(base);dirs[:]=[d for d in dirs if d not in {'cache','__pycache__'}]
 for d in list(dirs):
  p=here/d
  if p.is_symlink():links[str(p.relative_to(R))]=os.readlink(p);dirs.remove(d)
 for name in names:
  p=here/name;rel=str(p.relative_to(R))
  if rel in excluded:continue
  if p.is_symlink():links[rel]=os.readlink(p)
  elif p.is_file():files[rel]={'sha256':sha(p),'bytes':p.stat().st_size}
manifest={'version':1,'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Every non-cache probe artifact, including original captures/attachments/xcresults/logs, pinned design, observations, review submissions/findings/checks, source copies and tool revision snapshots. Cache dependency/build artifacts excluded; their identities are retained in native manifests and bootstrap record.','excluded':['cache/**','**/__pycache__/**']+sorted(excluded),'files':files,'symlinks':links,'original_prefix_unchanged':prefixcheck}
raw=json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();digest=hashlib.sha256(raw).hexdigest();(R/'seal.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');(R/'seal.sha256').write_text(digest+'\n')
assert all(sha(R/p)==info['sha256']for p,info in files.items());assert all(os.readlink(R/p)==target for p,target in links.items())
verification={'verified':True,'canonical_seal_sha256':digest,'file_count':len(files),'symlink_count':len(links),'total_bytes':sum(v['bytes']for v in files.values()),'original_png_count':sum(1 for p in files if p.startswith('captures/')and p.endswith('.png')),'scope_limit':'Hash identity, not authorship, independent agreement or semantic correctness.'}
(R/'seal-verification.json').write_text(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification))
