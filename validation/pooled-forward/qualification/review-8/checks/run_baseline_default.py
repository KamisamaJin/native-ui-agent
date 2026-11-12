# Reuse only the independent non-forwarding transport fixture from run_default;
# the baseline keeps its own public CLI/default controller and old resource API.
from pathlib import Path
transport=Path(__file__).with_name('run_default.py').read_text().split('# Default unapproved current source')[0]
transport=transport.replace(',capture_validity\n','\n').replace("return dict(self.config['native_options'],**{'reset-owned-app':'1'})","return dict(self.config['native_options'])").replace(",patch.object(resource_manager,'boot_identity',return_value='SIMULATED-review6-host-boot')",'')
exec(compile(transport,str(Path(__file__).with_name('run_default.py')),'exec'))
config,plan,lock=setup_config(base/'unapproved',arm);component=Path(config['evidence_subjects']['probe-component'][0]);component.write_text(component.read_text()+'\n// unapproved source change\n');r,raw,out=invoke(config,'pre-sdk-source-review')
record('B01-default-unapproved-queues-before-SDK',r is not None and r['status']=='review_source_domain'and not r['native_executed']and raw['boundary_calls']==0,{'command':raw,'cycle':r})
config,plan,lock=setup_config(base/'admitted',arm);r,raw,out=invoke(config,'original-source-collector');manifest=load(out/'capture/native/manifest.json')if(out/'capture/native/manifest.json').exists()else{}
record('B02-common-controller-domain-root-integration',r is not None and raw['boundary_calls']==1 and manifest.get('execution_coverage',{}).get('required_states',[{}])[0].get('complete')is True and(out/'capture/native/coverage-domain-binding.json').is_file()and '--coverage-domain'in boundary_calls[0]['argv'],{'command':raw,'cycle':r,'manifest_status':manifest.get('status'),'manifest_error':manifest.get('error'),'first_state_coverage':manifest.get('execution_coverage',{}).get('required_states',[None])[0],'scope':'Baseline public controller only; no pooling/adoption/automatic-repair feature imported'})
save(ROOT/'raw'/(a.arm+'-'+a.run_name+'-results.json'),rows);save(base/'boundary-calls.json',boundary_calls);save(base/'emitted-sdk-commands.json',emitted)
