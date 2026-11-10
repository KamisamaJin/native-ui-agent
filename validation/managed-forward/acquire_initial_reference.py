#!/usr/bin/env python3
"""Shared post-barrier hidden reference for the immutable original PR."""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import business
from acquire_business import CommonSafety, configuration, verify_host, verify_release

R = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=['ios', 'android'], required=True)
    args = parser.parse_args()
    verify_release()
    authority = business.authorize('self-finals')
    for arm in ['A', 'B']:
        for pl in ['ios', 'android']:
            if not (R / 'cache/study/arms' / arm / 'runs/Hidden' / pl / 'command.json').is_file():
                raise ValueError('Both final hidden native requests must close before shared reference')
    workspace = R / 'cache/study/author/workspace'
    assert business.fingerprint(workspace) == business.read(R / 'business-evidence/initial/seal.json')['files']
    verify_host(workspace, R / 'business-evidence/common-preparation/HOST-SEAL.json')
    # Reuse only the explicitly study-created control device, after both arms'
    # hidden acquisitions. No third concurrent device; this is grading cost.
    ready = business.read(R / 'cache/study/control-device-ready.json')
    scope = R / 'business-design/private'
    config = configuration(workspace, scope, 'evening-service', args.platform, 'B', ready['simulator'])
    base = R / 'cache/study/initial-hidden'
    config['resources']['root'] = str(base / 'resources' / args.platform)
    if args.platform == 'ios':
        config['native_options'].pop('build-cache', None)
    config['review_store'] = str(base / 'reviews' / args.platform)
    config['source_review_store'] = str(base / 'source-reviews' / args.platform)
    output = base / 'runs' / args.platform
    output.mkdir(parents=True, exist_ok=False)
    business.save(output / 'config.json', config)
    argv = [sys.executable, '-B', str(R / 'candidate-v12.6/scripts/ui_loop.py'), 'native',
            '--config', str(output / 'config.json'), '--output', str(output / 'cycle'), '--final']
    started = time.time()
    business.save(output / 'started.json', {'started_at_unix': started, 'authorization': authority,
                                          'source_seal_sha256': business.sha(R / 'business-evidence/initial/seal.json'),
                                          'adapter_sha256': business.sha(Path(__file__)), 'argv': argv,
                                          'scope': 'Shared independent grading reference, not either repair arm or a new repair attempt.'})
    safety = {'source_roots': config['source_roots'], 'native_options': {},
              'resources': {'root': str(R / 'cache/study/outer-safety/initial-reference' / args.platform),
                            'max_bytes': 32 * 2**30, 'min_free_bytes': 5 * 2**30,
                            'sample_seconds': 1, 'command_timeout_seconds': 1200}}
    code = None
    try:
        with CommonSafety(safety, output / 'common-safety', final=True) as resources:
            with (output / 'controller.log').open('wb') as stream:
                code = resources.run(argv, env=dict(os.environ), stdout=stream)
    finally:
        business.save(output / 'command.json', {'started_at_unix': started, 'finished_at_unix': time.time(),
                                               'exit_code': code, 'argv': argv,
                                               'source_unchanged': business.fingerprint(workspace) == business.read(R / 'business-evidence/initial/seal.json')['files'],
                                               'cost_attribution': 'Common initial-reference grading; exclude from per-arm tool advantage.'})
    verify_host(workspace, R / 'business-evidence/common-preparation/HOST-SEAL.json')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
