import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT=BASE/'claim-judgments/two/T3'
extract=json.loads((OUT/'original-evidence-extract.json').read_text())
records=[]
for source,entries in extract.items():
    for c in entries:
        if c['snapshots']:
            selected=[c['snapshots'][-1]] if '/content-' in c['original_scope'][0] else [c['snapshots'][0]]
            for s in selected: records.append({'source':source,'claim_id':c['claim_id'],'scope':c['original_scope'][0], 'path':s['screenshot'],'index':s['index']})
        else:
            for ev in c['original_evidence']:
                if ev['path'].endswith('.png'):
                    records.append({'source':source,'claim_id':c['claim_id'],'scope':c['original_scope'][0], 'path':ev['path'],'index':None})
                    break
# Deduplicate exact native screenshot while preserving all covered claim IDs.
unique={}
for r in records:
    key=r['path']
    if key not in unique: unique[key]={**r,'claim_ids':[]}
    unique[key]['claim_ids'].append(r['claim_id'])
groups={}
for r in unique.values(): groups.setdefault(r['source']+'-'+r['scope'].split('/')[1],[]).append(r)
for group,rs in groups.items():
    ios=group.endswith('ios'); cw=402 if ios else 413; ch=650 if ios else 1040
    cols=min(4,len(rs)); rows=(len(rs)+cols-1)//cols
    sheet=Image.new('RGB',(cw*cols,ch*rows),'white');draw=ImageDraw.Draw(sheet)
    for n,r in enumerate(rs):
        im=Image.open(r['path']).convert('RGB')
        r['sha256']=hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()
        r['original_size']=list(im.size)
        if ios:
            im=im.crop((0,186,1206,1986)).resize((402,600))
            r['display_transform']='Native viewport crop (0,186,1206,1986), uniform resize to 402x600; exact original retained.'
        else:r['display_transform']='Original native PNG, no image resize.'
        x=(n%cols)*cw;y=(n//cols)*ch
        draw.text((x+3,y+3),','.join(r['claim_ids']),fill='black')
        draw.text((x+3,y+18),r['scope'],fill='black')
        sheet.paste(im,(x,y+40))
    name=group+'-inspection.png';sheet.save(OUT/name)
    for r in rs:r['inspection_sheet']=name
(OUT/'screenshot-inspection-manifest.json').write_text(json.dumps(list(unique.values()),indent=2)+'\n')
print(json.dumps({k:len(v)for k,v in groups.items()},indent=2))
