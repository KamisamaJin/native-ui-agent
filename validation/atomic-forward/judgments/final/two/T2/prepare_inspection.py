from pathlib import Path
import sys,json,hashlib,time,datetime
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
O=B/'judgments/final/two/T2'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks,review_contract,design_contract
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
hashes={}; summaries=[]
for p in sorted((B/'evaluation-inputs/final/T2').glob('*/*/*')):
 rel=p.relative_to(B/'evaluation-inputs/final/T2'); out=O/rel
 D={n:load(p/(n+'.json')) for n in ['inputs','plan','catalog','automatic','environment-check']}
 for f in p.glob('*.json'): hashes[str(f)]=sha(f)
 i=D['inputs']; root=B/i['root']; obs=load(B/i['observation'])
 for f in root.rglob('*'):
  if f.is_file(): hashes[str(f)]=sha(f)
 for f in (B/i['design_root']).rglob('*'):
  if f.is_file(): hashes[str(f)]=sha(f)
 source=B/i['source_capsule']
 for f in source.rglob('RiverSensorTriageBoard.*'): hashes[str(f)]=sha(f)
 states={}
 for state in D['plan']['states']:
  found,complete,why,capture=native_checks.bound_state_evidence(obs,state)
  states[state['id']]={'state':state,'indices':[j for j,s in found],'complete':complete,'reason':why,'capture':capture,'frames':[{'index':j,'screenshot':s['screenshot'],'sha256':sha(root/s['screenshot']),'binding':s['binding'],'scroll_offset_dp':s.get('scroll_offset_dp'),'runtime':s.get('runtime'),'viewport':s.get('viewport')} for j,s in found]}
 blank={'version':1,'catalog_sha256':D['catalog']['catalog_sha256'],'observation_sha256':i['observation_sha256'],'decisions':[]}
 manual=review_contract.bind(D['plan'],load(B/i['design_root']/'design-lock.json'),i['approval']['design_lock_sha256'],load(B/i['design_root']/'policy.json'),i['approval']['policy_sha256'],obs,i['observation_sha256'],root,blank,i['platform'])
 save(out/'inspection-original.json',{'inputs':i,'state_evidence':states,'native_counts':D['automatic']['counts'],'environment_status':D['environment-check']['status'],'pixel_and_blank_findings':manual['review_contract']['findings'],'all_snapshot_count':len(obs['snapshots']),'steps':obs['steps'],'events':obs['events']})
 summaries.append({'case':str(rel),'snapshot_count':len(obs['snapshots']),'states':{k:{x:v[x] for x in ['indices','complete','reason']} for k,v in states.items()},'pixel_statuses':[{k:f[k] for k in ['id','status','snapshot_indices','reason']} for f in manual['review_contract']['findings'] if f['aspect'] in ['rendered_canvas','rendered_fill']]})
save(O/'input-hashes.json',hashes)
save(O/'inspection-index.json',summaries)
for s in summaries:
 print(s['case'],'snapshots',s['snapshot_count'],'coverage',[(k,len(v['indices']),v['complete']) for k,v in s['states'].items()],'pixel F',[(r['id'],r['snapshot_indices']) for r in s['pixel_statuses'] if r['status']=='failed'])
