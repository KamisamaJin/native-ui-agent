#!/usr/bin/env python3
"""Exact bytes and fixed fact projections, without grading or mapping reveal."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

LEAK = re.compile(r'baseline-v12|candidate-v13|stateful-default|baseline-explicit-prior|/business/T[1-5]/[AB]/|run-cohort2/(?:arms|requests)/')
LEAK_BYTES = re.compile(LEAK.pattern.encode())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def ref(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', required=True)
    parser.add_argument('--revision', type=int, default=1)
    parser.add_argument('--revision-reason')
    args = parser.parse_args()
    assert re.fullmatch(r'Case0[1-5]-[IXY]', args.group)
    assert 1 <= args.revision <= 4
    assert args.revision == 1 and not args.revision_reason
    root = args.root.resolve()
    coord = root / 'operators/cohort2/coordination'
    mapping_path = coord / 'anonymous-map/MAPPING.json'
    mapping_seal = load(coord / 'anonymous-map/SEAL.json')
    assert sha(mapping_path) == mapping_seal['files']['MAPPING.json']
    case_id, version = args.group.split('-')
    mapping = load(mapping_path)['mapping'][case_id]
    task_id, arm = mapping['task'], mapping[version]
    run = root / 'cache/business/run-cohort2'
    assert (run / 'HIDDEN-AUTHORIZATION.json').is_file()
    manifest = load(run / 'manifest.json')
    task = next(t for t in manifest['tasks'] if t['id'] == task_id)
    case = next(t for t in load(root / 'operators/cohort2/INITIAL-AUTHOR-ADMISSION.json')['cases'] if t['id'] == task_id)
    initial = version == 'I'
    private_arm = 'I' if initial else arm
    assert not (task_id == 'T1' and initial), 'Valid I1 already has sealed original facts and the identical complete-input supplement; do not replace its packet or judgments'
    evidence = root / 'cache/business/independent-evaluation'
    episode_ends = [evidence / f'episodes/{task_id}/{private_arm}/{revision}/END.json' for revision in ['continuation', 'remaining-first-execution-v3']]
    episode_end = next((p for p in reversed(episode_ends) if p.is_file() and load(p)['status'] == 'closed'), None)
    assert episode_end is not None, 'Registered first executions and retirement must terminate before packet assembly'
    attempt = args.group + '-complete-v3'
    packet = root / 'cache/business/blind-quality/packets' / attempt
    packet.mkdir(parents=True, exist_ok=False)
    ledger_root = coord / 'blind-packet-ledgers' / attempt
    ledger_root.mkdir(parents=True, exist_ok=False)
    ledger = {'version': 1, 'kind': 'operator-only-anonymous-packet-byte-and-projection-ledger', 'at_unix': time.time(),
              'group': args.group, 'source_identity': {'task': task_id, 'arm': private_arm}, 'copies': [], 'projections': [], 'catalog_commands': []}
    predecessors = []
    for folder in sorted((coord / 'blind-packet-ledgers').glob(args.group + '*')):
        if folder == ledger_root or not folder.is_dir():
            continue
        for name in ['SEAL.json', 'FAILED.json']:
            if (folder / name).is_file():
                predecessors.append(ref(folder / name))
    ledger['operational_revision'] = {'number': 3, 'prior_attempts': predecessors,
        'reason': 'Binding-only revision verifies the explicitly permitted preclaim entry record and unchanged licensed first-execution endpoints. Original failed versions and all source/fact projections remain unchanged; no native resampling.'}
    ledger['native_episode_terminal'] = ref(episode_end)
    runner_path = coord / 'independent_native_v3.py'
    assert sha(runner_path) == '7672ec99ca986a149d303eb8e37fb81da71edf1826c6eb1273da534945ddf722'
    spec = importlib.util.spec_from_file_location('packet_registered_effective_native_v3', runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    def copied(original, relative):
        original = Path(original)
        assert original.is_file() and not original.is_symlink()
        destination = packet / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(original.read_bytes())
        destination.chmod(0o444)
        assert sha(original) == sha(destination)
        ledger['copies'].append({'original': ref(original), 'anonymous_relative': str(relative), 'bytes': original.stat().st_size})
        return str(relative)

    def projected(original, relative, value, selection):
        save(packet / relative, value)
        ledger['projections'].append({'original': ref(original), 'anonymous_relative': str(relative),
                                      'projection_sha256': sha(packet / relative), 'selection': selection})
        return str(relative)

    try:
        source_folder = run / f"arms/{task_id}/{'A' if initial else arm}/{'initial' if initial else 'final-source'}"
        source = load(source_folder / 'source.json')
        assert digest(source['files']) == source['content_sha256']
        for relative, expected in source['files'].items():
            original = source_folder / 'files' / relative
            assert sha(original) == expected['sha256'] and original.stat().st_size == expected['bytes']
            copied(original, 'source/' + relative)
        workspace = root / (f'cache/business/initial-reference/{task_id}/workspace' if initial else f'cache/business/{task_id}/{arm}/workspace')
        placements = {}
        for platform, relative in [('ios', 'alerttoast/Package.swift'), ('android', 'reply/Reply/app/build.gradle.kts')]:
            original = workspace / relative
            assert sha(original) == sha(root / 'cache/hosts' / relative), 'Production placement differs from the original stock host'
            placements[platform] = copied(original, 'source/placement/' + platform + '/' + original.name)
        design = root / 'business-design-cohort2-v2'
        approvals = load(design / 'APPROVAL-MAPPING.json')
        contracts = {}
        for family in ['public', 'private']:
            contracts[family] = {}
            for platform in ['ios', 'android']:
                approved = approvals['profiles'][f"{family}-{case['design_task']}-{platform}"]
                docs = {}
                for key, relative in approved['paths'].items():
                    original = design / relative
                    docs[key] = copied(original, f'contracts/{family}/{platform}/{original.name}')
                contracts[family][platform] = docs
        observations = []
        events = [load(path) for path in sorted((run / 'events').glob('*.json'))]
        public_sources = []
        if initial:
            first = [e for e in events if e['kind'] == 'request_enqueued' and e.get('task') == task_id and e.get('action') == 'diagnostic']
            for public_arm in ['A', 'B']:
                public_sources.append(next(e for e in first if e['arm'] == public_arm))
            public_sources.sort(key=lambda e: e['sequence'])
        else:
            finals = [e for e in events if e['kind'] == 'request_enqueued' and e.get('task') == task_id and e.get('arm') == arm and e.get('action') == 'final']
            assert len(finals) == 1
            public_sources = finals
        specs = []
        for repeat, event in enumerate(public_sources, 1):
            assert event['source']['files'] == source['files']
            for platform in ['ios', 'android']:
                outcome_path = run / 'requests' / event['request_id'] / platform / 'outcome.json'
                config_ref = event['active_configs'][platform]
                assert sha(config_ref['path']) == config_ref['sha256']
                name = f'public-r{repeat}-{platform}' if initial else f'public-{platform}'
                specs.append((name, 'public', platform, outcome_path, Path(config_ref['path']), event['arm']))
        for platform in ['ios', 'android']:
            continued_path = runner.continuation_claim_path(evidence, task_id, private_arm, platform)
            continued = load(continued_path)
            outcome_path = Path(continued['record']) / 'outcome.json'
            outcome = load(outcome_path)
            runner.native_reference(evidence, task_id, private_arm, platform, outcome['config'], outcome['source_capsule'], outcome_path, sha(outcome_path))
            resources_path = Path(outcome['resources']['path'])
            resources = load(resources_path)
            assert sha(resources_path) == outcome['resources']['sha256'] and resources.get('final') is True and all(resources.get(k) == [] for k in ['cleanup_errors', 'remaining_directories', 'remaining_devices']), 'Both original private endpoints require positive owned closure'
            config_ref = outcome['config']
            assert sha(config_ref['path']) == config_ref['sha256']
            ledger.setdefault('registered_private_native_endpoints', []).append({'profile': platform, 'continuation_claim': ref(continued_path),
                'native_outcome': ref(outcome_path), 'original_zero_forwarding_outcome': continued['original_outcome'], 'authority': continued['authority']})
            specs.append((f'private-{platform}', 'private', platform, outcome_path, Path(config_ref['path']), 'A' if initial else arm))
        private_templates = []
        for name, family, platform, outcome_path, config_path, tool_arm in specs:
            outcome = load(outcome_path)
            config = load(config_path)
            entry = {'id': name, 'family': family, 'platform': platform, 'facts_available': False}
            capture_ref = outcome.get('capture')
            if not capture_ref:
                entry['availability'] = 'Original operation retained no capture receipt; native/image conclusions remain unknown.'
                observations.append(entry)
                ledger['projections'].append({'original': ref(outcome_path), 'anonymous_observation': name, 'selection': 'Capture absence only; no arm/tool/cost/failure verdict text.'})
                continue
            assert sha(capture_ref['path']) == capture_ref['sha256']
            capture = Path(capture_ref['path']).parent
            receipt = load(capture_ref['path'])
            request = load(capture / 'request.json')
            before = load(capture / 'source-before.json')
            wanted = {}
            for i, raw in enumerate(request['source_roots']):
                source_index = config['source_roots'].index(raw)
                for relative, row in source['files'].items():
                    index, tail = relative.split('/', 1)
                    if int(index) == source_index:
                        wanted[f'{i}/{tail}'] = row['sha256']
            source_model = receipt.get('source_model')
            if source_model is not None:
                roots = [str(Path(value).resolve()) for value in config['source_roots']]
                declared = config.get('platform_source_roots', {})
                assert isinstance(declared, dict) and not (set(declared) - {'ios', 'android', 'shared'})
                groups = {key: [str(Path(value).resolve()) for value in declared.get(key, [])] for key in ['ios', 'android', 'shared']}
                assert all(len(values) == len(set(values)) and set(values) <= set(roots) for values in groups.values())
                assigned = set().union(*map(set, groups.values()))
                groups['shared'] = sorted(set(groups['shared']) | (set(roots) - assigned))
                indices = [index for index, raw in enumerate(roots) if raw in groups[platform] or raw in groups['shared']]
                expected_model = {'version': 1, 'platform': platform, 'source_roots': roots, 'groups': groups, 'indices': indices}
                assert source_model == expected_model and digest(source_model) == receipt['source_model_sha256']
                assert load(capture / 'source-model.json') == source_model
                wanted = {key: value for key, value in wanted.items() if int(key.split('/', 1)[0]) in indices}
            else:
                assert not config.get('platform_source_roots')
            assert before == wanted and digest(before) == receipt['source_sha256']
            ledger['projections'].append({'original': ref(capture / 'source-before.json'), 'anonymous_observation': name,
                'selection': 'Controller capsule {relative:{sha256,bytes}} projected to frozen request stable-root-index {relative:sha256}; exact original source_model selection including conservative shared roots when present.',
                'controller_content_sha256': source['content_sha256'], 'sut_source_sha256': digest(before), 'source_model': source_model,
                'exact_namespace_verified': True})
            observation_path = capture / 'native/observation.json'
            if not observation_path.is_file():
                entry['availability'] = 'Original capture has no native observation; native/image conclusions remain unknown.'
                observations.append(entry)
                continue
            assert sha(observation_path) == receipt['observation_sha256']
            observation = load(observation_path)
            view = {key: value for key, value in observation.items() if key not in ['operations', 'issues']}
            prefix = f'observations/{name}'
            entry['native_observation'] = projected(observation_path, prefix + '/native/observation.json', view,
                {'all_original_top_level_members_except': ['operations', 'issues'], 'retained_values_unchanged': True})
            for relative, expected in receipt.get('image_hashes', {}).items():
                rel = Path(relative)
                assert not rel.is_absolute() and '..' not in rel.parts
                original = observation_path.parent / rel
                assert sha(original) == expected
                copied(original, prefix + '/native/' + relative)
            automatic_path = capture / 'automatic.json'
            if automatic_path.is_file():
                automatic = load(automatic_path)
                actuals = [{key: row[key] for key in ['id', 'actual', 'snapshot_indices'] if key in row} for row in automatic.get('assertions', [])]
                entry['automatic_actuals'] = projected(automatic_path, prefix + '/automatic-actuals.json', {'assertions': actuals},
                    {'all_assertions': True, 'member_allowlist': ['id', 'actual', 'snapshot_indices'], 'retained_values_unchanged': True})
            tool = manifest['tools'][task['arms'][tool_arm]['tool']]
            raw_catalog = ledger_root / (name + '-catalog-original.json')
            argv = [sys.executable, '-B', str(Path(tool['skill_root']) / 'scripts/review_contract.py'), 'catalog',
                    '--plan', config['plan'], '--design-lock', config['design_lock'], '--design-sha256', config['design_sha256'],
                    '--policy', config['policy'], '--policy-sha256', config['policy_sha256'], '--platform', platform, '--output', str(raw_catalog)]
            with (ledger_root / (name + '-catalog.log')).open('x') as stream:
                result = subprocess.run(argv, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdout=stream, stderr=subprocess.STDOUT)
            assert result.returncode == 0
            ledger['catalog_commands'].append({'argv': argv, 'output': ref(raw_catalog), 'native_or_sdk_execution': False})
            cat = load(raw_catalog)
            cat_sha = cat.pop('catalog_sha256')
            assert digest(cat) == cat_sha
            save(packet / prefix / 'catalog.json', cat)
            execution = load(capture / 'execution.json')
            selected = execution['selected_states']
            visual = [row for row in cat['rows'] if row['method'] == 'visual' and row['state'] in selected]
            template = {'version': 1, 'catalog_sha256': cat_sha, 'observation_sha256': sha(observation_path),
                        'decisions': [{'review_id': row['review_id'], 'actual': None, 'reason': '', 'snapshot_indices': []} for row in visual]}
            save(packet / prefix / 'visual-requirements.json', {'rows': [{key: row.get(key) for key in ['id', 'state', 'proposition', 'review_id']} for row in visual], 'submission_template': template})
            entry.update(facts_available=True, catalog=prefix + '/catalog.json', visual_requirements=prefix + '/visual-requirements.json',
                         original_observation_sha256=sha(observation_path), original_image_count=len(receipt.get('image_hashes', {})))
            observations.append(entry)
            if family == 'private':
                private_templates.append({'observation_id': name, 'platform': platform, 'submission': template})
        copied(coord / 'BLIND-JUDGE-INSTRUCTIONS-v1.md', 'INSTRUCTIONS.md')
        description = {'version': 1, 'anonymous_group': args.group, 'fixed_source_file_count': len(source['files']),
                       'source_files': source['files'], 'production_placement': placements, 'contracts': contracts,
                       'observations': observations, 'scope': 'One fixed source version. Exact source/PNG bytes and bounded unchanged native actuals/approved contracts; no tool identity, cost, worker claim, other grade or arm mapping.'}
        save(packet / 'PACKET.json', description)
        template = {'version': 1, 'kind': 'independent-blind-cause-grade', 'anonymous_group': args.group, 'judge_id': None,
                    'product_causes': [], 'uncertain_product_suspicions': [], 'measurement_and_infrastructure_limits': [],
                    'source_observations': [{'family': family, 'platform': platform, 'observations': [
                        {'id': claim, 'observed': None, 'reason': '', 'citations': []}
                        for claim in ['production-api', 'thin-bridge', 'production-placement']]}
                        for family in ['public', 'private'] for platform in ['ios', 'android']],
                    'private_image_observations': private_templates, 'coverage_assessment': [],
                    'images_inspected': [], 'source_files_inspected': [], 'native_facts_inspected': [], 'contract_files_inspected': [],
                    'independent_quality_complete': None, 'scope_notes': []}
        save(packet / 'GRADE-TEMPLATE.json', template)
        inventory = {}
        for path in sorted(packet.rglob('*')):
            assert not path.is_symlink()
            if path.is_file():
                assert not LEAK_BYTES.search(path.read_bytes()), 'Identity leak in anonymous member: ' + str(path.relative_to(packet))
                inventory[str(path.relative_to(packet))] = {'sha256': sha(path), 'bytes': path.stat().st_size}
        ledger.update(original_source_manifest=ref(source_folder / 'source.json'), private_episode=ref(episode_end),
                      anonymous_inventory=inventory, textual_identity_scan_passed=True, no_quality_judgment=True)
        save(ledger_root / 'LEDGER.json', ledger)
        save(packet / 'SEAL.json', {'version': 1, 'kind': 'anonymous-fixed-version-input-seal', 'anonymous_group': args.group,
                                    'files': {name: row['sha256'] for name, row in inventory.items()}})
        save(ledger_root / 'SEAL.json', {'version': 1, 'packet_seal': ref(packet / 'SEAL.json'), 'ledger': ref(ledger_root / 'LEDGER.json'),
                                        'projection_policy': ref(coord / 'ANONYMOUS-PROJECTION-v1.json'), 'mapping_revealed': False})
        supplement_admission_path = coord / 'SOURCE-CONTRACT-SUPPLEMENT-ADMISSION.json'
        assert sha(supplement_admission_path) == 'cfc6d7df72c75971f1781bc2d4306c9a90460e61f56e64d59fdf85729e15e904'
        supplement = next(v for v in load(supplement_admission_path)['cases'] if v['task'] == task_id)
        supplement_root = Path(supplement['anonymous_directory'])
        supplement_files = {str(p.relative_to(supplement_root)): {'sha256': sha(p), 'bytes': p.stat().st_size}
                            for p in sorted(supplement_root.rglob('*')) if p.is_file()}
        assert len(supplement_files) == 153
        assert all(not p.is_symlink() and not LEAK_BYTES.search(p.read_bytes()) for p in supplement_root.rglob('*') if p.is_file())
        save(ledger_root / 'COMPLETE-INPUT.json', {'version': 1, 'anonymous_group': args.group,
            'base_packet_seal': ref(packet / 'SEAL.json'), 'base_packet_ledger': ref(ledger_root / 'LEDGER.json'),
            'source_contract_supplement_admission': ref(supplement_admission_path),
            'anonymous_supplement_directory': str(supplement_root), 'anonymous_supplement_inventory': supplement_files,
            'anonymous_supplement_content_sha256': digest(supplement_files),
            'scope': 'Full immutable original-input version for this fixed source; old failed/incomplete inputs and grades remain intact. No mapping reveal or source/expected/native-fact change.'})
        print(json.dumps({'group': args.group, 'packet': str(packet), 'packet_seal_sha256': sha(packet / 'SEAL.json'),
                          'observations': len(observations), 'original_png_copies': sum(p.suffix.lower() == '.png' for p in packet.rglob('*')), 'mapping_revealed': False}))
    except BaseException as error:
        save(ledger_root / 'FAILED.json', {'at_unix': time.time(), 'error': {'type': type(error).__name__, 'message': str(error)},
                                         'traceback': traceback.format_exc(), 'partial_ledger': ledger,
                                         'scope': 'Partial original/projection attempt retained; no grade dispatched and no native retry.'})
        raise


if __name__ == '__main__':
    main()
