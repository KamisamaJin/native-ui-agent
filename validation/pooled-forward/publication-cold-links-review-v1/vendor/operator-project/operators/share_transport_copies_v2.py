"""Share byte-identical derived archive blobs; retain every name and payload.

Only a positively declared cache/publication-archives directory is writable.
This is transport storage, not logical dataset deduplication or evidence cleanup.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
COLD_PATH = ROOT / 'publication-transport-review/revision-v2/publication-tools/cold_storage/cold.py'
COLD_SHA = 'b5f8ad775e68312928b1d3cc9e2c5807edb47083a33929dd4f86611d459d0991'
LINK_PATH = ROOT / 'publication-transport-review/revision-v3/publication-tools/cold_storage/cold.py'
LINK_SHA = '1df42e542466ff45db9fbc00c950be13f1bac2e1a1eb9ebb24e854068f0e8fda'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    return {'path': str(path), 'sha256': sha(path)}


def identity(path):
    value = path.lstat()
    return {'device': value.st_dev, 'inode': value.st_ino, 'bytes': value.st_size,
            'mode': stat.S_IMODE(value.st_mode), 'mtime_ns': value.st_mtime_ns,
            'nlink': value.st_nlink, 'allocated_bytes': value.st_blocks * 512}


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def allocated_union(folders):
    values = {}
    for folder in folders:
        for path in folder.iterdir():
            need(stat.S_ISREG(path.lstat().st_mode), 'Only regular derived transport files allowed')
            st = path.stat()
            values[(st.st_dev, st.st_ino)] = st.st_blocks * 512
    return sum(values.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['archive', 'cold', 'owner-authority', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--transport-sha256', required=True)
    parser.add_argument('--owner-authority-sha256', required=True)
    args = parser.parse_args()
    need(sha(COLD_PATH) == COLD_SHA, 'Frozen transport code differs')
    spec = importlib.util.spec_from_file_location('share_original_cold', COLD_PATH)
    cold = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cold)
    need(sha(LINK_PATH) == LINK_SHA, 'Reviewed readonly link primitive differs')
    link_spec = importlib.util.spec_from_file_location('share_readonly_link', LINK_PATH)
    links = importlib.util.module_from_spec(link_spec)
    link_spec.loader.exec_module(links)
    archive, transport = cold.physical(str(args.archive)), cold.physical(str(args.cold))
    output = cold.physical(str(args.output), fresh=True)
    cold.disjoint(archive, transport)
    cold.disjoint(archive, output)
    cold.disjoint(transport, output)
    cold.physical(str(args.owner_authority))
    need(sha(args.owner_authority) == args.owner_authority_sha256, 'External owner authority differs')
    authority = cold.strict_json(args.owner_authority.read_bytes())
    cache = cold.physical(authority['path'])
    cold.physical(str(cache / 'OWNER.json'))
    need((cache.stat().st_dev, cache.stat().st_ino) == (authority['device'], authority['inode'])
         and sha(cache / 'OWNER.json') == authority['marker_sha256'], 'Positive owned cache identity differs')
    need(archive.is_relative_to(cache / 'publication-archives'), 'Only derived archive scratch may share storage')
    need(sha(transport / 'TRANSPORT.json') == args.transport_sha256, 'External transport pin differs')
    seal = cold.strict_json((transport / 'TRANSPORT.json').read_bytes())
    need(set(seal) == {'version', 'kind', 'index_sha256', 'archive_code_sha256', 'files', 'scope'}
         and seal.get('kind') == 'lossless-frozen-archive-transport' and type(seal.get('version')) is int
         and seal.get('version') == 1
         and seal.get('archive_code_sha256') == cold.ARCHIVE_SHA, 'Wrong immutable transport')
    module = cold.archive_module()
    verified = module.verify(archive, seal['index_sha256'])
    names = cold.source_files(archive)
    need(set(names) == set(seal['files']), 'Derived archive membership differs from transport')
    expected_stored = {'TRANSPORT.json'}
    planned = []
    for name in names:
        row = seal['files'][name]
        need(set(row) == {'stored', 'sha256', 'bytes', 'stored_sha256', 'stored_bytes'}, 'Unexpected transport member metadata')
        expected_name = name + '.gz' if name in {'INDEX.json', 'SPEC.json'} else name
        need(row['stored'] == expected_name, 'Unexpected stored filename')
        expected_stored.add(expected_name)
        source, target = cold.physical(str(transport / expected_name)), cold.physical(str(archive / name))
        need(stat.S_ISREG(source.lstat().st_mode) and stat.S_ISREG(target.lstat().st_mode), 'Regular transport members required')
        need(source.stat().st_size == row['stored_bytes'] and sha(source) == row['stored_sha256']
             and target.stat().st_size == row['bytes'] and sha(target) == row['sha256'], 'Derived copy bytes differ')
        if name in {'INDEX.json', 'SPEC.json'}:
            continue
        need(name == 'SEAL.json' or re.fullmatch(r'shard-[0-9]{5}\.tar\.gz', name), 'Only raw immutable transport blobs may share')
        need(not stat.S_IMODE(source.stat().st_mode) & 0o7222, 'Cold source must already be readonly ordinary data')
        need(row['sha256'] == row['stored_sha256'] and row['bytes'] == row['stored_bytes'], 'Raw transport copy differs')
        planned.append({'name': name, 'source': str(source), 'target': str(target),
                        'sha256': row['sha256'], 'source_before': identity(source), 'target_before': identity(target)})
    need({p.name for p in transport.iterdir()} == expected_stored, 'Unexpected cold namespace member')
    before_allocated = allocated_union([archive, transport])
    output.mkdir()
    stage = archive.parent / ('transport-share-' + uuid.uuid4().hex)
    stage.mkdir(mode=0o700)
    stage_id = (stage.stat().st_dev, stage.stat().st_ino)
    archive_id = (archive.stat().st_dev, archive.stat().st_ino)
    directories = {p: links.transport_identity(p.lstat())
                   for p in {archive, transport, cache, stage, *archive.parents,
                             *transport.parents, *stage.parents}}

    def stable_blob(path, expected):
        cold.physical(str(path))
        actual = identity(path)
        need(stat.S_ISREG(path.lstat().st_mode) and not actual['mode'] & 0o7222
             and all(actual[key] == expected[key] for key in ['device', 'inode', 'bytes', 'mode', 'mtime_ns']),
             'Readonly transport blob identity/mode changed')
        return actual

    def stable_directories():
        need(all(links.transport_identity(p.lstat()) == value for p, value in directories.items()),
             'Owned transport directory namespace changed')
    save(output / 'INTENT.json', {'version': 1, 'kind': 'owned-derived-transport-sharing-intent',
        'at_unix': time.time(), 'source': ref(Path(__file__)), 'authority': ref(args.owner_authority),
        'transport': ref(transport / 'TRANSPORT.json'), 'archive_verification': verified,
        'archive_root_identity': archive_id, 'stage': str(stage), 'stage_identity': stage_id,
        'planned': planned, 'all_original_dataset_paths_untouched': True})
    try:
        for row in planned:
            source, target = Path(row['source']), Path(row['target'])
            need((archive.stat().st_dev, archive.stat().st_ino) == archive_id, 'Derived archive directory replaced')
            need(sha(source) == sha(target) == row['sha256'], 'Transport blob changed before sharing')
            stable_directories()
            stable_blob(source, row['source_before'])
            src = source.lstat()
            if (target.stat().st_dev, target.stat().st_ino) == (src.st_dev, src.st_ino):
                continue
            temporary = stage / row['name']
            need(links.readonly_link(source, temporary), 'Readonly transport linking unavailable; no copy was replaced')
            stable_blob(source, row['source_before'])
            stable_blob(temporary, row['source_before'])
            linked = temporary.lstat()
            need(stat.S_ISREG(linked.st_mode) and (linked.st_dev, linked.st_ino) == (src.st_dev, src.st_ino)
                 and sha(temporary) == row['sha256'], 'Transport link identity differs')
            os.replace(temporary, target)
            stable_blob(source, row['source_before'])
            stable_blob(target, row['source_before'])
            stable_directories()
            need((target.stat().st_dev, target.stat().st_ino) == (source.stat().st_dev, source.stat().st_ino)
                 and sha(target) == row['sha256'], 'Derived alias differs after atomic replacement')
        need((stage.stat().st_dev, stage.stat().st_ino) == stage_id and not list(stage.iterdir()), 'Owned staging directory changed')
        stage.rmdir()
        final = module.verify(archive, seal['index_sha256'])
        # Stage is intentionally removed, so audit the remaining namespace and
        # each immutable alias again after the full frozen byte verification.
        directories.pop(stage)
        stable_directories()
        for row in planned:
            stable_blob(Path(row['source']), row['source_before'])
            stable_blob(Path(row['target']), row['source_before'])
        need(final == verified and cold.source_files(archive) == names
             and sha(transport / 'TRANSPORT.json') == args.transport_sha256, 'Logical archive or transport changed')
        after_allocated = allocated_union([archive, transport])
        save(output / 'END.json', {'version': 1, 'kind': 'owned-derived-transport-sharing-complete',
            'status': 'verified', 'at_unix': time.time(), 'archive': str(archive), 'cold': str(transport),
            'raw_alias_count': len(planned), 'before_union_allocated_file_bytes': before_allocated,
            'after_union_allocated_file_bytes': after_allocated,
            'namespace_allocation_difference_bytes': before_allocated - after_allocated,
            'final_inner_verification': final, 'original_dataset_files_modified_or_deleted': 0,
            'logical_dataset_payload_deduplicated': False,
            'scope': 'All archive/cold names and bytes remain. Only derived readonly transport copies share inodes; no APFS physical-freed or product/treatment-benefit claim.'})
        print(json.dumps({'status': 'verified', 'receipt': ref(output / 'END.json'),
                          'transport_union_allocation_difference': before_allocated - after_allocated}))
    except BaseException as error:
        save(output / 'FAILED.json', {'status': 'failed', 'type': type(error).__name__,
                                     'message': str(error), 'partial_aliases_retained': True})
        raise


if __name__ == '__main__':
    main()
