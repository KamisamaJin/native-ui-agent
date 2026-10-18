import json,pathlib,math
root=pathlib.Path.cwd();checks=[]
def record(case,rule,name,ok,actual,expected):
 checks.append(dict(platform='android',case=case,rule_id=rule,check=name,result='matched' if ok else 'mismatch',actual=actual,expected=expected,evidence=str(root/case/'semantics.json'),execution='native Compose semantics export'))
for case,fixture in [(f'repair/final-v2/android/I{n:02d}',f'feedback/initial-inputs/I{n:02d}-input.json') for n in range(1,7)]:
 f=json.loads(pathlib.Path(fixture).read_text());nodes=json.loads((root/case/'semantics.json').read_text());tags={n['tag']:n for n in nodes if n.get('tag')};items=f['items'];n=len(items)
 counts={s:sum(i['status']==s for i in items) for s in ['failed','running','queued','done']}
 F,R,Q,D=[counts[s] for s in ['failed','running','queued','done']]
 summary='No transfers' if not n else '1 needs retry' if F==1 else f'{F} need retry' if F>1 else f'{R} transferring' if R else f'{Q} waiting' if Q else 'All transfers complete'
 record(case,'TQ-STATE-03','summary',tags['transfer.summary']['text']==summary,tags['transfer.summary']['text'],summary)
 visible=items if f.get('expanded') or n<=2 else items[:2]
 got=[k[13:] for k in tags if k.startswith('transfer.row.')]
 record(case,'TQ-LIST-01','visible input order',got==[i['id'] for i in visible],got,[i['id'] for i in visible])
 record(case,'TQ-ACT-01','toggle visibility',('transfer.toggle' in tags)==(n>2),'transfer.toggle' in tags,n>2)
 if n:
  def safe(i):
   p=float(i['progress']);return min(1,max(0,p)) if math.isfinite(p) else 0
  agg=sum(1 if i['status']=='done' else 0 if i['status']=='queued' else safe(i) for i in items)/n
  pct=f'{math.floor(agg*100+.5)}%';pnode=tags['transfer.progress']
  record(case,'TQ-STATE-04','aggregate fraction',abs(pnode['progress']-agg)<=.002,pnode['progress'],agg)
  record(case,'TQ-STATE-04','aggregate displayed percentage',tags['transfer.percent']['text']==pct,tags['transfer.percent']['text'],pct)
  record(case,'TQ-STATE-04','done count',tags['transfer.count']['text']==f'{D} of {n} complete',tags['transfer.count']['text'],f'{D} of {n} complete')
  for i in visible:
   ident=i['id'];status=i['status'];expected={'done':'Complete','queued':'Waiting','failed':'Failed · retry available','running':f'{math.floor(safe(i)*100+.5)}% sent'}[status]
   record(case,'TQ-STATE-06',f'{ident} exact status',tags['transfer.status.'+ident]['text']==expected,tags['transfer.status.'+ident]['text'],expected)
   record(case,'TQ-A11Y-02',f'{ident} full name',tags['transfer.name.'+ident]['content_description']==i['name'],tags['transfer.name.'+ident]['content_description'],i['name'])
   record(case,'TQ-ACT-02',f'{ident} retry visibility',('transfer.retry.'+ident in tags)==(status=='failed'),'transfer.retry.'+ident in tags,status=='failed')
   if status=='running':
    p=tags['transfer.progress.'+ident];record(case,'TQ-STATE-02',f'{ident} safe progress',abs(p['progress']-safe(i))<=.002,p['progress'],safe(i))
 else:
  unwanted=[k for k in tags if k in ['transfer.count','transfer.percent','transfer.progress','transfer.list','transfer.more','transfer.toggle']]
  record(case,'TQ-STATE-05','empty controls and aggregate absent',not unwanted,unwanted,[])
 clickables=[node for node in nodes if node['clickable']]
 record(case,'TQ-ACT-03','only action buttons clickable',all(n['tag']=='transfer.toggle' or n['tag'].startswith('transfer.retry.') for n in clickables),[n['tag'] for n in clickables],'toggle/retry only')
 for node in clickables:
  b=node['touch_bounds_dp'];w,h=b[2]-b[0],b[3]-b[1]
  if w>0 and h>0:
   record(case,'TQ-ACT-03',node['tag']+' minimum hit target',w>=47.9 and h>=47.9,[w,h],'>=48 x 48')
  record(case,'TQ-ACT-03',node['tag']+' role',node['role']=='Button',node['role'],'Button')
for c,expected in [('I03',['toggle']),('I05',['retry:a6']),('I06',['toggle'])]:
 p=root/f'repair/final-v2/android/{c}/native-report.json';report=json.loads(p.read_text())
 checks.append(dict(platform='android',case=c,rule_id='TQ-ACT-02' if c=='I05' else 'TQ-ACT-01',check='single correct callback',result='matched' if report['activation_executed'] and report['events']==expected else 'mismatch',actual=report,expected=expected,evidence=str(p),execution=report['action_method']))
pathlib.Path('repair/final-measured-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'mismatches':[c for c in checks if c['result']=='mismatch']},ensure_ascii=False,indent=2))
