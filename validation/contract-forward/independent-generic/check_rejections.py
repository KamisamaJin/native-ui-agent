import pathlib,json,copy,subprocess,time,hashlib
P=pathlib.Path(__file__).resolve().parent;R=P/'rejections';R.mkdir(exist_ok=True)
script=pathlib.Path('native-ui-agent/scripts/design_contract.py'); check=pathlib.Path('native-ui-agent/scripts/native_checks.py'); sha=json.loads((P/'APPROVAL.json').read_text())['design_lock_sha256'];rows=[]
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def run(name,argv):
 start=time.time();r=subprocess.run(argv,capture_output=True,text=True);(R/(name+'.log')).write_text(r.stdout+r.stderr);rows.append({'name':name,'command':argv,'exit_code':r.returncode,'rejected':r.returncode!=0,'wall_seconds':time.time()-start,'message':(r.stdout+r.stderr).strip().splitlines()[-1]})
original=json.loads((P/'design/contract.json').read_text())
for name in ['source-digest','inline-expected','missing-state-cell','geometry-unit']:
 root=R/name;root.mkdir();contract=copy.deepcopy(original);reference=json.loads((P/'design/reference.json').read_text())
 if name=='source-digest':reference['heading']['A']['value']='Unapproved source mutation'
 if name=='inline-expected':contract['scenarios']['reading-long']['values']['heading']['initial']['ios']={'value':'Reading set A','unit':'string'}
 if name=='missing-state-cell':del contract['scenarios']['reading-long']['values']['footer']['replaced']
 if name=='geometry-unit':reference['geometry']['ios']['width']['unit']='dp'
 dump(root/'reference.json',reference)
 if name=='geometry-unit':contract['sources'][0]['sha256']=hashlib.sha256((root/'reference.json').read_bytes()).hexdigest()
 dump(root/'contract.json',contract)
 run(name,['python3',str(script),'seal','--contract',str(root/'contract.json'),'--root',str(root),'--output',str(root/'rejected-lock.json')])
for name in ['binding-override','route-mutation']:
 binding=json.loads((P/'bindings.json').read_text());actions=json.loads((P/'actions.json').read_text())
 if name=='binding-override':binding['heading']['expected']='Injected expectation'
 else:actions[0]['reveal']=False
 dump(R/(name+'-bindings.json'),binding);dump(R/(name+'-actions.json'),actions)
 run(name,['python3',str(script),'compile','--lock',str(P/'design-lock.json'),'--lock-sha256',sha,'--scenario','reading-long','--platform','android','--bindings',str(R/(name+'-bindings.json')),'--actions',str(R/(name+'-actions.json')),'--output',str(R/(name+'-compiled'))])
dump(R/'empty-observation.json',{'snapshots':[],'steps':[]})
for name in ['plan-expected','plan-tolerance','plan-source','plan-omission','plan-state']:
 plan=json.loads((P/'generated-android/plan.json').read_text())
 if name=='plan-expected':plan['assertions'][0]['expected']='Injected expectation'
 elif name=='plan-tolerance':next(a for a in plan['assertions']if a.get('tolerance')is not None)['tolerance']=20
 elif name=='plan-source':plan['assertions'][0]['expectation_provenance'][0]['pointer']='/heading/B'
 elif name=='plan-omission':plan['assertions'].pop();plan['required_assertion_ids'].pop()
 elif name=='plan-state':plan['states'][0]['coverage']='targets'
 dump(R/(name+'.json'),plan)
 run(name,['python3',str(check),'--plan',str(R/(name+'.json')),'--observation',str(R/'empty-observation.json'),'--platform','android','--design-lock',str(P/'design-lock.json'),'--design-sha256',sha,'--output',str(R/(name+'-checks.json'))])
dump(R/'results.json',rows)
print(json.dumps(rows,indent=2))
assert all(r['rejected']for r in rows)
