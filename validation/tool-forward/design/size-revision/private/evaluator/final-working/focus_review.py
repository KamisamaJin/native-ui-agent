import sys,json,math
from PIL import Image,ImageDraw
import raw_review as r
sub=sys.argv[1];dest=r.HERE/sub
for pl in ['android','apple']:
 cells=[];indices=[]
 for cid,cx in r.CTX.items():
  rows=[x for x in r.PLAN if x['contextId']==cid and x['platform']==pl and x['aspect']=='observedPixels']
  if cx['fullVisualCheckpoint'] or not rows:continue
  try:d=r.state_data(sub,pl,cid)
  except FileNotFoundError:continue
  i=d['indices'][-1];s=d['snapshots'][-1];raw,im,crop,sx,sy,off,h=r.image_info(pl,d['path'],s)
  vpim=im.crop(crop);vpim=vpim.resize((round(vpim.width/sx),600));cell=Image.new('RGB',(390,660),'#DDDDEE');cell.paste(vpim,(0,60));draw=ImageDraw.Draw(cell)
  target=rows[0]['target'];ns=[n for n in s['nodes'] if n.get('identifier')==target];visible=any(n.get('intersects_viewport') for n in ns)
  draw.text((3,4),cid,fill='black');draw.text((3,20),target,fill='black');draw.text((3,36),'target in viewport: '+str(visible),fill='black')
  cells.append(cell);indices.append(dict(context=cid,platform=pl,snapshot=i,path=str(raw),sha256=r.sha(raw),viewportCrop=crop,target=target,targetIntersects=visible))
 for start in range(0,len(cells),4):
  page=Image.new('RGB',(390*len(cells[start:start+4]),660),'#DDDDEE')
  for j,im in enumerate(cells[start:start+4]):page.paste(im,(390*j,0))
  page.save(dest/(pl+f'-focus-page-{start//4}.png'))
 r.write(dest/(pl+'-focus-index.json'),indices)
