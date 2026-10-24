#!/usr/bin/env python3
from pathlib import Path
import datetime,hashlib,json,time,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');D=ROOT/'validation/feedback-forward/design/T1/public';O=ROOT/'validation/feedback-forward/design-review/T1'
start=time.time();r=json.loads((D/'reference.json').read_text());c=json.loads((D/'contract.json').read_text())
def save(name,value):
 with (O/name).open('x')as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
result={'startedAtUnix':start,'scope':'Independent BRIEF state-machine replay and static-reference structure; no native measurements','cases':{},'references':[]}
for case in ['P1','P2']:
 f=json.loads((D/f'cases/{case}/fixtures.json').read_text());actions=json.loads((D/f'cases/{case}/actions.ios.json').read_text());states={s['after_action']:s for s in c['scenarios'][case]['states']};model=f['initial'];ack=opened=requested=False;ix=0;values=[]
 for index,a in enumerate(actions):
  events=[]
  if a['type']=='apply_next_fixture':model=f['updates'][ix];ix+=1;ack=opened=requested=False
  elif a['type']=='tap':
   target=a['target']['identifier']
   if target=='transfer.disclosure':opened=not opened
   elif target=='transfer.choice'and not requested:ack=not ack;events=[f'transfer.ack:{model["id"]}:{str(ack).lower()}']
   elif target=='transfer.primary'and model['sealIntact']and model['coolantReady']and ack and not requested:requested=True;events=[f'transfer.release:{model["id"]}']
  if index not in states:continue
  state=states[index];sv=r['cases'][case]['states'][state['id']]
  actual={'title':model['title'],'subtitle':model['destination']+' · '+model['temperatureRange'],'status':'Seal needs attention'if not model['sealIntact']else'Coolant not ready'if not model['coolantReady']else'Release requested'if requested else'Ready for release'if ack else'Awaiting check','disclosure':'Hide handling'if opened else'Review handling','disclosureEnabled':True,'choice':'Seal check confirmed'if ack else'Confirm seal checked','selected':ack,'choiceEnabled':not requested,'primary':'Requested'if requested else'Release transfer','enabled':model['sealIntact']and model['coolantReady']and ack and not requested,'open':opened,'requested':requested}
  mismatches={k:{'brief_derived':v,'typed_reference':sv[k]['value']}for k,v in actual.items()if sv[k]['value']!=v}
  values.append({'state':state['id'],'action_index':index,'input_index':ix,'stimulus_action':state.get('stimulus_action'),'mismatches':mismatches})
 result['cases'][case]={'state_replay':values,'all_values_match':all(not v['mismatches']for v in values),'model_id_different_on_update':f['initial']['id']!=f['updates'][0]['id'],'unique_note_ids':all(len(m['notes'])==len({n['id']for n in m['notes']})for m in [f['initial']]+f['updates']),'guard_samples':[{'sealIntact':m['sealIntact'],'coolantReady':m['coolantReady']}for m in [f['initial']]+f['updates']]}
 for state in c['scenarios'][case]['states']:
  sid=state['id'];svg=D/f'references/{case}/{sid}.svg';png=D/f'references/{case}/{sid}.png';root=ET.parse(svg).getroot();texts=[''.join(e.itertext())for e in root if e.tag.split('}')[-1]=='text'];joined=' '.join(texts)
  model=f['initial']if state['input_index']==0 else f['updates'][state['input_index']-1];sv=r['cases'][case]['states'][sid];copy=[model['title'],sv['subtitle']['value'],sv['status']['value'],sv['disclosure']['value'],sv['choice']['value'],sv['primary']['value']]
  if sv['open']['value']:
   for note in model['notes']:copy.extend([note['title'],note['body']])
  with Image.open(png)as im:size=im.size
  result['references'].append({'case':case,'state':sid,'png_dimensions':list(size),'svg_dimensions':[int(root.attrib['width']),int(root.attrib['height'])],'all_expected_copy_in_svg':all(t in joined for t in copy),'missing_copy':[t for t in copy if t not in joined],'contains_native_measurement_disclaimer':any('no native' in ''.join(e.itertext())for e in root if e.tag.split('}')[-1]=='desc')})
 # Top and bottom contact summaries of every original reference; derived QA images only.
 tiles=Image.new('RGB',(900,2100),'#D4D8DF');draw=ImageDraw.Draw(tiles)
 for i,state in enumerate(c['scenarios'][case]['states']):
  sid=state['id'];im=Image.open(D/f'references/{case}/{sid}.png').convert('RGB');x=(i%3)*300;y=(i//3)*700;draw.text((x+8,y+8),case+' / '+sid,fill='#000000')
  top=im.crop((0,0,im.width,min(im.height,600)));top.thumbnail((284,600));tiles.paste(top,(x+8,y+28))
  if im.height>650:
   foot=im.crop((0,max(0,im.height-120),im.width,im.height));foot.thumbnail((284,120));tiles.paste(foot,(x+8,y+570));draw.text((x+8,y+548),'[original bottom]',fill='#000000')
 tiles.save(O/f'references-{case}-contact.png')
result['finishedAtUnix']=time.time();save('semantic-checks.json',result)
with (O/'command-log.jsonl').open('a')as f:f.write(json.dumps({'startedAtUnix':start,'finishedAtUnix':result['finishedAtUnix'],'argv':['python3',str(O/'semantic_checks.py')],'sdk_invoked':False,'outputs':['semantic-checks.json','references-P1-contact.png','references-P2-contact.png']})+'\n')
print(json.dumps({'cases':result['cases'],'reference_count':len(result['references']),'reference_discrepancies':[v for v in result['references']if not v['all_expected_copy_in_svg']or v['png_dimensions']!=v['svg_dimensions']]},indent=2))
