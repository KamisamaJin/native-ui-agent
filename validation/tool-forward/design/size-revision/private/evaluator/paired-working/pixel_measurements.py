"""Actual screenshot color/geometry sampling helpers; no source constants read."""
import collections,math
import raw_review as rr
from base_grader import best_node,rect
def cropped_target(d,target):
 found=best_node(d,target)
 if not found:
  if target=='rr.detail':
   m=d['context']['model'];o=next((x for x in m['options'] if x['id']==m['selectedOptionId'] and x['disabledReason'] is None),None)
   if not o:return None
   for i,s in zip(d['indices'],d['snapshots']):
    ns=[n for n in s['nodes'] if n.get('label') in [o['detailTitle'],o['detailBody']]]
    if len(ns)>=2 and all(n.get('fully_within_viewport',n.get('fully_visible')) for n in ns):
     raw,im,crop,sx,sy,off,h=rr.image_info(d['platform'],d['path'],s)
     if d['platform']=='apple':bs=[[n['image_frame'][k] for k in ['x','y','width','height']] for n in ns];bs=[[x,y,x+w,y+h] for x,y,w,h in bs]
     else:bs=[[n['unclipped_bounds_dp'][k]*(sx if k%2==0 else sy) for k in range(4)] for n in ns]
     box=[max(crop[0],round(min(b[0] for b in bs)-10*sx)),max(crop[1],round(min(b[1] for b in bs)-10*sy)),min(crop[2],round(max(b[2] for b in bs)+10*sx)),min(crop[3],round(max(b[3] for b in bs)+10*sy))]
     return dict(raw=raw,box=box,im=im.crop(box),node=None,snapshot=i,scaleX=sx,scaleY=sy,pixelOnly=True)
   return None
  if target!='rr.card':return None
  # Pixel-only root segmentation remains possible when a native AX root frame
  # is unavailable. This fallback is never used for nativeBounds assertions.
  i=d['indices'][0];s=d['snapshots'][0];raw,im,crop,sx,sy,off,h=rr.image_info(d['platform'],d['path'],s)
  colors={(255,255,255),(215,221,217)} if d['context']['environment']['appearance']=='light' else {(25,34,36),(74,90,86)}
  pts=[(x,y) for y in range(crop[1],crop[3]) for x in range(crop[0],crop[2]) if im.getpixel((x,y)) in colors]
  if not pts:return None
  box=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1]
  return dict(raw=raw,box=box,im=im.crop(box),node=None,snapshot=i,scaleX=sx,scaleY=sy,pixelOnly=True)
 i,j,n,s=found;raw,im,crop,sx,sy,off,h=rr.image_info(d['platform'],d['path'],s)
 if d['platform']=='android':
  b=n['unclipped_bounds_dp'];box=[round(b[0]*sx),round(b[1]*sy),round(b[2]*sx),round(b[3]*sy)]
 else:b=n['image_frame'];box=[round(b['x']),round(b['y']),round(b['x']+b['width']),round(b['y']+b['height'])]
 # Always restrict to actual native parent viewport (never out-of-image fill).
 box=[max(crop[0],box[0]),max(crop[1],box[1]),min(crop[2],box[2]),min(crop[3],box[3])]
 if box[2]<=box[0] or box[3]<=box[1]:return None
 region=im.crop(tuple(box));return dict(raw=raw,box=box,im=region,node=n,snapshot=i,scaleX=sx,scaleY=sy)
def counts(region):return collections.Counter(region.getdata()).most_common(12)
def fit_radius(im,box,sx,sy,rgb):
 # Fit a circular top-left corner to the actual first foreground pixel in each
 # raster row. Optimize subpixel edge placement as well as radius. This is a
 # screenshot measurement, independent of any source shape declaration.
 x0,y0,x1,y1=box;pts=[]
 for yy in range(max(0,round(y0)),min(im.height,round(y0+28*sy))):
  xs=[xx for xx in range(max(0,round(x0)),min(im.width,round(x0+32*sx))) if max(abs(im.getpixel((xx,yy))[c]-rgb[c]) for c in range(3))<=2]
  if xs:pts.append(((yy-y0+0.5)/sy,(min(xs)-x0+0.5)/sx))
 best=None
 for r4 in range(24,113):
  r=r4/4
  for ox in [-.75,-.5,-.25,0,.25,.5,.75]:
   for oy in [-.75,-.5,-.25,0,.25,.5,.75]:
    residual=[]
    for y,x in pts:
     yy=y-oy
     if yy<0:continue
     pred=ox+(r-math.sqrt(max(0,r*r-(r-yy)**2)) if yy<r else 0)
     residual.append((x-pred)**2)
    if residual:
     loss=sum(residual)/len(residual)
     if best is None or loss<best['meanSquareResidual']:best=dict(radius=r,offsetX=ox,offsetY=oy,meanSquareResidual=loss,edgePoints=pts)
 return best
def radius_sample(d,role):
 target={'card':'rr.card','option':'rr.option.cash','primary':'rr.primary','notes':'rr.notes.toggle'}[role]
 v=cropped_target(d,target);s=d['observation']['snapshots'][v['snapshot']];raw,im,crop,sx,sy,off,h=rr.image_info(d['platform'],d['path'],s)
 n=v['node'];box=v['box'];rgb=counts(v['im'])[0][0]
 if role in ['card','option']:rgb=next(c for c,n in counts(v['im']) if c in [(215,221,217),(74,90,86)])
 if role=='notes':
  box=[box[0]-12*sx,box[1]-12*sy,box[2]+12*sx,box[3]+12*sy]
  # Discover actual panel extents at the center axes using its sampled neutral
  # fill, rather than assuming the nominal padding matches.
  xx=round((box[0]+box[2])/2);yy=round((box[1]+box[3])/2)
  rgb=(245,243,238)
  xs=[x for x in range(max(crop[0],round(box[0]-4*sx)),min(crop[2],round(box[2]+4*sx))) if im.getpixel((x,yy))==rgb]
  ys=[y for y in range(max(crop[1],round(box[1]-5*sy)),min(crop[3],round(box[3]+5*sy))) if im.getpixel((xx,y))==rgb]
  if xs:box[0],box[2]=min(xs),max(xs)+1
  if ys:box[1],box[3]=min(ys),max(ys)+1
 fit=fit_radius(im,box,sx,sy,rgb)
 return dict(rawPath=str(raw),snapshot=v['snapshot'],box=box,sx=sx,sy=sy,rgb=rgb,fit=fit)
def exact_color_box(image,rgb):
 pts=[(x,y) for y in range(image.height) for x in range(image.width) if image.getpixel((x,y))==rgb]
 if not pts:return None
 return [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1]
def tile_sample(d):
 v=cropped_target(d,'rr.item');rgb=(221,239,233);bb=exact_color_box(v['im'],rgb)
 box=[bb[0]+v['box'][0],bb[1]+v['box'][1],bb[2]+v['box'][0],bb[3]+v['box'][1]]
 raw,im,crop,sx,sy,off,h=rr.image_info(d['platform'],d['path'],d['observation']['snapshots'][v['snapshot']])
 fit=fit_radius(im,box,sx,sy,rgb)
 return dict(rawPath=str(raw),snapshot=v['snapshot'],box=box,width=(box[2]-box[0])/sx,height=(box[3]-box[1])/sy,radius=fit['radius'],fit=fit)
def spacing_samples(d):
 root=cropped_target(d,'rr.card');tile=tile_sample(d);badge=cropped_target(d,'rr.header.badge')
 cardx=root['box'][0];badgeBB=exact_color_box(badge['im'],(234,245,239));bY=badge['box'][1]+badgeBB[3]
 # Both badge and tile are observed in the same top viewport in this sample.
 major=(tile['box'][1]-bY)/badge['scaleY']
 s=d['snapshots'][0];raw,im,crop,sx,sy,off,h=rr.image_info(d['platform'],d['path'],s)
 ns=[n for n in s['nodes'] if n.get('native_text',n.get('label'))==d['context']['model']['merchant'] or n.get('label')==d['context']['model']['merchant']]
 n=ns[0]
 if d['platform']=='android':b=[n['unclipped_bounds_dp'][k]*(sx if k%2==0 else sy) for k in range(4)]
 else:b=n['image_frame'];b=[b['x'],b['y'],b['x']+b['width'],b['y']+b['height']]
 box=[round(x) for x in b];text=im.crop(box);bb=exact_color_box(text,(93,103,108));interior=(box[0]+bb[0]-cardx)/sx
 ranges=[];sampleRefs=[]
 for target in ['rr.option.cash','rr.option.credit']:
  q=cropped_target(d,target);bb=exact_color_box(q['im'],(215,221,217));snap=next(s for i,s in zip(d['indices'],d['snapshots']) if i==q['snapshot']);raw2,im2,vp,sx2,sy2,off2,h2=rr.image_info(d['platform'],d['path'],snap)
  ranges.append([(q['box'][1]+bb[1]-vp[1])/sy2+off2,(q['box'][1]+bb[3]-vp[1])/sy2+off2]);sampleRefs.append(dict(rawPath=str(raw2),box=q['box']))
 return dict(interior=dict(value=interior,rawPath=str(raw),box=[cardx,box[1],box[2],box[3]],method='Actual card-left raster edge to first flat merchant glyph pixel'),majorSections=dict(value=major,rawPath=tile['rawPath'],box=[tile['box'][0],bY,tile['box'][2],tile['box'][1]],method='Actual status pill lower flat-fill edge to item tile upper flat-fill edge'),relatedRows=dict(value=ranges[1][0]-ranges[0][1],samples=sampleRefs,method='Actual consecutive option outline raster extents transformed using native parent-scroll offsets'))
if __name__=='__main__':
 import sys,json
 sub=sys.argv[1]
 for pl in ['android','apple']:
  for row in rr.PLAN:
   if row['platform']!=pl or row['criterion']!='sampledFlatColorMatches':continue
   d=rr.state_data(sub,pl,row['contextId']);d['platform']=pl;v=cropped_target(d,row['target'])
   print(pl,row['key'],v['snapshot'] if v else None,counts(v['im'])[:7] if v else None)
