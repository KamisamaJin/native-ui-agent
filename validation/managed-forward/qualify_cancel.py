#!/usr/bin/env python3
"""Cancel one freshly launched neutral SDK run after a complete real frame.

Qualification harness only: observes the managed tool, never supplies its cleanup.
The exact owned process group is sampled before/after; escaped daemons, simulator
leases, and product quality are outside this Android provider qualification.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from PIL import Image

R = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group_members(group):
    output = subprocess.check_output(
        ['ps', '-axww', '-o', 'pid=', '-o', 'ppid=', '-o', 'pgid=',
         '-o', 'state=', '-o', 'lstart=', '-o', 'command='], text=True)
    rows = []
    for line in output.splitlines():
        parts = line.split(None, 9)
        if len(parts) != 10 or parts[2] != str(group) or parts[3].startswith('Z'):
            continue
        rows.append(dict(pid=int(parts[0]), ppid=int(parts[1]), pgid=int(parts[2]),
                         state=parts[3], started=' '.join(parts[4:9]),
                         executable=Path(parts[9].split()[0]).name,
                         command_sha256=hashlib.sha256(parts[9].encode()).hexdigest()))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--config', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--record', required=True, type=Path)
    a = p.parse_args()
    assert not a.output.exists() and not a.record.exists(), 'Fresh outputs required'
    a.record.mkdir(parents=True)
    config = json.loads(a.config.read_text())
    journal = Path(config['resources']['root']) / 'journal.json'
    sources = [Path(s) for s in config['source_roots']]
    argv = [sys.executable, '-B', str(a.candidate.resolve()/'scripts/ui_loop.py'),
            'native', '--config', str(a.config.resolve()),
            '--output', str(a.output.resolve()), '--final']
    row = dict(argv=argv, started_at_unix=time.time(),
               source_hashes_before={str(s):sha(s) for s in sources},
               scope='Actual Android SDK interruption qualification after a fully decoded frame. '
                     'Exact owned process-group cleanup only; no escaped-daemon, OS/iOS, or business PR claim.')
    process = None
    qualified = False
    try:
        with (a.record/'controller.log').open('x') as log:
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 180
            while process.poll() is None and time.monotonic() < deadline:
                frame = next(iter(sorted((a.output/'capture/native').glob('*.png'))), None)
                try:
                    if not frame or not journal.is_file():
                        time.sleep(.02); continue
                    with Image.open(frame) as image:
                        image.load(); size = list(image.size)
                    lease = json.loads(journal.read_text()).get('process', {})
                    group = group_members(lease['pgid'])
                    # Only the private SDK group is qualifying; outer command
                    # handle is the one launched above and never rediscovered.
                    if not group or 'android_observe.py' not in json.dumps(lease):
                        time.sleep(.02); continue
                    sdk_log = a.output/'capture/native/test.log'
                    prefix = sdk_log.read_bytes() if sdk_log.is_file() else b''
                    row.update(first_frame=dict(path=str(frame.resolve()), sha256=sha(frame), decoded_size=size),
                               sdk_process_receipt_before_cancel=lease, group_before=group,
                               log_before_cancel=dict(bytes=len(prefix), sha256=hashlib.sha256(prefix).hexdigest()))
                    # Preserve exact prefix, not a recreated error message.
                    (a.record/'pre-cancel-sdk-prefix.log').write_bytes(prefix)
                    qualified = True
                    break
                except (OSError, ValueError, KeyError):
                    time.sleep(.02)
            row['observed_complete_in_flight_sdk_frame'] = qualified
            if process.poll() is None:
                row['signal_at_unix'] = time.time()
                process.send_signal(signal.SIGTERM)
            row['exit_code'] = process.wait(timeout=30)
        row['group_after_samples'] = []
        if qualified:
            deadline = time.monotonic() + 10
            while True:
                members = group_members(row['sdk_process_receipt_before_cancel']['pgid'])
                row['group_after_samples'].append(dict(at_unix=time.time(), members=members))
                if not members or time.monotonic() >= deadline: break
                time.sleep(.1)
        sdk_log = a.output/'capture/native/test.log'
        if sdk_log.is_file():
            content = sdk_log.read_bytes()
            row['log_after_cancel'] = dict(bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
                                           retained_original_prefix=qualified and bool(prefix) and content.startswith(prefix))
        row['source_hashes_after'] = {str(s):sha(s) for s in sources}
        row['cycle_published'] = (a.output/'cycle.json').exists()
        project = Path(config['native_options']['project'])
        row['reserved_test_folder_exists'] = (project/'app/src/test/java/org/nativeobserver').exists()
        row['resources'] = json.loads((a.output/'resources.json').read_text())
        assert qualified, 'No complete in-flight frame; cancellation qualification not established'
        assert row['exit_code'] != 0 and not row['cycle_published']
        assert row['source_hashes_before'] == row['source_hashes_after']
        assert not row['reserved_test_folder_exists']
        assert row['group_after_samples'][-1]['members'] == []
        assert row['log_after_cancel']['retained_original_prefix']
        assert not row['resources']['cleanup_errors']
        row['status'] = 'PASS'
    except BaseException as error:
        row['status'] = 'not_qualified'
        row['error'] = dict(type=type(error).__name__, message=str(error))
        # Deliberately no harness process/group cleanup which could grant false
        # credit to the tool. Keep raw state for explicit recovery if necessary.
    finally:
        row['finished_at_unix'] = time.time()
        (a.record/'result.json').write_text(json.dumps(row, indent=2)+'\n')
    print(json.dumps({k:row.get(k) for k in ['status','exit_code','error','observed_complete_in_flight_sdk_frame','log_after_cancel']}))
    return 0 if row['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
