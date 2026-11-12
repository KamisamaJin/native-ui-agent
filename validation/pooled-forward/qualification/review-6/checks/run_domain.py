import sys,argparse,copy,shutil
sys.dont_write_bytecode=True
from domain_support import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import coverage_domain,native_checks,execution_plan,locator_diagnostics,requirement_routes
base=ROOT/'work'/a.arm/'domain';base.mkdir();rows=[]
def record(id,passed,detail):
 row={'id':id,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST source/domain/evaluator API and SIMULATED compile log/native packet; no SDK','detail':detail};rows.append(row);save(base/(id+'-result.json'),row)
 if not passed:save(ROOT/'first-failures'/(a.arm+'--domain--'+id+'.json'),row)
 print(a.arm+' '+id+': '+row['status'],flush=True)

config,plan,lock=setup_config(base/'admitted',arm);value=coverage_domain.prepare(config,plan,lock);save(base/'prepared-original.json',value)
record('D01-independent-normal-source-admission',value['revision']=='normal'and value['component']['sha256']==sha(config['evidence_subjects']['probe-component'][0]),{'prepared':str(base/'prepared-original.json')})
for name,change in[
 ('D02-unapproved-component-revision',lambda c,p,l:Path(c['evidence_subjects']['probe-component'][0]).write_text('// unapproved independent negative\n')),
 ('D03-unused-approved-subject',lambda c,p,l:c['evidence_subjects'].update({'probe-component':[str(Path(c['bridge']))]})),
 ('D04-changed-environment-policy',lambda c,p,l:c.update(environment_sha256='1'*64)),
 ('D05-changed-required-state',lambda c,p,l:p['states'][0].update(id='foreign-state')),
 ('D06-unpinned-approval',lambda c,p,l:c['coverage_domain_ref'].update(sha256='1'*64)),
 ('D07-unpinned-provider',lambda c,p,l:c['coverage_provider_ref'].update(sha256='1'*64)),
 ('D08-different-bridge',lambda c,p,l:Path(c['bridge']).write_text('// alternate bridge\n')),
 ('D09-foreign-product',lambda c,p,l:c['native_options'].update(product='UnusedProduct'))]:
 c,p,l=setup_config(base/name,arm);change(c,p,l);error=None;task=None
 try:coverage_domain.prepare(c,p,l)
 except (ValueError,OSError)as e:error=str(e);task=getattr(e,'task',None)
 record(name,error is not None and(name!='D02-unapproved-component-revision'or task and task['kind']=='review_source_domain'),{'error':error,'task':task})

for name,mod,expected in[
 ('D10-append-approved-source-observation',lambda d:d['platforms']['ios']['approved_component_revisions'].update({'independent-revision':{'sha256':'a'*64,'bytes':100,'authored_artifact':'SIMULATED-uncompiled'}}),True),
 ('D11-change-domain-host-rule',lambda d:d['common_host_shape']['common'].update(terminal_identifier='foreign-terminal'),False),
 ('D12-change-oracle-binding',lambda d:d['binds'].update(design_lock_sha256='b'*64),False),
 ('D13-change-domain-premise',lambda d:d.update(scope='Additional unobserved branch claim'),False)]:
 original=load(config['coverage_domain_ref']['path']);changed=copy.deepcopy(original);mod(changed);same=canonical(coverage_domain.policy(original))==canonical(coverage_domain.policy(changed));record(name,same==expected,{'normalized_policy_equal':same,'expected':expected,'original_policy_sha256':canonical(coverage_domain.policy(original)),'changed_policy_sha256':canonical(coverage_domain.policy(changed))})

# Bind the original source and host proof to an actual prepared/request namespace.
source=ROOT/'work'/a.arm/'geometry/positive-independent-encoded-strip';native=attach_packet(base/'pristine-packet',config,plan,value,arm,source/'images');verified=coverage_domain.verify_packet(native);save(base/'verified-original.json',verified)
o=load(source/'observation.json');s=load(source/'state.json');positive=native_checks.bound_state_evidence(o,s,native)
record('D14-original-domain-packet-and-full-state',positive[1],{'domain':verified,'state_reason':positive[2],'scope':'SIMULATED metadata and compiled text; only host validator semantics'})

for name,mutate in[
 ('D15-missing-prepared-input',lambda p:(p/'coverage-domain-prepared.json').unlink()),
 ('D16-tampered-prepared-input',lambda p:(p/'coverage-domain-prepared.json').write_text('{}')),
 ('D17-missing-request',lambda p:(p/'request.json').unlink()),
 ('D18-tampered-request-source-pin',lambda p:save(p/'request.json',dict(load(p/'request.json'),source_sha256='c'*64))),
 ('D19-tampered-source-map',lambda p:save(p/'source-before.json',{})),
 ('D20-tampered-parent-plan',lambda p:save(p/'parent-plan.json',{})),
 ('D21-missing-domain-binding',lambda p:(p/'native/coverage-domain-binding.json').unlink()),
 ('D22-tampered-component-copy',lambda p:(p/'native/coverage-domain-component.swift').write_text('// foreign')),
 ('D23-missing-compiled-build-log',lambda p:(p/'native/compiled-build.log').unlink()),
 ('D24-tampered-compile-action',lambda p:(p/'native/compiled-build.log').write_text('SwiftCompile unused-source.swift\n')),
 ('D25-tampered-compiled-host',lambda p:(p/'native/compiled-project/ObserverApp.swift').write_text('// foreign host')),
 ('D26-tampered-captured-provider',lambda p:(p/'native/tool-sources/ObserverTests.swift').write_text('// foreign provider')),
 ('D27-domain-header-only',lambda p:save(p/'native/coverage-domain-input.json',{'complete':True,'closed_domain':True}))]:
 packet=base/name;shutil.copytree(base/'pristine-packet',packet);mutate(packet);ev=native_checks.bound_state_evidence(o,s,packet/'native');record(name,not ev[1],{'state_reason':ev[2],'full_content_complete':ev[1]})

# Old failures are challenged again under the newly admitted schema/domain.
for name,expected in[('terminal-outside-true-header',False),('global-offscreen-id-other-lineage',False),('container-role-leaves',False),('content-offaxis',False),('unstable-binding-header-direct-only',False),('sixteen-bit-rgb-lowbit-mismatch',False),('joint-final-witness-inconsistency',False)]:
 src=ROOT/'work'/a.arm/'geometry'/name;packet=base/('integration-'+name);n=attach_packet(packet,config,plan,value,arm,src/'images');oo=load(src/'observation.json');ss=load(src/'state.json');ev=native_checks.bound_state_evidence(oo,ss,n);record('D28-'+name,ev[1]==expected,{'expected_complete':expected,'actual_complete':ev[1],'reason':ev[2]})

# Diagnose with a nonempty real source scan, holding original image root fixed.
diagplan={'states':[s],'design_contract':{'platform':'ios'},'assertions':[{'id':'diagnostic','state':s['id'],'kind':'control','target':{'identifier':'not-in-fixture'},'property':'present','expected':True}]};report={'rows':[{'id':'diagnostic','status':'failed'}]}
empty=locator_diagnostics.diagnose(diagplan,report,o,[],root=native);production=locator_diagnostics.diagnose(diagplan,report,o,config['source_roots'],root=native);missing=locator_diagnostics.diagnose(diagplan,report,o,config['source_roots'],root=None)
record('D29-diagnostic-root-survives-source-scan',empty['items'][0]['full_content_complete']and production['items'][0]['full_content_complete']and not missing['items'][0]['full_content_complete'],{'empty_scan':empty,'production_scan':production,'missing_original':missing})
save(ROOT/'raw'/(a.arm+'-domain-results.json'),rows)
