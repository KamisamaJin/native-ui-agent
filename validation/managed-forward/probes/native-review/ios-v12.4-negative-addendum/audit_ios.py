#!/usr/bin/env python3
"""Offline audit of the one sealed v12.4 iOS negative SDK package.

No SDK execution, source binding, device mutation, or production edits.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BASE = OUT.parents[2]
RUN = BASE / 'cache/neutral-ios-v12.4-negative'
NATIVE = RUN / 'capture/native'
CANDIDATE = BASE / 'candidate-v12.4'
PREPARED = BASE / 'probes/native/prepared'
FREEZE_SHA = '7056f1caf253284f3cd920ba6113384061abb359d2025747a0daeac0f35f2e2b'


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def load(path):
    return json.loads(Path(path).read_text())


def save(name, value):
    path = OUT / name
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def pin(paths):
    return {str(p.resolve()): {'sha256': sha(p), 'size': p.stat().st_size}
            for p in sorted(set(paths)) if p.is_file()}


def main():
    freeze_path = BASE / 'CANDIDATE-FREEZE-5.json'
    freeze = load(freeze_path)
    seal_path = PREPARED / 'pre-sdk-seal.json'
    seal = load(seal_path)
    permitted_seal = {k: v for k, v in seal['files'].items()
                      if k.startswith('ios/') or k in {'fixtures.json', 'routes.json'}}
    config = load(PREPARED / 'ios/config.json')
    source_files = [Path(x) for x in config['source_roots']]
    bridge = Path(config['bridge'])
    spec_dir = BASE / 'probes/spec'
    pinned = pin([freeze_path, seal_path, bridge, *source_files,
                  *spec_dir.glob('*'),
                  *[CANDIDATE / x for x in freeze['files']],
                  *[PREPARED / x for x in permitted_seal],
                  *[p for p in RUN.rglob('*') if p.is_file()]])
    save('readset-before.json', {'at_unix': time.time(), 'files': pinned,
         'scope': 'Only original neutral spec, permitted iOS/shared sealed inputs, exact candidate-v12.4 files, actual neutral Counter source roots, and this new raw iOS run. Hashing xcresult bytes is integrity inspection, not a claim to have interpreted every opaque object.'})
    integrity = {
        'freeze_sha256': sha(freeze_path),
        'freeze_matches_pinned': sha(freeze_path) == FREEZE_SHA,
        'frozen_file_count': len(freeze['files']),
        'frozen_mismatches': [x for x, digest in freeze['files'].items()
                              if sha(CANDIDATE / x) != digest],
        'prepared_permitted_file_count': len(permitted_seal),
        'prepared_mismatches': [x for x, digest in permitted_seal.items()
                                if sha(PREPARED / x) != digest],
        'raw_files': len([p for p in RUN.rglob('*') if p.is_file()]),
        'raw_bytes': sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()),
    }
    sys.path.insert(0, str(CANDIDATE / 'scripts'))
    import design_contract as design
    import execution_plan as execution
    import action_guard
    import native_checks
    import acceptance

    plan = load(config['plan'])
    lock = load(config['design_lock'])
    fixtures = load(config['fixtures'])
    observation_path = NATIVE / 'observation.json'
    observation = load(observation_path)
    receipt = load(RUN / 'capture/result.json')
    compiled_execution = load(RUN / 'capture/execution.json')
    compiled_plan = load(RUN / 'capture/parent-plan.json')
    actions = design.verify_generated(plan, lock, config['design_sha256'], 'ios')
    execution.verify_execution(compiled_execution, plan, lock, config['design_sha256'], fixtures, sha(bridge))
    guards = action_guard.verify_observation(compiled_execution['actions'], observation, 'ios')
    coverage = execution.coverage_receipt(compiled_execution, observation)
    report = native_checks.evaluate(plan, observation, 'ios', root=NATIVE,
               observation_sha256=sha(observation_path), design_lock=lock,
               design_sha256=config['design_sha256'])
    expected_environment = load(config['environment'])
    environment = acceptance.environment(observation, expected_environment, 'ios')
    execution.verify_capture_images(receipt, NATIVE)
    save('recomputed-automatic.json', report)
    save('recomputed-environment.json', environment)
    save('recomputed-coverage.json', coverage)
    save('recomputed-guards.json', guards)
    fingerprint = execution.source_fingerprint(config['source_roots'])
    integrity.update({
        'plan_exact_capture_match': plan == compiled_plan,
        'lock_canonical_sha256': design.digest(lock),
        'lock_approved_sha256_match': design.digest(lock) == config['design_sha256'],
        'source_fingerprint': fingerprint,
        'source_before_matches_current': fingerprint == load(RUN / 'capture/source-before.json'),
        'source_after_matches_current': fingerprint == load(RUN / 'capture/source-after.json'),
        'source_canonical_sha256': design.digest(fingerprint),
        'source_receipt_digest_matches': design.digest(fingerprint) == receipt['source_sha256'],
        'bridge_sha256': sha(bridge),
        'compiled_bridge_matches': sha(bridge) == sha(NATIVE / 'compiled-project/Bridge.swift'),
        'compiled_observer_app_matches_frozen': sha(NATIVE / 'compiled-project/ObserverApp.swift') == sha(CANDIDATE / 'assets/ios-observer/ObserverApp.swift'),
        'compiled_observer_tests_matches_frozen': sha(NATIVE / 'compiled-project/ObserverTests.swift') == sha(CANDIDATE / 'assets/ios-observer/ObserverTests.swift'),
        'fixture_transport_matches': compiled_execution['config'] == load(RUN / 'capture/fixtures.json'),
        'action_transport_matches': compiled_execution['actions'] == load(RUN / 'capture/actions.json'),
        'receipt_tool_files_match_frozen': {x: sha(CANDIDATE / x) == digest for x, digest in receipt['tool_files'].items()},
        'recomputed_counts': report['counts'],
        'automatic_exact_capture_match': report == load(RUN / 'capture/automatic.json'),
        'environment_exact_capture_match': environment == load(RUN / 'capture/environment-check.json'),
        'coverage_exact_capture_match': coverage == load(RUN / 'capture/execution-coverage.json'),
    })
    runtime_root = RUN / 'capture/tool-runtime'
    runtime_paths = [p for p in runtime_root.rglob('*') if p.is_file()]
    integrity['captured_runtime_file_count'] = len(runtime_paths)
    integrity['captured_runtime_mismatches'] = [str(p.relative_to(runtime_root)) for p in runtime_paths
          if not (CANDIDATE / p.relative_to(runtime_root)).is_file()
          or sha(p) != sha(CANDIDATE / p.relative_to(runtime_root))]
    save('integrity-before.json', integrity)

    from PIL import Image
    attachments = load(NATIVE / 'attachments/manifest.json')
    exported = {x['exportedFileName']: x for group in attachments for x in group['attachments']}
    image_rows = []
    for frame in observation['snapshots']:
        path = NATIVE / frame['screenshot']
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            size, mode = image.size, image.mode
            pixel_sha = sha_bytes(image.tobytes())
        item = exported[path.name]
        image_rows.append({'index': frame['index'], 'name': frame['name'], 'state_id': frame['state_id'],
             'path': str(path.resolve()), 'sha256': sha(path), 'pixel_sha256': pixel_sha,
             'fully_decoded': True, 'size': size, 'mode': mode,
             'dimensions_match_observation': list(size) == [frame['screenshot_pixels']['width'], frame['screenshot_pixels']['height']],
             'xcresult_attachment': item, 'binding': frame['binding'],
             'capture_binding_stable': frame['binding'] == frame['binding_after_capture'],
             'tally_nodes': [x for x in frame['nodes'] if x.get('identifier') == 'counter.tally'],
             'callbacks': frame['callbacks'], 'actual_environment': frame['runtime']['actual_environment']})
    save('image-decode.json', {'images': image_rows,
         'full_decode_count': len(image_rows), 'unique_encoded_sha256_count': len({x['sha256'] for x in image_rows}),
         'unique_decoded_pixel_sha256_count': len({x['pixel_sha256'] for x in image_rows}),
         'scope': 'Complete PNG decode and binding/attachment checks. Visual reading is recorded separately, and no full-content/computed-style/physical-hit-area claim is inferred.'})
    save('action-bindings.json', {'original_runtime': observation['original_runtime'],
         'steps': observation['steps'], 'state_captures': observation['state_captures'],
         'measurement_kind': observation['measurement_kind']})
    print(json.dumps({'integrity': integrity, 'decoded_images': len(image_rows),
                      'environment_status': environment['status'], 'coverage_satisfied': coverage['satisfied']}, indent=2))


if __name__ == '__main__':
    main()
