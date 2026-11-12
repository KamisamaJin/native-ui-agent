"""Author-only read-only snapshot recorder. Never used by the portable verifier.

Only fixed native metadata below the supplied original root is parsed. All
outputs belong to the supplied dedicated output directory. No SDK or locks.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent


def module(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--count', type=int, default=13)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if not args.output.resolve().is_relative_to(HERE):
        raise ValueError('Author outputs must remain inside publication-native-chain')
    args.output.mkdir(parents=True, exist_ok=False)
    root = args.root.resolve(); ev = root / 'cache/business/independent-evaluation'
    code_raw = (HERE / 'native_chain.py').read_bytes()
    (args.output / 'native_chain.py').write_bytes(code_raw)
    nc = module('native_chain_author', HERE / 'native_chain.py')
    resolver_code = module('pinned_resolver_author', HERE / 'schema-code/resolver.py')
    accessed = {}

    class OriginalReadOnly:
        def read_bytes(self, original):
            original = str(nc.path(str(original)))
            # No fallback or environment patch: this adapter explicitly reads
            # originals only for a separately labeled author live-read-only run.
            raw, _identity, actual = resolver_code.read_regular(original)
            accessed[original] = actual
            return raw
        def read_json(self, original):
            return nc.strict_json(self.read_bytes(original))
        def hash(self, original):
            raw = self.read_bytes(original)
            return hashlib.sha256(raw).hexdigest()
        def directory(self, original):
            original = Path(str(nc.path(str(original))))
            fd = resolver_code.open_directory(original)
            import os
            os.close(fd)
            return original
    reader = OriginalReadOnly()
    def ref(original):
        return {'path': str(original), 'sha256': reader.hash(str(original))}
    def load(original):
        return reader.read_json(str(original))
    anchors = {k: ref(root / v) for k, v in nc.ANCHORS.items()}
    order = load(anchors['order']['path'])['episodes']
    scopes = [r['task']+'/'+r['scope']+'/'+profile for r in order for profile in r['profiles']]
    if not 0 <= args.count <= 30:
        raise ValueError('A terminal prefix length from 0 to 30 is required')
    records = {}
    for scope in scopes[:args.count]:
        task, arm, profile = scope.split('/')
        claim = ev / ('native-claims' if scope in {'T1/I/ios', 'T1/I/android'} else 'native-continuation-claims') / task / arm / (profile+'.json')
        registered = load(claim); outcome = Path(registered['record']) / 'outcome.json'
        value = load(outcome)
        closure = value.get('resources')
        if closure is None:
            # A retained terminal failure may close only through an explicit
            # positive cleanup. Do not promote it to acquired native facts.
            for suffix in ['remaining-first-execution-v3','continuation','']:
                end = ev / f'episodes/{task}/{arm}' / suffix / 'END.json'
                if end.is_file():
                    terminal = load(end)
                    closures = terminal.get('positive_resource_closure', terminal.get('positive_resource_closures', {}))
                    if terminal.get('outcomes', {}).get(profile) == ref(outcome) and profile in closures:
                        closure = closures[profile]; break
        if closure is None:
            raise ValueError('No recorded positive resource closure for '+scope)
        records[scope] = {'claim': ref(claim), 'outcome': ref(outcome), 'closure': closure}
    original_end = load(ev / 'collection-operations/END.json')
    episodes = [v['end'] for v in original_end['episodes']]
    episode_paths = {v['path'] for v in episodes}
    for scope in scopes[:args.count]:
        task, arm, profile = scope.split('/')
        suffix = 'continuation' if scope in scopes[2:13] else 'remaining-first-execution-v3'
        if scope in scopes[:2]:
            continue
        end = ev / f'episodes/{task}/{arm}/{suffix}/END.json'
        if str(end) not in episode_paths:
            episodes.append(ref(end)); episode_paths.add(str(end))
    controls = []
    for directory, names in [('collection-operations', ['ENTRY.json','START.json','END.json']),
                             ('continuation-collection', ['ENTRY.json','START.json','FAILED.json']),
                             ('continuation-collection-v3', ['ENTRY.json','START.json'])]:
        controls += [ref(ev / directory / name) for name in names]
    if args.count == 30:
        final = ev / 'continuation-collection-v3/END.json'
        if not final.is_file():final = ev / 'continuation-collection-v3/FAILED.json'
        controls.append(ref(final))
    snapshot = {'kind': 'recorded-native-chain-snapshot-v1', 'version': 1, 'original_root': str(root),
                'created_at_unix': time.time(), 'terminal_scopes': scopes[:args.count], 'pending_scopes': scopes[args.count:],
                'complete_record_namespace': args.count == 30, 'anchors': anchors, 'terminal_records': records,
                'episodes': episodes, 'collection_controls': controls,
                'scope': 'Author read-only declared closed prefix; newer live scopes are excluded, never inferred failed or complete.'}
    target = args.output / 'SNAPSHOT.json'
    target.write_text(json.dumps(snapshot, indent=2, sort_keys=True)+'\n')
    snap_ref = {'path': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    result = nc.verify_chain(reader, str(root), snap_ref)
    record = {'kind': 'author-live-read-only-prefix-application', 'result': result,
              'snapshot': snap_ref, 'code_sha256': hashlib.sha256(code_raw).hexdigest(),
              'source_unchanged_during_author_run': (HERE/'native_chain.py').read_bytes() == code_raw,
              'files_read': accessed, 'sdk_executed': False, 'judgments_or_mapping_parsed': False,
              'originals_modified': False, 'scope': 'Not an archive/virtual-restore acceptance. Active collector is untouched.'}
    (args.output / 'RESULT.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: result[k] for k in ['status','acquisition_complete','error','terminal_scopes','acquired_scopes'] if k in result}))


if __name__ == '__main__':
    main()
