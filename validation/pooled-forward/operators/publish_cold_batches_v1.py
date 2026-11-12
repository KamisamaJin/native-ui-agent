"""Sequential, bounded Git object preloading for this authorized publication.

Only the fixed cold artifact paths are staged. No force push, branch switching,
source commits, main update, authentication changes or CI claim is performed.
"""
import json
import os
from pathlib import Path
import subprocess
import time

REPO = Path(__file__).resolve().parents[3]
HERE = REPO / 'validation/pooled-forward/operators/git-artifact-batches-v1'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


def main():
    assert git('branch', '--show-current').decode().strip() == 'codex/pooled-forward-v13'
    assert git('remote', 'get-url', 'origin').decode().strip() == 'git@github.com:KamisamaJin/native-ui-agent.git'
    plan = json.loads((HERE / 'PLAN.json').read_text())
    for batch in plan['batches'][1:]:
        number = batch['index']
        names_file = HERE / batch['path_list']
        names = set(names_file.read_bytes().rstrip(b'\0').split(b'\0'))
        assert len(names) == batch['files']
        assert all(n.startswith(b'validation/pooled-forward/publications/') for n in names)
        staged = set(git('diff', '--cached', '--name-only', '-z').rstrip(b'\0').split(b'\0')) - {b''}
        assert not staged or staged <= names
        log = HERE / ('BATCH-%02d.log' % number)
        with log.open('xb') as stream:
            steps = []
            commands = [
                ['git', 'add', '--pathspec-from-file=' + str(names_file), '--pathspec-file-nul'],
                ['git', 'commit', '-m', 'Preserve v13 closed evidence, batch %d of 7 [skip ci]' % number],
                ['git', 'push', '--progress', 'origin', 'HEAD:refs/heads/codex/pooled-forward-v13'],
            ]
            for command in commands:
                start = time.time()
                code = subprocess.call(command, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, GIT_TERMINAL_PROMPT='0'))
                stream.flush()
                steps.append({'argv': command, 'started_at_unix': start, 'finished_at_unix': time.time(), 'exit_code': code})
                if code:
                    (HERE / ('BATCH-%02d-FAILED.json' % number)).write_text(json.dumps({'batch': number, 'steps': steps}, indent=2) + '\n')
                    raise RuntimeError('Batch stopped, retained log: ' + str(log))
        commit = git('rev-parse', 'HEAD').decode().strip()
        (HERE / ('BATCH-%02d-END.json' % number)).write_text(json.dumps({'batch': number, 'commit': commit, 'steps': steps,
            'main_updated': False, 'source_or_final_manifest_committed': False}, indent=2) + '\n')
        print(json.dumps({'batch': number, 'commit': commit, 'branch_pushed': True, 'main_updated': False}), flush=True)


if __name__ == '__main__':
    main()
