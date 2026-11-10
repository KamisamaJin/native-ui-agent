from inspect_public import *
R=PACKET.parent
ref=json.loads((PACKET/'design/private/reference.json').read_text());out=[]
for cand,root in [('initial',R/'packet-initial-hidden'),('A',R/'packet-hidden-finals'),('B',R/'packet-hidden-finals')]:
 b=root/cand/'ios';obs=json.loads((b/'native/observation.json').read_text())
 for cap in obs['state_captures']:
  st=cap['state_id']
  if st not in ['draft','replacement','quantityChanged','ready','sent','revised','readyRevised','sentRevised']:continue
  for ix in cap['snapshot_indices']:
   s=obs['snapshots'][ix];ns=[n for n in s['nodes'] if n.get('identifier')=='menu.submit']
   if len(ns)!=1 or not ns[0]['fully_within_viewport']:continue
   r=rect(ns[0],'ios');q=b/'native'/s['screenshot'];w,h,k,rows,chunks=png(str(q));uv=[.025,.3,.045,.7];x1,y1,x2,y2=[math.ceil(r['x']+r['width']*uv[0]),math.ceil(r['y']+r['height']*uv[1]),math.floor(r['x']+r['width']*uv[2]),math.floor(r['y']+r['height']*uv[3])];c=collections.Counter(tuple(row[x*k:x*k+3]) for row in rows[y1:y2] for x in range(x1,x2));total=sum(c.values());expected=ref['expected'][st]['send-fill']['value'];e=tuple(int(expected[i:i+2],16) for i in [3,5,7]);support=sum(v for rgb,v in c.items() if max(abs(a-b) for a,b in zip(rgb,e))<=1)/total;out.append({'candidate':cand,'scope':'private','platform':'ios','state':st,'assertion_id':st+'/send-fill','path':str(q.relative_to(root)),'packet':root.name,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'snapshot':ix,'binding':s['binding'],'source_sha256':json.loads((PACKET/'SOURCE-INDEX.json').read_text())[cand]['ios']['sha256'],'expected_ref':{'path':'packet-public/design/private/reference.json','pointer':'/expected/'+st+'/send-fill'},'approved_expected':expected,'observed_argb':'#FF'+''.join(f'{v:02X}' for v in c.most_common(1)[0][0]),'mode_count':c.most_common(1)[0][1],'pixels':total,'support':support,'sample_px':[x1,y1,x2,y2],'target_image_box':r,'approved_region':uv,'approved_thresholds':{'minimum_pixels':12,'minimum_support':.9,'channel_tolerance':1},'sRGB_png':'sRGB' in chunks,'status':'P' if total>=12 and support>=.9 else 'F'});break
 print(cand,'send checked',flush=True)
(OUT/'hidden-send-independent-pixel-check.json').write_text(json.dumps(out,indent=2)+'\n');print([(r['candidate'],r['state'],r['observed_argb'],r['status']) for r in out])
