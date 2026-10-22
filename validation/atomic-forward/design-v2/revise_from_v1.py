from pathlib import Path
import json,hashlib,shutil,datetime
R=Path(__file__).resolve().parent;V=R.parent/'design-v1'
s=(V/'generate_design.py').read_text().replace('cohort design-v1','cohort design-v2').replace("'2026-10-22T01:14:41Z'","'2026-10-22T01:37:31Z'")
s=s.replace("scope':'candidate-v8/ only", "scope':'candidate-v8/ only")
s=s.replace("sample([.02,.05,.035,.95]", "sample([.02,.05,.03,.95]")
s=s.replace("'footer':t['footer'],initialDetailsExpanded", "'footer':t['footer'],initialDetailsExpanded") # explicit model extension below
s=s.replace("d[t['list']]=items", "d['guidance']=t['detail']\n d[t['list']]=items")
s=s.replace("items.append(x)", "x['unavailableReason']=({'T1':'Training supervisor is unavailable for this station.','T2':'Sensor is on a maintenance hold; field acknowledgement is paused.','T3':'This specialist repair is not offered at the community workshop.'}[t['id']] if i==2 else ('Availability changed: the duty supervisor paused new requests.' if not x['available'] else ''))\n  items.append(x)")
s=s.replace("r['cases'][cid]['states'][s]={'summary'", "if s in ['baseline','blocked','replaced']:evt=[]\n   r['cases'][cid]['states'][s]={'summary'")
old="Across every captured part of this exact state, are all title, subtitle, notice, choice labels/details, disclosure content, summary, action label and footer words readable in natural wrapped lines without truncation or ellipsis? Evaluate wrapping only; spacing collisions have their own atom."
new="Considering only text required to be visible by this exact state's current selection and disclosure rules, are all visible title, subtitle, notice, choice labels, visible item details/reasons, visible disclosure content, summary, action label and footer words readable in natural wrapped lines without truncation or ellipsis? Deliberately collapsed guidance and unselected incident dossiers are excluded. If required text is missing, answer unknown and identify it; missing text cannot count as correct wrapping. Visible word clipping or ellipsis answers false. Evaluate wrapping only; spacing collisions have their own atom. A true answer still requires complete exact-state coverage."
assert old in s;s=s.replace(old,new)
s=s.replace("itemargs='id = s(\"id\"), label = s(\"label\"), detail = s(\"detail\"), available = this[\"available\"]!!.jsonPrimitive.boolean'", "itemargs='id = s(\"id\"), label = s(\"label\"), detail = s(\"detail\"), unavailableReason = s(\"unavailableReason\"), available = this[\"available\"]!!.jsonPrimitive.boolean'")
s=s.replace('notice = input.s("notice"), footer = input.s("footer"),', 'notice = input.s("notice"), footer = input.s("footer"), guidance = input.s("guidance"),')
s=s.replace('`available: Bool`{itemextra}', '`available: Bool`, `unavailableReason: String`{itemextra}')
s=s.replace('`footer: String`, `{multi_field}`', '`footer: String`, `guidance: String`, `{multi_field}`')
s=s.replace('detail: String, available: Boolean{itemextra.replace', 'detail: String, available: Boolean, unavailableReason: String{itemextra.replace')
s=s.replace('notice: String, footer: String, {kfield}', 'notice: String, footer: String, guidance: String, {kfield}')
s=s.replace("{cb.replace('; ', ', ')}, onDetailsChange: (Bool) -> Void", "{cb.split('; ')[0]}, onDetailsChange: (Bool) -> Void, {cb.split('; ')[1]}")
s=s.replace('Unavailable entries remain visible with a reason and a real disabled control.', 'Unavailable entries remain visible with the literal status “Unavailable”, their nonempty caller-supplied unavailableReason, and a real disabled control. available=true requires unavailableReason=""; available=false requires a nonempty reason. The component displays that reason verbatim below the item label (and severity on T2), never invents a reason and never substitutes ordinary detail for it.')
s=s.replace('A non-interactive leading rail and time/severity marker sit outside each select button.', 'Only the non-interactive leading rail sits outside each select button. The time-bearing item label and uppercase severity are both inside the single colored selection button, matching the reference; there is no separate external time/severity marker.')
s=s.replace('when child width is at least 320 native units and text size is normal.', 'when child width is at least320 native units and text size is at most iOS DynamicTypeSize.large or Android fontScale<=1.0, respectively.')
s=s.replace("Opening with no selection shows the model's general guidance (first item's detail).", "T1 and T3 global disclosure content is exactly model.guidance. T2 opening with no selection shows model.guidance in a full-width block immediately below the disclosure; with a selection it instead shows only that incident's detail inline below its selected card. Collapsed content and unselected incident details are intentionally hidden.")
s=s.replace('No fixed text height, line limit, ellipsis or clipping.', 'No fixed text height, line limit, ellipsis or clipping. Wrap naturally at spaces and hyphens; if one unbroken segment exceeds the available text width, break between characters while preserving every character. Grow the surrounding block for every added line.')
s=s.replace('Those remain full brief requirements outside this selected denominator.', 'Also outside this selected ledger are T1 grid column count/breakpoint; T2 rail/severity/dossier placement and moving an open dossier on selection; T3 grouping and deselecting one item while preserving others; selected-background treatment, every unsampled canvas region and remaining typography hierarchy. Wrapping/overlap atoms cannot certify these features. Those remain full brief requirements outside this selected denominator.')
s=s.replace('Synthesized Codable keys exactly match fixtures', 'unavailableReason is a nonoptional String: empty iff available, otherwise the exact visible caller-supplied reason. Model guidance is the exact global/no-selection disclosure body; selected T2 dossier uses the selected item detail. T2 label includes its time; uppercase severity is inside the same selection button, only its rail is external. Synthesized Codable keys exactly match fixtures')
# Replace the drawing implementation with actual metric-based wrap accounting.
start=s.index('def draw(t,cid,folder,r):');end=s.index('\ndef generate():',start)
newdraw='''def draw(t,cid,folder,r):
 c=CASES[cid];m=input_model(t,c,0);cols=COLORS[c['theme']];w=c['width']-32;scale=1 if cid=='P1' else (1.42 if cid=='P2' else 1.18);fs=16*scale
 rgb=lambda k:cols[k][3:]
 fonts={False:fitz.Font('helv'),True:fitz.Font('hebo')};elements=[];audit=[]
 def wrap(value,width,size,weight=400):
  font=fonts[weight>=600];limit=width-2;lines=[]
  for para in value.split('\\n'):
   line=''
   for word in para.split():
    if line and font.text_length(line+' '+word,fontsize=size)<=limit:line+=' '+word;continue
    if line:lines.append(line);line=''
    # Prefer wrapping a hyphenated word at its existing hyphens, then characters.
    segments=[];part=''
    for char in word:
     part+=char
     if char=='-':segments.append(part);part=''
    if part:segments.append(part)
    for seg in segments:
     if font.text_length(line+seg,fontsize=size)<=limit:line+=seg;continue
     if line:lines.append(line);line=''
     for char in seg:
      if line and font.text_length(line+char,fontsize=size)>limit:lines.append(line);line=''
      line+=char
   lines.append(line)
  return lines
 def h(s,width,size,weight=400):return len(wrap(s,width,size,weight))*size*1.3
 def rect(x,y,ww,hh,color):elements.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" rx="10" fill="#{rgb(color)}"/>')
 def txt(value,x,y,ww,size=None,weight=400,ink='ink'):
  size=size or fs;lines=wrap(value,ww,size,weight)
  for j,line in enumerate(lines):
   tw=fonts[weight>=600].text_length(line,fontsize=size);right=c['direction']=='rtl';xx=x+ww if right else x;anchor='end' if right else 'start'
   elements.append(f'<text x="{xx:.3f}" y="{y+size+j*size*1.3:.3f}" font-size="{size:.3f}" font-family="Arial, sans-serif" font-weight="{weight}" fill="#{rgb(ink)}" text-anchor="{anchor}">{html.escape(line)}</text>')
   audit.append(dict(text=line,x_min=xx-tw if right else xx,x_max=xx if right else xx+tw,y_top=y+j*size*1.3,y_bottom=y+(j+1)*size*1.3,available_width=ww))
  return len(lines)*size*1.3
 y=16;y+=txt(m['title'],16,y,w-32,22*scale,600)+12;y+=txt(m['subtitle'],16,y,w-32)+12
 nh=h(m['notice'],w-64,fs)+32;rect(16,y,w-32,nh,'notice');txt(m['notice'],32,y+16,w-64);y+=nh+20
 if t['id']=='T2':y+=txt('Hide '+t['details'].lower(),16,y,w-32,fs,600)+16
 grid=t['id']=='T1' and cid=='P1';cw=(w-44)/2 if grid else w-32
 def label(item):return ('☑ ' if t['multi'] and item['id'] in ['a','b'] else '☐ ' if t['multi'] else '')+item['label']+(' · Unavailable' if not item['available'] else '')
 def card_h(item,ww):
  z=32+h(label(item),ww-40,fs,600)+10
  if t['id']=='T2':z+=h(item['severity'].upper(),ww-40,12*scale,600)+6
  if item['unavailableReason']:z+=h(item['unavailableReason'],ww-40,14*scale)+10
  if t['id']!='T2':z+=h(item['detail'],ww-40,14*scale)
  return max(80,z)
 gy=y
 for i,item in enumerate(m[t['list']]):
  if t['multi'] and i in [0,2,3]:y+=txt({0:'Inspection',2:'Specialist work',3:'Care and adjustments'}[i],16,y,w-32,fs,600)+10
  xx=16+(i%2)*(cw+12) if grid else (28 if t['id']=='T2' and c['direction']=='ltr' else 16);ww=cw if t['id']!='T2' else w-44;yy=gy if grid else y
  hh=max(card_h(z,ww) for z in m[t['list']][i//2*2:i//2*2+2]) if grid else card_h(item,ww)
  rect(xx,yy,ww,hh,'selected' if i in ([0,1] if t['multi'] else [0]) else 'surface');ty=yy+16;ty+=txt(label(item),xx+20,ty,ww-40,fs,600)+10
  if t['id']=='T2':ty+=txt(item['severity'].upper(),xx+20,ty,ww-40,12*scale,600)+6
  if item['unavailableReason']:ty+=txt(item['unavailableReason'],xx+20,ty,ww-40,14*scale)+10
  if t['id']!='T2':txt(item['detail'],xx+20,ty,ww-40,14*scale)
  if t['id']=='T2':
   rail=21 if c['direction']=='ltr' else w-21;elements.append(f'<path d="M {rail} {yy} V {yy+hh+12}" stroke="#{rgb("enabled")}" stroke-width="2"/>')
  if grid:
   if i%2==1:gy+=hh+12;y=gy
  else:y+=hh+12
  if t['id']=='T2' and i==0:y+=txt(item['detail'],40,y+12,w-68)+28
 y+=8;y+=txt(r['cases'][cid]['states']['expanded']['summary']['value'],16,y,w-32,fs,600)+20
 if t['id']!='T2':y+=txt('Hide '+t['details'].lower(),16,y,w-32,fs,600)+12;y+=txt(m['guidance'],16,y,w-32)+20
 bh=max(56,h(t['button'],w-68,fs,600)+32);rect(16,y,w-32,bh,'enabled');txt(t['button'],34,y+16,w-68,fs,600,'onAction');y+=bh+20;y+=txt(m['footer'],16,y,w-32,14*scale)+16
 assert all(z['x_min']>=12 and z['x_max']<=w-12 for z in audit),audit
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{int(y)+1}" viewBox="0 0 {w} {int(y)+1}"><rect width="{w}" height="{int(y)+1}" rx="12" fill="#{rgb("canvas")}"/>'+''.join(elements)+'</svg>'
 path=folder/f'reference-{cid}-expanded.svg';write(path,svg);doc=fitz.open(stream=svg.encode(),filetype='svg');pdf=fitz.open('pdf',doc.convert_to_pdf());pdf[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(str(folder/f'reference-{cid}-expanded.png'))
 write(folder/f'reference-{cid}-expanded.meta.json',{'case':cid,'state':'expanded','input_index':0,'source':'Independent SVG authoring, revised from v1 design review; no implementation','width_native':w,'content_height_design':int(y)+1,'host_viewport_height':600,'scope':'Structural reference, not native font pixel baseline','svg_sha256':sha(path),'png_sha256':sha(folder/f'reference-{cid}-expanded.png')})
 write(folder/f'reference-{cid}-text-fit-audit.json',{'metrics':'MuPDF Helvetica/Helvetica-Bold mapped from SVG Arial; conservative2-unit width reserve; literal hyphens retained and overly long segments broken between characters','empty_canvas_gutter':12,'all_text_inside_canvas_gutter':True,'lines':audit})
'''
s=s[:start]+newdraw+s[end:]
(R/'generate_design.py').write_text(s)
for name in ['validate_and_lock.py','replay_contract.py']:
 shutil.copy2(V/name,R/name)
# Explicit input source is retained unchanged in v1, including all historical authoring attempts.
record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_v1_cohort_seal_sha256':hashlib.sha256((V/'seal.json').read_bytes()).hexdigest(),'retained_rules':14,'retained_states_per_case':7,'changes':['Canvas strip x range .02-.03 entirely within12-unit gutter at all allowed widths','Metric-aware independent SVG word wrapping, growing blocks, all visible text/reasons within declared content bounds','Add item.unavailableReason and model.guidance to API/fixtures/bridge; unavailable reasons caller-supplied','T2 only rail outside; time-bearing label and severity inside actual selection button','Wrapping proposition explicitly quantifies required-visible text and excludes intentional collapse/unselected dossiers; missing required text unknown','Unused activation event anchors empty; exact T1 text-scale grid threshold; explicit remaining out-of-ledger features'],'process_note':'Initial combined cat of review.json emitted overbroad truncated inputHashes text. No listed target was opened and no hashes informed the design. Follow-up consumed blockers fields only. No assignment or candidate source was inspected.'}
(R/'REVISION-RECORD.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
