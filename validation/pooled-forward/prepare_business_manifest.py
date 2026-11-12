#!/usr/bin/env python3
"""Close the common controller manifest after all five initial pair admissions."""
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parent
DESIGN = R / 'business-design-cohort2-v2'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def ref(path):
    return {'path': str(path), 'sha256': sha(path)}


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def tool(root, api):
    members = [root / 'SKILL.md', *sorted((root / 'scripts').glob('*.py')),
               *sorted((root / 'references').glob('*.md')),
               *sorted(p for p in (root / 'assets').rglob('*') if p.is_file())]
    return {'skill_root': str(root), 'api': api,
            'files': {p.relative_to(root).as_posix(): sha(p) for p in members}}


def main():
    admission = load(R / 'operators/cohort2/INITIAL-AUTHOR-ADMISSION.json')
    output = R / 'operators/cohort2/study-manifest.json'
    manifest = {'version': 1, 'study_id': 'pooled_native_business_cohort2',
                'run_root': str(R / 'cache/business/run-cohort2'),
                'protocol': ref(R / 'PROTOCOL.json'),
                'speed_gate': ref(R / 'qualification/benchmark-gate/RESULT.json'),
                'design_approval': ref(R / 'business-design-cohort2-review/revision-v2/APPROVAL-SEAL.json'),
                'envelope': {'path': str(R / 'native_envelope.py'), 'sha256': sha(R / 'native_envelope.py'),
                             'meter_path': str(R / 'measure.py'), 'meter_sha256': sha(R / 'measure.py'),
                             'meter_spec_path': str(R / 'operators/whole-study-meter-spec-v2.json'),
                             'meter_spec_sha256': sha(R / 'operators/whole-study-meter-spec-v2.json')},
                'tools': {'control': tool(R / 'baseline-v12.6-common-6', 'baseline-explicit-prior'),
                          'treatment': tool(R / 'candidate-v13.9', 'stateful-default')},
                'source_domain_reviews': {'registry': ref(R / 'operators/cohort2/SOURCE-DOMAIN-REVIEW-REGISTRY.json'),
                                          'max_requests_per_arm': 4}, 'tasks': []}
    for case in admission['cases']:
        task = {'id': case['id'], 'arms': {}}
        public = Path(case['public_root'])
        for arm, selected in [('A', 'control'), ('B', 'treatment')]:
            base = R / 'cache/business' / case['id'] / arm
            workspace = base / 'workspace'
            configs = {pl: str(base / 'public-profiles' / (pl + '.json')) for pl in ['ios', 'android']}
            readset = {p for p in public.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
            readset.update({R / 'business_profile_admission.py', DESIGN / 'scripts/admit_profile.py',
                            DESIGN / 'APPROVAL-MAPPING.json', R / 'COHORT2-EXECUTION.json', R / 'BUSINESS-METRICS.md',
                            R / 'operators/cohort2/ALL-FIVE-INITIAL-PAIRS-BEFORE-RENDER.json',
                            workspace / 'alerttoast/Package.swift', workspace / 'reply/Reply/app/build.gradle.kts',
                            workspace / 'reply/Reply/build.gradle.kts', workspace / 'reply/Reply/settings.gradle.kts',
                            workspace / 'reply/Reply/gradle.properties', workspace / 'reply/Reply/gradle/libs.versions.toml',
                            workspace / 'reply/Reply/gradlew'})
            for path in configs.values():
                config = load(path)
                for key in ['coverage_domain_ref', 'coverage_provider_ref']:
                    if config.get(key):
                        readset.add(Path(config[key]['path']))
            if any(not p.is_file() for p in readset):
                raise ValueError('Required immutable public/build input is missing: ' + repr([str(p) for p in readset if not p.is_file()]))
            hooks = {pl: {'script': str(R / 'business_profile_admission.py'), 'root': str(DESIGN),
                           'approval': str(DESIGN / 'APPROVAL-MAPPING.json'),
                           'approval_sha256': canonical(load(DESIGN / 'APPROVAL-MAPPING.json')),
                           'dependencies': [str(DESIGN / 'scripts/admit_profile.py')]} for pl in configs}
            task['arms'][arm] = {'tool': selected, 'workspace': str(workspace),
                                'source_roots': [str(workspace / 'alerttoast/Sources'), str(workspace / 'reply/Reply/app/src/main')],
                                'public_configs': configs, 'profile_order': ['ios', 'android'],
                                'public_readset': sorted(map(str, readset)),
                                'hidden_configs': {pl: str(base / 'hidden-profiles' / (pl + '.json')) for pl in configs},
                                'resource_roots': [str(base / 'resources' / pl) for pl in configs],
                                'profile_admissions': hooks}
        manifest['tasks'].append(task)
    with output.open('x') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'manifest': str(output), 'sha256': sha(output), 'tasks': len(manifest['tasks']),
                      'native_executed': False, 'hidden_configs_opened': False}))


if __name__ == '__main__':
    main()
