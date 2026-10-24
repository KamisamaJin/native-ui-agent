from pathlib import Path
import json, xml.etree.ElementTree as ET
from PIL import Image
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=BASE/'design-review/T2'
rows=[]
for scope in ['public','private']:
 d=BASE/'design/T2'/scope; ref=json.loads((d/'reference.json').read_text())
 for case,cv in ref['cases'].items():
  for state in ['overview','permitted','requested','replaced']:
   p=d/'references'/case/(state+'.svg'); e=ET.parse(p).getroot();ns='{http://www.w3.org/2000/svg}'
   rects=e.findall(ns+'rect');band=rects[3];values={k:float(band.attrib[k]) for k in ['x','y','width','height']}
   with Image.open(p.with_suffix('.png')) as im:
    rgb=im.convert('RGB');x0,y0,w,h=[values[k] for k in ['x','y','width','height']]
    pts=[(x,y) for y in range(round(y0),round(y0+h)) for x in range(rgb.width) if rgb.getpixel((x,y))==(23,43,77)]
    bbox=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1] if pts else None
    outside=[(x,y) for x,y in pts if x<x0 or x>=x0+w]
    row={'scope':scope,'case':case,'state':state,'png_size':list(im.size),'svg_size':[float(e.attrib['width']),float(e.attrib['height'])],'status_band':values,'exact_navy_reference_ink_bbox_in_status_band_y':bbox,'reference_ink_pixels_horizontally_outside_status_band':len(outside),'measurement_scope':'Reference PNG only, never native or computed font evidence'}
    svgtext=' '.join(''.join(x.itertext()) for x in e.findall(ns+'text'))
    # Compare caller text with natural line-break whitespace removed.
    norm=lambda s:' '.join(s.split())
    fx=json.loads((d/'cases'/case/'fixtures.json').read_text());t=fx['updates'][0] if state=='replaced' else fx['initial']
    expected=[t['title'],cv['states'][state]['subtitle']['value'],cv['states'][state]['status']['value'],cv['states'][state]['disclosure']['value'],cv['states'][state]['choice']['value'],cv['states'][state]['primary']['value']]
    if state in ['permitted','requested']:
     for c in t['chapters']:expected.extend([c['title'],c['body']])
    row['expected_copy_missing_from_svg']=[x for x in expected if norm(x) not in norm(svgtext)]
    rows.append(row)
(OUT/'reference-inspection.json').write_text(json.dumps({'scope':'Independent authored SVG/PNG references; static only','rows':rows},ensure_ascii=False,indent=2)+'\n')
for row in rows:print(row['scope'],row['case'],row['state'],row['png_size'],'missingcopy',len(row['expected_copy_missing_from_svg']),'status-outside-ink',row['reference_ink_pixels_horizontally_outside_status_band'],'inkbbox',row['exact_navy_reference_ink_bbox_in_status_band_y'])
