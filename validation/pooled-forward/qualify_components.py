#!/usr/bin/env python3
"""Normal fresh/full, force-fresh, original reuse and final closure qualification."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

R = Path(__file__).resolve().parent
PY = sys.executable
def load(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(v, f, indent=2)


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--candidate', required=True); p.add_argument('--freeze', required=True)
    a = p.parse_args(); skill = R / a.candidate; freeze = R / a.freeze; tag = a.candidate
    base = R / 'cache/qualification' / ('evidence-' + tag)
    if base.exists(): raise ValueError('Fresh qualification evidence required')
    base.mkdir(); rows = []; captures = []
    save(base / 'ADMISSION.json', {'at_unix': time.time(), 'candidate_freeze_sha256': sha(freeze), 'driver_sha256': sha(__file__),
         'steps': ['ios-cold fresh default C0', 'same ios-cold explicit --fresh C07', 'android fresh C0',
                   'bind independently observed source', 'unchanged R0 both', 'ordinary full final both'],
         'expected': 'Same pooled iOS UUID, genuinely different native/app/reset sessions; all104 fixed atomic rows pass, original final reuse is explicit, no SDK on R0/final, final resources retired.',
         'no_business_or_performance_credit': True})
    def call(case, stage, args):
        c = R / 'cache/qualification/profiles-v3' / (case + '.json')
        record = R / 'operators/commands' / (tag + '-' + stage)
        command = [PY, '-B', str(R / 'native_envelope.py'), '--config', str(c), '--skill', str(skill), '--record', str(record),
                   '--timeout', '1200', '--', PY, '-B', str(skill / 'scripts/ui_loop.py')] + args
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        save(base / (stage + '-driver.json'), {'argv': command, 'exit_code': result.returncode, 'stdout': result.stdout})
        if result.returncode: raise RuntimeError('Qualification command failed: ' + stage)
    def native(case, stage, extra=()):
        out = base / stage
        call(case, stage, ['native', '--config', str(R / 'cache/qualification/profiles-v3' / (case + '.json')),
                           '--output', str(out)] + list(extra))
        cycle = load(out / 'cycle.json')
        if cycle.get('native_executed') or cycle.get('capture_reused'):
            receipt = load(cycle['capture_result']); packet = Path(cycle['capture_result']).parent
            report = load(packet / 'automatic.json')
            rows.append({'stage': stage, 'status': cycle['status'], 'native_executed': cycle['native_executed'],
                         'capture_reused': cycle.get('capture_reused'), 'capture': cycle['capture_result'],
                         'capture_sha256': cycle['capture_sha256'], 'counts': report['counts'], 'receipt_status': receipt['status']})
            if receipt['status'] != 'verified_capture' or report['counts'] != {'passed': 104, 'failed': 0, 'unassessed': 0}:
                raise RuntimeError('Mandatory native rows not fully demonstrated: ' + stage)
            if cycle['native_executed']: captures.append((stage, packet))
        else: rows.append({'stage': stage, 'status': cycle['status'], 'native_executed': False})
        return cycle
    try:
        native('ios-cold', 'C0-ios')
        native('ios-cold', 'C07-ios', ['--fresh'])
        native('android', 'C0-android')
        for case in ['ios-cold', 'android']:
            pl = 'android' if case == 'android' else 'ios'
            call(case, 'source-' + pl, ['bind-source-review', '--config', str(R / 'cache/qualification/profiles-v3' / (case + '.json')),
                                       '--submission', str(R / 'qualification/admission-review' / ('source-submission-' + pl + '.json')),
                                       '--output', str(base / ('source-bound-' + pl + '.json'))])
            cycle = native(case, 'R0-' + pl)
            if cycle['native_executed']: raise RuntimeError('Unchanged review repeated SDK work')
        for case in ['ios-cold', 'android']:
            pl = 'android' if case == 'android' else 'ios'; cycle = native(case, 'F2-' + pl, ['--final'])
            if cycle['status'] != 'accepted' or cycle['native_executed'] or not cycle.get('capture_reused'):
                raise RuntimeError('Ordinary final did not accept a valid original full packet')
            resources = load(base / ('F2-' + pl) / 'resources.json')
            if resources['cleanup_errors'] or resources['remaining_devices'] or resources['remaining_directories']:
                raise RuntimeError('Final retirement incomplete')
        original = {name: packet for name, packet in captures}
        first = load(original['C0-ios'] / 'native/observation.json'); second = load(original['C07-ios'] / 'native/observation.json')
        a_runtime, b_runtime = first['original_runtime'], second['original_runtime']
        a_manifest, b_manifest = (load(original[name] / 'native/manifest.json') for name in ['C0-ios', 'C07-ios'])
        check = {'same_device_uuid': a_manifest['simulator'] == b_manifest['simulator'],
                 'fresh_app_instance': a_runtime['instance'] != b_runtime['instance'],
                 'same_input': a_runtime['input_sha256'] == b_runtime['input_sha256'],
                 'fresh_initial_intervals': a_runtime['event_revision'] == b_runtime['event_revision'] == 0,
                 'actual_two_tests': a_manifest['native_test_count'] == b_manifest['native_test_count'] == 1,
                 'actual_two_owned_resets': bool(a_manifest.get('fixture_reset') and b_manifest.get('fixture_reset'))}
        save(base / 'RESULT.json', {'at_unix': time.time(), 'rows': rows, 'freshness_checks': check, 'passed': all(check.values()),
             'scope': 'Actual fixed neutral native rows, app/reset/session identity and default reuse/closure; no speed or business result. Advisory mounted-child UUID remains U.'})
        if not all(check.values()): raise RuntimeError('Native freshness/pooled identity proof incomplete')
        print(json.dumps({'passed': True, 'freshness_checks': check}))

    except BaseException as error:
        save(base / 'FAILURE.json', {'type':type(error).__name__,'message':str(error),'at_unix':time.time(),'status':'qualification_failed_not_regraded'})
        for case in ['ios-cold','android']:
            try:
                call(case,'failure-close-'+case,['cleanup-native-resources','--config',str(R / 'cache/qualification/profiles-v3' / (case+'.json')),'--output',str(base / ('failure-close-'+case))])
            except BaseException as cleanup:
                save(base / ('cleanup-error-'+case+'.json'),{'type':type(cleanup).__name__,'message':str(cleanup)})
        raise


if __name__ == '__main__': main()
