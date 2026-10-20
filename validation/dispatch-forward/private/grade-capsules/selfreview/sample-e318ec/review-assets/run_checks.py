import json,subprocess,hashlib
from pathlib import Path
r=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/dispatch-forward'); evidence=r/'evidence/own-d0/sample-e318ec';out=r/'private/submissions/sample-e318ec/review-assets'
allrows=[]
for platform in ['ios','android']:
 for case in ['C01','C02','C03','C04']:
  d=evidence/platform/case;f=json.loads((d/'fixtures.json').read_text());o=json.loads((d/'observation.json').read_text());mapping=json.loads((r/f'private/inputs/d0-v2/{case}/mapping.json').read_text());models=[f['initial']]+f.get('updates',[]);states=[];assertions=[]
  def add(cp,kind,target,prop,expected,**extra):
   ident=f'{cp}-{target or "event"}-{prop}'
   a={'id':ident,'state':mapping[cp]['state_id'],'kind':kind,'expected':expected,**extra}
   if target:a['target']={'identifier':'waterRound.'+target}
   if prop:a['property']=prop
   assertions.append(a)
  for cp,mp in mapping.items():
   m=models[mp['input_index']];idx=mp['state_action_index'];state={'id':mp['state_id'],'input_index':mp['input_index'],'after_action':idx,'coverage':'full_content'if mp['full_content']else'target'};states.append(state)
   n=m['bedCount']*m['dripLitresPerBed'if m['selectedMethod']=='drip'else'soakLitresPerBed']+(m['dripPrimeLitres']if m['selectedMethod']=='drip'else 0);sp=m['tankLitres']-m['reserveLitres'];rn=max(0,n-sp);rem=max(0,m['tankLitres']-n);short=max(0,n-m['tankLitres']);common=m['isEnabled']and not m['isSubmitting'];consent=rn>0 and short==0;release=common and short==0 and(rn==0 or m['reserveAcknowledged']);status='Round paused'if not m['isEnabled']else'Preparing release…'if m['isSubmitting']else'Not enough water'if short>0 else'Approve reserve use'if rn>0 and not m['reserveAcknowledged']else'Ready to release'
   labels={'title':m['title'],'description':m['description'],'notice':m['notice'],'beds':f'Beds: {m["bedCount"]}','tank':f'Tank: {m["tankLitres"]} L','reserve':f'Protected reserve: {m["reserveLitres"]} L','dripPrime':f'Drip prime: {m["dripPrimeLitres"]} L','required':f'Required: {n} L','spendable':f'Outside reserve: {sp} L','reserveNeeded':f'Reserve needed: {rn} L','remaining':f'Remaining: {rem} L','shortfall':f'Shortfall: {short} L','status':status,'submit':f'Release {n} L','reserveConsent':f'Use {rn} L from the protected reserve','method.drip':f'Drip lines, {m["dripLitresPerBed"]} L per bed','method.soak':f'Soak hoses, {m["soakLitresPerBed"]} L per bed'}
   for target,label in labels.items():
    present=bool(m['notice'])if target=='notice'else short>0 if target=='shortfall'else consent if target=='reserveConsent'else True
    add(cp,'control',target,'present',present)
    if present:add(cp,'control',target,'label',label)
   add(cp,'control','progress','present',m['isEnabled']and m['isSubmitting'])
   for meth in ['drip','soak']:
    add(cp,'control','method.'+meth,'enabled',common and(meth=='drip'or m['soakAllowed']))
    add(cp,'control','method.'+meth,'selected',m['selectedMethod']==meth)
   add(cp,'control','submit','enabled',release)
   if consent:
    add(cp,'control','reserveConsent','enabled',common)
    add(cp,'control','reserveConsent','value',m['reserveAcknowledged'])
   if mp['full_content']:
    for target,spx,w in [('title',20,600),('description',14,400),('beds',14,400),('tank',14,400),('reserve',14,400),('dripPrime',14,400),('status',14,600)]:
     add(cp,'text_layout',target,'font_sp',spx)
     add(cp,'text_layout',target,'font_weight',w)
     add(cp,'text_layout',target,'ellipsized',False)
   if cp!='initial':
    actionidx=mp['trigger_action_index'];step=o['steps'][actionidx];act=step.get('action',step);expected=[];stim='caller_update'if mp['trigger_type']=='replaceModel'else'activation';tar=act.get('target',step.get('selector',{})).get('identifier','')
    if stim=='activation':
     if tar=='waterRound.submit'and release:expected=[f'releaseRequested|roundId={m["roundId"]}|method={m["selectedMethod"]}|bedCount={m["bedCount"]}|requestedLitres={n}|remainingLitres={rem}|reserveUsedLitres={rn}']
     elif tar.startswith('waterRound.method.'):
      meth=tar.split('.')[-1]
      if common and(meth=='drip'or m['soakAllowed'])and meth!=m['selectedMethod']:expected=[f'methodRequested|roundId={m["roundId"]}|method={meth}']
     elif tar=='waterRound.reserveConsent'and consent and common:expected=[f'reserveAcknowledgementRequested|roundId={m["roundId"]}|acknowledged={str(not m["reserveAcknowledged"]).lower()}']
    add(cp,'event',None,None,expected,action_index=actionidx,stimulus=stim)
  plan={'version':1,'states':states,'assertions':assertions,'requirements_source':'public brief.md and api.md; expected projection computed independently from supplied case model'}
  pp=out/f'{platform}-{case}-plan.json';pp.write_text(json.dumps(plan,indent=2));dest=out/f'{platform}-{case}-checks.json'
  proc=subprocess.run(['python3',str(r/'opaque-collector/scripts/native_checks.py'),'--plan',str(pp),'--observation',str(d/'observation.json'),'--platform',platform,'--output',str(dest)],capture_output=True,text=True)
  result=json.loads(dest.read_text());rows=result.get('assertions',result.get('results',[]));print(platform,case,'exit',proc.returncode,'keys',list(result),'summary',result.get('summary'))
  allrows.append({'platform':platform,'case':case,'report':str(dest),'returncode':proc.returncode})
(out/'checks-index.json').write_text(json.dumps(allrows,indent=2))
