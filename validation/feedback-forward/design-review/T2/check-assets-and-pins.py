import hashlib,json,re,sys,time,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');O=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'validation/feedback-forward/candidate-v9/scripts'))
import design_contract as d
from PIL import Image
start=time.time();result={'scopes':{},'static_references':[]}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
normal=lambda s:' '.join(s.split())
for scope in ['public','private']:
 p=ROOT/'validation/feedback-forward/design/T2'/scope;r=d.load(p/'reference.json');a=d.load(p/'approval.json');lock=d.load(p/'design-lock.json');policy=d.load(p/'policy.json')
 seal=d.load(p/'SEAL.json')['files'];fail=[]
 for rel,expected in seal.items():
  assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
  path=p/rel
  if not path.is_file() or sha(path)!=expected:fail.append(rel)
 assert not fail,fail
 assert d.digest(lock)==a['design_lock_sha256']
 assert d.digest(policy)==a['policy_sha256']
 assert d.digest(d.load(p/'routes.json'))==a['routes_sha256']
 assert d.digest(d.load(p/'implementation-audit.json'))==a['implementation_audit_sha256']
 assert d.digest(d.load(p/'compatibility.json'))==a['compatibility_sha256']
 assert sha(ROOT/'validation/feedback-forward/check_minimum_api.py')==a['minimum_source_api_checker_sha256']
 for case in lock['contract']['scenarios']:
  f=d.load(p/'cases'/case/'fixtures.json');models=[f['initial'],*f['updates']]
  assert d.digest(models[0])==r['cases'][case]['original_initial_sha256']
  assert d.digest(models[1])==r['cases'][case]['original_update_sha256']
  for platform,bridge in [('ios','Bridge.swift'),('android','ObserverBridge.kt')]:
   assert d.digest(d.load(p/'cases'/case/('environment.'+platform+'.json')))==a['environment_sha256'][case][platform]
   launch=r['launch'][case][platform];assert launch['bridge_sha256']==sha(p/bridge) and launch['fixtures_sha256']==d.digest(f)
  for state in lock['contract']['scenarios'][case]['states']:
   svg=p/'references'/case/(state['id']+'.svg');png=svg.with_suffix('.png');root=E.parse(svg).getroot()
   with Image.open(png) as im:assert im.size==(int(root.attrib['width']),int(root.attrib['height']))
   texts=[normal(''.join(t.itertext()))for t in root.iter()if t.tag.endswith('text')];joined=normal(' '.join(texts));s=r['cases'][case]['states'][state['id']]
   for key in ['title','subtitle','status','disclosure','choice','primary']:assert normal(s[key]['value']) in joined,(case,state['id'],key)
   model=models[state['input_index']]
   if s['open']['value']:
    cursor=0
    for chapter in model['chapters']:
     for key in ['title','body']:
      needle=normal(chapter[key]);at=joined.find(needle,cursor);assert at>=0,(case,state['id'],chapter['id'],key);cursor=at+len(needle)
   result['static_references'].append({'scope':scope,'case':case,'state':state['id'],'svg_sha256':sha(svg),'png_sha256':sha(png),'copy_and_order_matches':True,'raster_vector_dimensions_match':True,'native_style_certified':False})
 result['scopes'][scope]={'seal_files_verified':len(seal),'original_model_object_sha_verified':True,'all_approval_digests_match':True,'state_count':len(r['state_definitions']),'status_leading_property':next(x['property']for x in lock['contract']['rules']if x['id']=='status-leading-inset'),'leading_strip':next(x['sampling']for x in policy['atoms']if x['rule_id']=='status-leading-clear')}
result.update(startedAtUnix=start,finishedAtUnix=time.time(),scope='Independent static asset/pin consistency only; all actual native measurements and render judgments remain unverified.')
(O/'assets-and-pins.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'scopes':result['scopes'],'static_reference_pairs':len(result['static_references'])},indent=2))
