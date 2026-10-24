import sys
sys.dont_write_bytecode=True
import json,hashlib,pathlib,math
from PIL import Image,ImageDraw
BASE=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=BASE/'judgments/final/two/T2'
sys.path.insert(0,str(BASE/'candidate-v9/scripts'))
import native_checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={};summary={}
for p in sorted((BASE/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(p.parts[-3:]); i=json.loads((p/'inputs.json').read_text());a=json.loads((p/'automatic.json').read_text());plan=json.loads((p/'plan.json').read_text());c=json.loads((p/'catalog.json').read_text());o=json.loads((BASE/i['observation']).read_text()); env=json.loads((p/'environment-check.json').read_text())
 out=OUT/key;out.mkdir(parents=True,exist_ok=True)
 evidence={s['id']:{'indices':[j for j,_ in native_checks.bound_state_evidence(o,s)[0]],'complete':native_checks.bound_state_evidence(o,s)[1],'reason':native_checks.bound_state_evidence(o,s)[2]} for s in plan['states']}
 uniq={};frames=[]
 for j,s in enumerate(o['snapshots']):
  f=BASE/i['raw']/s['screenshot'];h=sha(f)
  item={'index':j,'state':s.get('state_id'),'path':str(f.relative_to(BASE)),'sha256':h,'binding':s.get('binding'),'capture_consistent':s.get('capture_consistent'),'scroll_offset_dp':s.get('scroll_offset_dp'),'viewport':s.get('viewport'),'content_frame':s.get('runtime',{}).get('content_frame')}
  frames.append(item)
  if h not in uniq:uniq[h]={'representative':item,'same_pixels':[]}
  uniq[h]['same_pixels'].append(j)
 v=list(uniq.values());pages=[]
 for pg in range(math.ceil(len(v)/8)):
  selected=v[pg*8:(pg+1)*8]; sheet=Image.new('RGB',(1600,1264),'#eeeeee');d=ImageDraw.Draw(sheet)
  for k,u in enumerate(selected):
   f=u['representative'];im=Image.open(BASE/f['path']).convert('RGB');im=im.resize((400,600),Image.Resampling.LANCZOS);x=(k%4)*400;y=(k//4)*632
   d.text((x+3,y+3),f"{key} idx {f['index']} {f['state']}",fill='black');d.text((x+3,y+16),f"same {u['same_pixels']}",fill='black');sheet.paste(im,(x,y+32))
  dest=out/f'sheet-{pg+1:02}.png';sheet.save(dest);pages.append({'sheet':str(dest.relative_to(OUT)),'frames':selected})
 manifest[key]={'observation_sha256':i['observation_sha256'],'frames':frames,'pages':pages}
 steps=[]
 for j,s in enumerate(o.get('steps',[])):
  steps.append({k:s.get(k) for k in ['type','selector','outcome','callback_delta','dispatch','binding_after','snapshot','immediate_after'] if k in s})
 summary[key]={'inputs':{k:v for k,v in i.items() if k not in ['original_files','approval']},'automatic_counts':a['counts'],'environment_status':env['status'],'evidence':evidence,'steps':steps,'events':o.get('events'),'states':a['states'],'snapshot_count':len(frames),'unique_image_count':len(v),'all_input_sha_mismatches':[str(f) for f,h in i['original_files'].items() if not (BASE/f).is_file() or sha(BASE/f)!=h]}
(OUT/'image-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'inspection-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{'snapshots':v['snapshot_count'],'unique':v['unique_image_count'],'states':v['evidence'],'sha_mismatches':v['all_input_sha_mismatches']} for k,v in summary.items()},ensure_ascii=False,indent=2))
