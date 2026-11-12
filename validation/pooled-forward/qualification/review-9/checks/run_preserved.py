import sys,argparse
sys.dont_write_bytecode=True
from domain_support import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import native_checks
base=ROOT/'work'/a.arm/'preserved';base.mkdir(parents=True);prior=ROOT.parent/'review-8';oldarm='candidate-v13.7'if a.arm.startswith('candidate')else'baseline-v12.6-common-4';rows=[]
for suffix,group in[('query-scope','query'),('query-additive','query-additive')]:
 for oldrow in load(prior/'raw'/(oldarm+'-'+suffix+'-results.json')):
  name=oldrow['id']
  if name=='ios-complete-no-matches-absence':continue # Original invalid raster-anchor fixture remains sealed; corrected control included below.
  folder=prior/'work'/oldarm/group/name;o=load(folder/'observation.json');plan=load(folder/'plan.json');platform=oldrow['detail']['platform'];native=folder/('native'if platform=='android'else'packet/native');report=native_checks.evaluate(plan,o,platform,root=native);actual=report['assertions'][0]['status'];wanted=oldrow['detail']['expected_status'];row={'id':name,'status':'P'if actual==wanted else'F','arm':a.arm,'evidence_class':'HOST read-only original SIMULATED query packet; no SDK','expected_status':wanted,'actual_status':actual,'complete':report['states']['start']['complete'],'assertion':report['assertions'][0],'original_observation':str(folder/'observation.json'),'original_observation_sha256':sha(folder/'observation.json'),'original_plan_sha256':sha(folder/'plan.json')};rows.append(row);save(base/(name+'.json'),row)
  if row['status']=='F':save(ROOT/'first-failures'/(a.arm+'--preserved--'+name+'.json'),row)
  print(a.arm+' '+name+': '+row['status'],flush=True)
save(ROOT/'raw'/(a.arm+'-preserved-results.json'),rows)
