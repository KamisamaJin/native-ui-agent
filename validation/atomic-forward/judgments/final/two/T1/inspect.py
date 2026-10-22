import sys,pathlib,json,hashlib,collections,datetime
from PIL import Image,ImageDraw
BASE=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT=BASE/'judgments/final/two/T1'
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE/'candidate-v8/scripts'))
from native_checks import bound_state_evidence,resolve
manifest={};hashes={};reference_hashes={}
for f in sorted((BASE/'evaluation-inputs/final/T1').glob('*/*/*/inputs.json')):
 key=str(f.parent.relative_to(BASE/'evaluation-inputs/final/T1'));i=json.loads(f.read_text());obs=json.loads((BASE/i['observation']).read_text());plan=json.loads((f.parent/'plan.json').read_text());catalog=json.loads((f.parent/'catalog.json').read_text());auto=json.loads((f.parent/'automatic.json').read_text());env=json.loads((f.parent/'environment-check.json').read_text())
 for n in ['inputs.json','plan.json','catalog.json','automatic.json','environment-check.json']:
  q=f.parent/n;hashes[str(q.relative_to(BASE))]=hashlib.sha256(q.read_bytes()).hexdigest()
 for rel,expected in i['original_files'].items():
  p=BASE/rel
  actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
  reference_hashes[rel]={'expected':expected,'actual':actual,'matched':actual==expected}
 record={'inputs':{k:v for k,v in i.items() if k!='original_files'},'environment_status':env['status'],'automatic_counts':auto['counts'],'states':{},'original_frames':[],'contact_sheets':[]}
 unique={}
 for s in plan['states']:
  found,complete,why,cap=bound_state_evidence(obs,s)
  record['states'][s['id']]={'plan':s,'indices':[n for n,v in found],'complete':complete,'reason':why,'capture':cap,'targets':{}}
  for n,snap in found:
   path=BASE/i['root']/snap['screenshot'];sha=hashlib.sha256(path.read_bytes()).hexdigest()
   record['original_frames'].append({'index':n,'state':s['id'],'path':str(path),'sha256':sha,'scroll_offset':snap.get('scroll_offset_dp'),'screenshot_pixels':snap.get('screenshot_pixels')})
   if sha not in unique:unique[sha]={'path':path,'refs':[]}
   unique[sha]['refs'].append((s['id'],n))
  for selector in [{'identifier':'workshop.canvas'},{'identifier':'workshop.notice'},{'identifier':'workshop.submit'}]:
   record['states'][s['id']]['targets'][selector['identifier']]=[{'index':n,'resolved':resolve(snap,selector,i['platform'])} for n,snap in found]
 # Contact sheets preserve all unique selected-state original pixel content, with all state/index aliases in manifest.
 for page,start in enumerate(range(0,len(unique),6)):
  chosen=list(unique.items())[start:start+6]; thumbs=[]
  for sha,u in chosen:
   im=Image.open(u['path']).convert('RGB');im.thumbnail((400,800));thumbs.append((sha,u,im))
  cellh=max(im.height for _,_,im in thumbs)+76;sheet=Image.new('RGB',(1200,cellh*2),'#d0d0d0');draw=ImageDraw.Draw(sheet)
  for j,(sha,u,im) in enumerate(thumbs):
   x=(j%3)*400;y=(j//3)*cellh
   label=key+'\n'+' '.join(f'{s}:{n}' for s,n in u['refs'])
   # short lines to retain all labels
   lines=[]
   for ln in label.split('\n'):
    while len(ln)>60:lines.append(ln[:60]);ln=ln[60:]
    lines.append(ln)
   draw.multiline_text((x+4,y+2),'\n'.join(lines[:6]),fill='black',spacing=1)
   sheet.paste(im,(x,y+76))
  dest=OUT/'inspection'/key/f'page-{page+1:02d}.png';dest.parent.mkdir(parents=True,exist_ok=True);sheet.save(dest)
  record['contact_sheets'].append({'path':str(dest.relative_to(OUT)),'images':[{'sha256':sha,'path':str(u['path']),'aliases':[{'state':s,'index':n}for s,n in u['refs']]}for sha,u,im in thumbs]})
 manifest[key]=record
 print(key,'snapshots',len(obs['snapshots']),'bound',sum(len(s['indices'])for s in record['states'].values()),'unique',len(unique),'pages',len(record['contact_sheets']),'complete',[(s,v['complete'])for s,v in record['states'].items()])
(OUT/'inspection-records.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'input-hashes.json').write_text(json.dumps({'input_files':hashes,'original_references':reference_hashes},indent=2)+'\n')
print('HASH mismatches',[(k,v)for k,v in reference_hashes.items()if not v['matched']])
