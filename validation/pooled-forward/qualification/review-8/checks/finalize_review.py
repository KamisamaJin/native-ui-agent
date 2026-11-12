from domain_support import *
import tarfile,datetime,os
def verify_index(base,index):
 bad=[]
 for e in index['entries']:
  p=base/e['path']
  if e.get('type')=='symlink':
   if not p.is_symlink()or os.readlink(p)!=e['target']:bad.append(e['path'])
  elif sha(p)!=e['sha256']:bad.append(e['path'])
 return bad
freezes=[]
for filename,pin in[('CANDIDATE-FREEZE-8.json','161e2d1881de5eeaa5c8c65a7d2e6150887ad07f79e8c1baa5816fb5d5c87e61'),('BASELINE-COMMON-FREEZE-4.json','b5929b65a9ee4073ba6ca5d02e1a00c4298fe30c3aa6643667ed5b275cf34286')]:
 meta=load(POOLED/filename);assert sha(POOLED/filename)==pin;bad=[n for n,h in meta['files'].items()if sha(POOLED/meta['candidate']/n)!=h];assert not bad;freezes.append({'freeze':filename,'sha256':pin,'files_verified':len(meta['files']),'mismatches':bad})
prior=ROOT.parent/'review-7';seal=load(prior/'SEAL.json');assert all(sha(prior/n)==h for n,h in seal['files'].items());index=load(prior/'raw-artifact-index.json');assert not verify_index(prior,index);assert sha(prior/'SEAL.json')==sha(ROOT/'prior-review7/SEAL.json');assert sha(prior/'review.json')==sha(ROOT/'prior-review7/review.json')
criterion=POOLED/'qualification/spec/quantifier-scope';assert sha(criterion/'SEAL.json')=='c7d7a3936991a88b53a65444b184ed898345b335b3a5c7f7b8d71db9d95e2772';assert all(sha(criterion/e['path'])==e['sha256']for e in load(criterion/'SEAL.json')['files'])
seals=[]
for base,pin in[(POOLED/'qualification/spec/lazy-coverage/encoding-domain','edd57776951d2331d79fb91fa5a8182437f3686c691a6876f5166a7692fbb5fb'),(POOLED/'qualification/provider-review','cf06e358a011e941cefd0216939e2077f6b3c4979043930c0bcbdd6327d45f8f')]:
 assert sha(base/'SEAL.json')==pin;bad=[e['path']for e in load(base/'SEAL.json')['files']if sha(base/e['path'])!=e['sha256']];assert not bad;seals.append({'root':str(base),'seal_sha256':pin,'mismatches':bad})
save(ROOT/'raw/final-immutable-audit.json',{'freezes':freezes,'prior_review7_seal_sha256':sha(prior/'SEAL.json'),'prior_review7_entries_verified':len(index['entries']),'all268_previous_raw_outcomes_unchanged':True,'quantifier_seal_sha256':sha(criterion/'SEAL.json'),'other_independent_seals':seals})
op=ROOT/'operator-review';pins=load(op/'source-pins.json');assert all(sha(op/'original-source'/name)==h for name,h in pins.items())
save(op/'live-source-status-unassessed.json',{'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_pinned_source':pins,'current_live_hashes_observed_without_reading_new_code':{name:sha(POOLED/name)for name in pins},'later_changes_not_qualified':'Parent reports live corrections. This review only executed the original pinned copies and does not regrade them or certify live changes.'})
opnames=['OPERATOR-REVIEW.json','OPERATOR-REVIEW.md','source-pins.json','probe-results.json','envelope-error-probe.json','live-source-status-unassessed.json']+['original-source/'+name for name in pins]
save(op/'SEAL.json',{'review':'review8-original-operators-only','sealed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_rows':9,'raw_counts':{'P':5,'F':4},'operator_issue_ids':['OB01','OB02','OB03'],'actual_benchmark_episodes':0,'native_runs':0,'speed_samples':0,'files':{name:sha(op/name)for name in opnames}})
commands=[]
for arm in['candidate-v13.7','baseline-v12.6-common-4']:
 for script,group in[('run_query_scope.py','query-scope'),('run_query_additive.py','query-additive'),('run_typed_and_regressions.py','typed-regression'),('run_corrected_regressions.py','corrected-regression')]:
  result=f'raw/{arm}-{group}-results.json';commands.append({'argv':['python3',str(ROOT/'checks'/script),'--arm',arm,'--path',str(POOLED/arm)],'check_sha256':sha(ROOT/'checks'/script),'result':result,'result_sha256':sha(ROOT/result)})
for script,arm,run in[('run_default.py','candidate-v13.7','default'),('run_baseline_default.py','baseline-v12.6-common-4','default-common')]:
 result=f'raw/{arm}-{run}-results.json';commands.append({'argv':['python3',str(ROOT/'checks'/script),'--arm',arm,'--path',str(POOLED/arm),'--run-name',run],'check_sha256':sha(ROOT/'checks'/script),'result':result,'result_sha256':sha(ROOT/result),'verbatim_public_CLI_records':'work/'+arm+'/'+run+'/*-command.json'})
for script,result in[('probe_operators.py','operator-review/probe-results.json'),('probe_envelope_error.py','operator-review/envelope-error-probe.json')]:commands.append({'argv':['python3',str(ROOT/'checks'/script)],'check_sha256':sha(ROOT/'checks'/script),'result':result,'result_sha256':sha(ROOT/result),'scope':'HOST synthetic operator/resource/replay boundary; no SDK or actual episode'})
save(ROOT/'raw/command-source-result-proofs.json',{'cwd':str(POOLED.parents[1]),'commands':commands,'check_hashes':{str(p.relative_to(ROOT)):sha(p)for p in(ROOT/'checks').glob('*.py')},'environment_selection':'PYTHONDONTWRITEBYTECODE=1; no generated frozen bytecode','recording_scope':'Command inventory reconstructed from tool calls. Actual default CLI stdout/stderr are retained verbatim in per-run command JSON; no retroactive raw shell transcript claimed.','SDK_commands_executed':[],'actual_HOST_subprocesses':'Read-only Git archive and synchronous plutil inventory decoding only. All native/resource/compile/replay/recovery boundaries intercepted in-process; no private process groups.'})
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
save(ROOT/'raw/archive-verification.json',{'archive':str(archive),'archive_sha256':sha(archive),'members_verified':len(members),'mismatches':bad,'all_raw_first_failures_and_original_operator_sources_archived_before_closure':True})
save(ROOT/'RESOURCE-CLOSURE.json',{'owner':'/root/v13_default_qualification','root':str(ROOT),'closed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'real_devices_acquired':0,'SDK_or_native_processes_started':0,'actual_benchmark_episodes':0,'private_test_daemons_started':0,'test_processes_terminated':[],'synchronous_HOST_probes_finished':True,'mock_workflow_and_benchmark_files':'Retained inert artifacts only; no real watcher/device/process exists and synthetic gate outputs are not benchmark results.','archive_verified_before_closure':str(ROOT/'raw/archive-verification.json'),'all_artifacts_retained_no_deletion_required':True})
entries=[]
for p in sorted(ROOT.rglob('*')):
 if p.parent==ROOT and p.name in{'SEAL.json','raw-artifact-index.json'}:continue
 if p.is_symlink():entries.append({'path':str(p.relative_to(ROOT)),'type':'symlink','target':os.readlink(p),'sha256_of_link_text':hashlib.sha256(os.readlink(p).encode()).hexdigest()})
 elif p.is_file():entries.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
save(ROOT/'raw-artifact-index.json',{'review':'review-8-native-query-scope-delta','native_artifacts_from_this_review':'NONE','entries':entries,'files':len(entries),'total_file_bytes':sum(e.get('bytes',0)for e in entries)});assert not verify_index(ROOT,load(ROOT/'raw-artifact-index.json'))
names=['review.json','REVIEW.md','OPEN-ISSUES.md','OWNERSHIP.json','RESOURCE-CLOSURE.json','raw-artifact-index.json','raw/final-immutable-audit.json','raw/command-source-result-proofs.json','raw/common-port-audit.json','raw/archive-verification.json','archives/RAW-EVIDENCE.tar.gz','operator-review/SEAL.json','criterion/SEAL.json']
save(ROOT/'SEAL.json',{'review_id':'review-8-native-query-scope-delta','sealed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'NOT_QUALIFIED','confirmed_issue_ids':['SC13','SC14','SC15','SC16','SC17'],'primary_rows':150,'primary_counts':{'P':110,'F':40},'confirmed_primary_F_rows':28,'initial_fixture_expectation_F_rows_preserved':12,'separate_operator_rows':9,'separate_operator_counts':{'P':5,'F':4},'operator_issue_ids':['OB01','OB02','OB03'],'candidate_unchanged':True,'baseline_unchanged':True,'prior_review7_all268_raw_and_seal_unchanged':True,'original_operator_sources_preserved':True,'new_live_operator_changes_unassessed':True,'native_runs_this_review':0,'benchmark_episodes':0,'performance_samples':0,'business_tasks':0,'files':{name:sha(ROOT/name)for name in names}})
print(json.dumps({'seal_sha256':sha(ROOT/'SEAL.json'),'indexed_entries':len(entries),'archive_members':len(members),'archive_bytes':archive.stat().st_size,'native_runs':0,'primary_rows':150,'operator_rows':9},indent=2))
