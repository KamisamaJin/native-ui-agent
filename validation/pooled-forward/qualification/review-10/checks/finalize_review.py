from domain_support import *
import tarfile,datetime,os,shutil
freezes=[]
for filename,pin in[('CANDIDATE-FREEZE-10.json','6dac704edfb15491e59648ab0259f465469f81ed0f7b61d7cedf0e91e47140cf'),('BASELINE-COMMON-FREEZE-6.json','e04a0db08a4a617c372e1f3f9a05dc3c1042fb53e59d48e08f189f03aaf302c4')]:
 meta=load(POOLED/filename);arm=POOLED/meta['candidate'];assert sha(POOLED/filename)==pin;bad=[name for name,h in meta['files'].items()if sha(arm/name)!=h];actual={str(p.relative_to(arm))for p in arm.rglob('*')if p.is_file()and'__pycache__'not in p.parts};assert not bad and actual==set(meta['files']);freezes.append({'freeze':filename,'sha256':pin,'files_verified':len(meta['files']),'mismatches':bad,'exact_tree':True})
prior=ROOT.parent/'review-9';seal=load(prior/'SEAL.json');assert all(sha(prior/name)==h for name,h in seal['files'].items());assert sha(prior/'SEAL.json')==sha(ROOT/'prior-review9/SEAL.json')and sha(prior/'review.json')==sha(ROOT/'prior-review9/review.json')
criterion=POOLED/'qualification/spec/quantifier-scope';assert sha(criterion/'SEAL.json')=='c7d7a3936991a88b53a65444b184ed898345b335b3a5c7f7b8d71db9d95e2772';assert all(sha(criterion/e['path'])==e['sha256']for e in load(criterion/'SEAL.json')['files'])
save(ROOT/'raw/final-immutable-audit.json',{'freezes':freezes,'candidate_baseline_unchanged':True,'prior_review9_seal_sha256':sha(prior/'SEAL.json'),'prior_review9_seal_members_verified':len(seal['files']),'all174_previous_outcomes_preserved_by_unchanged_seal':True,'preservation_scope':'Initial prior index audit recorded; final audit uses only seal members, not another broad raw-tree read.','criterion_seal_sha256':sha(criterion/'SEAL.json'),'operators_reviewed':False})

# Archive only the selected original query inputs needed by this focused pass.
# Their prior directories remain unchanged; this makes the focused input package
# reviewable without reading unrelated old raw trees.
inputs=[]
for arm in['candidate-v13.9','baseline-v12.6-common-6']:
 for row in load(ROOT/'raw'/(arm+'-focus-results.json')):
  detail=row['detail']
  if not detail.get('original_observation'):continue
  source=Path(detail['original_observation']).parent;dest=ROOT/'inputs'/arm/row['id'];dest.mkdir(parents=True,exist_ok=False)
  for name in['observation.json','plan.json','state.json','QUERY-ABI.json','ABI-SIDECAR.json']:
   if(source/name).is_file():shutil.copyfile(source/name,dest/name)
  if(source/'packet/native').is_dir():shutil.copytree(source/'packet',dest/'packet')
  elif(source/'native').is_dir():shutil.copytree(source/'native',dest/'native')
  old_result=source.parent/(source.name+'-result.json')
  if old_result.is_file():shutil.copyfile(old_result,dest/'previous-verdict.json')
  assert sha(dest/'observation.json')==detail['original_observation_sha256']and sha(dest/'plan.json')==detail['original_plan_sha256']
  inputs.append({'case':row['id'],'arm':arm,'source':str(source),'archived':str(dest),'observation_sha256':sha(dest/'observation.json'),'plan_sha256':sha(dest/'plan.json'),'original_bytes_unchanged':True})
save(ROOT/'raw/selected-input-preservation.json',{'inputs':inputs,'count':len(inputs),'scope':'Only explicitly selected SC18/query-boundary inputs and their original supporting packet members, no unrelated prior outputs or operators.'})
commands=[]
for arm in['candidate-v13.9','baseline-v12.6-common-6']:
 result=f'raw/{arm}-focus-results.json';commands.append({'argv':['python3',str(ROOT/'checks/run_focus.py'),'--arm',arm,'--path',str(POOLED/arm)],'check_sha256':sha(ROOT/'checks/run_focus.py'),'result':result,'result_sha256':sha(ROOT/result)})
for script,arm,run in[('run_default.py','candidate-v13.9','default'),('run_baseline_default.py','baseline-v12.6-common-6','default-common')]:
 result=f'raw/{arm}-{run}-results.json';commands.append({'argv':['python3',str(ROOT/'checks'/script),'--arm',arm,'--path',str(POOLED/arm),'--run-name',run],'check_sha256':sha(ROOT/'checks'/script),'result':result,'result_sha256':sha(ROOT/result),'verbatim_public_CLI_commands_stdout_stderr':'work/'+arm+'/'+run+'/*-command.json'})
save(ROOT/'raw/command-source-result-proofs.json',{'cwd':str(POOLED.parents[1]),'commands':commands,'check_hashes':{str(p.relative_to(ROOT)):sha(p)for p in(ROOT/'checks').glob('*.py')},'environment':'PYTHONDONTWRITEBYTECODE=1','recording_scope':'Command inventory reconstructed from executed tool calls. Per-default CLI command/stdout/stderr JSON is verbatim. No retroactive raw console transcript claimed.','SDK_commands_executed':[],'operators_executed_or_reviewed':False,'actual_HOST_subprocesses':'Read-only Git archive and synchronous plutil inventory decoding only; all resource/SDK/build boundaries in-process non-forwarding mocks.'})
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
save(ROOT/'raw/archive-verification.json',{'archive':str(archive),'archive_sha256':sha(archive),'members_verified':len(members),'mismatches':bad,'all_selected_originals_and_new_evidence_archived_before_closure':True})
save(ROOT/'RESOURCE-CLOSURE.json',{'owner':'/root/v13_default_qualification','root':str(ROOT),'closed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'real_devices_acquired':0,'SDK_native_or_benchmark_processes_started':0,'private_test_daemons_started':0,'test_processes_terminated':[],'synchronous_HOST_probes_finished':True,'mock_workflow_artifacts':'Retained inert files only; no device, watcher or process exists. No deletion needed.','operators_excluded':True,'archive_verified_before_closure':str(ROOT/'raw/archive-verification.json')})
entries=[]
for p in sorted(ROOT.rglob('*')):
 if p.parent==ROOT and p.name in{'SEAL.json','raw-artifact-index.json'}:continue
 if p.is_symlink():entries.append({'path':str(p.relative_to(ROOT)),'type':'symlink','target':os.readlink(p),'sha256_of_link_text':hashlib.sha256(os.readlink(p).encode()).hexdigest()})
 elif p.is_file():entries.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
save(ROOT/'raw-artifact-index.json',{'review':'review-10-sc18-focused-delta','native_artifacts_from_this_review':'NONE','entries':entries,'files':len(entries),'total_file_bytes':sum(e.get('bytes',0)for e in entries)})
names=['review.json','REVIEW.md','OPEN-ISSUES.md','OWNERSHIP.json','RESOURCE-CLOSURE.json','raw-artifact-index.json','raw/final-immutable-audit.json','raw/focused-delta-source-audit.json','raw/selected-input-preservation.json','raw/command-source-result-proofs.json','raw/common-port-audit.json','raw/archive-verification.json','archives/RAW-EVIDENCE.tar.gz','criterion/SEAL.json']
save(ROOT/'SEAL.json',{'review_id':'review-10-sc18-focused-delta','sealed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'QUALIFIED','qualification_scope':'HOST_SIMULATED_FOCUSED_DELTA_ONLY','confirmed_issue_ids':[],'unresolved_interpretation_ids':[],'candidate_baseline_unchanged':True,'candidate_unchanged':True,'baseline_unchanged':True,'source_unchanged':True,'candidate':'candidate-v13.9','candidate_freeze_sha256':'6dac704edfb15491e59648ab0259f465469f81ed0f7b61d7cedf0e91e47140cf','baseline':'baseline-v12.6-common-6','baseline_freeze_sha256':'e04a0db08a4a617c372e1f3f9a05dc3c1042fb53e59d48e08f189f03aaf302c4','raw_rows':100,'raw_counts':{'P':100,'F':0},'prior_review9_all174_outcomes_and_seal_unchanged':True,'operators_reviewed':False,'native_runs_this_review':0,'benchmark_episodes':0,'performance_samples':0,'business_tasks':0,'native_qualification_performed':False,'performance_gate_passed':False,'business_tasks_may_start':False,'files':{name:sha(ROOT/name)for name in names}})
print(json.dumps({'seal_sha256':sha(ROOT/'SEAL.json'),'verdict':'QUALIFIED','scope':'HOST_SIMULATED_FOCUSED_DELTA_ONLY','indexed_entries':len(entries),'archive_members':len(members),'archive_bytes':archive.stat().st_size,'selected_original_inputs':len(inputs),'raw_rows':100,'P':100,'F':0,'native_runs':0},indent=2))
