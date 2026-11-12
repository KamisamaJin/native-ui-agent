#!/usr/bin/env python3
"""Reproduce the shared collector foundation on the preserved v12.6 control.

Only explicit collector/coverage/source-domain/log plumbing is ported. The old
resource policy, source fingerprint model, final recapture and controller remain.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import time

R=Path(__file__).resolve().parent
LIVE=R.parents[1]/'native-ui-agent'
TARGET=R/'baseline-v12.6-common-5'


def function(text,name):
    node=next(n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))and n.name==name)
    lines=text.splitlines(True);return ''.join(lines[node.lineno-1:node.end_lineno])


def replace_function(text,name,new):
    old=function(text,name);assert text.count(old)==1
    return text.replace(old,new)


def replace(text,before,after):
    assert text.count(before)==1,(before,text.count(before))
    return text.replace(before,after)


def main():
    shutil.copytree(R/'baseline-v12.6-common-1',TARGET,ignore=shutil.ignore_patterns('__pycache__','.DS_Store'))
    shared=['assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift','assets/ios-observer/provider-conformance.json','assets/ios-observer/geometry-encoding.json',
            'scripts/native_checks.py','scripts/scroll_coverage.py','scripts/coverage_domain.py','scripts/acceptance.py',
            'scripts/review_contract.py','scripts/requirement_routes.py','scripts/locator_diagnostics.py',
            'references/state-evidence.md','tests/test_scroll_coverage.py','tests/test_coverage_domain.py','tests/test_native_checks.py']
    for rel in shared:
        p=TARGET/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(LIVE/rel,p)
    p=TARGET/'scripts/execution_plan.py';t=p.read_text();new=(LIVE/'scripts/execution_plan.py').read_text()
    for name in ['_coverage_facts','coverage_receipt','request_coverage_receipt']:t=replace_function(t,name,function(new,name))
    t=replace(t,'environment_sha=None, resources=None):','environment_sha=None, resources=None, domain_approval=None):')
    t=replace(t,"    record = {'version': 1, 'startedAtUnix': time.time(), 'execution_sha256': value['execution_sha256'],",
                "    if domain_approval is not None and value['platform']=='ios':\n        save('coverage-domain-prepared.json',domain_approval)\n        command += ['--coverage-domain',str(output/'coverage-domain-prepared.json')]\n    record = {'version': 1, 'startedAtUnix': time.time(), 'execution_sha256': value['execution_sha256'],")
    t=replace(t,"    tool_root = Path(__file__).resolve().parents[1]", "    if domain_approval is not None and value['platform']=='ios':\n        record['input_hashes']['coverage-domain-prepared.json'] = hashlib.sha256((output/'coverage-domain-prepared.json').read_bytes()).hexdigest()\n    tool_root = Path(__file__).resolve().parents[1]")
    p.write_text(t)
    p=TARGET/'scripts/ios_observe.py';t=p.read_text();new=(LIVE/'scripts/ios_observe.py').read_text()
    t=replace_function(t,'validate_cached_build',function(new,'validate_cached_build'))
    build=function(new,'prepare_build')
    start=build.index('    import capture_validity\n');end=build.index('    signature = build_signature',start)
    build=build[:start]+build[end:]
    t=replace_function(t,'prepare_build',build)
    t=replace(t,"Path(__file__).with_name('scroll_coverage.py')]", "Path(__file__).with_name('scroll_coverage.py'), Path(__file__).with_name('coverage_domain.py')]")
    t=replace(t,"        if strategy == 'coalesced':\n            import execution_plan", "        if getattr(args,'coverage_domain',None) and test.returncode == 0 and manifest['native_test_count'] > 0:\n            import coverage_domain\n            coverage_domain.complete(json.loads(Path(args.coverage_domain).read_text()),manifest,output)\n        if strategy == 'coalesced':\n            import execution_plan")
    t=replace(t,'    except Exception as exc:\n        manifest["error"] = str(exc)', '    except Exception as exc:\n        manifest[\'status\'] = \'error\'\n        manifest["error"] = str(exc)')
    t=replace(t,'    args = parser.parse_args()',"    p.add_argument('--coverage-domain',help='Controller-prepared independently pinned closed-domain/source admission')\n    args = parser.parse_args()")
    p.write_text(t)
    p=TARGET/'scripts/feedback_loop.py';t=p.read_text();new=(LIVE/'scripts/feedback_loop.py').read_text()
    begin=new.index('    domain_approval=None; domain_tasks=[]');end=new.index('    if execute or reused:',begin)
    t=replace(t,'    if execute:\n        value=xp.compile_execution',new[begin:end]+'    if execute:\n        value=xp.compile_execution')
    t=replace(t,"environment_sha=config['environment_sha256'],resources=resources)","environment_sha=config['environment_sha256'],resources=resources,domain_approval=domain_approval)")
    t=replace(t,"'source_tasks':source_tasks,", "'source_tasks':source_tasks,'domain_tasks':domain_tasks,")
    t=replace(t,"    plan,lock,policy,packet=evidence_review.original(config,capture,cycle['capture_sha256'])", "    plan,lock,policy,packet=evidence_review.original(config,capture,cycle['capture_sha256'])\n    if config.get('coverage_domain_ref'):\n        __import__('coverage_domain').prepare(config,plan,lock)")
    p.write_text(t)
    original=R/'baseline-v12.6';patch='';changes={}
    for p in sorted(TARGET.rglob('*')):
        if not p.is_file()or'__pycache__'in p.parts:continue
        rel=str(p.relative_to(TARGET));o=original/rel;before=o.read_bytes()if o.exists()else b'';after=p.read_bytes()
        if before==after:continue
        changes[rel]={'before_sha256':hashlib.sha256(before).hexdigest()if o.exists()else None,'after_sha256':hashlib.sha256(after).hexdigest()}
        patch+=''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    with(R/'qualification/baseline-common-foundation-5.patch').open('x')as f:f.write(patch)
    with(R/'qualification/COMMON-FOUNDATION-5.json').open('x')as f:json.dump({'at_unix':time.time(),'changes':changes,'port_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Shared collector/domain/boundary/build-log provenance only. Original default controller, source model, one-shot devices, final recapture and cache build identity remain original.','whole_byte_identical_common_files':shared},f,indent=2)
    print(json.dumps({'files':len(changes),'baseline':str(TARGET)}))


if __name__=='__main__':main()
