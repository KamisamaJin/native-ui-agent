from foundation_cases import *
import tarfile,datetime
# All executed helpers were synchronous; command arrays passed to iOS command() were in-process mocks only.
invocations=[]
for script in ['run_foundation_arm.py','diagnostic_root_probe.py','run_integration_arm.py']:
 for name in ['candidate-v13.4','baseline-v12.6-common-1']:
  invocations.append({'argv':['python3','-B',str(ROOT/'checks'/script),'--arm',name,'--path',str(ROOT.parents[1]/name)],'evidence_class':'HOST Python evaluation of SIMULATED fixtures','provenance':'Exact command reconstructed from observed tool invocation; paths expanded to absolute for handoff. Script source/results retained.','individual_wall_time':'not separately captured; no timing claim','native_sdk_command':False})
save(ROOT/'raw'/'invocation-records.json',{'commands':invocations,'other_host_command':'raw/original-baseline-commit-check.json','real_sdk_build_test_device_calls':0,'performance_samples':0})
skill=Path('/Users/rex/.codex/skills/.system/skill-creator/SKILL.md');text=skill.read_text();(ROOT/'raw'/'skill-creator-independent-forward-testing.txt').write_text(text[text.index('## Independent Forward-Testing'):]);save(ROOT/'raw'/'skill-creator-source.json',{'path':str(skill),'sha256':sha(skill)})
archive_root=ROOT/'archives';archive_root.mkdir(exist_ok=False);rows=[]
for p in sorted(ROOT.rglob('*')):
 if p.is_relative_to(archive_root):continue
 if p.is_symlink():rows.append({'path':str(p.relative_to(ROOT)),'type':'symlink','target':os_readlink(p)if False else __import__('os').readlink(p)})
 elif p.is_file():rows.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
manifest=save(archive_root/'RAW-MANIFEST.json',{'candidate':'candidate-v13.4','baseline':'baseline-v12.6-common-1','native_runs':0,'files':rows});archive=archive_root/'RAW-EVIDENCE.tar'
with tarfile.open(archive,'x')as tf:
 for row in rows:tf.add(ROOT/row['path'],arcname=row['path'],recursive=False)
bad=[]
with tarfile.open(archive,'r')as tf:
 by={m.name:m for m in tf.getmembers()}
 for row in rows:
  m=by[row['path']]
  if row.get('type')=='symlink':
   if not m.issym()or m.linkname!=row['target']:bad.append(row['path'])
  elif hashlib.sha256(tf.extractfile(m).read()).hexdigest()!=row['sha256']:bad.append(row['path'])
if bad:raise RuntimeError('Archive mismatch '+repr(bad))
save(archive_root/'ARCHIVE-SEAL.json',{'verified':True,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size}for p in [manifest,archive]],'process_resource_closure':'All helper processes synchronous and complete; no Resources/native process/device/cache acquisition was performed. Synthetic fixtures/reports intentionally retained as evidence.','native_runs':0})
print(json.dumps({'archive_verified':True,'files':len(rows),'native_runs':0},indent=2))
