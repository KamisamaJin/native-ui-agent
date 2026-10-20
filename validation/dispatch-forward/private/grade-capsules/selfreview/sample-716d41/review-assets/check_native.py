import json,importlib.util,hashlib
from pathlib import Path
base=Path('own/native')
out=Path('review-assets')
spec=importlib.util.spec_from_file_location('checks','/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/dispatch-forward/opaque-collector/scripts/native_checks.py');checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
summary=[]
for plat in ['ios','android']:
 for case in ['C01','C02','C03','C04']:
  d=base/plat/case;o=json.loads((d/'observation.json').read_text());f=json.loads((d/'fixtures.json').read_text());models=[f['initial']]+f['updates'];mapping=json.loads((Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/dispatch-forward/private/inputs/d0-v2')/case/'mapping.json').read_text())
  states=[];assertions=[]
  def add(sid,target,prop,val,kind='control',op='eq'):
   assertions.append({'id':f'{sid}:{target}:{prop}','state':sid,'kind':kind,'target':{'identifier':'waterRound.'+target},'property':prop,'expected':val,'op':op})
  def project(m):
   req=m['bedCount']*(m['dripLitresPerBed'] if m['selectedMethod']=='drip' else m['soakLitresPerBed'])+(m['dripPrimeLitres'] if m['selectedMethod']=='drip' else 0);sp=m['tankLitres']-m['reserveLitres'];rn=max(0,req-sp);remaining=max(0,m['tankLitres']-req);short=max(0,req-m['tankLitres']);enabled=m['isEnabled'] and not m['isSubmitting'];release=enabled and short==0 and (rn==0 or m['reserveAcknowledged']);status='Round paused' if not m['isEnabled'] else 'Preparing release…' if m['isSubmitting'] else 'Not enough water' if short>0 else 'Approve reserve use' if rn>0 and not m['reserveAcknowledged'] else 'Ready to release';return req,sp,rn,remaining,short,enabled,release,status
  for name,mp in mapping.items():
   sid=mp['state_id'];m=models[mp['input_index']];state={'id':sid,'input_index':mp['input_index'],'after_action':mp['after_action'],'coverage':'full_content' if mp['full_content'] else 'target'};states.append(state)
   req,sp,rn,remaining,short,enabled,release,status=project(m)
   if mp['full_content']:
    for t,v in [('title',m['title']),('description',m['description']),('beds',f"Beds: {m['bedCount']}"),('tank',f"Tank: {m['tankLitres']} L"),('reserve',f"Protected reserve: {m['reserveLitres']} L"),('dripPrime',f"Drip prime: {m['dripPrimeLitres']} L"),('required',f'Required: {req} L'),('spendable',f'Outside reserve: {sp} L'),('reserveNeeded',f'Reserve needed: {rn} L'),('remaining',f'Remaining: {remaining} L'),('status',status),('submit',f'Release {req} L')]:add(sid,t,'label',v)
    add(sid,'notice','present',bool(m['notice']))
    if m['notice']:add(sid,'notice','label',m['notice'])
    add(sid,'shortfall','present',short>0)
    if short>0:add(sid,'shortfall','label',f'Shortfall: {short} L')
    add(sid,'reserveConsent','present',rn>0 and short==0)
    if rn>0 and short==0:
     add(sid,'reserveConsent','label',f'Use {rn} L from the protected reserve');add(sid,'reserveConsent','enabled',enabled);add(sid,'reserveConsent','value',m['reserveAcknowledged'])
    add(sid,'progress','present',m['isEnabled'] and m['isSubmitting'])
    add(sid,'submit','enabled',release)
    for method,name,rate in [('drip','Drip lines',m['dripLitresPerBed']),('soak','Soak hoses',m['soakLitresPerBed'])]:
     t='method.'+method
     add(sid,t,'label',f'{name}, {rate} L per bed');add(sid,t,'selected',m['selectedMethod']==method);add(sid,t,'enabled',enabled and (method=='drip' or m['soakAllowed']));add(sid,t,'control_role','button')
    if plat=='android':
     for t in ['method.drip','method.soak','submit']+(['reserveConsent'] if rn>0 and short==0 else []):
      add(sid,t,'touch_width',44,op='gte');add(sid,t,'touch_height',44,op='gte')
     for t,size in [('title',20),('description',14),('beds',14),('tank',14),('reserve',14),('dripPrime',14),('notice',14),('status',14)]:
      if t=='notice' and not m['notice']:continue
      add(sid,t,'font_sp',size,kind='text_layout')
   if mp['trigger_action_index'] is not None:
    ai=mp['trigger_action_index'];step=o['steps'][ai];stimulus='caller_update' if mp['trigger_type']=='replaceModel' else 'activation';expected=[]
    if stimulus=='activation':
     target=step.get('action',{}).get('target',step.get('selector',{})).get('identifier','')
     if target=='waterRound.submit':
      add(sid,'submit','label',f'Release {req} L');add(sid,'submit','enabled',release)
     if target=='waterRound.reserveConsent' and rn>0 and short==0:
      add(sid,'reserveConsent','value',m['reserveAcknowledged'])
     if target.startswith('waterRound.method.'):
      add(sid,'method.'+target.split('.')[-1],'selected',m['selectedMethod']==target.split('.')[-1])
     if target=='waterRound.submit' and release:expected=[f"releaseRequested|roundId={m['roundId']}|method={m['selectedMethod']}|bedCount={m['bedCount']}|requestedLitres={req}|remainingLitres={remaining}|reserveUsedLitres={rn}"]
     elif target=='waterRound.reserveConsent' and rn>0 and short==0 and enabled:expected=[f"reserveAcknowledgementRequested|roundId={m['roundId']}|acknowledged={str(not m['reserveAcknowledged']).lower()}"]
     elif target.startswith('waterRound.method.'):
      method=target.split('.')[-1]
      if enabled and (method=='drip' or m['soakAllowed']) and method!=m['selectedMethod']:expected=[f"methodRequested|roundId={m['roundId']}|method={method}"]
    assertions.append({'id':sid+':callback','state':sid,'kind':'event','action_index':ai,'expected':expected,'stimulus':stimulus})
  plan={'version':1,'states':states,'assertions':assertions}
  (out/f'{plat}-{case}-plan.json').write_text(json.dumps(plan,indent=2))
  result=checks.evaluate(plan,o,plat,observation_sha256=hashlib.sha256((d/'observation.json').read_bytes()).hexdigest())
  (out/f'{plat}-{case}-checks.json').write_text(json.dumps(result,indent=2))
  summary.append({'platform':plat,'case':case,'counts':result['counts'],'failed':[(a['id'],a['reason']) for a in result['assertions'] if a['status']=='failed'],'unassessed':[(a['id'],a['reason']) for a in result['assertions'] if a['status']=='unassessed']})
print(json.dumps(summary,indent=2))
(out/'typed-checks-summary.json').write_text(json.dumps(summary,indent=2))
