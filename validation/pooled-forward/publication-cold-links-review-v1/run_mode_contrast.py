"""One retained decoder control matching the sharing-operator mode fault.

The same real chmod immediately before a real os.link must be rejected by the
frozen v3 decoder's post-link stable identity check. No hash/verdict is mocked.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import time
from unittest import mock

from run_review import HERE, file_sha, load_module, need, save, snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run-dir', required=True)
    args = parser.parse_args(); run = Path(args.run_dir)
    need(run.is_absolute() and str(run) == args.run_dir and run.is_relative_to(HERE) and not run.exists(),
         'Fresh retained run directory required')
    run.mkdir(); cold = run / 'cold'; cold.mkdir()
    fixture = HERE / 'HOST/attempt-1/FIXTURE'
    fixture_record = json.loads((fixture / 'FIXTURE.json').read_bytes())
    frozen_source = HERE / 'vendor/v3/publication-tools/cold_storage/cold.py'
    need(file_sha(frozen_source) == '1df42e542466ff45db9fbc00c950be13f1bac2e1a1eb9ebb24e854068f0e8fda', 'External decoder pin differs')
    for path in (fixture / 'cold').iterdir():
        dest = cold / path.name; shutil.copyfile(path, dest); dest.chmod(stat.S_IMODE(path.lstat().st_mode))
    module = load_module('mode_contrast_decoder', frozen_source)
    original_link = os.link; calls = []; before = {}; caught = None
    def mode_fault(source, target, **kwargs):
        source = Path(source); before[str(source)] = snapshot(source)
        source.chmod(0o644); calls.append({'source': str(source), 'target': str(target)})
        return original_link(source, target, **kwargs)
    save(run / 'ENTRY.json', {'version': 1, 'test_source_sha256': file_sha(Path(__file__)),
                             'decoder_sha256': file_sha(frozen_source), 'started_at_unix': time.time()})
    with mock.patch.object(module.os, 'link', side_effect=mode_fault):
        try: module.decode(str(cold), fixture_record['transport_sha256'], str(run / 'decoded'))
        except (ValueError, OSError) as error: caught = {'type': type(error).__name__, 'message': str(error)}
    result = {'version': 1, 'kind': 'independent-v3-changed-mode-during-link-control',
              'caught': caught, 'calls': calls, 'before': before,
              'after': {path: snapshot(Path(path)) for path in before},
              'test_source_sha256': file_sha(Path(__file__)),
              'decoder_sha256': file_sha(frozen_source), 'partial_failure_retained': True,
              'status': 'passed' if len(calls) == 1 and caught is not None else 'failed'}
    save(run / 'RESULT.json', result)
    print(json.dumps({'status': result['status'], 'result': str(run / 'RESULT.json'),
                      'sha256': file_sha(run / 'RESULT.json')}))
    return result['status'] != 'passed'


if __name__ == '__main__': raise SystemExit(main())
