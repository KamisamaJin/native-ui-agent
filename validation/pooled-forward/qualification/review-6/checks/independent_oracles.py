from encoding_cases import *
from fractions import Fraction
import math,itertools
base=ROOT/'work/candidate-v13.5/geometry'
folder=base/'sixteen-bit-rgb-lowbit-mismatch'
def read_16bit(p):
 data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';pos=8;compressed=b'';size=None
 while pos<len(data):
  n=struct.unpack('>I',data[pos:pos+4])[0];typ=data[pos+4:pos+8];body=data[pos+8:pos+8+n];pos+=12+n
  if typ==b'IHDR':
   w,h,depth,col,comp,filt,inter=struct.unpack('>IIBBBBB',body);assert(depth,col,comp,filt,inter)==(16,2,0,0,0);size=w,h
  if typ==b'IDAT':compressed+=body
 w,h=size;raw=zlib.decompress(compressed);rows=[]
 for y in range(h):
  row=raw[y*(1+w*6):(y+1)*(1+w*6)];assert row[0]==0
  rows.append([struct.unpack('>HHH',row[1+x*6:7+x*6])for x in range(w)])
 return rows
a=read_16bit(folder/'images/frame-0.png');b=read_16bit(folder/'images/frame-1.png')
diff=[{'before_xy':[x,y+40],'after_xy':[x,y],'before_raw16':a[y+40][x],'after_raw16':b[y][x]}for y in range(56)for x in range(64)if a[y+40][x]!=b[y][x]]
assert len(diff)==1
pa=Image.open(folder/'images/frame-0.png');pb=Image.open(folder/'images/frame-1.png')
assert pa.crop((0,40,64,96)).tobytes()==pb.crop((0,0,64,56)).tobytes()
save(ROOT/'raw/oracle-16bit-lossless-mismatch.json',{'independent_decoder':'PNG type2 bitdepth16 deflate/raw big-endian; no Pillow used to inspect originals','difference_count':len(diff),'differences':diff,'Pillow_modes':[pa.mode,pb.mode],'Pillow_decoded_overlap_equal':True,'original_overlap_equal':False,'frozen_provider_complete':json.loads((folder/'proof.json').read_text())['complete'],'verdict':'Confirmed lossy original-raster comparison'})

folder=base/'joint-final-witness-inconsistency';o=json.loads((folder/'observation.json').read_text())
def q(v):v=Fraction(v);return range(math.floor(v),math.ceil(v)+1)
def candidates(frame,shift):
 x,y,w,h=[Fraction(frame[k])for k in['x','y','width','height']];return {b for b in itertools.product(q(x),q(y+shift),q(x+w),q(y+h+shift))if b[2]>b[0]and b[3]>b[1]and b[2]-b[0]in q(w)and b[3]-b[1]in q(h)}
final={}
for i,snap in enumerate(o['snapshots']):
 for n in snap['nodes'][1:5]:
  r=n['frame']
  if 0<=r['y']and r['y']+r['height']<=96:
   key=n['identifier'];cs=candidates(r,i*10);final[key]=cs if key not in final else final[key]&cs
assert final['leaf-a']=={(2,31,16,41)}and final['leaf-b']=={(2,40,16,50)}
first_common=['leaf-a','leaf-b'];possible=[(a,b)for a in final['leaf-a']for b in final['leaf-b']if a[3]<=b[1]or b[3]<=a[1]]
assert not possible
save(ROOT/'raw/oracle-joint-witness-inconsistency.json',{'independent_solver':'Exact Fraction of recorded binary64, all four edges and direct sizes; global intersection all eligible observations','final_rectangles':{k:sorted(v)for k,v in final.items()},'first_link_eligible_common_ids':first_common,'first_link_disjoint_pairs_under_final_global_assignment':possible,'frozen_provider_complete':json.loads((folder/'proof.json').read_text())['complete'],'verdict':'Confirmed no jointly consistent independent witness pair for first link'})

save(ROOT/'raw/initial-expectation-adjudication.json',{'preserve_all_initial_rows_and_first_failures':True,'not_confirmed_as_implementation_bugs':[{'row':'global-repeated-leaf-incompatible','reason':'Mutated leaf-b is outside final viewport; it is not an eligible final anchor. Original initial expected U was overbroad. Add a new all-visible repeated-leaf control separately.'},{'row':'raster-witness-overlap','reason':'Admitted candidate assignments include disjoint raster boxes. Original initial expected U was overbroad; do not count acceptance as bug.'}],'pending':[{'row':'root-frame-disjoint-advisory','reason':'Actual root frame is disjoint but membership metadata ancestry still coherent; pending independent mapping/host-shape criterion interpretation and default integration. No headline blocker on this observation alone.'}]})
print('Independent original16 and exact joint-witness oracle proofs confirmed; two initial expectation errors recorded separately.')
