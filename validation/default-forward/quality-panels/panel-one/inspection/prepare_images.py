import json,pathlib,hashlib
from PIL import Image,ImageDraw,ImageFont
base=pathlib.Path(__file__).resolve().parents[3]/'quality-inputs'
out=pathlib.Path(__file__).resolve().parent
index=json.loads((base/'image-sha-index.json').read_text())['images']
by_path={p:h for h,ps in index.items() for p in ps}
manifest=[];seen={};sheets=[]
for case in sorted(base.glob('candidate-*/native/*/*/*')):
 obs=json.loads((case/'native/observation.json').read_text())
 states=json.loads((case/'state-image-index.json').read_text())
 pending=[]
 for state,record in states.items():
  assert record['complete']
  for i in record['indices']:
   shot=obs['snapshots'][i]
   path=case/'native'/shot['screenshot']
   if not path.exists(): path=case/'native/attachments'/pathlib.Path(shot['screenshot']).name
   relative=str(path.relative_to(base));h=hashlib.sha256(path.read_bytes()).hexdigest()
   assert by_path[relative]==h
   entry={'candidate':case.parts[-5],'scope':case.parts[-3],'platform':case.parts[-2],'case':case.name,'state':state,'snapshot_index':i,'file':relative,'sha256':h}
   manifest.append(entry)
   if h not in seen:
    seen[h]=entry;pending.append(entry)
 for start in range(0,len(pending),4):
  group=pending[start:start+4];w=402;h=874;label=46
  canvas=Image.new('RGB',(w*len(group),h+label),'#dddddd');d=ImageDraw.Draw(canvas)
  for n,e in enumerate(group):
   img=Image.open(base/e['file']).convert('RGB');img.thumbnail((w,h),Image.Resampling.LANCZOS)
   canvas.paste(img,(n*w,label))
   d.text((n*w+4,3),f"{e['candidate']} {e['scope']} {e['platform']}",fill='black')
   d.text((n*w+4,19),f"{e['state']} snapshot {e['snapshot_index']} {e['sha256'][:10]}",fill='black')
  name=f'sheet-{len(sheets):02}.png';canvas.save(out/name)
  sheets.append({'file':name,'originals':group})
(out/'image-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'sheet-manifest.json').write_text(json.dumps(sheets,indent=2)+'\n')
print('frame references',len(manifest),'unique original sha',len(seen),'sheets',len(sheets))
print([(x['file'],x['originals'][0]['candidate'],x['originals'][0]['scope'],x['originals'][0]['platform'],[(v['state'],v['snapshot_index']) for v in x['originals']]) for x in sheets])
