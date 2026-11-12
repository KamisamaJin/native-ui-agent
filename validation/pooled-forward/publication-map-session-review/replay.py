#!/usr/bin/env python3
"""Common pure archive replay using a bounded map session, never a live source.

The source/domain grading limitations and all original provenance checks are
unchanged. Only repeated complete-map hashing is amortized with a no-follow
identity guard; every mapped payload is still hashed at final closure.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from session import MapSessionReader

HERE = Path(__file__).resolve().parent
PRESERVE_SHA = '4a1e18ebb43d1cddf82a02f69666d2ec9b898204c131469905b6a96646657a83'


def frozen_preserver():
    path = HERE.parent/'publication-actual-preservation-review/preserve.py'
    if hashlib.sha256(path.read_bytes()).hexdigest() != PRESERVE_SHA:
        raise ValueError('Frozen preservation orchestration pin differs')
    spec = importlib.util.spec_from_file_location('session_preservation_primitives', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def replay(plan, archive, index_sha, restore_map, map_sha):
    p = frozen_preserver(); p.A.verify(p.A.absolute(str(archive)), index_sha)
    base = MapSessionReader(restore_map, map_sha256=map_sha, index_sha256=index_sha)
    p.need(all(int(row['restored_mode'], 8) & 0o222 == 0 for row in base._rows.values()), 'Readonly restore required')
    public = p.module('audit').verify_run(base, str(Path(plan['study_root'])/'cache/business/run-cohort2'), require_hidden_authorization=True)
    history = p.module('history_view').HistoryReader(base, plan['history_ledger'])
    native = p.module('native_chain').verify_chain(history, plan['study_root'], plan['native_snapshot'])
    occurrence = p.module('replay_occurrences_v2').replay(base, plan['occurrence_input'])
    p.need(public.get('status') == native.get('status') == occurrence.get('status') == 'verified',
           'Recorded replay failed; preserve failure and block cleanup')
    p.need(native.get('terminal_scopes') == 30 and native.get('pending_scopes') == [],
           'Whole30 original terminal scopes required; no product pass inferred')
    count = base.verify_all(); base.close(); p.A.verify(p.A.absolute(str(archive)), index_sha)
    return {'version': 1, 'kind': 'readonly-map-session-provenance-replay-receipt', 'status': 'verified',
        'archive_index_sha256': index_sha, 'restore_map_sha256': map_sha, 'mapped_payloads_rehashed': count,
        'public_events': public.get('event_count'), 'native_terminal_scopes': native.get('terminal_scopes'),
        'native_acquired_scopes': native.get('acquired_scopes'), 'native_acquisition_complete': native.get('acquisition_complete'),
        'public_occurrence_windows': len(occurrence['records']),
        'source_domain_evaluation': 'unsupported', 'source_responsibility_evaluation': 'unsupported',
        'current_source_delivery_verified': False, 'cleanup_authorized': False,
        'meter_terminal_and_postcleanup_control_supplement_pending': True,
        'common_publication_io_not_treatment_benefit': True,
        'scope': 'Same pinned archive/public/native-history/occurrence functions as frozen preservation replay. Original-key no-fallback MapSessionReader uses full map hashes at session boundaries and no-follow POSIX identity checks around every access; all mapped payloads are rehashed. No SDK, source/domain grading, truth adjudication, monetary estimate or deletion.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['plan', 'archive', 'restore-map', 'output']: parser.add_argument('--'+key, required=True, type=Path)
    for key in ['plan-sha256', 'index-sha256', 'map-sha256']: parser.add_argument('--'+key, required=True)
    args = parser.parse_args(); p = frozen_preserver(); start_unix = time.time(); start_clock = time.clock_gettime(time.CLOCK_MONOTONIC)
    plan = p.pinned({'path': str(args.plan), 'sha256': args.plan_sha256})
    result = replay(plan, args.archive, args.index_sha256, args.restore_map, args.map_sha256)
    result.update(started_at_unix=start_unix, finished_at_unix=time.time(),
        started_at_clock_gettime=start_clock, finished_at_clock_gettime=time.clock_gettime(time.CLOCK_MONOTONIC),
        shared_clock_basis='clock_gettime(CLOCK_MONOTONIC)')
    p.save(args.output, result)
    print(json.dumps({'status': result['status'], 'output': str(args.output), 'sha256': p.A.file_hash(args.output)}))


if __name__ == '__main__': main()
