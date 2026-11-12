import sys,argparse,copy,shutil
sys.dont_write_bytecode=True
from domain_support import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import native_checks
prior=ROOT.parent/'review-9';oldarm='candidate-v13.8'if a.arm.startswith('candidate')else'baseline-v12.6-common-5';base=ROOT/'work'/a.arm/'focus';base.mkdir(parents=True);rows=[]
def record(name,passed,detail):
 row={'id':name,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST frozen evaluator with preserved SIMULATED native query/runtime/source fixtures; zeroSDK','detail':detail};rows.append(row);save(base/(name+'-result.json'),row)
 if not passed:
  with(ROOT/'first-failures'/(a.arm+'--'+name+'.json')).open('x')as stream:json.dump(row,stream,indent=2)
 print(a.arm+' '+name+': '+row['status'],flush=True)
def locate(folder):
 o=load(folder/'observation.json');plan=load(folder/'plan.json');platform='android'if'android'in folder.name else'ios';native=folder/('native'if platform=='android'else'packet/native');return o,plan,platform,native
def replay(name,folder,expected):
 o,plan,platform,native=locate(folder);report=native_checks.evaluate(plan,o,platform,root=native);actual=report['assertions'][0]['status'];record(name,actual==expected,{'expected_status':expected,'actual_status':actual,'original_observation':str(folder/'observation.json'),'original_observation_sha256':sha(folder/'observation.json'),'original_plan_sha256':sha(folder/'plan.json'),'report':report})

# All18 review9 new-wire controls:5 SC18 failures, visible/complete controls and
# explicit query/graph/schema negatives. Original bytes and old verdicts stay put.
for old in load(prior/'raw'/(oldarm+'-wire-delta-results.json')):
 replay(old['id'],prior/'work'/oldarm/'wire-delta'/old['id'],old['detail']['expected_status'])

selected=[]
for platform in['ios','android']:
 selected += [platform+'-'+name for name in ['full-native-query-positive','target-native-query-positive','incomplete-full-unique','incomplete-full-presence','distinct-native-duplicate','same-entity-duplicate-record','mixed-epoch','incomplete-no-matches-absence','local-complete-query-absence']]
oldrows={v['id']:v for v in load(prior/'raw'/(oldarm+'-preserved-results.json'))}
for name in selected:
 old=oldrows[name];replay('boundary-'+name,Path(old['original_observation']).parent,old['expected_status'])

# New near-branch controls: a complete local query is not full matching-domain
# coverage, and singleton native presence does not establish callback dispatch.
for platform in['ios','android']:
 original=prior/'work'/oldarm/'wire-delta'/(platform+'-offscreen-count1-presence')
 for mode,prop,expected,wanted in[('full-incomplete-offscreen-present','present',True,'passed'),('full-incomplete-offscreen-unique','unique',True,'unassessed'),('full-incomplete-empty','present',False,'unassessed'),('presence-does-not-prove-callback','present',True,'passed')]:
  name=platform+'-'+mode;folder=base/name;folder.mkdir();o,plan,pl,n=locate(original);o=copy.deepcopy(o);s=copy.deepcopy(plan['states'][0]);shutil.copytree(n,folder/'native');native=folder/'native';target=copy.deepcopy(plan['assertions'][0]['target'])
  if mode.startswith('full-incomplete'):
   s['coverage']='full_content';binding=copy.deepcopy(o['steps'][0]['binding_after']);o['state_captures']=[{'state_id':'start','after_action':0,'binding':binding,'snapshot_indices':[0],'top_reached':True,'bottom_reached':False,'stable_binding':True}]
  if mode=='full-incomplete-empty':target={'identifier':'never-native-target'}
  assertions=[{'id':'presence','state':'start','kind':'control','target':target,'property':prop,'expected':expected}]
  if mode=='presence-does-not-prove-callback':assertions.append({'id':'callback','state':'start','kind':'event','action_index':0,'expected':[]})
  plan={'version':1,'states':[s],'required_assertion_ids':[item['id']for item in assertions],'assertions':assertions};report=native_checks.evaluate(plan,o,pl,root=native);actual=report['assertions'][0]['status'];ok=actual==wanted and report['states']['start']['complete']is False
  if mode=='presence-does-not-prove-callback':ok=ok and report['assertions'][1]['status']=='unassessed'
  save(folder/'observation.json',o);save(folder/'plan.json',plan);save(folder/'evaluated.json',report);record(name,ok,{'expected_status':wanted,'actual_status':actual,'complete':report['states']['start']['complete'],'report':report,'scope':'Offscreen native existence/cardinality only; no new activation or whole-domain credit.'})
save(ROOT/'raw'/(a.arm+'-focus-results.json'),rows)
