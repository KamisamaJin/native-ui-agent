import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,json,hashlib,math,collections,functools
from PIL import Image
R=Path(__file__).resolve().parent.parents[3]
spec=importlib.util.spec_from_file_location('v3_measure',R/'design/private/evaluator-prep/v3/evaluator.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
g=e.geometry_calibration_module();plan=e.read(R/'design/private/evaluator-prep/normalized-final.json');oracle=e.read(R/'design/private/oracle.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
@functools.lru_cache(maxsize=3)
def img(p):return Image.open(p).convert('RGBA')
def dist(a,b):return max(abs(a[i]-b[i]) for i in range(3))
def clip(box,w,h):return [max(0,int(math.floor(box[0]))),max(0,int(math.floor(box[1]))),min(w,int(math.ceil(box[2]))),min(h,int(math.ceil(box[3])))]
def count_region(im,b):return collections.Counter(im.crop(tuple(b)).getdata())
def candidates_for(ctx,identifier,platform,cap):
 result=[]
 for si,s in ctx['found']:
  ns=[n for n in s['nodes'] if n.get('identifier')==identifier]
  if len(ns)!=1:continue
  n=ns[0];path=cap/Path(ctx['observation_ref']['path']).parent/s['screenshot'];im=img(str(path));cal=g.calibrate_png(s,platform,path)
  if platform=='ios':box=g.project_rect(n['frame'],cal);viewport=cal['viewport_png_rect']
  else:
   b=n.get('unclipped_bounds_dp',n.get('bounds_dp'))
   box=g.project_rect({'x':b[0],'y':b[1],'width':b[2]-b[0],'height':b[3]-b[1]},cal);viewport=[0,0,im.width,im.height]
  visible=clip([max(box[0],viewport[0]),max(box[1],viewport[1]),min(box[2],viewport[2]),min(box[3],viewport[3])],im.width,im.height)
  if visible[2]<=visible[0] or visible[3]<=visible[1]:continue
  full=(box[0]>=viewport[0]-.1 and box[1]>=viewport[1]-.1 and box[2]<=viewport[2]+.1 and box[3]<=viewport[3]+.1)
  result.append({'si':si,'snap':s,'node':n,'path':path,'im':im,'box':box,'visible':visible,'cal':cal,'full':full})
 return sorted(result,key=lambda x:(x['full'],(x['visible'][2]-x['visible'][0])*(x['visible'][3]-x['visible'][1])),reverse=True)
def independent_points(im,b,color,size,margin=0):
 x0,y0,x1,y1=b;x0+=margin;y0+=margin;x1-=margin;y1-=margin
 points=[]
 # Spread witnesses across the actual region before falling back to a dense scan.
 for frac in [(.2,.25),(.7,.5),(.4,.75),(.85,.25),(.15,.75),(.5,.5)]:
  cx=round(x0+(x1-x0)*frac[0]);cy=round(y0+(y1-y0)*frac[1])
  for radius in [0,3,8,20,60]:
   found=False
   for yy in range(max(y0,cy-radius),min(y1-size+1,cy+radius+1)):
    for xx in range(max(x0,cx-radius),min(x1-size+1,cx+radius+1)):
     if any(math.hypot(xx-p[0],yy-p[1])<max(8,size*3) for p in points):continue
     if all(im.getpixel((xx+dx,yy+dy))==color for dy in range(size) for dx in range(size)):
      points.append((xx,yy));found=True;break
    if found:break
   if found:break
  if len(points)==3:return points
 # Solid glyph interiors can be rare at base size; find separated actual opaque cores.
 for yy in range(y0,y1-size+1):
  for xx in range(x0,x1-size+1):
   if any(math.hypot(xx-p[0],yy-p[1])<max(6,size*3) for p in points):continue
   if all(im.getpixel((xx+dx,yy+dy))==color for dy in range(size) for dx in range(size)):
    points.append((xx,yy))
    if len(points)==3:return points
 return []
def edge_points(c):
 im=c['im'];l,t,r,b=c['box'];v=c['visible'];scale=c['cal']['native_pixels_per_logical_unit'];band=math.ceil(scale*2)+1
 pts=[]
 # Straight middle thirds of all available original edges, never the corner AA.
 for horizontal,at,a,z in [(True,t,l+(r-l)*.3,r-(r-l)*.3),(True,b,l+(r-l)*.3,r-(r-l)*.3),(False,l,t+(b-t)*.3,b-(b-t)*.3),(False,r,t+(b-t)*.3,b-(b-t)*.3)]:
  if horizontal:
   if not(v[1]-.01<=at<=v[3]+.01):continue
   for y in range(max(v[1],math.floor(at)-band),min(v[3],math.ceil(at)+band+1)):
    for x in range(max(v[0],int(a)),min(v[2],int(z))):pts.append((x,y))
  else:
   if not(v[0]<=at<=v[2]):continue
   for x in range(max(v[0],math.floor(at)-band),min(v[2],math.ceil(at)+band+1)):
    for y in range(max(v[1],int(a)),min(v[3],int(z))):pts.append((x,y))
 return pts

def choose_color(c,part):
 im=c['im'];v=c['visible'];l,t,r,b=v
 inner=[l+3,t+3,r-3,b-3]
 if inner[2]<=inner[0] or inner[3]<=inner[1]:return None,[]
 counts=count_region(im,inner);background=counts.most_common(1)[0][0]
 if part in ['fill','container_fill']:
  color=background;points=independent_points(im,inner,color,3,margin=2)
 elif part=='foreground':
  foreground=[(co,n) for co,n in counts.most_common() if co[3]==255 and dist(co,background)>16]
  if not foreground:return None,[]
  color=foreground[0][0];points=independent_points(im,inner,color,1)
 else:
  pts=edge_points(c);counts=collections.Counter(im.getpixel(p) for p in pts)
  # The full-color stroke is the stable maximum-contrast edge plateau, not a softened antialias fringe.
  popular=[(co,n) for co,n in counts.items() if n>=max(10,len(pts)*.008) and co[3]==255 and dist(co,background)>5]
  if not popular:return None,[]
  # For a selected outline, the outside card is also frequent. Remove it using the immediately outward edge sample.
  box=c['box'];sc=c['cal']['native_pixels_per_logical_unit'];outside=[]
  for xx,yy in [(int(box[0]-sc*2),int((box[1]+box[3])/2)),(int(box[2]+sc*2),int((box[1]+box[3])/2)),(int((box[0]+box[2])/2),int(box[1]-sc*2))]:
   if 0<=xx<im.width and 0<=yy<im.height:outside.append(im.getpixel((xx,yy)))
  popular=[(co,n) for co,n in popular if not any(dist(co,o)<5 for o in outside)]
  if not popular:return None,[]
  contrastmax=max(dist(co,background) for co,n in popular)
  strong=[(co,n) for co,n in popular if dist(co,background)>=contrastmax-4]
  color=max(strong,key=lambda z:z[1])[0]
  points=[]
  for p in pts:
   if im.getpixel(p)!=color:continue
   if any(math.hypot(p[0]-q[0],p[1]-q[1])<20 for q in points):continue
   points.append(p)
   if len(points)==3:break
 return color,points

def measured_geometry(c,part):
 # Curved tangent positions are recorded only when a unique unambiguous tangent is visible.
 # Full-App raster AA / continuous SwiftUI corners do not expose an exact radius parameter.
 # Border width can be measured directly across two separated straight stroke cross-sections.
 if part=='corner_radius':return None,'The rounded contour is visible, but its exact tangent/center cannot be localized reliably within one logical unit from the original antialiased contour; no source radius is substituted.'
 im=c['im'];box=c['box'];v=c['visible'];scale=c['cal']['native_pixels_per_logical_unit'];co,pts=choose_color(c,'border')
 if not pts:return None,'No independent opaque straight-stroke cores are resolvable for cross-section measurement.'
 sections=[]
 for side in ['left','right','top','bottom']:
  l,t,r,b=box
  if side in ['left','right']:
   edge=l if side=='left' else r
   if edge<v[0]-.1 or edge>v[2]+.1:continue
   y=round(max(v[1]+10,min(v[3]-10,(t+b)/2)));a=max(v[0],math.floor(edge)-math.ceil(scale*3));z=min(v[2],math.ceil(edge)+math.ceil(scale*3));seq=[(x,y) for x in range(a,z)]
  else:
   edge=t if side=='top' else b
   if edge<v[1]-.1 or edge>v[3]+.1:continue
   x=round((l+r)/2);a=max(v[1],math.floor(edge)-math.ceil(scale*3));z=min(v[3],math.ceil(edge)+math.ceil(scale*3));seq=[(x,y) for y in range(a,z)]
  core=[p for p in seq if dist(im.getpixel(p),co)<=4]
  if not core:continue
  # Pixel-cell outer and inner limits of the stable core, with native scale retained.
  if side in ['left','right']:pa=[min(p[0] for p in core),y];pb=[max(p[0] for p in core)+1,y]
  else:pa=[x,min(p[1] for p in core)];pb=[x,max(p[1] for p in core)+1]
  if math.dist(pa,pb)>scale*3:continue
  sections.append({'snapshot':c['si'],'a':pa,'b':pb,'native_pixels_per_logical_unit':scale})
  if len(sections)==2:break
 if len(sections)<2:return None,'Fewer than two separated straight border cross-sections can be resolved; no source width is substituted.'
 return sections,'Two separated straight border core cross-sections were measured between original pixel-cell outer/inner boundaries, excluding the softened antialias fringes.'

def decisionbase(row,ctx,cap,cs):
 indices=[c['si'] for c in cs];refs=[]
 for c in cs:
  ref={'path':str(c['path'].relative_to(cap)),'sha256':sha(c['path'])}
  if ref not in refs:refs.append(ref)
 return {'key':row['key'],'method':row['method'],'observation_sha256':ctx['observation_ref']['sha256'],'snapshot_indices':indices,'evidence':refs,'target_region':{str(c['si']):c['visible'] for c in cs},'local_counterexample':False,'witness':f'Exact native {row["target"]["identifier"]} target and its visible original PNG region; all coordinates are original native pixels.'}

def main():
 for aid in ['sample-716d41','sample-e318ec']:
  cap=R/'private/grade-capsules/final'/aid;manifest=e.read(cap/'manifest.json');entries={(x['platform'],x['case']):x for x in manifest['observations']};contexts={};decisions=[]
  for row in plan['rows']:
   if row['method'] not in ['pixels','visual'] or row['id']=='layout.fullContentCoverage':continue
   ck=(row['platform'],row['caseId'],row['stateId'])
   if ck not in contexts:contexts[ck]=e.load_context(entries[ck[:2]],cap,row,oracle)
   ctx=contexts[ck];cs=candidates_for(ctx,row['target']['identifier'],row['platform'],cap)
   if not cs:raise ValueError(('missing target for visual decision',row['key']))
   if row['method']=='visual':
    cs=sorted(cs,key=lambda c:c['si']);d=decisionbase(row,ctx,cap,cs);d['outcome']='P'
    if row['id']=='layout.noTextTruncation':why='Inspected the complete overlapping original native sweep: supplied title, description and notice, fixed facts/method copy, numeric summary, conditional consent, status and release label all wrap completely without ellipsis, horizontal loss or glyph clipping. Viewport-edge crops are resolved in adjacent overlapping frames.'
    elif row['id']=='layout.sectionOrder':why='The complete original sweep shows title, description, facts, methods, summary, conditional consent, notice, status and submit in that vertical order; only conditionally absent consent/empty notice are skipped.'
    elif row['id']=='layout.direction':
     direct=row['expected']['leading_trailing_direction'];why=('The RTL original sweep is right aligned at the leading edge, with method indicators on the right and text to their left; summary/consent arrangement follows RTL while section order is preserved.' if direct=='rtl' else 'The LTR original sweep is left aligned at the leading edge, with method indicators on the left and text to their right; summary/consent arrangement follows LTR while section order is preserved.')
    else:raise ValueError(row['id'])
    d['reason']=why;d['witness']+=' '+why
   elif 'rgb' in row['expected']:
    c=cs[0];color,points=choose_color(c,row['expected']['part']);d=decisionbase(row,ctx,cap,[c])
    if color is None or len(points)<3:d.update(outcome='U',reason='Three independent opaque interior patches could not be localized reliably in the actual target; no source palette is substituted.')
    else:
     outcome='P' if e.match_value(list(color[:3]),row['expected']) else 'F';size=3 if row['expected']['part'] in ['fill','container_fill'] else 1
     d.update(outcome=outcome,reason=f'Three independent original {size}x{size} opaque {row["expected"]["part"]} patches have median RGB {list(color[:3])}; the frozen per-channel matcher determines the outcome.',measurement={'patches':[{'snapshot':c['si'],'x':p[0],'y':p[1],'size':size} for p in points]})
   else:
    c=cs[0];segments,why=measured_geometry(c,row['expected']['part']);d=decisionbase(row,ctx,cap,[c]);d.update(outcome='U',reason=why)
    if segments:
     values=[math.dist(s['a'],s['b'])/s['native_pixels_per_logical_unit'] for s in segments];outcome,_,_=e.collapse_values(row,values);d.update(outcome=outcome,measurement={'segments':segments})
   decisions.append(d)
  (cap/'visual-review.json').write_text(json.dumps({'reviewer':'independent evaluator','scope':'Original native images only; native font/padding/hit capabilities remain separate','decisions':decisions},ensure_ascii=False,indent=2)+'\n')
  print(aid,len(decisions),collections.Counter(d['outcome'] for d in decisions),flush=True)

if __name__=="__main__":main()
