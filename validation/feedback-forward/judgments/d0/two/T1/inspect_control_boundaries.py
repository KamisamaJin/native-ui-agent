import sys,json,math,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');out=b/'judgments/d0/two/T1';sys.path.insert(0,str(b/'candidate-v9/scripts'))
import native_checks,native_pixels
manifest=[]
for p in sorted((b/'evaluation-inputs/d0/T1').glob('*/*/*')):
 i=json.loads((p/'inputs.json').read_text());o=json.loads((b/i['observation']).read_text());pl=json.loads((p/'plan.json').read_text());groups=[]
 for st in pl['states']:
  found,complete,why,cap=native_checks.bound_state_evidence(o,st)
  for n,s in found:
   r=native_checks.resolve(s,{'identifier':'transfer.primary'},i['platform']);node=r.get('control',{})
   if node and node.get('fully_within_viewport',node.get('fully_visible',False)):
    path=b/i['raw']/s['screenshot'];im=Image.open(path).convert('RGB');box,clip=native_pixels.image_rectangle(s,node,i['platform'],im.size);roi=[math.floor(box[0]-8),math.floor(box[1]-8),math.ceil(box[2]+8),math.ceil(box[3]+8)];crop=im.crop(roi);scale=min(1,380/crop.width);crop=crop.resize((int(crop.width*scale),int(crop.height*scale)))
    groups.append((st['id'],n,path,box,roi,crop,scale));manifest.append({'platform':i['platform'],'case':i['case'],'state':st['id'],'snapshot_index':n,'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'observed_control_boundary_in_original_image':box,'crop':roi});break
 for page in range(math.ceil(len(groups)/9)):
  sheet=Image.new('RGB',(1200,750),'#ddd');d=ImageDraw.Draw(sheet)
  for pos,(state,n,path,box,roi,crop,scale) in enumerate(groups[page*9:page*9+9]):
   x=pos%3*400;y=pos//3*250;d.text((x+6,y+4),i['platform']+'/'+i['case']+'/'+state+' index '+str(n),fill='black');sheet.paste(crop,(x+6,y+30));mapped=[(box[0]-roi[0])*scale+x+6,(box[1]-roi[1])*scale+y+30,(box[2]-roi[0])*scale+x+6,(box[3]-roi[1])*scale+y+30];d.rectangle([mapped[0]-2,mapped[1]-2,mapped[2]+2,mapped[3]+2],outline='#f000c0',width=1);d.text((x+6,y+220),'Magenta lies outside native control boundary.',fill='black')
  sheet.save(out/f"primary-boundaries-{i['platform']}-{i['case']}-{page+1}.png")
(out/'control-boundary-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
