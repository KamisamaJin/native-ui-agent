#!/usr/bin/env python3
"""Neutral counter protocol: intentional unavailable stimuli, no product defects."""
from pathlib import Path
import hashlib,json,shutil,sys,time,argparse
P=Path(__file__).resolve().parent;R=P.parents[1];REPO=R.parents[1]
sys.path.insert(0,str(REPO/'native-ui-agent/scripts'))
import design_contract as d,execution_plan as xp,action_guard as ag
parser=argparse.ArgumentParser();parser.add_argument('--positive-only',action='store_true');a=parser.parse_args()
W=R/'cache/neutral';S=R/'cache/stock'
if not W.exists():
 shutil.copytree(S,W,ignore=shutil.ignore_patterns('.git','build','.build','.gradle'))
for source,dest in [('Counter.swift',W/'alerttoast/Sources/AlertToast/NeutralCounter.swift'),('Counter.kt',W/'reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt')]:shutil.copy2(P/source,dest)
fixtures={'width':390,'viewportHeight':600,'theme':'light','direction':'ltr','dynamic_type':'large','fontScale':1,'initial':{'seed':0},'updates':[{'seed':8}],'max_scrolls':4}
targets={'tally':{'identifier':'counter.tally','role':'text'},'increment':{'identifier':'counter.increment','role':'button'},'disabled':{'identifier':'counter.disabled','role':'button'},'continue':{'identifier':'counter.continue','role':'button'},'pair':{'identifier':'counter.pair'},'missing':{'identifier':'counter.missing','role':'button'}}
def cond(name,prop,value):return{'target':targets[name],'property':prop,'op':'eq','expected':value}
actions=[{'type':'checkpoint'}, {'type':'tap','target':targets['increment'],'preconditions':[cond('increment','enabled',True)]},
 {'type':'tap','target':targets['disabled'],'allow_disabled':True}, {'type':'tap','target':targets['continue']},
 {'type':'checkpoint','depends_on':[]}, {'type':'apply_next_fixture'}, {'type':'tap','target':targets['missing'],'max_steps':1},
 {'type':'tap','target':targets['continue']}, {'type':'tap','target':targets['pair'],'depends_on':[]},
 {'type':'tap','target':targets['continue']}, {'type':'checkpoint','depends_on':[]},
 {'type':'tap','target':targets['continue'],'preconditions':[cond('tally','label','Tally: 8'),cond('continue','enabled',True)]}]
names=['front','counted','disabled_attempt','dependent_disabled','independent_one','replaced','missing_attempt','dependent_missing','ambiguous_attempt','dependent_ambiguous','independent_two','continued']
states=[{'id':n,'input_index':0 if i<5 else 1,'after_action':i,'coverage':'targets'}for i,n in enumerate(names)]
if a.positive_only:
 indices=[0,1,5,11];names=[names[i]for i in indices];actions=[actions[i]for i in indices]
 states=[{'id':n,'input_index':0 if i<2 else 1,'after_action':i,'coverage':'targets'}for i,n in enumerate(names)]
 actions[2]['callback_dependencies']=[{'action_index':1,'expected_events':['increment']}]
 actions[3]['callback_dependencies']=[{'action_index':2,'expected_events':[]}]
reference={'labels':{'zero':{'value':'Tally: 0','unit':'string'},'one':{'value':'Tally: 1','unit':'string'},'eight':{'value':'Tally: 8','unit':'string'}},
 'increments':{'value':['increment'],'unit':'events'},'continues':{'value':['continue'],'unit':'events'},'launch':{},
 'obligations':[{'id':'caption','clause':'The counter label matches the established caller/action path.','priority':'must','states':names,'risk':'content'},
 {'id':'events','clause':'Real counter actions emit their actual callbacks.','priority':'must','states':['counted','continued'],'risk':'behavior'}],
 'claims':[{'id':'caption-source','clause':'The component renders the counter from its caller-keyed state.','priority':'must','owner':'component','method':'source','subject':'component','rule_ids':[]},
 {'id':'bridge-source','clause':'The bridge forwards actual caller seed and event handler.','priority':'must','owner':'bridge','method':'source','subject':'bridge','rule_ids':[]}]}
rules=[{'id':'caption','kind':'control','target':'tally','property':'label'}, {'id':'event','kind':'event'}]
values={'caption':{},'event':{}}
for i,n in enumerate(names):
 label='zero'if i==0 else'one'if i<(2 if a.positive_only else 5)else'eight'
 values['caption'][n]={pl:{'source':'reference','pointer':'/labels/'+label}for pl in ['ios','android']}
 values['event'][n]=({pl:{'source':'reference','pointer':'/increments'if n=='counted'else'/continues'}for pl in ['ios','android']}if n in {'counted','continued'}else{'not_applicable':'No event behavior assertion requested for this checkpoint/stimulus.'})
routes={'version':1,'index':{'source':'reference','pointer':'/obligations'},'routes':{'caption':{'rule_ids':['caption'],'reason':'Native current label in each declared causal/independent branch.','regression_obligations':[]},'events':{'rule_ids':['event'],'reason':'Successful native stimuli only.','regression_obligations':['caption']}}}
O=P/('prepared-positive'if a.positive_only else'prepared');O.mkdir(exist_ok=False)
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
save(O/'fixtures.json',fixtures);save(O/'routes.json',routes)
for pl in ['ios','android']:
 out=O/pl;out.mkdir();bridge=P/('Bridge.swift'if pl=='ios'else'ObserverBridge.kt')
 ref=json.loads(json.dumps(reference));ref['launch']={'fixtures_sha256':d.digest(fixtures),'bridge_sha256':hashlib.sha256(bridge.read_bytes()).hexdigest(),'scenario':'neutral','platform':pl}
 save(out/'reference.json',ref)
 contract={'version':1,'design_owner':'independent neutral resource/action/evidence spec','approval_reference':'presealed probes/spec/seal-manifest.json','sources':[{'id':'reference','path':'reference.json','sha256':hashlib.sha256((out/'reference.json').read_bytes()).hexdigest()}], 'rules':rules,'required_rule_ids':[r['id']for r in rules], 'scenarios':{'neutral':{'states':states,'actions':actions,'values':values}}}
 save(out/'contract.json',contract);lock=d.seal(out/'contract.json',out);save(out/'lock.json',lock)
 plan,_=d.compile_contract(lock,d.digest(lock),'neutral',pl,{'tally':targets['tally']},actions)
 # Actions already carry exact independent native selectors; only assertion targets bind.
 save(out/'plan.json',plan)
 # Environment wire schema is generated below from the public example.
 example=json.loads((REPO/'native-ui-agent/assets/atomic-example'/('environment.'+pl+'.json')).read_text())
 example['width']=fixtures['width']
 save(out/'environment.json',example)
 config={'plan':str(out/'plan.json'),'design_lock':str(out/'lock.json'),'design_sha256':d.digest(lock),'routes':str(O/'routes.json'),'routes_sha256':d.digest(routes),'fixtures':str(O/'fixtures.json'),'bridge':str(bridge), 'launch_ref':{'source':'reference','pointer':'/launch'},
 'source_roots':[str(W/'alerttoast/Sources/AlertToast/NeutralCounter.swift'),str(W/'reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt')],
 'native_options':{'package':str(W/'alerttoast'),'simulator':'managed','developer-dir':'/Applications/Xcode.app/Contents/Developer'}if pl=='ios'else{'project':str(W/'reply/Reply'),'java-home':'/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home','android-sdk':'/Users/rex/Library/Android/sdk'},
 'responsibility_ref':{'source':'reference','pointer':'/claims'}, 'evidence_subjects':{'component':[str(W/('alerttoast/Sources/AlertToast/NeutralCounter.swift'if pl=='ios'else'reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt'))],'bridge':[str(bridge)]},'source_review_store':str(R/'cache/neutral-source-reviews'/pl),
 'environment':str(out/'environment.json'),'environment_sha256':d.digest(example),'resources':{'root':str(R/'cache'/('neutral-resources-'+pl)),'max_bytes':12*2**30,'min_free_bytes':5*2**30,'sample_seconds':1}}
 if pl=='ios':config['resources']['ios']={'device_type':'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro','runtime':'com.apple.CoreSimulator.SimRuntime.iOS-26-5'}
 save(out/'config.json',config)
save(O/'pre-sdk-seal.json',{'sealed_at_unix':time.time(),'files':{str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest()for p in O.rglob('*')if p.is_file()}})
print(O)
