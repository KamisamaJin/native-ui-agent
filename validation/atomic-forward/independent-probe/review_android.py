import json,hashlib,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;S=R.parents[2]/'native-ui-agent/scripts';a=json.loads((R/'APPROVAL.json').read_text())
for scenario in ['normal','narrow-large']:
 key='android-'+scenario;outputkey=key+'-v2';g=R/'generated'/key;cap=R/'captures'/outputkey;cat=json.loads((g/'catalog.json').read_text());obs=json.loads((cap/'observation.json').read_text())
 reasons={'text-wrap':{'normal':'Original full frame shows the complete title and two-line body. No glyph clipping or ellipsis is visible.','narrow-large':'Original full frame shows the title wrapped onto two lines and the complete body naturally wrapped into five lines (tapped) or four lines (changed). No glyph clipping or ellipsis is visible.'},'text-overlap':{'normal':'Original full frame shows a clear vertical gap between the band, title, body and Acknowledge action.','narrow-large':'Original full frame shows distinct gaps between the taller wrapped title/body, the accent band and the action; text does not cross those regions.'}}
 decisions=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  indices=next(s['snapshot_indices']for s in obs['state_captures']if s['state_id']==row['state'])
  decisions.append({'review_id':row['review_id'],'actual':True,'reason':reasons[row['requirement_id']][scenario],'snapshot_indices':indices})
 sub={'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':hashlib.sha256((cap/'observation.json').read_bytes()).hexdigest(),'decisions':decisions}
 dest=R/'submissions';dest.mkdir(exist_ok=True);f=dest/f'{outputkey}.json';f.write_text(json.dumps(sub,indent=2)+'\n')
 cmd=[sys.executable,str(S/'review_contract.py'),'review','--plan',str(g/'plan.json'),'--design-lock',str(R/'design/lock.json'),'--design-sha256',a['design_lock_sha256'],'--policy',str(R/'design/policy.json'),'--policy-sha256',a['policy_sha256'],'--platform','android','--observation',str(cap/'observation.json'),'--submission',str(f),'--output',str(R/'reviews'/outputkey)]
 p=subprocess.run([sys.executable,str(R/'run.py')]+cmd)
 if p.returncode:print('REVIEW EXIT',p.returncode)
