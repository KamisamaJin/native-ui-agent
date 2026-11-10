#!/usr/bin/env python3
"""Run one offline historical publication check under owned resource supervision."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import shutil

R = Path(__file__).resolve().parent
REPO = R.parents[1]
sys.path.insert(0, str(REPO/'native-ui-agent/scripts'))
from resource_manager import Resources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version', choices=['feedback-v9', 'default-v10', 'routed-v11'])
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if Path(args.name).name != args.name:
        raise ValueError('One fresh output name required')
    script = REPO/'validation/publications'/(args.version+'-replay')/'verify.py'
    output = R/'operators'/args.name
    # Some frozen verifiers exclude absolute paths containing a component named
    # cache. Keep their source views inside a differently named owned root.
    scratch = R/'history-scratch'/args.name
    if output.exists() or scratch.exists():
        raise ValueError('Fresh replay output and owned scratch required')
    sources = [script, REPO/'validation/publications/historical_sources.py', Path(__file__).resolve(),
               REPO/'native-ui-agent/scripts/resource_manager.py']
    before = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    config = {'source_roots':list(before),
              'native_options':{}, 'resources':{'root':str(scratch), 'max_bytes':20*2**30,
                                               'min_free_bytes':5*2**30,'sample_seconds':5}}
    argv = [sys.executable,'-B',str(script)]
    started = time.time()
    # The resource root is fresh, journaled and locked before any child can run.
    with Resources(config, output/'resources', final=True) as resources:
        temporary = resources.directory('temporary')
        output.mkdir(parents=True)
        with (output/'check.log').open('x') as log:
            code = resources.run(argv, env=dict(os.environ, TMPDIR=str(temporary), PYTHONDONTWRITEBYTECODE='1'),
                                 stdout=log, timeout=1800)
    record = {'argv':argv,'started_at_unix':started,'finished_at_unix':time.time(),
              'exit_code':code,'source_sha256_before':before,
              'source_sha256_after':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              'scope':'Offline original-byte/metric replay only; no SDK or new business grading.'}
    if record['source_sha256_before'] != record['source_sha256_after']:
        record['exit_code']=code=1
        record['error']='Replay source changed while executing'
    (output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    # Finalization has already copied journal/events into the permanent receipt.
    # Reacquire the root lock and require the same journal generation/identity;
    # remove only this fresh harness root with no owned handles remaining.
    with (scratch/'lease.lock').open('a') as lease:
        fcntl.flock(lease.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
        journal=json.loads((scratch/'journal.json').read_text())
        assert json.loads((scratch/'owner.json').read_text())==resources.identity
        assert journal==resources.state and not journal.get('process') and not journal['directories'] and not journal['devices']
        assert journal['root_identity']=={'device':scratch.stat().st_dev,'inode':scratch.stat().st_ino}
        shutil.rmtree(scratch)
    (output/'root-cleanup.json').write_text(json.dumps({'path':str(scratch),'removed':not scratch.exists(),
       'owner':resources.identity,'journal_generation':journal['generation'],'at_unix':time.time()},indent=2)+'\n')
    if not any(scratch.parent.iterdir()): scratch.parent.rmdir()
    print(json.dumps(record))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
