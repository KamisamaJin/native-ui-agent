exec(open('agent-output/review_sheets.py').read().split('records=[]')[0])
records=json.loads((out/'manual-image-index.json').read_text());ledger=[]
for platform,case,part in [('ios','P1','own-corpora'),('ios','P2','own-retries'),('android','P1','own-corpora'),('android','P2','own-corpora')]:
 p=r/part/'unit-092e15/d0'/platform/case;d=json.loads((p/'observation.json').read_text())
 seen=set(next(s for s in d['state_captures'] if s['state_id']=='browse')['snapshot_indices'])
 seen.update(x['snapshot_index'] for x in records if x['platform']==platform and x['case']==case)
 rows=[]
 for step in d['steps']:
  if step.get('state_id') not in ['configured','reserved','replaced','reserved-again','blocked','course-changed','editing']:continue
  for i in step['observation_set']['snapshot_indices']:
   if i not in seen:rows.append((i,step['state_id']));seen.add(i)
 for page in range(math.ceil(len(rows)/6)):
  chunk=rows[page*6:(page+1)*6];tiles=[]
  for i,state in chunk:
   s=d['snapshots'][i];im=Image.open(p/s['screenshot']).convert('RGB')
   if platform=='ios':
    v=s['viewport'];scale=3;im=im.crop((round(v['x']*scale),round(v['y']*scale),round((v['x']+v['width'])*scale),round((v['y']+v['height'])*scale)))
   im=im.resize((300,round(im.height*300/im.width)))
   tile=Image.new('RGB',(300,im.height+38),'#dddddd');tile.paste(im,(0,38));ImageDraw.Draw(tile).text((6,8),f'{platform} {case} {state} [{i}]',fill='black');tiles.append(tile)
   ledger.append({'case':case,'platform':platform,'state':state,'snapshot_index':i,'evidence':{'path':str(p/s['screenshot']),'sha256':hashlib.sha256((p/s['screenshot']).read_bytes()).hexdigest()}})
  h=max(t.height for t in tiles);sheet=Image.new('RGB',(900,math.ceil(len(tiles)/3)*h),'#aaaaaa')
  for j,tile in enumerate(tiles):sheet.paste(tile,(j%3*300,j//3*h))
  dest=out/f'{platform}-{case}-targets-{page}.png';sheet.save(dest);print(dest)
(out/'additional-image-index.json').write_text(json.dumps(ledger,indent=2)+'\n')
