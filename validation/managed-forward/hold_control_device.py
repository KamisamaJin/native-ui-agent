#!/usr/bin/env python3
"""A positively owned study device lent to the complete frozen old controller."""
import argparse
import json
import signal
import sys
import time
from pathlib import Path

import business

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / 'candidate-v12.6/scripts'))
from resource_manager import Resources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--arm', choices=['A', 'B'], required=True)
    args = parser.parse_args()
    study = R / 'cache/study'
    workspace = args.workspace.resolve()
    output = study / 'control-device-lease'
    config = {'source_roots': [str(workspace / rel) for rel in business.ROOTS],
              'native_options': {'simulator': 'managed',
                                 'build-cache': str(study / 'arms' / args.arm / 'ios-build-cache'),
                                 'developer-dir': '/Applications/Xcode.app/Contents/Developer'},
              'resources': {'root': str(study / 'control-device'), 'max_bytes': 32 * 2**30,
                            'min_free_bytes': 5 * 2**30, 'sample_seconds': 1,
                            'ios': {'device_type': 'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro',
                                    'runtime': 'com.apple.CoreSimulator.SimRuntime.iOS-26-5'}}}
    business.save(study / 'control-device-config.json', config)
    def interrupted(signum, _frame):
        raise InterruptedError('Study device holder interrupted: ' + str(signum))
    for signum in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(signum, interrupted)
    with Resources(config, output, final=True) as resource:
        options = resource.native_options('ios')
        business.save(study / 'control-device-ready.json', {'at_unix': time.time(), 'simulator': options['simulator'],
                                                           'owner': resource.identity,
                                                           'scope': 'Common study-owned device; old tool only borrows it. No default lifecycle behavior is backported.'})
        deadline = time.monotonic() + 10800
        while time.monotonic() < deadline:
            path = study / 'release-control-device.json'
            if path.is_file():
                if business.read(path) != {'owner': resource.identity}:
                    raise ValueError('Foreign release request')
                break
            resource.sample()
            resource.check_budget()
            time.sleep(1)
        else:
            raise TimeoutError('Three-hour common device lease expired')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
