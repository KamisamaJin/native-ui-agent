from foundation_cases import *
import argparse,traceback
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import scroll_coverage,native_checks,execution_plan
pristine=ROOT/'fixtures'/'pristine';results=[]
for name,expected_direct,expected_full in CASES:
 folder=ROOT/'work'/a.arm/name;o,s,root,found=make_case(name,folder,pristine)
 proof=scroll_coverage.certify(found,o['state_captures'][0]['binding'],root)
 evidence=native_checks.bound_state_evidence(o,s,root);execution={'execution_sha256':'e'*64,'scope':'full','platform':'ios','required_coverage':[{'state_id':'strip','coverage':'full_content','targets':[]}],'config':{'execution_state_definitions':[s]}}
 coverage=execution_plan.coverage_receipt(execution,o,root)
 plan={'version':1,'states':[s],'required_assertion_ids':['strip/absence'],'assertions':[{'id':'strip/absence','state':'strip','kind':'control','target':{'identifier':'absent-in-closed-world'},'property':'present','expected':False,'op':'eq'}]}
 evaluated=native_checks.evaluate(plan,o,'ios',root=root)
 passed=proof['complete']==expected_direct and evidence[1]==expected_full and coverage['satisfied']==expected_full
 row={'id':name,'status':'P'if passed else'F','evidence_class':'SIMULATED synthetic native packet with HOST image decode/files','expected_direct':expected_direct,'expected_full':expected_full,'actual_direct':proof['complete'],'actual_full':evidence[1],'coverage_satisfied':coverage['satisfied'],'proof':proof,'state_reason':evidence[2],'evaluated':evaluated,'root':str(root)if root else None,'observation':str(folder/'observation.json'),'observation_sha256':sha(folder/'observation.json'),'arm':a.arm,'provider_sha256':sha(arm/'scripts'/'scroll_coverage.py')}
 save(folder/'proof.json',proof);save(folder/'coverage.json',coverage);save(folder/'evaluated.json',evaluated)
 if not passed:save(ROOT/'first-failures'/(a.arm+'--'+name+'.json'),row)
 results.append(row);print(a.arm+' '+name+': '+row['status'],flush=True)
save(ROOT/'raw'/(a.arm+'-foundation-results.json'),results)
