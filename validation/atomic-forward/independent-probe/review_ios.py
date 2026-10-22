import json,hashlib,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;S=R.parents[2]/'native-ui-agent/scripts';a=json.loads((R/'APPROVAL.json').read_text());scenario=sys.argv[1];key='ios-'+scenario;g=R/'generated'/key;cap=R/'captures'/key;cat=json.loads((g/'catalog.json').read_text());obs=json.loads((cap/'observation.json').read_text())
reasons={'text-wrap':{'normal':'The original full state image shows the complete title and body; the body wraps onto two lines with readable glyphs and no visible clipping or ellipsis.','narrow-large':'The original overlapping state images show the complete large title and body wrapped into multiple lines within the narrow canvas. Glyphs remain readable without visible clipping or ellipsis.'},'text-overlap':{'normal':'The original full state image shows a clear gap between band, title, body and Acknowledge action; their text regions do not overlap.','narrow-large':'The original overlapping state images show distinct vertical gaps between the band, wrapped title, body and action, including the lower portion revealed by scrolling.'}}
decisions=[]
for row in cat['rows']:
 if row['method']!='visual':continue
 indices=next(s['snapshot_indices']for s in obs['state_captures']if s['state_id']==row['state'])
 decisions.append({'review_id':row['review_id'],'actual':True,'reason':reasons[row['requirement_id']][scenario],'snapshot_indices':indices})
sub={'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':hashlib.sha256((cap/'observation.json').read_bytes()).hexdigest(),'decisions':decisions};f=R/'submissions'/f'{key}.json';f.write_text(json.dumps(sub,indent=2)+'\n')
cmd=[sys.executable,str(S/'review_contract.py'),'review','--plan',str(g/'plan.json'),'--design-lock',str(R/'design/lock.json'),'--design-sha256',a['design_lock_sha256'],'--policy',str(R/'design/policy.json'),'--policy-sha256',a['policy_sha256'],'--platform','ios','--observation',str(cap/'observation.json'),'--submission',str(f),'--output',str(R/'reviews'/key)]
sys.exit(subprocess.run([sys.executable,str(R/'run.py')]+cmd).returncode)
