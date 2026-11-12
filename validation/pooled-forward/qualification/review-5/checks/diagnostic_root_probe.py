from foundation_cases import *
import argparse
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import native_checks,locator_diagnostics
folder=ROOT/'work'/a.arm/'diagnostic-original-root';folder.mkdir();production=folder/'production';production.mkdir();(production/'Neutral.swift').write_text('// Neutral source occurrence: leaf-a\n')
o=json.loads((ROOT/'fixtures'/'pristine'/'observation.json').read_text());state=json.loads((ROOT/'fixtures'/'pristine'/'state.json').read_text());images=ROOT/'fixtures'/'pristine'/'images'
plan={'version':1,'states':[state],'design_contract':{'platform':'ios'},'assertions':[{'id':'strip/anchor','state':'strip','kind':'control','target':{'identifier':'leaf-a'},'property':'label','expected':'B','op':'eq'}]};report={'assertions':[{'id':'strip/anchor','state':'strip','status':'failed','reason':'SIMULATED mismatch routes a known closed-strip finding'}]}
full=native_checks.bound_state_evidence(o,state,images)[1];without_sources=locator_diagnostics.diagnose(plan,report,o,[],root=images);with_sources=locator_diagnostics.diagnose(plan,report,o,[str(production)],root=images)
passed=full and without_sources['items'][0]['full_content_complete']and with_sources['items'][0]['full_content_complete']
row={'id':'I01-diagnostic-original-root-survives-production-scan','status':'P'if passed else'F','evidence_class':'HOST file reads with SIMULATED native packet','arm':a.arm,'original_image_root':str(images),'production_root':str(production),'direct_bound_complete':full,'diagnosis_without_source_scan':without_sources,'diagnosis_with_source_scan':with_sources}
save(folder/'result.json',row);save(ROOT/'raw'/(a.arm+'-diagnostic-root-result.json'),row)
if not passed:save(ROOT/'first-failures'/(a.arm+'--diagnostic-root.json'),row)
print(a.arm+' I01-diagnostic-original-root-survives-production-scan: '+row['status'])
