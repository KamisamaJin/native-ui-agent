#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys,time
R=Path(__file__).resolve().parent
S=R.parents[2]/'native-ui-agent/scripts'
sys.path.insert(0,str(S))
import design_contract as d
import requirement_routes as routes
import review_contract as review
import execution_plan as xp

def save(name,obj):
    p=R/name
    with p.open('x') as f:f.write(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def anchor(pointer):return {'source':'reference','pointer':pointer}
def cell(pointer):return {pl:anchor(pointer) for pl in ['ios','android']}
fixtures={'initial':{'side':'front'},'updates':[{'side':'reverse'}],'width':360,'theme':'light','dynamic_type':'large','direction':'ltr','canvas_color':'#FFFFFF','max_scrolls':4,'required_identifiers':['fold.heading','fold.diagram','fold.instruction','fold.status','fold.action']}
bindings={v:{'identifier':'fold.'+v}for v in ['heading','diagram','instruction','status','action']}
bindings['action']['role']='button'
base=[{'type':'checkpoint','state_id':'overview'},{'type':'tap','target':bindings['action'],'reveal':True,'state_id':'creased'},{'type':'apply_next_fixture','state_id':'reversed'}]
states=[{'id':v,'input_index':int(v=='reversed'),'after_action':i,'coverage':'full_content'}for i,v in enumerate(['overview','creased','reversed'])]
rules=[{'id':'heading-label','kind':'control','target':'heading','property':'label'},
       {'id':'instruction-label','kind':'control','target':'instruction','property':'label'},
       {'id':'status-label','kind':'control','target':'status','property':'label'},
       {'id':'diagram-width','kind':'geometry','target':'diagram','property':'width','measurement':'accessibility_box'},
       {'id':'diagram-height','kind':'geometry','target':'diagram','property':'height','measurement':'accessibility_box'},
       {'id':'action-height','kind':'geometry','target':'action','property':'height','measurement':'accessibility_box'},
       {'id':'action-enabled','kind':'control','target':'action','property':'enabled'},
       {'id':'crease-event','kind':'event','stimulus':'activation'},
       {'id':'diagram-content','kind':'manual','target':'diagram','property':'content_presence','coverage':'full_content','allowed_methods':['visual']},
       {'id':'instruction-clear','kind':'manual','target':'instruction','property':'overlap','coverage':'full_content','allowed_methods':['visual']}]
ref={'heading':{'value':'Fold guide','unit':'string'},'instructions':{'front':{'value':'Fold the front sheet along the dashed diagonal.','unit':'string'},'reverse':{'value':'Turn the sheet. Fold along the reverse diagonal.','unit':'string'}},
     'status':{v:{'value':t,'unit':'string'}for v,t in zip(['overview','creased','reversed'],['Sheet ready','Crease marked','Reverse side'])},
     'true':{'value':True,'unit':'bool'},'false':{'value':False,'unit':'bool'},'crease_event':{'value':['crease.marked'],'unit':'events'},
     'geometry':{'width':{'ios':{'value':180,'unit':'pt'},'android':{'value':180,'unit':'dp'}},'height':{'ios':{'value':100,'unit':'pt'},'android':{'value':100,'unit':'dp'}},'actionHeight':{'ios':{'value':44,'unit':'pt'},'android':{'value':44,'unit':'dp'}}},
     'questions':{'diagram':{'value':'Does the visible paper diagram show an upper-left to lower-right dashed crease in overview/creased, and an upper-right to lower-left dashed crease in reversed, with the paper outline visible?','unit':'string'},'instruction':{'value':'Is the instruction visibly clear of the heading, diagram, status and action?','unit':'string'}},
     'launch':{'fixtures_sha256':d.digest(fixtures),'bridge_sha256':hashlib.sha256((R/'FoldGuideBridge.swift').read_bytes()).hexdigest(),'scenario':'neutral','platform':'ios'}}
obligations=[{'id':'native-content','clause':'The title, instruction and status match the fixed per-state copy.','priority':'must','states':[s['id']for s in states],'risk':'content'},
             {'id':'native-bounds','clause':'The diagram AX bounds are 180 by 100pt and the action AX height is 44pt in every state.','priority':'must','states':[s['id']for s in states],'risk':'layout'},
             {'id':'interaction','clause':'Marking delivers one crease.marked callback and disables the action; caller replacement restores enabled reverse input.','priority':'must','states':[s['id']for s in states],'risk':'behavior'},
             {'id':'diagram','clause':'The crease diagonal follows the front/reverse state while retaining the paper outline.','priority':'must','states':[s['id']for s in states],'risk':'content'},
             {'id':'clarity','clause':'The instruction never overlaps other visible component content.','priority':'must','states':[s['id']for s in states],'risk':'layout'}]
ref['obligations']=obligations
save('reference.json',ref);save('fixtures.json',fixtures);save('bindings.json',bindings);save('actions.json',base)
values={}
for rule in rules:
    rid=rule['id'];values[rid]={}
    for state in states:
        sid=state['id']
        if rid=='heading-label':value=cell('/heading')
        elif rid=='instruction-label':value=cell('/instructions/'+('reverse'if sid=='reversed'else'front'))
        elif rid=='status-label':value=cell('/status/'+sid)
        elif rid in ['diagram-width','diagram-height','action-height']:
            key={'diagram-width':'width','diagram-height':'height','action-height':'actionHeight'}[rid]
            value={pl:anchor('/geometry/'+key+'/'+pl)for pl in ['ios','android']}
        elif rid=='action-enabled':value=cell('/false'if sid=='creased'else'/true')
        elif rid=='crease-event':value=cell('/crease_event')if sid=='creased'else{'not_applicable':'No activation stimulus at this checkpoint.'}
        else:value=cell('/true')
        values[rid][sid]=value
contract={'version':1,'design_owner':'Independent neutral benchmark author r11_neutral_benchmark','approval_reference':'SPECIFICATION.md fixed before any SDK execution; seal.json binds this author decision','sources':[{'id':'reference','path':'reference.json','sha256':hashlib.sha256((R/'reference.json').read_bytes()).hexdigest()}],'required_rule_ids':[r['id']for r in rules],'rules':rules,'scenarios':{'neutral':{'states':states,'actions':[dict(a,target='action')if a['type']=='tap'else a for a in base],'values':values}}}
save('contract.json',contract)
lock=d.seal(R/'contract.json',R);lsha=d.digest(lock);save('lock.json',lock)
plan,actions=d.compile_contract(lock,lsha,'neutral','ios',bindings,base);save('plan.ios.json',plan);save('compiled-actions.ios.json',actions)
policy={'version':1,'design_lock_sha256':lsha,'approval_reference':'Independent benchmark pre-SDK visual atom approval','ownership':{'diagram':'component','instruction':'component'},'atoms':[{'rule_id':'diagram-content','aspect':'content_presence','method':'visual','question':anchor('/questions/diagram')},{'rule_id':'instruction-clear','aspect':'overlap','method':'visual','question':anchor('/questions/instruction')}]}
save('policy.json',policy);psha=d.digest(policy)
cat=review.catalog(plan,lock,lsha,policy,psha,'ios');save('catalog.ios.json',cat)
mapping={'native-content':['heading-label','instruction-label','status-label'],'native-bounds':['diagram-width','diagram-height','action-height'],'interaction':['action-enabled','crease-event'],'diagram':['diagram-content'],'clarity':['instruction-clear']}
route={'version':1,'index':anchor('/obligations'),'routes':{oid:{'rule_ids':ids,'reason':'Exact original native facts or independent image proposition cover this fixed obligation.','regression_obligations':[]}for oid,ids in mapping.items()}}
save('routes.json',route);rsha=d.digest(route)
cov=routes.audit(lock,lsha,plan,route,rsha);save('coverage.json',cov)
assert not cov['must_route_gaps'] and not cov['unowned_assertions']
env={'width':360,'height':600,'direction':'ltr','theme':'light','dynamic_type':'large'};save('environment.ios.json',env)
execution=xp.compile_execution(plan,lock,lsha,fixtures,ref['launch']['bridge_sha256'],launch_ref=anchor('/launch'));save('execution.ios.json',execution)
approval={'version':1,'approvedAtUnix':time.time(),'design_sha256':lsha,'policy_sha256':psha,'routes_sha256':rsha,'environment_sha256':d.digest(env),'plan_sha256':d.digest(plan),'required_cells':len(plan['required_assertion_ids']),'not_applicable_cells':len(plan['matrix_contract']['cells'])-len(plan['required_assertion_ids']),'visual_cells':len(cat['rows']),'source':'Independent fixed neutral spec; no SDK execution; no injected defects'}
save('approval.json',approval)
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(R.iterdir())if p.is_file()}
save('seal.json',{'version':1,'sealedAtUnix':time.time(),'files':files,'scope':'All benchmark source/design inputs sealed before SDK collection.'})
print(json.dumps(approval,indent=2))
