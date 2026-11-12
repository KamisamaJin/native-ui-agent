#!/usr/bin/env python3
"""Gated uniform fifteen-version alarm selection; no product adjudication.

Selection/derivation is separate from immutable alarm_packet.build. Raw original
bytes and every intermediate projection remain outside judge inputs. Actual
data is inaccessible through this entry until the full cause barrier verifies.
"""
import argparse
import builtins
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import time
import traceback
import types

import material as m


def presentation_modules():
    """Execute pinned sources afresh; do not trust mutable sys.modules entries."""
    modules = {}; real_import = builtins.__import__
    def private_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in modules: return modules[name]
        return real_import(name, globals, locals, fromlist, level)
    for name in ['anonymous_projection', 'phase_barriers', 'alarm_packet']:
        path = Path(__file__).resolve().parent.parent / 'publication-alarm-review/revision-v2' / (name + '.py')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != m.PINS[name + '.py']:
            raise ValueError('Pinned presentation source differs')
        module = types.ModuleType('batch_private_' + name); module.__file__ = str(path)
        module.__dict__['__builtins__'] = dict(vars(builtins), __import__=private_import)
        exec(compile(raw, str(path), 'exec'), module.__dict__)
        modules[name] = module
    return modules


_presentation = presentation_modules()
json_text = _presentation['anonymous_projection'].json_text
strict_json = _presentation['anonymous_projection'].strict_json
verify_index = _presentation['phase_barriers'].verify_index
build = _presentation['alarm_packet'].build
MAP_SEAL_SHA = 'b7f575344dbe240ab0a2ffb041f52e5b450ccf0b77179a59633f69bc66a837c3'


def digest(raw): return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    path.chmod(0o444)


def encoded(value): return (json_text(value, sort_keys=True, indent=2) + '\n').encode()


class LiveReader:
    """Explicit no-follow original access for preparation, never restore fallback."""
    def __init__(self, root):
        p = root / 'publication-resolver/resolver.py'
        if digest(p.read_bytes()) != '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204':
            raise ValueError('Frozen Resolver source differs')
        spec = importlib.util.spec_from_file_location('alarm_prepare_live_reader', p)
        self.module = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.module)
    def read_bytes(self, original): return self.module.read_regular(original)[0]
    def read_json(self, original): return strict_json(self.read_bytes(original))
    def hash(self, original): return digest(self.read_bytes(original))
    def directory(self, original):
        p = self.module.absolute(str(original)); fd = self.module.open_directory(p); os.close(fd); return p


def ref(reader, path): return {'path': str(path), 'sha256': reader.hash(str(path))}


def pinned(reader, value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('Exact original reference required')
    raw = reader.read_bytes(value['path'])
    if digest(raw) != value['sha256']: raise ValueError('Original pinned bytes differ')
    return strict_json(raw)


def relative(value):
    p = PurePosixPath(value)
    if p.is_absolute() or str(p) != value or '..' in p.parts or '\\' in value:
        raise ValueError('Safe original relative artifact required')
    return p


class Group:
    def __init__(self, root, reader, group, task, arm, manifest, events, snapshot, native_read_pins, work):
        self.root, self.reader, self.group, self.task, self.arm = root, reader, group, task, arm
        self.manifest, self.events, self.snapshot, self.native_read_pins = manifest, events, snapshot, native_read_pins
        self.work = work / group; self.work.mkdir(parents=True, exist_ok=False)
        self.documents, self.derivations, self.description = [], [], {
            'anonymous_group': group, 'versions': [], 'episodes': [], 'documents': [],
            'scope': 'Original all-status reports and claims; status is not independent truth. Source capsules, native epochs and original image layout remain explicit.'}
        self.versions, self.aliases, self.captures, self.document_paths = {}, {}, {}, {}
        self.run = root / 'cache/business/run-cohort2'
        self.initial = group.endswith('-I')

    def original(self, path): return self.reader.read_json(str(path))

    def exact(self, original_ref, destination, info):
        name = relative(destination).as_posix(); raw = self.reader.read_bytes(original_ref['path'])
        if digest(raw) != original_ref['sha256']: raise ValueError('Original material pin differs')
        self.documents.append({'original': original_ref, 'anonymous_relative': name, 'method': 'copy'})
        self.description['documents'].append(dict(info, path=name, original_sha256=original_ref['sha256']))
        self.document_paths[original_ref['path']] = name

    def json_document(self, original_ref, destination, info, *, outcome=False, aliases=None):
        raw = self.reader.read_bytes(original_ref['path'])
        if digest(raw) != original_ref['sha256']: raise ValueError('Original report pin differs')
        original = strict_json(raw); value = m.outcome_view(original) if outcome else original
        if not isinstance(value, dict): raise ValueError('Recorded report object required')
        neutral, proof = m.neutralize(value, aliases)
        path = self.work / ('derived-%05d.json' % len(self.derivations))
        write(path, encoded(neutral))
        self.derivations.append({'original': original_ref, 'derived': ref(self.reader, path),
            'anonymous_relative': destination, 'projection': proof,
            'outer_fact_selection': {'kind': 'fixed-operation-outcome-fields',
                'retained': list(value), 'omitted': [k for k in original if k not in value]} if outcome else None})
        self.exact(ref(self.reader, path), destination, dict(info, raw_original_sha256=original_ref['sha256']))

    def sources(self, required, workspace_roots, candidates):
        content = required['content_sha256']
        if digest(json_text(required['files'], sort_keys=True).encode()) != content:
            raise ValueError('Original controller full-capsule source identity differs')
        if content not in self.versions:
            name = 'v%d' % len(self.versions); aliases = {}; missing = []
            for i, (rel, expected) in enumerate(sorted(required['files'].items())):
                relative(rel); match = candidates.get((rel, expected['sha256'], expected['bytes']))
                if match is None:
                    missing.append({'relative': rel, **expected}); continue
                destination = 'sources/' + name + '/' + rel
                self.exact(ref(self.reader, match), destination,
                           {'kind': 'source', 'source_version': content, 'relative': rel})
                if self.reader.hash(str(match)) != expected['sha256']:
                    raise ValueError('Supporting original source member changed')
                root_index, tail = rel.split('/', 1)
                aliases[str(Path(workspace_roots[int(root_index)]) / tail)] = destination
            self.versions[content] = name; self.aliases[content] = aliases
            self.description['versions'].append({'id': name, 'controller_content_sha256': content,
                 'source_member_count': len(required['files']), 'missing_original_members': missing,
                 'source_scope': 'Original full-controller capsule; selected-platform native hashes have a separate domain. A missing intermediate member is unavailable, never replaced by current source.'})
        # Identical initial bytes occur in both public roots. Their original
        # citation paths still need separate exact aliases to the same bytes.
        for rel, expected in required['files'].items():
            if (rel, expected['sha256'], expected['bytes']) in candidates:
                root_index, tail = rel.split('/', 1)
                self.aliases[content][str(Path(workspace_roots[int(root_index)]) / tail)] = (
                    'sources/' + self.versions[content] + '/' + rel)
        return content

    def operation(self, outcome_ref, episode, source, config_ref, candidates, visibility):
        outcome = pinned(self.reader, outcome_ref); config = pinned(self.reader, config_ref)
        version = self.sources(source, config['source_roots'], candidates)
        profile = outcome['profile']; base = 'episodes/' + episode + '/' + profile
        info = {'episode': episode, 'platform': profile, 'source_version': version, 'visibility': visibility}
        self.json_document(outcome_ref, base + '/outcome.json', dict(info, kind='operation-result'), outcome=True, aliases=self.aliases[version])
        entry = dict(info, outcome=base + '/outcome.json', action=outcome.get('action'), capture=None)
        inventory_ref = outcome.get('inventory')
        if inventory_ref:
            inventory = pinned(self.reader, inventory_ref); service = Path(outcome['service_output'])
            for original, row in sorted(inventory.items()):
                p = Path(original)
                if not p.is_relative_to(service): raise ValueError('Original service inventory escapes its namespace')
                expected = row if isinstance(row, str) else row['sha256']
                if p.name in m.REPORT_NAMES:
                    destination = base + '/reports/' + p.relative_to(service).as_posix()
                    self.json_document({'path': original, 'sha256': expected}, destination,
                                       dict(info, kind='original-service-report'), aliases=self.aliases[version])
        capture_ref = outcome.get('capture')
        if capture_ref:
            receipt = pinned(self.reader, capture_ref); key = capture_ref['sha256']
            if key not in self.captures:
                prefix = 'captures/n%d/native' % len(self.captures)
                native = Path(capture_ref['path']).parent / 'native'; obs = native / 'observation.json'
                if receipt.get('observation_sha256'):
                    observation_ref = {'path': str(obs), 'sha256': receipt['observation_sha256']}
                    self.json_document(observation_ref, prefix + '/observation.json',
                                       dict(info, kind='original-native-observation'), aliases=self.aliases[version])
                    for rel, expected in receipt.get('image_hashes', {}).items():
                        safe = relative(rel)
                        self.exact({'path': str(native / safe), 'sha256': expected}, prefix + '/' + rel,
                                   dict(info, kind='original-native-image'))
                    self.captures[key] = {'observation': prefix + '/observation.json',
                         'native_source_sha256': receipt.get('source_sha256'),
                         'native_source_model_sha256': receipt.get('source_model_sha256'),
                         'first_supplied_full_source_version': version,
                         'original_capture_sha256': key}
                else:
                    self.captures[key] = {'observation': None, 'availability': 'Original operation has no pinned native observation', 'original_capture_sha256': key}
            entry['capture'] = self.captures[key]
        else: entry['availability'] = 'Original operation retained no capture reference; no native pass is inferred.'
        self.description['episodes'].append(entry)

    def prepare(self):
        own = 'A' if self.initial else self.arm
        source_folders = [self.run / f'arms/{self.task}/{own}/initial', self.run / f'arms/{self.task}/{own}/final-source']
        candidates, sources = {}, []
        for folder in source_folders:
            source_path = folder / 'source.json'
            if self.native_read_pins.get(str(source_path)) != self.reader.hash(str(source_path)):
                raise ValueError('Supporting source capsule is not in the independently verified chain')
            source = self.original(source_path); sources.append(source)
            for rel, row in source['files'].items():
                p = folder / 'files' / relative(rel)
                if self.reader.hash(str(p)) != row['sha256'] or len(self.reader.read_bytes(str(p))) != row['bytes']:
                    raise ValueError('Original own source capsule member differs')
                candidates[(rel, row['sha256'], row['bytes'])] = p
        requests = [e for e in self.events if e['kind'] == 'request_enqueued' and e.get('task') == self.task
                    and (e.get('action') == 'diagnostic' if self.initial else e.get('arm') == own)]
        if self.initial:
            first = {a: next(e for e in requests if e['arm'] == a) for a in ['A', 'B']}
            requests = sorted(first.values(), key=lambda e: e['sequence'])
        else:
            sealed = next(e for e in self.events if e['kind'] == 'self_sealed' and e.get('task') == self.task and e.get('arm') == own)
            if any(e['sequence'] > sealed['sequence'] for e in requests): raise ValueError('Public request occurred after original self-seal')
        for i, event in enumerate(requests):
            request_path = self.run / 'requests' / event['request_id']; request = event
            terminal = next(e for e in self.events if e['kind'] == 'request_finished'
                            and e.get('request_id') == event['request_id'])
            result = pinned(self.reader, {'path': terminal['result_path'], 'sha256': terminal['result_sha256']})
            label = 'public-%03d' % i
            for platform in request['profiles']:
                path = request_path / platform / 'outcome.json'
                row = next(item for item in result['outcomes'] if item['profile'] == platform)
                if json_text(row, sort_keys=True) != json_text(self.original(path), sort_keys=True):
                    raise ValueError('Public outcome differs from its original event-pinned result')
                self.operation(ref(self.reader, path), label, event['source'], event['active_configs'][platform], candidates,
                               'common-initial-public' if self.initial else 'worker_public')
            if request.get('submission'):
                version = event['source']['content_sha256']
                self.json_document({'path': request['submission']['path'], 'sha256': request['submission']['sha256']},
                    'episodes/' + label + '/original-submission.json',
                    {'kind': 'original-worker-submission', 'episode': label, 'source_version': version,
                     'visibility': 'common-initial-public' if self.initial else 'worker_public'}, aliases=self.aliases[version])
        scope = 'I' if self.initial else own; independent = self.root / 'cache/business/independent-evaluation'
        for platform in ['ios', 'android']:
            key = self.task + '/' + scope + '/' + platform
            effective = self.snapshot['terminal_records'][key]
            effective_outcome = pinned(self.reader, effective['outcome'])
            source = pinned(self.reader, effective_outcome['source_capsule'])
            original_claim = independent / 'native-claims' / self.task / scope / (platform + '.json')
            claim = self.original(original_claim); original_outcome = Path(claim['record']) / 'outcome.json'
            refs = [ref(self.reader, original_outcome)]
            entry_permit_ref = next((v for v in self.snapshot['anchors'].values()
                if Path(v['path']).name == 'UNCLAIMED-ENTRY-v3-ADMISSION.json'), None)
            if entry_permit_ref:
                entry_permit = pinned(self.reader, entry_permit_ref)['entry_resume']
                if entry_permit['scope'] == key:
                    refs.append(entry_permit['failed_record_files']['outcome.json'])
            if refs[0] != effective['outcome']: refs.append(effective['outcome'])
            for i, item in enumerate(refs):
                if self.native_read_pins.get(item['path']) != item['sha256']:
                    raise ValueError('Private selected outcome is not in independently verified native chain')
                value = pinned(self.reader, item)
                self.operation(item, 'private-attempt-%d' % i, source, value['config'], candidates,
                               'independent_private_after_seal')
        if not self.initial:
            self.json_document({'path': sealed['claim_path'], 'sha256': sealed['claim_sha256']},
                'worker/self-claim.json', {'kind': 'original-worker-self-claim', 'visibility': 'worker_public',
                'source_version': sources[-1]['content_sha256']}, aliases=self.aliases[sources[-1]['content_sha256']])


def prepare(root, reader, cause_ref, snapshot_ref, native_result_ref, output, work):
    # This precedes mapping, manifest, event, report, source and image reads.
    verified = verify_index(reader, cause_ref, 'cause')
    snapshot = pinned(reader, snapshot_ref); result = pinned(reader, native_result_ref)
    if (result.get('snapshot') != snapshot_ref or result.get('result', {}).get('status') != 'verified'
            or result['result'].get('acquired_scopes') != 30 or snapshot.get('original_root') != str(root)):
        raise ValueError('Externally pinned all30 native acquisition proof required')
    mapping_seal = pinned(reader, {'path': str(root / 'operators/cohort2/coordination/anonymous-map/SEAL.json'),
                                  'sha256': MAP_SEAL_SHA})
    mapping_path = root / 'operators/cohort2/coordination/anonymous-map/MAPPING.json'
    mapping = pinned(reader, {'path': str(mapping_path), 'sha256': mapping_seal['files']['MAPPING.json']})['mapping']
    if set(mapping) != {'Case0%d' % i for i in range(1, 6)}:
        raise ValueError('Exactly the five original anonymous cases required')
    manifest = pinned(reader, snapshot['anchors']['manifest'])
    run = root / 'cache/business/run-cohort2'
    events = []
    for path in sorted(reader.directory(str(run / 'events')).glob('*.json')):
        if result['files_read'].get(str(path)) != reader.hash(str(path)):
            raise ValueError('Original public event differs from independently verified acquisition chain')
        events.append(reader.read_json(str(path)))
    output.mkdir(parents=True, exist_ok=False); work.mkdir(parents=True, exist_ok=False)
    all_specs = []
    for version in ['I', 'X', 'Y']:
        for case in sorted(mapping):
            group = case + '-' + version; row = mapping[case]
            collector = Group(root, reader, group, row['task'], row[version], manifest, events, snapshot, result['files_read'], work)
            collector.prepare()
            spec = {'version': 1, 'kind': 'explicit-anonymous-alarm-material-spec', 'anonymous_group': group,
                    'first_cause_barrier': cause_ref, 'documents': collector.documents,
                    'anonymous_description': collector.description,
                    'instructions': ref(reader, root / 'business-quality-tools/ALARM-INSTRUCTIONS-v1.md'),
                    'grade_template': ref(reader, root / 'business-quality-tools/ALARM-GRADE-TEMPLATE-v1.json')}
            folder = output / group; folder.mkdir()
            write(folder / 'SPEC.json', encoded(spec)); write(folder / 'DERIVATIONS.json', encoded(collector.derivations))
            all_specs.append({'group': group, 'spec': ref(reader, folder / 'SPEC.json'),
                              'derivations': ref(reader, folder / 'DERIVATIONS.json')})
    value = {'version': 1, 'kind': 'all15-uniform-original-alarm-selection-seal', 'at_unix': time.time(),
             'first_cause_barrier': cause_ref, 'groups': all_specs, 'closed_cause_contexts': verified['distinct_contexts'],
             'mapping_revealed_to_judges_or_model': False, 'quality_adjudicated': False}
    write(output / 'ALL-SPECS-SEAL.json', encoded(value))
    return ref(reader, output / 'ALL-SPECS-SEAL.json')


def main():
    p = argparse.ArgumentParser(); p.add_argument('command', choices=['prepare', 'build'])
    p.add_argument('--root', type=Path, required=True); p.add_argument('--id', required=True)
    for name in ['cause-index', 'native-snapshot', 'native-result', 'selection-seal']:
        p.add_argument('--' + name); p.add_argument('--' + name + '-sha256')
    a = p.parse_args(); root = a.root.resolve()
    if not a.id.isascii() or not a.id.replace('-', '').isalnum(): raise ValueError('Simple unique preparation ID required')
    reader = LiveReader(root); output = root / 'operators/cohort2/coordination/alarm-material-selections' / a.id
    try:
        if a.command == 'prepare':
            refs = [{ 'path': getattr(a, name), 'sha256': getattr(a, name + '_sha256')}
                    for name in ['cause_index', 'native_snapshot', 'native_result']]
            answer = prepare(root, reader, *refs, output,
                root / 'cache/business/blind-quality/alarm-intermediates' / a.id)
            print(json.dumps({'selection_seal': answer, 'groups': 15, 'quality_adjudicated': False}))
        else:
            selected = pinned(reader, {'path': a.selection_seal, 'sha256': a.selection_seal_sha256})
            expected = {'Case0%d-%s' % (i, v) for i in range(1, 6) for v in ['I', 'X', 'Y']}
            if (selected['kind'] != 'all15-uniform-original-alarm-selection-seal'
                    or len(selected['groups']) != 15 or {row['group'] for row in selected['groups']} != expected):
                raise ValueError('Complete all15 selection seal required')
            verify_index(reader, selected['first_cause_barrier'], 'cause')
            summaries = []
            for row in selected['groups']:
                spec = pinned(reader, row['spec']); pinned(reader, row['derivations'])
                group = row['group']
                result = build(reader, spec, root / 'cache/business/blind-quality/alarm-packets' / a.id / group,
                               output / 'packaging' / group)
                summaries.append({'group': group, **result})
            write(output / 'ALL-PACKETS-SEAL.json', encoded({'version': 1, 'groups': summaries,
                  'selection_seal': {'path': a.selection_seal, 'sha256': a.selection_seal_sha256},
                  'scope': 'Every original selection sealed before packaging/dispatch; no quality or reveal.'}))
            print(json.dumps({'groups': len(summaries), 'packets_seal': ref(reader, output / 'ALL-PACKETS-SEAL.json')}))
    except BaseException as error:
        output.mkdir(parents=True, exist_ok=True)
        failure = output / ('FAILED-' + str(time.time_ns()) + '.json')
        write(failure, encoded({'version': 1, 'error': {'type': type(error).__name__, 'message': str(error)},
              'traceback': traceback.format_exc(), 'quality_adjudicated': False, 'phase2_dispatched': False}))
        raise


if __name__ == '__main__': main()
