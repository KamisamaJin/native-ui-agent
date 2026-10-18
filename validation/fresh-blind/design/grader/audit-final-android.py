from pathlib import Path
import json,hashlib,copy,collections
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/fresh-blind');G=B/'design/grader';O=json.loads((B/'design/private/oracle.json').read_text())
SUBS=['submission-9e49d0','submission-3dd8b6','submission-4f1781']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
for sub in SUBS:
 for c in O['cases']:
  p=B/'evidence/final'/sub/'android'/c['caseId'];a=json.loads((p/'observation.json').read_text());cap=json.loads((p/'capture.json').read_text());issues=[];tests=collections.Counter();m=copy.deepcopy(c['fixture']['model']);byindex={}
  def check(rule,condition,detail,ix=None):
   tests[rule]+=1
   if not condition:issues.append({'ruleId':rule,'detail':detail,'snapshotIndex':ix})
  check('source_binding', all(sha(B/'implementations/final'/sub/'reply/Reply'/k)==v for k,v in cap['sources'].items()),'Source bytes')
  check('protocol',len(a['steps'])==len(cap['protocol']),'Protocol length')
  expected_events=[]
  for raw,actual in zip(cap['protocol'],a['steps']):
   check('protocol',raw['type']==actual['type'] and raw.get('identifier')==actual.get('identifier'),'Action binding')
   if raw['type']=='update':m=copy.deepcopy(raw['model'])
   for e in actual['callback_delta']:
    if e.startswith('select_slot:'):
     new=e.split(':',1)[1]
     if m.get('selectedSlotId')!=new:m['selectedSlotId']=new;m['feeAccepted']=False
    elif e.startswith('fee_accepted:'):m['feeAccepted']=e.endswith('true')
   byindex[actual['snapshot']]=copy.deepcopy(m)
  # Expected callback stream comes from the independent frozen protocol, not capture assertion results.
  for z in c['protocol']:expected_events+=z.get('expectedEvents',[])
  check('callback_trace',a['events']==expected_events,{'actual':a['events'],'expected':expected_events})
  current=copy.deepcopy(c['fixture']['model']); minhit=[]; ellipsis=[]
  for ix,z in enumerate(a['snapshots']):
   if ix in byindex:current=byindex[ix]
   nodes=z['nodes'];ids={n['identifier']:n for n in nodes if n['identifier'].startswith('visit.')};cnt=collections.Counter(n['identifier'] for n in nodes if n['identifier'].startswith('visit.'))
   def tx(n):return ' '.join([n.get('label',''),n.get('content_description','')])
   def text(i):
    if i not in ids:return ''
    parent=ids[i]['node_id'];allids={parent};out=[]
    for n in nodes:
     if n['parent_id'] in allids:allids.add(n['node_id'])
     if n['node_id'] in allids:out.append(tx(n))
    return ' '.join(out)
   check('R13',all(v==1 for v in cnt.values()),'Unique meaningful IDs',ix)
   for ident in ['visit.panel','visit.title','visit.service','visit.location','visit.current']:check('R13',ident in ids,'Required '+ident,ix)
   for ident,value in [('visit.title','Visit rescheduled' if current['mode']=='confirmed' else 'Reschedule visit'),('visit.service',current['serviceTitle']),('visit.location',current['location'])]:check('R02',value in text(ident),ident,ix)
   for value in ['Previous appointment' if current['mode']=='confirmed' else 'Current appointment',current['currentAppointment']['dayLabel'],current['currentAppointment']['timeLabel']]:check('R02',value in text('visit.current'),value,ix)
   mode=current['mode'];choosing=mode=='choosing';pairs=[(g,s) for g in current.get('groups',[]) for s in g['slots']] if choosing else [];valid=next(((g,s) for g,s in pairs if s['id']==current.get('selectedSlotId') and s['availability']!='unavailable'),None)
   check('R03',[n['identifier'] for n in nodes if n['identifier'].startswith('visit.slot.')]==['visit.slot.'+s['id'] for g,s in pairs],'Caller slot order',ix)
   check('R03',[n['identifier'] for n in nodes if n['identifier'].startswith('visit.group.')]==['visit.group.'+g['id'] for g in current.get('groups',[])] if choosing else not any(i.startswith('visit.group.') for i in ids),'Caller group order',ix)
   for g,s in pairs:
    ident='visit.slot.'+s['id'];n=ids.get(ident,{});rowlabel=tx(n)
    meta= s['unavailableReason'] if s['availability']=='unavailable' else ((s['feeLabel']+' fee') if s.get('feeLabel') else 'No fee')
    avail={'available':'Available','limited':'Few left','unavailable':'Unavailable'}[s['availability']]
    check('R03',all(v in rowlabel for v in [g['dayLabel'],s['timeLabel'],s['detail'],avail,meta]),'Full coherent '+ident,ix)
    check('R13',n.get('role')=='RadioButton' and n.get('clickable') and n.get('enabled')==(s['availability']!='unavailable'),'Native row role/enabled '+ident,ix)
    check('R04',n.get('selected')==(valid is not None and s['id']==valid[1]['id']),'Effective selection '+ident,ix)
   hasfee=valid is not None and bool(valid[1].get('feeLabel'))
   check('R07',('visit.fee_consent' in ids)==hasfee,'Conditional consent',ix)
   if hasfee:
    n=ids['visit.fee_consent'];check('R07',n.get('toggle_state')==('On' if current['feeAccepted'] else 'Off') and n.get('role')=='Checkbox' and n.get('enabled') and ('I agree to the rescheduling fee of '+valid[1]['feeLabel']+'.') in text('visit.fee_consent'),'Consent value/label/role',ix)
   check('R06',('visit.selection_summary'in ids)==bool(valid),'Conditional summary',ix)
   if valid:
    for v in ['New appointment',valid[0]['dayLabel'],valid[1]['timeLabel'],valid[1]['feeLabel'] if hasfee else 'No rescheduling fee']:
     check('R06',v in text('visit.selection_summary'),'Summary '+v,ix)
   invalid=choosing and current.get('selectedSlotId') is not None and not valid
   check('R06',('visit.selection_warning'in ids)==invalid,'Conditional warning',ix)
   if invalid:check('R06','That appointment is no longer available. Choose another time.' in text('visit.selection_warning'),'Invalid warning',ix)
   guidance=choosing and not invalid
   check('R06',('visit.guidance'in ids)==guidance,'Conditional guidance',ix)
   if guidance:
    v='Choose one appointment to continue.' if not valid else ('Agree to the fee to continue.' if hasfee and not current['feeAccepted'] else 'Your current time stays reserved until you confirm.')
    check('R06',v in text('visit.guidance'),'Guidance text',ix)
   check('R08',('visit.confirm'in ids)==choosing,'Mode confirm',ix)
   if choosing:check('R08',ids['visit.confirm']['enabled']==bool(valid and (not hasfee or current['feeAccepted'])),'Confirm gate',ix)
   for n in nodes:
    if n.get('ellipsized'):ellipsis.append({'index':ix,'label':n.get('label')})
    if n.get('clickable') and n.get('enabled') and n.get('fully_visible') and n.get('identifier','').startswith('visit.'):
     bb=n['touch_bounds_dp'];minhit.append(min(bb[2]-bb[0],bb[3]-bb[1]));check('R13',bb[2]-bb[0]>=47.5 and bb[3]-bb[1]>=47.5,'Touch dimension '+n['identifier'],ix)
   for ident,expectedMode in [('visit.loading','loading'),('visit.unavailable','unavailable'),('visit.confirmation','confirmed'),('visit.retry','unavailable'),('visit.done','confirmed'),('visit.reference','confirmed')]:check({'loading':'R10','unavailable':'R11','confirmed':'R12'}[expectedMode],(ident in ids)==(mode==expectedMode),'Mode visibility '+ident,ix)
   if mode=='loading':check('R10','Checking available appointments' in text('visit.loading'),'Loading text',ix)
   if mode=='unavailable':check('R11',all(v in text('visit.unavailable') for v in ['No appointments available',current['unavailableMessage']]) and ids['visit.retry']['enabled'],'Unavailable text/action',ix)
   if mode=='confirmed':
    conf=current['confirmation'];check('R12',all(v in text('visit.confirmation') for v in ['New appointment confirmed',conf['appointment']['dayLabel'],conf['appointment']['timeLabel'],conf['note']]) and ('Reference: '+conf['reference'])in text('visit.reference') and ids['visit.done']['enabled'],'Confirmed content/action',ix)
  env=c['fixture']['environment'];check('environment',a['configuration']['direction'].lower()==env['direction'] and abs(a['configuration']['font_scale']-env['fontScale'])<0.01 and a['configuration']['night_mode_mask']==(32 if env['theme']=='dark' else 16),'Theme/direction/font binding')
  check('R15',not ellipsis,'Native ellipsis')
  result={'submission':sub,'caseId':c['caseId'],'observationSha256':sha(p/'observation.json'),'tests':dict(tests),'issues':issues,'observedEvents':a['events'],'minFullyVisibleTouchDP':min(minhit) if minhit else None,'snapshotCount':len(a['snapshots']),'scrollMaxDP':a['snapshots'][0]['scroll_max_dp']};results.append(result)
  print(sub,c['caseId'],'issues',len(issues),'events',a['events'],'minimumHit',result['minFullyVisibleTouchDP'],'snapshots',result['snapshotCount'])
  for issue in issues:print(' ',issue)
(G/'final-android-native-audit.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
