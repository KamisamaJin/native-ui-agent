from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import textwrap,html,json
P=Path(__file__).resolve().parents[1]/'public';font='/System/Library/Fonts/Supplemental/Arial.ttf'
for case,width,dark in [('P1',390,False),('P2',300,True)]:
 model=json.loads((P/'cases'/case/'fixtures.json').read_text())['initial'];margin=16;content=width-2*margin;fill='#182635' if dark else '#FFFFFF';ink='#F1F5F9' if dark else '#172B3A';body='#CBD5E1' if dark else '#425466';accent='#8ACBEE' if dark else '#155E83';selected='#233E52' if dark else '#E7F2F8';canvas='#0D1420' if dark else '#EDF1F6';ops=[];y=24
 def rect(x,y,w,h,color,stroke=None,r=8):ops.append(('rect',x,y,w,h,color,stroke,r))
 def text(t,size=16,color=None,bold=False,pad=16):
  global y
  f=ImageFont.truetype(font,size);usable=content-2*pad;words=t.split();lines=[];line=''
  for word in words:
   test=(line+' '+word).strip()
   if f.getlength(test)>usable and line:lines.append(line);line=word
   else:line=test
  if line:lines.append(line)
  for line in lines:ops.append(('text',margin+pad,y,line,size,color or ink,bold));y+=int(size*1.32)
 def gap(n=20):
  global y;y+=n
 def option(t,sel=False,enabled=True):
  global y
  start=y;y+=12;before=len(ops);text(('● ' if sel else '○ ')+t,16,ink if enabled else body,pad=28);y+=12
  ops.insert(before,('rect',margin+16,start,content-32,y-start,selected if sel else fill,accent if sel else body,8));gap(8)
 y+=16;text(model['title'],22,bold=True);gap(8);text(model['detail'],16,body);gap()
 text('Courses',14,bold=True);gap(8)
 for i,c in enumerate(model['courses']):
  option(c['title'],i==0);text(c['detail'],14,body,pad=28);gap(12)
 text('Attendance',14,bold=True);gap(8);option('Remote',True);option('In person',False,model['courses'][0]['onsiteAvailable']);gap(12)
 text('Seats',14,bold=True);gap(8)
 for n in (1,3,6):option(f'{n} '+('seat' if n==1 else 'seats'),n==1)
 gap(12);option('Printed workbook',False,False);gap(12)
 start=y;y+=12;text('Total $90.00 · 1 seat · Remote · No workbooks',18,bold=True,pad=28);y+=12;ops.insert(len(ops)-2,('rect',margin+16,start,content-32,y-start,selected,None,8));gap(16)
 text('Choose options, then reserve.',16,body);gap(16)
 for label,color in [('Reserve seats',accent),('Edit selection',body)]:
  rect(margin+16,y,content-32,48,color);ops.append(('text',margin+28,y+13,label,16,canvas,True));y+=56
 gap(16);height=y+24;im=Image.new('RGB',(width,height),canvas);dr=ImageDraw.Draw(im);dr.rounded_rectangle((margin,24,width-margin,height-24),radius=16,fill=fill)
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',f'<rect width="{width}" height="{height}" fill="{canvas}"/>',f'<rect x="{margin}" y="24" width="{content}" height="{height-48}" rx="16" fill="{fill}"/>']
 for op in ops:
  if op[0]=='rect':
   _,x,yy,w,h,c,st,r=op;dr.rounded_rectangle((x,yy,x+w,yy+h),r,fill=c,outline=st,width=1);svg.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{h}" rx="{r}" fill="{c}" stroke="{st or "none"}"/>')
  else:
   _,x,yy,t,size,c,bold=op;f=ImageFont.truetype(font,size);x=(width-x-f.getlength(t)) if dark else x;dr.text((x,yy),t,font=f,fill=c);svg.append(f'<text x="{x}" y="{yy+size}" fill="{c}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{600 if bold else 400}">{html.escape(t)}</text>')
 svg.append('</svg>');out=P/'references';out.mkdir(exist_ok=True);(out/f'{case}.svg').write_text('\n'.join(svg));im.save(out/f'{case}.png')
