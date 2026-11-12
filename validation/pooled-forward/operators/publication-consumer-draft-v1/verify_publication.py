#!/usr/bin/env python3
"""Decode original bytes and replay recorded provenance/metrics, without SDKs.

PUBLICATION.json is written only after the independent judgments, consensus,
reveal and final live bindings close. No live original-path fallback or portable
source-responsibility/source-domain grading is provided by this verifier.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
CODE_KEYS = {'cold', 'archive', 'preserve', 'session', 'session_replay', 'phase', 'projection', 'metric'}
INPUT_KEYS = {'cause_index', 'alarm_index', 'correspondence_seal', 'mapping_reveal',
              'coverage_registry', 'metric_inputs', 'metric_results'}
COVERAGE_SHA = 'bf0b28d507c9fa1f638e0233980ddaf4d4293745e0ac59e63205ef7d43f57baa'


def need(ok, why):
    if not ok: raise ValueError(why)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def relative(value):
    need(type(value) is str and value and '\\' not in value and '\x00' not in value, 'Safe publication member required')
    path = PurePosixPath(value)
    need(not path.is_absolute() and str(path) == value and '..' not in path.parts
         and not any(p.casefold() == '.git' for p in path.parts), 'Safe publication relative member required')
    return path


def exact_ref(value):
    need(type(value) is dict and set(value) == {'path', 'sha256'}, 'Exact external file reference required')
    need(type(value['sha256']) is str and len(value['sha256']) == 64 and all(c in '0123456789abcdef' for c in value['sha256']),
         'Exact SHA256 required')
    return value


def code_module(reference, name):
    exact_ref(reference); path = ROOT/relative(reference['path'])
    for part in [path, *path.parents]: need(not part.is_symlink(), 'Symlink in publication code path')
    need(sha(path.read_bytes()) == reference['sha256'], 'Publication code pin differs: ' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def pinned(reader, reference):
    exact_ref(reference); raw = reader.read_bytes(reference['path'])
    need(sha(raw) == reference['sha256'], 'Preserved original reference differs')
    return json.loads(raw)


def sealed_output(reader, reference, kind):
    seal = pinned(reader, reference); root = Path(reference['path']).parent
    need(type(seal.get('version')) is int and seal['version'] == 1 and seal.get('kind') == kind
         and type(seal.get('files')) is dict, 'Exact original output seal required')
    physical = reader.directory(str(root)); members = set()
    for path in physical.rglob('*'):
        need(not path.is_symlink(), 'No symlinks in independent output')
        if path.is_file(): members.add(path.relative_to(physical).as_posix())
    need(members == set(seal['files']) | {'SEAL.json'}, 'Independent sealed output membership differs')
    for name, digest in seal['files'].items():
        relative(name); need(sha(reader.read_bytes(str(root/name))) == digest, 'Independent sealed member differs')
    return len(seal['files'])


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')
    path.chmod(0o444)


def verify(manifest, output):
    need(manifest.get('kind') == 'pooled-forward-published-study' and type(manifest.get('version')) is int
         and manifest['version'] == 1 and manifest.get('study_closed') is True, 'Closed publication manifest required')
    need(set(manifest['code']) == CODE_KEYS and set(manifest['inputs']) == INPUT_KEYS, 'Exact publication code/input registry required')
    modules = {}
    # Explicit names are needed by these unchanged dependency imports.
    for key, name in [('projection', 'anonymous_projection'), ('session', 'session'), ('archive', 'published_archive'),
                      ('cold', 'published_cold'), ('preserve', 'published_preserve'), ('phase', 'published_phase'),
                      ('metric', 'published_metric'), ('session_replay', 'published_session_replay')]:
        modules[key] = code_module(manifest['code'][key], name)
    transports = {}; decoded = {}; restored = None
    for item in manifest['transports']:
        need(type(item) is dict and set(item) == {'id', 'directory', 'transport_sha256', 'index_sha256', 'restore'},
             'Exact cold transport declaration required')
        key = item['id']; need(type(key) is str and key.replace('-', '').isalnum() and key not in transports, 'Unique finite transport identity required')
        folder = output/key; folder.mkdir(); target = folder/'decoded'
        result = modules['cold'].decode(str(ROOT/relative(item['directory'])), item['transport_sha256'], str(target))
        verified = modules['archive'].verify(target, item['index_sha256'])
        save(folder/'DECODED.json', {'transport': result, 'inner': verified})
        transports[key] = verified; decoded[key] = target
        need(type(item['restore']) is bool, 'Explicit restore selection required')
        if item['restore']:
            need(restored is None and key == manifest['main_transport'], 'Exactly the declared main evidence restore required')
            restored = modules['archive'].restore(target, folder/'readonly-restore', item['index_sha256'], readonly=True)
            save(folder/'RESTORED.json', restored)
            restored = dict(restored, transport_id=key)
    need(restored is not None, 'Main original-key readonly restore missing')
    mapping = Path(restored['mapping']); mapping_sha = sha(mapping.read_bytes()); main_id = manifest['main_transport']
    reader = modules['session'].MapSessionReader(str(mapping), map_sha256=mapping_sha, index_sha256=restored['index_sha256'])
    plan = pinned(reader, manifest['preservation_plan'])
    recorded = modules['session_replay'].replay(plan, decoded[main_id], restored['index_sha256'], str(mapping), mapping_sha)
    save(output/'RECORDED-PROVENANCE.json', recorded)
    cause = modules['phase'].verify_index(reader, manifest['inputs']['cause_index'], 'cause')
    alarm = modules['phase'].verify_index(reader, manifest['inputs']['alarm_index'], 'alarm')
    alarm_index = modules['phase'].original(reader, manifest['inputs']['alarm_index'])
    need(alarm_index['first_cause_barrier'] == manifest['inputs']['cause_index'], 'Complete original predecessor differs')
    members = sealed_output(reader, manifest['inputs']['correspondence_seal'], 'independent-anonymous-correspondence-seal')
    inputs = {key: pinned(reader, ref) for key, ref in manifest['inputs'].items()
              if key not in {'cause_index', 'alarm_index', 'correspondence_seal'}}
    need(manifest['inputs']['coverage_registry']['sha256'] == COVERAGE_SHA, 'Prospective mandatory applicability registry differs')
    metric_input = inputs['metric_inputs']; need(metric_input.get('kind') == 'sealed-five-case-metric-input'
        and type(metric_input.get('version')) is int and metric_input['version'] == 1, 'Exact closed metric input required')
    for key in ['correspondence_seal', 'mapping_reveal', 'coverage_registry']:
        need(metric_input['provenance'][key] == manifest['inputs'][key], 'Metric input predecessor differs: '+key)
    need(metric_input['coverage_denominators'] == inputs['coverage_registry']['coverage_denominators'],
         'Metric applicability differs from the independent frozen registry')
    calculated = {'version': 1, 'kind': 'five-case-fixed-metric-results', 'arms': {
        arm: modules['metric'].summarize(metric_input['cases'], arm, metric_input['assignment'],
            shared_costs=metric_input['shared_costs'], coverage_denominators=metric_input['coverage_denominators'])
        for arm in ['A', 'B']}}
    need(calculated == inputs['metric_results'], 'Fixed metric replay differs; no result regeneration accepted')
    save(output/'METRIC-REPLAY.json', calculated)
    mapped = reader.verify_all(); reader.close()
    result = {'version': 1, 'kind': 'pooled-forward-publication-replay', 'status': 'verified',
        'cold_transports_verified': sorted(transports), 'readonly_original_key_payloads_verified': mapped,
        'cause_contexts': cause['distinct_contexts'], 'alarm_contexts': alarm['distinct_contexts'],
        'independent_consensus_members': members, 'five_case_fixed_metrics_identical': True,
        'source_domain_evaluation': 'unsupported', 'source_responsibility_evaluation': 'unsupported',
        'current_source_delivery_verified': False, 'native_sdk_execution': False,
        'scope': 'Lossless transport, byte/record barriers, original native-history/public provenance and arithmetic replay. Independent product judgments remain sealed observations. No original-path fallback, new source/domain grading, UI resampling or cleanup.'}
    save(output/'RESULT.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT/'PUBLICATION.json')
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); output = args.output.resolve(); need(not output.exists(), 'Fresh publication replay output required')
    raw = args.manifest.read_bytes(); need(sha(raw) == args.manifest_sha256, 'External publication manifest pin differs')
    output.mkdir(parents=True); save(output/'ENTRY.json', {'manifest': str(args.manifest.resolve()),
        'manifest_sha256': args.manifest_sha256, 'started_at_unix': time.time(), 'native_sdk_execution': False})
    try:
        result = verify(json.loads(raw), output)
    except BaseException as error:
        save(output/'FAILURE.json', {'status': 'failed', 'error_type': type(error).__name__, 'message': str(error),
            'traceback': traceback.format_exc(), 'finished_at_unix': time.time(), 'partial_outputs_retained': True})
        raise
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__': main()
