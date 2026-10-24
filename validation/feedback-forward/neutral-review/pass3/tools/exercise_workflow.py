from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parents[1];NEUTRAL=BASE/'neutral';SNAPSHOT=BASE/'development/candidate-attempt-3';CAP=BASE/'neutral-targeted'
sys.path.insert(0,str(SNAPSHOT/'scripts'))
import design_contract as design
import native_checks
import requirement_routes
import acceptance

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(ROOT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')

def main():
    begun=time.time();approval=load(NEUTRAL/'APPROVAL.json');lock=load(NEUTRAL/'design/lock.json');planpath=NEUTRAL/'generated/ordinary400/design/plan.json';plan=load(planpath)
    obs=load(CAP/'native/observation.json');env=load(ROOT/'environment-recomputed.json');receipt=load(CAP/'result.json');result_sha=sha(CAP/'result.json')
    state=next(s for s in plan['states']if s['id']=='replaced');found,complete,_,_=native_checks.bound_state_evidence(obs,state);assert complete
    decisions=[]
    for rule in plan['assertions']:
        if rule['kind']!='manual'or rule['state']!='replaced':continue
        if rule['coverage']=='full_content':indices=[i for i,_ in found]
        else:indices=[next(i for i,s in found if native_checks.resolve(s,rule['target'],'ios')['semantic'].get('fully_within_viewport'))]
        status='failed'if rule['requirement_id']=='action-appearance'else'passed'
        reasons={
            'full-layout':'All eight overlapping original frames show the current heading/summary/revision/count, cards 01–06, action, cards 07–10 and end note in order, with real bottom and no observed overlap or horizontal clipping.',
            'text-wrapping':'Original full-content frames at actual width400/large show all labels, ten card bodies and footer wrapping readably without ellipses or horizontal truncation. The disabled color failure is separate.',
            'neutral-surfaces':'Original middle-card frames show the approved white canvas and neutral card/main/secondary text appearance; no computed SwiftUI style measurement is claimed.',
            'action-appearance':'The disabled action remains visibly faded beyond the sealed #DCE2E7 fill / #55616C label. Original PNG diagnostic picking again shows #EDF0F3 fill and #A1A8AF solid glyph core. Native disabled state and 52 pt height pass separately.'}
        decisions.append({'id':rule['id'],'method':'visual','status':status,'reason':reasons[rule['requirement_id']],'snapshot_indices':indices,
            'evidence':[{'path':obs['snapshots'][i]['screenshot'],'sha256':sha(CAP/'native'/obs['snapshots'][i]['screenshot'])}for i in indices]})
    manual={'version':1,'observation_sha256':sha(CAP/'native/observation.json'),'decisions':decisions,'reviewer':'Independent neutral forward tester','scope':'Selected replaced state only; no old full-run judgment fills an unobserved targeted state.'}
    save('manual.json',manual)
    reviewed=native_checks.evaluate(plan,obs,'ios',manual=manual,root=CAP/'native',observation_sha256=sha(CAP/'native/observation.json'),design_lock=lock,design_sha256=approval['design_lock_sha256'])
    reviewed['environment']=env;save('reviewed.json',reviewed)
    coverage=requirement_routes.audit(lock,approval['design_lock_sha256'],plan,load(NEUTRAL/'design/routes.json'),approval['routes_sha256'])
    save('library-admission.json',requirement_routes.admission(coverage,plan,reviewed,execution_scope='targeted',capture=receipt,environment=env))
    commands=[]
    def run(name,script,args,expected_exit=0):
        argv=[sys.executable,'-B',str(SNAPSHOT/'scripts'/script),*map(str,args)];start=time.time();r=subprocess.run(argv,capture_output=True,text=True)
        row={'name':name,'argv':argv,'started_unix':start,'finished_unix':time.time(),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'expected_exit':expected_exit}
        (ROOT/'cli'/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n');commands.append(row)
        assert r.returncode==expected_exit,(name,r.stderr)
    common=['--plan',planpath,'--design-lock',NEUTRAL/'design/lock.json','--design-sha256',approval['design_lock_sha256'],'--routes',NEUTRAL/'design/routes.json','--routes-sha256',approval['routes_sha256']]
    run('recompile-selected','execution_plan.py',['--plan',planpath,'--design-lock',NEUTRAL/'design/lock.json','--design-sha256',approval['design_lock_sha256'],
        '--fixtures',NEUTRAL/'inputs/ordinary400.json','--bridge',NEUTRAL/'source/Bridge.swift','--launch-source','launch','--launch-pointer','/ordinary400','--state','replaced','--output',ROOT/'cli/recompiled'])
    assert load(ROOT/'cli/recompiled/execution.json')==load(CAP/'execution.json')
    run('audit','requirement_routes.py',['audit',*common,'--output',ROOT/'cli/coverage.json'])
    run('route-automatic','requirement_routes.py',['route',*common,'--report',CAP/'automatic.json','--observation',CAP/'native/observation.json','--output',ROOT/'cli/automatic-routes.json'])
    run('route-reviewed','requirement_routes.py',['route',*common,'--report',ROOT/'reviewed.json','--observation',CAP/'native/observation.json','--output',ROOT/'cli/reviewed-routes.json'])
    capture_args=['--capture-result',CAP/'result.json','--capture-result-sha256',result_sha,'--environment',CAP/'expected-environment.json','--environment-sha256',design.digest(load(CAP/'expected-environment.json'))]
    run('admit-targeted','requirement_routes.py',['admit',*common,'--report',CAP/'automatic.json',*capture_args,'--scope','targeted','--output',ROOT/'cli/targeted-admission.json'])
    run('admit-default-full','requirement_routes.py',['admit',*common,'--report',CAP/'automatic.json',*capture_args,'--output',ROOT/'cli/default-full-admission.json'])
    run('admit-reviewed-original-receipt','requirement_routes.py',['admit',*common,'--report',ROOT/'reviewed.json',*capture_args,'--scope','targeted','--output',ROOT/'cli/reviewed-admission-unproduced.json'],expected_exit=1)
    retest=['--coverage',ROOT/'cli/coverage.json','--plan',planpath,'--capture-result',CAP/'result.json','--capture-result-sha256',result_sha,'--failed-id','replaced/action-appearance']
    run('retest-unchanged-source','retest_plan.py',[*retest,'--source-root',NEUTRAL/'source/Bridge.swift','--output',ROOT/'cli/retest-unchanged-unproduced.json'],expected_exit=1)
    run('retest-different-root-namespace','retest_plan.py',[*retest,'--source-root',NEUTRAL/'source','--output',ROOT/'cli/retest-root-unproduced.json'],expected_exit=1)
    # This focused library control exercises the measured mode's original-failure gate
    # using ACTUAL original automatic rows, without declaring a fake source version.
    try:
        requirement_routes.report_rows(load(CAP/'automatic.json'),plan)
        original_failed=[r['id']for r in load(CAP/'automatic.json')['assertions']if r['status']=='failed']
        assert original_failed==[]
    except ValueError:raise
    save('workflow.json',{'version':1,'started_unix':begun,'finished_unix':time.time(),'commands':commands,'reviewed_counts':reviewed['counts'],
        'selected_state_counts':{s:sum(r['status']==s for r in reviewed['assertions']if r['state']=='replaced')for s in ['passed','failed','unassessed']},
        'original_automatic_failed_ids':original_failed,'result_sha256_retained_before_cli':result_sha,'source_unchanged':True,'sdk_executed':False,
        'limits':['Targeted capture cannot satisfy full release.', 'No source change exists, so no positive measured-retest route is justified.', 'Measured retest currently reads original automatic.json; this original report has no failed rows. Independent visual failures are in a separate SHA-bound reviewed report.', 'Retest source-root identities/order are exact; using the containing directory instead of the captured explicit file is rejected, even though it contains the same file. No relocation mapping was exercised.']})
    print(json.dumps({'reviewed_counts':reviewed['counts'],'selected_replaced_counts':{s:sum(r['status']==s for r in reviewed['assertions']if r['state']=='replaced')for s in ['passed','failed','unassessed']},'commands':len(commands),'expected_errors_retained':sum(r['exit_code']!=0 for r in commands)},indent=2))

if __name__=='__main__':main()
