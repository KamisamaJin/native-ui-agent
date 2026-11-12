"""Deterministic in-memory HOST controller transcripts, no current run or SDK.

The real filesystem resolver has separate HOST controls. These fixtures exercise
semantic chains with valid outer byte pins, including honest failures and late
outcomes. Only compact control records are written; fixtures reconstruct exactly.
"""
import copy
import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
import unittest

from audit import DOMAIN_SHA, HELPER_SHA, digest, policy, verify_run


def encode(value):
    return (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class MemoryPath:
    def __init__(self, owner, p): self.owner=owner; self.p=PurePosixPath(p)
    def __truediv__(self, other): return MemoryPath(self.owner,self.p/other)
    def __lt__(self, other): return str(self.p)<str(other.p)
    def __eq__(self, other): return isinstance(other,MemoryPath) and self.owner is other.owner and self.p==other.p
    def __hash__(self): return hash((id(self.owner),self.p))
    @property
    def name(self): return self.p.name
    def relative_to(self, other): return self.p.relative_to(other.p)
    def is_file(self): return str(self.p) in self.owner.files
    def is_dir(self): return any(PurePosixPath(p).is_relative_to(self.p) and p!=str(self.p) for p in self.owner.files)
    def read_bytes(self): return self.owner.read_bytes(str(self.p))
    def iterdir(self):
        children=set()
        for raw in self.owner.files:
            p=PurePosixPath(raw)
            if p.is_relative_to(self.p) and p!=self.p:
                children.add(self.p/p.relative_to(self.p).parts[0])
        return iter(MemoryPath(self.owner,p) for p in sorted(children))
    def glob(self, pattern): return (p for p in self.iterdir() if fnmatch.fnmatch(p.name,pattern))
    def rglob(self, pattern):
        nodes=set()
        for raw in self.owner.files:
            p=PurePosixPath(raw)
            if p.is_relative_to(self.p) and p!=self.p:
                nodes.add(p)
                nodes.update(parent for parent in p.parents if parent.is_relative_to(self.p) and parent!=self.p)
        return (MemoryPath(self.owner,p) for p in sorted(nodes) if fnmatch.fnmatch(p.name,pattern))


class MemoryResolver:
    def __init__(self, files):
        self.files=files; self.expected={p:sha(raw) for p,raw in files.items()}; self.accessed=[]
    def read_bytes(self,p):
        p=str(p); self.accessed.append(p)
        raw=self.files[p]
        if sha(raw)!=self.expected[p]: raise ValueError('Synthetic outer byte pin differs')
        return raw
    def read_json(self,p): return json.loads(self.read_bytes(p))
    def hash(self,p): return sha(self.read_bytes(p))
    def file(self,p): self.read_bytes(p); return MemoryPath(self,p)
    def directory(self,p):
        p=PurePosixPath(p); found=[raw for raw in self.files if PurePosixPath(raw).is_relative_to(p)]
        if not found: raise KeyError(str(p))
        for raw in found: self.read_bytes(raw)
        return MemoryPath(self,p)


class Fixture:
    def __init__(self, **options):
        self.options=options; self.files={}; self.events=[]; self.clock=1000.0; self.number=0
        self.base=PurePosixPath('/ORIGINAL/controller-study'); self.root=self.base/'run'; self.sources={}; self.seals={}; self.initial_cohort={}; self.active={}; self.public={}; self.outcomes={}
        protocol=self.put(self.base/'PROTOCOL.json',{'business':{'tasks':5,'repair_budget_minutes':20,'diagnostic_requests_max':2}})
        gate=self.put(self.base/'gate.json',{'passed':True,'business_tasks_may_start':True}); approval=self.put(self.base/'design-approval.json',{'independent':True})
        env=self.put(self.base/'native_envelope.py',b'# synthetic never executed\n'); meter=self.put(self.base/'study_watch.py',b'# synthetic never executed\n')
        spec=self.put(self.base/'meter-spec.json',{'max_total_allocated_bytes':32*2**30,'min_free_bytes':5*2**30})
        tools={}
        self.registry_ref=None
        if options.get('domain_review'):
            registry={'version':1,'kind':'independent-source-domain-review-registry','reviewers':{'reviewer':{'root':str(self.base/'reviewer'),'scope':'source_shape_only'}},'operators':['trusted-operator']}
            self.registry_ref=self.put(self.base/'registry.json',registry)
        for key,api in [('explicit','baseline-explicit-prior'),('pooled','stateful-default')]:
            folder=self.base/'tools'/key
            rows={}
            for rel,raw in [('SKILL.md',b'Synthetic frozen skill\n'),('scripts/ui_loop.py',b'# synthetic never executed\n')]: rows[rel]=self.put(folder/rel,raw)['sha256']
            tools[key]={'skill_root':str(folder),'api':api,'files':rows}
        tasks=[]
        for index in range(5):
            task='Case%02d'%index; arms={}; self.initial_cohort[task]={}
            for alias,tool in [('Left','explicit'),('Right','pooled')]:
                key=(task,alias); source_root=self.base/'live'/task/alias/'src'; resources=self.base/'resources'/task/alias
                initial_approval=None
                if options.get('domain_review'):
                    component=('component-'+task).encode()
                    approval_doc={'shape':'synthetic finite component','platforms':{'ios':{'approved_component_revisions':{'initial':{'sha256':sha(component),'bytes':len(component)}}}}}
                    ref=self.put(self.base/'public'/task/alias/'source-approval.json',approval_doc)
                    initial_approval={'path':ref['path'],'sha256':digest(approval_doc)}
                configs={}; hidden={}
                for profile in ['one','two']:
                    c={'source_roots':[str(source_root)],'resources':{'root':str(resources),'max_simulators':1},'review_store':str(self.base/'public-context'/task/alias/profile/'image'),'source_review_store':str(self.base/'public-context'/task/alias/profile/'source')}
                    if tool=='pooled': c['workflow']={'root':str(self.base/'public-context'/task/alias/'workflow')}
                    if initial_approval: c['coverage_domain_ref']=initial_approval
                    ref=self.put(self.base/'public'/task/alias/(profile+'.json'),c); configs[profile]=ref['path']
                    h=copy.deepcopy(c); h['review_store']=str(self.base/'hidden-context'/task/alias/profile/'image'); h['source_review_store']=str(self.base/'hidden-context'/task/alias/profile/'source')
                    if tool=='pooled': h['workflow']={'root':str(self.base/'hidden-context'/task/alias/'workflow')}
                    if options.get('hidden_reuses_public') and key==('Case04','Right'): h['review_store']=c['review_store']
                    if options.get('hidden_changes_source') and key==('Case04','Right'): h['source_roots']=[str(source_root/'foreign')]
                    ref=self.put(self.base/'hidden-profiles'/task/alias/(profile+'.json'),h); hidden[profile]=ref['path']
                a={'tool':tool,'workspace':str(self.base/'live'/task/alias),'source_roots':[str(source_root)],'resource_roots':[str(resources)],'public_configs':configs,'hidden_configs':hidden,'profile_order':['one','two']}; arms[alias]=a
                raw=('component-'+task).encode()
                if options.get('different_initial') and key==('Case00','Right'): raw+=b'different'
                source=self.snapshot(a,raw,index*2+(alias=='Right')+1); self.sources[key]=source
                capsule=self.capsule(key,'initial',source,raw,corrupt=bool(options.get('bad_capsule') and key==('Case00','Left')))
                self.initial_cohort[task][alias]=capsule
                self.active[key]={p:{'path':v,'sha256':sha(self.files[v])} for p,v in configs.items()}
                self.public[key]={v:sha(self.files[v]) for v in configs.values()}
                if initial_approval: self.public[key][initial_approval['path']]=sha(self.files[initial_approval['path']])
                self.put(self.root/'arms'/task/alias/'public-inputs.json',self.public[key])
            tasks.append({'id':task,'arms':arms})
        self.manifest={'version':1,'study_id':'synthetic-independent-controller','run_root':str(self.root),'protocol':protocol,'speed_gate':gate,'design_approval':approval,'envelope':{'path':env['path'],'sha256':env['sha256'],'meter_path':meter['path'],'meter_sha256':meter['sha256'],'meter_spec_path':spec['path'],'meter_spec_sha256':spec['sha256']},'tools':tools,'tasks':tasks}
        if self.registry_ref: self.manifest['source_domain_reviews']={'registry':self.registry_ref,'max_requests_per_arm':4}
        m=self.put(self.root/'manifest.json',self.manifest); cohort=self.put(self.root/'INITIAL-COHORT.json',self.initial_cohort)
        authority=None
        if self.registry_ref: authority=self.put(self.root/'DOMAIN-AUTHORITY.json',{'registry':self.registry_ref,'identities':{'reviewer':{'path':str(self.base/'reviewer'),'device':1,'inode':99}}})
        self.put(self.root/'INIT.json',{'manifest_sha256':m['sha256'],'initial_cohort_sha256':cohort['sha256'],'helper_sha256':HELPER_SHA,'domain_transport_sha256':DOMAIN_SHA,'domain_authority_sha256':authority['sha256'] if authority else None})
        self.event('initialized',cohort_members=10,no_native_execution=True,no_hidden_open=True)
        if options.get('early_task_admit'):
            for t in tasks: self.event('task_admitted',task=t['id'],arms=list(t['arms']))
        for t in tasks:
            if not options.get('early_task_admit'): self.event('task_admitted',task=t['id'],arms=list(t['arms']))
            for alias,a in t['arms'].items(): self.arm(t['id'],alias,a)
        members={task+'/'+alias:{'path':str(self.root/'arms'/task/alias/'SELF-SEAL.json'),'sha256':sha(self.files[str(self.root/'arms'/task/alias/'SELF-SEAL.json')]),'source_sha256':seal['source_sha256']} for (task,alias),seal in self.seals.items()}
        if options.get('incomplete_cohort'): members.pop('Case04/Right')
        if options.get('early_hidden'): self.event('hidden_authorized',cohort_sha256='00'*32,scope='Invalid premature authorization')
        sealed=self.event('cohort_sealed',members=members); cohort_pin=self.put(self.root/'COHORT-SEAL.json',sealed)
        if not options.get('no_hidden'):
            auth=self.event('hidden_authorized',cohort_sha256=cohort_pin['sha256'],scope='Synthetic one-shot authorization')
            entries={}
            for t in tasks:
                entries[t['id']]={}
                for alias,a in t['arms'].items():
                    entries[t['id']][alias]={}
                    for profile,p in a['hidden_configs'].items():
                        c=json.loads(self.files[p]); roots=[v for v in [c.get('review_store'),c.get('source_review_store'),c.get('workflow',{}).get('root')] if v]
                        entries[t['id']][alias][profile]={'path':p,'sha256':sha(self.files[p]),'context_roots':roots}
            self.event('hidden_contexts_validated',authorization_sequence=auth['sequence'],scope='Synthetic names and recorded declaration')
            self.put(self.root/'HIDDEN-AUTHORIZATION.json',{'authorization':auth,'hidden_configs':entries,'barrier_wait_seconds':{task+'/'+alias:auth['at_unix']-e['at_unix'] for (task,alias),e in self.seals.items()}})
            if options.get('duplicate_hidden'): self.event('hidden_authorized',cohort_sha256=cohort_pin['sha256'],scope='Invalid duplicate')
        if options.get('broken_event_chain'):
            self.events[3]['previous_sha256']='00'*32
            self.put(self.root/'events'/'000003.json',self.events[3])
        if options.get('pre_enqueue_artifact'): self.put(self.root/'requests'/('d'*32)/'request.json',{'scope':'Synthetic pre-enqueue record, never executed'})
        if options.get('unregistered_terminal'): self.put(self.root/'requests'/('d'*32)/'result.json',{'scope':'Invalid unregistered terminal result'})
        self.resolver=MemoryResolver(self.files)

    def put(self,p,value):
        raw=value if isinstance(value,bytes) else encode(value); self.files[str(p)]=raw
        return {'path':str(p),'sha256':sha(raw)}
    def event(self,kind,**data):
        self.clock+=1; e={'sequence':len(self.events),'previous_sha256':sha(self.files[str(self.root/'events'/('%06d.json'%(len(self.events)-1)))]) if self.events else None,'at_clock':self.clock,'at_unix':1700000000+self.clock,'kind':kind,**data}
        self.events.append(e); self.put(self.root/'events'/('%06d.json'%e['sequence']),e); return e
    def snapshot(self,a,raw,inode):
        files={'0/Component.swift':{'sha256':sha(raw),'bytes':len(raw)}}
        return {'roots':[{'path':a['source_roots'][0],'device':1,'inode':inode}],'files':files,'content_sha256':digest(files)}
    def capsule(self,key,kind,source,raw,corrupt=False):
        root=self.root/'arms'/key[0]/key[1]/kind
        self.put(root/'files/0/Component.swift',b'wrong' if corrupt else raw)
        return self.put(root/'source.json',source)
    def readset(self,key,a):
        return {'public_inputs':self.public[key],'tool_files':self.manifest['tools'][a['tool']]['files'],'helper_sha256':HELPER_SHA,'speed_gate':self.manifest['speed_gate'],'design_approval':self.manifest['design_approval'],'domain_transport_sha256':DOMAIN_SHA,'source_domain_registry':self.registry_ref,'active_configs':self.active[key]}
    def ticket(self,key,a,action,source,profiles=None):
        self.number+=1; rid='%032x'%self.number; folder=self.root/'requests'/rid
        req={'task':key[0],'arm':key[1],'request_id':rid,'action':action,'profiles':profiles or a['profile_order'],'source':source,'readset':self.readset(key,a),'active_configs':self.active[key],'supersedes':[],'revision_reason':None}
        self.put(folder/'request.json',req); queued=self.event('request_enqueued',**req)
        started=self.event('request_started',task=key[0],arm=key[1],request_id=rid,queue_wait_seconds=1.0)
        outcomes=[]
        for profile in req['profiles']:
            p=folder/profile; output=p/'service'; status='feedback_complete' if action=='diagnostic' else 'accepted'
            if self.options.get('final_u') and key==('Case00','Left') and action in {'final','finish-review'} and profile=='one': status='not_accepted'
            generated=self.put(output/('completion.json' if action=='finish-review' else 'cycle.json'),{'status':status,'counts':{'unassessed':3 if status=='not_accepted' else 0}})
            resource={'cleanup_errors':[],'remaining_devices':[],'remaining_directories':[]}
            if self.options.get('bad_retirement') and key==('Case00','Left') and action=='final': resource['remaining_devices']=['owned-not-closed']
            self.put(output/'resources.json',resource)
            inventory={raw:sha(data) for raw,data in self.files.items() if PurePosixPath(raw).is_relative_to(output)}
            inv=self.put(p/'original-inventory.json',inventory)
            row={'profile':profile,'action':action,'started_at_unix':1700000000+started['at_clock']+0.01,'finished_at_unix':1700000000+started['at_clock']+0.05,'wall_seconds':0.04,'envelope_record':str(p/'envelope'),'service_output':str(output),'exit_code':0,'service_status':status,'completion' if action=='finish-review' else 'cycle':generated,'inventory':inv,'integrity':{'passed':True,'source_sha256':source['content_sha256'],'readset_sha256':digest(req['readset'])},'accepted':status=='accepted','new_ui_acquisition':action in {'diagnostic','final'}}
            if self.options.get('acquisition_evidence') and action in {'diagnostic','final'}:
                capture_dir=p/'capture'
                capture=self.put(capture_dir/'result.json',{'synthetic':True})
                evidence={'capture_receipt':capture,'execution':self.put(capture_dir/'execution.json',{'synthetic':True}),
                          'native_log':self.put(capture_dir/'native.log',b'SYNTHETIC HOST, NO SDK\n'),
                          'observation':None if self.options.get('absent_observation') else self.put(capture_dir/'native/observation.json',{'synthetic':True}),
                          'scope':'Frozen capture execution identity; absent/failed observation remains a failure or unknown, never acceptance'}
                row.update(capture=capture,acquisition_evidence=evidence)
                if key==('Case00','Left') and profile=='one' and action=='diagnostic':
                    if self.options.get('bad_acquisition_scope'): evidence['scope']='Changed scope'
                    if self.options.get('extra_acquisition_member'): evidence['extra']=capture
                    if self.options.get('missing_acquisition_log'): del self.files[evidence['native_log']['path']]
                    if self.options.get('foreign_acquisition_path'): evidence['execution']=self.put(p/'foreign.json',{'synthetic':True})
                    if self.options.get('bad_acquisition_pin'): evidence['execution']['sha256']='00'*32
                    if self.options.get('different_acquisition_receipt'): evidence['capture_receipt']=self.put(p/'foreign-receipt.json',{'synthetic':True})
            if self.options.get('failed_d0') and key==('Case00','Left') and action=='diagnostic': row.update(exit_code=1,error={'type':'SyntheticNativeFailure','message':'Honest terminal failure'},accepted=False)
            if row.get('error') and not self.options.get('omit_failure_original'): self.put(p/'failure.json',{'error':row['error'],'traceback':'Synthetic original traceback, not actual SDK execution'})
            if self.options.get('wrong_outcome_accepted') and key==('Case00','Left') and action=='diagnostic': row['accepted']=True
            self.put(p/'outcome.json',row); outcomes.append(row)
        result={'task':key[0],'arm':key[1],'request_id':rid,'outcomes':outcomes,'queue_wait_seconds':1.0,'finished_at_clock':started['at_clock']+0.1,'finished_at_unix':1700000000+started['at_clock']+0.1,'service_wall_seconds':0.2,'native_execution_is_not_delivery_acceptance':True}
        result_ref=self.put(folder/'result.json',result)
        first=not any(e['kind']=='d0_result_prepared' and e.get('task')==key[0] and e.get('arm')==key[1] for e in self.events)
        if action=='diagnostic' and first and not (self.options.get('missing_prepared') and key==('Case00','Left')):
            outcome_refs={r['profile']:{'path':str(folder/r['profile']/'outcome.json'),'sha256':sha(self.files[str(folder/r['profile']/'outcome.json')])} for r in outcomes}
            if self.options.get('wrong_prepared_outcome') and key==('Case00','Left'): outcome_refs['one']['sha256']='00'*32
            self.event('d0_result_prepared',task=key[0],arm=key[1],request_id=rid,result_path=result_ref['path'],result_sha256=result_ref['sha256'],outcome_files=outcome_refs,source_sha256=source['content_sha256'],readset_sha256=digest(req['readset']))
        self.event('request_finished',task=key[0],arm=key[1],request_id=rid,result_path=result_ref['path'],result_sha256=result_ref['sha256'])
        self.outcomes.setdefault(key,[]).extend(outcomes)
        return queued,result,result_ref

    def arm(self,task,alias,a):
        key=task,alias; initial=self.sources[key]
        first,result,result_ref=self.ticket(key,a,'diagnostic',initial)
        fields={'deadline_clock':result['finished_at_clock']+1200,'deadline_at_unix':result['finished_at_unix']+1200,'repair_budget_seconds':1200,'d0_request_id':first['request_id'],'d0_finished_at_clock':result['finished_at_clock'],'d0_finished_at_unix':result['finished_at_unix'],'d0_result':result_ref,'d0_source_sha256':initial['content_sha256'],'d0_readset_sha256':digest(first['readset'])}
        if self.options.get('reset_anchor') and key==('Case00','Left'): fields['deadline_clock']+=1; fields['deadline_at_unix']+=1
        anchor=self.event('repair_started',task=task,arm=alias,**fields)
        raw=('component-'+task).encode()
        if self.options.get('different_initial') and key==('Case00','Right'): raw+=b'different'
        final=initial
        if (self.options.get('changed_source') or self.options.get('domain_review')) and key==('Case00','Left'):
            raw+=b' natural patch'; final=self.snapshot(a,raw,initial['roots'][0]['inode'])
        if self.options.get('changed_before_unlock') and key==('Case00','Left'):
            raw+=b' early patch'; final=self.snapshot(a,raw,initial['roots'][0]['inode']); self.ticket(key,a,'review-source',final,['one'])
        self.event('repair_unlocked',task=task,arm=alias,anchor_sequence=anchor['sequence'],deadline_clock=anchor['deadline_clock'],deadline_at_unix=anchor['deadline_at_unix'])
        if self.options.get('domain_review') and key==('Case00','Left'): self.domain_review(key,a,final,raw,anchor)
        for _ in range(2 if self.options.get('third_diagnostic') and key==('Case00','Left') else 0): self.ticket(key,a,'diagnostic',final)
        late=bool(self.options.get('honest_late') and key==('Case00','Left'))
        if late: self.clock=anchor['deadline_clock']+2
        cap=self.capsule(key,'final-source',final,raw)
        self.event('source_locked',task=task,arm=alias,reason='repair_deadline' if late else 'irrevocable_early_seal',source_manifest=cap['path'],source_manifest_sha256=cap['sha256'],source_sha256=final['content_sha256'],source_deadline_compliant=not late,changed_after_deadline=[a['source_roots'][0]+'/Component.swift'] if late else [],deadline_enforcement_lateness_seconds=2.0 if late else 0.0)
        self.ticket(key,a,'final',final)
        final_rows={r['profile']:r for r in self.outcomes[key] if r['action']=='final'}
        for profile in ['one','two']: self.ticket(key,a,'finish-review',final,[profile])
        selected={r['profile']:r for r in self.outcomes[key] if r['action']=='finish-review'}
        retirement={p:{'path':str(PurePosixPath(r['service_output'])/'resources.json'),'sha256':sha(self.files[str(PurePosixPath(r['service_output'])/'resources.json')])} for p,r in final_rows.items()}
        claim=self.put(self.root/'arms'/task/alias/'self-claim.json',{'statement':'Synthetic honest self-claim; independent hidden quality pending'})
        accepted=all(r['accepted'] for r in selected.values()) and not late
        if self.options.get('wrong_public_accepted') and key==('Case00','Left'): accepted=True
        seal=self.event('self_sealed',task=task,arm=alias,source_sha256=final['content_sha256'],active_configs=self.active[key],claim_path=claim['path'],claim_sha256=claim['sha256'],final_outcomes=selected,retirement=retirement,public_service_accepted=accepted,own_delivery_wall_seconds=self.clock+0.5-first['at_clock'],delivery_scope='Synthetic own public wall; no hidden quality claim')
        self.put(self.root/'arms'/task/alias/'SELF-SEAL.json',seal); self.seals[key]=seal

    def domain_review(self,key,a,source,raw,anchor):
        profile='one'; rid='f'*32; folder=self.root/'arms'/key[0]/key[1]/'domain-requests'/rid
        old_ref=copy.deepcopy(self.active[key][profile]); old=json.loads(self.files[old_ref['path']]); approval_ref=old['coverage_domain_ref']; previous=json.loads(self.files[approval_ref['path']])
        component={'path':a['source_roots'][0]+'/Component.swift','sha256':sha(raw),'bytes':len(raw)}
        component_ref=self.put(folder/'component.source',raw)
        req={'version':1,'kind':'source_shape_review_request','request_id':rid,'study_id':self.manifest['study_id'],'task':key[0],'arm':key[1],'profile':profile,'platform':'ios','source':source,'component':component,'component_capsule':component_ref,'active_config':old_ref,'parent_approval':{'path':approval_ref['path'],'sha256':sha(self.files[approval_ref['path']])},'parent_approval_sha256':digest(previous),'policy_sha256':digest(policy(previous)),'readset':self.readset(key,a)}
        request_ref=self.put(folder/'request.json',req)
        request_event=self.event('domain_review_requested',task=key[0],arm=key[1],profile=profile,request_id=rid,request=request_ref)
        proposed=copy.deepcopy(previous); proposed['platforms']['ios']['approved_component_revisions']['reviewed']={'sha256':component['sha256'],'bytes':component['bytes']}
        if self.options.get('domain_policy_change'): proposed['shape']='forbidden policy change'
        if self.options.get('domain_two_revisions'): proposed['platforms']['ios']['approved_component_revisions']['extra']={'sha256':'cd'*32,'bytes':7}
        review_root=self.base/'reviewer'/'delivery'
        record={'version':1,'kind':'independent-source-domain-review','reviewer_id':'reviewer','scope':'source_shape_only','decision':'approved','request_id':rid,'request_sha256':request_ref['sha256'],'study_id':req['study_id'],'task':key[0],'arm':key[1],'profile':profile,'platform':'ios','source_sha256':source['content_sha256'],'component':component,'parent_approval_sha256':req['parent_approval_sha256'],'policy_sha256':req['policy_sha256'],'config_sha256':old_ref['sha256'],'reason':'Synthetic independently bound source-shape review','proposed_approval_sha256':digest(proposed)}
        if self.options.get('domain_wrong_request'): record['request_id']='e'*32
        sealed_files={}
        for name,value in [('review.json',record),('approval.json',proposed),('component.source',raw)]: sealed_files[name]=self.put(review_root/name,value)['sha256']
        seal_ref=self.put(review_root/'SEAL.json',{'version':1,'kind':'source-domain-review-seal','reviewer_id':'reviewer','files':sealed_files})
        provenance={'version':1,'kind':'independent-source-domain-review-provenance','request_id':rid,'review_seal_sha256':seal_ref['sha256'],'reviewer_id':'reviewer','independent_of_repair':True,'operator_id':'trusted-operator','delivery_reference':'SYNTHETIC-INDEPENDENT-DELIVERY'}
        if self.options.get('domain_bad_provenance'): provenance['independent_of_repair']=False
        provenance_ref=self.put(self.base/'operator'/'provenance.json',provenance)
        version=self.root/'arms'/key[0]/key[1]/'config-versions'/rid
        for name,source_path in [('approval.json',review_root/'approval.json'),('review.json',review_root/'review.json'),('review-seal.json',PurePosixPath(seal_ref['path'])),('provenance.json',PurePosixPath(provenance_ref['path'])),('component.source',folder/'component.source')]: self.put(version/name,self.files[str(source_path)])
        new=copy.deepcopy(old); new['coverage_domain_ref']={'path':str(version/'approval.json'),'sha256':digest(proposed)}
        new_ref=self.put(version/'config.json',new); self.put(version/'profile-admission.json',{'status':'synthetic-pure-admission'})
        inventory={PurePosixPath(p).name:sha(data) for p,data in self.files.items() if PurePosixPath(p).is_relative_to(version)}
        self.event('domain_review_admitted',task=key[0],arm=key[1],profile=profile,request_id=rid,request=request_ref,parent_config=old_ref,config=new_ref,component=component,platform='ios',policy_sha256=req['policy_sha256'],revision='reviewed',review_seal=seal_ref,provenance=provenance_ref,files=inventory,review_elapsed_seconds=self.clock+1-request_event['at_clock'],source_deadline_clock=anchor['deadline_clock'],attribution='Synthetic common source-shape transport, no product/quality credit')
        self.active[key][profile]=new_ref


RECORDS=[]


class Controls(unittest.TestCase):
    def check_case(self,expected,**options):
        fixture=Fixture(**options); result=verify_run(fixture.resolver,str(fixture.root),require_hidden_authorization=not options.get('no_hidden'))
        RECORDS.append({'test':self.id(),'options':options,'expected':expected,'actual':result,'deterministic_fixture_file_count':len(fixture.files),'deterministic_fixture_digest':digest({p:sha(raw) for p,raw in fixture.files.items()})})
        self.assertEqual(result['status'],expected,result)
        return fixture,result
    def test_complete_recorded_chain(self):
        _f,r=self.check_case('verified'); self.assertEqual(len(r['arms']),10); self.assertTrue(r['barrier']['hidden_authorized'])
    def test_terminal_failed_d0_still_anchors_original_window(self):
        _f,r=self.check_case('verified',failed_d0=True); self.assertTrue(r['retained_failed_outcomes'])
    def test_failure_traceback_cannot_be_omitted_from_archive(self): self.check_case('failed',failed_d0=True,omit_failure_original=True)
    def test_pre_enqueue_residue_is_retained_without_becoming_execution(self):
        _f,r=self.check_case('verified',pre_enqueue_artifact=True); self.assertEqual(len(r['retained_pre_enqueue_artifacts']),1)
    def test_unregistered_terminal_result_cannot_be_silently_dropped(self): self.check_case('failed',unregistered_terminal=True)
    def test_honest_u_remains_incomplete_without_excluding_attempt(self):
        _f,r=self.check_case('verified',final_u=True); self.assertFalse(r['arms']['Case00/Left']['public_service_accepted'])
    def test_honest_late_source_is_preserved_as_not_accepted(self):
        _f,r=self.check_case('verified',honest_late=True); self.assertTrue(r['late_records']); self.assertFalse(r['arms']['Case00/Left']['public_service_accepted'])
    def test_legitimate_source_patch_within_original_window(self):
        _f,r=self.check_case('verified',changed_source=True); self.assertFalse(r['arms']['Case00/Left']['source_unchanged'])
    def test_pre_hidden_barrier_mode_does_not_open_hidden_bodies(self):
        f,r=self.check_case('verified',no_hidden=True); self.assertFalse(any('/hidden-profiles/' in p for p in f.resolver.accessed))
        self.assertEqual(verify_run(f.resolver,str(f.root))['status'],'failed')
    def test_deadline_reset_rejected(self): self.check_case('failed',reset_anchor=True)
    def test_missing_write_ahead_proof_rejected(self): self.check_case('failed',missing_prepared=True)
    def test_original_outcome_pin_rejected(self): self.check_case('failed',wrong_prepared_outcome=True)
    def test_diagnostic_cap_rejected(self): self.check_case('failed',third_diagnostic=True)
    def test_different_initial_source_rejected(self): self.check_case('failed',different_initial=True)
    def test_source_capsule_bytes_rejected(self): self.check_case('failed',bad_capsule=True)
    def test_source_edit_before_unlock_rejected(self): self.check_case('failed',changed_before_unlock=True)
    def test_incomplete_cohort_rejected_before_hidden_read(self):
        f,_r=self.check_case('failed',incomplete_cohort=True); self.assertFalse(any('/hidden-profiles/' in p for p in f.resolver.accessed))
    def test_duplicate_hidden_authorization_rejected(self): self.check_case('failed',duplicate_hidden=True)
    def test_premature_hidden_authorization_rejected(self): self.check_case('failed',early_hidden=True)
    def test_hidden_public_context_reuse_rejected(self): self.check_case('failed',hidden_reuses_public=True)
    def test_hidden_source_swap_rejected(self): self.check_case('failed',hidden_changes_source=True)
    def test_public_acceptance_cannot_hide_u(self): self.check_case('failed',final_u=True,wrong_public_accepted=True)
    def test_outcome_acceptance_cannot_hide_unsuccessful_status(self): self.check_case('failed',wrong_outcome_accepted=True)
    def test_missing_resource_retirement_rejected(self): self.check_case('failed',bad_retirement=True)
    def test_task_sequential_barrier_rejected(self): self.check_case('failed',early_task_admit=True)
    def test_event_hash_chain_rejected(self): self.check_case('failed',broken_event_chain=True)
    def test_independent_source_domain_append_keeps_original_window(self):
        _f,r=self.check_case('verified',domain_review=True); self.assertEqual(r['domain_admission_count'],1)
    def test_source_domain_policy_change_rejected(self): self.check_case('failed',domain_review=True,domain_policy_change=True)
    def test_source_domain_extra_revision_rejected(self): self.check_case('failed',domain_review=True,domain_two_revisions=True)
    def test_source_domain_foreign_review_request_rejected(self): self.check_case('failed',domain_review=True,domain_wrong_request=True)
    def test_source_domain_nonindependent_provenance_rejected(self): self.check_case('failed',domain_review=True,domain_bad_provenance=True)
    def test_v4_acquisition_evidence_scope_is_metadata(self): self.check_case('verified',acquisition_evidence=True)
    def test_v4_absent_observation_remains_allowed(self): self.check_case('verified',acquisition_evidence=True,absent_observation=True)
    def test_v4_acquisition_scope_not_arbitrary(self): self.check_case('failed',acquisition_evidence=True,bad_acquisition_scope=True)
    def test_v4_acquisition_extra_member_not_ignored(self): self.check_case('failed',acquisition_evidence=True,extra_acquisition_member=True)
    def test_v4_acquisition_log_cannot_be_dropped(self): self.check_case('failed',acquisition_evidence=True,missing_acquisition_log=True)
    def test_v4_acquisition_original_path_is_bound(self): self.check_case('failed',acquisition_evidence=True,foreign_acquisition_path=True)
    def test_v4_acquisition_pin_cannot_change(self): self.check_case('failed',acquisition_evidence=True,bad_acquisition_pin=True)
    def test_v4_acquisition_receipt_is_same_as_outcome(self): self.check_case('failed',acquisition_evidence=True,different_acquisition_receipt=True)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    host=Path(__file__).resolve().parent/'HOST'; host.mkdir(exist_ok=True)
    record={'version':1,'at_unix':time.time(),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'controls':RECORDS,'scope':'Author in-memory deterministic HOST transcripts; no current business run, actual archive/SDK or quality claim. Reconstructable fixture digests retained.'}
    (host/('RESULT-'+str(time.time_ns())+'.json')).write_bytes(encode(record))
    raise SystemExit(not result.wasSuccessful())
