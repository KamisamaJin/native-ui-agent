from foundation_cases import *
import argparse,subprocess,plistlib,contextlib,io
from types import SimpleNamespace
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import ios_observe,execution_plan,native_checks,review_contract,requirement_routes,design_contract as d,feedback_loop
base=ROOT/'work'/a.arm/'integration';base.mkdir();results=[]
def record(id,passed,detail):
 row={'id':id,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST file/module execution with SIMULATED SDK/observations','detail':detail};results.append(row)
 if not passed:save(ROOT/'first-failures'/(a.arm+'--'+id+'.json'),row)
 print(a.arm+' '+id+': '+row['status'],flush=True)

# A second independently rendered width-160 fixture is exported by a wholly mocked SDK.
source_images=base/'source-images';source_images.mkdir();o=json.loads((ROOT/'fixtures'/'pristine'/'observation.json').read_text());state=json.loads((ROOT/'fixtures'/'pristine'/'state.json').read_text());rng=random.Random(588301);world=Image.new('RGBA',(160,176));world.putdata([(rng.randrange(256),rng.randrange(256),rng.randrange(256),255)for _ in range(160*176)]);draw=ImageDraw.Draw(world)
for label,y in [('A',50),('B',72),('C',102),('D',124)]:draw.rectangle((2,y,15,y+9),fill=(255,255,255,255));draw.text((3,y),label,fill=(0,0,0,255))
draw.rectangle((0,170,159,173),fill=(180,20,210,255));world.save(base/'oracle-world-160.png')
for i,(snap,off)in enumerate(zip(o['snapshots'],[0,40,80])):
 world.crop((0,off,160,off+96)).save(source_images/('frame-'+str(i)+'.png'));snap['app_frame']['width']=160;snap['viewport']['width']=160;snap['runtime']['content_frame']['width']=160;snap['screenshot_pixels']['width']=160;snap['nodes'][0]['frame']['width']=160;snap['nodes'][5]['frame']['width']=160
config={'initial':{'fixture':'closed-four-leaf-static-world'},'updates':[],'width':160,'theme':'light','direction':'ltr','dynamic_type':'large','state_capture':True,'observation_strategy':'coalesced','execution_scope':'full','execution_states':[{'state_id':'strip','coverage':'full_content','targets':[]}],'execution_state_definitions':[state]};fixtures=save(base/'fixtures.json',config);actions=save(base/'actions.json',[{'type':'checkpoint','state_id':'strip','capture_scope':'full_content'}]);bridge=base/'NeutralBridge.swift';bridge.write_text('// SIMULATED collector transport only; no SDK execution\n')
compiled=base/'mock-compiled.xctestrun';compiled.write_bytes(plistlib.dumps({'ObserverTests':{'TestBundlePath':'__TESTROOT__/ObserverTests.xctest'}}));commands=[]
def command(argv,env,log=None):
 text='SIMULATED command; no SDK/tool process executed\n'
 if 'summary'in argv:text=json.dumps({'totalTestCount':1,'failedTests':0})
 if 'export'in argv:
  exported=Path(argv[argv.index('--output-path')+1]);exported.mkdir();entries=[]
  for i in range(3):name='frame-'+str(i)+'.png';shutil.copyfile(source_images/name,exported/name);entries.append({'suggestedHumanReadableName':name,'exportedFileName':name})
  save(exported/'manifest.json',entries);save(exported/'SIMULATED-observation.json',o)
 if argv and argv[0]=='xcodebuild':
  result=Path(argv[argv.index('-resultBundlePath')+1]);result.mkdir();(result/'SIMULATED.txt').write_text('Mock result bundle only\n')
 commands.append({'evidence_class':'SIMULATED','argv':argv,'response_sha256':hashlib.sha256(text.encode()).hexdigest()})
 if log:Path(log).write_text(text)
 return subprocess.CompletedProcess(argv,0,stdout=text)
output=base/'collector-output';args=SimpleNamespace(output=str(output),bridge=str(bridge),package=None,fixtures=str(fixtures),actions=str(actions),developer_dir='/SIMULATED/Developer',simulator='SIMULATED-NOT-A-DEVICE',sdk='iphonesimulator',product='Neutral',build_cache=None,reset_owned_app=None,build_context_sha256=None)
with patch.object(ios_observe,'command',command),patch.object(ios_observe,'prepare_build',return_value=compiled),contextlib.redirect_stdout(io.StringIO())as printed:code=ios_observe.run(args)
manifest=d.load(output/'manifest.json');exported_obs=d.load(output/'observation.json');receipt=manifest.get('execution_coverage',{});save(base/'mock-commands.json',commands);save(base/'collector-return.json',{'exit_code':code,'stdout':printed.getvalue(),'evidence_class':'SIMULATED SDK / HOST collector'})
record('I02-collector-original-export-root',code==0 and receipt.get('satisfied')is True and len(receipt['required_states'][0]['coverage_proof']['links'])==2,{'manifest':str(output/'manifest.json'),'original_root':str(output),'proof':receipt,'provider_source_pinned':str(arm/'scripts'/'scroll_coverage.py')in manifest['source_hashes']})

# Independently sealed closed-world visual proposition tests review/evaluation/routing.
design=base/'independent-design';design.mkdir();facts={'expected':{'value':True,'unit':'bool'},'question':{'value':'The known closed static component strip is present in the original exported frames.','unit':'string'},'obligations':[{'id':'closed-strip','clause':'Review only this closed static vertical strip; no hidden/async/offaxis claim.','priority':'must','states':['strip'],'risk':'content'}]};save(design/'facts.json',facts)
ref={'source':'oracle','pointer':'/expected'};contract={'version':1,'design_owner':'independent-review-5','approval_reference':'sealed synthetic closed-world oracle; never native credit','sources':[{'id':'oracle','path':'facts.json','sha256':sha(design/'facts.json')}],'required_rule_ids':['strip-visible'],'rules':[{'id':'strip-visible','kind':'manual','target':'content','allowed_methods':['visual'],'coverage':'full_content'}],'scenarios':{'closed':{'states':[state],'actions':[{'type':'checkpoint','state_id':'strip'}],'values':{'strip-visible':{'strip':{'ios':ref,'android':ref}}}}}};save(design/'contract.json',contract);lock=d.seal(design/'contract.json',design);lock_sha=d.digest(lock);save(design/'lock.json',lock);plan,_=d.compile_contract(lock,lock_sha,'closed','ios',{'content':{'identifier':'leaf-a'}},[{'type':'checkpoint','state_id':'strip'}]);save(design/'plan.json',plan)
policy={'version':1,'design_lock_sha256':lock_sha,'approval_reference':'independent closed-world scope','ownership':{'content':'component'},'atoms':[{'rule_id':'strip-visible','aspect':'content_presence','method':'visual','question':{'source':'oracle','pointer':'/question'}}]};policy_sha=d.digest(policy);save(design/'policy.json',policy);cat=review_contract.catalog(plan,lock,lock_sha,policy,policy_sha,'ios');obs_sha=sha(output/'observation.json')
def bind(actual):
 sub={'version':1,'catalog_sha256':d.digest(cat),'observation_sha256':obs_sha,'decisions':[{'review_id':cat['rows'][0]['review_id'],'actual':actual,'reason':'SIMULATED independently known fixture proposition'if actual else'SIMULATED deliberate failing actual for route challenge','snapshot_indices':[0,1,2]}]}
 return review_contract.bind(plan,lock,lock_sha,policy,policy_sha,exported_obs,obs_sha,output,sub,'ios')
manual=bind(True);report=native_checks.evaluate(plan,exported_obs,'ios',manual,output,obs_sha,lock,lock_sha,policy,policy_sha);save(base/'bound-positive-review.json',manual);save(base/'evaluated-positive.json',report)
negative=bind(False);report_f=native_checks.evaluate(plan,exported_obs,'ios',negative,output,obs_sha,lock,lock_sha,policy,policy_sha);save(base/'bound-routing-control-review.json',negative);save(base/'evaluated-routing-control.json',report_f)
routes={'version':1,'index':{'source':'oracle','pointer':'/obligations'},'routes':{'closed-strip':{'rule_ids':['strip-visible'],'reason':'Only the independently closed observed vertical strip','regression_obligations':[]}}};coverage=requirement_routes.audit(lock,lock_sha,plan,routes,d.digest(routes));good=requirement_routes.route_findings(coverage,plan,report_f,exported_obs,root=output);missing=requirement_routes.route_findings(coverage,plan,report_f,exported_obs,root=None);save(base/'routes-original-root.json',good);save(base/'routes-missing-root.json',missing)
record('I03-review-evaluation-routing-original-root',report['counts']=={'passed':1,'failed':0,'unassessed':0}and all(t['action']=='diagnose_product'for t in good['tasks'])and all(t['action']=='acquire_evidence'for t in missing['tasks']),{'positive_report':str(base/'evaluated-positive.json'),'with_original_root':good,'without_original_root':missing,'scope':'Closed static strip only; deliberate failing actual is a protocol routing input, not a native product defect.'})

# Pixel files and observation/receipt bytes stay externally pinned; forged wrappers cannot replace them.
pin=save(base/'externally-pinned-result.json',{'image_hashes':{str(p.relative_to(output)):sha(p)for p in(output/'attachments').glob('*.png')}});external=sha(pin);original_pin=(base/'pristine-external-result.json');original_pin.write_bytes(pin.read_bytes());target=output/'attachments'/'frame-1.png';pristine=base/'pristine-frame-1.png';shutil.copyfile(target,pristine);im=Image.open(target).convert('RGBA');v=im.getpixel((4,4));im.putpixel((4,4),((v[0]+1)%256,*v[1:]));im.save(target);image_error=receipt_error=None
try:execution_plan.verify_capture_images(d.load(pin),output)
except ValueError as e:image_error=str(e)
changed=d.load(pin);changed['image_hashes']['attachments/frame-1.png']=sha(target);changed['coverage_satisfied']=True;save(pin,changed)
try:feedback_loop.load_previous(pin,external,{}, {},'',{},bridge,[])
except ValueError as e:receipt_error=str(e)
record('I04-pinned-pixels-and-wrapper-tamper',image_error is not None and receipt_error is not None,{'original_frame':str(pristine),'pixel_error':image_error,'rewritten_wrapper_error':receipt_error,'external_original_sha256':external,'altered_sha256':sha(pin),'evidence_class':'HOST altered copy with SIMULATED collector files; original bytes retained'})
save(ROOT/'raw'/(a.arm+'-integration-results.json'),results)
