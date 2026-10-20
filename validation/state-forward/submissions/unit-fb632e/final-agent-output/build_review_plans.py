"""Independent public-requirements plan; no capture or implementation data is read."""
import copy, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT/'brief/cases.json').read_text())['cases']
SOURCE = 'brief/BRIEF.md; brief/API.md; brief/reference.svg'
def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
def totals(model,state):
    jobs=[j for j in model['jobs'] if j['id'] in state['selected']]
    sheets=lambda j: ((j['pages']+1)//2 if state['mode']=='duplex' else j['pages'])*j['copies']
    ink=lambda j:j['pages']*j['copies']*(3 if j['isColor'] else 1)
    pages=sum(j['pages']*j['copies'] for j in jobs)
    paper=sum(map(sheets,jobs));ink_total=sum(map(ink,jobs));surcharge=6 if jobs and state['priority'] else 0
    total=paper+ink_total+surcharge
    return dict(jobs=jobs,pages=pages,sheets=paper,ink=ink_total,surcharge=surcharge,total=total,row_prices={j['id']:ink(j)+sheets(j) for j in model['jobs']})
def initial(m):return dict(selected={j['id'] for j in m['jobs'] if j['selected']},mode=m['initialPaperMode'],priority=m['initialPriority'],expanded=m['initialExpanded'])
def apply(m,s,a):
    t=totals(m,s);target=a.get('targetID','');event=[]
    if target.startswith('printbatch.job.'):
        j=next(j for j in m['jobs'] if target==f"printbatch.job.{j['id']}.toggle")
        if not j['locked']:
            s['selected'].symmetric_difference_update({j['id']});event=[dict(name='selectionChanged',payload=dict(jobIDs=[j['id'] for j in m['jobs'] if j['id'] in s['selected']]))]
    elif target.startswith('printbatch.mode.'):
        mode=target.rsplit('.',1)[1]
        if mode!=s['mode']:s['mode']=mode;event=[dict(name='paperModeChanged',payload=dict(paperMode=mode))]
    elif target=='printbatch.priority' and m['allowPriority'] and t['jobs']:
        s['priority']=not s['priority'];event=[dict(name='priorityChanged',payload=dict(priority=s['priority']))]
    elif target=='printbatch.breakdown.toggle':
        s['expanded']=not s['expanded'];event=[dict(name='breakdownChanged',payload=dict(expanded=s['expanded']))]
    elif target=='printbatch.approve' and t['jobs'] and t['total']<=m['budgetCredits']:
        event=[dict(name='approve',payload=dict(modelID=m['modelID'],jobIDs=[j['id'] for j in t['jobs']],paperMode=s['mode'],priority=s['priority'],totalCredits=t['total'],printedPages=t['pages'],sheets=t['sheets']))]
    return event
matrix=[]
for case in CASES:
    cid=case['caseID'];out=ROOT/'agent-output/review-plan'/cid
    mapping=json.loads((ROOT/f'native-inputs/{cid}/mapping.json').read_text())
    actions=json.loads((ROOT/f'native-inputs/{cid}/actions.json').read_text())
    # Only observation destinations change; fixed activation routes and state IDs remain exact.
    for action in actions:
        if action['type']=='tap':
            target=action['target']['identifier']
            if target.startswith('printbatch.mode.') or target.startswith('printbatch.job.'):
                action['after_target']={'identifier':'printbatch.charge.value'}
    write(out/'actions.json',actions)
    m=case['models'][0];s=initial(m);checkpoints=[]
    checkpoints.append((case['initial']['stateID'],copy.deepcopy(m),copy.deepcopy(s),None,[]))
    for action in case['actions']:
        if action['type']=='replaceModel':m=case['models'][action['modelIndex']];s=initial(m);events=[]
        else:events=apply(m,s,action)
        checkpoints.append((action['stateID'],copy.deepcopy(m),copy.deepcopy(s),action,events))
    for platform in ['ios','android']:
        plan={'version':1,'caseID':cid,'platform':platform,'expectation_source':SOURCE,'states':[],'required_assertion_ids':[],'assertions':[],
              'limits':['Full sweeps are the fixed two public checkpoints only. Missing target evidence is unassessed, not passed.','Disabled observer activations can establish disabled state but cannot establish exercised handler behavior.','SwiftUI AX frames do not measure physical hit regions, font sizes, padding or colors.','Manual visual judgments compare independent reference intent, not incidental y positions or renderer font rasterization.']}
        for sid,model,state,action,events in checkpoints:
            mp=mapping[sid];scope='full_content' if mp['full_content'] else 'target'
            plan['states'].append({'id':sid,'input_index':mp['input_index'],'after_action':mp['after_action'],'coverage':scope})
            t=totals(model,state);count=len(t['jobs']);over=t['total']>model['budgetCredits'];can=count>0 and not over
            status='No jobs' if count==0 else 'Over budget' if over else 'Ready'
            def add(key,kind,**kw):
                row=dict(id=f'{sid}.{key}',state=sid,kind=kind,coverage=scope,source=SOURCE,**kw)
                plan['assertions'].append(row);plan['required_assertion_ids'].append(row['id'])
            def prop(key,target,property,expected,**kw):add(key,'control',target={'identifier':target},property=property,expected=expected,**kw)
            def text(target,expected):
                prop(target.removeprefix('printbatch.')+'.text',target,'label',expected)
                prop(target.removeprefix('printbatch.')+'.unique',target,'unique',True)
            texts={
                'printbatch.title':'Print budget check','printbatch.status':status,'printbatch.charge.caption':'Estimated charge',
                'printbatch.charge.value':f"{t['total']} cr",'printbatch.summary':f"{count} jobs • {t['pages']} pages • {t['sheets']} sheets",
                'printbatch.mode.title':'Paper mode',
                'printbatch.priority.helper':'Priority unavailable for this batch.' if not model['allowPriority'] else 'Adds 6 cr to this batch.' if state['priority'] else 'Add 6 cr for priority handling.',
                'printbatch.balance':'No charge selected' if not count else f"Short by {t['total']-model['budgetCredits']} cr" if over else f"Balance after approval: {model['budgetCredits']-t['total']} cr",
                'printbatch.approve':'Select a job to approve' if not count else f"Over budget by {t['total']-model['budgetCredits']} cr" if over else f"Approve {count} jobs · {t['total']} cr",
                'printbatch.breakdown.toggle':'Hide cost breakdown' if state['expanded'] else 'Show cost breakdown'}
            for j in model['jobs']:
                base=f"printbatch.job.{j['id']}"
                texts[base+'.title']=j['title']
                texts[base+'.subtitle']=f"{j['pages']} pages × {j['copies']} copies • {'Color' if j['isColor'] else 'Mono'}"+(' • Locked' if j['locked'] else '')
                texts[base+'.price']=f"{t['row_prices'][j['id']]} cr"
                texts[base+'.toggle']=f"{'Deselect' if j['id'] in state['selected'] else 'Select'} {j['title']}"
                prop(base+'.enabled',base+'.toggle','enabled',not j['locked'])
                prop(base+'.selection',base+'.toggle','value',('Selected' if j['id'] in state['selected'] else 'Not selected') if platform=='ios' else j['id'] in state['selected'])
                prop(base+'.role',base+'.toggle','control_role','button' if platform=='ios' else 'checkbox')
            for mode,title in [('single','Single-sided'),('duplex','Duplex')]:
                target='printbatch.mode.'+mode;texts[target]=title
                prop('mode.'+mode+'.enabled',target,'enabled',True)
                prop('mode.'+mode+'.selected',target,'selected',state['mode']==mode)
                prop('mode.'+mode+'.role',target,'control_role','button')
            texts['printbatch.priority']='Priority handling'
            prop('priority.enabled','printbatch.priority','enabled',model['allowPriority'] and count>0)
            prop('priority.value','printbatch.priority','value',state['priority'])
            prop('priority.role','printbatch.priority','control_role','switch')
            prop('breakdown.enabled','printbatch.breakdown.toggle','enabled',True)
            prop('approve.enabled','printbatch.approve','enabled',can)
            prop('approve.role','printbatch.approve','control_role','button')
            if platform=='ios':prop('breakdown.expanded','printbatch.breakdown.toggle','value','Expanded' if state['expanded'] else 'Collapsed')
            else:add('breakdown.expanded','text_layout',target={'identifier':'printbatch.breakdown.toggle'},property='state_description',expected='Expanded' if state['expanded'] else 'Collapsed',capability_note='Production Compose stateDescription is native; supplied observer does not export it. Preserve unassessed.')
            for key,title,value in [('ink','Ink',t['ink']),('paper','Paper',t['sheets']),('priority','Priority',t['surcharge']),('total','Total',t['total'])]:
                for suffix,value_ in [('label',title),('value',f'{value} cr')]:
                    target=f'printbatch.breakdown.{key}.{suffix}'
                    if state['expanded']:texts[target]=value_
                    else:prop('breakdown.'+key+'.'+suffix+'.absent',target,'present',False)
            for target,expected in texts.items():text(target,expected)
            # Exact scalar text metrics use exported native Compose TextLayoutResult only.
            if platform=='android':
                dark=case['host']['theme']=='dark';scale=case['host']['textScale']
                color={'text':0xFFF2F5FA if dark else 0xFF14243A,'muted':0xFFB7C4D5 if dark else 0xFF53657A,'accent':0xFF8BB0FF if dark else 0xFF265FE4,'ready':0xFF75D6AA if dark else 0xFF167650,'error':0xFFFF9A96 if dark else 0xFFB63835}
                for target in texts:
                    if target.endswith('.toggle') or target in ['printbatch.priority','printbatch.approve','printbatch.mode.single','printbatch.mode.duplex']:continue
                    size=20 if target=='printbatch.title' else 28 if target=='printbatch.charge.value' else 12 if any(q in target for q in ['status','caption','summary','helper','subtitle','breakdown.']) else 14
                    weight=600 if target in ['printbatch.title','printbatch.status'] or target.endswith('.title') or target=='printbatch.balance' else 700 if target=='printbatch.charge.value' else 400
                    ink='muted' if any(q in target for q in ['caption','summary','helper','subtitle','breakdown.']) else 'error' if target=='printbatch.balance' and over and count else 'text'
                    if target=='printbatch.status':ink='muted' if not count else 'error' if over else 'ready'
                    for property,value in [('font_sp',size*scale),('font_weight',weight),('color_argb',color[ink]),('ellipsized',False),('overflow',False)]:
                        add(target.removeprefix('printbatch.')+'.'+property,'text_layout',target={'identifier':target},property=property,expected=value)
            controls=[f"printbatch.job.{j['id']}.toggle" for j in model['jobs']]+['printbatch.mode.single','printbatch.mode.duplex','printbatch.priority','printbatch.breakdown.toggle','printbatch.approve']
            for target in controls:
                for dimension in ['width','height']:
                    prop(target.removeprefix('printbatch.')+'.minimum-'+dimension,target,('touch_' if platform=='android' else 'ax_')+dimension,48,op='gte')
            if action:
                add('callback','event',action_index=mp['trigger_action_index'],expected=events,stimulus='caller_update' if action['type']=='replaceModel' else 'activation',required_method='caller_fixture_update' if action['type']=='replaceModel' else 'xcui_tap' if platform=='ios' else 'compose_onclick')
            # Each independent aspect remains in the denominator at every checkpoint.
            manual={
              'visual-hierarchy':'Title/status, charge/summary, jobs, mode, priority, breakdown, balance, approval retain specified vertical order; title20 and charge28 have distinct visual hierarchy.',
              'visual-palette':'Match theme surface/text/muted/accent/ready/error palettes. Badge and shortfall use their status colors; selected mode and approval use accent with required contrasting foreground.',
              'visual-wrap':'Read every required label and value; long content expands, wraps and stays associated. No clipping, truncation or overlap at supplied width/textScale.',
              'visual-state':'Visible job checks, selected mode, priority persisted choice, disabled surfaces/labels and breakdown state match expected checkpoint state.',
              'visual-layout':'Card radius16, internal padding16, section spacing12, job vertical padding12, separator muted25%, approval radius10 and full inner width match reference intent.',
              'visual-direction':'Leading/trailing relationships and mode order mirror for RTL, including title/badge and job selection/text/price. English words and numbers remain readable.',
              'visual-scroll':'Native parent scroller provides bounded overlapping evidence to actual content bottom for this state; no nested component vertical scroller or unreachable footer.',
              'physical-hit-region':'Physical touch region is separate from AX bounds. Verify actual native action target/hit evidence for this state; offscreen or unmeasured controls remain unassessed.'}
            for key,description in manual.items():add(key,'manual',allowed_methods=['visual','native_pixels'],description=description,expected_state=dict(modelID=model['modelID'],selected=[j['id'] for j in t['jobs']],paperMode=state['mode'],priority=state['priority'],expanded=state['expanded'],total=t['total']))
            if platform=='ios':
                for aspect in ['font-tokens','padding-radius-separators']:
                    add('unsupported-exact-'+aspect,'manual',allowed_methods=['visual','native_pixels'],description='Exact SwiftUI '+aspect+' is not exported by public AX. Visual intent may be inspected separately; exact numeric values stay unassessed unless independently measured native pixel evidence supports them.')
            matrix.append({'case':cid,'platform':platform,'state':sid,'input_index':mp['input_index'],'after_action':mp['after_action'],'scope':scope,'assertions':len([a for a in plan['assertions'] if a['state']==sid]),'expected_total':t['total'],'expected_pages':t['pages'],'expected_sheets':t['sheets'],'action_event':events})
        write(out/f'plan.{platform}.json',plan)
write(ROOT/'agent-output/review-plan/requirements-matrix.json',{'source':SOURCE,'records':matrix,'capability_limits':['No implementation screenshot or native product observation informed these expectations.','Full-content acceptance at target-only checkpoints remains represented but not claimed covered.','Callback assertions for disabled controls deliberately remain unassessed when observer blocks native dispatch.']})
