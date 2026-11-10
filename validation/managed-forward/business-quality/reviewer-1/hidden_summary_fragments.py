from inspect_hidden_finals import *
regs=json.loads((OUT/'hidden-finals-target-regions.json').read_text());res=[]
for m in regs:
 if not m.get('unavailable') or m['target']!='menu.summary':continue
 b=H/m['candidate']/m['platform'];o=json.loads((b/'native/observation.json').read_text());plat=m['platform'];ins=[]
 for ix in m['coverage_snapshot_indices']:
  s=o['snapshots'][ix];n=next(n for n in s['nodes'] if n.get('identifier')=='menu.summary')
  if not n.get('intersects_viewport'):continue
  r=rect(n,plat)
  if plat=='ios':
   v=s['viewport'];a=s['app_frame'];scale=s['screenshot_pixels']['width']/a['width'];vp=[(v['x']-a['x'])*scale,(v['y']-a['y'])*scale,(v['x']+v['width']-a['x'])*scale,(v['y']+v['height']-a['y'])*scale]
  else:vp=[0,0,s['screenshot_pixels']['width'],s['screenshot_pixels']['height']]
  box=[max(r['x'],vp[0]),max(r['y'],vp[1]),min(r['x']+r['width'],vp[2]),min(r['y']+r['height'],vp[3])]
  if box[3]-box[1]<min(r['height']*.3,200):continue
  q=b/'native'/s['screenshot'];x={'candidate':m['candidate'],'platform':plat,'state':m['state'],'scope':'private','target':'menu.summary.fragment','snapshot':ix,'path':str(q.relative_to(H)),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'binding':s['binding'],'coverage_snapshot_indices':m['coverage_snapshot_indices'],'fragment_vertical_interval':[max(0,vp[1]-r['y']),min(r['height'],vp[3]-r['y'])],'target_full_height_px':r['height'],**crop_hash(q,box)};res.append(x);ins.append(x['fragment_vertical_interval'])
 print(m['candidate'],plat,m['state'],ins,flush=True)
(OUT/'hidden-finals-summary-fragments.json').write_text(json.dumps(res,indent=2)+'\n')
g=collections.defaultdict(list)
for r in res:g[(r['platform'],r['crop_sha256'],r['crop_box_px'][2]-r['crop_box_px'][0],r['crop_box_px'][3]-r['crop_box_px'][1])].append(r)
gs=[{'group':i,'representative':rs[0],'members':rs} for i,rs in enumerate(g.values())];(OUT/'hidden-finals-summary-fragment-groups.json').write_text(json.dumps(gs,indent=2)+'\n');print('groups',[(x['group'],x['representative']['platform'],x['representative']['state'],x['representative']['snapshot'],len(x['members'])) for x in gs])
