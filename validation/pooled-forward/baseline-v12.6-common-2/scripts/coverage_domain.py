"""Pinned independent closed-domain/source admission, separate from pixel proof."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import design_contract as d


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x') as f: json.dump(v,f,indent=2)


class DomainReviewRequired(ValueError):
    def __init__(self,component,approval):
        super().__init__('Current source needs an independent closed-domain approval')
        self.task = {'kind':'review_source_domain','component':component,'approval_policy_sha256':d.digest(policy(approval)),
                     'design_lock_sha256':approval['binds']['design_lock_sha256'],
                     'reason':str(self),'status':'unassessed','scope':'Review finite closed main-scroll scope of actual current source; no behavioral verdict or oracle changes.'}


def pinned(ref):
    if not isinstance(ref,dict) or set(ref) != {'path','sha256'}: raise ValueError('Independent coverage approval reference required')
    value = d.load(Path(ref['path']))
    if d.digest(value) != ref['sha256']: raise ValueError('Pinned independent coverage approval differs')
    return value


def policy(value):
    """Current source approvals are observations, never editable design rules.

    Appending a separately approved source revision cannot waive its measured
    source diff/fresh retest. Changing any closed-domain/host/oracle policy can.
    """
    value = copy.deepcopy(value)
    for k in ['approved_at_utc','approved_by']: value.pop(k,None)
    for platform in value['platforms'].values(): platform.pop('approved_component_revisions',None)
    return value


def prepare(config,plan,lock):
    if not config.get('coverage_domain_ref'): return None
    approval = pinned(config['coverage_domain_ref']); platform = plan['design_contract']['platform']
    if approval.get('version') != 1 or approval['binds']['design_lock_sha256'] != config['design_sha256'] or d.digest(lock) != config['design_sha256']:
        raise ValueError('Coverage domain belongs to another independent design')
    if approval['binds']['required_native_assertions'] != len(plan['assertions']) or approval['binds']['selected_state_ids'] != [s['id']for s in plan['states']]:
        raise ValueError('Coverage domain state/assertion scope differs')
    if approval['binds']['full_content_state_ids'] != [s['id']for s in plan['states']if s.get('coverage')=='full_content']:
        raise ValueError('Coverage domain full-state scope differs')
    if approval['binds']['environment_'+platform+'_canonical_sha256'] != config['environment_sha256']:
        raise ValueError('Coverage domain environment differs')
    fixtures = d.load(Path(config['fixtures'])); definition = approval['platforms'][platform]
    offered = [v for v in approval['approved_inputs'].values()if v['platform']==platform and v['fixture_canonical_sha256']==d.digest(fixtures)]
    if len(offered)!=1 or offered[0]['fixture_file_sha256']!=sha(config['fixtures']): raise ValueError('Exact approved domain fixture required')
    bridge = Path(config['bridge']).resolve()
    if sha(bridge)!=definition['exact_bridge']['sha256'] or sha(bridge)!=offered[0]['launch_bridge_sha256']:
        raise ValueError('Exact domain bridge required')
    project = Path(config['native_options']['package'if platform=='ios'else'project']).resolve()
    component = (project / definition['component_install_path']).resolve()
    if not component.is_relative_to(project) or not any(component.is_relative_to(Path(v).resolve())for v in config['source_roots']):
        raise ValueError('Domain component is outside actual installed production roots')
    subjects = config.get('evidence_subjects',{}); actual = approval['actual_subject_binding']
    if list(map(lambda v:str(Path(v).resolve()),subjects.get(actual['component_subject'],[]))) != [str(component)] or list(map(lambda v:str(Path(v).resolve()),subjects.get(actual['bridge_subject'],[]))) != [str(bridge)]:
        raise ValueError('Unused/foreign domain subject cannot substitute for actual imported component')
    revisions = [k for k,v in definition['approved_component_revisions'].items()if v['sha256']==sha(component) and v['bytes']==component.stat().st_size]
    if len(revisions)!=1: raise DomainReviewRequired({'path':str(component),'sha256':sha(component)},approval)
    provider = pinned(config.get('coverage_provider_ref')); root = Path(__file__).resolve().parents[1]
    if provider.get('status')!='conforming' or provider['common_host_shape_sha256']!=approval['common_host_shape_sha256']:
        raise ValueError('Independently reviewed current host conformance required')
    host_files = provider['files']
    if set(host_files) != {'assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift'} or any(sha(root/rel)!=expected for rel,expected in host_files.items()):
        raise ValueError('Actual host differs from independently reviewed provider')
    if platform=='ios' and config['native_options'].get('product','AlertToast')!=definition['product']: raise ValueError('Actual imported domain product differs')
    return {'version':1,'approval':approval,'approval_sha256':d.digest(approval),'policy_sha256':d.digest(policy(approval)),
            'provider':provider,'provider_sha256':d.digest(provider),'platform':platform,'revision':revisions[0],
            'component':{'path':str(component),'sha256':sha(component)},'bridge':{'path':str(bridge),'sha256':sha(bridge)},
            'scope':'Independent finite domain/source approval only; no behavior pass, old-capture waiver or raster proof.'}


def complete(value,manifest,output):
    """Bind the real compiled subject and byte-identical reviewed host after SDK."""
    output = Path(output); approval = value['approval']; component = value['component']; platform = value['platform']
    if platform!='ios': raise ValueError('This original-build coverage provider currently supports iOS')
    if manifest['source_hashes'].get(component['path'])!=component['sha256'] or manifest['source_hashes'].get(value['bridge']['path'])!=value['bridge']['sha256']:
        raise ValueError('Actual native source namespace differs from approved domain')
    log = output/'compiled-build.log'; module = approval['platforms'][platform]['module']
    lines = log.read_text().replace('\\ ',' ').splitlines()
    matches = [s for s in lines if s.startswith('SwiftCompile ') and ' '+component['path']+" (in target '"+module+"' " in s]
    if not matches: raise ValueError('Approved component has no original native compile action')
    for relative,expected in value['provider']['files'].items():
        if relative.startswith('assets/ios-observer/'):
            p = output/'tool-sources'/Path(relative).name
            compiled = output/'compiled-project'/Path(relative).name
            if sha(p)!=expected or sha(compiled)!=expected: raise ValueError('Actually compiled/rendered host differs from reviewed provider')
    if sha(component['path'])!=component['sha256'] or sha(value['bridge']['path'])!=value['bridge']['sha256']:
        raise ValueError('Domain subject changed during native capture')
    save(output/'coverage-domain-input.json',value)
    shutil.copy2(component['path'],output/'coverage-domain-component.swift')
    save(output/'coverage-domain-binding.json',{'version':1,'status':'bound_actual_compiled_source','approval_sha256':value['approval_sha256'],
          'provider_sha256':value['provider_sha256'],'policy_sha256':value['policy_sha256'],'component_sha256':component['sha256'],
          'compiled_build_log_sha256':sha(log),'compile_actions':matches,'platform':platform})


def verify_packet(root):
    """Reconstruct domain permission from original files, not an observed flag."""
    if root is None: raise ValueError('coverage_domain: original domain evidence unavailable')
    root = Path(root); value = d.load(root/'coverage-domain-input.json'); binding = d.load(root/'coverage-domain-binding.json')
    approval = value['approval']; provider = value['provider']; component = value['component']
    parent = root.parent; request = d.load(parent/'request.json'); plan = d.load(parent/'parent-plan.json')
    prepared = parent/'coverage-domain-prepared.json'; before = d.load(parent/'source-before.json')
    if (d.digest(plan)!=request['parent_plan_sha256'] or approval['binds']['design_lock_sha256']!=plan['design_contract']['lock_sha256']
            or value!=d.load(prepared) or sha(prepared)!=request['input_hashes'].get('coverage-domain-prepared.json')
            or d.digest(before)!=request['source_sha256']):
        raise ValueError('coverage_domain: independent parent/request/source binding differs')
    namespaces = []
    for index,raw in enumerate(request['source_roots']):
        source_root = Path(raw).resolve(); actual = Path(component['path']).resolve()
        if actual.is_relative_to(source_root):
            key = str(index)+'/'+str(actual.relative_to(source_root))
            if before.get(key)==component['sha256']: namespaces.append(key)
    if not namespaces or value.get('platform')!='ios' or binding.get('platform')!='ios':
        raise ValueError('coverage_domain: original actual production source namespace unavailable')
    if d.digest(approval)!=value['approval_sha256'] or d.digest(provider)!=value['provider_sha256'] or d.digest(policy(approval))!=value['policy_sha256']:
        raise ValueError('coverage_domain: original approval/provider changed')
    if (binding.get('status')!='bound_actual_compiled_source' or binding['approval_sha256']!=value['approval_sha256']
            or binding['provider_sha256']!=value['provider_sha256'] or binding['policy_sha256']!=value['policy_sha256']
            or binding['component_sha256']!=component['sha256'] or sha(root/'coverage-domain-component.swift')!=component['sha256']):
        raise ValueError('coverage_domain: original actual subject binding differs')
    definition = approval['platforms']['ios']
    if component['sha256'] not in {v['sha256']for v in definition['approved_component_revisions'].values()}:
        raise ValueError('coverage_domain: original source revision unapproved')
    log = root/'compiled-build.log'
    if sha(log)!=binding['compiled_build_log_sha256']: raise ValueError('coverage_domain: original compiled build log changed')
    actions = [s for s in log.read_text().replace('\\ ',' ').splitlines()if s.startswith('SwiftCompile ')and ' '+component['path']+" (in target '"+definition['module']+"' " in s]
    if not actions or actions!=binding['compile_actions']: raise ValueError('coverage_domain: original compile action missing/changed')
    if (provider.get('status')!='conforming' or provider['common_host_shape_sha256']!=approval['common_host_shape_sha256']
            or set(provider['files'])!={'assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift'}):
        raise ValueError('coverage_domain: reviewed host conformance absent')
    for relative,expected in provider['files'].items():
        if relative.startswith('assets/ios-observer/'):
            if sha(root/'tool-sources'/Path(relative).name)!=expected or sha(root/'compiled-project'/Path(relative).name)!=expected:
                raise ValueError('coverage_domain: captured/compiled host changed')
    return {'approval_sha256':value['approval_sha256'],'policy_sha256':value['policy_sha256'],'component_sha256':component['sha256'],
            'provider_sha256':value['provider_sha256'],'scope':approval['scope']}
