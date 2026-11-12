from encoding_cases import *
import datetime,tarfile,os
pooled=ROOT.parents[1]
def verify_index(base,index):
 bad=[]
 for entry in index['entries']:
  p=base/entry['path']
  if entry.get('type')=='symlink':
   if not p.is_symlink()or os.readlink(p)!=entry['target']:bad.append(entry['path'])
  elif sha(p)!=entry['sha256']:bad.append(entry['path'])
 return bad
freezes=[]
for name,expected in[('CANDIDATE-FREEZE-6.json','b65d88a6c03a0bc9cff36c40df5bf54e6f54ad0ee1b96616b7f71e277a342982'),('BASELINE-COMMON-FREEZE-2.json','c0d4b7b78974372343b5035f9d97052f123e27daeb3dfc2d472990c40f502f59')]:
 meta=json.loads((pooled/name).read_text());arm=pooled/meta['candidate'];bad=[n for n,h in meta['files'].items()if sha(arm/n)!=h];assert sha(pooled/name)==expected and not bad
 freezes.append({'pin':name,'sha256':expected,'files_verified':len(meta['files']),'mismatches':bad})
spec=pooled/'qualification/spec/lazy-coverage/encoding-domain';provider=pooled/'qualification/provider-review';seals=[]
for base,expected in[(spec,'edd57776951d2331d79fb91fa5a8182437f3686c691a6876f5166a7692fbb5fb'),(provider,'cf06e358a011e941cefd0216939e2077f6b3c4979043930c0bcbdd6327d45f8f')]:
 meta=json.loads((base/'SEAL.json').read_text());bad=[e['path']for e in meta['files']if sha(base/e['path'])!=e['sha256']];assert sha(base/'SEAL.json')==expected and not bad
 seals.append({'root':str(base),'seal_sha256':expected,'files_verified':len(meta['files']),'mismatches':bad})
prior=ROOT.parent/'review-5';index=json.loads((prior/'raw-artifact-index.json').read_text());bad=verify_index(prior,index);assert not bad
assert sha(prior/'review.json')==sha(ROOT/'legacy-review5/review.json')and sha(prior/'SEAL.json')==sha(ROOT/'legacy-review5/SEAL.json')
save(ROOT/'raw/final-immutable-audit.json',{'freezes':freezes,'independent_seals':seals,'prior_review5':{'entries_verified':len(index['entries']),'mismatches':bad,'exact85_outcomes_retained':True,'exact6_old_issues_retained':True,'report_and_seal_match_initial_copy':True},'native_runs':0})

# Describe exact executions from tool-call records and durable per-run artifacts;
# do not relabel reconstructed command inventory as an original shell transcript.
commands=[]
for script,args,result in[
 ('setup.py',[],'raw/freeze-verification.json'),
 ('run_geometry.py',['--arm','candidate-v13.5','--path','validation/pooled-forward/candidate-v13.5'],'raw/candidate-v13.5-geometry-results.json'),
 ('run_geometry.py',['--arm','baseline-v12.6-common-2','--path','validation/pooled-forward/baseline-v12.6-common-2'],'raw/baseline-v12.6-common-2-geometry-results.json'),
 ('run_domain.py',['--arm','candidate-v13.5','--path','validation/pooled-forward/candidate-v13.5'],'raw/candidate-v13.5-domain-results.json'),
 ('run_domain.py',['--arm','baseline-v12.6-common-2','--path','validation/pooled-forward/baseline-v12.6-common-2'],'raw/baseline-v12.6-common-2-domain-results.json'),
 ('run_semantics.py',['--arm','candidate-v13.5','--path','validation/pooled-forward/candidate-v13.5'],'raw/candidate-v13.5-semantics-results.json'),
 ('run_semantics.py',['--arm','baseline-v12.6-common-2','--path','validation/pooled-forward/baseline-v12.6-common-2'],'raw/baseline-v12.6-common-2-semantics-results.json'),
 ('run_default.py',['--arm','candidate-v13.5','--path','validation/pooled-forward/candidate-v13.5'],'raw/candidate-v13.5-default-results.json'),
 ('run_default.py',['--arm','candidate-v13.5','--path','validation/pooled-forward/candidate-v13.5','--run-name','default-retry-1'],'raw/candidate-v13.5-default-retry-1-results.json'),
 ('run_baseline_default.py',['--arm','baseline-v12.6-common-2','--path','validation/pooled-forward/baseline-v12.6-common-2','--run-name','default-common'],'raw/baseline-v12.6-common-2-default-common-results.json'),
 ('run_admitted_runtime.py',['--arm','candidate-v13.5','--path','validation/pooled-forward/candidate-v13.5'],'raw/candidate-v13.5-admitted-runtime-results.json'),
 ('run_admitted_runtime.py',['--arm','candidate-v13.5','--path','validation/pooled-forward/candidate-v13.5','--run-name','admitted-runtime-retry-1'],'raw/candidate-v13.5-admitted-runtime-retry-1-results.json'),
 ('run_admitted_runtime.py',['--arm','baseline-v12.6-common-2','--path','validation/pooled-forward/baseline-v12.6-common-2'],'raw/baseline-v12.6-common-2-admitted-runtime-results.json'),
 ('audit_port.py',[],'raw/common-port-audit.json'),('verify_admitted_oracles.py',[],'raw/admitted-original16-and-global-joint-oracles.json'),('independent_oracles.py',[],'raw/oracle-joint-witness-inconsistency.json')]:
 commands.append({'argv':['python3',str(ROOT/'checks'/script),*args],'recording_kind':'Command inventory reconstructed from executed tool calls; default public-CLI command/stdout/stderr are stored verbatim per run. Initial check-script variants are separately retained.','current_check_sha256':sha(ROOT/'checks'/script),'result':result,'result_sha256':sha(ROOT/result),'evidence_class':'HOST/SIMULATED only'})
save(ROOT/'raw/command-source-result-proofs.json',{'cwd':str(pooled.parents[1]),'SDK_commands_executed':[],'external_HOST_subprocesses':'Read-only git archive and synchronous plutil JSON conversion; no running test group or SDK process retained. All xcrun/xcodebuild emissions captured by in-process command mocks.','commands':commands,'current_check_source_hashes':{str(p.relative_to(ROOT)):sha(p)for p in(ROOT/'checks').glob('*.py')},'original_source_version_records':['raw/encoding-cases-first-syntax-failure.py','raw/default-first-run-harness.py','raw/admitted-runtime-first-syntax-failure.py','raw/admitted-runtime-initial-runtime-harness.py'],'raw_failure_transcriptions':['raw/setup-first-failure.txt','raw/geometry-first-harness-failure.txt','raw/default-first-run-environment-note.json','raw/admitted-runtime-first-harness-failure.txt'],'provenance_limit':'Harness source/result hashes provide reproducibility. Only captured per-default command JSON claims verbatim stdout/stderr; this inventory does not claim retroactive raw console transcription.'})

# Archive all generated raw/source/failure artifacts before declaring closure.
archive=ROOT/'archives/RAW-EVIDENCE.tar.gz';archive.parent.mkdir(exist_ok=True)
assert not archive.exists()
members=[p for p in sorted(ROOT.rglob('*'))if p.is_file()or p.is_symlink()]
members=[p for p in members if 'archives'not in p.relative_to(ROOT).parts and p.name not in{'SEAL.json','raw-artifact-index.json','RESOURCE-CLOSURE.json'}]
with tarfile.open(archive,'w:gz',compresslevel=6,dereference=False)as tf:
 for p in members:tf.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
bad=[]
with tarfile.open(archive,'r:gz')as tf:
 for m in tf.getmembers():
  p=ROOT/m.name
  if m.issym():
   if not p.is_symlink()or m.linkname!=os.readlink(p):bad.append(m.name)
  elif m.isfile():
   if hashlib.sha256(tf.extractfile(m).read()).hexdigest()!=sha(p):bad.append(m.name)
assert not bad
save(ROOT/'raw/archive-verification.json',{'archive':str(archive),'archive_sha256':sha(archive),'members_verified':len(members),'mismatches':bad,'native_artifacts_from_this_review':0,'all_raw_and_failures_archived_before_closure':True})
save(ROOT/'RESOURCE-CLOSURE.json',{'closed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':'/root/v13_default_qualification','positive_owned_root':str(ROOT),'private_devices_created':0,'real_SDK_processes_started':0,'test_daemons_or_process_groups_started':0,'synchronous_host_subprocesses_finished':True,'test_processes_terminated':[],'resource_scope':'All resource-manager/devices/SDK calls simulated in-process. Host Python, read-only Git archive and plutil completed synchronously. No device/native cache/project run was acquired or cleaned.','archive_verified_before_closure':str(ROOT/'raw/archive-verification.json'),'owned_probe_artifacts':'retained; no deletion required','pending_workflow_files':'Simulated workflow journals are retained inert files; no watcher/device/process exists.'})
entries=[]
for p in sorted(ROOT.rglob('*')):
 if p.name in{'SEAL.json','raw-artifact-index.json'}and p.parent==ROOT:continue
 if p.is_symlink():entries.append({'path':str(p.relative_to(ROOT)),'type':'symlink','target':os.readlink(p),'sha256_of_link_text':hashlib.sha256(os.readlink(p).encode()).hexdigest()})
 elif p.is_file():entries.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
save(ROOT/'raw-artifact-index.json',{'review':'review-6-common-pixel-encoding-domain','native_artifacts':'NONE produced; all native fields simulated','entries':entries,'files':len(entries),'total_file_bytes':sum(e.get('bytes',0)for e in entries)})
assert not verify_index(ROOT,json.loads((ROOT/'raw-artifact-index.json').read_text()))
seal_files=['review.json','REVIEW.md','OPEN-ISSUES.md','OWNERSHIP.json','RESOURCE-CLOSURE.json','raw-artifact-index.json','raw/final-immutable-audit.json','raw/command-source-result-proofs.json','raw/common-port-audit.json','raw/archive-verification.json','archives/RAW-EVIDENCE.tar.gz']
save(ROOT/'SEAL.json',{'review_id':'review-6-common-pixel-encoding-domain','sealed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'NOT_QUALIFIED','confirmed_issue_ids':['SC07','SC08','SC09','SC10'],'primary_raw_rows':213,'primary_raw_counts':{'P':169,'F':44},'all_recorded_raw_rows':232,'all_recorded_raw_counts':{'P':181,'F':51},'candidate_unchanged':True,'baseline_unchanged':True,'review5_exact85_outcomes_6_issues_unchanged':True,'native_runs_this_review':0,'performance_samples':0,'business_tasks':0,'files':{n:sha(ROOT/n)for n in seal_files}})
print(json.dumps({'sealed':str(ROOT/'SEAL.json'),'indexed_files':len(entries),'archive_members':len(members),'archive_bytes':archive.stat().st_size,'native_runs':0,'all_raw_rows':232},indent=2))
