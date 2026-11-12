from domain_support import *
import tarfile,datetime,os
def verify_index(base,index):
 bad=[]
 for entry in index['entries']:
  p=base/entry['path']
  if entry.get('type')=='symlink':
   if not p.is_symlink()or os.readlink(p)!=entry['target']:bad.append(entry['path'])
  elif sha(p)!=entry['sha256']:bad.append(entry['path'])
 return bad
freezes=[]
for filename,pin in[('CANDIDATE-FREEZE-9.json','e96973fbdb7909ef56a3926059c6b20f651aa2464cd6bc5cd6b58879196a7e96'),('BASELINE-COMMON-FREEZE-5.json','4b47ece620f1dab419e150f6e7bbd0c6e2622a70fb96770b19aba2d6db6eda17')]:
 meta=load(POOLED/filename);arm=POOLED/meta['candidate'];assert sha(POOLED/filename)==pin;bad=[n for n,h in meta['files'].items()if sha(arm/n)!=h];actual={str(p.relative_to(arm))for p in arm.rglob('*')if p.is_file()and'__pycache__'not in p.parts};extra=sorted(actual-set(meta['files']));missing=sorted(set(meta['files'])-actual);assert not bad and not extra and not missing;freezes.append({'freeze':filename,'sha256':pin,'files_verified':len(meta['files']),'mismatches':bad,'extra_paths':extra,'missing_paths':missing})
prior=ROOT.parent/'review-8';prior_seal=load(prior/'SEAL.json');assert all(sha(prior/n)==h for n,h in prior_seal['files'].items());index=load(prior/'raw-artifact-index.json');assert not verify_index(prior,index);assert sha(prior/'SEAL.json')==sha(ROOT/'prior-review8/SEAL.json')and sha(prior/'review.json')==sha(ROOT/'prior-review8/review.json')
criterion=POOLED/'qualification/spec/quantifier-scope';assert sha(criterion/'SEAL.json')=='c7d7a3936991a88b53a65444b184ed898345b335b3a5c7f7b8d71db9d95e2772';assert all(sha(criterion/entry['path'])==entry['sha256']for entry in load(criterion/'SEAL.json')['files'])
save(ROOT/'raw/final-immutable-audit.json',{'freezes':freezes,'candidate_baseline_unchanged':True,'prior_review8_seal_sha256':sha(prior/'SEAL.json'),'prior_review8_entries_verified':len(index['entries']),'all150_primary_and9_operator_previous_outcomes_unchanged':True,'quantifier_seal_sha256':sha(criterion/'SEAL.json'),'operators_reviewed':False})
commands=[]
for arm in['candidate-v13.8','baseline-v12.6-common-5']:
 for script,result in[('run_preserved.py','preserved'),('run_wire_delta.py','wire-delta'),('run_prior_regressions.py',None),('complete_prior_regressions.py','typed-regression'),('run_corrected_regressions.py','corrected-regression')]:
  entry={'argv':['python3',str(ROOT/'checks'/script),'--arm',arm,'--path',str(POOLED/arm)],'current_check_sha256':sha(ROOT/'checks'/script)}
  if result:
   p=f'raw/{arm}-{result}-results.json';entry.update(result=p,result_sha256=sha(ROOT/p))
  else:entry.update(initial_script='raw/prior-regression-first-harness.py',failure='raw/prior-regression-first-harness-error.txt',result='19 P case files before wrapper error; completion only executed remaining5')
  commands.append(entry)
for script,arm,run in[('run_default.py','candidate-v13.8','default'),('run_baseline_default.py','baseline-v12.6-common-5','default-common')]:
 result=f'raw/{arm}-{run}-results.json';commands.append({'argv':['python3',str(ROOT/'checks'/script),'--arm',arm,'--path',str(POOLED/arm),'--run-name',run],'check_sha256':sha(ROOT/'checks'/script),'result':result,'result_sha256':sha(ROOT/result),'verbatim_public_CLI_commands_stdout_stderr':'work/'+arm+'/'+run+'/*-command.json'})
save(ROOT/'raw/command-source-result-proofs.json',{'cwd':str(POOLED.parents[1]),'commands':commands,'check_hashes':{str(p.relative_to(ROOT)):sha(p)for p in(ROOT/'checks').glob('*.py')},'environment':'PYTHONDONTWRITEBYTECODE=1; no frozen bytecode written','recording_scope':'Inventory reconstructed from executed tool calls; per-default CLI commands/stdout/stderr retained verbatim. No retroactive raw console transcript claimed.','SDK_commands_executed':[],'operators_executed_or_reviewed':False,'actual_HOST_subprocesses':'Read-only git archive and synchronous plutil inventory JSON decoding; all resource/SDK/compile boundaries are in-process non-forwarding mocks.'})
archive=ROOT/'archives/RAW-EVIDENCE.tar.gz';archive.parent.mkdir(exist_ok=True);assert not archive.exists();members=[p for p in sorted(ROOT.rglob('*'))if(p.is_file()or p.is_symlink())and'archives'not in p.relative_to(ROOT).parts and not(p.parent==ROOT and p.name in{'SEAL.json','raw-artifact-index.json','RESOURCE-CLOSURE.json'})]
with tarfile.open(archive,'w:gz',compresslevel=6,dereference=False)as tf:
 for p in members:tf.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
bad=[]
with tarfile.open(archive,'r:gz')as tf:
 for member in tf.getmembers():
  p=ROOT/member.name
  if member.issym():
   if not p.is_symlink()or os.readlink(p)!=member.linkname:bad.append(member.name)
  elif member.isfile()and hashlib.sha256(tf.extractfile(member).read()).hexdigest()!=sha(p):bad.append(member.name)
assert not bad
save(ROOT/'raw/archive-verification.json',{'archive':str(archive),'archive_sha256':sha(archive),'members_verified':len(members),'mismatches':bad,'all_raw_originals_first_failures_and_harness_error_archived_before_closure':True})
save(ROOT/'RESOURCE-CLOSURE.json',{'owner':'/root/v13_default_qualification','root':str(ROOT),'closed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'real_devices_acquired':0,'SDK_native_or_benchmark_processes_started':0,'private_test_daemons_started':0,'test_processes_terminated':[],'synchronous_HOST_probes_finished':True,'mock_workflow_artifacts':'Retained inert data only; no real device/watcher/process exists. No deletion necessary.','operators_excluded':True,'archive_verified_before_closure':str(ROOT/'raw/archive-verification.json')})
entries=[]
for p in sorted(ROOT.rglob('*')):
 if p.parent==ROOT and p.name in{'SEAL.json','raw-artifact-index.json'}:continue
 if p.is_symlink():entries.append({'path':str(p.relative_to(ROOT)),'type':'symlink','target':os.readlink(p),'sha256_of_link_text':hashlib.sha256(os.readlink(p).encode()).hexdigest()})
 elif p.is_file():entries.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
save(ROOT/'raw-artifact-index.json',{'review':'review-9-offscreen-native-query-delta','native_artifacts_from_this_review':'NONE','entries':entries,'files':len(entries),'total_file_bytes':sum(entry.get('bytes',0)for entry in entries)});assert not verify_index(ROOT,load(ROOT/'raw-artifact-index.json'))
names=['review.json','REVIEW.md','OPEN-ISSUES.md','OWNERSHIP.json','RESOURCE-CLOSURE.json','raw-artifact-index.json','raw/final-immutable-audit.json','raw/command-source-result-proofs.json','raw/common-port-audit.json','raw/archive-verification.json','archives/RAW-EVIDENCE.tar.gz','criterion/SEAL.json']
save(ROOT/'SEAL.json',{'review_id':'review-9-offscreen-native-query-delta','sealed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'NOT_QUALIFIED','confirmed_issue_ids':['SC18'],'unresolved_interpretation_ids':[],'candidate_baseline_unchanged':True,'candidate_unchanged':True,'baseline_unchanged':True,'primary_rows':174,'primary_counts':{'P':162,'F':12},'confirmed_F_rows':10,'preserved_old_positive_graph_F_rows':2,'prior_review8_all150_primary_and9_operator_rows_and_seal_unchanged':True,'operators_reviewed':False,'native_runs_this_review':0,'benchmark_episodes':0,'performance_samples':0,'business_tasks':0,'files':{name:sha(ROOT/name)for name in names}})
print(json.dumps({'seal_sha256':sha(ROOT/'SEAL.json'),'indexed_entries':len(entries),'archive_members':len(members),'archive_bytes':archive.stat().st_size,'verdict':'NOT_QUALIFIED','confirmed_issue_ids':['SC18'],'unresolved_interpretation_ids':[],'candidate_baseline_unchanged':True},indent=2))
