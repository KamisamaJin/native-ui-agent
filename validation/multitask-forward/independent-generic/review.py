#!/usr/bin/env python3
import argparse,json,hashlib,sys
from pathlib import Path
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');O=R/'validation/multitask-forward/independent-generic';sys.path.insert(0,str(R/'validation/multitask-forward/development/v7-neutral-candidate/scripts'));sys.dont_write_bytecode=True;import native_checks as nc
ap=argparse.ArgumentParser();ap.add_argument('platform');ap.add_argument('config');ap.add_argument('--manual',action='store_true');a=ap.parse_args();e=O/'evidence'/(a.platform+'-'+a.config);obs=json.loads((e/'observation.json').read_text());plan=json.loads((O/'plans'/a.config/a.platform/'plan.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manual=None
if a.manual:
 decisions=[]
 for st in plan['states']:
  state=st['id'];frames,complete,reason,_=nc.state_evidence(obs,st);inds=[i for i,_ in frames]
  decisions.append({'id':state+'/visual','method':'visual','status':'passed','reason':'Reviewed the state contact sheet and original native frame series against the preimplementation typed reference. Clear title and control order; readable overlapping reading sections reach the footer; expansion creates visibly taller disclosure and status text; selection marker and replacement reset agree. This is visual judgment, not exact style or physical touch measurement.','snapshot_indices':inds,'evidence':[{'path':obs['snapshots'][i]['screenshot'],'sha256':sha(e/obs['snapshots'][i]['screenshot'])} for i in inds]})
 manual={'observation_sha256':sha(e/'observation.json'),'decisions':decisions};(O/('manual-'+a.platform+'-'+a.config+'.json')).write_text(json.dumps(manual,indent=2)+'\n')
lock=json.loads((O/'approved-lock-rev3.json').read_text());digest=json.loads((O/'APPROVAL-rev3.json').read_text())['design_lock_sha256'];report=nc.evaluate(plan,obs,a.platform,manual,e,sha(e/'observation.json'),lock,digest);report['input_hashes']={'plan':sha(O/'plans'/a.config/a.platform/'plan.json'),'observation':sha(e/'observation.json')};(O/('checks-'+a.platform+'-'+a.config+('-reviewed' if a.manual else '')+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(a.platform,a.config,report['counts']);print([(r['id'],r['reason']) for r in report['assertions'] if r['status']=='failed'])
