"""Same-fixture v1 false rejection then v2 success on real Git0644 inputs."""
import argparse
import json
from pathlib import Path
import shutil

import test_cleanup_v2 as controls


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run-dir', required=True)
    args = parser.parse_args(); run = Path(args.run_dir)
    controls.need(run.is_absolute() and run.is_relative_to(controls.HERE) and not run.exists(), 'Fresh retained own fixture root required')
    controls.need(controls.sha(controls.HERE / 'cleanup.py') == 'f72adb087d14acbbc461a3ee206cfe93f28d07c3c0981f4f3cd01dad924d01f7', 'Preserved v1 source differs')
    controls.need(controls.sha(controls.HERE / 'cleanup_v2.py') == 'cdbbbe8134df207338a85c580f04f45c19c5910730d60c8f7ec901a23cd9d093', 'V2 source differs')
    run.mkdir(); subject = controls.Controls(run)
    def compare(ctx):
        before_output = controls.raw_state(ctx['replay'])
        cold_before = controls.raw_state(ctx['repo'] / 'publications')
        # Byte-exact copied versions, identical namespace/metadata fixture.
        # The helper's fixed repo relation depends on its directory, not basename.
        shutil.copyfile(controls.HERE / 'cleanup.py', ctx['helper'])
        controls.need(subject.invoke(ctx) != 0, 'V1 Git0644 false rejection was not reproduced')
        controls.need('Readonly ordinary file required' in (ctx['case'] / 'stderr.txt').read_text(), 'V1 rejection did not reach the cold permission gate')
        controls.need(before_output == controls.raw_state(ctx['replay']), 'Rejected v1 changed output bytes/modes')
        for name in ['COMMAND.json', 'stdout.txt', 'stderr.txt']:
            (ctx['case'] / name).rename(ctx['case'] / ('v1-' + name))
        shutil.copyfile(controls.HERE / 'cleanup_v2.py', ctx['helper'])
        evidence = subject.positive(ctx)
        controls.need(cold_before == controls.raw_state(ctx['repo'] / 'publications'), 'Version correction changed Git cold bytes/modes/inodes')
        return {'v1_false_rejection_reproduced': True, 'same_exact_input_namespace': True,
                'v2': evidence, 'only_test_helper_copy_replaced_with_exact_versioned_bytes': True}
    subject.case('same-git0644-fixture-v1-reject-v2-complete', compare, git_modes=True)
    result = {'version': 1, 'kind': 'same-fixture-git-checkout-compatibility-control',
              'test_sha256': controls.sha(Path(__file__)),
              'controls_source_sha256': controls.sha(controls.HERE / 'test_cleanup_v2.py'),
              'passed': sum(v['status'] == 'passed' for v in subject.results),
              'failed': sum(v['status'] == 'failed' for v in subject.results), 'results': subject.results,
              'actual_study_or_cache_accessed': False}
    controls.write(run / 'RESULT.json', result)
    print(json.dumps({'result': str(run / 'RESULT.json'), 'sha256': controls.sha(run / 'RESULT.json'),
                      'passed': result['passed'], 'failed': result['failed']}))
    return result['failed'] != 0


if __name__ == '__main__': raise SystemExit(main())
