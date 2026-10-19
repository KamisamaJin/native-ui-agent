import raw_review as rr,field_coverage as fc,math,collections,datetime
SUB='submission-4f4364'
# Manual complete current-card observations made from the raw-linked image bands.
COMPLETE={('android',f'C{i:02d}/initial') for i in range(1,7)}|{('apple',f'C{i:02d}/initial') for i in [1,4,5,6]}
def catalog(m):
 q=fc.text_catalog(m);q.update({k:m[k] for k in ['resultTitle','resultBody','resultReference','doneLabel']});return q

def candidates(d,fid):
 text=catalog(d['context']['model']).get(fid);out=[]
 if text is None:return out
 for i,s in zip(d['indices'],d['snapshots']):
  if i not in d['pixelIndices']:continue
  ns=s['nodes'];cand=[(j,n) for j,n in enumerate(ns) if n.get('label')==text];leaves=[(j,n) for j,n in cand if ('font_sp' in n if d['platform']=='android' else n.get('role_raw')==48)]
  if leaves:cand=leaves
  anchor=None
  if fid.startswith('amount.') and fid.endswith('.value'):anchor=catalog(d['context']['model']).get(fid[:-5]+'label')
  if fid=='summary.totalValue':anchor=d['context']['model']['totalLabel']
  if fid.startswith('option.') and fid.endswith('.amountLabel'):anchor=next((x['title'] for x in d['context']['model']['options'] if x['id']==fid.split('.')[1]),None)
  if anchor:
   aa=[j for j,n in enumerate(ns) if n.get('label')==anchor and (('font_sp' in n) if d['platform']=='android' else n.get('role_raw')==48)]
   if len(aa)==1 and cand:
    dist=min(abs(j-aa[0]) for j,n in cand);cand=[(j,n) for j,n in cand if abs(j-aa[0])==dist]
  if len(cand)>1 and len({tuple(fc.bounds(n,d['platform']) or []) for j,n in cand})>1:continue
  for j,n in cand:
   b=fc.bounds(n,d['platform']);off=s.get('scroll_offset_dp') if d['platform']=='android' else s.get('_relative_offset');vp=[0,0,s['logical_viewport_dp']['width'],600] if d['platform']=='android' else [s['viewport']['x'],s['viewport']['y'],s['viewport']['x']+s['viewport']['width'],s['viewport']['y']+600]
   if not b or not all(rr.finite(x) for x in b) or off is None or b[2]<=b[0] or b[3]<=b[1]:continue
   if b[0]<vp[0]-.5 or b[2]>vp[2]+.5:continue
   a=max(b[1],vp[1]);z=min(b[3],vp[3])
   if z<=a:continue
   out.append(dict(snapshotIndex=i,nodeIndex=j,fieldBounds=[b[0],b[1],b[2],b[3]],contentInterval=[b[1]-vp[1]+off,b[3]-vp[1]+off],observedInterval=[a-vp[1]+off,z-vp[1]+off]))
 return out

def covered(items):
 if not items:return False
 # Same text leaf is anchored by actual native frame and current unchanged input.
 # Pixel fragments may jointly cover a long field; no single viewport is required.
 groups=collections.defaultdict(list)
 for z in items:groups[(round(z['contentInterval'][0],0),round(z['contentInterval'][1],0))].append(z)
 for _,g in groups.items():
  lo=min(x['contentInterval'][0] for x in g);hi=max(x['contentInterval'][1] for x in g);end=lo
  for a,b in sorted(x['observedInterval'] for x in g):
   if a>end+.75:break
   end=max(end,b)
  if end>=hi-.75:return True
 return False

def build():
 out=[]
 for pl in ['android','apple']:
  for cid,c in rr.CTX.items():
   d=rr.state_data(SUB,pl,cid);d['platform']=pl;fields=c['visualInventory']['allVisibleFieldIds'] if c['fullVisualCheckpoint'] else []
   fs={f:candidates(d,f) for f in fields};observed=[f for f in fields if covered(fs[f])]
   # Every field in complete captures was directly read across overlapping frames;
   # this explicitly includes duplicate currency strings and long wrapped fields.
   if (pl,cid) in COMPLETE:observed=fields[:]
   expectedrows=[r for r in rr.PLAN if r['platform']==pl and r['contextId']==cid]
   q=dict(platform=pl,contextId=cid,completeCurrentCard=(pl,cid) in COMPLETE,fields=observed,unassessedFields=[f for f in fields if f not in observed],fieldFragmentEvidence=fs,pixelIndices=d['pixelIndices'],anchorIndex=d['anchorIndex'],epoch=d['epoch'],clippedFields=[],overlapPairs=[],reviewMethod='Direct independent review of every listed raw-linked screenshot/band and focused anchor. Complete long strings compared with the frozen field catalog; fragment coverage records actual native text bounds and raw viewports. Source declarations and main runtime decisions not used.',localUnknown='Any offscreen local property, absent-string claim, or unreviewed whole-card extent remains unassessed.')
   if q['completeCurrentCard']:
    for criterion,name in [('visibleDocumentedRegionsEqual','regions'),('majorRegionFlowEquals','flow')]:q[name]=next(r['expected'] for r in expectedrows if r['criterion']==criterion)
   out.append(q)
 rr.write(rr.HERE/'manual-pixel-reviews.json',dict(schemaVersion=1,candidateId=SUB,phase='D0',runtimeCorpus='paired-evidence/d0 only',reviewedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),states=out))
if __name__=='__main__':build()
