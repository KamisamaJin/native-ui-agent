import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path('skill/scripts').resolve()))
from state_plan import compile_matrix
root=Path('.')
cases=json.loads(Path('brief/cases.json').read_text())['cases']

def facts(model,sel,mode,priority,expanded):
    jobs=model['jobs']; chosen=[j for j in jobs if j['id'] in sel]
    ink=sum(j['pages']*j['copies']*(3 if j['isColor'] else 1) for j in chosen)
    sheets=sum((j['pages'] if mode=='single' else (j['pages']+1)//2)*j['copies'] for j in chosen)
    surcharge=6 if chosen and priority else 0; total=ink+sheets+surcharge;n=len(chosen);budget=model['budgetCredits']
    texts={'title':'Print budget check','status':'No jobs' if not n else 'Over budget' if total>budget else 'Ready','charge.caption':'Estimated charge','charge.value':f'{total} cr','summary':f'{n} jobs • {sum(j["pages"]*j["copies"] for j in chosen)} pages • {sheets} sheets','mode.title':'Paper mode','mode.single':'Single-sided','mode.duplex':'Duplex','priority':'Priority handling','priority.helper':'Priority unavailable for this batch.' if not model['allowPriority'] else 'Adds 6 cr to this batch.' if priority else 'Add 6 cr for priority handling.','breakdown.toggle':'Hide cost breakdown' if expanded else 'Show cost breakdown','balance':'No charge selected' if not n else f'Short by {total-budget} cr' if total>budget else f'Balance after approval: {budget-total} cr','approve':'Select a job to approve' if not n else f'Over budget by {total-budget} cr' if total>budget else f'Approve {n} jobs · {total} cr'}
    enabled={'mode.single':True,'mode.duplex':True,'priority':model['allowPriority'] and n>0,'breakdown.toggle':True,'approve':n>0 and total<=budget}
    selected={'mode.single':mode=='single','mode.duplex':mode=='duplex'}
    for j in jobs:
        p=f'job.{j["id"]}';s=j['id'] in sel
        texts[p+'.toggle']=('Deselect ' if s else 'Select ')+j['title'];texts[p+'.title']=j['title'];texts[p+'.subtitle']=f'{j["pages"]} pages × {j["copies"]} copies • '+('Color' if j['isColor'] else 'Mono')+(' • Locked' if j['locked'] else '')
        texts[p+'.price']=f'{j["pages"]*j["copies"]*(3 if j["isColor"] else 1)+(j["pages"] if mode=="single" else (j["pages"]+1)//2)*j["copies"]} cr';enabled[p+'.toggle']=not j['locked'];selected[p+'.toggle']=s
    detail={}
    for key,value in [('ink',ink),('paper',sheets),('priority',surcharge),('total',total)]:
        detail[f'breakdown.{key}.label']=key.title();detail[f'breakdown.{key}.value']=f'{value} cr'
    if expanded:texts.update(detail)
    approval={'name':'approve','payload':{'modelID':model['modelID'],'jobIDs':[j['id'] for j in chosen],'paperMode':mode,'priority':priority,'totalCredits':total,'printedPages':sum(j['pages']*j['copies'] for j in chosen),'sheets':sheets}}
    return texts,enabled,selected,detail,approval

for case in cases:
    cid=case['caseID'];folder=Path('agent-output/review-plan')/cid;folder.mkdir(parents=True,exist_ok=True)
    mapping=json.loads((Path('native-inputs')/cid/'mapping.json').read_text());actions=json.loads((Path('native-inputs')/cid/'actions.json').read_text());fixtures=json.loads((Path('native-inputs')/cid/'fixtures.json').read_text())
    model=copy.deepcopy(case['models'][0]);sel={j['id'] for j in model['jobs'] if j['selected']};mode=model['initialPaperMode'];priority=model['initialPriority'];expanded=model['initialExpanded'];rows=[]
    for logical in range(len(case['actions'])+1):
        event=[];stimulus='activation'
        if logical:
            action=case['actions'][logical-1];target=action.get('targetID','');before=facts(model,sel,mode,priority,expanded)
            if action['type']=='replaceModel':
                model=copy.deepcopy(case['models'][action['modelIndex']]);sel={j['id'] for j in model['jobs'] if j['selected']};mode=model['initialPaperMode'];priority=model['initialPriority'];expanded=model['initialExpanded'];stimulus='caller_update'
            elif target.startswith('printbatch.job.'):
                jid=target.split('.')[2];j=next(j for j in model['jobs'] if j['id']==jid)
                if not j['locked']:
                    sel.symmetric_difference_update({jid});event=[{'name':'selectionChanged','payload':{'jobIDs':[j['id'] for j in model['jobs'] if j['id'] in sel]}}]
            elif target.startswith('printbatch.mode.'):
                new=target.split('.')[-1]
                if mode!=new:mode=new;event=[{'name':'paperModeChanged','payload':{'paperMode':mode}}]
            elif target=='printbatch.priority' and before[1]['priority']:
                priority=not priority;event=[{'name':'priorityChanged','payload':{'priority':priority}}]
            elif target=='printbatch.breakdown.toggle':
                expanded=not expanded;event=[{'name':'breakdownChanged','payload':{'expanded':expanded}}]
            elif target=='printbatch.approve' and before[1]['approve']:event=[before[4]]
        sid=f'{cid}.s{logical}';rows.append({'id':sid,'map':mapping[sid],'facts':facts(model,sel,mode,priority,expanded),'priority':priority,'expanded':expanded,'events':event,'stimulus':stimulus})
    for platform in ['ios','android']:
        states=[{'id':r['id'],'input_index':r['map']['input_index'],'after_action':r['map']['after_action'],'coverage':'full_content' if r['map']['full_content'] else 'targets',**({'stimulus_action':r['map']['trigger_action_index']} if r['map']['trigger_action_index'] is not None else {})} for r in rows]
        reqs=[]
        def add(rid,check,values,source='brief/BRIEF.md; brief/API.md'):
            reqs.append({'id':rid,'source':source,'check':check,'by_state':{r['id']:{'expected':values(r)} for r in rows}})
        alltexts=set().union(*(set(r['facts'][0])|set(r['facts'][3]) for r in rows))
        controls=set(rows[0]['facts'][1])
        for key in sorted(alltexts):
            target={'identifier':'printbatch.'+key};present=lambda r,k=key:k in r['facts'][0]
            add(key+'.present',{'kind':'control','target':target,'property':'present'},present)
            add(key+'.unique',{'kind':'control','target':target,'property':'unique'},present)
            req={'id':key+'.copy','source':'brief/BRIEF.md Exact visible copy; brief/API.md native IDs','check':{'kind':'control','target':target,'property':'label'},'by_state':{r['id']:{'expected':r['facts'][0][key]} for r in rows if key in r['facts'][0]},'not_applicable':{r['id']:'Collapsed breakdown has no text node; absence is checked separately.' for r in rows if key not in r['facts'][0]}};reqs.append(req)
            if key not in controls:
                for prop,val in [('font_sp', (20 if key=='title' else 28 if key=='charge.value' else 14 if key in ['summary','balance'] or key.endswith('.title') or key.endswith('.price') else 12)*case['host']['textScale']),('ellipsized',False),('overflow',False)]:
                    if platform=='android':
                        rr={'id':key+'.'+prop,'source':'brief/BRIEF.md Typography and no clipping','check':{'kind':'text_layout','target':target,'property':prop,'expected':val},'not_applicable':{r['id']:'Collapsed contents are absent.' for r in rows if key not in r['facts'][0]}};reqs.append(rr)
        if platform=='android':
            palette={'text':0xFFF2F5FA if case['host']['theme']=='dark' else 0xFF14243A,'muted':0xFFB7C4D5 if case['host']['theme']=='dark' else 0xFF53657A,'ready':0xFF75D6AA if case['host']['theme']=='dark' else 0xFF167650,'error':0xFFFF9A96 if case['host']['theme']=='dark' else 0xFFB63835}
            for key in sorted(alltexts-controls):
                overrides={}
                for r in rows:
                    if key not in r['facts'][0]:continue
                    label=r['facts'][0][key]
                    token=('muted' if label=='No jobs' else 'error' if label=='Over budget' else 'ready') if key=='status' else 'error' if key=='balance' and label.startswith('Short by ') else 'muted' if key in ['charge.caption','summary','priority.helper'] or key.endswith('.subtitle') or key.startswith('breakdown.') else 'text'
                    overrides[r['id']]={'expected':palette[token]}
                reqs.append({'id':key+'.color_argb','source':'brief/BRIEF.md exact palette','check':{'kind':'text_layout','target':{'identifier':'printbatch.'+key},'property':'color_argb'},'by_state':overrides,'not_applicable':{r['id']:'Collapsed contents are absent.' for r in rows if key not in r['facts'][0]}})
                weight=700 if key=='charge.value' else 600 if key in ['title','status','mode.title'] or key.startswith('job.') and key.endswith('.title') else 400
                reqs.append({'id':key+'.font_weight','source':'brief/BRIEF.md typography weights','check':{'kind':'text_layout','target':{'identifier':'printbatch.'+key},'property':'font_weight','expected':weight},'not_applicable':{r['id']:'Collapsed contents are absent.' for r in rows if key not in r['facts'][0]}})
            add('breakdown.expanded.native',{'kind':'control','target':{'identifier':'printbatch.breakdown.toggle'},'property':'expanded'},lambda r:r['expanded'],source='brief/API.md native expanded state; adapter does not export Compose stateDescription, so this aspect remains unknown unless actual native support is added.')
        for key in sorted(controls):
            target={'identifier':'printbatch.'+key};add(key+'.enabled',{'kind':'control','target':target,'property':'enabled'},lambda r,k=key:r['facts'][1][k]);add(key+'.role',{'kind':'control','target':target,'property':'control_role'},lambda r,k=key:'checkbox' if k.startswith('job.') and platform=='android' else 'switch' if k=='priority' else 'button')
            for prop in (['touch_width','touch_height'] if platform=='android' else ['ax_width','ax_height']):add(key+'.'+prop,{'kind':'control','target':target,'property':prop,'op':'gte'},lambda r:48,source='brief/BRIEF.md minimum semantic/action bounds. iOS AX does not establish physical hit bounds.')
        for key in rows[0]['facts'][2]:
            add(key+'.selected',{'kind':'control','target':{'identifier':'printbatch.'+key},'property':'selected'},lambda r,k=key:r['facts'][2][k])
        add('priority.on',{'kind':'control','target':{'identifier':'printbatch.priority'},'property':'value'},lambda r:r['priority'])
        if platform=='ios':add('breakdown.expanded',{'kind':'control','target':{'identifier':'printbatch.breakdown.toggle'},'property':'value'},lambda r:'Expanded' if r['expanded'] else 'Collapsed')
        eventreq={'id':'callback.delta','source':'brief/API.md exact callbacks; native disabled dispatch gate','check':{'kind':'event'},'by_state':{r['id']:{'expected':r['events'],'action_index':r['map']['trigger_action_index'],'stimulus':r['stimulus']} for r in rows if r['map']['trigger_action_index'] is not None},'not_applicable':{rows[0]['id']:'Initial rendering has no requested activation or caller replacement.'}};reqs.append(eventreq)
        for aspect,reason in [('layout','Order, association, full intrinsic content and no overlap; reference.svg'),('palette','Exact light/dark palette, state tints and subdued disabled surfaces; reference.svg'),('typography','System sans, relative hierarchy, all required text wraps and remains readable; reference.svg'),('geometry','16 inset/radius, section spacing12, row padding12, approval radius10; unsupported native SwiftUI padding must remain unknown'),('direction','Leading/trailing relationships, text readability and mirrored mode order under supplied direction'),('physical_hit_regions','Physical controls at least48, unobstructed; iOS AX frames cannot prove physical hit regions')]:
            reqs.append({'id':'visual.'+aspect,'source':'brief/BRIEF.md Visual and accessibility requirements; '+reason,'check':{'kind':'manual','allowed_methods':['visual','native_pixels'],'coverage':'full_content'}})
        matrix={'version':1,'states':states,'requirements':reqs,'required_state_ids':[s['id'] for s in states],'required_requirement_ids':[r['id'] for r in reqs]}
        plan,_=compile_matrix(matrix,None)
        enriched=copy.deepcopy(actions)
        for action in enriched:
            row=next((r for r in rows if r['id']==action['state_id']),None)
            if row and not row['map']['full_content']:
                omit={'title','charge.caption','mode.title'}|{f'breakdown.{k}.label' for k in ['ink','paper','priority','total']}
                targets=[{'identifier':'printbatch.'+k} for k in row['facts'][0] if k not in omit]
                action['after_targets']=targets[:32]
        (folder/f'matrix.{platform}.json').write_text(json.dumps(matrix,indent=2,ensure_ascii=False)+'\n');(folder/f'plan.{platform}.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n');(folder/f'actions.{platform}.json').write_text(json.dumps(enriched,indent=2,ensure_ascii=False)+'\n')
    print(cid,len(rows),'states; plans frozen before source implementation')
