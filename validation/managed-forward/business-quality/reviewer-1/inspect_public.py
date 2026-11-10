from pathlib import Path
import json,hashlib,struct,zlib,collections,math,functools
PACKET=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/packet-public')
OUT=PACKET.parent/'reviewer-1'
@functools.lru_cache(maxsize=3)
def png(path):
 b=Path(path).read_bytes();i=8;ds=[];chunks=[]
 while i<len(b):
  n,=struct.unpack('>I',b[i:i+4]);t=b[i+4:i+8];v=b[i+8:i+8+n];chunks.append(t.decode())
  if t==b'IHDR':w,h,bd,ct,_,_,inter=struct.unpack('>IIBBBBB',v)
  if t==b'IDAT':ds.append(v)
  i+=n+12
 assert bd==8 and inter==0 and ct in (2,6)
 k=3 if ct==2 else 4;s=w*k;r=zlib.decompress(b''.join(ds));prev=bytearray(s);rows=[]
 for y in range(h):
  start=y*(s+1);f=r[start];v=bytearray(r[start+1:start+s+1])
  if f==1:
   for x in range(k,s):v[x]=(v[x]+v[x-k])&255
  elif f==2:v=bytearray((a+b)&255 for a,b in zip(v,prev))
  elif f==3:
   for x in range(s):v[x]=(v[x]+((v[x-k] if x>=k else 0)+prev[x])//2)&255
  elif f==4:
   for x in range(s):
    a=v[x-k] if x>=k else 0;b=prev[x];c=prev[x-k] if x>=k else 0;t=a+b-c;pa=abs(t-a);pb=abs(t-b);pc=abs(t-c)
    v[x]=(v[x]+(a if pa<=pb and pa<=pc else b if pb<=pc else c))&255
  else:assert f==0
  rows.append(bytes(v));prev=v
 return w,h,k,rows,chunks

def rect(node,plat):
 if plat=='ios':return node['image_frame']
 x1,y1,x2,y2=node['image_bounds_px'];return {'x':x1,'y':y1,'width':x2-x1,'height':y2-y1}
def crop_hash(path,box):
 w,h,k,rows,chunks=png(str(path));x1,y1,x2,y2=box;x1=max(0,math.ceil(x1));y1=max(0,math.ceil(y1));x2=min(w,math.floor(x2));y2=min(h,math.floor(y2))
 digest=hashlib.sha256()
 for row in rows[y1:y2]:digest.update(row[x1*k:x2*k])
 return {'crop_box_px':[x1,y1,x2,y2],'crop_sha256':digest.hexdigest(),'png_color_type':k,'png_chunks':chunks[:8]}

def process():
 regions=[];cohorts=[]
 for arm in ['A','B']:
  for stage in ['D0','Final']:
   for plat in ['ios','android']:
    b=PACKET/f'native/{arm}/public/{stage}/{plat}';obs=json.loads((b/'native/observation.json').read_text());auto=json.loads((b/'automatic.json').read_text())
    src=json.loads((b/'source-before.json').read_text());after=json.loads((b/'source-after.json').read_text())
    source={k:v for k,v in src.items() if k.endswith('MenuChangeReviewPanel.swift') or k.endswith('MenuChangeReviewPanel.kt')}
    cohorts.append({'cohort':f'{arm}/{stage}/{plat}','source':source,'source_stable':src==after,'automatic_counts':auto['counts'],'failed_ids':auto['failed_assertion_ids'],'unassessed_ids':[x['id'] for x in auto['assertions'] if x['status']=='unassessed']})
    for cap in obs['state_captures']:
     state=cap['state_id']
     if state not in ['draft','replacement','quantityChanged','ready','sent','revised','readyRevised','sentRevised']:continue
     for kind in ['title','options','summary','send']:
      chosen=None
      for ix in cap['snapshot_indices']:
       s=obs['snapshots'][ix];nd={n.get('identifier'):n for n in s['nodes'] if n.get('identifier')}
       ids=['menu.title'] if kind=='title' else ['menu.option.roast','menu.option.lentil','menu.option.pasta'] if kind=='options' else ['menu.summary'] if kind=='summary' else ['menu.submit']
       if not all(n in nd and nd[n].get('fully_within_viewport' if plat=='ios' else 'fully_visible') for n in ids):continue
       rr=[rect(nd[n],plat) for n in ids]
       if kind=='title':
        # Include the following section heading up to the first option, to support hierarchy.
        op=rect(nd['menu.option.roast'],plat)
        rr.append({'x':rr[0]['x'],'y':rr[0]['y'],'width':rr[0]['width'],'height':op['y']-rr[0]['y']})
       box=[min(r['x'] for r in rr),min(r['y'] for r in rr),max(r['x']+r['width'] for r in rr),max(r['y']+r['height'] for r in rr)]
       path=b/'native'/s['screenshot'];selected={'cohort':f'{arm}/{stage}/{plat}','candidate':'initial' if stage=='D0' else arm,'platform':plat,'state':state,'kind':kind,'snapshot':ix,'path':str(path.relative_to(PACKET)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'binding':s['binding'],'capture_complete':cap['complete'],**crop_hash(path,box)}
       regions.append(selected);chosen=selected;break
      if not chosen:regions.append({'cohort':f'{arm}/{stage}/{plat}','candidate':'initial' if stage=='D0' else arm,'platform':plat,'state':state,'kind':kind,'unavailable':True})
    print('processed',arm,stage,plat,flush=True)
 (OUT/'public-target-region-index.json').write_text(json.dumps(regions,indent=2)+'\n');(OUT/'public-cohort-identity.json').write_text(json.dumps(cohorts,indent=2)+'\n')
 groups=collections.defaultdict(list)
 for r in regions:
  if 'crop_sha256' in r:groups[(r['platform'],r['kind'],tuple([r['crop_box_px'][2]-r['crop_box_px'][0],r['crop_box_px'][3]-r['crop_box_px'][1]]),r['crop_sha256'])].append(r)
 group_rows=[]
 for i,(k,rs) in enumerate(groups.items()):
  row={'group':i,'platform':k[0],'kind':k[1],'representative':rs[0],'members':[{'cohort':r['cohort'],'state':r['state'],'snapshot':r['snapshot'],'sha256':r['sha256']} for r in rs]};group_rows.append(row)
 (OUT/'public-target-region-groups.json').write_text(json.dumps(group_rows,indent=2)+'\n')
 print('regions',len(regions),'unique',len(groups));print([(g['group'],g['platform'],g['kind'],g['representative']['cohort'],g['representative']['state'],len(g['members'])) for g in group_rows])
if __name__=='__main__':process()
