from pathlib import Path
import json, hashlib, shutil, datetime
ROOT=Path(__file__).resolve().parents[1]
POOLED=ROOT.parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v): Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2)+'\n')
pins={'CANDIDATE-FREEZE-6.json':'b65d88a6c03a0bc9cff36c40df5bf54e6f54ad0ee1b96616b7f71e277a342982','BASELINE-COMMON-FREEZE-2.json':'c0d4b7b78974372343b5035f9d97052f123e27daeb3dfc2d472990c40f502f59'}
results=[]
for filename,expected in pins.items():
 p=POOLED/filename;meta=json.loads(p.read_text());arm=POOLED/meta['candidate']
 errors=[key for key,value in meta['files'].items()if sha(arm/key)!=value]
 actual_paths={str(p.relative_to(arm))for p in arm.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
 result={'freeze':filename,'freeze_sha256':sha(p),'pin':expected,'exact_pin':sha(p)==expected,'arm':str(arm),'file_count':len(meta['files']),'mismatches':errors,'unexpected_files':sorted(actual_paths-set(meta['files']))}
 assert result['exact_pin'] and not errors and not result['unexpected_files'],result
 shutil.copyfile(p,ROOT/'raw'/filename);results.append(result)
spec=POOLED/'qualification/spec/lazy-coverage/encoding-domain'
seal=json.loads((spec/'SEAL.json').read_text())
save(ROOT/'raw/domain-seal-original.json',seal)
save(ROOT/'raw/domain-spec-original-hashes.json',{str(p.relative_to(spec)):sha(p)for p in spec.rglob('*')if p.is_file()})
provider=POOLED/'qualification/provider-review'
save(ROOT/'raw/provider-source-review-hashes.json',{str(p.relative_to(provider)):sha(p)for p in provider.rglob('*')if p.is_file()})
prior=ROOT.parent/'review-5';index=json.loads((prior/'raw-artifact-index.json').read_text())
wrong=[e['path']for e in index['entries']if 'sha256'in e and sha(prior/e['path'])!=e['sha256']]
assert not wrong,wrong
for filename in ['review.json','REVIEW.md','OPEN-ISSUES.md','SEAL.json','raw-artifact-index.json']:
 dest=ROOT/'legacy-review5'/filename;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(prior/filename,dest)
shutil.copytree(prior/'fixtures/pristine',ROOT/'legacy-review5/pristine')
save(ROOT/'raw/review5-preserved.json',{'prior_root':str(prior),'files_verified':len(index['entries']),'mismatches':wrong,'seal_sha256':sha(prior/'SEAL.json'),'outcomes':json.loads((prior/'review.json').read_text())['raw_results'],'old_fixture_bytes_copied_without_schema_changes':True})
save(ROOT/'raw/freeze-verification.json',results)
save(ROOT/'OWNERSHIP.json',{'review':'review-6','owner':'/root/v13_default_qualification','root':str(ROOT),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'permission':'Only writes under this positive-owned review root. All SDK/device commands forbidden. Synchronous Python and in-process non-forwarding mocks only.','native_runs':0,'performance_samples':0,'business_tasks':0})
print(json.dumps({'frozen':results,'prior_verified':len(index['entries'])},indent=2))
