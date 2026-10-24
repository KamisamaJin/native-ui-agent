import sys,json,hashlib,math
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=B/'judgments/final/two/T1'
sys.path.insert(0,str(B/'candidate-v9/scripts'));import native_checks
manifest={};coverage={}
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',12)
for p in sorted((B/'evaluation-inputs/final/T1').glob('*/*/*')):
 rel=str(p.relative_to(B/'evaluation-inputs/final/T1'));d={n:json.loads((p/(n+'.json')).read_text()) for n in ['inputs','plan','catalog','automatic','environment-check']};i=d['inputs'];obs=json.loads((B/i['observation']).read_text());raw=B/i['raw'];plat=i['platform'];groups={};states={}
 for state in d['plan']['states']:
  found,complete,reason,binding=native_checks.bound_state_evidence(obs,state);states[state['id']]={'indices':[j for j,_ in found],'complete':complete,'reason':reason,'binding':binding}
  for j,s in found:
   path=raw/s['screenshot'];im=Image.open(path).convert('RGB')
   if plat=='ios':
    v=s['viewport'];scale=im.width/s['app_frame']['width'];im=im.crop(tuple(round(v[k]*scale) for k in ['x','y'])+tuple(round((v[k]+v[z])*scale) for k,z in [('x','width'),('y','height')]))
   key=hashlib.sha256(im.tobytes()).hexdigest()
   entry={'index':j,'state':state['id'],'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
   if key not in groups:groups[key]={'image':im,'originals':[]}
   groups[key]['originals'].append(entry)
 tiles=[]
 for g in groups.values():
  im=g.pop('image');w=350;h=round(im.height*w/im.width);im=im.resize((w,h));tile=Image.new('RGB',(w+8,h+54),'#EEEEEE');tile.paste(im,(4,50));dr=ImageDraw.Draw(tile);labels=';'.join(f"{x['state']}#{x['index']}" for x in g['originals']);
  for line in range(math.ceil(len(labels)/44)):dr.text((4,2+13*line),labels[line*44:(line+1)*44],font=font,fill='black')
  tiles.append((tile,g))
 pages=[]
 dest=O/rel;dest.mkdir(parents=True,exist_ok=True)
 for start in range(0,len(tiles),6):
  chunk=tiles[start:start+6];ch=max(t.height for t,_ in chunk);sheet=Image.new('RGB',(3*358,2*ch+30),'#AAAAAA');dr=ImageDraw.Draw(sheet);dr.text((4,4),rel+' original viewport crops; exact-pixel duplicates labelled',font=font,fill='black')
  for n,(tile,g) in enumerate(chunk):sheet.paste(tile,((n%3)*358,30+(n//3)*ch))
  fn=dest/f'catalog-{start//6+1:02}.png';sheet.save(fn);pages.append(str(fn.relative_to(O)))
 manifest[rel]={'pages':pages,'tiles':[g for _,g in tiles],'observation_sha256':i['observation_sha256']}
 coverage[rel]={'states':states,'environment':d['environment-check'],'automatic_counts':d['automatic']['counts'],'automatic_failures':d['automatic']['failed_assertion_ids'],'steps':obs['steps'],'observation_issues':obs['issues'],'observed_identifiers':obs['coverage'].get('observed_identifiers'),'catalog_rows':len(d['catalog']['rows'])}
 print(rel,'unique viewports',len(tiles),'pages',len(pages))
(O/'image-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(O/'binding-coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
# Independent source-backed reference images for every supplied case/state.
refs=[]
for case in ['P1','P2','H1']:
 inp=json.loads((B/f'evaluation-inputs/final/T1/source-a/ios/{case}/inputs.json').read_text());scope=B/inp['scope']
 for state in json.loads((B/f'evaluation-inputs/final/T1/source-a/ios/{case}/plan.json').read_text())['states']:
  p=scope/f'references/{case}/{state["id"]}.png'
  if p.is_file():refs.append({'case':case,'state':state['id'],'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for start in range(0,len(refs),6):
 chunk=refs[start:start+6];tiles=[]
 for r in chunk:
  im=Image.open(r['path']).convert('RGB');w=330;h=round(im.height*w/im.width);tile=Image.new('RGB',(338,h+30),'white');tile.paste(im.resize((w,h)),(4,30));ImageDraw.Draw(tile).text((4,4),r['case']+'/'+r['state'],font=font,fill='black');tiles.append(tile)
 ch=max(t.height for t in tiles);sh=Image.new('RGB',(1014,2*ch),'#AAAAAA')
 for j,t in enumerate(tiles):sh.paste(t,((j%3)*338,(j//3)*ch))
 sh.save(O/f'references-{start//6+1:02}.png')
(O/'reference-manifest.json').write_text(json.dumps(refs,indent=2)+'\n')
