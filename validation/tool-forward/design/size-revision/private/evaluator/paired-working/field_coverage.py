"""Generate candidate field coverage from actual native leaves/rectangles for manual pixel review."""
import math,json
import raw_review as rr

def text_catalog(m):
 o=next((x for x in m['options'] if x['id']==m['selectedOptionId'] and x['disabledReason'] is None),None)
 q={'header.merchant':m['merchant'],'header.heading':m['heading'],'header.orderReference':m['orderReference'],'header.intro':m['intro'],'header.statusLabel':m['statusLabel'],'summary.totalLabel':m['totalLabel'],'summary.totalValue':m['totalValue'],'summary.totalFootnote':m['totalFootnote'],'context':m['contextMessage'],'optionsTitle':m['optionsTitle'],'notes.title':m['notes']['title'],'notes.body':m['notes']['body'],'sizes.title':m['sizesTitle'],'primary':o['primaryLabel'] if o else m['idlePrimaryLabel'],'keep':m['keepLabel'],'done':m['doneLabel'],'progress.title':m['progressTitle'],'progress.body':m['progressBody'],'result.title':m['resultTitle'],'result.body':m['resultBody'],'result.reference':m['resultReference']}
 if m['deadline']:q['deadline']=m['deadline']['text']
 q.update({'item.'+k:v for k,v in m['item'].items() if k!='accent'})
 for x in m['options']:
  q.update({'option.'+x['id']+'.'+k:x[k] for k in ['title','description','amountLabel','tag'] if x[k] is not None})
  if x['disabledReason'] is not None:q['option.'+x['id']+'.disabledReason']=x['disabledReason'];q['option.'+x['id']+'.reason']=x['disabledReason']
 for x in m['sizes']:
  q['size.'+x['id']+'.label']=x['label']
  if x['unavailableReason']:q['size.'+x['id']+'.reason']=x['unavailableReason']
 for x in m['amountRows']:
  q['amount.'+x['id']+'.label']=x['label'];q['amount.'+x['id']+'.value']=x['value']
 for i,x in enumerate(m['notes']['bullets']):q['notes.bullet.'+str(i)]=x
 if o:q.update({'detail.title':o['detailTitle'],'detail.body':o['detailBody'],'ack':o['acknowledgementLabel']})
 q['gate']=m['strings']['noOptions'] if not any(x['disabledReason'] is None for x in m['options']) else m['strings']['chooseOption'] if o is None else m['strings']['chooseSize'] if o['kind']=='exchange' and not any(x['id']==m['selectedSizeId'] and x['unavailableReason'] is None for x in m['sizes']) else m['strings']['acceptTerms'] if o['acknowledgementLabel'] is not None and not m['acknowledgementAccepted'] else m['strings']['ready']
 return q

def bounds(n,pl):
 if pl=='android':return n.get('unclipped_bounds_dp')
 b=n.get('frame',{});v=[b.get(k) for k in ['x','y','width','height']]
 if not all(rr.finite(x) for x in v):return None
 return [v[0],v[1],v[0]+v[2],v[1]+v[3]]
def fully_visible(n,s,pl):
 b=bounds(n,pl)
 if not b or not all(rr.finite(x) for x in b) or b[2]<=b[0] or b[3]<=b[1]:return False
 vp=[0,0,s['logical_viewport_dp']['width'],600] if pl=='android' else [s['viewport']['x'],s['viewport']['y'],s['viewport']['x']+s['viewport']['width'],s['viewport']['y']+600]
 return b[0]>=vp[0]-.5 and b[1]>=vp[1]-.5 and b[2]<=vp[2]+.5 and b[3]<=vp[3]+.5

def field_nodes(d,fid):
 text=text_catalog(d['context']['model']).get(fid);out=[]
 if text is None:return out
 for i,s in zip(d['indices'],d['snapshots']):
  if i not in d['pixelIndices']:continue
  ns=s['nodes'];cand=[(j,n) for j,n in enumerate(ns) if n.get('label')==text]
  # Prefer actual text leaves over combined aggregate/control duplicates.
  leaves=[(j,n) for j,n in cand if ('font_sp' in n if d['platform']=='android' else n.get('role_raw')==48)]
  if leaves:cand=leaves
  anchor=None
  if fid.startswith('amount.') and fid.endswith('.value'):anchor=text_catalog(d['context']['model']).get(fid[:-5]+'label')
  if fid=='summary.totalValue':anchor=d['context']['model']['totalLabel']
  if anchor:
   aa=[j for j,n in enumerate(ns) if n.get('label')==anchor]
   if len(aa)==1 and cand:
    dist=min(abs(j-aa[0]) for j,n in cand);cand=[(j,n) for j,n in cand if abs(j-aa[0])==dist]
  if len(cand)>1:
   # Ambiguous duplicate amount labels cannot automatically cover another field.
   unique={(tuple(bounds(n,d['platform']) or []),n.get('label')) for _,n in cand}
   if len(unique)>1:continue
  for j,n in cand:
   if fully_visible(n,s,d['platform']):out.append((i,j,n,s))
 return out

def candidate_review(sub,pl,cid):
 d=rr.state_data(sub,pl,cid);d['platform']=pl;c=d['context'];fields=c['visualInventory']['allVisibleFieldIds'] if c['fullVisualCheckpoint'] else []
 return dict(platform=pl,contextId=cid,epoch=d['epoch'],anchorIndex=d['anchorIndex'],pixelIndices=d['pixelIndices'],candidateFields=[f for f in fields if field_nodes(d,f)],candidateFieldSources={f:[dict(snapshotIndex=i,nodeIndex=j) for i,j,n,s in field_nodes(d,f)] for f in fields if field_nodes(d,f)},allRequiredFieldIds=fields,policy='Candidates require actual complete finite text bounds in a captured native viewport. Manual direct image review must confirm strings/drawing; candidate metadata alone is not pixel acceptance.')
if __name__=='__main__':
 out=[]
 for pl in ['android','apple']:
  for cid,c in rr.CTX.items():
   if c['fullVisualCheckpoint']:out.append(candidate_review('submission-4f4364',pl,cid))
 rr.write(rr.HERE/'candidate-field-coverage.json',out)
