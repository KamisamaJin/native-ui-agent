from pathlib import Path
import json,math
from PIL import Image
root=Path.cwd();base=root/'repair';checks=[]
def add(platform,case,rule,description,actual,expected,ok,evidence,method):
 checks.append({'platform':platform,'case':case,'rule_id':rule,'description':description,'actual':actual,'expected':expected,'status':'passed' if ok else 'failed','execution':'observed','evidence':str(evidence),'method':method})
def safe(value):
 value=float(value)
 return min(1,max(0,value)) if math.isfinite(value) else 0
pct=lambda x:str(math.floor(x*100+0.5))+'%'
for manifest in sorted((base/'final-captures').glob('*/*/capture.json')):
 platform=manifest.parent.parent.name;case=manifest.parent.name;profile=json.loads(manifest.read_text())['profile'];args=profile['commands'][0]['argv'];fixture=json.loads((root/args[args.index('--fixture')+1]).read_text());items=fixture['items'];n=len(items);d=manifest.parent/'native';ev=d/'semantics.json';report=json.loads((d/'native-report.json').read_text())
 image=Image.open(d/'actual.png').convert('RGB');pt=(image.width//2,round(34*image.height/fixture['height']));rgb=list(image.getpixel(pt));expected=[24,34,53] if fixture['dark'] else [255,255,255]
 add(platform,case,'TQ-COLOR-01','Flat panel RGB in native appearance',rgb,expected,max(abs(a-e) for a,e in zip(rgb,expected))<=12,d/'actual.png',f'Pillow flat sample at pixel {pt}')
 if platform=='ios':
  if report['activation_requested']:
   checks.append({'platform':platform,'case':case,'rule_id':'TQ-ACT-01' if report['activation_requested']=='transfer.toggle' else 'TQ-ACT-02','description':'Requested iOS action','status':'not_executed','execution':'not_executed','reason':'Common native AX export unavailable','evidence':str(d/'native-report.json')})
  continue
 add(platform,case,'TQ-COLOR-01','Actual native Configuration night mode mask',report['native_night_mode_mask'],32 if fixture['dark'] else 16,report['native_night_mode_mask']==(32 if fixture['dark'] else 16),d/'native-report.json','Common host actual native Configuration.uiMode mask')
 nodes=json.loads(ev.read_text());tags={x['tag']:x for x in nodes if x['tag']}
 def text(tag,expected,rule):
  actual=tags.get(tag,{}).get('text');add(platform,case,rule,tag,actual,expected,actual==expected,ev,'Native Compose text semantics')
 f=sum(x['status']=='failed' for x in items);r=sum(x['status']=='running' for x in items);q=sum(x['status']=='queued' for x in items);done=sum(x['status']=='done' for x in items)
 summary='No transfers' if not n else '1 needs retry' if f==1 else str(f)+' need retry' if f else str(r)+' transferring' if r else str(q)+' waiting' if q else 'All transfers complete'
 text('transfer.summary',summary,'TQ-STATE-03');text('transfer.title','Attachment transfers','TQ-STATE-03')
 visible=items if n<=2 or fixture['expanded'] else items[:2]
 rows=[x['tag'][len('transfer.row.'):] for x in nodes if x['tag'].startswith('transfer.row.')]
 add(platform,case,'TQ-LIST-01','Visible row input order',rows,[x['id'] for x in visible],rows==[x['id'] for x in visible],ev,'Native Compose visible semantics')
 for tag,wanted in [('transfer.toggle',n>2),('transfer.more',n>2 and not fixture['expanded']),('transfer.count',n>0),('transfer.percent',n>0),('transfer.progress',n>0),('transfer.list',n>0),('transfer.empty',n==0)]:
  add(platform,case,'TQ-STATE-05' if n==0 else 'TQ-LIST-01',tag+' presence',tag in tags,wanted,(tag in tags)==wanted,ev,'Native Compose tag presence')
 if n:
  aggregate=sum(1 if i['status']=='done' else 0 if i['status']=='queued' else safe(i['progress']) for i in items)/n
  text('transfer.count',f'{done} of {n} complete','TQ-STATE-04');text('transfer.percent',pct(aggregate),'TQ-STATE-04');node=tags['transfer.progress']
  add(platform,case,'TQ-A11Y-02','Aggregate normalized progress and native range',[node['progress'],node['range_start'],node['range_end']],[aggregate,0,1],abs(node['progress']-aggregate)<=.002 and node['range_start']==0 and node['range_end']==1,ev,'Native ProgressBarRangeInfo')
  if 'transfer.more' in tags:text('transfer.more',f'+{n-2} more '+('attachment' if n==3 else 'attachments'),'TQ-LIST-01')
 else:text('transfer.empty','Add an attachment to get started.','TQ-STATE-05')
 for item in visible:
  ident=item['id'];status=item['status'];p=safe(item['progress']);label={'done':'Complete','queued':'Waiting','failed':'Failed · retry available','running':pct(p)+' sent'}[status]
  text('transfer.name.'+ident,item['name'],'TQ-A11Y-02');text('transfer.status.'+ident,label,'TQ-STATE-06')
  for prefix,wanted in [('transfer.retry.',status=='failed'),('transfer.progress.',status=='running')]:
   add(platform,case,'TQ-STATE-06',prefix+ident+' presence',prefix+ident in tags,wanted,(prefix+ident in tags)==wanted,ev,'Native Compose tag presence')
  if status=='running':
   value=tags['transfer.progress.'+ident]['progress'];add(platform,case,'TQ-STATE-02',ident+' normalized progress',value,p,abs(value-p)<=.002,ev,'Native ProgressBarRangeInfo')
  cap=3 if fixture['font_scale']>=1.6 else 2;lines=tags['transfer.name.'+ident]['lines'];add(platform,case,'TQ-LAYOUT-04',ident+' name line cap',lines,cap,lines<=cap,ev,'Native TextLayoutResult line count')
 allowed=({'transfer.toggle'} if n>2 else set())|{'transfer.retry.'+x['id'] for x in visible if x['status']=='failed'}
 clickable=[x['tag'] for x in nodes if x['clickable']]
 add(platform,case,'TQ-ACT-03','Only explicit buttons have OnClick',clickable,sorted(allowed),set(clickable)==allowed,ev,'Native Compose OnClick semantics')
 for tag in clickable:
  node=tags[tag];b=node['touch_bounds_dp'];w=b[2]-b[0];h=b[3]-b[1]
  add(platform,case,'TQ-ACT-03',tag+' native button role',node['role'],'Button',node['role']=='Button',ev,'Native Compose role semantics')
  if w>0 and h>0 and b[1]>=0 and b[3]<=fixture['height']:
   add(platform,case,'TQ-ACT-03',tag+' touch target',[w,h],[48,48],w>=47.99 and h>=47.99,ev,'Native touch bounds in initial viewport')
 if report['activation_requested']:
  expected_events=['toggle'] if report['activation_requested']=='transfer.toggle' else ['retry:'+report['activation_requested'].removeprefix('transfer.retry.')]
  add(platform,case,'TQ-ACT-01' if expected_events==['toggle'] else 'TQ-ACT-02','Actual activation callback events',report['events'],expected_events,report['activation_executed'] and report['events']==expected_events,d/'native-report.json',report['action_method'])
(base/'final-measured-checks.json').write_text(json.dumps({'checks':checks,'totals':{s:sum(x['status']==s for x in checks) for s in ['passed','failed','not_executed']}},indent=2)+'\n')
print(json.dumps({'totals':{s:sum(x['status']==s for x in checks) for s in ['passed','failed','not_executed']},'failed':[c for c in checks if c['status']=='failed']},indent=2))
