#!/usr/bin/env python3
"""Run the shared before-code guard on all20 profiles and adversarial mapping checks."""
from author import *
sys.path.insert(0,str(ROOT/'scripts'))
from admit_profile import verify

def main():
    mapping=load(ROOT/'APPROVAL-MAPPING.json');mapping_sha=digest(mapping)
    write(ROOT/'APPROVAL-MAPPING.sha256',mapping_sha+'\n')
    shared=REPO/'validation/pooled-forward/design_capability_preflight.py'
    freeze=load(REPO/'validation/pooled-forward/operators/design-capability-preflight-freeze.json')
    assert sha(shared)==freeze['sha256']
    results=[];checks=[];rebuilds=[]
    roots={'candidate-v13.9':TOOLS.parent,'baseline-v12.6-common-6':REPO/'validation/pooled-forward/baseline-v12.6-common-6'}
    for profile_id,entry in mapping['profiles'].items():
        p=ROOT/entry['profile_path'];config=load(p)
        baseline=roots['baseline-v12.6-common-6'];rebuild=ROOT/'baseline-rebuild'/profile_id
        argv=[sys.executable,'-B',str(baseline/'scripts/design_contract.py'),'compile','--lock',config['design_lock'],'--lock-sha256',config['design_sha256'],'--scenario',entry['scenario'],'--platform',entry['intended_platform'],'--bindings',str(p.parent/'bindings.json'),'--actions',str(p.parent/'actions.json'),'--output',str(rebuild)]
        c=subprocess.run(argv,cwd=REPO,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
        receipt=ROOT/'pure-receipts'/('baseline-rebuild-'+profile_id+'.json')
        write(receipt,dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,native_run=False,recorded_at_utc=datetime.now(timezone.utc).isoformat()))
        assert c.returncode==0,receipt
        assert load(rebuild/'plan.json')==load(config['plan'])
        assert load(rebuild/'actions.json')==load(p.parent/'generated/actions.json')
        rebuilds.append(dict(profile_id=profile_id,plan_equal=True,actions_equal=True,receipt_sha256=sha(receipt)))
        for arm,skill in roots.items():
            out=ROOT/'shared-preflight'/arm/profile_id
            argv=[sys.executable,'-B',str(shared),'--skill',str(skill),'--config',str(p),'--output',str(out),'--responsibility-source','reference','--responsibility-pointer','/responsibilities']
            c=subprocess.run(argv,cwd=REPO,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
            receipt=ROOT/'pure-receipts'/('shared-'+arm+'-'+profile_id+'.json')
            write(receipt,dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,native_run=False,shared_script_sha256=sha(shared),recorded_at_utc=datetime.now(timezone.utc).isoformat()))
            assert c.returncode==0,receipt
            result=load(out/'RESULT.json')
            assert result['passed'] and not result['mandatory_capability_issues'] and not result['must_route_gaps'] and not result['unowned_assertions']
            assert result['source_truth_approved'] is False and result['runtime_truth_approved'] is False and result['native_execution'] is False
            assert len(result['evidence_truth_still_unassessed'])>=3
            results.append(dict(arm=arm,profile_id=profile_id,result_path=str((out/'RESULT.json').relative_to(ROOT)),result_sha256=sha(out/'RESULT.json'),receipt_path=str(receipt.relative_to(ROOT)),receipt_sha256=sha(receipt),passed=True))
        admitted=verify(ROOT,mapping,mapping_sha,entry['intended_platform'],profile_id,config)
        assert admitted['status']=='admitted_profile'
        negative=[]
        def reject(name,cfg,platform=None,approval=None):
            try:verify(ROOT,approval or mapping,mapping_sha,platform or entry['intended_platform'],profile_id,cfg)
            except (ValueError,KeyError,FileNotFoundError):negative.append(name);return
            raise AssertionError('Wrong profile admitted: '+name)
        opposite='android' if entry['intended_platform']=='ios' else 'ios'
        reject('actual-opposite-platform',config,platform=opposite)
        for key in ['design_lock','plan','policy','routes','environment','fixtures','bridge']:
            changed=copy.deepcopy(config);changed[key]=str(ROOT/'not-approved'/Path(changed[key]).name);reject('wrong-'+key+'-path',changed)
        for key in ['design_sha256','policy_sha256','routes_sha256','environment_sha256']:
            changed=copy.deepcopy(config);changed[key]='0'*64;reject('wrong-'+key,changed)
        changed=copy.deepcopy(config);changed['launch_ref']={'source':'launch','pointer':'/'+opposite};reject('wrong-launch-ref',changed)
        changed=copy.deepcopy(config);changed['responsibility_ref']={'source':'reference','pointer':'/obligations'};reject('wrong-responsibility-ref',changed)
        try:verify(ROOT,mapping,mapping_sha,entry['intended_platform'],profile_id,config,runtime=True)
        except ValueError:negative.append('placeholder-native-launch')
        else:raise AssertionError('Placeholder native launch admitted')
        checks.append(dict(profile_id=profile_id,admitted=admitted,rejected_mutations=negative))
    write(ROOT/'PROFILE-ADMIT-DECLARATION.json',dict(version=1,mandatory_script='scripts/admit_profile.py',mandatory_native_entry='scripts/native_entry.py',approval_mapping_path='APPROVAL-MAPPING.json',approval_mapping_canonical_sha256=mapping_sha,actual_platform_must_be_explicit=True,opposite_platform_expressions_schema_only=True,exact_inputs=['design_lock','plan','policy','routes','environment','fixtures','bridge','launch_ref','responsibility_ref'],placeholder_native_launch_forbidden=True,all_twenty_profiles_checked=checks,scope='This is pure profile/capability admission. All source/runtime truth remains unassessed.'))
    write(ROOT/'SHARED-PREFLIGHT-SUMMARY.json',dict(version=2,shared_script_sha256=sha(shared),shared_freeze_sha256=sha(REPO/'validation/pooled-forward/operators/design-capability-preflight-freeze.json'),frozen_skills={k:str(v) for k,v in roots.items()},results=results,passed_count=len(results),passes_each_arm={arm:sum(r['arm']==arm for r in results) for arm in roots},baseline_exact_rebuilds=rebuilds,native_executions=0,source_approvals=0,statement='All20 profiles passed the shared subprocess-forbidden preimplementation full-chain preflight in both frozen SUTs. Required native responsibility groups have nonempty matching compiled assertions. Source claims are still MUST, supported only as provider/boundary capability and explicitly unassessed.'))
    print(json.dumps({'shared_preflight_passed':len(results),'baseline_exact_rebuilds':len(rebuilds),'profile_positive_checks':len(checks),'negative_checks':sum(len(v['rejected_mutations']) for v in checks),'native_executions':0,'source_approvals':0}))
if __name__=='__main__':main()
