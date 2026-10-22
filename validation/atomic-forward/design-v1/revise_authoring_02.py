from pathlib import Path
import shutil,json,datetime
R=Path(__file__).resolve().parent
A=R/'authoring-attempts'/'attempt-01';A.mkdir(parents=True)
for t in ['T1','T2','T3']:shutil.move(str(R/t),str(A/t))
for n in ['generate_design.py','authored-at.json','reference-contact-sheet.png']:shutil.copy2(R/n,A/n)
(R/'authored-at.json').unlink();(R/'reference-contact-sheet.png').unlink()
p=R/'generate_design.py';s=p.read_text()
s=s.replace("'selected':'#FFD6E6E5'", "'selected':'#FFD6E6E5','onAction':'#FFF8FBFA'").replace("'selected':'#FF31575C'", "'selected':'#FF31575C','onAction':'#FF102D30'")
s=s.replace("Each card shows its severity text and its detail.","Each card shows its severity text. The selected incident detail appears only in the expanded inline dossier, so closed rows stay compact.")
s=s.replace("supporting text14. iOS", "supporting text14. Use palette ink for text on canvas/cards/notice, and onAction for primary action text. iOS")
s=s.replace("start=now();root=", "start='2026-10-22T01:14:41Z';root=")
s=s.replace("def txt(s,x,yy,ww,size=None,weight=400):", "def txt(s,x,yy,ww,size=None,weight=400,ink='ink'):")
s=s.replace('rgb("ink")', 'rgb(ink)')
s=s.replace("'in model order'", "'in model order'")
start=s.index(" grid=t['id']=='T1' and cid=='P1';")
end=s.index(" y+=8\n y+=txt",start)
replacement=''' grid=t['id']=='T1' and cid=='P1';cardw=(w-44)/2 if grid else w-32
 def card_h(item,ww):
  label=item['label']+(' · Unavailable' if not item['available'] else '')
  label_lines=len(textwrap.wrap(label,width=max(8,int((ww-40)/(fs*.53))),break_long_words=False,break_on_hyphens=False))
  detail_lines=0 if t['id']=='T2' else len(textwrap.wrap(item['detail'],width=max(8,int((ww-40)/(14*scale*.53))),break_long_words=False,break_on_hyphens=False))
  return max(80,label_lines*line+detail_lines*14*scale*1.3+44+(22*scale if t['id']=='T2' else 0))
 grid_y=y
 for i,item in enumerate(m[t['list']]):
  if t['multi'] and i in [0,2,3]: y+=txt({0:'Inspection',2:'Specialist work',3:'Care and adjustments'}[i],16,y,w-32,fs,600)+10
  xx=16+(i%2)*(cardw+12) if grid else (28 if t['id']=='T2' and c['direction']=='ltr' else 16); ww=cardw if t['id']!='T2' else w-44
  yy=grid_y if grid else y
  label=item['label']+(' · Unavailable' if not item['available'] else '')
  hh=card_h(item,ww)
  if grid:hh=max(card_h(z,ww) for z in m[t['list']][i//2*2:i//2*2+2])
  rect(xx,yy,ww,hh,'selected' if i in ([0,1] if t['multi'] else [0]) else 'surface')
  ty=yy+16;ty+=txt(('☑ ' if t['multi'] and i<2 else '☐ ' if t['multi'] else '')+label,xx+20,ty,ww-40,fs,600)+10
  if t['id']=='T2':ty+=txt(item['severity'].upper(),xx+20,ty,ww-40,12*scale,600)+6
  else:txt(item['detail'],xx+20,ty,ww-40,14*scale)
  if t['id']=='T2':
   rail_x=21 if c['direction']=='ltr' else w-21
   elements.append(f'<path d="M {rail_x} {yy} V {yy+hh+12}" stroke="#{rgb("enabled")}" stroke-width="2"/>')
  if grid:
   if i%2==1:grid_y+=hh+12;y=grid_y
  else:y+=hh+12
  if t['id']=='T2' and i==0:
   y+=txt(m[t['list']][0]['detail'],40,y+12,w-68)+28
'''
s=s[:start]+replacement+s[end:]
s=s.replace("txt(t['button'],34,y+16,w-68,fs,600)","txt(t['button'],34,y+16,w-68,fs,600,ink='onAction')")
p.write_text(s)
(R/'revision-02-record.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Independent reference self-inspection: align grid rows, measure alert-card text heights, show dossier only inline for selected alert, specify action text contrast, mirror timeline rail in RTL. No implementation or native SDK viewed.','preserved_draft':'authoring-attempts/attempt-01'},indent=2)+'\n')
