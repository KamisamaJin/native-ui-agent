#!/usr/bin/env python3
"""Read-only verification of the prepared finite list; no binding execution."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

D = Path(__file__).resolve().parent


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_bytes())


def main():
    plan = load(D/'PLAN.json'); contexts = load(D/'CONTEXTS.json'); ops = plan['operations']
    assert len(ops) == len({x['id'] for x in ops}) == len({x['record'] for x in ops}) == 110
    assert Counter(x['action'] for x in ops) == {'bind-source-review':30, 'bind-native-review':30, 'finish-native-review':30, 'source-only':20}
    private = {x['scope']:x for x in contexts['private_contexts']}
    public = {x['scope']:x for x in contexts['final_public_contexts']}
    assert len(private) == 30 and len(public) == 20
    for op in ops:
        argv = op['argv']; arg = lambda k: argv[argv.index(k)+1]
        if op['kind'] == 'original-private':
            c = private[op['scope']]
            assert arg('--config') == c['config']['path'] and arg('--record') == op['record'] and arg('--action') == op['action']
            if op['action'] != 'bind-source-review':
                assert arg('--native-outcome') == c['native_operation']['path']
                assert arg('--native-outcome-sha256') == c['native_operation']['sha256']
                key = 'capture' if op['action'] == 'bind-native-review' else 'cycle'
                assert arg('--'+key) == c[key]['path']
            if c['arm'] == 'I':
                assert arg('--initial-monitor') == c['initial_monitor']['record']
                assert arg('--initial-seal-sha256') == contexts['pins']['initial_preparation']['sha256']
        else:
            c = public[op['scope']]
            assert c['arm'] in {'A', 'B'} and c['config']['path'] in argv and c['config']['sha256'] in argv
            assert argv[2] == contexts['envelope']['meter_path'] and contexts['envelope']['path'] in argv
            assert contexts['pins']['source_only']['path'] in argv and '@SUBMISSION_SHA256@' in argv
    assert sum(bool(c['source_domain_append_chain']) for c in public.values()) == 2
    for c in public.values():
        active = c['original_public_config']
        for step in c['source_domain_append_chain']:
            assert step['parent_config'] == active; active = step['config']
        assert active == c['config']
    refs = list(contexts['pins'].values()) + [contexts[k] for k in ['manifest', 'hidden_authorization', 'native_all30_closure']]
    for c in private.values():
        refs += [c[k] for k in ['config', 'source_capsule', 'original_claim', 'native_operation', 'capture', 'cycle', 'original_observation', 'review_request', 'compiled_responsibility_ref']]
    for c in public.values(): refs += [c[k] for k in ['config', 'source_capsule', 'tool_manifest']]
    for pin in refs: assert sha(pin['path']) == pin['sha256']
    assert len(refs) > 300 and plan['execution_authorized'] is False
    assert all(x['execution_authorized'] is False and x['submission_ref'] is None for x in ops)
    assert not Path(plan['future_namespace']).exists()
    for name in ['prepare_inventory.py', 'emit_command.py']:
        text = (D/name).read_text(); compile(text, str(D/name), 'exec')
        assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any(a.name in {'subprocess','socket'} for a in n.names) for n in ast.walk(ast.parse(text)))
    base = [sys.executable, '-B', str(D/'emit_command.py'), '--plan-sha256', sha(D/'PLAN.json')]
    cases = [([], True), (['--operation-id','T1-I-ios-finish-native-review'], True),
             (['--operation-id','T1-I-ios-bind-source-review'], False), (['--operation-id','T9-A-ios-native'], False)]
    for args, ok in cases:
        result = subprocess.run(base+args, capture_output=True, text=True)
        assert (result.returncode == 0) == ok
        if ok: assert load_stdout(result)['execution_authorized'] is False
    result = subprocess.run([*base[:4], '0'*64], capture_output=True, text=True)
    assert result.returncode != 0
    fixture = D/'SYNTHETIC-SUBMISSION.json'
    for pin, ok in [(sha(fixture), True), ('0'*64, False)]:
        result = subprocess.run(base+['--operation-id','T1-A-ios-public-source-only','--submission',str(fixture),'--submission-sha256',pin], capture_output=True, text=True)
        assert (result.returncode == 0) == ok
        if ok: assert load_stdout(result)['executes_process'] is False and load_stdout(result)['execution_authorized'] is False
    manifest = load(contexts['manifest']['path'])
    for name, tool in manifest['tools'].items(): assert load(D/('tool-manifest-'+name+'.json')) == tool
    assert plan['mandatory_per_arm'] == 8232 and plan['not_applicable_per_arm'] == 2100
    assert not Path(plan['future_namespace']).exists()
    print(json.dumps({'status':'verified-preparation-only', 'operations':110, 'original_context_refs_rehashed':len(refs), 'formatter_cases':7, 'bind_finish_sdk_operations_executed':0}))


def load_stdout(result): return json.loads(result.stdout)


if __name__ == '__main__': main()
