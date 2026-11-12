import sys,argparse,copy,shutil
sys.dont_write_bytecode=True
from domain_support import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import native_checks,coverage_domain
base=ROOT/'work'/a.arm/'metadata-scope';base.mkdir();rows=[];original=ROOT/'work'/a.arm/'delta/ABI-A01-approved-runtime-shape-positive'
def record(id,passed,detail):
 row={'id':id,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST API/files with SIMULATED admitted native/runtime/compile ABI; no SDK','detail':detail};rows.append(row);save(base/(id+'-result.json'),row)
 if not passed:save(ROOT/'first-failures'/(a.arm+'--'+id+'.json'),row)
 print(a.arm+' '+id+': '+row['status'],flush=True)
for name,kind,wanted in[
 ('M01-full-after-action-bool','full-bool','unassessed'),('M02-full-after-action-float','full-float','unassessed'),
 ('M03-legacy-action-snapshot-bool','legacy-bool','unassessed'),('M04-legacy-action-integer-positive','legacy-int','passed'),
 ('M05-target-bundle-snapshot-bool','bundle-bool','unassessed'),('M06-target-only-unique-visible-scope','target-unique','passed')]:
 folder=base/name;folder.mkdir();shutil.copytree(original/'packet',folder/'packet');o=load(original/'observation.json');s=load(original/'state.json');target='absent-target';prop='present';expected=False
 if kind=='full-bool':o['state_captures'][0]['after_action']=False
 if kind=='full-float':o['state_captures'][0]['after_action']=0.0
 if kind in{'legacy-bool','legacy-int','bundle-bool'}:
  binding=copy.deepcopy(o['state_captures'][0]['binding']);o['state_captures']=[];s['coverage']='targets'if kind=='bundle-bool'else'target';target='anchor-a';expected=True
  step={'state_id':'start','after':False if kind=='legacy-bool'else 0,'binding_after':binding};o['steps']=[step]
  if kind=='bundle-bool':step.update(immediate_after=0,observation_set={'state_id':'start','after_action':0,'binding':binding,'binding_after_observation':binding,'binding_stable':True,'snapshot_indices':[False]})
 if kind=='target-unique':
  s['coverage']='targets';o['snapshots'][-1]['bottom_boundary']['hittable']=False;target='anchor-a';prop='unique';expected=True
 plan={'version':1,'states':[s],'required_assertion_ids':['typed'],'assertions':[{'id':'typed','state':'start','kind':'control','target':{'identifier':target},'property':prop,'expected':expected}]};report=native_checks.evaluate(plan,o,'ios',root=folder/'packet/native');save(folder/'observation.json',o);save(folder/'state.json',s);save(folder/'evaluated.json',report);actual=report['assertions'][0]['status'];record(name,actual==wanted,{'expected_status':wanted,'actual_status':actual,'state_complete':report['states']['start']['complete'],'assertion':report['assertions'][0]})
for name,mode in[('M07-approval-version-bool','approval-bool'),('M08-provider-version-bool','provider-bool'),('M09-host-shape-checksum-mismatch','shape'),('M10-unsupported-encoding-rehashed','encoding')]:
 folder=base/name;c,p,l=setup_config(folder,arm)
 if mode=='provider-bool':
  path=Path(c['coverage_provider_ref']['path']);v=load(path);v['version']=True;save(path,v);c['coverage_provider_ref']['sha256']=canonical(v)
 else:
  path=Path(c['coverage_domain_ref']['path']);v=load(path)
  if mode=='approval-bool':v['version']=True
  elif mode=='shape':v['common_host_shape']['ios']['viewport_height_pt']=599
  elif mode=='encoding':v['geometry_encoding']['cell_enclosure']['Q']='round(q)';v['geometry_encoding_sha256']=canonical(v['geometry_encoding'])
  save(path,v);c['coverage_domain_ref']['sha256']=canonical(v)
 error=None
 try:coverage_domain.prepare(c,p,l)
 except (ValueError,OSError,KeyError,TypeError)as e:error=str(e)
 record(name,error is not None,{'recomputed_external_file_reference':True,'error':error,'scope':'Synthetic pinned schema/policy negative, no newly authorized independent domain claimed'})
save(ROOT/'raw'/(a.arm+'-metadata-scope-results.json'),rows)
