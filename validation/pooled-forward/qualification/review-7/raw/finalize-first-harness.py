from encoding_cases import *
import tarfile,datetime,os
pooled=ROOT.parents[1]
def verify_index(base,index):
 bad=[]
 for e in index['entries']:
  p=base/e['path']
  if e.get('type')=='symlink':
   if not p.is_symlink()or os.readlink(p)!=e['target']:bad.append(e['path'])
  elif sha(p)!=e['sha256']:bad.append(e['path'])
 return bad
freezes=[]
for filename,pin in[('CANDIDATE-FREEZE-7.json','a4063eae16a0541d7046099a1b4e6d5f1abe10aff2f1613dac716aa65d86bd81'),('BASELINE-COMMON-FREEZE-3.json','871422cc1f5bf5b6a979b9cbd9387a7f6821a5f51c78f1d87c8c36a59fb3281e')]:
 meta=load(pooled/filename);assert sha(pooled/filename)==pin;bad=[n for n,h in meta['files'].items()if sha(pooled/meta['candidate']/n)!=h];assert not bad;freezes.append({'freeze':filename,'sha256':pin,'files_verified':len(meta['files']),'mismatches':bad})
prior=ROOT.parent/'review-6';seal=load(prior/'SEAL.json');assert all(sha(prior/n)==h for n,h in seal['files'].items());index=load(prior/'raw-artifact-index.json');assert not verify_index(prior,index);assert sha(prior/'SEAL.json')==sha(ROOT/'prior-review6/SEAL.json');assert sha(prior/'review.json')==sha(ROOT/'prior-review6/review.json')
seals=[]
for base,pin in[(pooled/'qualification/spec/lazy-coverage/encoding-domain','edd57776951d2331d79fb91fa5a8182437f3686c691a6876f5166a7692fbb5fb'),(pooled/'qualification/provider-review','cf06e358a011e941cefd0216939e2077f6b3c4979043930c0bcbdd6327d45f8f')]:
 meta=load(base/'SEAL.json');assert sha(base/'SEAL.json')==pin;bad=[e['path']for e in meta['files']if sha(base/e['path'])!=e['sha256']];assert not bad;seals.append({'root':str(base),'sha256':pin,'files_verified':len(meta['files']),'mismatches':bad})
save(ROOT/'raw/final-immutable-audit.json',{'freezes':freezes,'prior_review6_seal_sha256':sha(prior/'SEAL.json'),'prior_review6_entries_verified':len(index['entries']),'prior_review6_report_and_all232_rows_unchanged':True,'independent_seals':seals,'native_runs':0})
commands=[]
for arm in['candidate-v13.6','baseline-v12.6-common-3']:
 for script,group in[('run_delta.py','delta'),('run_csp.py','csp'),('run_metadata_scope.py','metadata-scope')]:
  result=f'raw/{arm}-{group}-results.json';commands.append({'argv':['python3','-B',str(ROOT/'checks'/script),'--arm',arm,'--path',str(pooled/arm)],'check_sha256':sha(ROOT/'checks'/script),'results':result,'results_sha256':sha(ROOT/result)})
 result=f'raw/{arm}-csp-bound-result.json';commands.append({'argv':['python3','-B',str(ROOT/'checks/run_csp_bound.py'),'--arm',arm,'--path',str(pooled/arm)],'check_sha256':sha(ROOT/'checks/run_csp_bound.py'),'results':result,'results_sha256':sha(ROOT/result)})
for script,arm,run in[('run_default.py','candidate-v13.6','default'),('run_baseline_default.py','baseline-v12.6-common-3','default-common')]:
 result=f'raw/{arm}-{run}-results.json';commands.append({'argv':['python3','-B',str(ROOT/'checks'/script),'--arm',arm,'--path',str(pooled/arm),'--run-name',run],'check_sha256':sha(ROOT/'checks'/script),'results':result,'results_sha256':sha(ROOT/result),'verbatim_public_CLI_commands_stdout_stderr':'work/'+arm+'/'+run+'/*-command.json'})
save(ROOT/'raw/command-source-result-proofs.json',{'cwd':str(pooled.parents[1]),'commands':commands,'current_check_hashes':{str(p.relative_to(ROOT)):sha(p)for p in(ROOT/'checks').glob('*.py')},'frozen_command_sources':'Freeze manifests pin all loaded candidate/baseline bytes. Sidecars independently document new ABI fields and original observation/PNG provenance.','initial_harness_script':'raw/run-delta-first-harness.py','initial_harness_error':'raw/run-delta-first-harness-error.txt','recording_limit':'Inventory reconstructed from executed tool calls; per-default CLI records contain verbatim stdout/stderr. No retroactive raw console capture claimed. -B and PYTHONDONTWRITEBYTECODE=1 are equivalent no-bytecode selections; actual invocations used latter.','SDK_commands_executed':[],'actual_HOST_subprocesses':'Only read-only Git archive and synchronous plutil inventory JSON conversion; all xcrun/xcodebuild/SDK commands non-forwarding in-process mocks.'})
archive=ROOT/'archives/RAW-EVIDENCE.tar.gz';archive.parent.mkdir(exist_ok=True);assert not archive.exists();members=[p for p in sorted(ROOT.rglob('*'))if(p.is_file()or p.is_symlink())and'archives'not in p.relative_to(ROOT).parts and not(p.parent==ROOT and p.name in{'SEAL.json','raw-artifact-index.json','RESOURCE-CLOSURE.json'})]
with tarfile.open(archive,'w:gz',compresslevel=6,dereference=False)as tf:
 for p in members:tf.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
bad=[]
with tarfile.open(archive,'r:gz')as tf:
 for m in tf.getmembers():
  p=ROOT/m.name
  if m.issym():
   if not p.is_symlink()or os.readlink(p)!=m.linkname:bad.append(m.name)
  elif m.isfile()and hashlib.sha256(tf.extractfile(m).read()).hexdigest()!=sha(p):bad.append(m.name)
assert not bad
save(ROOT/'raw/archive-verification.json',{'archive':str(archive),'archive_sha256':sha(archive),'members_verified':len(members),'mismatches':bad,'all_own_raw_and_first_failures_archived_before_closure':True})
save(ROOT/'RESOURCE-CLOSURE.json',{'owner':'/root/v13_default_qualification','root':str(ROOT),'closed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'real_devices_acquired':0,'SDK_or_native_processes_started':0,'private_test_daemons_started':0,'test_processes_terminated':[],'synchronous_HOST_probes_finished':True,'mock_workflow_state':'retained inert files; no watcher/device/process exists','artifacts':'All original/negative/source/ABI/command artifacts archived and retained; no deletion needed','archive_verified_before_closure':str(ROOT/'raw/archive-verification.json')})
entries=[]
for p in sorted(ROOT.rglob('*')):
 if p.parent==ROOT and p.name in{'SEAL.json','raw-artifact-index.json'}:continue
 if p.is_symlink():entries.append({'path':str(p.relative_to(ROOT)),'type':'symlink','target':os.readlink(p),'sha256_of_link_text':hashlib.sha256(os.readlink(p).encode()).hexdigest()})
 elif p.is_file():entries.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
save(ROOT/'raw-artifact-index.json',{'review':'review-7-common-correction-delta','native_artifacts_from_this_review':'NONE','entries':entries,'files':len(entries),'total_file_bytes':sum(e.get('bytes',0)for e in entries)});assert not verify_index(ROOT,load(ROOT/'raw-artifact-index.json'))
names=['review.json','REVIEW.md','OPEN-ISSUES.md','OWNERSHIP.json','RESOURCE-CLOSURE.json','raw-artifact-index.json','raw/final-immutable-audit.json','raw/command-source-result-proofs.json','raw/common-port-audit.json','raw/archive-verification.json','archives/RAW-EVIDENCE.tar.gz']
save(ROOT/'SEAL.json',{'review_id':'review-7-common-correction-delta','sealed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'NOT_QUALIFIED','confirmed_issue_ids':['SC11'],'unresolved_interpretation_ids':['SC12'],'raw_rows':268,'raw_counts':{'P':258,'F':10},'confirmed_F_rows':8,'unresolved_F_rows':2,'candidate_unchanged':True,'baseline_unchanged':True,'prior_review6_all232_outcomes_and_seal_unchanged':True,'native_runs_this_review':0,'performance_samples':0,'business_tasks':0,'files':{n:sha(ROOT/n)for n in names}})
print(json.dumps({'seal_sha256':sha(ROOT/'SEAL.json'),'indexed_entries':len(entries),'archive_members':len(members),'archive_bytes':archive.stat().st_size,'native_runs':0,'rows':268},indent=2))
