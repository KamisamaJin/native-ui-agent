#!/usr/bin/env python3
"""Presentation crops only; quantitative grading uses original native files."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def font(size):
 for path in ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
  if Path(path).is_file():return ImageFont.truetype(path,size)
 return ImageFont.load_default()
def crop(phase,sub,platform,case):
 d=R/'evidence'/phase/sub/platform/case;o=read(d/'observation.json')
 if platform=='ios':
  bottom=o.get('coverage_screenshots',{}).get('bottom',{}).get('snapshot_index')
  snap=o['snapshots'][bottom]if bottom is not None else o['snapshots'][-1]
 else:snap=o['snapshots'][0]
 im=Image.open(d/snap['screenshot']).convert('RGB')
 if platform=='ios':
  vp=snap['viewport'];app=snap['app_frame'];sx=im.width/app['width'];sy=im.height/app['height']
  box=(round((vp['x']-app['x'])*sx),round((vp['y']-app['y'])*sy),round((vp['x']+vp['width']-app['x'])*sx),round((vp['y']+vp['height']-app['y'])*sy));im=im.crop(box)
 return im

def main():
 release=read(R/'unblinding.json');by_arm={arm:sub for sub,arm in release['submissions'].items()}
 for platform,case,title in [('android','initial_05','Android RTL: D0 / FINAL'),('ios','initial_01','iOS disabled controls, bottom viewport: D0 / FINAL')]:
  w,h=340,524;canvas=Image.new('RGB',(3*w+100,2*h+130),'#e7ecf3');draw=ImageDraw.Draw(canvas);draw.text((16,12),title,fill='#182230',font=font(22))
  for row,phase in enumerate(['d0','final']):
   draw.text((6,80+row*(h+18)),phase.upper(),fill='#182230',font=font(17))
   for col,arm in enumerate(['without_skill','skill_v1','skill_v2']):
    im=crop(phase,by_arm[arm],platform,case);im=im.resize((w,h),Image.Resampling.LANCZOS);x=80+col*w;y=68+row*(h+18);canvas.paste(im,(x,y))
    if row==0:draw.text((x+10,44),arm,fill='#182230',font=font(18))
  canvas.save(R/f'comparison-{platform}.png')
 print('Created presentation comparisons after unblinding; no image scores generated')
if __name__=='__main__':main()
