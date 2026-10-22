import sys
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image,ImageDraw
import json,sys
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/one/T2'
sys.path.insert(0,str(B/'candidate-v8/scripts'));from native_checks import bound_state_evidence,resolve
allfacts={}
for d in sorted((B/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(d.parts[-3:]);i=json.loads((d/'inputs.json').read_text());p=json.loads((d/'plan.json').read_text());obs=json.loads((B/i['observation']).read_text());root=B/i['root'];f=json.loads((root/'fixtures.json').read_text());facts={};tiles=[]
 for st in p['states']:
  found,complete,reason,cap=bound_state_evidence(obs,st);fixture=([f['initial']]+f.get('updates',[]))[st['input_index']]
  strings=[fixture[x] for x in ['title','subtitle','notice','footer']]+[it['label'] for it in fixture['incidents']]+[it['unavailableReason'] for it in fixture['incidents'] if not it['available']]
  if st['id'] in ['expanded','blocked']:strings.append(fixture['incidents'][0]['detail'])
  labels=[str(node.get('label','')) for _,s in found for node in s['nodes']]
  targets={}
  for target in ['river.canvas','river.title','river.notice','river.choice.a','river.choice.c','river.disclosure','river.summary','river.submit','river.footer']:
   rows=[]
   for j,s in found:
    rr=resolve(s,{'identifier':target},i['platform']);node=rr.get('control') or rr.get('semantic') or {}
    if node.get('intersects_viewport'):rows.append({'index':j,'resolution':rr.get('resolution'),'label':node.get('label'),'enabled':node.get('enabled'),'selected':node.get('selected'),'frame':node.get('frame') or node.get('unclipped_bounds_dp'),'native_geometry':node.get('native_geometry')})
   targets[target]=rows
  facts[st['id']]={'input_index':st['input_index'],'after_action':st['after_action'],'binding':cap.get('binding'),'complete':complete,'reason':reason,'visible_text_missing_from_native_labels':[text for text in strings if not any(text in label for label in labels)],'targets':targets}
  if st['id'] in ['selected','blocked','replaced','reselected']:
   for j,s in [found[0],found[-1]]:
    im=Image.open(root/s['screenshot']).convert('RGB')
    if i['platform']=='ios':
     vp=s['viewport'];scale=im.width/s['app_frame']['width'];im=im.crop(tuple(round(v*scale) for v in [vp['x'],vp['y'],vp['x']+vp['width'],vp['y']+vp['height']]))
    w=312 if i['platform']=='android' else round(s['viewport']['width']);h=round(im.height*w/im.width);im=im.resize((w,h),Image.Resampling.LANCZOS);tile=Image.new('RGB',(400,h+42),'#ededed');tile.paste(im,((400-w)//2,42));dr=ImageDraw.Draw(tile);dr.text((4,2),key,fill='black');dr.text((4,18),f"{st['id']} original index {j}",fill='black');tiles.append(tile)
 h=max(t.height for t in tiles);sheet=Image.new('RGB',(1600,h*2),'#ccc')
 for n,t in enumerate(tiles):sheet.paste(t,(n%4*400,n//4*h))
 sheet.save(O/key/'transitions.png')
 facts['steps']=[{k:st.get(k) for k in ['type','action','state_id','outcome','dispatch','callback_delta','binding_after','immediate_after']} for st in obs['steps']]
 allfacts[key]=facts
(O/'native-bindings-targets-and-text-audit.json').write_text(json.dumps(allfacts,indent=2)+'\n')
for k,v in allfacts.items():print(k,{s:v[s]['visible_text_missing_from_native_labels'] for s in ['baseline','expanded','submitted']})
