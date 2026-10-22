import sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT=BASE/'claim-judgments/two/T3'
sys.path.insert(0,str(BASE/'candidate-v8/scripts'))
from native_checks import resolve
from native_pixels import sample
policy=json.loads((BASE/'design-v2/T3/public/policy.json').read_text())
spec=next(x['sampling']for x in policy['atoms']if x['rule_id']=='primary-surface-color')
products=json.loads((OUT/'common-confirmed-product-rows.json').read_text())
facts=[];pictures={}
for source,rows in products.items():
    for row in rows:
        case,platform=row['key'].split('/')[:2]
        meta=json.loads((BASE/'evaluation-inputs/d0/T3'/source/platform/case/'inputs.json').read_text())
        root=BASE/meta['root'];obs=json.loads((root/'observation.json').read_text())
        ids=row.get('authoritative',{}).get('snapshot_indices',[])
        if not ids: ids=sorted(set(i for a in row['cause_assessments']for i in a.get('snapshot_indices',[])))
        item={'source':source,'key':row['key'],'observation':str(root/'observation.json'),'snapshots':[]}
        for i in ids:
            s=obs['snapshots'][i];p=root/s['screenshot']
            v={'index':i,'state_id':s.get('state_id'),'binding':s.get('binding'),'capture_consistent':s.get('capture_consistent'),
               'screenshot':str(p),'screenshot_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            if platform=='ios':
                v['native_facts']={z:resolve(s,{'identifier':z},platform)['facts']for z in ['bicycle.summary','bicycle.submit','bicycle.choice.a','bicycle.choice.b']}
                if row['requirement_id']=='primary-surface-color':v['pixel_sample']=sample(s,{'identifier':'bicycle.submit'},platform,root,spec)
            item['snapshots'].append(v)
        if platform=='ios': item['raw_update_and_submit_steps']=obs['steps'][6:9]
        facts.append(item)
        # Images supplement native facts; no common FINAL outcome is used.
        if item['snapshots'] and row['requirement_id']in ['content-wrapping','primary-surface-color']:
            v=item['snapshots'][-1];pictures[v['screenshot']]={'source':source,'key':row['key'],**v}
(OUT/'common-original-facts.json').write_text(json.dumps(facts,indent=2)+'\n')
rs=list(pictures.values());cw=413;ch=1040;cols=4
sheet=Image.new('RGB',(cols*cw,((len(rs)+cols-1)//cols)*ch),'white');draw=ImageDraw.Draw(sheet)
for n,r in enumerate(rs):
    im=Image.open(r['screenshot']).convert('RGB')
    if '/ios/'in r['key']:im=im.crop((0,186,1206,1986)).resize((402,600))
    x=(n%cols)*cw;y=(n//cols)*ch
    draw.text((x+3,y+3),r['source']+' '+r['key'],fill='black');sheet.paste(im,(x,y+40))
sheet.save(OUT/'common-d0-inspection.png')
(OUT/'common-screenshot-inspection-manifest.json').write_text(json.dumps(rs,indent=2)+'\n')
print('Common product rows:',len(facts),'representative original screenshots:',len(rs))
