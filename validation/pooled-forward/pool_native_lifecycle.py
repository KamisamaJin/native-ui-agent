#!/usr/bin/env python3
"""Actual simctl resource lifecycle qualification, separate from UI SDK claims."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill', type=Path, required=True); p.add_argument('--config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    sys.path.insert(0, str(a.skill.resolve() / 'scripts'))
    from resource_manager import Resources
    import pool_watch
    out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    config = json.loads(a.config.read_text()); study = Path(__file__).resolve().parent
    config = copy.deepcopy(config)
    if config['resources']['root'] != str(study / 'cache/qualification/lifecycle/resources/ios'):
        raise ValueError('Predeclared lifecycle resource namespace required')
    def save(name, v):
        with (out / name).open('x') as f: f.write(json.dumps(v, indent=2) + '\n')
    env = dict(os.environ, DEVELOPER_DIR=config['native_options']['developer-dir'])
    inventories = []
    def inventory(phase):
        at = time.time(); r = subprocess.run(['xcrun', 'simctl', 'list', 'devices', '--json'], env=env, text=True,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
        value = json.loads(r.stdout); inventories.append({'phase': phase, 'started_at_unix': at, 'finished_at_unix': time.time(), 'raw': value})
        save('inventory-' + str(len(inventories)) + '.json', inventories[-1])
        return {d['udid']: d for rows in value['devices'].values() for d in rows}
    save('PLAN.json', {'at_unix': time.time(), 'config': config, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'scope': 'Actual SDK resource create/reuse/expiry/retirement and HOST leases. No UI test, app freshness, rendering or performance claim.',
         'expected': ['same active checkout', 'active lease survives idle limit', 'same compatible idle UUID before expiry',
                      'guardian actually deletes expired idle UUID', 'new UUID after expiry', 'final resource closure', 'borrowed own loaner/device/build path preserved']})
    checks = []; before = inventory('before')
    def check(name, passed, details=None): checks.append({'id': name, 'passed': bool(passed), 'details': details})
    try:
        with Resources(config, out / 'first') as first:
            one = first.native_options(platform='ios')['simulator']
            again = first.native_options(platform='ios')['simulator']
            check('same-active-checkout', one == again and len(first.state['devices']) == 1)
            time.sleep(4)
            check('active-lease-not-expired', one in inventory('active-after-idle-limit'))
            command = [sys.executable, '-B', str(a.skill / 'scripts/resource_manager.py'), '--config', str(out / 'config.json'), '--output', str(out / 'contender'), 'inspect']
            save('config.json', config)
            with (out / 'contender.log').open('x') as stream:
                contender = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=20)
            check('real-concurrent-lock-refused', contender.returncode != 0 and len(first.state['devices']) == 1)
        with Resources(config, out / 'second') as second:
            two = second.native_options(platform='ios')['simulator']
            check('actual-compatible-idle-reuse', one == two, {'one': one, 'two': two})
            watch_pid = second.state['pool_watch']['pid']
            watch = pool_watch._CHILDREN.get(watch_pid)
        deadline = time.perf_counter() + 30
        while time.perf_counter() < deadline:
            if watch is not None:
                if watch.poll() is not None: break
            elif one not in inventory('expiry-poll'): break
            time.sleep(.25)
        after_expiry = inventory('after-expiry')
        check('actual-idle-expiry-retirement', one not in after_expiry)
        with Resources(config, out / 'after-expiry', final=True) as third:
            three = third.native_options(platform='ios')['simulator']
            check('new-uuid-after-expiry', three != one, {'expired': one, 'new': three})
        check('final-retirement', three not in inventory('after-final'))
        loaner_config = copy.deepcopy(config)
        loaner_config['resources']['root'] = str(study / 'cache/qualification/lifecycle/loaner/ios')
        with Resources(loaner_config, out / 'loaner-owner', final=True) as owner:
            options = owner.native_options(platform='ios'); loaner = options['simulator']; cache = Path(options['build-cache'])
            marker = (cache / '.native-ui-owner.json').read_bytes(); inode = cache.stat().st_ino
            borrowed = copy.deepcopy(config)
            borrowed['native_options'] = {k: v for k, v in options.items() if k in {'package', 'simulator', 'developer-dir', 'build-cache', 'product', 'sdk'}}
            with Resources(borrowed, out / 'borrower-final', final=True) as borrower:
                returned = borrower.native_options(platform='ios')
                check('borrowed-not-adopted', returned['simulator'] == loaner and not borrower.state['devices'])
                check('borrowed-not-reset-authorized', 'reset-owned-app' not in returned)
            check('borrowed-device-and-build-preserved', loaner in inventory('after-borrower-final') and
                  cache.stat().st_ino == inode and (cache / '.native-ui-owner.json').read_bytes() == marker)
        after = inventory('after-all-owners-closed')
        check('owned-devices-all-retired', not ({one, two, three, loaner} & set(after)))
    finally:
        save('checks.json', {'checks': checks, 'passed': all(v['passed'] for v in checks), 'scope': 'Actual native resource identities and HOST leases; not UI or business truth.'})
    print(json.dumps({'checks': len(checks), 'passed': all(v['passed'] for v in checks)}))
    return 0 if all(v['passed'] for v in checks) else 1


if __name__ == '__main__': raise SystemExit(main())
