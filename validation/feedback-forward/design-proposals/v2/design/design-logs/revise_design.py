#!/usr/bin/env python3
"""Revision 2: original inputs retained; no SDK, product source or implementation."""
from pathlib import Path
import sys, json, hashlib, copy, datetime, importlib.util, shutil, html, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT.parent/'design-proposals'/'v1'/'design'
REVIEWS=ORIGINAL.parent/'review'
SKILL=ROOT.parent/'candidate-v9'
sys.path.insert(0,str(SKILL/'scripts'))
import design_contract as dc
import requirement_routes as rr
import execution_plan as ep
import review_contract as rc
from PIL import Image, ImageDraw, ImageFont
spec=importlib.util.spec_from_file_location('v1_seed',ROOT/'design-logs'/'v1-author-seed.py')
seed=importlib.util.module_from_spec(spec);spec.loader.exec_module(seed)
TERMS=seed.TERMS;COLORS=seed.COLORS
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v)
def val(v,u):return {'value':v,'unit':u}
def ref(p):return {'source':'reference','pointer':p}
def cell(p):return {'ios':ref(p),'android':ref(p)}
def load(p):return dc.load(p)
FULL=['overview','permitted','requested','requested-closed','replaced']
BASE_STATES=['overview','opened','permitted','cleared','restored','requested','requested-closed','replaced','held-choice']

def state_definitions(task):
    result=[]
    for name,index,input_index,stimulus in [
      ('overview',0,0,None),('opened',1,0,1),('permitted',3,0,2),('cleared',4,0,4),('restored',5,0,5),
      ('requested',7,0,6),('requested-closed',9,0,8),('replaced',11,1,10),('held-choice',12,1,12)]:
        r={'id':name,'input_index':input_index,'after_action':index,'coverage':'full_content' if name in FULL else 'targets'}
        if stimulus is not None:r['stimulus_action']=stimulus
        result.append(r)
    if task=='T2':result.append({'id':'competing-gates','input_index':2,'after_action':13,'stimulus_action':13,'coverage':'targets'})
    return result

def local_state(task,name):
    open_=name in ['opened','permitted','cleared','restored','requested']
    requested=name in ['requested','requested-closed']
    changed=name in ['permitted','restored','requested','requested-closed','held-choice']
    selected=changed if task=='T1' else not changed
    return open_,requested,selected

def expectations(task,fixture,states):
    result={};t=TERMS[task]
    for s in states:
        name=s['id'];i=s['input_index'];m=fixture['initial'] if i==0 else fixture['updates'][i-1]
        open_,requested,selected=local_state(task,name)
        if task=='T1':
            status='Seal needs attention' if not m['sealIntact'] else 'Coolant not ready' if not m['coolantReady'] else 'Release requested' if requested else 'Ready for release' if selected else 'Awaiting check'
            enabled=m['sealIntact'] and m['coolantReady'] and selected and not requested
            subtitle=m['destination']+' · '+m['temperatureRange']
            choice=t['choice_on'] if selected else t['choice_off']
            choice_event=f'transfer.ack:{m["id"]}:{str(selected).lower()}'
            request_event=f'transfer.release:{m["id"]}'
        else:
            status='Storage needed' if m['availableMB']<m['downloadSizeMB'] else 'Download requested' if requested else 'Wi-Fi required' if m['meteredConnection'] and selected else 'Ready to download'
            enabled=m['availableMB']>=m['downloadSizeMB'] and not(m['meteredConnection'] and selected) and not requested
            subtitle=m['language']+' · '+str(m['downloadSizeMB'])+' MB'
            choice='Wi-Fi only';choice_event=f'audio.wifiOnly:{m["id"]}:{str(selected).lower()}'
            request_event=f'audio.download:{m["id"]}:{"wifi" if selected else "mobile"}'
        role='blocked' if status in ['Seal needs attention','Coolant not ready','Storage needed','Wi-Fi required'] else 'requested' if requested else 'ready' if enabled else 'waiting'
        result[name]={'title':val(m['title'],'string'),'subtitle':val(subtitle,'string'),'status':val(status,'string'),
          'disclosure':val(t['disclosure_on'] if open_ else t['disclosure_off'],'string'),'disclosureEnabled':val(True,'bool'),
          'choice':val(choice,'string'),'selected':val(selected,'bool'),'choiceEnabled':val(not requested,'bool'),
          'primary':val(t['primary_done'] if requested else t['primary'],'string'),'enabled':val(enabled,'bool'),
          'statusColor':val(COLORS[role],'argb'),'buttonColor':val(COLORS['enabled' if enabled else 'disabled'],'argb'),
          'choiceEvents':val([choice_event],'events'),'requestEvents':val([request_event],'events'),
          'open':val(open_,'bool'),'requested':val(requested,'bool')}
    return result

def action_route(task,expected):
    def tap(target,state=None,event=None):
        a={'type':'tap','target':target,'reveal':True,'max_steps':18,'observation_max_scrolls':18}
        if state:a['state_id']=state
        if event:a['expect_callback']=event
        return a
    def sweep(state):return {'type':'sweep','state_id':state,'max_steps':18}
    a=[sweep('overview'),tap('disclosure','opened'),
       tap('choice',event=expected['permitted']['choiceEvents']['value'][0]),sweep('permitted'),
       tap('choice','cleared',expected['cleared']['choiceEvents']['value'][0]),
       tap('choice','restored',expected['restored']['choiceEvents']['value'][0]),
       tap('primary',event=expected['requested']['requestEvents']['value'][0]),sweep('requested'),
       tap('disclosure'),sweep('requested-closed'),{'type':'apply_next_fixture'},sweep('replaced'),
       tap('choice','held-choice',expected['held-choice']['choiceEvents']['value'][0])]
    if task=='T2':a.append({'type':'apply_next_fixture','state_id':'competing-gates','observation_max_scrolls':18})
    return a

def questions(task):
    t=TERMS[task]
    q={
     'title-wrapping':('title','wrapping','The title visibly displays its complete supplied text through natural wrapping, without truncation or an ellipsis.','target'),
     'subtitle-wrapping':('subtitle','wrapping','The subtitle visibly displays its complete supplied text through natural wrapping, without truncation or an ellipsis.','target'),
     'status-wrapping':('statusText','wrapping','The status text visibly displays its complete status string through natural wrapping, without truncation or an ellipsis.','target'),
     'disclosure-wrapping':('disclosure','wrapping','The disclosure button visibly displays its complete label through natural wrapping, without truncation or an ellipsis.','target'),
     'choice-wrapping':('choice','wrapping','The choice button visibly displays its complete label through natural wrapping, without truncation or an ellipsis.','target'),
     'primary-wrapping':('primary','wrapping','The primary button visibly displays its complete label through natural wrapping, without truncation or an ellipsis.','target'),
     'heading-wrapping':('canvas','wrapping',f'Every expanded {t["section_name"].lower()} heading visibly displays its complete supplied text through natural wrapping, without truncation or an ellipsis.','full_content'),
     'body-wrapping':('canvas','wrapping','Every expanded body paragraph visibly displays its complete supplied text through natural wrapping, without truncation or an ellipsis.','full_content'),
     'title-hierarchy':('canvas','hierarchy','The title is visually more prominent than the expanded section headings.','full_content'),
     'horizontal-clipping':('canvas','clipping','Visible content remains inside the component horizontal bounds without clipping.','full_content'),
     'row-overlap':('canvas','overlap','Successive rows in the component do not visually overlap.','full_content'),
     'flow-order':('canvas','content_presence','Main component blocks occur in this reading order: ink accent, title, subtitle, status, disclosure, any expanded sections, choice, primary.','full_content'),
     'single-column':('canvas','hierarchy','Main component blocks form one vertical column.','full_content'),
     'full-width-canvas':('canvas','content_presence','The component-painted pale canvas spans the complete width offered inside the host horizontal gutters.','full_content'),
     'collapsed-headings':('canvas','content_presence',f'No {t["section_name"].lower()} section heading is visible while the disclosure is closed.','full_content'),
     'collapsed-bodies':('canvas','content_presence',f'No {t["section_name"].lower()} body paragraph is visible while the disclosure is closed.','full_content'),
     'expanded-order':('canvas','content_presence',f'The eight expanded {t["section_name"].lower()} heading/body pairs appear in caller order.','full_content')}
    return q

def source_audits(task,reference):
    t=TERMS[task];reference['audit_propositions']={};audits=[]
    clauses={
     'production-component':'The declared native component is implemented in the exact production file named by its public API.',
     'caller-driven-rendering':'The production component renders the supplied caller model values rather than a separate observer-only approximation.',
     'disclosure-production-state':'Disclosure state is owned by the production component.',
     'choice-production-state':'Choice state is owned by the production component.',
     'requested-production-state':'Requested state is owned by the production component.',
     'identity-reset-disclosure':'The production component resets disclosure to closed when the caller model ID changes.',
     'identity-reset-choice':'The production component resets choice to '+('false' if task=='T1' else 'true')+' when the caller model ID changes.',
     'identity-reset-requested':'The production component resets requested to false when the caller model ID changes.',
     'reset-quiet':'The production identity-reset path invokes no caller business callback.',
     'native-disclosure-button':'Disclosure is implemented as a native Button control.',
     'native-choice-button':'Choice is implemented as a native Button control.',
     'native-primary-button':'Primary is implemented as a native Button control.',
     'native-selected':'The choice exposes its actual selected state through native selected semantics.',
     'choice-native-disabled':'The choice uses actual native disabled semantics when disabled.',
     'primary-native-disabled':'The primary uses actual native disabled semantics when disabled.',
     'canvas-preserve-controls':'The canvas accessibility container preserves descendant Buttons as independently addressable controls.',
     'surface-preserve-controls':'The surface accessibility container preserves descendant Buttons as independently addressable controls.',
     'unique-semantic-ids':'Each declared component semantic identifier is attached to exactly one real component node.',
     'status-band-provenance':'The status semantic identifier belongs to the actual painted status band, not a geometry proxy.',
     'status-text-provenance':'The statusText semantic identifier belongs to the actual displayed status Text allocation, not a geometry proxy.',
     'no-nested-scroll':'The production component introduces no nested scrolling container; scrolling belongs to the supplied parent.',
     'no-blank-padding-rows':'The production component inserts no fixed-height blank row or spacer for the purpose of manufacturing long-content scrolling.',
     'model-row-order':'Expanded section nodes are generated from caller rows in caller order.',
     'no-hidden-input-special-cases':'Rendering and business decisions do not special-case observer scenario names, fixture IDs, or expected test values.',
     'callback-model-id':'The business request callback forwards the current caller model ID.',
     'callbacks-only-actions':'The component invokes caller business callbacks only from enabled user-action paths.',
     'no-callback-on-disclosure':'The disclosure open and close paths invoke no caller business callback.',
     'no-primary-callback-on-disabled':'A disabled primary cannot invoke its caller business callback.',
     'no-choice-callback-on-disabled':'A disabled choice cannot invoke its caller business callback.',
    }
    if task=='T1':
        clauses.update({
         'guard-predicate':'The release enabled predicate is exactly sealIntact && coolantReady && acknowledged && !requested.',
         'guard-priority':'The status decision order is broken seal, unavailable coolant, requested, acknowledged, then awaiting check.',
         'choice-toggle':'Every successful pre-request confirmation toggle flips the current acknowledgement Boolean.',
         'choice-callback-value':'The confirmation callback forwards the resulting acknowledgement Boolean.',
         'choice-callback-count':'A successful pre-request confirmation toggle invokes its caller callback exactly once.',
         'release-requested-state':'A successful eligible release changes local requested state to true.',
         'release-callback-count':'A successful eligible release invokes onRelease exactly once.',
         'no-physical-transfer':'The component initiates no freezer hardware or physical transfer operation.'})
    else:
        clauses.update({
         'guard-predicate':'The download enabled predicate is exactly availableMB >= downloadSizeMB && !(meteredConnection && wifiOnly) && !requested.',
         'guard-priority':'The status decision order is insufficient storage, requested, metered connection with Wi-Fi only, then ready.',
         'choice-toggle':'Every successful pre-request Wi-Fi-only toggle flips the current Wi-Fi-only Boolean.',
         'choice-callback-value':'The Wi-Fi-only callback forwards the resulting preference Boolean.',
         'choice-callback-count':'A successful pre-request Wi-Fi-only toggle invokes its caller callback exactly once.',
         'download-requested-state':'A successful eligible download request changes local requested state to true.',
         'download-callback-count':'A successful eligible download request invokes onDownload exactly once.',
         'callback-preference':'The download request callback forwards the current local Wi-Fi-only preference.',
         'no-disk-measurement':'The component does not measure disk capacity; it uses the caller-supplied whole-MB availableMB and downloadSizeMB values.',
         'no-audio-fetch':'The component does not fetch or download audio data.'})
    for platform,path in [('ios',t['ios_path']),('android',t['android_path'])]:
        for key,clause in clauses.items():
            rid=platform+'-'+key;reference['audit_propositions'][rid]=val(clause,'string')
            audits.append({'id':rid,'clause':clause,'priority':'must','files':[path],
               'proposition':ref('/audit_propositions/'+rid),'expected':ref('/truth')})
        bridge='Bridge.swift' if platform=='ios' else 'ObserverBridge.kt'
        for key,clause in {
          'bridge-no-ui':'The approved bridge constructs no substitute component UI.',
          'bridge-no-state':'The approved bridge owns no local component business state.',
          'bridge-no-identity-reset':'The approved bridge applies no identity-reset wrapper around the production component.',
          'bridge-current-input':'The approved bridge decodes the current supplied fixture into the declared production model.',
          'bridge-callback-forwarding':'The approved bridge forwards actual production callbacks into observer event receipt.'}.items():
            rid=platform+'-'+key;reference['audit_propositions'][rid]=val(clause,'string')
            audits.append({'id':rid,'clause':clause,'priority':'must','files':['@design/'+bridge],
               'proposition':ref('/audit_propositions/'+rid),'expected':ref('/truth')})
    reference['implementation_audits']=audits
    return {'version':1,'index':{'source':'reference','pointer':'/implementation_audits'}}

def brief(task,scope):
    old=(ORIGINAL/task/scope/'BRIEF.md').read_text()
    first='The four checkpoints are overview, permitted (after disclosure and choice activation), requested (after a successful business primary activation), and replaced (after a real caller fixture update followed by a fresh full sweep).'
    new=('The original overview, permitted, requested, and replaced full checkpoints are retained. Revision 2 adds opened, cleared, restored, and held-choice transition checkpoints plus a full requested-closed checkpoint. '
         +('T2 additionally appends a separately sourced competing-gates caller fixture and targeted checkpoint; original caller records remain unchanged. ' if task=='T2' else '')+
         'There are '+('10' if task=='T2' else '9')+' representative states, prospectively approved by the parent coordinator before implementation. The transition table and explicit action indices are in reference.json. Extra targeted checkpoints establish their declared state/callback facts; they do not claim a complete content sweep. The five complete visual states each retain fresh overlapping full-content evidence.')
    old=old.replace(first,new)
    old=old.replace('Status text starts at least 16 native units inside its painted band; keep its leading 4% empty for the approved fill sample.',
        'Status text starts at least 16 pt/dp inside the logical leading edge of its painted band. Its separately identified native text semantic boundary is measured against the band semantic boundary using inset_left in LTR and inset_right in RTL, with gte 16 and no invented tolerance. This is a measured boundary inset, not a computed padding attribute or glyph-ink measurement. The whole logical leading 4% strip must contain only the status fill; an independent pixel atom samples that complete physical-left strip in LTR and physical-right strip in RTL with minimum support 1.0. Status and primary fills are rectangular without rounded corners or borders so the approved solid regions remain meaningful.')
    old=old.replace('two independent visual judges inspect every original state sweep for the qualitative atoms.',
        'two independent visual judges inspect original full-state sweeps or the explicitly approved original target frames for the qualitative atoms. Title, subtitle, status, disclosure, choice, primary, section-heading, and section-body wrapping each has a separate source-backed proposition.')
    old=old.replace('Long content needs overlapping sweep evidence and actual bottom reachability in each expanded state.',
        'Long-content acceptance requires overlapping sweep evidence and actual bottom reachability in the representative permitted and requested full states. The intermediate opened/cleared/restored states add only targeted transition verification and cannot replace those full expanded sweeps.')
    old+='''

The source-only MUST index is `/implementation_audits` in the same sealed independent reference and lock. `implementation-audit.json` points to that index. Platform-specific audit IDs name exact production paths and one source-code proposition each. The approved shared source-audit sidecar binds future reviewer actuals to exact final source SHA and file/line evidence; missing or uncertain source audits block complete release. This gate is ANDed with unchanged runtime acceptance. Source-audit assertions are deliberately outside the runtime-only obligation index and cannot claim rendered padding, color, font, wrapping, geometry, callback dispatch, or actual update success. The same sidecar and conditions apply to both comparison arms. No sidecar implementation or product source is authored here.

Whole-brief sampling limits: these cases are representative rather than a Cartesian truth table. Exact-capacity equality and the unmetered Wi-Fi-only true download path are reviewed in the source predicate/callback audit, not claimed as executed native cases. Same-ID update behavior remains unspecified. Actual native semantic allocations, exact image mapping, real full sweeps, and the proposed targeted observation support remain unverified until approved native execution. The rendered 16-unit inset remains a runtime MUST and has not been reclassified as source-only or advisory.
'''
    return old

def api(task,scope):
    old=(ORIGINAL/task/scope/'API.md').read_text()
    old=old.replace('`.status`, `.disclosure`','`.status`, `.statusText`, `.disclosure`')
    old=old.replace('Status is one semantic band with its label on the whole painted allocation. Its text must not create another copy of that identifier.',
       'Status is one semantic band with its label on the whole painted allocation, and a separate child Text node uses the distinct identifier `'+TERMS[task]['prefix']+'.statusText`. Keep the band and text as separate semantic allocations without hiding the text child or duplicating either identifier. The statusText semantic frame is the real native text allocation, not a proxy or a fabricated geometry marker. Its logical leading inset from the real painted band must be at least 16 pt/dp. Public LTR cases measure inset_left and private RTL measures inset_right. Both boxes must be fully visible in one coherent native frame. This does not assert a generic computed padding attribute.')
    old+='\nSource-only implementation constraints and their exact platform paths are separately indexed at reference.json `/implementation_audits`; they remain mandatory in addition to native observation. Bridges remain byte-identical to v1 and continue calling these public APIs directly.\n'
    return old

def render_reference(dest,task,case,reference,fixture):
    """Static prospective reference only: no native renderer or SDK."""
    from math import ceil
    width=fixture['width'];scale=fixture['fontScale'];rtl=fixture['direction']=='rtl';x=40;cw=width-80
    for name,e in reference['states'].items():
        items=[];y=48
        def wrap(text,size,w):
            font=ImageFont.load_default(size=int(size));lines=[];line=''
            for word in text.split():
                candidate=(line+' '+word).strip()
                if line and font.getlength(candidate)>w:lines.append(line);line=word
                else:line=candidate
            if line:lines.append(line)
            return lines
        def text(s,size,bold=False,left=x,w=cw,gap=12):
            nonlocal y
            fs=size*scale;lh=round(fs*1.35)
            for line in wrap(s,fs,w):items.append(('text',left+w if rtl else left,y+fs,line,fs,'#172B4D','bold' if bold else 'normal','end' if rtl else 'start'));y+=lh
            y+=gap
        items.append(('rect',x+cw-6 if rtl else x,y,6,40,'#172B4D'));y+=52
        text(e['title']['value'],22,True);text(e['subtitle']['value'],16)
        sy=y;status_lines=wrap(e['status']['value'],17*scale,cw-32)
        sh=max(56,len(status_lines)*round(17*scale*1.35)+28)
        items.append(('rect',x,sy,cw,sh,'#'+e['statusColor']['value'][3:]));y=sy+14
        for line in status_lines:
            items.append(('text',x+cw-16 if rtl else x+16,y+17*scale,line,17*scale,'#172B4D','bold','end' if rtl else 'start'));y+=round(17*scale*1.35)
        y=sy+sh+12
        text(e['disclosure']['value'],17,True)
        if e['open']['value']:
            for row in reference['rows']:text(row['title'],17,True);text(row['body'],16,gap=16)
        choice_top=y;choice_text=('[x] ' if e['selected']['value'] else '[ ] ')+e['choice']['value']
        text(choice_text,17,gap=0);y=max(y,choice_top+56)+12
        items.append(('rect',x,y,cw,56,'#'+e['buttonColor']['value'][3:]))
        items.append(('text',x+cw/2,y+34,e['primary']['value'],17*scale,'#FFFFFF' if e['enabled']['value'] else '#172B4D','bold','middle'));y+=80
        height=max(600,ceil(y+24));image=Image.new('RGB',(width,height),'#F4F6FA');draw=ImageDraw.Draw(image)
        draw.rectangle((24,32,width-24,y-8),fill='#FFFFFF')
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
          f'<title>{html.escape(TERMS[task]["domain"])} — {case} — {name}</title>',
          '<desc>Independent static design illustration; no native font or frame measurement is claimed.</desc>',
          f'<rect width="{width}" height="{height}" fill="#F4F6FA"/><rect x="24" y="32" width="{width-48}" height="{y-40}" fill="#FFFFFF"/>']
        for it in items:
            if it[0]=='rect':
                _,xx,yy,w,h,c=it;draw.rectangle((xx,yy,xx+w,yy+h),fill=c);svg.append(f'<rect x="{xx}" y="{yy}" width="{w}" height="{h}" fill="{c}"/>')
            else:
                _,xx,yy,s,fs,c,weight,anchor=it;font=ImageFont.load_default(size=int(fs));draw.text((xx,yy),s,font=font,fill=c,anchor={'start':'ls','end':'rs','middle':'ms'}[anchor])
                svg.append(f'<text x="{xx}" y="{yy}" font-family="sans-serif" font-size="{fs}" font-weight="{weight}" fill="{c}" text-anchor="{anchor}">{html.escape(s)}</text>')
        svg.append('</svg>');out=dest/'references'/case;write(out/(name+'.svg'),'\n'.join(svg)+'\n');image.save(out/(name+'.png'))
        # Geometry here belongs solely to the static design illustration for self-check.
        STATIC_REFERENCES.append({'task':task,'scope':dest.name,'case':case,'state':name,'png_size':[width,height],
          'status_band':[x,sy,cw,sh],'status_lines':status_lines,'status_inner_width':cw-32,'reference_only':True})

def bundle(task,scope):
    t=TERMS[task];dest=ROOT/task/scope;dest.mkdir(parents=True,exist_ok=True)
    write(dest/'BRIEF.md',brief(task,scope));write(dest/'API.md',api(task,scope))
    for name in ['Bridge.swift','ObserverBridge.kt']:shutil.copyfile(ORIGINAL/task/scope/name,dest/name)
    oldref=load(ORIGINAL/task/scope/'reference.json')
    reference={'version':2,'component':t['component'],'design_owner':'Independent original design author, prospective review revision',
       'prior_source_sha256':sha(ORIGINAL/task/scope/'reference.json'),'palette':copy.deepcopy(oldref['palette']),
       'geometry':copy.deepcopy(oldref['geometry']),'typography_guidance':copy.deepcopy(oldref['typography_guidance']),
       'truth':val(True,'bool'),'quiet':val([],'events'),'labels':{'inkAccent':val('Ink accent','string')},'questions':{},'cases':{},'launch':{},'obligations':[]}
    for p,u in [('ios','pt'),('android','dp')]:reference['geometry'][p]['statusLeadingMinimum']=val(16,u)
    q=questions(task)
    for rid,(_,_,question,_) in q.items():reference['questions'][rid]=val(question,'string')
    states=state_definitions(task);names=[s['id'] for s in states]
    rules=[]
    def rule(rid,kind,target=None,**kw):rules.append({'id':rid,'kind':kind,**({'target':target} if target else {}),**kw})
    native=[('title-label','title','label','title'),('subtitle-label','subtitle','label','subtitle'),('status-label','status','label','status'),
      ('status-text-label','statusText','label','status'),('disclosure-label','disclosure','label','disclosure'),('disclosure-enabled','disclosure','enabled','disclosureEnabled'),
      ('choice-label','choice','label','choice'),('choice-selected','choice','selected','selected'),('choice-enabled','choice','enabled','choiceEnabled'),
      ('primary-label','primary','label','primary'),('primary-enabled','primary','enabled','enabled')]
    for rid,target,prop,key in native:rule(rid,'control',target,property=prop)
    rule('ink-accent-label','control','inkMark',property='label')
    rule('primary-height','geometry','primary',property='height',basis='control',measurement='accessibility_box',op='near')
    rule('choice-primary-gap','geometry','primary',reference_target='choice',property='gap_y',basis='control',measurement='accessibility_box',op='near')
    rule('status-leading-inset','geometry','statusText',reference_target='status',property='inset_left' if scope=='public' else 'inset_right',
         basis='semantic',measurement='accessibility_box',op='gte')
    for rid,target,prop in [('status-fill','status','rendered_fill_argb'),('primary-fill','primary','rendered_fill_argb'),
      ('surface-fill','surface','rendered_fill_argb'),('canvas-fill','canvas','rendered_canvas_argb'),('ink-fill','inkMark','rendered_ink_argb'),
      ('status-leading-clear','status','rendered_fill_argb')]:rule(rid,'manual',target,property=prop,coverage='target',allowed_methods=['native_pixels'])
    for i in range(8):
        for field in ['heading','body']:rule(f'section-{i}-{field}','control',f'section{i}{field.title()}',property='label')
    for rid,(target,aspect,question,coverage) in q.items():rule(rid,'manual',target,property=aspect,coverage=coverage,allowed_methods=['visual'])
    for rid in ['choice-receipt','request-receipt','disclosure-receipt']:rule(rid,'event')
    rule('replacement-quiet','event',stimulus='caller_update')
    bindings={}
    for r in rules:
        for k in ['target','reference_target']:
            if k in r:bindings[r[k]]={'identifier':t['prefix']+'.'+r[k]}
    for i in range(8):
        for field in ['heading','body']:bindings[f'section{i}{field.title()}']={'identifier':t['prefix']+f'.section.{i}.{field}'}
    put(dest/'bindings.json',bindings)
    scenarios={};environments={};cases=['P1','P2'] if scope=='public' else ['H1']
    for case in cases:
        f=load(ORIGINAL/task/scope/'cases'/case/'fixtures.json');original=copy.deepcopy(f)
        if task=='T2':
            competing=copy.deepcopy(f['updates'][0]);competing['id']={'P1':'TOUR-933','P2':'TOUR-978','H1':'TOUR-982'}[case]
            competing['availableMB']=competing['downloadSizeMB']-41;competing['meteredConnection']=True
            f['updates'].append(competing)
        # Required identifiers are observation configuration, not caller data.
        f['required_identifiers'].append(t['prefix']+'.statusText')
        assert f['initial']==original['initial'] and f['updates'][0]==original['updates'][0]
        expected=expectations(task,f,states)
        rows=copy.deepcopy(oldref['cases'][case]['rows'])
        reference['cases'][case]={'caller':copy.deepcopy(f),'states':expected,'rows':rows,
          'rowAssertions':[{'title':val(r['title'],'string'),'body':val(r['body'],'string')} for r in rows],
          'original_initial_sha256':dc.digest(original['initial']),'original_update_sha256':dc.digest(original['updates'][0])}
        reference['launch'][case]={};environments[case]={}
        put(dest/'cases'/case/'fixtures.json',f)
        for p in ['ios','android']:
            environment=load(ORIGINAL/task/scope/'cases'/case/f'environment.{p}.json')
            put(dest/'cases'/case/f'environment.{p}.json',environment);environments[case][p]=dc.digest(environment)
            reference['launch'][case][p]={'fixtures_sha256':dc.digest(f),'bridge_sha256':sha(dest/('Bridge.swift' if p=='ios' else 'ObserverBridge.kt')),'scenario':case,'platform':p}
        route=action_route(task,expected);bound=copy.deepcopy(route)
        for a in bound:
            if isinstance(a.get('target'),str):a['target']=copy.deepcopy(bindings[a['target']])
        for p in ['ios','android']:put(dest/'cases'/case/f'actions.{p}.json',bound)
        values={};keys={rid:key for rid,target,prop,key in native}
        for r in rules:
            rid=r['id'];values[rid]={}
            for s in states:
                st=s['id'];isfull=st in FULL;open_,requested,selected=local_state(task,st);base=f'/cases/{case}/states/{st}'
                if rid in keys:c=cell(base+'/'+keys[rid])
                elif rid=='ink-accent-label':
                    c=cell('/labels/inkAccent') if isfull else {'not_applicable':'This targeted business transition does not change the ink accent; its exact accessible label is checked in every representative full state.'}
                elif rid in ['primary-height','choice-primary-gap']:
                    c={p:ref('/geometry/'+p+('/primaryHeight' if rid=='primary-height' else '/choicePrimaryGap')) for p in ['ios','android']}
                    c['tolerance']={p:ref('/geometry/'+p+'/tolerance') for p in ['ios','android']}
                elif rid=='status-leading-inset':c={p:ref('/geometry/'+p+'/statusLeadingMinimum') for p in ['ios','android']}
                elif rid in ['status-fill','status-leading-clear','primary-fill']:c=cell(base+('/buttonColor' if rid=='primary-fill' else '/statusColor'))
                elif rid in ['surface-fill','canvas-fill','ink-fill']:c=cell('/palette/'+{'surface-fill':'surface','canvas-fill':'canvas','ink-fill':'ink'}[rid])
                elif rid.startswith('section-'):
                    if not open_:c={'not_applicable':'Disclosure is closed, so this expanded heading/body node does not exist; separate closed-heading and closed-body propositions cover representative closed full states.'}
                    elif not isfull:c={'not_applicable':'This intermediate checkpoint targets the declared transition. Exact expanded copy and complete content are checked in permitted and requested full sweeps of the unchanged same caller input.'}
                    else:
                        _,i,field=rid.split('-');c=cell(f'/cases/{case}/rowAssertions/{i}/'+('title' if field=='heading' else 'body'))
                elif rid in q:
                    coverage=q[rid][3]
                    if coverage=='full_content' and not isfull:c={'not_applicable':'This explicitly targeted intermediate transition does not assert full-content visual acceptance; representative full checkpoints retain this structural obligation.'}
                    elif rid in ['heading-wrapping','body-wrapping','title-hierarchy','expanded-order'] and not open_:
                        c={'not_applicable':'Expanded reading rows are absent while disclosure is closed; all visible compact text roles retain independent wrapping checks.'}
                    elif rid in ['collapsed-headings','collapsed-bodies'] and open_:
                        c={'not_applicable':'Disclosure is open; exact expanded text, wrapping and caller-order requirements cover the opposite condition.'}
                    else:c=cell('/truth')
                elif rid=='choice-receipt':
                    c=cell(base+'/choiceEvents') if st in ['permitted','cleared','restored','held-choice'] else {'not_applicable':'This state is not bound to an independent choice activation; its original stimulus has a different callback contract.'}
                elif rid=='request-receipt':
                    c=cell(base+'/requestEvents') if st=='requested' else {'not_applicable':'Only requested follows the successful business primary activation; disabled controls are never credited as callback dispatch.'}
                elif rid=='disclosure-receipt':
                    c=cell('/quiet') if st in ['opened','requested-closed'] else {'not_applicable':'Only opened and requested-closed are bound to actual disclosure activations and their own original receipt intervals.'}
                elif rid=='replacement-quiet':
                    c=cell('/quiet') if st in ['replaced','competing-gates'] else {'not_applicable':'Only a real caller-update stimulus can establish update quietness; other empty intervals are not substituted.'}
                else:raise ValueError(rid)
                if r['kind']=='manual' and rid not in q and not isfull:
                    c={'not_applicable':'This targeted transition checkpoint asserts state and callbacks, not a complete style result; unchanged/state-equivalent style is verified at the representative full checkpoints.'}
                values[rid][st]=c
        scenarios[case]={'states':copy.deepcopy(states),'actions':route,'values':values}
    obligations=[];routes={}
    for r in rules:
        rid=r['id'];applicable=[s for s in names if any('not_applicable' not in scenarios[c]['values'][rid][s] for c in cases)]
        if rid in q:clause=q[rid][2]
        else:clause={
          'title-label':'The current caller title has its complete exact accessible text.',
          'subtitle-label':'The current caller summary uses the exact specified string composition.',
          'status-label':'The status follows the original independently specified business guard/state precedence.',
          'status-text-label':'The actual status Text node exposes the exact current status string independently of the painted band.',
          'ink-accent-label':'The actual accessible solid ink mark has the exact label Ink accent.',
          'disclosure-label':'The disclosure label reflects the open or closed local state.',
          'disclosure-enabled':'The actual disclosure Button remains enabled, including after a business request.',
          'choice-label':'The actual choice Button exposes its exact specified accessible label.',
          'choice-selected':'The native selected trait reflects the current '+('acknowledgement.' if task=='T1' else 'Wi-Fi-only preference.'),
          'choice-enabled':'The actual choice is disabled after request and enabled after identity replacement.',
          'primary-label':'The primary exposes its exact normal or requested label.',
          'primary-enabled':'The actual primary enabled state follows the original complete business predicate.',
          'primary-height':'The actual native primary control height is 56 pt/dp within the independently fixed 0.75 pt/dp tolerance.',
          'choice-primary-gap':'The primary actual native control top edge is 12 pt/dp below the choice control bottom edge within 0.75 pt/dp.',
          'status-leading-inset':'The actual status Text semantic boundary is at least 16 pt/dp inside the painted band logical leading semantic boundary.',
          'status-fill':'The approved status-band solid region has the independently fixed opaque state-role fill.',
          'status-leading-clear':'The entire logical leading 4% strip of the painted status band contains only the current status fill.',
          'primary-fill':'The approved primary solid region has the independently fixed enabled or disabled fill.',
          'surface-fill':'The component surface gutter renders the independently fixed opaque white role.',
          'canvas-fill':'The component canvas gutter renders the independently fixed opaque pale role.',
          'ink-fill':'The solid ink accent renders the independently fixed opaque navy role.',
          'choice-receipt':'Each selected forward, reverse, restored, or held choice activation emits exactly its independent one-event receipt after demonstrated native dispatch.',
          'request-receipt':'The successful native primary activation emits exactly the independently fixed business callback event.',
          'disclosure-receipt':'Each selected successful disclosure open or close activation has its own empty original business callback interval.',
          'replacement-quiet':'Each selected same-process caller replacement has an empty original business callback interval.'
        }.get(rid,f'Expanded {rid} exposes its exact caller text.')
        risk='behavior' if r['kind']=='event' or r.get('property') in ['enabled','selected'] else 'layout' if r['kind']=='geometry' or rid in ['horizontal-clipping','row-overlap'] or 'wrapping' in rid else 'style' if r['kind']=='manual' else 'content'
        obligations.append({'id':rid,'clause':clause,'priority':'must','states':applicable,'risk':risk})
        regress=['primary-enabled','status-label','choice-selected'] if rid=='choice-receipt' else ['choice-enabled','primary-enabled','primary-label','status-label','disclosure-enabled'] if rid=='request-receipt' else []
        routes[rid]={'rule_ids':[rid],'reason':clause+' This is a runtime-only route on both native platforms; source-only constraints are indexed separately.', 'regression_obligations':regress}
    obligations.append({'id':'typography-nominal','clause':oldref['obligations'][-1]['clause'],'priority':'advisory','states':names,'risk':'style'})
    routes['typography-nominal']={'rule_ids':[],'reason':'Original explicitly advisory generic computed SwiftUI typography/text ink/internal layout values remain unavailable. No rendered MUST is moved to this route.','regression_obligations':[]}
    reference['obligations']=obligations
    audit_contract=source_audits(task,reference)
    put(dest/'implementation-audit.json',audit_contract)
    reference['state_definitions']=states
    reference['sampling_limits']={'runtime':'Representative states; not a Cartesian truth table. Exact-capacity equality and a Wi-Fi-only true unmetered request are not claimed as native executions.',
      'source_audit':'Source audit is a mandatory separate conjunct and cannot prove native rendered facts or actual dispatch.',
      'provider':'Frozen Android may perform additional sweeps after targeted actions; the plan makes only its declared target-coverage claim.'}
    put(dest/'reference.json',reference)
    contract={'version':1,'design_owner':'Independent original design author; revised solely from official preimplementation semantic review',
      'approval_reference':str((dest/'approval.json').relative_to(ROOT))+'; revised proposal awaits fresh independent feasibility review',
      'sources':[{'id':'reference','path':'reference.json','sha256':sha(dest/'reference.json')}],
      'required_rule_ids':[r['id'] for r in rules],'rules':rules,'scenarios':scenarios}
    put(dest/'contract.json',contract)
    lock=dc.seal(dest/'contract.json',dest);locksha=dc.digest(lock);put(dest/'design-lock.json',lock)
    atoms=[]
    for rid,target,aspect,region,visibility,support in [
      ('status-fill','status','rendered_fill',[.012,.20,.035,.80] if scope=='public' else [.965,.20,.988,.80],'fully_visible',.85),
      ('status-leading-clear','status','rendered_fill',[0,0,.04,1] if scope=='public' else [.96,0,1,1],'fully_visible',1.0),
      ('primary-fill','primary','rendered_fill',[.02,.20,.04,.80],'fully_visible',.85),
      ('surface-fill','surface','rendered_fill',[.012,0,.028,1],'visible_fragment',.85),
      ('canvas-fill','canvas','rendered_canvas',[.002,0,.015,1],'visible_fragment',.85),
      ('ink-fill','inkMark','rendered_ink',[.2,.2,.8,.8],'fully_visible',.85)]:
        atoms.append({'rule_id':rid,'aspect':aspect,'method':'native_pixels','sampling':{'region':region,'minimum_pixels':12,
          'minimum_support':support,'channel_tolerance':0,'basis':'semantic','visibility':visibility}})
    for rid,(target,aspect,question,coverage) in q.items():atoms.append({'rule_id':rid,'aspect':aspect,'method':'visual','question':ref('/questions/'+rid)})
    policy={'version':1,'design_lock_sha256':locksha,'approval_reference':contract['approval_reference'],
      'ownership':{r['target']:'component' for r in rules if r['kind']=='manual'},'atoms':atoms};put(dest/'policy.json',policy)
    routefile={'version':1,'index':{'source':'reference','pointer':'/obligations'},'routes':routes};put(dest/'routes.json',routefile)
    approval={'version':2,'status':'independently_revised_preimplementation_proposal_pending_fresh_review','scope':task+'/'+scope,
      'design_lock_sha256':locksha,'policy_sha256':dc.digest(policy),'routes_sha256':dc.digest(routefile),
      'implementation_audit_sha256':dc.digest(audit_contract),'environment_sha256':environments,'launch':reference['launch'],
      'production_paths':{'ios':[t['ios_path']],'android':[t['android_path']]},'production_repositories':{'ios':'AlertToast','android':'Reply'},
      'prior_proposal_seal_sha256':sha(ORIGINAL/'DESIGN-SEAL.json'),'official_review_sha256':sha(REVIEWS/task/'review.json'),
      'prospective_protocol_amendment':'Root explicitly approved 9 T1 / 10 T2 representative states and the shared source-only implementation audit index before product source or SDK output existed.',
      'acceptance_conjunction':'Unchanged frozen runtime acceptance AND separately source-bound shared implementation audit. Neither gate can mask a failure or unknown in the other.',
      'no_product_source_access':True,'no_native_execution':True,'no_product_implementation':True,
      'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(dest/'approval.json',approval)
    for case in cases:
        f=load(dest/'cases'/case/'fixtures.json')
        for p in ['ios','android']:
            out=dest/'compiled'/case/p;out.mkdir(parents=True)
            plan,derived=dc.compile_contract(lock,locksha,case,p,bindings,load(dest/'cases'/case/f'actions.{p}.json'))
            put(out/'plan.json',plan);put(out/'actions.json',derived)
            coverage=rr.audit(lock,locksha,plan,routefile,dc.digest(routefile));put(out/'coverage.json',coverage)
            assert not coverage['must_route_gaps'] and not coverage['unowned_assertions']
            b=dest/('Bridge.swift' if p=='ios' else 'ObserverBridge.kt')
            execution=ep.compile_execution(plan,lock,locksha,f,sha(b),launch_ref={'source':'reference','pointer':f'/launch/{case}/{p}'})
            put(out/'execution.json',execution);put(out/'execution-inputs'/'actions.json',execution['actions']);put(out/'execution-inputs'/'fixtures.json',execution['config'])
            ep.verify_execution(execution,plan,lock,locksha,f,sha(b))
            cat=rc.catalog(plan,lock,locksha,policy,dc.digest(policy),p);put(out/'review-catalog.json',dict(cat,catalog_sha256=dc.digest(cat)))
            OPERATIONS.append({'task':task,'scope':scope,'case':case,'platform':p,'states':len(states),'actions':len(execution['actions']),
             'assertions':len(plan['assertions']),'matrix_cells':len(plan['matrix_contract']['cells']),
             'runtime_must_route_gaps':coverage['must_route_gaps'],'source_only_must_audits':len(reference['implementation_audits']),
             'lock_canonical_sha256':locksha,'native_execution':False})
        render_reference(dest,task,case,reference['cases'][case],f)
    for ext in ['svg','png']:shutil.copyfile(dest/'references'/cases[0]/('permitted.'+ext),dest/('reference.'+ext))
    write(dest/'COLLECTION.md',collection(task,scope))
    put(dest/'SEAL.json',{'files':{str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='SEAL.json'}})

def collection(task,scope):
    return f'''# Revision 2 collection and release gates

This {task}/{scope} proposal retains the original caller values and bridge bytes. The expanded state plan and source-only audit gate were prospectively approved by root before any product implementation or SDK output. The original four-state helper must not be bypassed; root will record its protocol amendment and use a separate mechanical verifier. Frozen candidate-v9 runtime tools, evaluator and metrics remain unchanged.

Use the actual frozen `execution_plan.py` with each independently compiled scenario, the original case fixtures, exact bridge, lock/launch/policy/environment approvals and explicit production source roots. `compiled/<case>/<platform>/execution.json` retains the complete approved action route; its execution-inputs are derived runtime transport, not replacement launch approval. Native runs require a new evidence directory. Every full state has fresh overlapping coverage; target states retain only their declared native/control/event and target-wrapping requirements. A target state never supplies full-page absence or complete content proof. Event rules are explicitly action-indexed through the independently fixed stimulus_action; disclosure silence is bound to each real open/close action, choice reverse/restored/held intervals are separate, and update quietness binds actual successful same-process updates.

The new status Text semantic node and real band must occur fully visible in one coherent frame for the >=16 native-unit leading-inset measurement. It is inset_left for public LTR and inset_right for private RTL, with no implicit tolerance or computed-padding claim. The whole logical leading 4% pixel strip is separately sampled with support 1.0; all color expectations remain opaque and source-backed. Static reference images illustrate natural wrapping, including the formerly overflowing P2 status. They are never native measurements or cross-platform pixel oracles.

All source-only MUSTs live in the SAME sealed reference/lock at `/implementation_audits`. `implementation-audit.json` is the approved index pointer; approval pins its canonical digest. The shared generic sidecar will derive source expectations/provenance and require reviewer actuals bound to exact final production SHA plus file/line evidence. Missing, false, uncertain, foreign-source, or incomplete audits block complete release. It is a mandatory conjunct with unchanged frozen runtime acceptance, and applies identically to both arms. It cannot stand in for rendered spacing, colors, fonts, native dispatch, update receipt, or full content. The source-only audit implementation belongs to root's shared infrastructure; no fake runtime style rule was created for it.

Native semantic allocation, real dispatch, full sweep reachability, pixel eligibility, source audit results and independent visual agreement remain unverified. This document and successful static compilation are not product acceptance.
'''

def report_closure():
    r1=load(REVIEWS/'T1'/'review.json');r2=load(REVIEWS/'T2'/'review.json')
    dispositions={
      'T1-R1':'cleared targeted state binds reverse acknowledgement false; restored binds the subsequent true callback and resulting state.',
      'T1-R2':'held-choice activates acknowledgement on each original seal/coolant held replacement (P1/P2; H1 both); hold status and disabled primary are independently expected.',
      'T1-R3':'opened and requested-closed have actual native disclosure quiet intervals; disclosure-enabled is checked, post-request close is activated, and closed headings/bodies are separate propositions.',
      'T1-R4':'All eight text roles have independent wrapping atoms; individual compact roles use actual target frames and expanded roles use full sweeps.',
      'T1-R5':'full-width-canvas visual MUST; real status Text/band leading inset >=16 runtime geometry; full leading 4% clear native pixels; no nested scroller/artificial spacer rows remain source-only MUSTs.',
      'T1-R6':'Acknowledgement obligation names only acknowledgement; no unrelated Wi-Fi alternative remains.',
      'T2-R1':'opened and requested-closed have successful disclosure quiet intervals, full same-model close proof for headings/bodies, and disclosure remains enabled after request.',
      'T2-R2':'Original caller records stay unchanged; a separately appended caller fixture activates insufficient storage plus metered Wi-Fi-only, with targeted status/disabled and successful quiet update checks.',
      'T2-R3':'Title/subtitle/status/disclosure/choice/primary/heading/body wrapping are distinct source-backed atoms.',
      'T2-R4':'Actual status Text semantic boundary compared with real painted band via leading >=16 geometry; LTR left / RTL right; whole leading strip is separately sampled.',
      'T2-R5':'Separately source-backed per-platform audit MUSTs cover caller disk values/no capacity measurement, no audio fetch, parent scrolling, no manufactured blank rows, production state/reset and API ownership. Runtime acceptance is conjunctive with this shared sidecar.',
      'T2-R6':'Static reference status is wrapped inside cw-32, band height grows to its text, SVG/PNG generated from the same line records; no native font result claimed.'}
    rows=[]
    for report in [r1,r2]:
        for issue in report['issues']:rows.append({'id':issue['id'],'original_review_sha256':sha(REVIEWS/report['task']/'review.json'),
             'original_issue':copy.deepcopy(issue),'revision_response':dispositions[issue['id']],
             'status':'proposed_route_added_pending_independent_feasibility_review','native_result':None})
    return {'version':2,'issues':rows,'whole_brief_recheck':[
       'Retained original public APIs, callbacks, model values, guards, local reset and disabled semantics.',
       'Added reverse preference checks to T2 as well as T1, beyond the minimum enumerated T2 blockers.',
       'Separated flow order from single-column hierarchy; separate closed heading/body absence.',
       'Added source-only per-platform clauses for generic data rendering, native control ownership, callback/reset logic and observer-scenario independence.',
       'Preserved original advisory typography/internal allocation scope; rendered status inset and whole leading strip remain actual runtime MUSTs.',
       'Native state sampling limits and provider-specific extra scans remain explicit; no runtime or source-audit pass is claimed.']}

OPERATIONS=[];STATIC_REFERENCES=[]
if __name__=='__main__':
    try:
        for task in ['T1','T2']:
            for scope in ['public','private']:bundle(task,scope)
        put(ROOT/'design-logs'/'revision-closure.json',report_closure())
        put(ROOT/'design-logs'/'compiler-results.json',OPERATIONS)
        put(ROOT/'design-logs'/'static-reference-records.json',STATIC_REFERENCES)
        put(ROOT/'design-logs'/'protocol-amendment.json',{'version':2,'root_approved':True,'approved_before_implementation':True,
          'state_counts':{'T1':9,'T2':10},'actions_below_40':True,'original_values_retained':True,
          'source_only_gate':'Separate per-platform implementation_audits index in same sealed reference/lock; canonical implementation-audit digest in approval; shared source-bound sidecar AND unchanged runtime acceptance.',
          'frozen_runtime_tools_changed':False,'metrics_changed':False,'native_execution':False,'product_source_access':False,
          'new_mechanical_verifier':'Root will provide an explicit amended verifier; the old four-state helper is not silently bypassed.'})
        write(ROOT/'README.md','''# Independent prospective design revision 2

T1 retains ColdStorageTransferPanel; T2 retains OfflineAudioTourPanel. Original v1 proposal and official source-pinned reviews remain immutable under design-proposals/v1. No existing initial/update caller values, bridge APIs, business guards, callback or disabled/reset intent was weakened. All review issues have proposed new runtime or separately source-only routes, awaiting fresh independent feasibility review.

Root explicitly approved 9 T1 / 10 T2 representative states and a shared generic source-audit gate before any implementation/native output. Four original full states remain, with an additional full same-model disclosure-close state and targeted transition checkpoints. T2 appends a competing-gates caller fixture without mutating either original caller record. The original helper must not be silently bypassed; the explicit protocol amendment and separate root mechanical verifier apply. Frozen candidate-v9 runtime tools, evaluator and metrics are unchanged.

Every bundle contains exact production API paths, byte-identical thin bridges, fixed references and all public/private fixtures, contracts, source-only audit indexes, locks, policies, routes, launch/environment approvals, generated plans/actions/coverage/execution manifests/catalogs and seals. Source-only MUSTs are separately indexed at reference.json /implementation_audits in the same sealed source/lock. They remain a required release conjunct. No rendered or native behavior is proven from source alone.

Do not expose private fixtures or design-logs (which retain private inputs) to builders. No product source, implementation, SDK execution, native render, other cases, or outcomes were accessed. Static reconstruction is not feasibility or product acceptance. Previous unsuccessful authoring attempts and all v1 approvals are retained in the immutable archive; new unsuccessful revisions will be preserved in design-logs.
''')
        put(ROOT/'DESIGN-SEAL.json',{'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='DESIGN-SEAL.json'},
          'no_product_source_access':True,'no_native_execution':True,'no_product_implementation':True,
          'status':'sealed_independent_revision_2_pending_fresh_feasibility_review'})
        print(json.dumps({'status':'sealed_revision_2','compiled_pairs':len(OPERATIONS),'states':{'T1':9,'T2':10},'root':str(ROOT)}))
    except Exception:
        attempt=ROOT/'design-logs'/('unsuccessful-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
        attempt.mkdir(parents=True,exist_ok=True)
        for task in ['T1','T2']:
            if (ROOT/task).exists():shutil.copytree(ROOT/task,attempt/task)
        shutil.copyfile(__file__,attempt/'revise_design.py');write(attempt/'traceback.txt',traceback.format_exc());put(attempt/'operations.json',OPERATIONS)
        raise
