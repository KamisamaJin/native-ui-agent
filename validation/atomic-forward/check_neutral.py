#!/usr/bin/env python3
import json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'development/native-v8-attempt1/scripts'))
import design_contract as d,review_contract as review,native_checks as n,native_pixels,acceptance

def main():
 root=R/'neutral/design';lock=d.load(root/'lock.json');policy=d.load(root/'policy.json');approval=d.load(root/'approval.json');rows=[]
 for pl in ['ios','android']:
  plan,_=d.compile_contract(lock,approval['design_lock_sha256'],'neutral',pl,d.load(root/'bindings.json'),d.load(root/'actions.json'))
  cat=review.catalog(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],pl)
  for case in ['N1','N2']:
   raw=R/'neutral-evidence'/pl/case;op=raw/'observation.json';obs=d.load(op);out=R/'neutral-checks'/pl/case;assert not out.exists();out.mkdir(parents=True)
   req={'version':1,'catalog_sha256':d.digest(cat),'observation_sha256':native_pixels.sha(op),'decisions':[]}
   m=review.bind(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],obs,req['observation_sha256'],raw,req,pl)
   report=n.evaluate(plan,obs,pl,m,raw,req['observation_sha256'],lock,approval['design_lock_sha256'],policy,approval['policy_sha256'])
   env=acceptance.environment(obs,d.load(R/'neutral'/case/('environment.'+pl+'.json')),pl)
   for name,value in [('plan.json',plan),('manual.json',m),('report.json',report),('environment.json',env)]: (out/name).write_text(json.dumps(value,indent=2)+'\n')
   rows.append({'platform':pl,'case':case,'counts':report['counts'],'environment':env['status'],'pixels':[{k:f[k]for k in ['id','status','expected','unit','responsibility']}for f in m['review_contract']['findings']if f['aspect'].startswith('rendered_')], 'coverage':report['states']})
 (R/'neutral-summary.json').write_text(json.dumps({'finishedAtUnix':time.time(),'scope':'Actual neutral native observations. Qualitative review intentionally unsubmitted; no product defect denominator. Strict sampling F/U retained.','runs':rows},indent=2)+'\n')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
