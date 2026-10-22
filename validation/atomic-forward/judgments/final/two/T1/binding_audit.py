import json,pathlib,sys,hashlib
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/two/T1';sys.dont_write_bytecode=True;sys.path.insert(0,str(B/'candidate-v8/scripts'));from native_checks import resolve,bound_state_evidence
results={}
for p in sorted((B/'evaluation-inputs/final/T1').glob('*/*/*/inputs.json')):
 i=json.loads(p.read_text());obs=json.loads((B/i['observation']).read_text());plan=json.loads((p.parent/'plan.json').read_text());key='/'.join([i['source'],i['platform'],i['case']]);results[key]={'steps':obs['steps'],'events':obs['events'],'state_facts':{},'fixtures':{}}
 # Original caller fixtures are evidence, no implementation-generated truth.
 fx=B/i['root']/'fixtures.json'
 if fx.exists():results[key]['fixtures']=json.loads(fx.read_text())
 for state in plan['states']:
  found,complete,why,cap=bound_state_evidence(obs,state);record={'complete':complete,'why':why,'binding':cap.get('binding')if cap else None,'targets':{}}
  for target in sorted({a['target']['identifier'] for a in plan['assertions']if a.get('target',{}).get('identifier')}):
   record['targets'][target]=[{'index':n,'resolution':resolve(s,{'identifier':target},i['platform'])}for n,s in found]
  results[key]['state_facts'][state['id']]=record
  # Read actual semantic/control summaries; empty control lookup is not an absent semantic.
  facts={}
  for target in ['workshop.summary','workshop.disclosure','workshop.choice.a','workshop.choice.c','workshop.submit']:
   vals=[]
   for ent in record['targets'][target]:
    r=ent['resolution'];node=r.get('control')or r.get('semantic')or{};v={k:node.get(k)for k in ['label','enabled','selected']}
    if v.get('label')and v not in vals:vals.append(v)
   facts[target]=vals
  print(key,state['id'],'complete='+str(complete),'summary='+str([v['label']for v in facts['workshop.summary']]),'disclosure='+str([v['label']for v in facts['workshop.disclosure']]),'A='+str([(v['enabled'],v['selected'])for v in facts['workshop.choice.a']]),'C='+str([v['enabled']for v in facts['workshop.choice.c']]),'submit='+str([v['enabled']for v in facts['workshop.submit']]))
(O/'binding-facts.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
