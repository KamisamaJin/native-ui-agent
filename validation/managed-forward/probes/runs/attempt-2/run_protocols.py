#!/usr/bin/env python3
"""Sealed neutral validator probes. All native-format records here are synthetic.

No native SDK is invoked. This adapter calls public validators and preserves their
outputs; it does not provide cleanup, prerequisite enforcement or attribution.
"""
import argparse
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
CANDIDATE=PROJECT/'validation/managed-forward/candidate-v12'
SCRIPTS=CANDIDATE/'scripts'
sys.path.insert(0,str(SCRIPTS))
import action_guard as ag
import design_contract as d
import native_checks as nc
import review_contract as rc
import evidence_responsibility as er
import acceptance as ac
import observation_contract as oc
import native_pixels as pixels
from PIL import Image

MODULE_ORIGINS={module.__name__:str(Path(module.__file__).resolve()) for module in [ag,d,nc,rc,er,ac,oc,pixels]}
assert all(Path(path).is_relative_to(CANDIDATE.resolve()) for path in MODULE_ORIGINS.values())

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def identities():
    return {str(p.relative_to(PROJECT)):sha(p) for p in sorted(SCRIPTS.glob('*.py'))}

LOADED_IDENTITIES=identities()
IMPORT_TRIAL=1
while (HERE/('protocol-tool-identity-at-import-'+str(IMPORT_TRIAL)+'.json')).exists():IMPORT_TRIAL+=1
dump(HERE/('protocol-module-origins-'+str(IMPORT_TRIAL)+'.json'),MODULE_ORIGINS)
dump(HERE/('protocol-tool-identity-at-import-'+str(IMPORT_TRIAL)+'.json'),LOADED_IDENTITIES)
for rel in LOADED_IDENTITIES:
    source=PROJECT/rel;destination=HERE/('tool-sources/protocol-start-'+str(IMPORT_TRIAL))/source.relative_to(CANDIDATE)
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)

class Row:
    def __init__(self,cid,variant):
        self.id=cid+'/'+variant;self.cid=cid;self.variant=variant
        slug=cid+'__'+variant;trial=1
        while (HERE/'raw'/slug).exists() or (HERE/'cache'/slug).exists():
            trial+=1;slug=cid+'__'+variant+'__execution-'+str(trial)
        self.raw=HERE/'raw'/slug;self.cache=HERE/'cache'/slug
        self.raw.mkdir();self.cache.mkdir();self.calls=[];self.before=identities();self.started=time.monotonic()
    def call(self,name,fn,*args,**kwargs):
        number=len(self.calls)+1;prefix=self.raw/(str(number).zfill(2)+'-'+name.replace('.','-'))
        before=identities();stdout=io.StringIO();stderr=io.StringIO()
        dump(Path(str(prefix)+'.inputs.json'),{'public_api':name,'args':args,'kwargs':kwargs,
            'synthetic_native_protocol_input':True,'native_SDK_executed':False,'tool_identity_before':before})
        try:
            with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):value=fn(*args,**kwargs)
            result={'ok':True,'value':value}
        except BaseException as error:
            result={'ok':False,'exception_type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc()}
        result.update(public_api=name,tool_identity_before=before,tool_identity_after=identities(),loaded_module_source_identity=LOADED_IDENTITIES)
        dump(Path(str(prefix)+'.output.json'),result)
        Path(str(prefix)+'.stdout').write_text(stdout.getvalue());Path(str(prefix)+'.stderr').write_text(stderr.getvalue())
        self.calls.append({'public_api':name,'input':str(Path(str(prefix)+'.inputs.json')),'output':str(Path(str(prefix)+'.output.json'))})
        return result
    def finish(self,verdict,reason,observations=None):
        after=identities();changed=sorted(k for k in self.before if self.before[k]!=after[k] or self.before[k]!=LOADED_IDENTITIES[k])
        value={'id':self.id,'verdict':verdict,'scope':'synthetic_native_protocol_validator_only',
            'native_SDK_executed':False,'native_capability_or_product_claim':False,
            'reason':reason,'observations':observations or {},'calls':self.calls,
            'tool_identity_before':self.before,'tool_identity_after':after,'changed_tool_paths':changed,
            'candidate_status':'invalid_candidate_changed' if changed else 'frozen_candidate_per_call_identity_stable',
            'candidate_path':str(CANDIDATE),'freeze_manifest_sha256':'40959a3f3fddf55e198cc4a15ab37ea70097220d9e968db191b3fd434ca76349',
            'duration_seconds':time.monotonic()-self.started,'raw_directory':str(self.raw)}
        dump(self.raw/'result.json',value);print(json.dumps({'id':self.id,'verdict':verdict,'reason':reason}),flush=True);return value

def binding(index=0,revision=0):
    return {'fixture_index':index,'input_sha256':hashlib.sha256(('synthetic-input-'+str(index)).encode()).hexdigest(),
            'instance':'synthetic-instance-not-a-native-execution','pid':987654,'event_revision':revision}

def tap_step(action,index=0,before=None,events=None):
    before=copy.deepcopy(before or binding());events=['increment'] if events is None else events
    after=dict(before,event_revision=before['event_revision']+len(events))
    return {'action':copy.deepcopy(action),'outcome':'tapped','state_id':action.get('state_id','s'),
        'dispatch':{'attempted':True,'succeeded':True,'method':'xcui_tap','stimulus':'activation','matches':1,
            'native_controls':1,'enabled':True,'binding_before':before,'event_start':before['event_revision'],'event_end':after['event_revision']},
        'binding_after':after,'callback_delta':[{'event':e,'fixture_index':before['fixture_index']} for e in events],
        'guard':{'protocol':1,'depends_on':action.get('depends_on',[]),'conditions':[],'ready':True,'established':True,'binding':before},
        'before':0,'after':0,'snapshot':0,'immediate_after':0}

def actions_two(independent=False):
    return ag.compile_actions([{'type':'tap','target':{'identifier':'probe.atom'},'state_id':'s','depends_on':[]},
        {'type':'tap','target':{'identifier':'probe.atom'},'state_id':'t','depends_on':[] if independent else [0]}])

def packet(actions,steps):
    return {'probe_protocol_input':'synthetic; not a native observation','guard_protocol':1,'guard_platform':'ios',
            'guard_actions':copy.deepcopy(actions),'steps':steps,'snapshots':[]}

def blocked(step):
    step=copy.deepcopy(step);step['dispatch'].update(attempted=False,succeeded=False)
    step['outcome']='blocked_precondition';step['callback_delta']=[]
    step['binding_after']=copy.deepcopy(step['dispatch']['binding_before'])
    step['guard'].update(ready=False,established=False);return step

def run_d(r):
    v=r.variant;a=actions_two();s0=tap_step(a[0]);s1=tap_step(a[1],1,s0['binding_after']);steps=[s0,s1]
    if (r.cid=='D01' and v=='successful-predicate-chain') or (r.cid=='D04' and v=='callback-predicate-dependency-with-wrong-callback'):
        a[1]['callback_dependencies']=[{'action_index':0,'expected_events':['increment']}]
        a=ag.compile_actions(a);s0=tap_step(a[0]);s1=tap_step(a[1],1,s0['binding_after']);steps=[s0,s1]
    if r.cid=='D08':
        if v=='unknown-dependency':a[1]['depends_on']=[99]
        elif v=='self-dependency':a[1]['depends_on']=[1]
        elif v=='cycle':a[0]['depends_on']=[1]
        elif v=='unknown-predicate':a[0]['preconditions']=[{'target':{'identifier':'probe.atom'},'property':'callback_assertion_passed','op':'eq','expected':True}]
        else:
            a[1]['state_id']=a[0]['state_id']
            out=r.call('observation_contract.validate_actions',oc.validate_actions,a)
            return r.finish('P' if not out['ok'] else 'F','Duplicate native action identity must be rejected before collection',out)
        out=r.call('action_guard.compile_actions',ag.compile_actions,a)
        return r.finish('P' if not out['ok'] else 'F','Invalid prerequisite graph/predicate must be rejected before dispatch',out)
    if r.cid=='D02':
        s0=blocked(s0);s0['outcome']={'A-disabled':'blocked_disabled','A-target-missing':'target_missing','A-target-ambiguous':'target_ambiguous','A-not-attempted':'not_attempted','A-dispatch-exception':'dispatch_error','A-dispatch-timeout':'dispatch_timeout'}[v]
        s1=blocked(s1);steps=[s0,s1]
    if r.cid=='D03':
        if v=='wrong-method':s0['dispatch']['method']='source_review'
        elif v=='wrong-stimulus':s0['dispatch']['stimulus']='caller_update'
        elif v=='outcome-string-only':s0.pop('dispatch')
        elif v=='succeeded-flag-without-attempt':s0['dispatch']['attempted']=False
        else:s0['dispatch']['native_controls']=2
        # Deliberately leave a producer's optimistic B receipt. Consumer replay must still block its credit.
    if r.cid=='D04':
        s0['callback_delta'][0]['event']='different-event'
        out=r.call('native_checks.callback_verdict',nc.callback_verdict,s0,['increment'],'ios')
        replay=r.call('action_guard.verify_observation',ag.verify_observation,a,packet(a,steps),'ios')
        expected=[True,False] if v=='callback-predicate-dependency-with-wrong-callback' else [True,True]
        ok=out['ok'] and out['value']['status']=='failed' and replay['ok'] and [x['established'] for x in replay['value']]==expected
        return r.finish('P' if ok else 'F','Wrong callback stays F; the declared dispatch or callback predicate controls dependency credit',{'expected_established':expected,'callback':out,'guard':replay})
    if r.cid=='D05':
        a[0]['type']='apply_next_fixture';before=binding();after=binding(1,0)
        if v=='caller-update-does-not-advance':after=binding(0,0)
        elif v=='caller-update-jumps-two-inputs':after=binding(2,0)
        elif v=='caller-update-restarts-process':after.update(instance='synthetic-new-instance',pid=987655)
        s0={'action':a[0],'outcome':'updated','state_id':'s','callback_delta':[],
            'dispatch':{'attempted':True,'succeeded':True,'method':'caller_fixture_update','stimulus':'caller_update','binding_before':before,'event_start':0,'event_end':0},
            'binding_after':after,'guard':{'protocol':1,'depends_on':[],'conditions':[],'ready':True,'established':True,'binding':before}}
        s1=tap_step(a[1],1,after);steps=[s0,s1]
    if r.cid=='D06':
        fixture=build(r);obs=fixture['observation'];obs.pop('guard_protocol');obs.pop('guard_actions');obs.pop('guard_platform')
        obs['steps'][0]=blocked(obs['steps'][0]);obs['steps'][0]['binding_after']=obs['snapshots'][0]['binding']
        out=evaluate_fixture(r,fixture,observation=obs)
        if not out['ok']:return r.finish('U','Literal/causal evidence probe setup did not produce a valid report',out)
        statuses={x['id']:x['status'] for x in out['value']['assertions']}
        ok=statuses['s/label']=='passed' and statuses['s/callback']=='unassessed'
        return r.finish('P' if ok else 'F','Independent current fact survives while undispatched callback behavior remains unknown',statuses)
    if r.cid=='D07':
        if v=='other-session-receipt':s0['dispatch']['binding_before']['instance']='synthetic-foreign-session'
        elif v=='old-input-hash':s0['dispatch']['binding_before']['input_sha256']='f'*64
        elif v=='different-PID-instance':s0['dispatch']['binding_before']['pid']=987655
        elif v=='wrong-action-index':
            # Native wire carries the original action object, not a standalone index field.
            s0['action']=copy.deepcopy(a[1])
        elif v=='event-revision-gap':s0['dispatch']['event_end']+=1
        else:
            fixture=build(r);obs=fixture['observation'];obs['snapshots'][0]['binding_after_capture']=binding(0,99)
            out=evaluate_fixture(r,fixture,observation=obs)
            ok=(not out['ok'] and out.get('exception_type')=='ValueError') or (out['ok'] and all(x['status']=='unassessed' for x in out['value']['assertions']))
            return r.finish('P' if ok else 'F','Torn image/state binding withholds causal-state assertion credit',out)
    if r.cid=='D09':
        a=ag.compile_actions([dict(a[0],depends_on=[]),dict(a[1],depends_on=[]),{'type':'tap','target':{'identifier':'probe.atom'},'state_id':'u','depends_on':[0]}])
        s0=blocked(tap_step(a[0]));s1=tap_step(a[1],1,binding());s2=tap_step(a[2],2,s1['binding_after']);steps=[s0,s1,s2]
        out=r.call('action_guard.verify_observation',ag.verify_observation,a,packet(a,steps),'ios')
        ok=out['ok'] and [x['established'] for x in out['value']]==[False,True,False]
        return r.finish('P' if ok else 'F','Independent branch survives; later state does not repair an earlier blocked route',out)
    out=r.call('action_guard.verify_observation',ag.verify_observation,a,packet(a,steps),'ios')
    expected=([True,True] if r.cid=='D01' or (r.cid=='D05' and v=='caller-update-advances-one-input') else [False,False])
    ok=(out['ok'] and [x['established'] for x in out['value']]==expected) or (not out['ok'] and r.cid in {'D03','D07'} and out.get('exception_type')=='ValueError')
    return r.finish('P' if ok else 'F','Consumer replay establishes exactly the supported prerequisite receipts',{'expected_established':expected,'actual':out})

def build(r,owner='component',full=False,pixel_expected='#FF204060',claims=None,bad_na=False):
    inputs=r.cache/'inputs';inputs.mkdir(exist_ok=True)
    source=inputs/'production';source.mkdir(exist_ok=True);subject=source/'Probe.py';subject.write_text("CAPABILITY = 'source-declaration'\n")
    bridge=inputs/'Bridge.py';bridge.write_text('def bridge(): return None\n')
    integration=inputs/'Integration.py';integration.write_text('INTEGRATION_DECLARATION = True\n')
    default_claim={'id':'source-claim','clause':'Probe.py declares CAPABILITY as source-declaration','priority':'must','owner':'component','method':'source','subject':'probe-source','rule_ids':[]}
    reference={'label':{'value':'0','unit':'string'},'selected':{'value':True,'unit':'bool'},'width':{'value':16,'unit':'pt'},
        'font':{'value':16,'unit':'sp'},'events':{'value':['increment'],'unit':'events'},'visual':{'value':True,'unit':'bool'},
        'pixel':{'value':pixel_expected,'unit':'argb'},'question':{'value':'Is the left probe region visible?','unit':'string'},
        'responsibilities':claims if claims is not None else [default_claim]}
    refpath=inputs/'reference.json';dump(refpath,reference)
    rules=[{'id':'label','kind':'control','target':'atom','property':'label'},
        {'id':'selected','kind':'control','target':'atom','property':'selected'},
        {'id':'width','kind':'control','target':'atom','property':'ax_width'},
        {'id':'font','kind':'text_layout','target':'atom','property':'font_sp'},
        {'id':'callback','kind':'event'},
        {'id':'visual','kind':'manual','target':'atom','coverage':'full_content' if full else 'target','allowed_methods':['visual']},
        {'id':'pixel','kind':'manual','target':'atom','coverage':'full_content' if full else 'target','allowed_methods':['native_pixels']}]
    values={rule['id']:{'s':{'ios':{'source':'reference','pointer':'/'+{'callback':'events'}.get(rule['id'],rule['id'])},
        'android':{'source':'reference','pointer':'/'+{'callback':'events'}.get(rule['id'],rule['id'])}}} for rule in rules}
    if bad_na:values['font']['s']={'not_applicable':''}
    logical_actions=[{'type':'tap','target':'atom','state_id':'s','depends_on':[]}]
    contract={'version':1,'design_owner':'independent-neutral-probe-author','approval_reference':'sealed spec r1; protocol fixture only',
        'sources':[{'id':'reference','path':'reference.json','sha256':sha(refpath)}],
        'required_rule_ids':[x['id'] for x in rules],'rules':rules,
        'scenarios':{'neutral':{'states':[{'id':'s','input_index':0,'after_action':0,'coverage':'targets'}],
            'actions':logical_actions,'values':values}}}
    contractpath=inputs/'contract.json';dump(contractpath,contract)
    sealed=r.call('design_contract.seal',d.seal,contractpath,inputs)
    if not sealed['ok']:return {'setup_error':sealed}
    lock=sealed['value'];locksha=d.digest(lock);dump(inputs/'lock.json',lock)
    selector={'identifier':'probe.atom'};base_actions=[dict(logical_actions[0],target=selector)]
    compiled=r.call('design_contract.compile_contract',d.compile_contract,lock,locksha,'neutral','ios',{'atom':selector},base_actions)
    if not compiled['ok']:return {'setup_error':compiled}
    plan,enriched=compiled['value'];dump(inputs/'plan.json',plan)
    policy={'version':1,'design_lock_sha256':locksha,'approval_reference':'sealed neutral protocol policy',
        'ownership':{'atom':owner},'atoms':[{'rule_id':'visual','aspect':'content_presence','method':'visual','question':{'source':'reference','pointer':'/question'}},
        {'rule_id':'pixel','aspect':'rendered_fill','method':'native_pixels','sampling':{'region':[0,0,1,1],'minimum_pixels':16,'minimum_support':1,'channel_tolerance':0,'basis':'semantic','visibility':'fully_visible'}}]}
    policysha=d.digest(policy);dump(inputs/'policy.json',policy)
    image=Image.new('RGB',(64,64),(32,64,96));image.paste((180,200,220),(32,0,64,64));image.save(inputs/'board.png')
    b=binding(0,1);node={'identifier':'probe.atom','label':'0','role_raw':9,'frame':{'x':0,'y':0,'width':16,'height':16},
        'enabled':True,'selected':True,'intersects_viewport':True,'fully_within_viewport':True,'font_sp':16}
    actions=ag.compile_actions(enriched);step=tap_step(actions[0]);step.update(after=0,snapshot=0,immediate_after=0)
    step['observation_set']={'state_id':'s','after_action':0,'binding':b,'binding_after_observation':b,'binding_stable':True,'snapshot_indices':[0]}
    snapshot={'index':0,'state_id':'s','binding':b,'binding_after_capture':b,'capture_consistent':True,'screenshot':'board.png',
        'screenshot_pixels':{'width':64,'height':64},'app_frame':{'x':0,'y':0,'width':64,'height':64},'viewport':{'x':0,'y':0,'width':64,'height':64},
        'runtime':{'content_frame':{'x':0,'y':0,'width':64,'height':128},'actual_environment':{'direction':'ltr','theme':'light','dynamic_type':'large'}},
        'nodes':[node],'control_groups':[{'selector':selector,'match_count':1,'resolution':'unique_native_control','semantic':node,'control':node}]}
    observation=packet(actions,[step]);observation['snapshots']=[snapshot];dump(inputs/'observation.json',observation)
    config={'source_roots':[str(source)],'bridge':str(bridge),'design_sha256':locksha,'design_lock':str(inputs/'lock.json'),'plan':str(inputs/'plan.json'),
        'policy':str(inputs/'policy.json'),'policy_sha256':policysha,
        'responsibility_ref':{'source':'reference','pointer':'/responsibilities'},'source_review_store':str(r.cache/'source-review-store'),
        'evidence_subjects':{'probe-source':[str(subject)],'probe-bridge':[str(bridge)],'probe-integration':[str(integration)]}}
    return {'root':inputs,'plan':plan,'lock':lock,'locksha':locksha,'policy':policy,'policysha':policysha,'observation':observation,'config':config,'subject':subject}

def review_fixture(r,f,observation=None,actual=True,decision=True):
    obs=observation or f['observation'];dump(f['root']/'observation-for-review.json',obs);obssha=sha(f['root']/'observation-for-review.json')
    cat=r.call('review_contract.catalog',rc.catalog,f['plan'],f['lock'],f['locksha'],f['policy'],f['policysha'],'ios')
    if not cat['ok']:return cat
    visual=next(x for x in cat['value']['rows'] if x['requirement_id']=='visual')
    submission={'version':1,'catalog_sha256':d.digest(cat['value']),'observation_sha256':obssha,'decisions':[
        {'review_id':visual['review_id'],'actual':actual,'reason':'Protocol sample observation; no native or product claim','snapshot_indices':[0]}] if decision else []}
    return r.call('review_contract.bind',rc.bind,f['plan'],f['lock'],f['locksha'],f['policy'],f['policysha'],obs,obssha,f['root'],submission,'ios')

def evaluate_fixture(r,f,observation=None,actual=True,decision=True):
    if 'setup_error' in f:return f['setup_error']
    obs=observation or f['observation'];manual=review_fixture(r,f,obs,actual,decision)
    if not manual['ok']:return manual
    return r.call('native_checks.evaluate',nc.evaluate,f['plan'],obs,'ios',manual['value'],f['root'],sha(f['root']/'observation-for-review.json'),
        f['lock'],f['locksha'],f['policy'],f['policysha'])

def statuses(out):return {x['id']:x['status'] for x in out['value']['assertions']} if out['ok'] else {}

def run_e(r):
    v=r.variant
    if r.cid=='E08' and v in {'zero-native-tests','old-image-copied-as-new'}:
        return r.finish('U','No actual SDK capture was run in this task; native test discovery/fresh-image provenance remains for the separately executed native supplement. No fake native runner was used.')
    if r.cid=='E06' and v=='unreasoned-not-applicable':
        f=build(r,bad_na=True);out=f.get('setup_error')
        return r.finish('P' if out and not out['ok'] else 'F','Unreasoned N/A must be rejected before collection',out)
    claims=None
    if r.cid=='E03':
        claims=[{'id':'scoped-visual-claim','clause':'The scoped probe region must satisfy its separately approved visual policy','priority':'must',
                 'owner':{'host-owned-target':'host','system-owned-target':'system','ambiguous-owner':'uncertain'}.get(v,'component'),
                 'method':'visual','subject':'atom','rule_ids':['pixel']}]
    if r.cid=='E08' and v=='method-native-with-source-only':
        claims=[{'id':'native-claim','clause':'A native label claim requires actual native evidence, not source bytes','priority':'must','owner':'component','method':'control','subject':'probe-source','rule_ids':['label']}]
    if r.cid=='E02' and v in {'source-to-runtime-action','source-to-effective-font','rendered-RGB-to-native-computed-style'}:
        claims=[{'id':'unsupported','clause':'Protocol unsupported runtime claim','priority':'must','owner':'component',
            'method':'source' if v=='source-to-runtime-action' else 'computed-style','subject':'probe-source','rule_ids':['callback'] if v=='source-to-runtime-action' else []}]
    f=build(r,owner={'host-owned-target':'host','system-owned-target':'system'}.get(v,'component'),
        full=(r.cid=='E02' and v in {'local-pixels-to-whole-canvas','partial-targets-to-full-page-pass'}) or r.cid=='E05',
        pixel_expected='#FF102030' if r.cid in {'E03','E04'} or (r.cid=='E05' and v=='local-visible-failure-in-incomplete-state') else '#FF204060',claims=claims)
    if 'setup_error' in f:return r.finish('U','Public fixture compilation failed; not a tool pass',f['setup_error'])
    obs=f['observation']
    if r.cid=='E01' and v=='source-declaration-to-nominal-API-claim':
        audit=r.call('evidence_responsibility.compile_contract',er.compile_contract,f['config'],f['plan'],f['lock'])
        submission={'version':1,'observations':[{'id':'source-claim','observed':True,'reason':'Exact source line declares the nominal capability; no runtime claim',
            'citations':[{'path':str(f['subject']),'line':1}]}]}
        bound=r.call('evidence_responsibility.bind',er.bind,f['config'],submission,r.raw/'source-review-receipt.json')
        out=r.call('evidence_responsibility.evaluate',er.evaluate,f['config'],audit['value']) if audit['ok'] and bound['ok'] else bound
        return r.finish('P' if out['ok'] and out['value'].get('status')=='passed' else 'F','Actual source file/line and bound nominal review',out)
    if r.cid=='E01':
        out=evaluate_fixture(r,f);key={'PNG-to-visible-proposition':'visual','PNG-local-pixel-region-to-rendered-RGB':'pixel','bound-AX-to-label':'label',
            'bound-AX-to-selected':'selected','bound-AX-to-AX-dimensions':'width','native-text-layout-to-supported-font-field':'font','successful-native-action-to-callback-interval':'callback'}[v]
        return r.finish('P' if statuses(out).get('s/'+key)=='passed' else 'F','Positive evidence method admitted only at its declared scope',out)
    if r.cid=='E02':
        if claims is not None:
            out=r.call('evidence_responsibility.compile_contract',er.compile_contract,f['config'],f['plan'],f['lock'])
            ok=out['ok'] and bool(out['value']['issues']) and all(not c['supported'] for c in out['value']['claims'])
        elif v in {'screenshot-to-exact-font-size','screenshot-to-internal-padding','AX-frame-to-physical-hit-region'}:
            if v=='screenshot-to-exact-font-size':
                obs['snapshots'][0]['nodes'][0].pop('font_sp');out=evaluate_fixture(r,f);ok=statuses(out).get('s/font')=='unassessed'
            else:
                plain={'version':1,'states':[{'id':'s','input_index':0,'after_action':0,'coverage':'targets'}],
                    'assertions':[{'id':'unsupported','state':'s','kind':'control' if v.startswith('AX') else 'geometry','target':{'identifier':'probe.atom'},
                        'property':'touch_width' if v.startswith('AX') else 'inset_left','expected':16,'measurement':'layout_box',
                        **({} if v.startswith('AX') else {'reference_target':{'identifier':'probe.container'}})}]}
                out=r.call('native_checks.evaluate',nc.evaluate,plain,obs,'ios');ok=out['ok'] and out['value']['assertions'][0]['status']=='unassessed'
        elif v=='AX-label-to-click-delivery':
            obs.pop('guard_protocol');obs.pop('guard_platform');obs.pop('guard_actions');obs['steps'][0]['dispatch']['succeeded']=False
            out=evaluate_fixture(r,f);ss=statuses(out);ok=ss.get('s/label')=='passed' and ss.get('s/callback')=='unassessed'
        else:
            out=evaluate_fixture(r,f);ss=statuses(out);key='pixel' if v=='local-pixels-to-whole-canvas' else 'visual';ok=ss.get('s/'+key)=='unassessed'
        return r.finish('P' if ok else 'F','Broader/unsupported claim must not earn a supported pass',out)
    if r.cid in {'E03','E04'}:
        if r.cid=='E03' and v=='ambiguous-owner':
            responsibility=r.call('evidence_responsibility.compile_contract',er.compile_contract,f['config'],f['plan'],f['lock'])
            f['policy']['ownership']['atom']='uncertain';f['policysha']=d.digest(f['policy'])
            out=r.call('review_contract.catalog',rc.catalog,f['plan'],f['lock'],f['locksha'],f['policy'],f['policysha'],'ios')
            return r.finish('P' if not out['ok'] and not responsibility['ok'] else 'F','Ambiguous responsibility cannot certify a component defect',{'review':out,'responsibility':responsibility})
        measured=evaluate_fixture(r,f);cat=r.call('review_contract.catalog',rc.catalog,f['plan'],f['lock'],f['locksha'],f['policy'],f['policysha'],'ios')
        if not measured['ok'] or not cat['ok']:return r.finish('U','Consensus fixture was not valid',measured)
        responsibility=None
        if r.cid=='E03':
            compiled=r.call('evidence_responsibility.compile_contract',er.compile_contract,f['config'],f['plan'],f['lock'])
            responsibility=r.call('evidence_responsibility.evaluate',er.evaluate,f['config'],compiled['value'],measured['value']) if compiled['ok'] else compiled
            expected_owner=f['policy']['ownership']['atom']
            if not compiled['ok'] or compiled['value']['issues'] or not responsibility['ok'] or responsibility['value']['rows'][0]['owner']!=expected_owner or responsibility['value']['rows'][0]['status']!='failed':
                return r.finish('F','Frozen responsibility provider must preserve the approved owner and original strict fact',{'compiled':compiled,'responsibility':responsibility})
        report=copy.deepcopy(measured['value'])
        # These reports/cause assessments are protocol samples, never actual independent native judgments.
        attrs=[{'s/pixel':{'cause':'product','reason':'synthetic scoped cause sample','snapshot_indices':[0]}},
               {'s/pixel':{'cause':'product','reason':'synthetic scoped cause sample','snapshot_indices':[0]}}]
        if v=='missing-attribution':attrs=[{},{}]
        elif v=='product-versus-infrastructure-disagreement':attrs[1]['s/pixel']['cause']='infrastructure'
        elif v=='both-uncertain':
            for p in attrs:p['s/pixel']['cause']='uncertain'
        out=r.call('acceptance.consensus',ac.consensus,f['plan'],report,measured['value'],measured['value'],cat['value'],{'status':'P'},attrs)
        target=next((x for x in out['value']['rows'] if x['id']=='s/pixel'),{}) if out['ok'] else {}
        expected_cause={'host-owned-target':'infrastructure','system-owned-target':'system','missing-attribution':'uncertain','product-versus-infrastructure-disagreement':'uncertain','both-uncertain':'uncertain'}.get(v,'product')
        ok=target.get('ungated_fact_status')=='failed' and target.get('cause_category')==expected_cause
        return r.finish('P' if ok else 'F','Strict fact and scoped cause remain separate in consensus protocol',{'expected_cause':expected_cause,'actual':out,'responsibility_provider':responsibility})
    if r.cid=='E05':
        out=evaluate_fixture(r,f);ss=statuses(out)
        ok=ss.get('s/pixel')=='failed' if v=='local-visible-failure-in-incomplete-state' else ss.get('s/visual')=='unassessed' and ss.get('s/pixel')=='unassessed'
        return r.finish('P' if ok else 'F','Incomplete coverage withholds full P but retains a directly observed local F',out)
    if r.cid=='E06':
        if v=='visual-present-action-missing':
            obs.pop('guard_protocol');obs.pop('guard_actions');obs.pop('guard_platform');obs['steps'][0]['dispatch']['succeeded']=False
            out=evaluate_fixture(r,f);ss=statuses(out);ok=ss.get('s/visual')=='passed' and ss.get('s/callback')=='unassessed' and len(ss)==7
        elif v=='color-present-font-missing':
            obs['snapshots'][0]['nodes'][0].pop('font_sp');out=evaluate_fixture(r,f);ss=statuses(out);ok=ss.get('s/pixel')=='passed' and ss.get('s/font')=='unassessed' and len(ss)==7
        else:
            plain={'version':1,'states':[{'id':'s','input_index':0,'after_action':0,'coverage':'targets'}, {'id':'missing','input_index':0,'after_action':1,'coverage':'targets'}],
                'assertions':[{'id':'s-label','state':'s','kind':'control','target':{'identifier':'probe.atom'},'property':'label','expected':'0'},
                    {'id':'missing-label','state':'missing','kind':'control','target':{'identifier':'probe.atom'},'property':'label','expected':'0'}], 'required_assertion_ids':['s-label','missing-label']}
            out=r.call('native_checks.evaluate',nc.evaluate,plain,obs,'ios');ss=statuses(out);ok=ss.get('s-label')=='passed' and ss.get('missing-label')=='unassessed' and len(ss)==2
        return r.finish('P' if ok else 'F','Atomic missing aspect/state remains in the denominator',out)
    if r.cid=='E07':
        manual=review_fixture(r,f)
        if not manual['ok']:return r.finish('U','Original review failed before tamper test',manual)
        if v=='changed-responsibility':f['policy']['ownership']['atom']='host'
        elif v=='changed-expected-or-tolerance':f['plan']['assertions'][0]['expected']='rewritten'
        elif v=='changed-target':f['plan']['assertions'][0]['target']={'identifier':'different'}
        elif v=='changed-method':f['policy']['atoms'][0]['method']='native_pixels'
        elif v=='manual-status-override':manual['value']['decisions'][0]['status']='failed'
        if v=='missing-policy-binding':
            out=r.call('native_checks.evaluate',nc.evaluate,f['plan'],obs,'ios',manual['value'],f['root'],sha(f['root']/'observation-for-review.json'),f['lock'],f['locksha'])
        else:
            out=r.call('native_checks.evaluate',nc.evaluate,f['plan'],obs,'ios',manual['value'],f['root'],sha(f['root']/'observation-for-review.json'),f['lock'],f['locksha'],f['policy'],f['policysha'])
        return r.finish('P' if not out['ok'] else 'F','Changed sealed identity/expectation/method/manual verdict must be rejected',out)
    if r.cid=='E08':
        if v=='method-native-with-source-only':
            compiled=r.call('evidence_responsibility.compile_contract',er.compile_contract,f['config'],f['plan'],f['lock'])
            claim=compiled['value']['claims'][0]
            # Actual source evidence is deliberately left unbound; a method label supplies no fact.
            out=r.call('evidence_responsibility.evaluate',er.evaluate,f['config'],compiled['value'])
            ok=out['ok'] and out['value']['rows'][0]['status']=='unassessed'
        elif v=='native-environment-mismatch':
            obs['snapshots'][0]['runtime']['actual_environment']['theme']='dark'
            out=r.call('acceptance.environment',ac.environment,obs,{'width':64,'height':64,'direction':'ltr','theme':'light','dynamic_type':'large'},'ios')
            ok=out['ok'] and out['value']['status']=='F'
        else:
            # A producer complete flag is intentionally inconsistent with actual local geometry.
            step=obs['steps'][0];obs['state_captures']=[{'state_id':'s','after_action':0,'binding':step['binding_after'],'snapshot_indices':[0],
                'top_reached':True,'bottom_reached':True,'stable_binding':True,'complete':True}]
            out=r.call('native_checks.state_evidence',nc.state_evidence,obs,{'id':'s','input_index':0,'after_action':0,'coverage':'full_content'})
            ok=out['ok'] and out['value'][1] is False
        return r.finish('P' if ok else 'F','Self-reported provenance/completeness cannot replace required evidence',out)
    if r.cid=='E09':
        manual=review_fixture(r,f)
        if not manual['ok']:return r.finish('U','Original review failed before artifact mutation',manual)
        original=(f['root']/'board.png').read_bytes();(r.raw/'original-board.png').write_bytes(original)
        if v=='missing-image':(f['root']/'board.png').unlink()
        elif v=='path-escapes-evidence-root':
            outside=r.cache/'outside-board.png';outside.write_bytes(original);obs['snapshots'][0]['screenshot']='../outside-board.png'
        else:Image.new('RGB',(64,64),(10,20,30)).save(f['root']/'board.png')
        out=r.call('native_checks.evaluate',nc.evaluate,f['plan'],obs,'ios',manual['value'],f['root'],sha(f['root']/'observation-for-review.json'),f['lock'],f['locksha'],f['policy'],f['policysha'])
        return r.finish('P' if not out['ok'] else 'F','Actual artifact mutation/missing/outside-root bytes must invalidate old bound evidence',out)
    return r.finish('U','No compatible public mapping without adding missing tool semantics')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only-id',action='append');parser.add_argument('--execution-name',default='protocol-results');args=parser.parse_args()
    cases=json.loads((HERE.parents[1]/'spec/cases.json').read_text());results=[]
    for case in cases['cases']:
        if not case['id'].startswith(('D','E')):continue
        for variant in case['variants']:
            if args.only_id and case['id']+'/'+variant not in args.only_id:continue
            r=Row(case['id'],variant)
            try:out=run_d(r) if r.cid.startswith('D') else run_e(r)
            except BaseException as error:
                dump(r.raw/'harness-error.json',{'type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc()})
                out=r.finish('U','Verifier setup error; preserve original, do not count as tool pass',{'error':str(error)})
            results.append(out);dump(HERE/(args.execution_name+'.partial.json'),results)
    dump(HERE/(args.execution_name+'.json'),results)

if __name__=='__main__':main()
