import pathlib,json,hashlib,datetime
P=pathlib.Path(__file__).resolve().parent
(P/'design').mkdir(exist_ok=True)
def dump(p,v): p.write_text(json.dumps(v,indent=2)+'\n')
def t(v,u):return {'value':v,'unit':u}
ref={'intent':t('Reading Notes uses a pale canvas, clear heading hierarchy, two blue markers separated by 12 native units, readable untruncated rows, and a readable far footer. Opening notes changes status, preserves the list, and emits one notes.open event. Replacing caller data preserves local open state and emits no callback.','string'),'heading':{'A':t('Reading set A','string'),'B':t('Reading set B','string')},'status':{'closed':t('Notes closed','string'),'open':t('Notes open','string')},'footer':{'A':t('End of reading set A','string'),'B':t('End of reading set B','string')},'geometry':{p:{'width':t(72,u),'gap':t(12,u),'tolerance':t(0.75,u)}for p,u in [('ios','pt'),('android','dp')]},'style':{'ink':t('#FF204B6D','argb'),'font':t(16,'sp')},'events':{'open':t(['notes.open'],'events'),'quiet':t([],'events')}}
dump(P/'design/reference.json',ref)
rules=[{'id':'heading','kind':'control','target':'heading','property':'label'},{'id':'status','kind':'control','target':'status','property':'label'},{'id':'footer','kind':'control','target':'footer','property':'label'},{'id':'marker-width','kind':'geometry','target':'markerA','property':'width','op':'near','basis':'semantic'},{'id':'marker-gap','kind':'geometry','target':'markerB','reference_target':'markerA','property':'gap_x','op':'near','basis':'semantic'},{'id':'ink','kind':'text_layout','target':'ink','property':'color_argb'},{'id':'font','kind':'text_layout','target':'ink','property':'font_sp'},{'id':'open-callback','kind':'event'},{'id':'replace-quiet','kind':'event','stimulus':'caller_update'},{'id':'visual-reading','kind':'manual','target':'heading','allowed_methods':['visual'],'coverage':'full_content'}]
states=[{'id':'initial','input_index':0,'after_action':-1,'coverage':'full_content'},{'id':'opened','input_index':0,'after_action':0,'coverage':'targets'},{'id':'replaced','input_index':1,'after_action':1,'coverage':'targets'}]
actions=[{'type':'tap','target':'disclosure','reveal':True,'state_id':'opened'},{'type':'apply_next_fixture','state_id':'replaced'}]
def expr(pointer):return {'source':'reading-design','pointer':pointer}
values={}
for r in rules:
 values[r['id']]={}
 for state in states:
  sid=state['id'];index='B'if sid=='replaced'else'A'
  if r['id']=='open-callback' and sid!='opened':cell={'not_applicable':'No disclosure activation in this state.'}
  elif r['id']=='replace-quiet' and sid!='replaced':cell={'not_applicable':'No caller replacement in this state.'}
  elif r['id']=='visual-reading' and sid!='initial':cell={'not_applicable':'Full-content visual inspection fixed for initial; target-state typed checks separately cover activation and replacement.'}
  else:
   pointer={'heading':'/heading/'+index,'status':'/status/'+('closed'if sid=='initial'else'open'),'footer':'/footer/'+index,'ink':'/style/ink','font':'/style/font','open-callback':'/events/open','replace-quiet':'/events/quiet','visual-reading':'/intent'}.get(r['id'])
   if r['id'].startswith('marker-'):
    cell={p:expr('/geometry/'+p+'/'+('width'if r['id']=='marker-width'else'gap'))for p in ['ios','android']};cell['tolerance']={p:expr('/geometry/'+p+'/tolerance')for p in ['ios','android']}
   else:cell={p:expr(pointer)for p in ['ios','android']}
  values[r['id']][sid]=cell
contract={'version':1,'design_owner':'Independent generic forward-test agent, isolated from root design/code/results','approval_reference':'independent-generic/APPROVAL.json fixed before implementation and rendering','sources':[{'id':'reading-design','path':'reference.json','sha256':hashlib.sha256((P/'design/reference.json').read_bytes()).hexdigest()}],'required_rule_ids':[r['id']for r in rules],'rules':rules,'scenarios':{'reading-long':{'states':states,'actions':actions,'values':values}}}
dump(P/'design/contract.json',contract)
bindings={key:{'identifier':'reading.'+key}for key in ['heading','status','footer','markerA','markerB','ink','disclosure']}
dump(P/'bindings.json',bindings)
dump(P/'actions.json',[dict(a,target=bindings['disclosure'])if a['type']=='tap'else a for a in actions])
fixture={'initial':{'title':'Reading set A','footer':'End of reading set A','prefix':'Field note'},'updates':[{'title':'Reading set B','footer':'End of reading set B','prefix':'Revised note'}],'width':390,'theme':'light','fontScale':1.0,'dynamic_type':'large','direction':'ltr','canvas_color':'#F4F7FA','required_identifiers':['reading.heading','reading.footer'],'max_scrolls':18,'observation_max_scrolls':24,'trace_reveal_images':True}
dump(P/'fixtures.json',fixture)
dump(P/'early-failure.json',{'stage':'bootstrap first invocation','failure':'FileExistsError because I pre-created the bootstrap workspace. Caller setup mistake; corrected by using fresh hosts child directory.','exit_code':1,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(P)
