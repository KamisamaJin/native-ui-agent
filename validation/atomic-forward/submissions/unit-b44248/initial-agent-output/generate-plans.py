from pathlib import Path
import subprocess
root = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-v2/T1/public')
workspace = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-b44248')
compiler = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/candidate-v8/scripts/design_contract.py')
for case in ('P1', 'P2'):
    for platform in ('ios', 'android'):
        command = ['python3', str(compiler), 'compile', '--lock', str(root / 'design-lock.json'), '--lock-sha256', '1595cbbb3a50848a0fe9a639bc775dde0a781690fc94381a6eb8f0a469d4c31a', '--scenario', case, '--platform', platform, '--bindings', str(root / 'bindings.json'), '--actions', str(root / 'cases' / case / ('actions.' + platform + '.json')), '--output', str(workspace / 'agent-output/plans' / case / platform)]
        print(' '.join(command), flush=True)
        subprocess.run(command, check=True)
