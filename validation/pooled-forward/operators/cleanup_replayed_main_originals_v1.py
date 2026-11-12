"""Remove selected owned originals only after the actual complete replay passed.

Unselected leftovers remain for the terminal supplement. Meter directory shells,
the cache owner and the controller's small manifest/events remain until stop.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'cache/publication-archives/closed-business-main-v2/SPEC.json'
SPEC_SHA = '01d572c64bc51a8e905b0eeb57b694f4ef2f9f395ead373f3163439ed08f9e10'
MANIFEST_SHA = 'f3e33b09fc0adaa90933d616f615f03dad3effffe1bc790febb9e8ef02775515'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts
         and not any(p.is_symlink() for p in [path, *path.parents]), 'Unsafe original path')
    return path


def sha(path):
    digest = hashlib.sha256()
    with safe(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def identity(path):
    st = safe(path).lstat()
    return [st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_blocks * 512]


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--result-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    replay, output = safe(args.replay), safe(args.output)
    need(not output.exists(), 'Fresh cleanup receipt required')
    result_path = replay / 'RESULT.json'
    need(sha(result_path) == args.result_sha256, 'Actual replay result pin differs')
    result = json.loads(result_path.read_text())
    need(result.get('kind') == 'pooled-forward-publication-replay' and result.get('status') == 'verified'
         and result.get('five_case_fixed_metrics_identical') is True
         and result.get('readonly_original_key_payloads_verified') == 104062
         and result.get('cause_contexts') == result.get('alarm_contexts') == 30
         and result.get('independent_consensus_members') == 115
         and result.get('current_source_delivery_verified') is False
         and result.get('native_sdk_execution') is False,
         'Complete actual consumer replay is not verified')
    entry = json.loads((replay / 'ENTRY.json').read_text())
    need(entry['manifest_sha256'] == MANIFEST_SHA and sha(SPEC) == SPEC_SHA, 'Original main selection/manifest differs')
    proof = json.loads((replay / 'RECORDED-PROVENANCE.json').read_text())
    need(proof['status'] == 'verified' and proof['native_terminal_scopes'] == 30
         and proof['native_acquired_scopes'] == 30 and proof['public_occurrence_windows'] == 10,
         'Actual full native/public recorded replay is missing')
    cache, business = ROOT / 'cache', ROOT / 'cache/business'
    need((cache.stat().st_dev, cache.stat().st_ino) == (16777232, 26682812)
         and sha(cache / 'OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55',
         'Positive owned cache identity differs')
    keep_shell = business / 'run-cohort2'
    keep_files = {keep_shell / 'manifest.json'}
    spec = json.loads(SPEC.read_text())
    planned = []
    for row in spec['files']:
        path = Path(row['path'])
        if not path.is_relative_to(business) or path in keep_files or path.is_relative_to(keep_shell / 'events'):
            continue
        need(stat.S_ISREG(safe(path).lstat().st_mode) and path.stat().st_size == row['bytes']
             and sha(path) == row['sha256'], 'Selected original is absent or changed before cleanup')
        planned.append({'path': str(path), 'sha256': row['sha256'], 'identity': identity(path)})
    output.mkdir()
    raw = (json.dumps(planned, separators=(',', ':'), sort_keys=True) + '\n').encode()
    with (output / 'EXACT-MEMBERS.json.gz').open('xb') as f:
        with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as stream:
            stream.write(raw)
        f.flush()
        os.fsync(f.fileno())
    save(output / 'INTENT.json', {'version': 1, 'kind': 'verified-main-selected-original-cleanup-intent',
        'at_unix': time.time(), 'source_sha256': sha(Path(__file__)), 'spec_sha256': SPEC_SHA,
        'actual_consumer_result': {'path': str(result_path), 'sha256': args.result_sha256},
        'exact_members_sha256': sha(output / 'EXACT-MEMBERS.json.gz'), 'selected_files': len(planned),
        'retained_meter_shell': str(keep_shell), 'unselected_files_removed': 0,
        'scope': 'Only byte-selected main archive originals beneath positive owned cache/business, after complete actual readonly replay. Cold transports, live meter streams, metadata shells, all unselected originals and project source remain.'})
    parents = {}
    for row in planned:
        parent = Path(row['path']).parent
        parents.setdefault(parent, identity(parent))
    removed = 0
    try:
        for parent, original in parents.items():
            need(identity(parent)[:5] == original[:5], 'Selected original directory changed')
            if not parent.stat().st_mode & stat.S_IWUSR:
                parent.chmod(stat.S_IMODE(parent.stat().st_mode) | 0o700)
        for row in planned:
            path = Path(row['path'])
            need(identity(path) == row['identity'] and sha(path) == row['sha256'], 'Original changed before exact unlink')
            path.unlink()
            removed += 1
        # Leave empty directories in place until the final meter supplement;
        # this keeps every active filesystem anchor and resource owner inode.
        need(keep_shell.is_dir() and (keep_shell / 'manifest.json').is_file(), 'Active meter anchor lost')
        save(output / 'END.json', {'version': 1, 'status': 'verified', 'at_unix': time.time(),
            'removed_selected_regular_files': removed, 'retained_unselected_files': True,
            'allocated_file_bytes_of_removed_names': sum(row['identity'][9] for row in planned),
            'original_cold_data_or_project_source_modified': False,
            'scope': 'All removed original bytes remain in the independently verified main cold transport. No exact physical-reclaim claim; only original selected names were unlinked. Directory shells and unselected leftovers require terminal preservation/cleanup.'})
        print(json.dumps({'status': 'verified', 'removed_selected_files': removed}))
    except BaseException as error:
        save(output / 'FAILED.json', {'status': 'failed', 'at_unix': time.time(), 'removed_files': removed,
                                     'type': type(error).__name__, 'message': str(error), 'partial_cleanup_retained': True})
        raise


if __name__ == '__main__':
    main()
