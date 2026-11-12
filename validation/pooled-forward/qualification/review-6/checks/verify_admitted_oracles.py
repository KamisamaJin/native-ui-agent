from encoding_cases import *
from fractions import Fraction
import math,itertools
def read16(p):
 data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';pos=8;compressed=b''
 while pos<len(data):
  n=struct.unpack('>I',data[pos:pos+4])[0];typ=data[pos+4:pos+8];body=data[pos+8:pos+8+n];pos+=n+12
  if typ==b'IHDR':w,h,depth,col,comp,filt,inter=struct.unpack('>IIBBBBB',body);assert(depth,col,comp,filt,inter)==(16,2,0,0,0)
  if typ==b'IDAT':compressed+=body
 raw=zlib.decompress(compressed);rows=[]
 for y in range(h):
  row=raw[y*(1+w*6):(y+1)*(1+w*6)];assert row[0]==0;rows.append([struct.unpack('>HHH',row[1+x*6:7+x*6])for x in range(w)])
 return rows
def q(x):x=Fraction(x);return range(math.floor(x),math.ceil(x)+1)
def boxes(r,shift):
 x,y,w,h=[Fraction(r[k])for k in['x','y','width','height']];return{b for b in itertools.product(q(x),q(y+shift),q(x+w),q(y+h+shift))if b[2]>b[0]and b[3]>b[1]and b[2]-b[0]in q(w)and b[3]-b[1]in q(h)}
results=[]
for arm in['candidate-v13.5','baseline-v12.6-common-2']:
 run='admitted-runtime-retry-1'if arm=='candidate-v13.5'else'admitted-runtime';base=ROOT/'work'/arm/run
 a=read16(base/'A07-raster16-lowbit-admitted-host/packet/native/frame-0.png');b=read16(base/'A07-raster16-lowbit-admitted-host/packet/native/frame-1.png');mismatch=[{'before_xy':[x,y+250],'after_xy':[x,y],'before':a[y+250][x],'after':b[y][x]}for y in range(350)for x in range(390)if a[y+250][x]!=b[y][x]];assert len(mismatch)==1
 o=json.loads((base/'A08-joint-witness-admitted-host/observation.json').read_text());domains={}
 for i,s in enumerate(o['snapshots']):
  for n in s['nodes'][1:5]:
   r=n['frame']
   if 0<=r['y']and r['y']+r['height']<=600:
    key=n['identifier'];new=boxes(r,i*64);domains[key]=new if key not in domains else domains[key]&new
 assert domains['anchor-a']=={(20,201,50,211)}and domains['anchor-b']=={(20,210,50,220)}
 possible=[(a,b)for a in domains['anchor-a']for b in domains['anchor-b']if a[3]<=b[1]or b[3]<=a[1]];assert not possible
 results.append({'arm':arm,'raw16_mismatches':mismatch,'first_link_common':['anchor-a','anchor-b'],'final_exact_rational_rectangles':{k:sorted(v)for k,v in domains.items()},'first_link_jointly_disjoint_pairs':possible,'evidence_class':'Independent HOST raw PNG16 and rational geometry oracle, not provider implementation','native_runs':0})
save(ROOT/'raw/admitted-original16-and-global-joint-oracles.json',results);print('Verified both admitted-shape original16 mismatches and global witness contradictions.')
