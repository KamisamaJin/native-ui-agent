#!/usr/bin/env python3
"""Independent business design authoring; no production UI, SDK or rendering calls.

Private authoring input: never include this file in a worker's public read set.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, re, subprocess, sys, textwrap

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[2]
TOOLS = REPO / 'validation/pooled-forward/candidate-v13.9/scripts'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TOOLS))
import design_contract as dc
import evidence_responsibility as er
import execution_plan as ep
import review_contract as rc
import requirement_routes as rr
import action_guard as ag

def canonical(v): return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def digest(v): return hashlib.sha256(canonical(v)).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def write(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists(): raise ValueError('Preserve prior artifact: '+str(p))
    p.write_text(v if isinstance(v,str) else json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def typed(v,u=None):
    if u is None: u='bool' if type(v)is bool else 'count' if type(v)is int else 'events' if isinstance(v,list) else 'string'
    return {'value':v,'unit':u}
def expr(pointer): return {'source':'reference','pointer':pointer}

TASKS = [
 dict(id='catering-package',name='Catering package configuration',api='CateringPackagePlanner',model='CateringPackageInput',
      rootNoun='package',detailNoun='service',quantityField='guestCount',quantityUnit='guests',rootCaption='Package',detailCaption='Service',
      roots=[('buffet','Buffet package'),('boxed','Boxed package')],
      details=[('reusable','Reusable service'),('compostable','Compostable service')],alt='compostable',fallback='compostable',
      ack='I confirm the dietary counts',ackShort='the dietary counts',submit='Record catering order',receipt='Catering order recorded.',event='catering',
      fields=[('guestCount','Int'),('vegetarianGuests','Int'),('vegetarianMeals','Int'),('buffetCapacity','Int'),('boxedCapacity','Int'),('reusableSets','Int'),('compostableSets','Int')],
      base=dict(guestCount=12,vegetarianGuests=3,vegetarianMeals=8,buffetCapacity=30,boxedCapacity=30,reusableSets=24,compostableSets=30),
      edge=dict(guestCount=6,vegetarianGuests=2,vegetarianMeals=2,buffetCapacity=6,boxedCapacity=5,reusableSets=6,compostableSets=6),
      detailLoss=dict(reusableSets=5),rootLoss=dict(buffetCapacity=5,boxedCapacity=6),none=dict(buffetCapacity=5,boxedCapacity=5),
      rules=["Buffet is eligible when guestCount is at least 6 and at most buffetCapacity.","Boxed is eligible when guestCount is at most boxedCapacity and vegetarianMeals is at least vegetarianGuests.","Reusable service is eligible only for Buffet and when reusableSets is at least guestCount.","Compostable service is eligible for either selected eligible package when compostableSets is at least guestCount."],
      context='Prepare a reusable order summary for the facilities desk. Capacity and dietary facts come from the caller; this component records the requested package and service.',
      notes=['Quantities describe this event only. A reusable place setting counts as one complete set.','Selecting another package clears the service and confirmation.']),
 dict(id='training-pathway',name='Training pathway enrollment',api='TrainingPathwayEnrollment',model='TrainingPathwayInput',
      rootNoun='pathway',detailNoun='participation mode',quantityField='completedHours',quantityUnit='completed hours',rootCaption='Pathway',detailCaption='Mode',
      roots=[('guided','Guided cohort'),('independent','Independent lab')],
      details=[('certificate','Certificate assessment'),('practice','Practice only')],alt='practice',fallback='practice',
      ack='I confirm the learning commitment',ackShort='the learning commitment',submit='Record training enrollment',receipt='Training enrollment recorded.',event='training',
      fields=[('completedHours','Int'),('completedModules','List<String>'),('cohortSeats','Int'),('deviceCredits','Int'),('assessmentSlots','Int'),('practiceSeats','Int')],
      base=dict(completedHours=16,completedModules=['foundation','safety'],cohortSeats=3,deviceCredits=4,assessmentSlots=2,practiceSeats=5),
      edge=dict(completedHours=12,completedModules=['foundation'],cohortSeats=1,deviceCredits=1,assessmentSlots=1,practiceSeats=1),
      detailLoss=dict(assessmentSlots=0),rootLoss=dict(cohortSeats=0,deviceCredits=2),none=dict(cohortSeats=0,deviceCredits=1),
      rules=["Both pathways require completedModules to contain the exact case-sensitive value foundation.","Guided cohort also requires completedHours at least 8 and cohortSeats at least 1.","Independent lab also requires completedHours at least 4 and deviceCredits at least 2.","Certificate assessment requires Guided cohort, completedHours at least 12, and assessmentSlots at least 1.","Practice only is eligible for either selected eligible pathway when practiceSeats is at least 1."],
      context='Enroll a staff member in the next learning activity using already completed modules and published capacity. This panel does not book a date or load a course service.',
      notes=['Foundation completion is a case-sensitive module identifier, not a display label.','Changing a pathway clears the participation mode and commitment.']),
 dict(id='subscription-capacity',name='Subscription capacity change',api='SubscriptionCapacityChange',model='SubscriptionCapacityInput',
      rootNoun='plan',detailNoun='billing term',quantityField='seatCount',quantityUnit='seats',rootCaption='Plan',detailCaption='Term',
      roots=[('scale','Scale plan'),('team','Team plan')],details=[('annual','Annual billing'),('monthly','Monthly billing')],alt='monthly',fallback='monthly',
      ack='I confirm the capacity commitment',ackShort='the capacity commitment',submit='Record capacity change',receipt='Capacity change recorded.',event='capacity',
      fields=[('seatCount','Int'),('teamQuota','Int'),('scaleQuota','Int'),('prepaidMonths','Int'),('accountBalanceCents','Int')],
      base=dict(seatCount=18,teamQuota=25,scaleQuota=50,prepaidMonths=18,accountBalanceCents=0),
      edge=dict(seatCount=10,teamQuota=9,scaleQuota=10,prepaidMonths=12,accountBalanceCents=0),
      detailLoss=dict(prepaidMonths=11),rootLoss=dict(scaleQuota=9,teamQuota=10),none=dict(scaleQuota=9,teamQuota=9),
      rules=["Scale plan is eligible when seatCount is at least 10 and at most scaleQuota.","Team plan is eligible when seatCount is between 2 and 25 inclusive and at most teamQuota.","Annual billing is eligible only for Scale plan and when prepaidMonths is at least 12.","Monthly billing is eligible for either selected eligible plan when accountBalanceCents is nonnegative. A negative balance blocks Monthly, independently of plan capacity."],
      context='Prepare a workspace capacity change from current seat demand, allocation limits, and prepaid credit. The component records a request and does not charge a payment method.',
      notes=['Quota limits are inclusive. Ten seats is the first eligible Scale quantity.','Selecting another plan clears the billing term and capacity confirmation.']),
 dict(id='visitor-preclearance',name='Visitor access preclearance',api='VisitorAccessPreclearance',model='VisitorAccessInput',
      rootNoun='access area',detailNoun='credential route',quantityField='guestCount',quantityUnit='visitors',rootCaption='Area',detailCaption='Credential',
      roots=[('research','Research floor'),('office','Office floor')],details=[('research-badge','Research badge'),('visitor-escort','Visitor escort')],alt='visitor-escort',fallback='visitor-escort',
      ack='I confirm the visitor briefing',ackShort='the visitor briefing',submit='Record visitor clearance',receipt='Visitor clearance recorded.',event='visitor',
      fields=[('guestCount','Int'),('sponsorActive','Bool'),('badgeTrainingComplete','Bool'),('researchCapacity','Int'),('officeCapacity','Int'),('verifiedIDs','Int'),('labInductions','Int'),('escortCount','Int')],
      base=dict(guestCount=3,sponsorActive=True,badgeTrainingComplete=True,researchCapacity=8,officeCapacity=10,verifiedIDs=4,labInductions=4,escortCount=4),
      edge=dict(guestCount=2,sponsorActive=True,badgeTrainingComplete=True,researchCapacity=2,officeCapacity=1,verifiedIDs=2,labInductions=2,escortCount=2),
      detailLoss=dict(verifiedIDs=1),rootLoss=dict(researchCapacity=1,officeCapacity=2),none=dict(researchCapacity=1,officeCapacity=1),
      rules=["Both access areas require sponsorActive and positive guestCount.","Research floor also requires badgeTrainingComplete and guestCount at most researchCapacity.","Office floor also requires guestCount at most officeCapacity.","Research badge is eligible only for Research floor and when both verifiedIDs and labInductions are at least guestCount.","Visitor escort is eligible for either selected eligible area when escortCount is at least guestCount."],
      context='Prepare one deterministic visitor access request using sponsor, identity, induction, and escort facts already supplied by reception. This panel does not issue a badge.',
      notes=['Each visitor requires a verified identity and an induction for a research badge.','Changing an access area clears the credential route and briefing confirmation.']),
 dict(id='candidate-disposition',name='Recruiting candidate disposition',api='CandidateDispositionReview',model='CandidateDispositionInput',
      rootNoun='disposition',detailNoun='next step or reason',quantityField='portfolioScore',quantityUnit='portfolio points',rootCaption='Disposition',detailCaption='Detail',
      roots=[('continue','Continue review'),('archive','Archive application')],details=[('technical','Technical interview'),('recruiter','Recruiter screen'),('skills-gap','Skills gap'),('role-closed','Role closed')],alt='skills-gap',fallback='recruiter',
      ack='I confirm the evidence review',ackShort='the evidence review',submit='Record candidate disposition',receipt='Candidate disposition recorded.',event='candidate',
      fields=[('portfolioScore','Int'),('reviewerCapacity','Int'),('technicalSlots','Int'),('recruiterSlots','Int'),('legalHold','Bool'),('assessmentCount','Int'),('openRoleCount','Int')],
      base=dict(portfolioScore=82,reviewerCapacity=2,technicalSlots=2,recruiterSlots=2,legalHold=False,assessmentCount=2,openRoleCount=0),
      edge=dict(portfolioScore=75,reviewerCapacity=1,technicalSlots=1,recruiterSlots=1,legalHold=True,assessmentCount=1,openRoleCount=0),
      detailLoss=dict(technicalSlots=0),rootLoss=dict(reviewerCapacity=0,legalHold=False),none=dict(reviewerCapacity=0,legalHold=True),
      rules=["Continue review is eligible when portfolioScore is at least 60 and reviewerCapacity is at least 1.","Archive application is eligible only when legalHold is false.","Technical interview is eligible only for Continue review, portfolioScore at least 75, and technicalSlots at least 1.","Recruiter screen is eligible only for Continue review and recruiterSlots at least 1.","Skills gap is eligible only for Archive application and assessmentCount at least 1.","Role closed is eligible only for Archive application and openRoleCount exactly 0. Both archive reasons may be eligible at once; the user chooses one."],
      context='Record the recruiting team’s next step from completed assessment evidence and current reviewer capacity. Archiving requires a reason and is unavailable during a legal hold.',
      notes=['An eligible archive reason does not override a legal hold.','Changing disposition clears the next step or reason and evidence confirmation.']),
]

COMMON_FIELDS=[('entityID','String'),('revision','Int'),('title','String'),('context','String'),('notes','List<String>')]

def eligible(t,f,root=None):
    k=t['id']
    if k=='catering-package':
        roots={'buffet':6<=f['guestCount']<=f['buffetCapacity'],'boxed':f['guestCount']<=f['boxedCapacity'] and f['vegetarianMeals']>=f['vegetarianGuests']}
        details={'reusable':root=='buffet' and f['reusableSets']>=f['guestCount'],'compostable':root is not None and f['compostableSets']>=f['guestCount']}
    elif k=='training-pathway':
        foundation='foundation' in f['completedModules']
        roots={'guided':foundation and f['completedHours']>=8 and f['cohortSeats']>=1,'independent':foundation and f['completedHours']>=4 and f['deviceCredits']>=2}
        details={'certificate':root=='guided' and f['completedHours']>=12 and f['assessmentSlots']>=1,'practice':root is not None and f['practiceSeats']>=1}
    elif k=='subscription-capacity':
        roots={'scale':10<=f['seatCount']<=f['scaleQuota'],'team':2<=f['seatCount']<=25 and f['seatCount']<=f['teamQuota']}
        details={'annual':root=='scale' and f['prepaidMonths']>=12,'monthly':root is not None and f['accountBalanceCents']>=0}
    elif k=='visitor-preclearance':
        valid=f['sponsorActive'] and f['guestCount']>0
        roots={'research':valid and f['badgeTrainingComplete'] and f['guestCount']<=f['researchCapacity'],'office':valid and f['guestCount']<=f['officeCapacity']}
        details={'research-badge':root=='research' and min(f['verifiedIDs'],f['labInductions'])>=f['guestCount'],'visitor-escort':root is not None and f['escortCount']>=f['guestCount']}
    else:
        roots={'continue':f['portfolioScore']>=60 and f['reviewerCapacity']>=1,'archive':not f['legalHold']}
        details={'technical':root=='continue' and f['portfolioScore']>=75 and f['technicalSlots']>=1,'recruiter':root=='continue' and f['recruiterSlots']>=1,'skills-gap':root=='archive' and f['assessmentCount']>=1,'role-closed':root=='archive' and f['openRoleCount']==0}
    return roots,details

def fixture(t,kind):
    return dict(entityID=t['id']+'-'+('public' if kind=='public' else 'edge'),revision=4 if kind=='public' else 11,
                title=t['name'],context=t['context'],notes=t['notes'],**t['base' if kind=='public' else 'edge'])

def long_content(f,t):
    f=copy.deepcopy(f)
    f['title']='Extended review: '+t['name']+' for the cross-functional welcome and operations programme'
    f['context']=(t['context']+' Please read this caller-supplied narrative in full before recording the request. The facilities, people, and operations teams share this reusable panel, so the narrative may include several complete sentences and meaningful spaces. Every sentence must remain visible when the host scrolls; the panel must grow naturally instead of clipping, shrinking the type, or introducing an internal scroll region.')
    f['notes']=[*t['notes'],'Caller note: keep the accessibility labels on the actual controls. Long descriptive text belongs in the component content and wraps across as many lines as necessary. This explanatory note is business context for the operator.']
    return f

def families(t,kind):
    base=fixture(t,kind); a=t['roots'][0][0]; b=t['roots'][1][0]; x=t['details'][0][0]
    actions=[];states=[];fixtures=[base];snapshots={};f=base;local=dict(root=None,detail=None,ack=False,recorded=False)
    def transition(act):
        nonlocal f,local
        events=[]
        if act['type']=='tap':
            target=act['target'];roots,details=eligible(t,f,local['root'])
            if target.startswith('root:'):
                val=target[5:];assert roots[val] and not local['recorded']
                if val!=local['root']:local.update(root=val,detail=None,ack=False)
            elif target.startswith('detail:'):
                val=target[7:];assert details[val] and local['root'] and not local['recorded']
                if val!=local['detail']:local.update(detail=val,ack=False)
            elif target=='ack':
                assert local['root'] and local['detail'] and not local['recorded'];local['ack']=not local['ack']
            elif target=='submit':
                assert local['root'] and local['detail'] and local['ack'] and not local['recorded']
                events=[event(t,f,local)];local['recorded']=True
        elif act['type']=='apply_next_fixture':
            old=f; f=fixtures[len([v for v in actions if v['type']=='apply_next_fixture'])+1]
            if (old['entityID'],old['revision'])!=(f['entityID'],f['revision']):local=dict(root=None,detail=None,ack=False,recorded=False)
            else:
                roots,details=eligible(t,f,local['root'])
                if local['root'] is not None and not roots[local['root']]:local=dict(root=None,detail=None,ack=False,recorded=False)
                elif local['detail'] is not None and not details[local['detail']]:local.update(detail=None,ack=False,recorded=False)
        return events
    def add(kind,target=None,state=None,full=False,stim=None):
        act={'type':kind}
        if target:
            act.update(target=target,reveal=True,max_steps=18,preconditions=[{'target':target,'property':'enabled','op':'eq','expected':True}])
        if kind=='sweep':act['max_scrolls']=18
        if state:act['state_id']=state
        if target=='submit':
            act['expect_callback']=event(t,f,local)
            ack_index=max(i for i,v in enumerate(actions) if v.get('target')=='ack')
            act['callback_dependencies']=[{'action_index':ack_index,'expected_events':[]}]
            act['preconditions'] += [{'target':'ack','property':'selected','op':'eq','expected':True}]
        events=transition(act);actions.append(act)
        if state:
            st=dict(id=state,input_index=len([v for v in actions if v['type']=='apply_next_fixture']),after_action=len(actions)-1,coverage='full_content' if full else 'targets')
            if stim is not None:st['stimulus_action']=stim
            states.append(st); snapshots[state]=dict(fixture=copy.deepcopy(f),local=copy.deepcopy(local),events=events if stim is None else None)
        return len(actions)-1
    def update(v,name):
        fixtures.append(copy.deepcopy(v));i=add('apply_next_fixture');add('sweep',state=name,full=True,stim=i)
        snapshots[name]['events']=[]
    add('sweep',state='blank',full=True)
    add('tap','root:'+a,'root-chosen')
    add('tap','detail:'+x,'detail-chosen')
    i=add('tap','ack');add('sweep',state='ready',full=True,stim=i);snapshots['ready']['events']=[]
    if kind=='public':
        i=add('tap','submit');add('sweep',state='recorded',full=True,stim=i);snapshots['recorded']['events']=[event(t,f,local)]
        update(long_content(f,t),'long-retained')
        new=fixture(t,kind);new.update(entityID=t['id']+'-next',revision=4);update(new,'entity-replaced')
        add('tap','root:'+b,'alternate-root')
        add('tap','detail:'+t['alt'],'alternate-detail')
        add('tap','root:'+a,'dependent-reset')
        add('tap','detail:'+x);add('tap','ack')
        new=copy.deepcopy(f);new['revision']+=1;update(new,'revision-replaced')
    else:
        add('tap','root:'+a,'repeat-root')
        new=copy.deepcopy(f);new.update(t['detailLoss']);update(new,'detail-invalidated')
        add('tap','detail:'+t['fallback'],'alternative-detail')
        add('tap','ack')
        i=add('tap','submit');add('sweep',state='recorded',full=True,stim=i);snapshots['recorded']['events']=[event(t,f,local)]
        update(long_content(f,t),'long-retained')
        new=copy.deepcopy(f);new.update(t['rootLoss']);update(new,'root-invalidated')
        add('tap','root:'+b,'new-path')
        new=fixture(t,kind);new.update(entityID=t['id']+'-unavailable',revision=12);new.update(t['none']);update(new,'unavailable')
        new=fixture(t,kind);new.update(entityID=f['entityID'],revision=f['revision']+1);update(new,'revision-replaced')
    assert 8<=len(states)<=13 and len(actions)<=25
    return dict(states=states,actions=actions,fixtures=fixtures,snapshots=snapshots)

def event(t,f,s):return '|'.join(map(str,[t['event'],f['entityID'],f['revision'],s['root'],s['detail'],f[t['quantityField']]]))

def expected(t,f,s):
    roots,details=eligible(t,f,s['root']);rl=dict(t['roots']);dl=dict(t['details'])
    if s['recorded']:status='Recorded. Selections are locked for this request.'
    elif not any(roots.values()):status='No '+t['rootNoun']+' is eligible for these request details.'
    elif not s['root']:status='Choose a '+t['rootNoun']+'.'
    elif not s['detail']:status='Choose a '+t['detailNoun']+' for '+rl[s['root']]+'.'
    elif not s['ack']:status='Confirm '+t['ackShort']+' to continue.'
    else:status='Ready to '+t['submit'][0].lower()+t['submit'][1:]+'.'
    summary=f"{t['rootCaption']}: {rl.get(s['root'],'Not chosen')}. {t['detailCaption']}: {dl.get(s['detail'],'Not chosen')}. {f[t['quantityField']]} {t['quantityUnit']}."
    vals={'title-label':f['title'],'context-label':f['context'],'notes-label':'\n\n'.join(f['notes']),'status-label':status,'summary-label':summary,
          'receipt-label':t['receipt'] if s['recorded'] else 'No request recorded.',
          'submit-enabled':bool(s['root'] and s['detail'] and s['ack'] and not s['recorded']),
          'ack-enabled':bool(s['root'] and s['detail'] and not s['recorded']),'ack-selected':s['ack']}
    for key,label in t['roots']:
        vals['root-'+key+'-enabled']=roots[key] and not s['recorded'];vals['root-'+key+'-selected']=s['root']==key
    for key,label in t['details']:
        vals['detail-'+key+'-enabled']=bool(s['root'] and details[key] and not s['recorded']);vals['detail-'+key+'-selected']=s['detail']==key
    return vals

if __name__=='__main__':
    raise SystemExit('Load through materialize.py; this file is sealed private authoring input.')
