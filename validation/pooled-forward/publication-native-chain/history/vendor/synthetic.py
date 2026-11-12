"""Self-contained synthetic original-key fixture; all bytes are invented except
the vendored frozen code snapshots. Synthetic image bytes are not native images.
"""
import copy
import json
from pathlib import Path, PurePosixPath
import shutil

import native_chain as nc


HERE = Path(__file__).resolve().parent
ROOT = '/recorded/native-study'


class Fixture:
    def __init__(self, physical, mutation=None, prefix=30, terminal_failure=False):
        self.physical = Path(physical)
        self.files = {}
        self.mutation = mutation
        self.prefix = prefix
        self.terminal_failure = terminal_failure
        self.r = PurePosixPath(ROOT)
        self.ev = self.r / 'cache/business/independent-evaluation'
        self.run = self.r / 'cache/business/run-cohort2'
        self.coord = self.r / 'operators/cohort2/coordination'
        self.configs = {}; self.caps = {}; self.original = {}; self.effective = {}
        self.build()
        self.materialize()

    def edit(self, stage, value):
        if self.mutation and self.mutation[0] == stage:
            self.mutation[1](value)
        return value

    def put(self, original, value):
        original = str(original)
        raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
        self.files[original] = raw
        return {'path': original, 'sha256': nc.sha(raw)}

    def ref(self, original):
        return {'path': str(original), 'sha256': nc.sha(self.files[str(original)])}

    def get(self, original):
        return json.loads(self.files[str(original)])

    def source(self, base, roots):
        content = {'0/Screen.swift': b'synthetic Swift production\n', '1/Screen.kt': b'synthetic Kotlin production\n'}
        value = {'roots': [{'path': root, 'device': 1, 'inode': 20+i} for i, root in enumerate(roots)],
                 'files': {k: {'sha256': nc.sha(v), 'bytes': len(v)} for k,v in content.items()}}
        value['content_sha256'] = nc.digest(value['files'])
        self.edit('capsule:'+str(base), value)
        for name, raw in content.items():
            self.put(base/'files'/name, raw)
        return self.put(base/'source.json', value)

    def resources(self, folder, config, stage):
        token = 'a'*32
        value = {'version':1, 'root':config['resources']['root'], 'owner':{'format':'native-ui-owned-resources-v1',
                 'owner_key':nc.sha(json.dumps(config['source_roots']).encode()), 'token':token},
                 'final':True, 'cleanup_errors':[], 'remaining_directories':[], 'remaining_devices':[]}
        self.edit('resources:'+stage, value)
        journal = {'token':token, 'devices':[], 'directories':[]}
        self.edit('journal:'+stage, journal)
        self.put(folder/'resource-journal.json', journal)
        self.put(folder/'resource-events.jsonl', b'{"kind":"synthetic_positive_close"}\n')
        return self.put(folder/'resources.json', value)

    def entry(self, record, out, version):
        runner = {2:'independent_native.py',3:'independent_native_v2.py',4:'independent_native_v3.py'}[version]
        value = {k:out[k] for k in ['version','kind','task','arm','profile','action','started_at_unix','started_at_monotonic']}
        if version == 4:
            value['started_at_clock_gettime_monotonic'] = out['started_at_clock_gettime_monotonic']
        value['runner'] = {'path':str(self.coord/runner), 'sha256':nc.CODE[runner]}
        value['argv'] = [str(self.coord/runner),'--root',ROOT,'--record',str(record),'--task',out['task'],
                         '--arm',out['arm'],'--profile',out['profile'],'--action','native','--config',out['config']['path']]
        self.edit('entry:'+out['task']+'/'+out['arm']+'/'+out['profile']+':'+str(version), value)
        self.put(record/'ENTRY.json', value)

    def operation(self, key, record, version, start, *, zero=False, preclaim=False, terminal_failure=False):
        task,arm,profile = key.split('/'); cref,capref,config = self.configs[key]
        cap = self.get(capref['path']); ordinary = self.ev / ('native-claims/'+key+'.json')
        if zero or version == 2:
            claim = {'version':1,'task':task,'arm':arm,'profile':profile,'action':'native','record':str(record),
                     'config':cref,'source_capsule':capref,'reserved_at_unix':start+0.1,'scope':nc.CLAIM_SCOPE}
            self.edit('original-claim:'+key, claim)
            claimref = self.put(ordinary,claim)
        elif not preclaim:
            old = self.auth['scopes'][key]['original']
            claim = {'version':1,'task':task,'arm':arm,'profile':profile,'action':'native','record':str(record),
                     'config':cref,'source_capsule':capref,'original_claim':old['original_claim'],'original_outcome':old['original_outcome'],
                     'authority':self.authref,'reserved_at_unix':start+0.1,'scope':nc.CONT_SCOPE}
            if key == 'T1/B/android':
                claim.update(entry_resume_permit=self.permitref,failed_preclaim_entry=self.permit['entry_resume']['failed_record_files']['outcome.json'],
                             licensed_original_record=self.auth['scopes'][key]['record'])
            self.edit('continuation-claim:'+key, claim)
            claimref = self.put(self.ev/('native-continuation-claims/'+key+'.json'),claim)
        out = {'version':version,'kind':'independent-original-fact-operation','task':task,'arm':arm,'profile':profile,'action':'native',
               'started_at_unix':start,'finished_at_unix':start+1,'started_at_monotonic':0.1,'finished_at_monotonic':1.1,'wall_seconds':1.0,
               'config':cref,'source_capsule':capref,'source_before':copy.deepcopy(cap),'source_after':copy.deepcopy(cap),'source_unchanged':True,
               'tool_root':str(self.r/('tools/control' if arm in ['I','A'] else 'tools/candidate')),'accepted':False}
        if arm == 'I':
            out.update(initial_preparation=self.ref(self.r/nc.ANCHORS['initial_preparation']),
                       original_initial_capsule=self.get(self.run/'INITIAL-COHORT.json')[task]['A'])
        if version == 4:
            out.update(started_at_clock_gettime_monotonic=start,finished_at_clock_gettime_monotonic=start+1)
        if preclaim:
            out['error'] = nc.ENTRY_ERROR
            self.entry(record,out,version)
            self.put(record/'failure.json',{'error':nc.ENTRY_ERROR,'traceback':'synthetic original failed preclaim traceback'})
            return self.put(record/'outcome.json',out), None
        out['native_claim'] = self.ref(ordinary)
        if version >= 3:
            old = self.auth['scopes'][key]['original']
            out.update(native_continuation_claim=claimref,original_zero_forwarding_outcome=old['original_outcome'],continuation_authority=self.authref)
        if terminal_failure == 'pre_admission':
            out.update(exit_code=None,error={'type':'ValueError','message':'synthetic recorded failure before profile admission'})
            self.entry(record,out,version)
            self.put(record/'failure.json',{'error':out['error'],'traceback':'synthetic retained early-failure traceback'})
            closure=self.resources(record.parent/'explicit-cleanup-v3/service',config,key+':early-failure-cleanup')
            return self.put(record/'outcome.json',out),closure
        service = record/'service'; env = record/('envelope' if version == 2 else 'envelope-'+nc.sha(str(record).encode()))
        if version >= 3:
            out['envelope_record'] = str(env)
        argv = ['/synthetic/python','-B',out['tool_root']+'/scripts/ui_loop.py','native','--config',cref['path'],'--output',str(service),'--final']
        self.put(record/'command.json',{'argv':argv,'config':cref,'service_output':str(service)})
        source = {k:v['sha256'] for k,v in cap['files'].items()}
        request = {'argv':argv,'config_sha256':cref['sha256'],'source_before':source}
        self.edit('envelope-request:'+key+':'+str(version), request)
        self.put(env/'request.json',request)
        result = copy.deepcopy(request); result.update(source_after=source,source_unchanged=True,exit_code=0,error=None)
        sdk = {'journal_prefixes':[{'path':config['resources']['root']+'/events.jsonl','start_byte':0,'end_byte':0,'prefix_sha256':nc.sha(b'')}],
               'observed_command_records':[]}
        self.edit('sdk:'+key+':'+str(version),sdk)
        self.put(record/'sdk-observation.json',sdk)
        self.put(record/'supervisor.log',b'synthetic supervisor output\n')
        if zero:
            out.update(exit_code=1,service_output=str(service),error={'type':'ValueError','message':'A fresh original native packet was required'})
            result.update(exit_code=None,error=nc.OWNERSHIP_ERROR,recovery={'exit_code':0,'argv':['/synthetic/python','-B',out['tool_root']+'/scripts/resource_manager.py',
                 '--config',cref['path'],'--output',str(env/'error-recovery'),'cleanup']})
            closure = self.resources(env/'error-recovery',config,key+':original')
            self.put(env/'exception.log',b'synthetic original ownership traceback\n');self.put(env/'recovery.log',b'synthetic recovery\n')
            self.put(record/'failure.json',{'error':out['error'],'traceback':'synthetic original failed transport traceback'})
        else:
            self.put(env/'command.log',b'synthetic inner process log\n')
            self.admission(record,cref,config,task,arm,profile)
            out.update(exit_code=0,service_output=str(service),service_status='awaiting_review',capture_reused=False)
            closure = self.resources(service,config,key+':effective'); out['resources'] = closure
            if terminal_failure:
                out.update(exit_code=1,new_ui_acquisition=False,error={'type':'RuntimeError','message':'synthetic original inner transport failed'})
                self.put(record/'failure.json',{'error':out['error'],'traceback':'synthetic terminal native transport traceback'})
            else:
                capture,cycle = self.capture(service,config,cap,profile,key,arm=='B')
                out.update(new_ui_acquisition=True,capture=capture,cycle=cycle)
                if arm == 'B' and profile == 'ios':
                    self.workflow(service,config,out,profile)
            if version == 4:
                proof = {'current_platform_fresh':True,'workflow':'fresh_empty'}
                if arm == 'B' and profile == 'android':
                    sibling = self.get(self.effective[task+'/'+arm+'/ios']['outcome']['path'])
                    workflow = PurePosixPath(config['workflow']['root'])
                    proof = {'current_platform_fresh':True,'workflow':'registered_same_arm_sibling_only',
                             'sibling_native':self.effective[task+'/'+arm+'/ios']['outcome'], 'owner':self.ref(workflow/'owner.json'),
                             'sibling_files':{n:self.ref(workflow/n) for n in ['owner.json','ios.lock','ios.json','ios-backup.json']}}
                self.edit('context:'+key,proof)
                out['fresh_platform_context'] = self.put(record/'fresh-platform-context.json',proof)
            inventory = {p:{'sha256':nc.sha(raw),'bytes':len(raw)} for p,raw in self.files.items() if p.startswith(str(service)+'/')}
            self.edit('inventory:'+key,inventory)
            out['inventory'] = self.put(record/'original-inventory.json',inventory)
        self.put(env/'result.json',result)
        self.edit('outcome:'+key+':'+str(version),out)
        self.entry(record,out,version)
        return self.put(record/'outcome.json',out), closure

    def admission(self, record, cref, config, task, arm, profile):
        hook = self.hook
        inputs = {}
        for key in ['design_lock','plan','policy','routes','environment','fixtures','bridge']:
            ref = self.ref(config[key])
            if key != 'bridge':ref['canonical_sha256'] = nc.digest(self.get(config[key]))
            inputs[key] = ref
        value = {'version':1,'config':{**cref,'canonical_sha256':nc.digest(config)},'platform':profile,
                 'script':self.ref(hook['script']),'approval':{**self.ref(hook['approval']),'canonical_sha256':hook['approval_sha256']},
                 'dependency_files':{p:self.ref(p)['sha256'] for p in [hook['script'],hook['approval']]},'inputs':inputs,
                 'verdict':{'status':'admitted_profile','platform':profile}}
        self.edit('admission:'+task+'/'+arm+'/'+profile,value)
        self.put(record/'profile-admission.json',value)

    def capture(self, service, config, cap, profile, key, selective):
        folder=service/'capture'; roots=config['source_roots']; wanted={k:v['sha256'] for k,v in cap['files'].items()}
        model=None
        if selective:
            model={'version':1,'platform':profile,'source_roots':roots,
                   'groups':{'ios':[roots[0]],'android':[roots[1]],'shared':[]},'indices':[0 if profile=='ios' else 1]}
            self.edit('source-model:'+key,model)
            wanted={k:v for k,v in wanted.items() if int(k.split('/')[0]) in [0 if profile=='ios' else 1]}
            self.put(folder/'source-model.json',model)
        self.put(folder/'source-before.json',wanted); after=copy.deepcopy(wanted); self.edit('source-after:'+key,after)
        self.put(folder/'source-after.json',after)
        plan=self.get(config['plan']);execution={'version':1,'platform':profile,'scope':'full','synthetic':True,
             'parent_plan_sha256':nc.digest(plan),'design_lock_sha256':nc.digest(self.get(config['design_lock'])),
             'fixtures_sha256':nc.digest(self.get(config['fixtures'])),'bridge_sha256':self.ref(config['bridge'])['sha256']}
        self.edit('execution:'+key,execution)
        execution['execution_sha256']=nc.digest(execution)
        self.put(folder/'parent-plan.json',plan);self.put(folder/'execution.json',execution)
        self.put(folder/'fixtures.json',{'synthetic':'fixtures'});self.put(folder/'actions.json',{'synthetic':'actions'})
        self.put(folder/'native.log',b'synthetic recorded SDK log\n')
        self.put(folder/'native/frame.png',('synthetic image for '+key).encode())
        self.put(folder/'native/observation.json',b'{"synthetic_native_actuals":"never graded"}\n')
        self.put(folder/'automatic.json',b'{"synthetic_automatic_actuals":"never graded"}\n')
        tool_raw=b'# synthetic native runtime; never executed\n'
        self.put(folder/'tool-runtime/scripts/ui_loop.py',tool_raw)
        req={'version':1,'source_sha256':nc.digest(wanted),'source_roots':roots,'execution_sha256':execution['execution_sha256'],
             'parent_plan_sha256':nc.digest(plan),'input_hashes':{n:self.ref(folder/n)['sha256'] for n in ['fixtures.json','actions.json']},
             'tool_files':{'scripts/ui_loop.py':nc.sha(tool_raw)}}
        if model is not None:
            req.update(source_model=model,source_model_sha256=nc.digest(model))
            context={'version':2,'platform':profile,'source_model':model,'native_options':config['native_options'],
                     'files':{k:self.ref(config[k])['sha256'] for k in ['plan','design_lock','policy','routes','environment','fixtures','bridge']}}
            self.edit('capture-context:'+key,context)
            self.put(folder/'capture-context.json',context);req['capture_context_sha256']=nc.digest(context)
        self.edit('capture-request:'+key,req)
        self.put(folder/'request.json',req)
        result={**copy.deepcopy(req),'source_unchanged':True,'image_hashes':{'frame.png':self.ref(folder/'native/frame.png')['sha256']},
                'observation_sha256':self.ref(folder/'native/observation.json')['sha256'],'automatic_sha256':self.ref(folder/'automatic.json')['sha256']}
        self.edit('receipt:'+key,result)
        receipt=self.put(folder/'result.json',result)
        cycle={'version':2,'native_executed':True,'capture_reused':False,'capture_result':receipt['path'],'capture_sha256':receipt['sha256']}
        self.edit('cycle:'+key,cycle)
        return receipt,self.put(service/'cycle.json',cycle)

    def workflow(self, service, config, out, profile):
        root=PurePosixPath(config['workflow']['root']);owner=nc.digest(config['source_roots'])
        self.put(root/'owner.json',{'format':'native-ui-workflow-v1','owner':owner,'root_identity':{'device':1,'inode':2}})
        context={'synthetic':'workflow context'};cref=self.put(service/'workflow-context.json',context)
        state={'owner':owner,'platform':profile,'generation':1,'cycles':[{'cycle':out['cycle'],'context_sha256':nc.digest(context)}],
               'capture':{'cycle':out['cycle'],'context_sha256':nc.digest(context),'capture':out['capture'],'context':cref}}
        self.put(service/'workflow-state.json',state)
        state={**state,'generation':3}
        self.put(root/(profile+'.json'),state);self.put(root/(profile+'-backup.json'),state);self.put(root/(profile+'.lock'),b'')

    def episode(self, task, arm, suffix, outcomes):
        base=self.ev/f'episodes/{task}/{arm}'
        if suffix:base=base/suffix
        vals=[self.get(v['outcome']['path']) for v in outcomes.values()]
        start={'task':task,'arm':arm,'started_at_unix':min(v['started_at_unix'] for v in vals),'started_at_monotonic':0.0}
        end={'version':1,'status':'failed' if any(v.get('error') for v in vals) else 'closed','start':self.put(base/'START.json',start),
             'finished_at_unix':max(v['finished_at_unix'] for v in vals)+0.1,'finished_at_monotonic':2.0,'quality_evaluated':False,
             'outcomes':{p:v['outcome'] for p,v in outcomes.items()},'positive_resource_closure':{p:v['closure'] for p,v in outcomes.items()}}
        self.edit('episode:'+task+'/'+arm+('/'+suffix if suffix else ''),end)
        return self.put(base/'END.json',end)

    def build(self):
        for name in nc.CODE:
            target=(self.r/'business-tools-v4' if name in ['blind_study.py','source_domain.py'] else self.coord)/name
            self.put(target,(HERE/'schema-code'/name).read_bytes())
        self.hook={'script':str(self.r/'admission.py'),'approval':str(self.r/'approval.json'),'root':str(self.r/'admission')}
        self.put(self.hook['script'],b'# synthetic recorded admission authority\n')
        self.put(self.hook['approval'],{'synthetic':'recorded profile authority'})
        self.hook['approval_sha256']=nc.digest(self.get(self.hook['approval']))
        frozen_files={'scripts/ui_loop.py':nc.sha(b'# synthetic native runtime; never executed\n')}
        m={'version':1,'tasks':[],'tools':{'control':{'skill_root':str(self.r/'tools/control'),'files':frozen_files},
                                        'candidate':{'skill_root':str(self.r/'tools/candidate'),'files':frozen_files}}}
        initial={}; prep={'version':1,'kind':'canonical-initial-reference-preparation','tasks':{}}
        hidden={'hidden_configs':{}};locks={}; events=[]
        def event(kind,**fields):
            i=len(events);prev=self.ref(self.run/f'events/{i-1:06d}.json')['sha256'] if i else None
            value={'kind':kind,'sequence':i,'previous_sha256':prev,'at_unix':10+i,**fields}
            self.put(self.run/f'events/{i:06d}.json',value);events.append(value);return value
        event('initialized')
        members={}
        for ti in range(1,6):
            task='T'+str(ti);t={'id':task,'arms':{}};initial[task]={};prep['tasks'][task]={};hidden['hidden_configs'][task]={}
            for arm in ['A','B','I']:
                base=self.r/(f'cache/business/initial-reference/{task}' if arm=='I' else f'cache/business/{task}/{arm}')
                roots=[str(base/'workspace/ios'),str(base/'workspace/android')]
                if arm!='I':
                    original=self.source(self.run/f'arms/{task}/{arm}/initial',roots);initial[task][arm]=original
                    capref=self.source(self.run/f'arms/{task}/{arm}/final-source',roots)
                    lock=event('source_locked',task=task,arm=arm,source_manifest=capref['path'],source_manifest_sha256=capref['sha256'],source_sha256=self.get(capref['path'])['content_sha256'])
                    seal=event('self_sealed',task=task,arm=arm,source_sha256=lock['source_sha256'])
                    sref=self.put(self.run/f'arms/{task}/{arm}/SELF-SEAL.json',seal)
                    members[task+'/'+arm]={**sref,'source_sha256':lock['source_sha256']}
                else:
                    # Canonical source does not use a capsule files directory in
                    # the real record; its bytes bind the original A capsule.
                    capref=self.source(base,roots)
                spec={'source_roots':roots,'resource_roots':[],'profile_admissions':{p:self.hook for p in ['ios','android']},'tool':'control' if arm=='A' else 'candidate'}
                hidden['hidden_configs'][task][arm]={}
                for profile in ['ios','android']:
                    contract=base/'contracts'/profile
                    for name in ['design_lock','policy','routes','environment','fixtures']:
                        self.put(contract/(name+'.json'),{'synthetic':name})
                    plan=contract/'plan.json';self.put(plan,{'design_contract':{'platform':profile},'synthetic':'plan'})
                    bridge=contract/'Bridge.source';self.put(bridge,b'synthetic immutable bridge\n')
                    resource=str(base/'resources'/profile);spec['resource_roots'].append(resource)
                    contexts=[str(base/'reviews'/profile/'images'),str(base/'reviews'/profile/'source')]
                    config={'version':1,'platform':profile,'source_roots':roots,'resources':{'root':resource,'max_simulators':1},
                            'plan':str(plan),'bridge':str(bridge),'review_store':contexts[0],'source_review_store':contexts[1],
                            'native_options':{'package' if profile=='ios' else 'project':str(base/'workspace')},
                            **{n:str(contract/(n+'.json')) for n in ['design_lock','policy','routes','environment','fixtures']}}
                    if arm=='B':
                        config.update(platform_source_roots={'ios':[roots[0]],'android':[roots[1]]},workflow={'root':str(base/'workflow')})
                        contexts.append(str(base/'workflow'))
                    self.edit('config:'+task+'/'+arm+'/'+profile,config)
                    cref=self.put(base/('profiles' if arm=='I' else 'hidden-profiles')/(profile+'.json'),config)
                    self.configs[task+'/'+arm+'/'+profile]=(cref,capref,config)
                    if arm=='I':prep['tasks'][task][profile]={'config':cref,'source_manifest':capref,'source_roots':roots,'resource_root':resource}
                    else:hidden['hidden_configs'][task][arm][profile]={**cref,'context_roots':contexts}
                if arm!='I':t['arms'][arm]=spec
                if arm!='I':
                    self.put(self.run/f'arms/{task}/{arm}/public-inputs.json',
                             {p:self.ref(p)['sha256'] for p in [self.hook['script'],self.hook['approval']]})
            hidden['hidden_configs'][task].pop('I')
            m['tasks'].append(t)
        cohort=event('cohort_sealed',members=members);cohortref=self.put(self.run/'COHORT-SEAL.json',cohort)
        auth_event=event('hidden_authorized',cohort_sha256=cohortref['sha256']);hidden['authorization']=auth_event
        event('hidden_contexts_validated',authorization_sequence=auth_event['sequence'])
        self.edit('hidden',hidden)
        self.put(self.run/'manifest.json',m);self.put(self.run/'INITIAL-COHORT.json',initial)
        self.put(self.run/'HIDDEN-AUTHORIZATION.json',hidden);self.put(self.r/nc.ANCHORS['initial_preparation'],prep)
        self.put(self.ev/'INITIAL-PREPARATION-AUTHORITY.json',self.ref(self.r/nc.ANCHORS['initial_preparation']))
        pairs=[('T'+str(i),'I') for i in range(1,6)]+[('T1','A'),('T1','B'),('T2','B'),('T2','A'),('T3','A'),('T3','B'),('T4','B'),('T4','A'),('T5','A'),('T5','B')]
        self.order=[t+'/'+a+'/'+p for t,a in pairs for p in ['ios','android']]
        self.put(self.coord/'POST-PUBLIC-ACQUISITION-ORDER.json',{'episodes':[{'task':t,'scope':a,'profiles':['ios','android']} for t,a in pairs],
                 'cohort_sha256':cohortref['sha256']})
        rows={}
        for i,key in enumerate(self.order):
            rec=self.ev/(key+'/native');out,closure=self.operation(key,rec,2,200+i*3,zero=i>=2)
            self.original[key]={'outcome':out,'closure':closure,'claim':self.ref(self.ev/('native-claims/'+key+'.json'))}
            if i<2:self.effective[key]=self.original[key];continue
            task,arm,profile=key.split('/')
            original={'task':task,'arm':arm,'profile':profile,'original_claim':self.original[key]['claim'],'original_outcome':out,
                      'original_config':self.configs[key][0],'original_source_capsule':self.configs[key][1],
                      'envelope_request':self.ref(rec/'envelope/request.json'),'envelope_result':self.ref(rec/'envelope/result.json'),
                      'positive_recovery_resources':closure,'inner_command_log_absent':True,'service_namespace_absent':True}
            self.edit('zero-index:'+key,original)
            licensed=str(self.ev/('continuations/'+key+'/native'))
            rows[key]={'original':original,'record':licensed,'unique_envelope_leaf':'envelope-'+nc.sha(licensed.encode()),
                       'original_sidecars':{k:self.ref(rec/v) for k,v in nc.SIDECARS.items()}}
        index=self.put(self.coord/'ZERO-FORWARDING-FAILURE-INDEX.json',{'failures':[v['original'] for v in rows.values()]})
        review=self.put(self.coord/'ZERO-FORWARDING-INDEPENDENT-REVIEW.json',{'status':'verified','errors':[],'index':index,
                        'checked':[{**{k:v['original'][k] for k in ['task','arm','profile']},'original_outcome':v['original']['original_outcome']} for v in rows.values()]})
        self.auth={'version':1,'kind':'explicit-single-unforwarded-native-continuation-authority','approval_delivery':{'operator_review_completed':True},
                   'original_runner':{'path':str(self.coord/'independent_native.py'),'sha256':nc.CODE['independent_native.py']},
                   'cohort':cohortref,'hidden_authorization':self.ref(self.run/'HIDDEN-AUTHORIZATION.json'),
                   'initial_preparation':self.ref(self.r/nc.ANCHORS['initial_preparation']),'zero_forwarding_index':index,'independent_review':review,'scopes':rows,
                   'initial_monitor_record':str(self.r/'cache/business/initial-reference-monitor-continuation'),
                   'prior_monitor_positive_closed':self.put(self.r/'cache/business/initial-reference-monitor-actual/CLOSED.json',
                       {'status':'closed','positive_idle':{'all_clear':True},'finished_at_unix':230})}
        self.edit('authority',self.auth)
        self.authref=self.put(self.coord/'UNFORWARDED-CONTINUATION-AUTHORIZATION.json',self.auth)
        self.put(self.ev/'NATIVE-CONTINUATION-AUTHORITY.json',self.authref)
        for i,key in enumerate(self.order[2:13]):
            rec=self.ev/('continuations/'+key+'/native');out,closure=self.operation(key,rec,3,1000+i*3)
            self.effective[key]={'outcome':out,'closure':closure,'claim':self.ref(self.ev/('native-continuation-claims/'+key+'.json'))}
        failed=self.ev/'continuations/T1/B/android/native';self.operation('T1/B/android',failed,3,1100,preclaim=True)
        resumed=str(self.ev/'entry-resumptions/T1/B/android/native')
        self.plan={'version':1,'kind':'remaining-unexecuted-native-scopes-v3','base_authority':self.authref,'entry_resumption_record':resumed,
                   'prior_continuation_acquisitions':[{'scope':key,**{('positive_resources' if k=='closure' else k):v for k,v in self.effective[key].items()}} for key in self.order[2:13]],
                   'remaining':[{'scope':key,'licensed_record':rows[key]['record'],'record':resumed if i==0 else rows[key]['record']} for i,key in enumerate(self.order[13:])]}
        self.edit('plan',self.plan);planref=self.put(self.coord/'REMAINING-NATIVE-SCOPES-v3.json',self.plan)
        placeholders={k:self.put(self.coord/(k+'.json'),{'synthetic':k}) for k in ['diagnosis','independent_review','reviewed_proposal']}
        self.permit={'version':1,'kind':'explicit-unclaimed-pre-forward-entry-admission','operator_review_completed':True,'base_authority':self.authref,
                     'remaining_plan':planref,**placeholders,'entry_resume':{'scope':'T1/B/android','licensed_record':str(failed),'resumed_record':resumed,
                     'failed_record_files':{n:self.ref(failed/n) for n in ['ENTRY.json','outcome.json','failure.json']}}}
        self.edit('permit',self.permit);self.permitref=self.put(self.coord/'UNCLAIMED-ENTRY-v3-ADMISSION.json',self.permit)
        for i,key in enumerate(self.order[13:]):
            rec=PurePosixPath(resumed) if i==0 else self.ev/('continuations/'+key+'/native')
            out,closure=self.operation(key,rec,4,2000+i*3,terminal_failure=self.terminal_failure if i==16 else False)
            self.effective[key]={'outcome':out,'closure':closure,'claim':self.ref(self.ev/('native-continuation-claims/'+key+'.json'))}
        episodes=[];base_episodes=[];v2_episodes=[]
        for t,a in pairs:
            eref=self.episode(t,a,'',{p:self.original[t+'/'+a+'/'+p] for p in ['ios','android']});base_episodes.append({'task':t,'arm':a,'end':eref});episodes.append(eref)
            keys=[k for k in self.order[2:13] if k.split('/')[:2]==[t,a]]
            if keys:
                outcomes={k.split('/')[-1]:self.effective[k] for k in keys}
                if (t,a)==('T1','B'):
                    clean=self.resources(failed.parent/'explicit-cleanup/service',self.configs['T1/B/android'][2],'T1/B/android:preclaim-cleanup')
                    outcomes['android']={'outcome':self.ref(failed/'outcome.json'),'closure':clean}
                eref=self.episode(t,a,'continuation',outcomes);v2_episodes.append({'task':t,'arm':a,'end':eref});episodes.append(eref)
            keys=[k for k in self.order[13:self.prefix] if k.split('/')[:2]==[t,a]]
            if keys:
                episodes.append(self.episode(t,a,'remaining-first-execution-v3',{k.split('/')[-1]:self.effective[k] for k in keys}))
        controls=[]
        for dirname,collector in [('collection-operations','collect_independent.py'),('continuation-collection','collect_independent_v2.py'),('continuation-collection-v3','collect_independent_v3.py')]:
            base=self.ev/dirname
            controls.append(self.put(base/'ENTRY.json',{'collector':{'path':str(self.coord/collector),'sha256':nc.CODE[collector]}}))
            start={'quality_evaluated':False}
            if dirname=='continuation-collection':
                start.update(authority=self.authref,old_collection_end=self.ref(self.ev/'collection-operations/END.json'),
                    original_order=self.ref(self.coord/'POST-PUBLIC-ACQUISITION-ORDER.json'),
                    new_monitor_ready=self.put(self.r/'cache/business/initial-reference-monitor-continuation/READY.json',{'status':'ready'}))
            if dirname=='continuation-collection-v3':
                start.update(authority=self.authref,prior_failed_collection=self.ref(self.ev/'continuation-collection/FAILED.json'),
                    permit=self.permitref,plan=self.ref(self.coord/'REMAINING-NATIVE-SCOPES-v3.json'),
                    initial_monitor_closed=self.put(self.r/'cache/business/initial-reference-monitor-continuation/CLOSED.json',
                         {'status':'closed','positive_idle':{'all_clear':True},'finished_at_unix':1025}))
            controls.append(self.put(base/'START.json',start))
            if dirname=='collection-operations':controls.append(self.put(base/'END.json',{'status':'closed','episodes':base_episodes}))
            if dirname=='continuation-collection':controls.append(self.put(base/'FAILED.json',{'error':nc.ENTRY_ERROR,'traceback':'synthetic retained collector failure','completed':v2_episodes}))
            if dirname=='continuation-collection-v3' and self.prefix==30:
                if self.terminal_failure:
                    controls.append(self.put(base/'FAILED.json',{'error':{'type':'RuntimeError','message':'synthetic final failure'},'traceback':'synthetic failed final collector'}))
                else:
                    controls.append(self.put(base/'END.json',{'status':'closed','first_UI_v3':17,'quality_evaluated':False}))
        snap={'version':1,'kind':'recorded-native-chain-snapshot-v1','original_root':ROOT,'anchors':{k:self.ref(self.r/v) for k,v in nc.ANCHORS.items()},
              'terminal_scopes':self.order[:self.prefix],'pending_scopes':self.order[self.prefix:], 'complete_record_namespace':self.prefix==30,
              'terminal_records':{k:self.effective[k] for k in self.order[:self.prefix]},'episodes':episodes,'collection_controls':controls}
        self.edit('snapshot',snap)
        self.snapshot_ref=self.put('/recorded/native-snapshot.json',snap)
        if self.mutation and self.mutation[0]=='files':self.mutation[1](self.files)

    def materialize(self):
        self.physical.mkdir(parents=True,exist_ok=False)
        for original,raw in self.files.items():
            physical=self.physical/original.lstrip('/');physical.parent.mkdir(parents=True,exist_ok=True);physical.write_bytes(raw)

    def read_bytes(self,original):
        original=str(original)
        if original not in self.files:raise KeyError('Synthetic original absent: '+original)
        return (self.physical/original.lstrip('/')).read_bytes()

    def read_json(self,original):return nc.strict_json(self.read_bytes(original))
    def hash(self,original):return nc.sha(self.read_bytes(original))
    def directory(self,original):
        prefix=str(original).rstrip('/')+'/'
        if not any(k.startswith(prefix) for k in self.files):raise KeyError('Synthetic directory absent: '+str(original))
        return self.physical/str(original).lstrip('/')

    def restore(self,folder):
        """Build a real frozen-Resolver virtual restore with no original files."""
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);namespace=folder/'files';namespace.mkdir()
        mappings={}
        for original,raw in self.files.items():
            logical=original.lstrip('/');physical=namespace/logical;physical.parent.mkdir(parents=True,exist_ok=True);physical.write_bytes(raw)
            mappings[original]={'physical_path':str(physical),'logical_path':logical,'sha256':nc.sha(raw),'bytes':len(raw),
                                'original_mode':'0644','restored_mode':'0644'}
        index=nc.sha(b'synthetic externally pinned index')
        value={'format':'explicit-file-lossless-v1','version':1,'index_sha256':index,'namespace':str(namespace),
               'mappings':mappings,'scope':'Synthetic only; no actual archive or native execution.'}
        mapping=folder/'RESTORED-MAP.json';mapping.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
        return mapping,nc.sha(mapping.read_bytes()),index
