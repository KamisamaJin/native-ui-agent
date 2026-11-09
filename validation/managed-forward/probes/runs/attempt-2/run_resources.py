#!/usr/bin/env python3
"""Independent sealed lifecycle probes using only documented resource APIs."""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback
import uuid

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
CANDIDATE = PROJECT / 'validation/managed-forward/candidate-v12'
SCRIPTS = CANDIDATE / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import resource_manager
assert Path(resource_manager.__file__).resolve().parent == SCRIPTS.resolve()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def hashfile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def identity(pid):
    r = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'pgid=', '-o', 'command='], text=True, capture_output=True)
    s = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], text=True, capture_output=True)
    return {'pid': pid, 'raw': r.stdout.strip(), 'stat': s.stdout.strip(),
            'live': r.returncode == 0 and bool(s.stdout.strip()) and not s.stdout.strip().startswith('Z')}

def waitfor(test, timeout=5):
    start = time.monotonic(); trace = []
    while True:
        try: value = test()
        except (FileNotFoundError, json.JSONDecodeError): value = False
        trace.append({'elapsed': time.monotonic()-start, 'satisfied': bool(value)})
        if value or time.monotonic()-start >= timeout:
            return bool(value), trace
        time.sleep(.05)

def load(path, default=None):
    try: return json.loads(path.read_text())
    except (FileNotFoundError, NotADirectoryError, json.JSONDecodeError): return default

class Row:
    def __init__(self, cid, variant):
        self.id = cid + '/' + variant; self.cid = cid; self.variant = variant
        slug = cid + '__' + variant
        trial = 1
        while (HERE / 'raw' / slug).exists() or (HERE / 'cache' / slug).exists():
            trial += 1
            slug = cid + '__' + variant + '__execution-' + str(trial)
        self.raw = HERE / 'raw' / slug; self.cache = HERE / 'cache' / slug
        self.raw.mkdir(); self.cache.mkdir(); self.token = uuid.uuid4().hex
        self.fixture = self.cache / 'fixture'; self.fixture.mkdir()
        self.source = self.cache / 'protected-source'; self.source.mkdir()
        self.borrowed = self.cache / 'borrowed-directory'; self.borrowed.mkdir()
        self.buildcache = self.cache / 'shared-build-cache'; self.buildcache.mkdir()
        self.keep = [self.source/'source.txt', self.borrowed/'sentinel.txt', self.buildcache/'compiled.bin', self.raw/'evidence-sentinel.txt']
        for path in self.keep: path.write_text('immutable-' + self.token + '\n')
        self.before = {str(p): {'sha256':hashfile(p), 'inode':p.stat().st_ino} for p in self.keep}
        self.sentinel_root = self.cache/'borrowed-live'; self.sentinel_root.mkdir()
        sentinel_argv = [sys.executable, '-B', str(HERE/'fixture_process.py'), '--root', str(self.sentinel_root), '--token', self.token, '--role', 'sentinel', '--mode', 'hang']
        self.sentinel_log = (self.raw/'borrowed-process.log').open('wb')
        self.sentinel = subprocess.Popen(sentinel_argv, stdout=self.sentinel_log, stderr=subprocess.STDOUT)
        ready, trace = waitfor(lambda:(self.sentinel_root/'heartbeat-sentinel.json').exists())
        if not ready: raise RuntimeError('Probe borrowed sentinel did not start')
        self.sentinel_identity = identity(self.sentinel.pid)
        self.config = {'source_roots':[str(self.source)], 'native_options':{'build-cache':str(self.buildcache)},
            'resources':{'root':str(self.cache/'resources'), 'max_bytes':2**28, 'min_free_bytes':0, 'sample_seconds':.1, 'ttl_seconds':86400}}
        self.config_path = self.raw/'config.json'; dump(self.config_path, self.config)
        self.commands=[]; self.trace=[{'kind':'borrowed_ready', 'trace':trace}]; self.worker=None; self.started=time.monotonic()
        self.tool_identity_before=hashfile(SCRIPTS/'resource_manager.py')
        dump(self.raw/'initial.json', {'id':self.id,'token':self.token,'protected':self.before,'borrowed_process':self.sentinel_identity,'argv':sentinel_argv})

    @property
    def root(self): return Path(self.config['resources']['root'])

    def start(self, mode, final=True):
        tool_before=hashfile(SCRIPTS/'resource_manager.py')
        shutil.copyfile(SCRIPTS/'resource_manager.py',self.raw/'resource-manager-before-worker.py')
        argv=[sys.executable,'-B',str(HERE/'resource_worker.py'),'--scripts',str(SCRIPTS),'--config',str(self.config_path),
            '--output',str(self.raw/'tool-output'),'--fixture',str(HERE/'fixture_process.py'),'--fixture-root',str(self.fixture),
            '--token',self.token,'--mode',mode]
        if final: argv.append('--final')
        self.worker_log=(self.raw/'worker.log').open('wb')
        self.worker=subprocess.Popen(argv, stdout=self.worker_log, stderr=subprocess.STDOUT)
        self.commands.append({'argv':argv,'pid':self.worker.pid,'started_monotonic':time.monotonic(),'tool_identity_before':tool_before})
        return self.worker

    def pause_ready(self):
        ok, trace=waitfor(lambda:(self.fixture/'entered.json').exists())
        self.trace.append({'kind':'entered','trace':trace}); return ok

    def tree_ready(self):
        ok, trace=waitfor(lambda:(self.fixture/'heartbeat-descendant.json').exists() and (self.root/'journal.json').exists())
        self.trace.append({'kind':'owned_tree_ready','trace':trace}); return ok

    def wait(self, seconds=10):
        try: code=self.worker.wait(timeout=seconds)
        except subprocess.TimeoutExpired: return None
        self.commands[-1].update(exit_code=code,finished_monotonic=time.monotonic(),tool_identity_after=hashfile(SCRIPTS/'resource_manager.py'))
        self.worker_log.close(); return code

    def cli(self, command, name):
        out=self.raw/name
        argv=[sys.executable,'-B',str(SCRIPTS/'resource_manager.py'),command,'--config',str(self.config_path),'--output',str(out)]
        start=time.monotonic()
        tool_before=hashfile(SCRIPTS/'resource_manager.py')
        shutil.copyfile(SCRIPTS/'resource_manager.py',self.raw/(name+'-resource-manager-before.py'))
        try:
            r=subprocess.run(argv, stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=12)
            (self.raw/(name+'.stdout')).write_bytes(r.stdout); (self.raw/(name+'.stderr')).write_bytes(r.stderr)
            value={'argv':argv,'exit_code':r.returncode,'duration':time.monotonic()-start,'receipt':load(out/'resources.json')}
        except subprocess.TimeoutExpired as e:
            (self.raw/(name+'.stdout')).write_bytes(e.stdout or b''); (self.raw/(name+'.stderr')).write_bytes(e.stderr or b'')
            value={'argv':argv,'timeout':True,'duration':time.monotonic()-start}
        value.update(tool_identity_before=tool_before,tool_identity_after=hashfile(SCRIPTS/'resource_manager.py'))
        self.commands.append(value); return value

    def snapshot(self, name):
        proc=[]
        path=self.fixture/'processes.jsonl'
        if path.exists():
            for line in path.read_text().splitlines():
                try: row=json.loads(line); proc.append(dict(row, observed_identity=identity(row['pid'])))
                except json.JSONDecodeError: pass
        heartbeat={p.name:load(p) for p in self.fixture.glob('heartbeat-*.json')}
        result={'at_monotonic':time.monotonic(),'owned_fixture_processes':proc,'heartbeats':heartbeat,
            'borrowed_process':identity(self.sentinel.pid),
            'protected':{str(p):{'sha256':hashfile(p),'inode':p.stat().st_ino if p.exists() else None} for p in self.keep},
            'journal':load(self.root/'journal.json'), 'tool_receipt':load(self.raw/'tool-output/resources.json'),
            'wrapper_result':load(self.fixture/'wrapper-result.json'),
            'files':[{'path':str(p.relative_to(self.cache)),'sha256':hashfile(p),'symlink':p.is_symlink()} for p in self.cache.rglob('*') if p.is_file() and not p.name.startswith('heartbeat-')]}
        dump(self.raw/(name+'.json'), result); return result

    def protected_ok(self, snap):
        return snap['protected']==self.before and snap['borrowed_process']['live'] and snap['borrowed_process']['raw']==self.sentinel_identity['raw']

    def owned_live(self, snap):
        return [p for p in snap['owned_fixture_processes'] if p['observed_identity']['live']]

    def await_owned_deadline(self, deadline):
        observations=[];number=0
        while True:
            snap=self.snapshot('owned-deadline-'+str(number).zfill(3));number+=1
            observations.append({'at_monotonic':time.monotonic(),'owned_live':[p['pid'] for p in self.owned_live(snap)],'heartbeats':snap['heartbeats']})
            if not self.owned_live(snap) or time.monotonic()>=deadline:break
            time.sleep(min(.4,max(0,deadline-time.monotonic())))
        self.trace.append({'kind':'sealed_10_second_cleanup_deadline','deadline_monotonic':deadline,'observations':observations})
        return snap

    def finish(self, verdict, reason, observations=None):
        snap=self.snapshot('before-harness-teardown')
        value={'id':self.id,'verdict':verdict,'scope':'real_process_and_filesystem','reason':reason,
            'candidate_path':str(CANDIDATE),'freeze_manifest_sha256':'40959a3f3fddf55e198cc4a15ab37ea70097220d9e968db191b3fd434ca76349',
            'observations':observations or {},'protected_ok':self.protected_ok(snap),
            'duration_seconds':time.monotonic()-self.started,'commands':self.commands,'trace':self.trace,
            'tool_identity_before':self.tool_identity_before,'tool_identity_after':hashfile(SCRIPTS/'resource_manager.py'),
            'raw_directory':str(self.raw),'snapshot':'before-harness-teardown.json'}
        dump(self.raw/'result.json',value)
        emergency=[]
        # This happens only AFTER the independent result and raw snapshot are durable.
        if self.worker and self.worker.poll() is None:
            before=identity(self.worker.pid)
            if before['live'] and str(HERE/'resource_worker.py') in before['raw']:
                os.kill(self.worker.pid,signal.SIGKILL); self.worker.wait()
                emergency.append({'target':'manager','before':before,'action':'SIGKILL'})
        for row in snap['owned_fixture_processes']:
            before=identity(row['pid'])
            if before['live'] and self.token in before['raw']:
                try: os.kill(row['pid'], signal.SIGKILL)
                except ProcessLookupError: pass
                emergency.append({'target':'fixture-owned','before':before,'action':'SIGKILL'})
        journal=load(self.root/'journal.json',{}) or {}
        rp=journal.get('process')
        if rp:
            before=identity(rp['pid'])
            if before['live'] and rp.get('token','!missing!') in before['raw'] and str(SCRIPTS/'resource_manager.py') in before['raw']:
                try: os.kill(rp['pid'], signal.SIGKILL)
                except ProcessLookupError: pass
                emergency.append({'target':'journaled-owned-launcher','before':before,'action':'SIGKILL'})
        if self.sentinel.poll() is None:
            before=identity(self.sentinel.pid)
            self.sentinel.terminate()
            try:self.sentinel.wait(timeout=2)
            except subprocess.TimeoutExpired:self.sentinel.kill();self.sentinel.wait()
            emergency.append({'target':'borrowed-probe-fixture','before':before,'action':'intentional harness fixture teardown after verdict'})
        self.sentinel_log.close()
        dump(self.raw/'harness-emergency-cleanup.json',{'after_original_result_only':True,'actions':emergency})
        print(json.dumps({'id':self.id,'verdict':verdict,'reason':reason}),flush=True)
        return value

def test(cid, variant):
    r=Row(cid,variant)
    try:
        if cid=='R01' or cid=='R02' or (cid=='R09' and variant=='borrowed-process-shares-executable-name'):
            mode='orphan-return' if cid!='R02' else ('orphan-error' if variant=='body-command-exits-7' else 'raise-after-run')
            r.start(mode); code=r.wait(); snap=r.await_owned_deadline(time.monotonic()+10)
            if not any(p['role']=='descendant' for p in snap['owned_fixture_processes']):
                return r.finish('U','Owned process tree prerequisite was not reached; actual tool startup error retained',{'exit_code':code,'tool_receipt':snap['tool_receipt']})
            live=r.owned_live(snap)
            ok=code is not None and not live and r.protected_ok(snap) and not (r.root/'scratch').exists()
            if cid!='R02':ok=ok and code==0
            if cid=='R02':ok=ok and code!=0 and bool(snap['tool_receipt'].get('primary_error'))
            return r.finish('P' if ok else 'F','Owned descendant remains live after supervised leader returned' if live else 'Lifecycle ownership/protection check',{'exit_code':code,'live_owned':live})
        if cid=='R03' and variant=='command-timeout':
            r.start('tree-timeout');code=r.wait();snap=r.await_owned_deadline(time.monotonic()+10)
            actual_tree=any(p['role']=='descendant' for p in snap['owned_fixture_processes'])
            if not actual_tree:return r.finish('U','Timeout probe did not reach actual owned-tree startup',{'exit_code':code,'receipt':snap['tool_receipt']})
            error=(snap['tool_receipt'] or {}).get('primary_error') or {}
            ok=code not in {0,None} and error.get('type')=='TimeoutExpired' and not r.owned_live(snap) and r.protected_ok(snap) and not (r.root/'scratch').exists()
            return r.finish('P' if ok else 'F','Actual public timeout and owned-group cleanup checked',{'exit_code':code,'primary_error':error,'public_signature':str(inspect.signature(resource_manager.Resources.run))})
        if cid=='R05' and variant=='SIGKILL-after-first-release':
            r.start('release-first');ready=r.tree_ready() and (r.fixture/'released-one.json').exists()
            if not ready:
                if r.worker.poll() is None:os.kill(r.worker.pid,signal.SIGTERM)
                r.wait();return r.finish('U','Release/crash probe did not reach its actual public release plus subsequent live-tree boundary')
            release=load(r.fixture/'released-one.json');r.snapshot('after-first-release-before-crash')
            os.kill(r.worker.pid,signal.SIGKILL);r.wait();r.snapshot('crash-after-first-release')
            started=time.monotonic();out=r.cli('cleanup','release-crash-reconcile');snap=r.await_owned_deadline(started+10)
            ok=release['released_path_absent'] and out.get('exit_code')==0 and not r.owned_live(snap) and r.protected_ok(snap) and not (r.root/'scratch-second').exists()
            return r.finish('P' if ok else 'F','Crash after actual public release; already released and remaining resources checked',{'release':release,'reconcile':out})
        if cid=='R06' and variant=='finish-twice':
            r.start('finish-twice');code=r.wait();snap=r.await_owned_deadline(time.monotonic()+10);results=load(r.fixture/'finish-results.json',{})
            actual_tree=any(p['role']=='descendant' for p in snap['owned_fixture_processes'])
            if not actual_tree:return r.finish('U','Finish-repeat probe did not reach actual owned-tree startup',{'exit_code':code})
            ok=code==0 and results.get('receipt_unchanged') is True and results.get('events_unchanged') is True and not r.owned_live(snap) and not (r.root/'scratch').exists() and r.protected_ok(snap)
            return r.finish('P' if ok else 'F','Repeated documented finish retained the original receipt and event history',results)
        if cid=='R03' or cid=='R04':
            r.start('tree-ignore-term' if cid=='R03' else 'tree-hang')
            ready=r.tree_ready(); r.snapshot('before-signal')
            cancellation_at=time.monotonic();os.kill(r.worker.pid,signal.SIGINT if variant=='SIGINT' else signal.SIGTERM)
            code=r.wait(); snap=r.snapshot('after-signal')
            snap=r.await_owned_deadline(cancellation_at+10)
            live=r.owned_live(snap)
            ok=ready and code not in {None,0} and not live and r.protected_ok(snap) and bool(snap['tool_receipt'])
            return r.finish('P' if ok else 'F','Cancellation did not reclaim an ignoring descendant' if live else 'Actual signal and owned-resource cleanup checked',{'exit_code':code,'owned_live':live})
        if cid=='R05':
            r.start('tree-hang');ready=r.tree_ready()
            if not ready:
                if r.worker.poll() is None:os.kill(r.worker.pid,signal.SIGTERM)
                r.wait();return r.finish('U','Crash boundary unavailable: real owned-tree startup prerequisite was not reached')
            r.snapshot('before-kill');os.kill(r.worker.pid,signal.SIGKILL);r.wait()
            before=r.snapshot('crash-before-reconcile')
            if variant=='truncated-final-journal-record':
                p=r.root/'journal.json';raw=p.read_bytes();(r.raw/'original-journal.json').write_bytes(raw);p.write_bytes(raw[:-8])
                (r.raw/'truncated-journal.json').write_bytes(p.read_bytes())
                shutil.copyfile(r.root/'journal-backup.json',r.raw/'original-journal-backup.json')
            reconcile_started=time.monotonic();outcome=r.cli('cleanup','reconcile-1');after=r.await_owned_deadline(reconcile_started+10)
            ok=ready and outcome.get('exit_code')==0 and not r.owned_live(after) and r.protected_ok(after) and not (r.root/'scratch').exists()
            return r.finish('P' if ok else 'F','Crash reconciliation retained live owned resources / could not recover earlier ownership' if not ok else 'Dead-owner reconcile reclaimed only owned resources',{'before_owned_live':r.owned_live(before),'after_owned_live':r.owned_live(after),'reconcile':outcome})
        if cid=='R06':
            r.start('simple-return');code=r.wait();a=r.cli('cleanup','cleanup-1');b=r.cli('cleanup','cleanup-2');s=r.snapshot('after-second-cleanup')
            ok=code==0 and a.get('exit_code')==0 and b.get('exit_code')==0 and r.protected_ok(s)
            return r.finish('P' if ok else 'F','Two explicit public cleanup calls checked',{'first':a,'second':b})
        if cid=='R07':
            if variant.startswith('preexisting-directory'):r.root.mkdir();(r.root/'sentinel.txt').write_text('preexisting')
            else:r.root.write_text('preexisting-file')
            original=hashfile(r.root/'sentinel.txt') if r.root.is_dir() else hashfile(r.root)
            r.start('simple-return');code=r.wait();s=r.snapshot('after-rejection')
            actual=hashfile(r.root/'sentinel.txt') if r.root.is_dir() else hashfile(r.root)
            ok=code not in {0,None} and actual==original and not (r.fixture/'requested-run.json').exists() and r.protected_ok(s)
            return r.finish('P' if ok else 'F','Preexisting unowned root refused before command dispatch',{'exit_code':code,'before_hash':original,'after_hash':actual})
        if cid=='R08' and variant!='recorded-path-escapes-root':
            r.start('pause');ready=r.pause_ready();p=r.root/'scratch';p.rename(r.root/'original-owned')
            if 'symlink' in variant:p.symlink_to(r.borrowed,target_is_directory=True)
            else:p.mkdir();(p/'foreign.txt').write_text('foreign replacement')
            r.snapshot('before-replaced-path-cleanup');(r.fixture/'release').touch();code=r.wait();s=r.snapshot('after-replaced-path-cleanup')
            receipt=s['tool_receipt'] or {};ok=ready and code not in {0,None} and bool(receipt.get('cleanup_errors')) and r.protected_ok(s)
            return r.finish('P' if ok else 'F','Substituted path refused; original conflict remains explicit',{'exit_code':code,'receipt':receipt})
        if cid=='R08':
            r.start('simple-return',final=False);r.wait();p=r.root/'journal.json';j=load(p);dump(r.raw/'original-journal.json',j);j['directories'][0]['name']='../borrowed-directory';dump(p,j)
            out=r.cli('cleanup','traversal-cleanup');s=r.snapshot('after-traversal')
            ok=out.get('exit_code') not in {0,None} and r.protected_ok(s)
            return r.finish('P' if ok else 'F','Escaping cleanup record refused without altering borrowed bytes',out)
        if cid=='R09':
            r.start('tree-hang');r.tree_ready();os.kill(r.worker.pid,signal.SIGKILL);r.wait();j=load(r.root/'journal.json');dump(r.raw/'original-journal.json',j)
            if variant.startswith('stale-PID'):j['process']['pid']=r.sentinel.pid
            else:j['process']['identity'] += ' wrong-start-identity'
            dump(r.root/'journal.json',j);before=r.snapshot('before-mismatched-reconcile');out=r.cli('cleanup','identity-cleanup');after=r.snapshot('after-mismatched-reconcile')
            ok=out.get('exit_code') not in {0,None} and r.protected_ok(after)
            if variant.startswith('owned-marker'):ok=ok and bool(r.owned_live(after))
            return r.finish('P' if ok else 'F','Live identity mismatch refused before termination',{'reconcile':out,'before':before['borrowed_process'],'after':after['borrowed_process']})
        if cid=='R10':
            r.start('tree-hang');ready=r.tree_ready();before=r.snapshot('live-owner-before-challenge')
            if not ready:
                if r.worker.poll() is None:os.kill(r.worker.pid,signal.SIGTERM)
                r.wait();return r.finish('U','Live-lease challenge did not reach the real owned-tree prerequisite; actual startup failure preserved')
            if variant=='two-live-sessions-different-roots':
                other=Row('R10-side',uuid.uuid4().hex[:8]);other.start('tree-hang');other_ready=other.tree_ready();time.sleep(2);side=other.snapshot('overlap')
                os.kill(other.worker.pid,signal.SIGTERM);other.wait();other_result=other.finish('P' if other_ready and other.protected_ok(side) else 'F','Auxiliary disjoint live session, not a sealed additional row')
                out={'other_ready':other_ready,'other_result':other_result}
                challenge_ok=other_ready
            else:
                out=r.cli('inspect','live-lease-challenge');time.sleep(2);challenge_ok=out.get('exit_code') not in {0,None}
            after=r.snapshot('live-owner-after-challenge');same_live=all(p['observed_identity']['live'] for p in after['owned_fixture_processes'])
            os.kill(r.worker.pid,signal.SIGTERM);r.wait();ok=ready and challenge_ok and same_live and r.protected_ok(after)
            return r.finish('P' if ok else 'F','Exclusive lease / session isolation checked with actual overlapping processes',{'challenge':out,'owned_same_live':same_live})
        if cid=='R11':
            r.start('pause');ready=r.pause_ready();scratch=r.root/'scratch';payload=scratch/'payload.txt';scratch.chmod(0o500)
            denied=False
            try:payload.unlink()
            except PermissionError as e:denied=True;dump(r.raw/'OS-permission-denial.json',{'error_type':type(e).__name__,'error':str(e)})
            if not denied:
                scratch.chmod(0o700);payload.write_text('owned temporary payload\n');(r.fixture/'release').touch();r.wait()
                return r.finish('U','This account/OS did not produce a real cleanup permission denial')
            (r.fixture/'release').touch();code=r.wait();first=r.snapshot('original-cleanup-denied');scratch.chmod(0o700);retry=r.cli('cleanup','permissions-restored-retry');s=r.snapshot('after-retry')
            ok=ready and code not in {0,None} and bool((first['tool_receipt'] or {}).get('cleanup_errors')) and retry.get('exit_code')==0 and r.protected_ok(s)
            return r.finish('P' if ok else 'F','Real OS denial, retained original failure, then separate retry',{'original':first['tool_receipt'],'retry':retry})
        if cid=='R12':
            r.start('simple-return' if variant=='success' else 'tree-hang')
            if variant=='success':code=r.wait();out=None
            else:
                r.tree_ready();os.kill(r.worker.pid,signal.SIGTERM if variant=='cancel' else signal.SIGKILL);code=r.wait()
                out=r.cli('cleanup','protection-reconcile') if variant=='crash-reconcile' else None
            s=r.snapshot('after-protected-lifecycle');ok=r.protected_ok(s)
            return r.finish('P' if ok else 'F','Source, shared cache, borrowed files and original evidence identities checked',{'exit_code':code,'reconcile':out})
        return r.finish('U','No public mapping was implemented by this argument-only verifier')
    except BaseException as error:
        dump(r.raw/'harness-error.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
        return r.finish('U','Probe harness error; original execution retained, not a tool pass',{'error':str(error)})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--only-id',action='append');parser.add_argument('--execution-name',default='resource-results');args=parser.parse_args()
    cases=json.loads((HERE.parents[1]/'spec/cases.json').read_text())
    results=load(HERE/(args.execution_name+'.partial.json'),[]) or []
    completed={r['id'] for r in results}
    for c in cases['cases']:
        if c['id'].startswith('R'):
            for variant in c['variants']:
                if args.only_id and c['id']+'/'+variant not in args.only_id:continue
                if c['id']+'/'+variant in completed: continue
                results.append(test(c['id'],variant))
                dump(HERE/(args.execution_name+'.partial.json'),results)
    dump(HERE/(args.execution_name+'.json'),results)
