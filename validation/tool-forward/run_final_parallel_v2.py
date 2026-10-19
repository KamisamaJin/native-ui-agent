#!/usr/bin/env python3
"""Final-only resource scheduling; calls the unchanged frozen capture harness.

Each parity worker has its own fresh pinned source checkout and simulator.
No test/tool/fixture/expected outcome is changed. Android remains sequential.
"""
import argparse
import concurrent.futures
import json
import subprocess
import time
from pathlib import Path

R = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--odd-workspace', type=Path, required=True)
    p.add_argument('--even-workspace', type=Path, required=True)
    p.add_argument('--odd-simulator', required=True)
    p.add_argument('--even-simulator', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--capability', type=Path, required=True)
    a = p.parse_args()
    source = R / 'private/inputs/final'
    manifest = json.loads((source / 'manifest.json').read_text())
    names = sorted(c['case'] for c in manifest['cases'])
    assert len(names) == 8 and len(set(names)) == 8, 'Eight distinct manifest-defined cases required'
    for submission in ['submission-b2e249', 'submission-4f4364']:
        assert (R / 'implementations/final' / submission / 'manifest.json').is_file()
    a.output.mkdir(parents=True, exist_ok=True)

    def worker(index):
        workspace = (a.odd_workspace if index == 0 else a.even_workspace).resolve()
        simulator = a.odd_simulator if index == 0 else a.even_simulator
        results = []
        for name in names[index::2]:
            dest = a.output / 'ios' / name
            assert not dest.exists(), 'No silent overwrite or retry'
            dest.parent.mkdir(parents=True, exist_ok=True)
            command = ['python3', str(R / 'harness/capture.py'), '--platform', 'ios',
                       '--project', str(workspace / 'alerttoast'), '--fixture', str(source / (name + '.json')),
                       '--output', str(dest), '--capability', str(a.capability.resolve()),
                       '--simulator', simulator]
            started = time.time()
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            results.append({'case': name, 'platform': 'ios', 'command': command,
                            'started_at': started, 'finished_at': time.time(),
                            'seconds': round(time.time() - started, 3),
                            'exit_code': result.returncode, 'output': result.stdout})
            (a.output / ('ios-parity-%s-progress.json' % index)).write_text(json.dumps(results, indent=2) + '\n')
        return results

    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, [0, 1]))
    (a.output / 'ios-parallel-operator-summary.json').write_text(json.dumps({
        'phase': 'final', 'started_at': started, 'finished_at': time.time(),
        'parity_assignment': {'odd': names[0::2], 'even': names[1::2]}, 'results': results,
        'scope': 'Two identical per-arm iOS slots, fresh checkouts, unchanged capture harness/tools/inputs. Parallel calendar time is not comparable with sequential D0 as a tool-speed effect.'}, indent=2) + '\n')


if __name__ == '__main__':
    main()
