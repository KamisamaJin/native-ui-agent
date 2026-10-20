#!/usr/bin/env python3
"""Recheck generic native evidence, gates, coverage and cache facts, not business UI."""
import argparse
import ast
import json
from pathlib import Path
from contract import R, read, sha, checks


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--write', action='store_true'); args=parser.parse_args()
    freezes = [('original-v3','original-v3-freeze.json'),('common-v3','common-gate-freeze.json'),('candidate-v4','candidate-v4-freeze.json')]
    for bundle, filename in freezes:
        for relative, expected in read(R/filename)['files'].items(): assert sha(R/bundle/relative)==expected
    def gate(path): return ast.dump(next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='callback_verdict'),include_attributes=False)
    assert gate(R/'common-v3/scripts/native_checks.py')==gate(R/'candidate-v4/scripts/native_checks.py')
    copies=[p for folder in ['common-v3','candidate-v4','generic-sources','generic-evidence']for p in(R/folder).rglob('*')if p.is_file()and p.suffix in {'.swift','.kt','.py'}]
    by_sha={sha(p):str(p.relative_to(R))for p in copies}
    rows=[];observations={};manifests={}
    for folder in sorted((R/'generic-evidence').iterdir()):
        if not folder.is_dir():continue
        for relative,digest in read(folder/'portable-sha256.json').items():assert sha(folder/relative)==digest,(folder,relative)
        manifest=read(folder/'manifest.json');observation=read(folder/'observation.json');observations[folder.name]=observation;manifests[folder.name]=manifest
        assert manifest['native_test_count']==1
        for snapshot in observation['snapshots']:assert sha(folder/snapshot['screenshot'])==manifest['image_hashes'][snapshot['screenshot']]
        relevant={name:digest for name,digest in manifest['source_hashes'].items()if name.endswith(('ObserverTests.swift','ObserverApp.swift','Bridge.swift','ObserverBridge.kt','NativeObserverTest.kt','ios_observe.py','android_observe.py'))}
        assert relevant and all(digest in by_sha for digest in relevant.values()),(folder,'missing exact compiled observer/wrapper/bridge source copy')
        states=[]
        for capture in observation.get('state_captures',[]):
            b=capture['binding'];spec={'id':capture['state_id'],'input_index':b.get('fixture_index',b.get('input_index')),'after_action':capture['after_action']}
            _,complete,reason,_=checks.state_evidence(observation,spec)
            assert complete,(folder,capture['state_id'],reason)
            states.append(capture['state_id'])
        rows.append({'case':folder.name,'native_tests':1,'native_exit_code':manifest.get('test_exit_code',manifest.get('exit_code')),
                     'native_capture_status':manifest['status'],'command_seconds':round(manifest['finished_at']-manifest['started_at'],3),
                     'snapshots':len(observation['snapshots']),'complete_states':states,'cache_hit':manifest.get('build_cache',{}).get('hit'),
                     'timings':manifest.get('timings'),'manifest_sha256':sha(folder/'manifest.json'),
                     'observer_source_copies':{name:by_sha[digest]for name,digest in relevant.items()}})
    expected=read(R/'generic/expected.json')['gate']
    for name in ['ios-common-gate','ios-candidate-first','android-common-gate','android-candidate-gate']:
        platform='ios'if name.startswith('ios')else'android'
        for step in observations[name]['steps']:
            state=step['state_id'];events=['delivered']if state=='delivered-correct'else['wanted']if state in {'delivered-silent','delivered-wrong'}else[]
            verdict=checks.callback_verdict(step,events,platform,stimulus='caller_update'if state=='caller-update-quiet'else'activation')
            assert verdict['status']==expected[state],(name,state,verdict)
    viewport=[]
    for name in ['ios-common-viewport','ios-final-cache-cold','ios-final-frozen-warm','android-common-viewport','android-candidate-viewport']:
        o=observations[name];step=o['steps'][1];snapshot=o['snapshots'][step.get('after',step.get('snapshot'))]
        target=[n for n in snapshot['nodes']if n['identifier']=='gen.disclosure'];assert len(target)==1
        full=target[0].get('fully_within_viewport',target[0].get('fully_visible'))is True
        assert full==('common'not in name),(name,'unexpected generic viewport outcome')
        platform='ios'if name.startswith('ios')else'android'
        assert checks.callback_verdict(step,['expanded'],platform)['status']=='passed'
        viewport.append({'case':name,'target_fully_visible':full,'callback_exactly_once':True})
    cold=manifests['ios-final-tool-path-change'];warm=manifests['ios-final-frozen-warm']
    assert cold['build_cache']['hit']is False and warm['build_cache']['hit']is True
    assert cold['build_cache']['signature']==warm['build_cache']['signature']
    assert cold['build_cache']['artifacts']==warm['build_cache']['artifacts']
    c=observations['ios-final-tool-path-change']['original_runtime'];w=observations['ios-final-frozen-warm']['original_runtime']
    assert c['instance']!=w['instance']and c['input_sha256']!=w['input_sha256']
    independent=read(R/'independent-generic/summary.json')
    for platform in ['ios','android']:
        item=independent['platforms'][platform]
        assert item['native_test_count']==1 and item['native_exit_code']==0
        assert item['checker_counts']=={'passed':5,'failed':0,'unassessed':1}
        assert all(s['complete_recomputed']for s in item['states'])
    result={'native_tests':len(rows),'snapshots':sum(row['snapshots']for row in rows),'runs':rows,'post_action_viewport':viewport,
            'scope':'Generic probes only, including deliberate missing selectors and wrong/silent handlers. Real native source/input/PNG integrity, shared gates, interval recomputation, target viewport and fresh-input/process cache reuse. Not new business samples, a new visual grade, native SDK replay or isolated hardware performance benchmark.'}
    output=R/'generic-summary.json';encoded=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.write:assert not output.exists();output.write_text(encoded)
    else:assert output.read_text()==encoded
    print(json.dumps({'status':'passed_generic_native_evidence','native_tests':result['native_tests'],'snapshots':result['snapshots']}))


if __name__=='__main__':main()
