#!/usr/bin/env python3
"""Focused all15 gate mutation: a repinned derived fact must not reach build."""
import contextlib
import argparse
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
from unittest import mock

from fixture import Reader, Store, sha

ROOT = Path(__file__).resolve().parent.parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--candidate-only', action='store_true'); args = parser.parse_args()
    candidate = load(ROOT / 'revision-v3/alarm-material-tools-v3/batch.py', 'derived_candidate')
    sys.path.insert(0, str(ROOT / 'snapshots/driver-v1'))
    original = load(ROOT / 'snapshots/driver-v1/batch.py', 'derived_original')
    study = ROOT / 'fixtures/compatible'; reader = Reader(ROOT, candidate)
    cause = {'path': str(ROOT / 'fixtures/cause/INDEX.json'), 'sha256': reader.hash(str(ROOT / 'fixtures/cause/INDEX.json'))}
    rows = []
    for i in range(1, 6):
        for version in ('I', 'X', 'Y'):
            group = 'Case0%d-%s' % (i, version); source = ROOT / 'fixtures/miniselection' / (group + '.json')
            rows.append({'group': group, 'spec': {'path': str(source), 'sha256': reader.hash(str(source))},
                'derivations': {'path': str(ROOT / 'fixtures/miniselection/DERIVATIONS.json'),
                                'sha256': reader.hash(str(ROOT / 'fixtures/miniselection/DERIVATIONS.json'))}})
    for label, module in ([('v3', candidate)] if args.candidate_only else [('v1', original), ('v3', candidate)]):
        folder = ROOT / 'results' / ('derivation-' + label); folder.mkdir()
        store = Store(folder, candidate); work = folder / 'work'; work.mkdir()
        collector = candidate.Group(study, reader, 'Case01-I', 'T1', 'I', {}, [], {}, {}, work)
        raw = store.put(folder / 'RAW.json', {'rows': [{'status': 'F', 'expected': 48, 'actual': 44}]})
        collector.json_document(raw, 'reports/derived.json', {'kind': 'original-synthetic-report'})
        derivation = copy.deepcopy(collector.derivations[0]); path = Path(derivation['derived']['path'])
        value = reader.read_json(str(path)); value['rows'][0]['actual'] = 42
        (folder / 'BEFORE-DERIVED.json').write_bytes(path.read_bytes()); path.chmod(0o644); path.write_bytes(candidate.encoded(value))
        changed = {'path': str(path), 'sha256': reader.hash(str(path))}
        derivation['derived'] = changed; collector.documents[0]['original'] = changed
        collector.description['documents'][0]['original_sha256'] = changed['sha256']
        selected = copy.deepcopy(rows); spec = reader.read_json(selected[0]['spec']['path'])
        spec['documents'] = collector.documents; spec['anonymous_description'] = collector.description
        selected[0]['spec'] = store.put(folder / 'SPEC.json', spec)
        selected[0]['derivations'] = store.put(folder / 'DERIVATIONS.json', [derivation])
        seal = store.put(folder / 'SELECTION.json', {'version': 1, 'kind': 'all15-uniform-original-alarm-selection-seal',
            'original_root': str(study), 'groups': selected, 'first_cause_barrier': cause, 'closed_cause_contexts': 30,
            'code_pins': module.code_pins() if hasattr(module, 'code_pins') else {},
            'mapping_revealed_to_judges_or_model': False, 'quality_adjudicated': False})
        calls = []; error = None
        def marker(_reader, _spec, output, record):
            calls.append({'group': _spec['anonymous_group'], 'output': str(output)})
            raise RuntimeError('Synthetic build-reach marker')
        try:
            with mock.patch.object(module, 'build', side_effect=marker):
                if hasattr(module, 'package_selected'):
                    module.package_selected(study, reader, seal, folder / 'packets', folder / 'packaging')
                else:
                    argv = [module.__file__, 'build', '--root', str(study), '--id', 'derived-tamper-' + label,
                            '--selection-seal', seal['path'], '--selection-seal-sha256', seal['sha256']]
                    with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()): module.main()
        except Exception as exc: error = {'type': type(exc).__name__, 'message': str(exc)}
        result = {'version': 1, 'test': 'repinned-derived-fact-cannot-bypass-original-proof',
            'passed': error is not None and not calls, 'packaging_calls': calls, 'error': error,
            'module_sha256': sha(Path(module.__file__).read_bytes()), 'control_sha256': sha(Path(__file__).read_bytes()),
            'scope': 'Synthetic actual changed 44 to 42 with all derived/spec/selection byte pins updated; raw original/projection proof remains 44. Real readers retained; a build-reach marker observes the preflight boundary.'}
        (folder / 'RESULT.json').write_bytes(candidate.encoded(result)); print(json.dumps({'revision': label, 'passed': result['passed'], 'error': error}))


if __name__ == '__main__': main()
