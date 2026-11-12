"""Close this study's exact owned cache and retained closed control fixtures.

Every non-regenerable regular byte must be covered by an original-key cold
inventory. Links/special files require terminal structural metadata. This never
deletes project code, cold transports, Git, shared SDKs or external link targets.
"""
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'operators/terminal-scratch-cleanup-v1'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    h = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def ident(st):
    return [st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid,
            st.st_nlink, st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_blocks * 512]


def save(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')


def main():
    need(not OUT.exists(), 'Fresh terminal cleanup output required')
    terminal = ROOT / 'publications/closed-terminal-v1/TRANSPORT.json'
    need(sha(terminal) == '5e7f99c0acf89b4b6eeb75bbc2731ac9262b1fe5ef907152432b642aadbca031', 'Terminal transport pin differs')
    proof = ROOT / 'operators/terminal-preservation-v1/COLD-VERIFICATION.json'
    need(json.loads(proof.read_text())['status'] == 'verified', 'Complete terminal decode/inner verification required')
    cache = ROOT / 'cache'
    need((cache.stat().st_dev, cache.stat().st_ino) == (16777232, 26682812)
         and sha(cache / 'OWNER.json') == 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55', 'Owned study cache differs')
    closed = json.loads((ROOT / 'operators/final-meter-closure-v1/CLOSED.json').read_text())
    need(closed['actual_original_meter_process_exit_codes'] == {'whole': 0, 'arm': 0}, 'Original meters not joined')
    covered, derived, cold_refs = {}, set(), []
    for cold in sorted((ROOT / 'publications').iterdir()):
        if not cold.is_dir():
            continue
        transport_path = cold / 'TRANSPORT.json'
        transport = json.loads(transport_path.read_text())
        cold_refs.append({'path': str(transport_path), 'sha256': sha(transport_path)})
        for name, row in transport['files'].items():
            p = cold / row['stored']
            need(p.stat().st_size == row['stored_bytes'] and sha(p) == row['stored_sha256'], 'Retained cold bytes differ')
            cold_refs.append({'path': str(p), 'sha256': row['stored_sha256']})
            derived.add((row['sha256'], row['bytes']))
        meta = transport['files']['SPEC.json']
        raw = gzip.decompress((cold / meta['stored']).read_bytes())
        need(hashlib.sha256(raw).hexdigest() == meta['sha256'], 'Original spec bytes differ')
        for row in json.loads(raw)['files']:
            covered.setdefault(row['path'], set()).add((row['sha256'], row['bytes'], row['mode']))
    structures = {r['path']: r for r in json.loads((ROOT / 'operators/terminal-preservation-v1/STRUCTURE.json').read_text())['entries']}
    targets = [cache]
    # The whole study is closed. These are its Git-ignored generated control
    # namespaces, not discovery of user/application directories elsewhere.
    for directory, dirs, files in os.walk(ROOT, followlinks=False):
        parent = Path(directory)
        for name in list(dirs):
            p = parent / name
            if p == cache or p == ROOT / 'publications' or p.is_symlink():
                dirs.remove(name)
                continue
            generated = name in {'HOST', 'fixtures', 'results', 'ROOT-HOST-REEXECUTION'} or name.startswith('HOST-')
            generated |= p.is_relative_to(ROOT / 'qualification') and name == 'work'
            generated |= p == ROOT / 'operators/alarm-v2-admission-v1/root-controls/cases'
            if generated:
                need(not p.is_symlink() and p.stat().st_uid == os.geteuid(), 'Unowned generated fixture boundary')
                targets.append(p)
                dirs.remove(name)
    raw_meter = ROOT / 'operators/cohort2/business-arm-disk.jsonl'
    targets.append(raw_meter)
    rows, directories = [], {}
    for target in targets:
        entries = [target]
        while entries:
            p = entries.pop()
            need(p.is_relative_to(ROOT) and not p.is_relative_to(ROOT / 'publications')
                 and not any(x.is_symlink() for x in p.parents), 'Cleanup escaped its explicit study namespace')
            st = p.lstat()
            need(st.st_uid == os.geteuid() and st.st_dev == 16777232, 'Unowned cleanup member')
            if stat.S_ISDIR(st.st_mode):
                directories[str(p)] = ident(st)
                entries.extend(Path(e.path) for e in os.scandir(p))
                continue
            if p == cache / 'OWNER.json':
                continue
            row = {'path': str(p), 'identity': ident(st)}
            if stat.S_ISREG(st.st_mode):
                digest = sha(p)
                ordinary = (digest, st.st_size, format(stat.S_IMODE(st.st_mode), '04o')) in covered.get(str(p), set())
                duplicate = p.is_relative_to(cache / 'publication-archives') and (digest, st.st_size) in derived
                regenerated = '__pycache__' in p.parts or '.git' in p.parts or p.is_relative_to(cache / 'design-schema-python') or p.is_relative_to(cache / 'skill-validation-python')
                need(ordinary or duplicate or regenerated, 'Unpreserved original refuses cleanup: ' + str(p))
                row.update(kind='regular', sha256=digest, original_key_covered=ordinary, transport_duplicate=duplicate, regenerated=regenerated)
            elif stat.S_ISLNK(st.st_mode):
                need(str(p) in structures and structures[str(p)]['kind'] == 'symlink'
                     and os.readlink(p) == structures[str(p)]['target'], 'Unpreserved structural link')
                row.update(kind='symlink', target=os.readlink(p))
            else:
                need(str(p) in structures and structures[str(p)]['kind'] == 'special'
                     and stat.S_IFMT(st.st_mode) == structures[str(p)]['file_type'], 'Unpreserved special fixture')
                row.update(kind='special')
            need(ident(p.lstat()) == row['identity'], 'Scratch member changed during inventory')
            rows.append(row)
    OUT.mkdir()
    file_parents = {str(Path(r['path']).parent): ident(Path(r['path']).parent.lstat()) for r in rows}
    exact = {'members': rows, 'directories': directories, 'file_parents': file_parents}
    with (OUT / 'EXACT-MEMBERS.json.gz').open('xb') as f:
        with gzip.GzipFile(fileobj=f, filename='', mode='wb', mtime=0) as z:
            z.write((json.dumps(exact, sort_keys=True, separators=(',', ':')) + '\n').encode())
    save('INTENT.json', {'at_unix': time.time(), 'source_sha256': sha(Path(__file__)),
        'terminal_verification_sha256': sha(proof), 'members_sha256': sha(OUT / 'EXACT-MEMBERS.json.gz'),
        'exact_generated_boundaries': [str(p) for p in targets], 'files_or_specials': len(rows),
        'directories': len(directories), 'retained_cold_inputs': cold_refs,
        'scope': 'Only closed generated study cache/control namespaces and the archived closed full meter. Every non-regenerable regular byte has original-key cold coverage or exact derived-transport coverage. Directory chmod only; inert links never followed. Main repository Git, frozen tool source, shared SDK and user resources excluded.'})
    removed = 0
    aliases = collections.Counter()
    try:
        for path, old in sorted(directories.items(), key=lambda item: item[0].count('/')):
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                now = ident(os.fstat(fd))
                need(now[:5] == old[:5], 'Inventoried directory replaced')
                os.fchmod(fd, stat.S_IMODE(now[2]) | 0o700)
            finally:
                os.close(fd)
        for row in rows:
            p = Path(row['path'])
            old, now = row['identity'], ident(p.lstat())
            inode = tuple(old[:2])
            need(now[:5] == old[:5] and now[6:8] == old[6:8] and now[9] == old[9]
                 and now[5] == old[5] - aliases[inode]
                 and (aliases[inode] > 0 or now[8] == old[8]), 'Unexplained scratch member replacement/change')
            if row['kind'] == 'regular':
                need(sha(p) == row['sha256'], 'Scratch bytes changed before unlink')
            elif row['kind'] == 'symlink':
                need(os.readlink(p) == row['target'], 'Structural link changed')
            parent_fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                need(ident(os.fstat(parent_fd))[:2] == file_parents[str(p.parent)][:2], 'Cleanup parent replaced')
                os.unlink(p.name, dir_fd=parent_fd)
            finally:
                os.close(parent_fd)
            aliases[inode] += 1
            removed += 1
        for path, old in sorted(directories.items(), key=lambda item: -item[0].count('/')):
            p = Path(path)
            if p == cache:
                continue
            need(ident(p.lstat())[:2] == old[:2], 'Empty shell replaced')
            p.rmdir()
        for reference in cold_refs:
            need(sha(Path(reference['path'])) == reference['sha256'], 'Protected cold bytes changed')
        need(set(p.name for p in cache.iterdir()) == {'OWNER.json'}, 'Unexpected cache residue')
        save('END.json', {'status': 'verified', 'at_unix': time.time(), 'removed_members': removed,
            'removed_regular_files': sum(r['kind'] == 'regular' for r in rows), 'removed_directories': len(directories) - 1,
            'removed_namespace_allocated_file_bytes': sum(r['identity'][9] for r in rows if r['kind'] == 'regular'),
            'file_chmod_calls': 0, 'physical_reclaim_measured': False, 'original_cache_marker_retained': True,
            'retained_cold_members_reverified': len(cold_refs), 'current_product_graded': False})
        print(json.dumps({'status': 'verified', 'removed_members': removed, 'removed_directories': len(directories) - 1}))
    except BaseException as error:
        save('FAILED.json', {'status': 'failed', 'removed_members': removed, 'type': type(error).__name__,
                             'message': str(error), 'partial_outputs_retained': True})
        raise


if __name__ == '__main__':
    main()
