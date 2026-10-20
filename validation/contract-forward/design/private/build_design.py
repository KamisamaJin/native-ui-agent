from pathlib import Path
import json,hashlib,sys,subprocess,datetime
D=Path(__file__).resolve().parents[1]; P=D/'public'; V=D/'private'; T=D.parent/'candidate-v6';
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n' if not isinstance(v,str) else v)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def typed(v,u):return {'value':v,'unit':u}
def course(id,title,detail,price,cap,onsite=True,workbook=True):return dict(id=id,title=title,detail=detail,seatPriceCents=price,capacity=cap,onsiteAvailable=onsite,workbookAvailable=workbook)
def model(title,detail,courses,disc=1000,fee=2500,work=1200):return dict(title=title,detail=detail,courses=courses,remoteDiscountCents=disc,onsiteFeeCents=fee,workbookCents=work)
A=course('foundations','Service foundations','A practical workshop for new customer support colleagues.',10000,6)
B=course('advanced','Advanced service recovery','Practice resolving complex customer conversations as a team.',15000,6)
p1=model('Workshop enrollment','Reserve a team place in the next learning cohort.',[A,B])
p1u=model('Updated workshop enrollment','The organizer has changed capacity and attendance options.',[dict(A,capacity=3),dict(B,capacity=1,onsiteAvailable=False,workbookAvailable=False,seatPriceCents=18000)])
p2=model('Professional learning for distributed service teams','Choose a course for colleagues working across several regions. The organizer provides detailed preparation notes, accessibility arrangements, and a practical follow-up exercise so that every participant can prepare comfortably before the workshop.',[dict(A,title='Foundations of thoughtful customer service across languages and regions',detail='A detailed introduction with realistic examples, guided practice, and generous time for colleagues to discuss difficult situations.',onsiteAvailable=False),dict(B,title='Advanced recovery and escalation conversations for experienced customer service colleagues',capacity=3,onsiteAvailable=False,workbookAvailable=False)])
p2u=model('Updated distributed learning catalog','Enrollment has closed for the advanced course. Foundations remains available for a small group.',[dict(A,capacity=1,onsiteAvailable=False),dict(B,capacity=0,onsiteAvailable=False,workbookAvailable=False)])
h1=model('Regional team learning','Choose a course and reserve places for the regional team.',[dict(A,capacity=0),dict(B,capacity=6)])
h1u=model('Regional catalog revised','Advanced is no longer offered. Your draft should follow the available course.',[dict(A,capacity=3,onsiteAvailable=False,workbookAvailable=False)])
h1z=model('Regional catalog closed','The organizer has closed this learning cohort.',[dict(A,capacity=0,onsiteAvailable=False,workbookAvailable=False)])
bind={k:{'identifier':'enroll.'+v} for k,v in dict(title='title',detail='detail',courseA='course.foundations',courseB='course.advanced',remote='mode.remote',onsite='mode.onsite',seats3='seats.3',seats6='seats.6',workbook='workbook',total='total',reserve='reserve',status='status',edit='edit').items()}
def tap(t,state=None):return dict(type='tap',target=t,reveal=True,**({'state_id':state} if state else {}))
def update(s):return dict(type='apply_next_fixture',state_id=s)
cases={
'P1':dict(models=[p1,p1u],width=390,theme='light',direction='ltr',dynamic_type='large',fontScale=1.0,actions=[dict(type='sweep',state_id='browse'),tap('courseB'),tap('onsite'),tap('seats3'),tap('workbook','configured'),tap('reserve','reserved'),update('replaced'),tap('reserve','reserved-again')],states=[('browse',0,0),('configured',0,4),('reserved',0,5),('replaced',1,6),('reserved-again',1,7)]),
'P2':dict(models=[p2,p2u],width=300,theme='dark',direction='rtl',dynamic_type='xxxLarge',fontScale=1.3,actions=[dict(type='sweep',state_id='browse'),tap('onsite','blocked'),tap('seats6'),tap('courseB','course-changed'),tap('reserve','reserved'),tap('edit','editing'),update('replaced')],states=[('browse',0,0),('blocked',0,1),('course-changed',0,3),('reserved',0,4),('editing',0,5),('replaced',1,6)]),
'H1':dict(models=[h1,h1u,h1z],width=360,theme='light',direction='ltr',dynamic_type='xLarge',fontScale=1.1,actions=[dict(type='sweep',state_id='browse'),tap('onsite'),tap('seats6'),tap('workbook','configured'),update('reconciled'),tap('reserve','reserved'),tap('edit'),update('empty')],states=[('browse',0,0),('configured',0,3),('reconciled',1,4),('reserved',1,5),('empty',2,7)])}
# Fixed business oracle: independent state reducer, never imports candidate or builder plan.
def reconcile(m,s=None):
 s=dict(s or dict(course=None,mode='remote',seats=1,workbook=False,confirmed=False));s['confirmed']=False
 active=[c for c in m['courses'] if c['capacity']>=1]
 c=next((c for c in active if c['id']==s['course']),active[0] if active else None)
 s['course']=c['id'] if c else None
 if not c:s.update(mode='remote',seats=0,workbook=False);return s
 if s['mode']=='onsite' and not c['onsiteAvailable']:s['mode']='remote'
 if s['seats'] not in (1,3,6) or s['seats']>c['capacity']:s['seats']=max(n for n in (1,3,6) if n<=c['capacity'])
 s['workbook']=s['workbook'] and s['mode']=='onsite' and c['workbookAvailable'];return s
def statefacts(m,s):
 c=next((c for c in m['courses'] if c['id']==s['course']),None);locked=s['confirmed'];cap=c['capacity'] if c else 0
 eligible=bool(c and s['mode']=='onsite' and c['workbookAvailable']);n=s['seats'];price=(c['seatPriceCents']-(m['remoteDiscountCents'] if s['mode']=='remote' else 0)) if c else 0
 total=n*price+(n*m['workbookCents'] if s['workbook'] else 0)+(m['onsiteFeeCents'] if c and s['mode']=='onsite' else 0)
 mode='In person' if s['mode']=='onsite' else 'Remote';money=f'${total//100}.{total%100:02d}'
 summary=f'Total {money} · {n} '+('seat' if n==1 else 'seats')+f' · {mode} · '+('Workbooks' if s['workbook'] else 'No workbooks')
 return {'heading':m['title'],'detail':m['detail'],'course-a-selected':s['course']=='foundations','course-b-enabled':any(c['id']=='advanced' and c['capacity']>=1 for c in m['courses']) and not locked,'onsite-enabled':bool(c and c['onsiteAvailable']) and not locked,'onsite-selected':s['mode']=='onsite','remote-selected':s['mode']=='remote','seats3-enabled':cap>=3 and not locked,'seats6-enabled':cap>=6 and not locked,'seats3-selected':n==3,'seats6-selected':n==6,'workbook-enabled':eligible and not locked,'workbook-selected':s['workbook'],'total':summary,'reserve-enabled':bool(c) and not locked,'edit-enabled':locked,'status':f"Reserved {n} "+('seat' if n==1 else 'seats')+f" for {c['title']}." if locked else 'Choose options, then reserve.' if c else 'No courses available.'}
def apply(m,s,a):
 s=dict(s);events=[];target=a.get('target');c=next((c for c in m['courses'] if c['id']==s['course']),None)
 if a['type']!='tap':return s,events
 enabled=not s['confirmed']
 if target=='edit':
  if s['confirmed']:s['confirmed']=False
 elif enabled and target in ('courseA','courseB'):
  id={'courseA':'foundations','courseB':'advanced'}[target]
  if any(c['id']==id and c['capacity']>=1 for c in m['courses']):s['course']=id;s=reconcile(m,s)
 elif enabled and c:
  if target=='remote':s['mode']='remote';s['workbook']=False
  elif target=='onsite' and c['onsiteAvailable']:s['mode']='onsite'
  elif target in ('seats3','seats6'):
   n=int(target[-1]);
   if n<=c['capacity']:s['seats']=n
  elif target=='workbook' and s['mode']=='onsite' and c['workbookAvailable']:s['workbook']=not s['workbook']
  elif target=='reserve':
   s['confirmed']=True;events=[f"reserve:{s['course']}:{s['mode']}:{s['seats']}:{str(s['workbook']).lower()}"]
 return s,events
ruledefs=[('heading','control','title','label'),('detail','control','detail','label'),('course-a-selected','control','courseA','selected'),('course-b-enabled','control','courseB','enabled'),('onsite-enabled','control','onsite','enabled'),('onsite-selected','control','onsite','selected'),('remote-selected','control','remote','selected'),('seats3-enabled','control','seats3','enabled'),('seats6-enabled','control','seats6','enabled'),('seats3-selected','control','seats3','selected'),('seats6-selected','control','seats6','selected'),('workbook-enabled','control','workbook','enabled'),('workbook-selected','control','workbook','selected'),('total','control','total','label'),('reserve-enabled','control','reserve','enabled'),('status','control','status','label'),('edit-enabled','control','edit','enabled'),('activation','event',None,None),('caller-update','event',None,None),('title-font','text_layout','title','font_sp'),('title-ink','text_layout','title','color_argb'),('detail-ellipsis','text_layout','detail','ellipsized'),('reserve-height','geometry','reserve','height'),('reserve-visible','manual','reserve',None)]
rules=[]
for id,kind,t,p in ruledefs:
 r=dict(id=id,kind=kind)
 if t:r['target']=t
 if p:r['property']=p
 if id=='caller-update':r['stimulus']='caller_update'
 if id=='title-font':r['op']='near'
 if kind=='geometry':r.update(op='gte',basis='control',measurement='accessibility_box')
 if kind=='manual':r.update(coverage='target',allowed_methods=['visual'])
 rules.append(r)
reference={'tokens':{'ios':{'titleFont':typed(22,'pt'),'minimumAction':typed(44,'pt')},'android':{'titleFont':typed(22,'sp'),'fontTolerance':typed(.05,'sp'),'minimumAction':typed(48,'dp')},'titleFontUnsupportedIOS':typed(22,'sp'),'fontToleranceIOS':typed(.05,'sp'),'lightInk':typed('#FF172B3A','argb'),'darkInk':typed('#FFF1F5F9','argb'),'detailEllipsis':typed(False,'bool'),'reserveVisible':typed('Reserve seats label is fully visible without clipped glyphs or ellipsis.','string')},'cases':{}}
scenarios={};table=[]
for cid,cfg in cases.items():
 dest=(P if cid.startswith('P') else V)/'cases'/cid;models=cfg['models'];acts=cfg['actions'];states=cfg['states'];m=models[0];s=reconcile(m);idx=0;history={};eventhist={}
 for ai,a in enumerate(acts):
  if a['type']=='apply_next_fixture':idx+=1;m=models[idx];s=reconcile(m,s);events=[]
  else:s,events=apply(m,s,a)
  history[ai]=(idx,m,dict(s));eventhist[ai]=events
 fixture={k:cfg[k] for k in ('width','theme','direction','dynamic_type','fontScale')};fixture.update(viewportHeight=640,state_capture=False,max_scrolls=28,initial=models[0],updates=models[1:],observation_targets=list(bind.values()))
 put(dest/'fixtures.json',fixture)
 literals=[dict(a,**({'target':bind[a['target']]} if 'target'in a else {})) for a in acts]
 for platform in ('ios','android'):put(dest/f'actions.{platform}.json',literals)
 values={r['id']:{} for r in rules};reference['cases'][cid]={};state_specs=[]
 for sid,ii,ai in states:
  ix,m,ss=history[ai];f=statefacts(m,ss);reference['cases'][cid][sid]={};state_specs.append(dict(id=sid,input_index=ii,after_action=ai,coverage='full_content' if acts[ai]['type']=='sweep' else 'targets'))
  for r in rules:
   rid=r['id'];reason=None;unit='bool';v=f.get(rid)
   if rid=='course-b-enabled' and not any(c['id']=='advanced' for c in m['courses']):reason='This caller catalog does not contain the advanced course.'
   if rid in ('heading','detail','total','status'):unit='string'
   if rid in ('activation','caller-update'):
    if rid=='activation' and acts[ai]['type']!='tap':reason='Selected checkpoint is not an activation stimulus.'
    if rid=='caller-update' and acts[ai]['type']!='apply_next_fixture':reason='Selected checkpoint is not a caller replacement stimulus.'
    v=eventhist[ai];unit='events'
   for platform in ('ios','android'):
    p=f'/cases/{cid}/{sid}/{rid}/{platform}'
    expected=v;u=unit
    if rid=='title-font':expected=22;u='sp'
    if rid=='title-ink':expected='#FFF1F5F9' if cfg['theme']=='dark' else '#FF172B3A';u='argb'
    if rid=='detail-ellipsis':expected=False;u='bool'
    if rid=='reserve-height':expected=44 if platform=='ios' else 48;u='pt' if platform=='ios' else 'dp'
    if rid=='reserve-visible':expected=reference['tokens']['reserveVisible']['value'];u='string'
    reference['cases'][cid][sid].setdefault(rid,{})[platform]=typed(expected,u)
    klass='business_transition' if r['kind']=='event' else 'style_native' if r['kind']=='text_layout' else 'visual' if r['kind']=='manual' else 'native_geometry' if r['kind']=='geometry' else 'business_current' if rid not in ('heading','detail') else 'native_content'
    table.append(dict(id=f'{cid}/{platform}/{sid}/{rid}',case=cid,platform=platform,state=sid,requirement=rid,aspect=rid,**{'class':klass},kind=r['kind'],expected=expected,unit=u,op=r.get('op','eq'),tolerance=.05 if rid=='title-font' else None,applicable=not bool(reason),na_reason=reason,source_pointer=p,source_file='public/reference.json' if cid.startswith('P') else 'private/reference.hidden.json',state_spec=state_specs[-1],rule=r,action=acts[ai],action_index=ai))
   if reason:cell={'not_applicable':reason}
   else:
    cell={platform:{'source':'reference','pointer':f'/cases/{cid}/{sid}/{rid}/{platform}'} for platform in ('ios','android')}
    if rid=='title-font':cell['tolerance']={'ios':{'source':'reference','pointer':'/tokens/fontToleranceIOS'},'android':{'source':'reference','pointer':'/tokens/android/fontTolerance'}}
   values[rid][sid]=cell
 scenarios[cid]=dict(states=state_specs,actions=acts,values=values)
put(P/'bindings.json',bind);put(V/'bindings.hidden.json',bind)
publicref=dict(reference,cases={k:v for k,v in reference['cases'].items() if k.startswith('P')});hiddenref=dict(reference,cases={'H1':reference['cases']['H1']})
put(P/'reference.json',publicref);put(V/'reference.hidden.json',hiddenref)
for dst,ref,ids in [(P,'reference.json',['P1','P2']),(V,'reference.hidden.json',['H1'])]:
 contract=dict(version=1,design_owner='Independent business UI designer (procedurally blind context)',approval_reference='private/DESIGN-SEAL.json; design owner approval before candidate source',sources=[dict(id='reference',path=ref,sha256=sha(dst/ref))],required_rule_ids=[r['id'] for r in rules],rules=rules,scenarios={id:scenarios[id] for id in ids});put(dst/'contract.json',contract)
put(V/'acceptance-table.json',dict(version=1,scope='Every frozen runtime cell; API/input checks separately.',rows=table))
print('Generated',len(table),'runtime cells')
