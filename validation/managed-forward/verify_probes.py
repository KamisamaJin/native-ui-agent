#!/usr/bin/env python3
"""Portable closed neutral verification; no live cache, SDK or process cleanup."""
import argparse,collections,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def table(p):return{str(q.relative_to(p)):sha(q)for q in p.rglob('*')if q.is_file()and'__pycache__'not in q.parts}
def verify_capsule(root):
 seal=read(root/'SEAL.json')
 for rel,item in seal['files'].items():
  p=root/rel;assert p.stat().st_size==item['bytes']and sha(p)==item['sha256'],str(p)
def tool_identity(root,freeze):
 files=read(root/'capture/result.json')['tool_files'];expected=read(R/freeze)['files']
 assert files and all(expected.get(rel)==value for rel,value in files.items())
ARCHIVED={}
def cache_archives():
 for index_path in sorted((R/'probes/native-review').rglob('cache-archive-index.json')):
  parent=index_path.parent
  index=read(parent/'cache-archive-index.json');archive=parent/Path(index['archive']).name
  assert sha(archive)==index['archive_sha256']
  with tarfile.open(archive,'r:gz')as stream:
   for row in index['entries']:
    if row['kind']!='file':continue
    data=stream.extractfile(row['archive_member']).read()
    assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']
    ARCHIVED[(row['run'],row['relative'])]={'sha256':row['sha256'],'bytes':row['bytes']}
def inventory(root,entries):
 for row in entries:
  p=(root/row['path']).resolve();assert p.is_relative_to(root.resolve()),str(p)
  if p.is_file():assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'],str(p)
  else:assert ARCHIVED.get((root.name,row['path']))=={'sha256':row['sha256'],'bytes':row['bytes']},str(p)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--tracked',action='store_true');a=parser.parse_args()
 cache_archives();spec=R/'probes/spec/seal-manifest.json';s=read(spec);inventory(spec.parent,s['files']);counts=[]
 for folder,freeze in [('candidate-v12','CANDIDATE-FREEZE.json'),('candidate-v12.1','CANDIDATE-FREEZE-2.json'),('candidate-v12.2','CANDIDATE-FREEZE-3.json'),('candidate-v12.3','CANDIDATE-FREEZE-4.json'),('candidate-v12.4','CANDIDATE-FREEZE-5.json')]:assert table(R/folder)==read(R/freeze)['files']
 latest=read(R/'LATEST-ENGINEERING.json')
 assert table(REPO/'native-ui-agent')==table(R/latest['candidate'])
 assert table(R/'baseline-v11')==read(R/'baseline-v11-seal.json')['files']
 runs=[p.name for p in sorted((R/'probes/runs').glob('attempt-*'))if(p/'run-manifest.json').is_file()]
 for name in runs:
  root=R/'probes/runs'/name;m=read(root/'run-manifest.json');inventory(root,m['files']);summary=read(root/'summary.json')
  assert summary['spec_sha256']==sha(spec)
  assert len(summary['rows'])==len(s['row_ids'])and {r['id']for r in summary['rows']}==set(s['row_ids'])
  derived={k:sum(r['verdict']==k for r in summary['rows'])for k in ['P','F','U']};assert derived==summary.get('adjudicated_counts',summary.get('counts'))
  counts.append({'run':name,'counts':derived})
  if name not in {'attempt-1','attempt-2'}:
   assert derived=={'P':106,'F':0,'U':23}
   assert summary.get('native_SDK_executed_by_this_subtask',summary.get('native_SDK_executed_in_this_replay'))is False
   if 'live_tool_imported'in summary:assert summary['live_tool_imported']is False
   assert not any(r.get('native_SDK_executed')is True for r in summary['rows'])
 seal=read(R/'evidence/probes/SEAL.json')
 for rel,item in seal['files'].items():
  p=R/'evidence/probes'/rel;assert p.stat().st_size==item['bytes']and sha(p)==item['sha256'],rel
 for name in ['android-candidate-positive','android-candidate-negative']:
  tool_identity(R/'evidence/probes'/name,'CANDIDATE-FREEZE-2.json')
  subprocess.run([sys.executable,'-B',str(R/'replay_native_probe.py'),name],check=True)
 for version in ['v12.2','v12.3']:
  current=R/('evidence/qualification-'+version)
  for rel,item in read(current/'SEAL.json')['files'].items():
   p=current/rel;assert p.stat().st_size==item['bytes']and sha(p)==item['sha256'],rel
  tool_identity(current/'android-positive','CANDIDATE-FREEZE-3.json'if version=='v12.2'else'CANDIDATE-FREEZE-4.json')
  subprocess.run([sys.executable,'-B',str(R/'replay_native_probe.py'),'android-candidate-positive','--capture-root',str(current/'android-positive')],check=True)
 bad=read(R/'evidence/probes/responsibility-negative/cycle.json');assert bad['status']=='blocked_evidence_responsibility'and not bad['native_executed']
 feedback=read(R/'evidence/probes/android-source-feedback/cycle.json');assert not feedback['native_executed']and not feedback['source_tasks']
 zero=read(R/'probes/native/zero-sdk-tests/result.json');assert zero['sdk_command_exit_code']==0 and zero['actual_native_test_count']==0 and zero['exit_code']!=0 and not zero['native_observation_exists']and zero['host_sha256_before']==zero['host_sha256_after']
 cancel=read(R/'probes/native/cancel-sdk/result.json');root=R/'evidence/probes/cancel-sdk'
 assert cancel['observed_in_flight_sdk_frame']and cancel['exit_code']!=0 and not cancel['cycle_published']and not cancel['reserved_test_folder_exists']
 assert cancel['source_hashes_before']==cancel['source_hashes_after']and not(root/'cycle.json').exists()
 assert read(root/'resources.json')['primary_error']['type']=='InterruptedError'and not read(root/'resources.json')['cleanup_errors']
 assert read(root/'service-error.json')['status']=='not_accepted'
 actual_frame=root/'capture/native'/Path(cancel['first_frame']['path']).name;assert sha(actual_frame)==cancel['first_frame']['sha256']
 # Preserve the first incomplete cancellation qualification above; the two
 # later runs add distinct complete-frame/group evidence without replacing it.
 for name,scope,child in [('cancel-sdk-v2','cancel-sdk-v2-qualification',''),('cancel-sdk-v3','qualification-v12.3','android-cancel')]:
  capsule=R/'evidence'/scope
  for rel,item in read(capsule/'SEAL.json')['files'].items():
   p=capsule/rel;assert p.stat().st_size==item['bytes']and sha(p)==item['sha256'],rel
  native=(capsule/child if child else capsule)/'capture/native'
  row=read(R/'probes/native'/name/'result.json');assert row['observed_complete_in_flight_sdk_frame']
  frame=native/Path(row['first_frame']['path']).name
  assert sha(frame)==row['first_frame']['sha256']
  with Image.open(frame)as img:img.load();assert list(img.size)==row['first_frame']['decoded_size']
  assert row['group_before']and row['group_after_samples'][-1]['members']==[]
  assert row['source_hashes_before']==row['source_hashes_after']and not row['cycle_published']and not row['reserved_test_folder_exists']
  if name=='cancel-sdk-v3':
   prefix=(R/'probes/native'/name/'pre-cancel-sdk-prefix.log').read_bytes();log=(native/'test.log').read_bytes()
   assert prefix and log.startswith(prefix)and sha(native/'test.log')==row['log_after_cancel']['sha256']
   assert row['status']=='PASS'and not row['resources']['cleanup_errors']
 ios=read(R/'operators/ios-prerequisite.json');assert ios['status']=='blocked_native_ios'
 for name in ['pre-cleanup','host-setup']:verify_capsule(R/'evidence'/name)
 cleanup=read(R/'CLEANUP.json');assert cleanup['status']=='complete'and cleanup['post_cleanup']['path_exists']is False and cleanup['remaining_owned_cache_bytes']==0
 assert cleanup['owned_native_devices_remaining']==[]and cleanup['live_working_directories']==[]
 archive_root=R/'operators/local-ci-after-compatibility';partial=read(archive_root/'partial-grade-archive.json');archive=archive_root/partial['archive']
 assert sha(archive)==partial['sha256']and sha(archive_root/'partial-historical-grade-replay/inventory.json')==partial['original_inventory_sha256']
 with tarfile.open(archive,'r:gz')as stream:
  for row in partial['entries']:
   data=stream.extractfile(row['file']).read();assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']
 checkpoint=read(R/'PHASE1.json')
 assert checkpoint['business_blind_trial']=='not_started'and not checkpoint['business_design_dispatched']and not checkpoint['initial_business_source_authored']
 if a.tracked:
  tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0'))
  assert all(str(p.relative_to(REPO))in tracked for p in R.rglob('*')if p.is_file()and'cache'not in p.parts and'__pycache__'not in p.parts)
 print(json.dumps({'status':'PASS','independent_runs':counts,'business_blind_trial':'not_started_pending_ios_prerequisite','scope':'Integrity and original neutral evidence only; not iOS validation, human gold, or product PR quality/cost advantage.'}))
if __name__=='__main__':main()
