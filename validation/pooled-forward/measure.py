#!/usr/bin/env python3
"""Identical external allocated-byte/time sampler for anonymous study arms.

Sampling is an observed lower bound, not an exact transient or APFS physical
peak. It never deletes files or controls resources based on names/PIDs alone.
The experiment driver owns cancellation and source/evidence preservation.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,threading,time
from pathlib import Path
import shutil


def allocated(paths):
    roots=[Path(p).resolve()for p in paths];roots=[p for p in set(roots)if not any(p!=q and p.is_relative_to(q)for q in roots)]
    seen=set();total=0
    for p in roots:
        if not p.exists():continue
        files=[p]if p.is_file()else None
        def visit():
            for base,dirs,names in os.walk(p,followlinks=False):
                dirs[:]=[d for d in dirs if not(Path(base)/d).is_symlink()]
                for n in names:yield Path(base)/n
        for f in files if files is not None else visit():
            try:st=f.lstat()
            except FileNotFoundError:continue
            key=(st.st_dev,st.st_ino)
            if key not in seen:total+=st.st_blocks*512;seen.add(key)
    return total


class Meter:
    def __init__(self,spec,output):
        self.spec=spec;self.output=Path(output);self.stop_event=threading.Event();self.samples=[]
        self.interval=spec['sample_seconds'];self.groups=spec['groups'];self.thread=None;self.lock=threading.Lock()
        if not .1<=self.interval<=60 or not self.groups:raise ValueError('Explicit bounded interval/groups required')
        self.budget=spec['max_total_allocated_bytes'];self.min_free=spec['min_free_bytes'];self.error=None
    def sample(self):
        with self.lock:return self._sample()
    def _sample(self):
        started=time.time();groups={};all_paths=[]
        for name,group in self.groups.items():
            paths=list(group['paths'])
            for item in group.get('resource_journals',[]):
                path=Path(item)
                if not path.is_file():continue
                try:j=json.loads(path.read_text())
                except (ValueError,OSError):continue
                # Only explicit journaled creates in this configured arm. The
                # sampler does not infer ownership from a global device list.
                if j.get('format')!='native-ui-owned-resources-v1':raise ValueError('Foreign resource journal')
                for device in j.get('devices',[]):
                    if device.get('udid'):paths.append(str(Path.home()/'Library/Developer/CoreSimulator/Devices'/device['udid']))
            paths=[str(Path(p).resolve())for p in paths];groups[name]={'allocated_bytes':allocated(paths),'paths':paths};all_paths.extend(paths)
        free=shutil.disk_usage(self.spec['filesystem_root']).free;total=allocated(all_paths)
        row={'started_at_unix':started,'finished_at_unix':time.time(),'groups':groups,'total_allocated_bytes':total,'free_bytes':free,
             'budget_exceeded':total>self.budget or free<self.min_free}
        with self.output.open('a')as f:f.write(json.dumps(row)+'\n')
        self.samples.append(row)
        return row
    def __enter__(self):
        self.output.parent.mkdir(parents=True,exist_ok=True)
        with self.output.open('x'):pass
        self.sample()
        def observe():
            while not self.stop_event.wait(self.interval):
                try:self.sample()
                except Exception as error:self.error={'type':type(error).__name__,'message':str(error)};return
        self.thread=threading.Thread(target=observe,daemon=True);self.thread.start();return self
    def boundary(self,phase):
        row=self.sample();return{'phase':phase,'sample_index':len(self.samples)-1,'at_unix':row['finished_at_unix']}
    def __exit__(self,*args):
        self.stop_event.set();self.thread.join();self.sample()
        result={'spec_sha256':hashlib.sha256(json.dumps(self.spec,sort_keys=True).encode()).hexdigest(),'sample_seconds':self.interval,
                'sample_count':len(self.samples),'first_sample_at_unix':self.samples[0]['started_at_unix'],'last_sample_at_unix':self.samples[-1]['finished_at_unix'],
                'observed_peak_allocated_bytes':{name:max(r['groups'][name]['allocated_bytes']for r in self.samples)for name in self.groups},
                'post_run_allocated_bytes':{name:self.samples[-1]['groups'][name]['allocated_bytes']for name in self.groups},
                'observed_total_peak_allocated_bytes':max(r['total_allocated_bytes']for r in self.samples),
                'budget_exceeded':any(r['budget_exceeded']for r in self.samples),'sampling_error':self.error,
                'scope':'Observed sampled allocated-byte peaks; group peaks are not necessarily simultaneous. Shared hard links deduplicated within each measured union; APFS clone sharing and global shared SDK/Gradle caches are not exact per-arm physical use.'}
        self.output.with_suffix('.summary.json').write_text(json.dumps(result,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('argv',nargs=argparse.REMAINDER);a=p.parse_args();argv=a.argv[1:]if a.argv[:1]==['--']else a.argv
    if not argv:raise ValueError('An explicit supervised command required')
    start=time.time()
    with Meter(json.loads(a.spec.read_text()),a.output)as meter:
        # No broad process cleanup here: the default managed controller owns its
        # native process groups; this records the entire actual command wall.
        result=subprocess.run(argv)
    a.output.with_suffix('.command.json').write_text(json.dumps({'argv':argv,'started_at_unix':start,'finished_at_unix':time.time(),'exit_code':result.returncode},indent=2)+'\n')
    return result.returncode
if __name__=='__main__':raise SystemExit(main())
