import sys,argparse,traceback
sys.dont_write_bytecode=True
from encoding_cases import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);args=p.parse_args();arm=Path(args.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import scroll_coverage
rows=[]
for name,expected in CASES:
 folder=ROOT/'work'/args.arm/'geometry'/name;o,s,root,found=make(name,folder)
 proof=scroll_coverage.certify(found,o['state_captures'][0]['binding'],root)
 row={'id':name,'expected_complete':expected,'actual_complete':proof['complete'],'status':'P'if proof['complete']==expected else'F','arm':args.arm,'evidence_class':'HOST PNG/files and SIMULATED native metadata; no SDK/device','proof':proof,'observation':str(folder/'observation.json'),'observation_sha256':sha(folder/'observation.json'),'provider_sha256':sha(arm/'scripts/scroll_coverage.py')}
 save(folder/'proof.json',proof);rows.append(row)
 if row['status']=='F':save(ROOT/'first-failures'/(args.arm+'--geometry--'+name+'.json'),row)
 print(args.arm+' '+name+': '+row['status']+'; '+str(proof.get('reason')),flush=True)
save(ROOT/'raw'/(args.arm+'-geometry-results.json'),rows)
