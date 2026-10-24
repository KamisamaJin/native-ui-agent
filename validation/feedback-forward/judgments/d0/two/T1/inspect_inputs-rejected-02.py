import sys,json,hashlib,collections,math
from pathlib import Path
sys.dont_write_bytecode=True
from PIL import Image,ImageDraw,ImageFont
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');out=b/'judgments/d0/two/T1'
sys.path.insert(0,str(b/'candidate-v9/scripts'))
import native_checks
manifest={};bindings={};summaries={}
for p in sorted((b/'evaluation-inputs/d0/T1').glob('*/*/*')):
 alias,platform,case=p.parts[-3:];key='/'.join([alias,platform,case]);i=json.loads((p/'inputs.json').read_text());o=json.loads((b/i['observation']).read_text());pl=json.loads((p/'plan.json').read_text());a=json.loads((p/'automatic.json').read_text());c=json.loads((p/'catalog.json').read_text());e=json.loads((p/'environment-check.json').read_text());raw=b/i['raw'];dest=out/alias/platform/case;dest.mkdir(parents=True,exist_ok=True)
 h=collections.defaultdict(list);frames=[]
 for n,s in enumerate(o['snapshots']):
  path=raw/s['screenshot'];sha=hashlib.sha256(path.read_bytes()).hexdigest();h[sha].append(n);frames.append({'index':n,'state':s.get('state_id'),'path':str(path),'sha256':sha})
 groups=[]
 for sha,indices in h.items(): groups.append({'sha256':sha,'indices':indices,'representative':frames[indices[0]]})
 sheets=[]
 for page in range(math.ceil(len(groups)/6)):
  subset=groups[page*6:page*6+6];cw,ch=370,620;im=Image.new('RGB',(cw*3,ch*2),'#e5e5e5');d=ImageDraw.Draw(im)
  for pos,g in enumerate(subset):
   x=(pos%3)*cw;y=(pos//3)*ch;s=Image.open(g['representative']['path']).convert('RGB');s.thumbnail((354,548));im.paste(s,(x+8,y+62));d.text((x+8,y+4),key,fill='black');d.text((x+8,y+18),g['representative']['state']+' index '+str(g['indices']),fill='black');d.text((x+8,y+32),Path(g['representative']['path']).name,fill='black');d.text((x+8,y+46),'sha '+g['sha256'][:24],fill='black')
  path=dest/f'contact-{page+1:02d}.png';im.save(path);sheets.append(str(path))
 manifest[key]={'observation_sha256':i['observation_sha256'],'frames':frames,'unique_groups':groups,'sheets':sheets}
 bindings[key]={}
 for st in pl['states']:
  be=native_checks.bound_state_evidence(o,st)
  bindings[key][st['id']]={'indices':[n for n,s in be[0]],'complete':be[1],'reason':be[2],'capture':be[3]}
 summaries[key]={'environment':{'status':e['status'],'expected':e['expected'],'frames':len(e['frames']),'statuses':dict(collections.Counter(z['status'] for z in e['frames']))},'steps':[{'index':n,**{k:s.get(k) for k in ['type','action','outcome','selector','callback_delta','dispatch','binding_after','state_id']}} for n,s in enumerate(o['steps'])],'events':o['events'],'unassessed_nonvisual':[r for r in a['assertions'] if r['status']=='unassessed' and not any(z['id']==r['id'] and z['method']=='visual' for z in c['rows'])],'failed': [r for r in a['assertions'] if r['status']=='failed'],'coverage':o['coverage']}
 print(key,'frames',len(frames),'unique',len(groups),'sheets',sheets)
(out/'image-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'bound-state-evidence.json').write_text(json.dumps(bindings,indent=2)+'\n');(out/'native-evidence-summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
