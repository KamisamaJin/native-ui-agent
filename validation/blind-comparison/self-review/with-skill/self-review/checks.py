from pathlib import Path
import json,math,hashlib
from PIL import Image,ImageChops
root=Path.cwd();base=root/'self-review';results=[];texts=[]
def add(platform,case,rule,check,actual,expected,passed,evidence,method='Native Compose semantics exported by the unchanged common host'):
 results.append({'platform':platform,'case':case,'rule_id':rule,'check':check,'actual':actual,'expected':expected,'status':'passed' if passed else 'failed','execution':'observed','method':method,'evidence':str(evidence)})
def safe(v):
 try:v=float(v)
 except:v=float('nan')
 return max(0,min(1,v)) if math.isfinite(v) else 0
pct=lambda v:str(math.floor(v*100+0.5))+'%'
for platform in ['android','ios']:
 for capture in sorted((base/'captures'/platform).glob('*/capture.json')):
  case=capture.parent.name;d=capture.parent/'native';fixture=json.loads((base/'fixtures'/f'{case}.json').read_text());items=fixture['items'];n=len(items)
  image=Image.open(d/'actual.png').convert('RGB');point=(image.width//2,round(34*image.height/fixture['height']))
  actual=list(image.getpixel(point));expected=[24,34,53] if fixture.get('dark') else [255,255,255]
  add(platform,case,'TQ-COLOR-01','Panel flat interior RGB',actual,expected,max(abs(a-e) for a,e in zip(actual,expected))<=12,d/'actual.png',f'Pillow RGB pixel at native pixel {point}; logical y=34, center x')
  report=json.loads((d/'native-report.json').read_text());wanted=fixture.get('activate_id')
  if wanted:
   expected_events=['toggle'] if wanted=='transfer.toggle' else ['retry:archive'] if wanted=='transfer.retry.archive' else []
   if platform=='android':
    add(platform,case,'TQ-ACT-01' if wanted=='transfer.toggle' else 'TQ-ACT-02' if wanted.startswith('transfer.retry') else 'TQ-ACT-03','Actual activation callback events',report['events'],expected_events,report['events']==expected_events,d/'native-report.json',report['action_method'])
   else:
    results.append({'platform':platform,'case':case,'rule_id':'TQ-ACT-01' if wanted=='transfer.toggle' else 'TQ-ACT-02' if wanted.startswith('transfer.retry') else 'TQ-ACT-03','check':'Requested native activation','status':'not_executed','execution':'not_executed','actual':report,'evidence':str(d/'native-report.json'),'reason':'iOS AX export unavailable in common infrastructure; no activation was executed.'})
  if platform!='android':continue
  nodes=json.loads((d/'semantics.json').read_text());tags={x['tag']:x for x in nodes if x['tag']};ev=d/'semantics.json'
  def text(tag,expected,rule):
   actual=tags.get(tag,{}).get('text');add(platform,case,rule,tag,actual,expected,actual==expected,ev)
  f=sum(x['status']=='failed' for x in items);r=sum(x['status']=='running' for x in items);q=sum(x['status']=='queued' for x in items);done=sum(x['status']=='done' for x in items)
  summary='No transfers' if not n else '1 needs retry' if f==1 else f'{f} need retry' if f>1 else f'{r} transferring' if r else f'{q} waiting' if q else 'All transfers complete'
  tone='secondary' if not n else 'error' if f else 'accent' if r else 'secondary' if q else 'success'
  text('transfer.title','Attachment transfers','TQ-STATE-03');text('transfer.summary',summary,'TQ-STATE-03')
  visible=items if n<=2 or fixture['expanded'] else items[:2]
  actualrows=[x['tag'][len('transfer.row.'):] for x in nodes if x['tag'].startswith('transfer.row.')]
  add(platform,case,'TQ-LIST-01','Visible row order',actualrows,[x['id'] for x in visible],actualrows==[x['id'] for x in visible],ev)
  wanted_toggle=n>2
  add(platform,case,'TQ-ACT-01','Toggle presence','transfer.toggle' in tags,wanted_toggle,('transfer.toggle' in tags)==wanted_toggle,ev)
  if not n:
   text('transfer.empty','Add an attachment to get started.','TQ-STATE-05')
   forbidden=[k for k in tags if k in ['transfer.count','transfer.percent','transfer.progress','transfer.list','transfer.more','transfer.toggle'] or k.startswith('transfer.row.')]
   add(platform,case,'TQ-STATE-05','Empty-state forbidden elements',forbidden,[],not forbidden,ev)
  else:
   aggregate=sum(1 if x['status']=='done' else 0 if x['status']=='queued' else safe(x['progress']) for x in items)/n
   text('transfer.count',f'{done} of {n} complete','TQ-STATE-04');text('transfer.percent',pct(aggregate),'TQ-STATE-04')
   node=tags['transfer.progress'];actual=node['progress']
   add(platform,case,'TQ-A11Y-02','Overall normalized progress',actual,aggregate,abs(actual-aggregate)<=.002 and node['range_start']==0 and node['range_end']==1,ev)
   add(platform,case,'TQ-A11Y-02','Overall label/state',[node['content_description'],node['state_description']],['Overall transfer progress',pct(aggregate)],node['content_description']=='Overall transfer progress' and node['state_description']==pct(aggregate),ev)
   more=n>2 and not fixture['expanded'];add(platform,case,'TQ-LIST-01','Overflow presence','transfer.more' in tags,more,('transfer.more' in tags)==more,ev)
   if more:text('transfer.more',f'+{n-2} more '+('attachment' if n==3 else 'attachments'),'TQ-LIST-01')
  for item in visible:
   ident=item['id'];status=item['status'];p=safe(item['progress']);label={'done':'Complete','queued':'Waiting','failed':'Failed · retry available','running':pct(p)+' sent'}[status]
   text('transfer.name.'+ident,item['name'],'TQ-A11Y-02');text('transfer.status.'+ident,label,'TQ-STATE-06')
   for prefix,wanted in [('transfer.retry.',status=='failed'),('transfer.progress.',status=='running')]:
    add(platform,case,'TQ-STATE-06',prefix+ident+' presence',prefix+ident in tags,wanted,(prefix+ident in tags)==wanted,ev)
   if status=='running':
    node=tags['transfer.progress.'+ident];add(platform,case,'TQ-STATE-02',ident+' normalized bar progress',node['progress'],p,abs(node['progress']-p)<=.002,ev)
   node=tags['transfer.name.'+ident];maxlines=3 if fixture.get('font_scale',1)>=1.6 else 2
   add(platform,case,'TQ-LAYOUT-04',ident+' name line cap',node['lines'],maxlines,node['lines']<=maxlines,ev)
  allowed={('transfer.toggle' if n>2 else '')}|{'transfer.retry.'+x['id'] for x in visible if x['status']=='failed'}
  actualclicks=[x['tag'] for x in nodes if x['clickable']]
  add(platform,case,'TQ-ACT-03','Only explicit buttons clickable',actualclicks,sorted(allowed-{''}),set(actualclicks)==allowed-{''},ev)
  for tag in actualclicks:
   node=tags[tag];b=node['touch_bounds_dp'];w=b[2]-b[0];h=b[3]-b[1]
   if w>0 and h>0:
    add(platform,case,'TQ-ACT-03',tag+' minimum touch dimensions',[w,h],[48,48],w>=47.99 and h>=47.99,ev)
   add(platform,case,'TQ-ACT-03',tag+' role',node['role'],'Button',node['role']=='Button',ev)
  for node in nodes:
   if node.get('tag') and 'font_sp' in node:texts.append({'platform':platform,'case':case,**node})
# Empty captures are expected to be identical for both expansion inputs.
for platform in ['android','ios']:
 a=base/'captures'/platform/'empty/native/actual.png';b=base/'captures'/platform/'empty-collapsed/native/actual.png'
 equal=ImageChops.difference(Image.open(a).convert('RGB'),Image.open(b).convert('RGB')).getbbox() is None
 add(platform,'empty versus empty-collapsed','TQ-STATE-05','Empty-state pixel equality',equal,True,equal,[str(a),str(b)],'Exact image pixel comparison of two fresh native captures with otherwise identical fixtures')
(base/'measured-checks.json').write_text(json.dumps({'checks':results,'totals':{s:sum(x['status']==s for x in results) for s in ['passed','failed','not_executed']}},indent=2)+'\n')
(base/'text-measurements.json').write_text(json.dumps(texts,indent=2)+'\n')
print(json.dumps({'totals':{s:sum(x['status']==s for x in results) for s in ['passed','failed','not_executed']},'failed':[x for x in results if x['status']=='failed']},indent=2))
