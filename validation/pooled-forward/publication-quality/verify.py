#!/usr/bin/env python3
"""Read-only mechanical publication input checks, with explicit live/restore mode."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

from integrity import verify_packet


RESOLVER_SHA = '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204'


def reader_module():
    path = Path(__file__).resolve().parent.parent / 'publication-resolver/resolver.py'
    if hashlib.sha256(path.read_bytes()).hexdigest() != RESOLVER_SHA:
        raise ValueError('Publication resolver code pin differs')
    spec = importlib.util.spec_from_file_location('quality_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LiveReader:
    """Explicit original-file access for pre-archive checks, never a restore fallback."""
    def __init__(self, module):
        self.module = module

    def read_bytes(self, original):
        return self.module.read_regular(original)[0]

    def read_json(self, original):
        return self.module.strict_json(self.read_bytes(original))

    def directory(self, original):
        path = self.module.absolute(str(original))
        fd = self.module.open_directory(path)
        os.close(fd)
        return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--packet', required=True)
    p.add_argument('--ledger', required=True)
    p.add_argument('--packet-seal-sha256', required=True)
    p.add_argument('--ledger-sha256', required=True)
    p.add_argument('--output', required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--live-read-only', action='store_true')
    mode.add_argument('--restore-map')
    p.add_argument('--map-sha256')
    p.add_argument('--index-sha256')
    a = p.parse_args()
    started = time.time()
    status = 0
    try:
        module = reader_module()
        reader = (LiveReader(module) if a.live_read_only else
                  module.Resolver(a.restore_map, map_sha256=a.map_sha256, index_sha256=a.index_sha256))
        result = verify_packet(reader, a.packet, a.ledger, packet_seal_sha256=a.packet_seal_sha256,
                               ledger_sha256=a.ledger_sha256)
    except BaseException as error:
        status = 1
        result = {'status': 'failed', 'error': {'type': type(error).__name__, 'message': str(error)},
                  'traceback': traceback.format_exc()}
    result.update(started_at_unix=started, finished_at_unix=time.time(),
                  reader_mode='live-read-only' if a.live_read_only else 'explicit-pinned-restore',
                  native_or_sdk_execution=False)
    destination = Path(a.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    destination.chmod(0o444)
    print(json.dumps({'status': result['status'], 'output': str(destination), 'error': result.get('error')}))
    return status


if __name__ == '__main__':
    sys.exit(main())
