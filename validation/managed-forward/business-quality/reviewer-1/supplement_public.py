from inspect_public import *

def run():
 regions=json.loads((OUT/'public-target-region-index.json').read_text());extras=[];samples=[]
 for arm in ['A','B']:
  for stage in ['D0','Final']:
   b=PACKET/f'native/{arm}/public/{stage}/ios';obs=json.loads((b/'native/observation.json').read_text())
   for cap in obs['state_captures']:
    if cap['state_id'] not in ['draft','replacement','quantityChanged','ready','sent','revised','readyRevised','sentRevised']:continue
    # Retain each revised option as its own original, fully visible card region.
    if cap['state_id'] in ['revised','readyRevised','sentRevised']:
     for tag in ['menu.option.roast','menu.option.lentil','menu.option.pasta']:
      found=False
      for ix in cap['snapshot_indices']:
       s=obs['snapshots'][ix];ns=[n for n in s['nodes'] if n.get('identifier')==tag]
       if len(ns)!=1 or not ns[0].get('fully_within_viewport'):continue
       n=ns[0];r=rect(n,'ios');box=[r['x'],r['y'],r['x']+r['width'],r['y']+r['height']];q=b/'native'/s['screenshot']
       extras.append({'cohort':f'{arm}/{stage}/ios','candidate':'initial' if stage=='D0' else arm,'platform':'ios','state':cap['state_id'],'kind':'options-individual','target':tag,'snapshot':ix,'path':str(q.relative_to(PACKET)),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'binding':s['binding'],**crop_hash(q,box)});found=True;break
      assert found,(arm,stage,cap['state_id'],tag)
    # Independently sample the frozen exact send region without changing its thresholds.
    for ix in cap['snapshot_indices']:
     s=obs['snapshots'][ix];ns=[n for n in s['nodes'] if n.get('identifier')=='menu.submit']
     if len(ns)!=1 or not ns[0].get('fully_within_viewport'):continue
     r=rect(ns[0],'ios');uv=[.025,.3,.045,.7];box=[r['x']+r['width']*uv[0],r['y']+r['height']*uv[1],r['x']+r['width']*uv[2],r['y']+r['height']*uv[3]];q=b/'native'/s['screenshot']
     w,h,k,rows,chunks=png(str(q));x1,y1,x2,y2=[math.ceil(box[0]),math.ceil(box[1]),math.floor(box[2]),math.floor(box[3])];colors=collections.Counter(tuple(row[x*k:x*k+3]) for row in rows[y1:y2] for x in range(x1,x2));total=sum(colors.values());e=(33,107,74) if cap['state_id'] in ['ready','readyRevised'] else (217,226,220);supported=sum(v for rgb,v in colors.items() if max(abs(a-b) for a,b in zip(rgb,e))<=1)
     samples.append({'cohort':f'{arm}/{stage}/ios','candidate':'initial' if stage=='D0' else arm,'state':cap['state_id'],'assertion_id':cap['state_id']+'/send-fill','snapshot':ix,'path':str(q.relative_to(PACKET)),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'target_image_box':r,'sample_px':[x1,y1,x2,y2],'pixels':total,'approved_expected_rgb':e,'expected_ref':{'path':'design/public/reference.json','pointer':'/expected/'+cap['state_id']+'/send-fill'},'approved_thresholds':{'minimum_pixels':12,'minimum_support':.9,'channel_tolerance':1},'mode_rgb':colors.most_common(1)[0][0],'mode_count':colors.most_common(1)[0][1],'support':supported/total,'observed_argb':'#FF'+''.join(f'{v:02X}' for v in colors.most_common(1)[0][0]),'result':'P' if total>=12 and supported/total>=.9 else 'F','sRGB_png': 'sRGB' in chunks});break
   print('supplement',arm,stage,flush=True)
 (OUT/'public-option-fragments.json').write_text(json.dumps(extras,indent=2)+'\n');(OUT/'public-send-independent-pixel-check.json').write_text(json.dumps(samples,indent=2)+'\n')
 groups=collections.defaultdict(list)
 for r in extras:groups[(r['target'],r['crop_sha256'])].append(r)
 gs=[{'group':i,'representative':rs[0],'members':rs} for i,rs in enumerate(groups.values())]
 (OUT/'public-option-fragment-groups.json').write_text(json.dumps(gs,indent=2)+'\n')
 print('option groups',[(r['group'],r['representative']['target'],r['representative']['cohort'],r['representative']['state'],r['representative']['snapshot']) for r in gs]);print('send',[(r['cohort'],r['state'],r['observed_argb'],r['result']) for r in samples])
if __name__=='__main__':run()
