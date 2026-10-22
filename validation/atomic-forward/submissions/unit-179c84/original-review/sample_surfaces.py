import pathlib,json,collections,math,hashlib
from PIL import Image
root=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
base=root/'own-corpora/unit-179c84/d0';ref=json.loads((root/'design-v2/T3/public/reference.json').read_text());out=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  p=base/platform/case/'observation.json';d=json.loads(p.read_text())
  for state in ['baseline','selected','expanded','blocked','replaced','reselected','submitted']:
   indices=next(x['snapshot_indices'] for x in d['state_captures'] if x['state_id']==state)
   for target in ['submit','notice']:
    for idx in indices:
     s=d['snapshots'][idx];nodes=[n for n in s['nodes'] if n.get('identifier')=='bicycle.'+target and n.get('fully_within_viewport',n.get('fully_visible',False))]
     if len(nodes)!=1:continue
     n=nodes[0];path=base/platform/case/s['screenshot'];im=Image.open(path).convert('RGBA')
     if platform=='ios':
      f=n['frame'];scale=im.width/s['app_frame']['width'];x,y,w,h=[f[k]*scale for k in ['x','y','width','height']]
     else:
      x,y,x2,y2=n['image_bounds_px'];w=x2-x;h=y2-y
     box=[math.ceil(x+w*.025),math.ceil(y+h*.2),math.floor(x+w*.045),math.floor(y+h*.8)]
     hist=collections.Counter(im.crop(box).getdata());rgba,num=hist.most_common(1)[0];actual='#%02X%02X%02X%02X'%(rgba[3],*rgba[:3]);total=sum(hist.values())
     expected=ref['cases'][case]['states'][state]['primaryColor']['value'] if target=='submit' else ref['cases'][case]['colors']['notice']['value']
     out.append({'case':case,'platform':platform,'state':state,'target':target,'snapshot':idx,'originalPNG':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'box_px':box,'pixels':total,'modeARGB':actual,'modeSupport':num/total,'expectedARGB':expected,'exactExpectedSupport':sum(v for c,v in hist.items() if '#%02X%02X%02X%02X'%(c[3],*c[:3])==expected)/total,'policy':'normalized semantic side strip [0.025,0.2,0.045,0.8]; original fully visible target; no tolerance'})
     break
p=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/cache/unit-179c84/agent-output/review/pixel-samples.json');p.write_text(json.dumps(out,indent=2)+'\n')
for x in out:
 if x['modeARGB']!=x['expectedARGB']:print(x['platform'],x['case'],x['state'],x['target'],x['modeARGB'],x['expectedARGB'],x['modeSupport'],x['snapshot'])
print('samples',len(out))
