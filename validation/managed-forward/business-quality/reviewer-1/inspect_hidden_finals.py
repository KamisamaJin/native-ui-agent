from inspect_public import *
H=PACKET.parent/'packet-hidden-finals'
STATES=['draft','replacement','quantityChanged','ready','sent','revised','readyRevised','sentRevised']
def run():
 regions=[];bindings=[];fullread=[]
 idx=json.loads((PACKET/'SOURCE-INDEX.json').read_text())
 for cand in ['A','B']:
  for plat in ['ios','android']:
   b=H/cand/plat;obs=json.loads((b/'native/observation.json').read_text());req=json.loads((b/'review-request.json').read_text());catalog=json.loads((PACKET/f'design/private/compiled/evening-service/{plat}/catalog.json').read_text());plan=json.loads((PACKET/f'design/private/compiled/evening-service/{plat}/plan.json').read_text());nativeplan=json.loads((b/'parent-plan.json').read_text());before=json.loads((b/'source-before.json').read_text());after=json.loads((b/'source-after.json').read_text());execution=json.loads((b/'execution.json').read_text());bridge=PACKET/'design/private'/('Bridge.swift' if plat=='ios' else 'ObserverBridge.kt');srcsha=idx[cand][plat]['sha256']
   bindings.append({'candidate':cand,'platform':plat,'source_identity':idx[cand][plat],'subject_source_matches':srcsha in [v for k,v in before.items() if k.endswith('MenuChangeReviewPanel.swift' if plat=='ios' else 'MenuChangeReviewPanel.kt')],'all_source_stable':before==after,'execution_bridge_matches_fixed':execution['bridge_sha256']==hashlib.sha256(bridge.read_bytes()).hexdigest(),'native_plan_matches_fixed':nativeplan==plan,'request_catalog_matches_fixed':req['catalog']==catalog,'submission_template_headers':{k:v for k,v in req['submission_template'].items() if k!='decisions'},'observation_file_sha256':hashlib.sha256((b/'native/observation.json').read_bytes()).hexdigest(),'capture_sha256':req['capture_sha256'],'source_claims_treated_as_actuals':False})
   for cap in obs['state_captures']:
    st=cap['state_id']
    if st not in STATES:continue
    for ix in cap['snapshot_indices']:
     s=obs['snapshots'][ix];q=b/'native'/s['screenshot'];fullread.append({'candidate':cand,'platform':plat,'state':st,'snapshot':ix,'path':str(q.relative_to(H)),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'binding':s['binding'],'capture_consistent':s['capture_consistent'],'full_sweep_complete':cap['complete']})
    targets=['menu.title','@heading','menu.option.chickpea','menu.option.aubergine','menu.option.barley','menu.summary','menu.submit','menu.notes.last']
    for target in targets:
     chosen=None
     for ix in cap['snapshot_indices']:
      s=obs['snapshots'][ix];nodes=[n for n in s['nodes'] if (n.get('label')=='Choose a replacement' if target=='@heading' else n.get('identifier')==target)]
      if len(nodes)!=1 or not nodes[0].get('fully_within_viewport' if plat=='ios' else 'fully_visible'):continue
      n=nodes[0];r=rect(n,plat);box=[r['x'],r['y'],r['x']+r['width'],r['y']+r['height']];q=b/'native'/s['screenshot']
      chosen={'candidate':cand,'platform':plat,'scope':'private','state':st,'target':target,'snapshot':ix,'path':str(q.relative_to(H)),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'binding':s['binding'],'capture_complete':cap['complete'],'coverage_snapshot_indices':cap['snapshot_indices'],**crop_hash(q,box)};regions.append(chosen);break
     if chosen is None:regions.append({'candidate':cand,'platform':plat,'state':st,'target':target,'unavailable':True,'coverage_snapshot_indices':cap['snapshot_indices']})
   print('hidden indexed',cand,plat,flush=True)
 (OUT/'hidden-finals-target-regions.json').write_text(json.dumps(regions,indent=2)+'\n');(OUT/'hidden-finals-binding-checks.json').write_text(json.dumps(bindings,indent=2)+'\n');(OUT/'hidden-finals-original-image-index.json').write_text(json.dumps(fullread,indent=2)+'\n')
 groups=collections.defaultdict(list)
 for r in regions:
  if 'crop_sha256' in r:groups[(r['platform'],r['target'],r['crop_box_px'][2]-r['crop_box_px'][0],r['crop_box_px'][3]-r['crop_box_px'][1],r['crop_sha256'])].append(r)
 gs=[{'group':i,'representative':rs[0],'members':rs} for i,rs in enumerate(groups.values())];(OUT/'hidden-finals-target-groups.json').write_text(json.dumps(gs,indent=2)+'\n')
 print('unique',len(gs),'unavailable',[(r['candidate'],r['platform'],r['state'],r['target']) for r in regions if r.get('unavailable')]);print([(r['group'],r['representative']['platform'],r['representative']['target'],r['representative']['state'],r['representative']['snapshot'],len(r['members'])) for r in gs])
 print('bindingchecks',[{k:v for k,v in x.items() if isinstance(v,bool)} for x in bindings])
if __name__=='__main__':run()
