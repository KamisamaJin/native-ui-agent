"""Use only the candidate snapshot's actual compilers; never launch an SDK."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT.parent / 'development/candidate-attempt-1'
SCRIPTS = SNAPSHOT / 'scripts'
LOG = ROOT / 'logs/compile-attempts.jsonl'

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def load(path):
    return json.loads(path.read_text())

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def run(script, args):
    command = [sys.executable, '-B', str(SCRIPTS / script), *map(str, args)]
    before = time.time()
    result = subprocess.run(command, capture_output=True, text=True)
    row = {'command': command, 'started_unix': before, 'finished_unix': time.time(),
           'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    with LOG.open('a') as stream:
        stream.write(json.dumps(row) + '\n')
    print(json.dumps(row, indent=2))
    if result.returncode:
        raise SystemExit(result.returncode)
    return result

def main():
    bridge = ROOT / 'source/Bridge.swift'
    bridge_sha = hashlib.sha256(bridge.read_bytes()).hexdigest()
    launches = {name: {'scenario': name, 'platform': 'ios',
                'fixtures_sha256': digest(load(ROOT / ('inputs/' + name + '.json'))),
                'bridge_sha256': bridge_sha} for name in ['ordinary400', 'narrow280-large']}
    write(ROOT / 'design/launch.json', launches)
    contract = load(ROOT / 'design/contract.json')
    contract['sources'] = [{'id': sid, 'path': name, 'sha256': hashlib.sha256((ROOT / 'design' / name).read_bytes()).hexdigest()}
                           for sid, name in [('reference', 'reference.json'), ('launch', 'launch.json')]]
    write(ROOT / 'design/contract.json', contract)
    lock_path = ROOT / 'design/lock.json'
    run('design_contract.py', ['seal', '--contract', ROOT / 'design/contract.json', '--root', ROOT / 'design', '--output', lock_path])
    lock_sha = digest(load(lock_path))
    routes_sha = digest(load(ROOT / 'design/routes.json'))
    approval = {'version': 1, 'approved_unix': time.time(), 'design_lock_sha256': lock_sha,
                'routes_sha256': routes_sha, 'bridge_sha256': bridge_sha,
                'authority': 'Independent neutral forward-test author under parent request',
                'approval_scope': 'Exact fixed design, obligations, routes and launch inputs. No native result has been seen; no SDK has been executed.',
                'preimplementation_record': 'design/PREIMPLEMENTATION.json',
                'launch_approvals': launches,
                'expected_source_change': 'Only sources records were added to the preimplementation contract to pin existing reference and launch bytes; no rule, state, action or expected expression changed.'}
    write(ROOT / 'APPROVAL.json', approval)
    for name in ['ordinary400', 'narrow280-large']:
        case = ROOT / 'generated' / name
        run('design_contract.py', ['compile', '--lock', lock_path, '--lock-sha256', lock_sha,
            '--scenario', name, '--platform', 'ios', '--bindings', ROOT / 'inputs/bindings.json',
            '--actions', ROOT / 'inputs/actions.json', '--output', case / 'design'])
        run('requirement_routes.py', ['audit', '--plan', case / 'design/plan.json', '--design-lock', lock_path,
            '--design-sha256', lock_sha, '--routes', ROOT / 'design/routes.json', '--routes-sha256', routes_sha,
            '--output', case / 'coverage.json'])
        for strategy in ['legacy', 'coalesced']:
            run('execution_plan.py', ['--plan', case / 'design/plan.json', '--design-lock', lock_path,
                '--design-sha256', lock_sha, '--fixtures', ROOT / ('inputs/' + name + '.json'), '--bridge', bridge,
                '--launch-source', 'launch', '--launch-pointer', '/' + name,
                '--strategy', strategy, '--output', case / strategy])
    print(json.dumps({'design_lock_sha256': lock_sha, 'routes_sha256': routes_sha, 'bridge_sha256': bridge_sha}, indent=2))

if __name__ == '__main__':
    main()
