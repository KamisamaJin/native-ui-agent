from encoding_cases import *
import shutil,sys
POOLED=ROOT.parents[1]
SPEC=POOLED/'qualification/spec/lazy-coverage/encoding-domain'
PROFILE=POOLED/'qualification/neutral-design/executable-profile'
def load(p):return json.loads(Path(p).read_text())
def setup_config(folder,arm,revision='normal'):
 folder.mkdir(parents=True,exist_ok=False);project=folder/'project';component=project/'Sources/AlertToast/NativeQualificationProbe.swift';component.parent.mkdir(parents=True)
 inputs=load(SPEC/'INPUTS.json');src=inputs['sources']['ios'][revision];shutil.copyfile(POOLED/src['authored_artifact'],component)
 bridge=folder/'ObserverBridge.swift';shutil.copyfile(POOLED/inputs['sources']['ios']['bridge']['authored_artifact'],bridge)
 assert sha(component)==src['sha256']and sha(bridge)==inputs['sources']['ios']['bridge']['sha256']
 (project/'Package.swift').write_text('// SIMULATED private package marker. Never sent to swift/xcodebuild.\n')
 paths={'plan':PROFILE/'prepared/ios-cold/plan.json','design_lock':PROFILE/'approved-lock.json','fixtures':PROFILE/'fixtures/ios-cold.json','routes':PROFILE/'routes.json','environment':PROFILE/'environment.ios.json'}
 config={}
 for k,p in paths.items():
  dest=folder/(k+'.json');shutil.copyfile(p,dest);config[k]=str(dest)
 config.update(bridge=str(bridge),design_sha256=canonical(load(config['design_lock'])),routes_sha256=canonical(load(config['routes'])),environment_sha256=canonical(load(config['environment'])),launch_ref={'source':'reference','pointer':'/launch/ios-cold'},source_roots=[str(project/'Sources')],platform_source_roots={'ios':[str(project/'Sources')]},native_options={'package':str(project),'product':'AlertToast','developer-dir':str(folder/'SIMULATED-Developer'),'simulator':'SIMULATED-NONFORWARDING'},evidence_subjects={'probe-component':[str(component)],'thin-bridge':[str(bridge)]},workflow={'root':str(folder/'workflow'),'max_cycles':30},resources={'root':str(folder/'resources')})
 approval=folder/'domain-approval.json';shutil.copyfile(SPEC/'DOMAIN-APPROVAL.json',approval)
 config['coverage_domain_ref']={'path':str(approval),'sha256':canonical(load(approval))}
 provider=folder/'provider-conformance.json';shutil.copyfile(arm/'assets/ios-observer/provider-conformance.json',provider)
 config['coverage_provider_ref']={'path':str(provider),'sha256':canonical(load(provider))}
 save(folder/'config.json',config)
 return config,load(config['plan']),load(config['design_lock'])
def attach_packet(folder,config,plan,value,arm,image_source=None):
 """Host-executed domain files with explicitly simulated original compile log.

 This is API validation, never actual compilation or native truth. All files are
 owned by this review and retain SIMULATED labels outside production namespace.
 """
 import coverage_domain,execution_plan
 folder.mkdir(parents=True,exist_ok=False);native=folder/'native';native.mkdir()
 before=execution_plan.source_fingerprint(config['source_roots'])
 save(folder/'parent-plan.json',plan);save(folder/'source-before.json',before);save(folder/'coverage-domain-prepared.json',value)
 save(folder/'request.json',{'parent_plan_sha256':canonical(plan),'source_sha256':canonical(before),'source_roots':config['source_roots'],'input_hashes':{'coverage-domain-prepared.json':sha(folder/'coverage-domain-prepared.json')},'evidence_class':'SIMULATED no SDK compile'})
 component=value['component'];bridge=value['bridge'];module=value['approval']['platforms']['ios']['module']
 (native/'compiled-build.log').write_text('SIMULATED mock compile log, no SDK/process was run\nSwiftCompile normal arm64 '+component['path']+" (in target '"+module+"' from project 'SIMULATED')\n")
 for subdir in['tool-sources','compiled-project']:
  (native/subdir).mkdir()
  for rel in value['provider']['files']:shutil.copyfile(arm/rel,native/subdir/Path(rel).name)
 coverage_domain.complete(value,{'source_hashes':{component['path']:component['sha256'],bridge['path']:bridge['sha256']}},native)
 if image_source:
  for p in Path(image_source).glob('*.png'):shutil.copyfile(p,native/p.name)
 save(folder/'SIMULATION.json',{'evidence_class':'HOST API/files with SIMULATED build/observation','native_executed':False,'SDK_commands':[],'cannot_support_native_or_timing_credit':True})
 return native
