#!/usr/bin/env python3
"""Archive then delete only the explicitly authorized attempt-7 per-run cache."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile
import time

ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
BASE=ROOT/'validation/managed-forward'
OUT=BASE/'probes/native-review/attempt-7-cleanup'
RUNS=BASE/'probes/runs'
parser=argparse.ArgumentParser();parser.add_argument('--manifest-sha256',required=True);args=parser.parse_args()
assert len(args.manifest_sha256)==64 and all(c in '0123456789abcdef' for c in args.manifest_sha256)
TRUSTED={'attempt-7':args.manifest_sha256}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def dump(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def parse_identity(value,pid):
    if isinstance(value,dict):return value
    if not isinstance(value,str):return None
    parts=value.split(None,6)
    if len(parts)!=7:return None
    try:pgid=int(parts[5])
    except ValueError:return None
    return {'pid':pid,'started':' '.join(parts[:5]),'pgid':pgid,'command':parts[6]}
def actual_identity(pid):
    result=subprocess.run(['ps','-ww','-p',str(pid),'-o','lstart=','-o','pgid=','-o','command='],text=True,capture_output=True)
    stat=subprocess.run(['ps','-p',str(pid),'-o','stat='],text=True,capture_output=True)
    return {'raw':result.stdout.strip(),'identity':parse_identity(result.stdout.strip(),pid) if result.returncode==0 else None,
            'live':result.returncode==0 and bool(stat.stdout.strip()) and not stat.stdout.strip().startswith('Z'),'stat':stat.stdout.strip()}
def identity_matches(record,actual):
    e=parse_identity(record['expected'],record['pid']);a=actual['identity'];token=record['token']
    return bool(e and a and actual['live'] and e.get('pid')==a.get('pid')==record['pid'] and e.get('started')==a.get('started') and e.get('pgid')==a.get('pgid') and
                token in e.get('command','') and token in a.get('command','') and record['source_path'] in e.get('command','') and record['source_path'] in a.get('command',''))

pre=[];manifests={};entries=[]
for name,trusted in TRUSTED.items():
    run=RUNS/name;p=run/'run-manifest.json';assert sha(p)==trusted
    m=load(p);manifests[name]=m;bad=[]
    for row in m['files']:
        path=run/row['path']
        if not path.is_file() or sha(path)!=row['sha256']:bad.append(row['path'])
    assert not bad,(name,bad)
    cache=run/'cache';assert cache.is_dir() and not cache.is_symlink() and cache.resolve()==cache.absolute()
    stat=cache.stat()
    pre.append({'run':name,'manifest_sha256':trusted,'all_original_artifacts_match':True,'artifact_count':len(m['files']),
                'manifest_cache_entries':sum(r['path'].startswith('cache/') for r in m['files']),'cache_root':str(cache),'cache_inode':stat.st_ino,'cache_device':stat.st_dev})
    listed={r['path']:r['sha256'] for r in m['files']}
    for path in sorted(cache.rglob('*')):
        rel=str(path.relative_to(run));entry={'run':name,'path':str(path),'relative':rel,'archive_member':name+'/'+rel}
        if path.is_symlink():entry.update(kind='symlink',link_target=os.readlink(path))
        elif path.is_file():entry.update(kind='file',bytes=path.stat().st_size,sha256=sha(path),listed_in_original_manifest=rel in listed)
        elif path.is_dir():entry.update(kind='directory')
        else:raise RuntimeError('Unexpected cache object type: '+str(path))
        entries.append(entry)
dump('pre-cleanup-integrity.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':pre,
    'observed_manifest_discrepancy':'Disposable cache exclusion was fixed before execution. The original run-manifest remains byte-identical; exact cache bytes are archived and deletion is separately recorded.'})

# Only original recorded identities are queried; there is no process-name/global scan.
records={}
def add(pid,token,expected,source_path,provenance):
    if type(pid)is not int or pid<=1 or not token or not parse_identity(expected,pid):return
    key=(pid,token)
    records.setdefault(key,{'pid':pid,'token':token,'expected':expected,'source_path':source_path,'provenance':provenance})
for name in TRUSTED:
    run=RUNS/name;fixture=str(run/'fixture_process.py')
    for p in (run/'raw').rglob('initial.json'):
        v=load(p);r=v.get('borrowed_process',{})
        if r.get('raw'):add(r['pid'],v.get('token'),r['raw'],fixture,str(p))
    for p in (run/'raw').rglob('before-harness-teardown.json'):
        value=load(p)
        for row in value.get('owned_fixture_processes',[]):
            original=row.get('observed_identity',{}).get('raw')
            if original:add(row['pid'],row.get('token'),original,fixture,str(p))
        process=(value.get('journal') or {}).get('process')
        if process:
            expected=process.get('identity');parsed=parse_identity(expected,process.get('pid'))
            if parsed:
                for source in [BASE/'candidate-v12.6/scripts/resource_manager.py']:
                    if str(source) in parsed.get('command',''):add(process['pid'],process.get('token'),expected,str(source),str(p));break
process_results=[]
for record in records.values():
    before=actual_identity(record['pid']);result=dict(record,actual_before=before,action='none; absent or identity does not match this recorded probe')
    if identity_matches(record,before):
        os.kill(record['pid'],signal.SIGTERM);result['action']='SIGTERM to exact birth/group/token/source identity'
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and identity_matches(record,actual_identity(record['pid'])):time.sleep(.1)
        if identity_matches(record,actual_identity(record['pid'])):
            os.kill(record['pid'],signal.SIGKILL);result['action']+='; then SIGKILL after rechecking the same identity'
        time.sleep(.05)
    result['actual_after']=actual_identity(record['pid']);assert not identity_matches(record,result['actual_after'])
    process_results.append(result)
dump('pre-cleanup-process-identities.json',{'scope':'Only exact PIDs read from the authorized original raw run, with recorded creation time/group/random token/source path. No native SDK or unrelated processes were targeted.','records':process_results})

archive=OUT/'prior-per-run-cache-evidence.tar.gz'
with tarfile.open(archive,'x:gz',dereference=False) as tar:
    for name in TRUSTED:tar.add(RUNS/name/'cache',arcname=name+'/cache',recursive=True)
with tarfile.open(archive,'r:gz') as tar:
    members={m.name:m for m in tar.getmembers()}
    for entry in entries:
        member=members[entry['archive_member']]
        if entry['kind']=='file':
            stream=tar.extractfile(member);assert stream is not None
            assert hashlib.sha256(stream.read()).hexdigest()==entry['sha256']
        elif entry['kind']=='symlink':assert member.issym() and member.linkname==entry['link_target']
        else:assert member.isdir()
archive_sha=sha(archive)
dump('cache-archive-index.json',{'archive':str(archive),'archive_sha256':archive_sha,'entries':entries})

removed=[]
for before in pre:
    path=Path(before['cache_root']);assert path==RUNS/before['run']/'cache' and not path.is_symlink()
    stat=path.stat();assert stat.st_ino==before['cache_inode'] and stat.st_dev==before['cache_device']
    shutil.rmtree(path);assert not path.exists()
    selected=[e for e in entries if e['run']==before['run'] and e['kind']=='file']
    removed.append({'path':str(path),'run':before['run'],'regular_file_count':len(selected),'bytes':sum(e['bytes'] for e in selected),
                    'archive_sha256':archive_sha,'archive_member_prefix':before['run']+'/cache/','removed':True})

post=[]
for name,trusted in TRUSTED.items():
    run=RUNS/name;assert sha(run/'run-manifest.json')==trusted
    noncache=[e for e in manifests[name]['files'] if not e['path'].startswith('cache/')]
    bad=[e['path'] for e in noncache if not(run/e['path']).is_file() or sha(run/e['path'])!=e['sha256']];assert not bad
    post.append({'run':name,'manifest_sha256':trusted,'manifest_unchanged':True,'all_non_cache_artifacts_unchanged':True,
                 'non_cache_artifact_count':len(noncache),'cache_absent':not(run/'cache').exists()})
assert load(RUNS/'attempt-7/summary.json')['counts']=={'P':106,'F':0,'U':23}
dump('cleanup.json',{'version':1,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization':'Explicit task: only the attempt-7 own per-run cache after native review and manifest verification.',
    'original_manifest_cache_exclusion_claim_verified':True,'manifest_discrepancy_resolution':'Cache was excluded from the original run-manifest as predeclared. All cache bytes archived and SHA-verified before deletion; original run-manifest and raw remain unchanged. Exact source/archive-member mapping is retained.',
    'archive':{'path':str(archive),'sha256':archive_sha,'bytes':archive.stat().st_size,'all_member_hashes_verified':True},
    'removed':removed,'process_identity_records_checked':len(process_results),'matched_live_probe_processes_signalled':sum(r['action'].startswith('SIGTERM') for r in process_results),
    'post_cleanup':post,'untouched':['raw directories','source files outside the explicit authorized cache','spec','frozen candidates','main validation/managed-forward/cache','native SDK evidence packages'],
    'attempt7_counts_unchanged':{'P':106,'F':0,'U':23}})
print(json.dumps({'cache_roots_removed':len(removed),'regular_files_archived':sum(r['regular_file_count'] for r in removed),'archive_sha256':archive_sha,
                  'manifest_files_unchanged':True,'noncache_artifacts_unchanged':True,'processes_signalled':sum(r['action'].startswith('SIGTERM') for r in process_results)}))
