"""Original pixel contour/tangent localization for a manual geometry witness."""
import importlib.util,math,statistics,json
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('m',P/'measure_visuals.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def corners(c):
 im=c['im'];l,t,r,b=c['box'];v=c['visible'];sc=c['cal']['native_pixels_per_logical_unit'];limit=min((r-l)/3,(b-t)/2,50*sc)
 if t<v[1]-.01 or t+limit>=v[3]:return None,{'reason':'top corners obscured by original viewport'}
 edgecolor,pts=m.choose_color(c,'border')
 if edgecolor is None:
  # The submit has a filled silhouette and no explicit stroke.
  edgecolor=m.count_region(im,[math.ceil(l+(r-l)*.3),math.ceil(t+limit*.5),math.floor(r-(r-l)*.3),math.floor(t+limit*.8)]).most_common(1)[0][0]
 estimates=[];observations=[]
 for side in ['left','right']:
  exterior=im.getpixel((max(0,min(im.width-1,math.floor(l-2*sc) if side=='left' else math.ceil(r+2*sc))),round(t+limit*.6)))
  contrast=m.dist(edgecolor,exterior)
  if contrast<8:return None,{'reason':'corner/outside contrast insufficient'}
  values=[];contour=[]
  for y in range(math.ceil(t+sc*2),math.floor(t+limit)):
   xs=range(math.floor(l),math.ceil(l+limit)) if side=='left' else range(math.ceil(r)-1,math.floor(r-limit),-1)
   prev=0;previous_x=None;edge=None
   for x in xs:
    if not(0<=x<im.width and 0<=y<im.height):continue
    d=m.dist(im.getpixel((x,y)),exterior)
    if d>=contrast*.5:
     if previous_x is not None and d!=prev:
      fraction=(contrast*.5-prev)/(d-prev);edge=previous_x+.5+(x-previous_x)*fraction
     else:edge=x+.5
     break
    prev=d;previous_x=x
   if edge is None:continue
   dx=edge-l if side=='left' else r-edge;dy=y+.5-t
   if dx<sc*1.5 or dy<sc*1.5:continue
   rr=dx+dy+math.sqrt(2*dx*dy);values.append(rr);contour.append([edge,y+.5])
  if len(values)<4:return None,{'reason':'not enough independent visible curved contour samples'}
  median=statistics.median(values);mad=statistics.median(abs(x-median) for x in values)
  estimates.append(median);observations.append({'corner':side+'-top','median_radius_pixels':median,'median_absolute_deviation_pixels':mad,'sample_count':len(values),'contour_points':contour})
 if max(o['median_absolute_deviation_pixels'] for o in observations)>.7*sc or abs(estimates[0]-estimates[1])>sc:
  return None,{'reason':'actual contour does not locate a common circular tangent/center within one logical unit','corners':observations}
 segments=[]
 for side,rr in zip(['left','right'],estimates):
  if side=='left':a=[l,t+rr];bb=[l+rr,t+rr]
  else:a=[r-rr,t+rr];bb=[r,t+rr]
  segments.append({'snapshot':c['si'],'a':a,'b':bb,'native_pixels_per_logical_unit':sc})
 return segments,{'reason':'Two visible top corner outer contours localize their circular centers/tangents independently; radius segments connect the vertical tangent to its measured center. Centers derived from actual half-coverage antialias boundary samples, without expected radius or source declarations.','corners':observations}
if __name__=='__main__':
 for aid in ['sample-716d41','sample-e318ec']:
  cap=m.R/'private/grade-capsules/final'/aid;manifest=m.e.read(cap/'manifest.json');entries={(x['platform'],x['case']):x for x in manifest['observations']};out=[];review=m.e.read(cap/'visual-review.json');review_by_key={d['key']:d for d in review['decisions']}
  for row in m.plan['rows']:
   if row['method']!='pixels' or row['expected'].get('part')!='corner_radius':continue
   ctx=m.e.load_context(entries[(row['platform'],row['caseId'])],cap,row,m.oracle);cs=m.candidates_for(ctx,row['target']['identifier'],row['platform'],cap)
   for c in cs:
    seg,detail=corners(c)
    if seg:break
   vals=[math.dist(x['a'],x['b'])/x['native_pixels_per_logical_unit'] for x in seg] if seg else None
   out.append({'key':row['key'],'snapshot':c['si'],'segments':seg,'measured_radii':vals,'detail':detail})
   d=m.decisionbase(row,ctx,cap,[c]);d.update(outcome='U',reason=detail['reason'])
   if seg:
    outcome,_,_=m.e.collapse_values(row,vals);d.update(outcome=outcome,measurement={'segments':seg,'contour_localization':detail['corners']})
   review_by_key[row['key']]=d
  (m.R/'design/private/evaluation/final'/aid/'corner-localization.json').write_text(json.dumps(out,indent=2)+'\n')
  review['decisions']=list(review_by_key.values());(cap/'visual-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');print(aid,len(out),'corner records')
