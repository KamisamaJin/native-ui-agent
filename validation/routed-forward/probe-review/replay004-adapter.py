#!/usr/bin/env python3
"""Independent neutral forward replay. All transport packets are SYNTHETIC."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent / 'probe-design'
REPO = HERE.parents[2]
SCRIPTS = Path(os.environ.get('NEUTRAL_PROBE_SCRIPTS', str(REPO / 'native-ui-agent/scripts'))).resolve()
sys.path.insert(0, str(SCRIPTS))
import design_contract as d
import execution_plan as xp
import feedback_loop as loop
import evidence_review as er
import review_contract as review
import requirement_routes as routes
import retest_plan as retest
import native_checks as native
import ax_calibration as ax

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p, value):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');return p
def load(p): return json.loads(Path(p).read_text())
def rows(report): return {r['id']:r for r in report.get('assertions',report.get('rows',[]))}
def pending(report): return sorted(k for k,r in rows(report).items() if k.endswith('/caption-clear') and r['status']=='unassessed')
def failed(report): return [k for k,r in rows(report).items() if r['status']=='failed']

class Lab:
    def __init__(self,root,platform='ios'):
        self.root=Path(root);self.root.mkdir(parents=True);self.platform=platform;self.calls=[];self.serial=0
        self.fix=load(DESIGN/'fixture.json');self.source=self.root/'production/SampleView.swift'
        self.source.parent.mkdir();shutil.copy2(DESIGN/'fixture/SampleView.swift',self.source)
        self.bridge=self.root/'SyntheticBridge.swift';self.bridge.write_text('// Synthetic transport capsule; never launched by a native SDK.\n')
        self.fixtures={'initial':self.fix['inputs'][0],'updates':[self.fix['inputs'][1]]}
        self.actions=[{'type':'checkpoint'},{'type':'apply_next_fixture'},{'type':'checkpoint'}]
        states=[{k:s[k] for k in ['id','input_index','after_action','coverage'] } for s in self.fix['states']]
        states[1]['stimulus_action']=1
        rules=[{'id':'caption-label','kind':'control','target':'caption','property':'label','op':'eq'},
               {'id':'sample-box','kind':'geometry','target':'sample','property':'width','op':'eq','measurement':'accessibility_box'},
               {'id':'caption-clear','kind':'manual','target':'caption','property':'no_overlap','op':'eq','allowed_methods':['visual']}]
        source={'labels':{s['id']:{'value':s['expected_label'],'unit':'string'} for s in self.fix['states']},
                'width':{'ios':{'value':66,'unit':'pt'},'android':{'value':66,'unit':'dp'}},
                'clear':{'value':True,'unit':'bool'},'question':{'value':self.fix['rules'][2]['question'],'unit':'string'},
                'launch':{'fixtures_sha256':d.digest(self.fixtures),'bridge_sha256':sha(self.bridge),'scenario':'paper','platform':platform},
                'obligations':[{'id':f'{s["id"]}/{r["id"]}','clause':f'Paper {s["id"]}: {r["id"]}.','priority':'must','states':[s['id']],
                                'risk':'layout' if r['id']=='sample-box' else 'style' if r['id']=='caption-clear' else 'content'}for s in states for r in rules]}
        values={}
        for r in rules:
            values[r['id']]={}
            for s in states:
                values[r['id']][s['id']]={pl:{'source':'reference','pointer':f'/labels/{s["id"]}' if r['id']=='caption-label' else f'/width/{pl}' if r['id']=='sample-box' else '/clear'}for pl in ['ios','android']}
        put(self.root/'reference.json',source)
        contract={'version':1,'design_owner':'sealed-neutral-probe','approval_reference':'../probe-design/seal.json',
                  'sources':[{'id':'reference','path':'reference.json','sha256':sha(self.root/'reference.json')}],
                  'rules':rules,'required_rule_ids':[r['id'] for r in rules],
                  'scenarios':{'paper':{'states':states,'actions':self.actions,'values':values}}}
        put(self.root/'contract.json',contract);self.lock=d.seal(self.root/'contract.json',self.root);self.lock_sha=d.digest(self.lock)
        self.plan,_=d.compile_contract(self.lock,self.lock_sha,'paper',platform,self.fix['bindings'],self.actions)
        self.policy={'version':1,'design_lock_sha256':self.lock_sha,'approval_reference':'sealed-neutral-probe',
                     'ownership':{'caption':'component'},'atoms':[{'rule_id':'caption-clear','aspect':'overlap','method':'visual','question':{'source':'reference','pointer':'/question'}}]}
        self.route={'version':1,'index':{'source':'reference','pointer':'/obligations'},'routes':{
            o['id']:{'rule_ids':[o['id'].split('/')[1]],'reason':'Direct sealed neutral cell.',
                     'regression_obligations':self.fix['regressions'].get(o['id'],[])}for o in source['obligations']}}
        self.env={'width':90,'height':110,'direction':'ltr','theme':'light',('dynamic_type'if platform=='ios'else'font_scale'):('large'if platform=='ios'else 1.)}
        objs={'plan':self.plan,'design_lock':self.lock,'fixtures':self.fixtures,'policy':self.policy,'routes':self.route,'environment':self.env}
        self.config={k:str(put(self.root/(k+'.json'),v))for k,v in objs.items()}
        self.config.update(design_sha256=self.lock_sha,policy_sha256=d.digest(self.policy),routes_sha256=d.digest(self.route),
                           environment_sha256=d.digest(self.env),bridge=str(self.bridge),source_roots=[str(self.source)],native_options={},
                           launch_ref={'source':'reference','pointer':'/launch'},review_store=str(self.root/'reviews'))
        self.coverage=routes.audit(self.lock,self.lock_sha,self.plan,self.route,d.digest(self.route))
        self.cat=review.catalog(self.plan,self.lock,self.lock_sha,self.policy,d.digest(self.policy),platform)

    def packet(self,selected,*,width=66,label=None,full=True,overlap=False,conflict=None):
        obs={'snapshots':[],'state_captures':[],'steps':[],'execution_scope':'full'if len(selected)==2 else'targeted'}
        if self.platform=='android':obs['configuration']={'direction':'Ltr','font_scale':1.,'night_mode_mask':16}
        for s in self.plan['states']:
            if s['id']not in selected:continue
            state=s['id'];idx=s['input_index'];binding={'fixture_index':idx,'input_sha256':d.digest(self.fix['inputs'][idx]),'event_revision':idx,'instance':'synthetic-paper-process','pid':777}
            indices=[]
            widths=conflict if conflict and state=='reverse' else [width if state=='reverse' else 66]
            for actual_width in widths:
                cap={'identifier':'paper.caption','label':label if label and state=='reverse' else ('Front'if state=='front'else'Reverse'),
                     'intersects_viewport':True,'fully_visible':True,'frame':{'x':24,'y':20,'width':42,'height':8},'node_id':1,'parent_id':-1}
                sample={'identifier':'paper.sample','label':'Sample','intersects_viewport':True,'fully_visible':True,'frame':{'x':12,'y':40,'width':actual_width,'height':44},'node_id':2,'parent_id':-1}
                if self.platform=='android':
                    for n in [cap,sample]:
                        f=n['frame'];n['unclipped_bounds_dp']=[f['x'],f['y'],f['x']+f['width'],f['y']+f['height']]
                        n['native_geometry']={'version':1,'provider':'compose_semantics_int_size','coordinate_unit':'px','density':2.5,'position_px':[f['x']*2.5,f['y']*2.5],'size_px':[int(f['width']*2.5),int(f['height']*2.5)]}
                image='reverse-overlap.png'if overlap and state=='reverse'else state+'.png'
                snap={'state_id':state,'binding':binding,'binding_after_capture':copy.deepcopy(binding),'capture_consistent':True,
                      'nodes':[cap,sample],'screenshot':image,'screenshot_pixels':{'width':180,'height':220},
                      'viewport':{'x':0,'y':0,'width':90,'height':110},'app_frame':{'x':0,'y':0,'width':90,'height':110},
                      'runtime':{'content_frame':{'x':0,'y':0,'width':90,'height':110 if full else 220},
                                 'actual_environment':{'direction':'ltr','theme':'light','dynamic_type':'large'},'provider_build':'synthetic'},
                      'logical_viewport_dp':{'width':90,'height':110},'scroll_offset_dp':0,'scroll_max_dp':0 if full else 110,'viewport_height_dp':110}
                indices.append(len(obs['snapshots']));obs['snapshots'].append(snap)
            obs['state_captures'].append({'state_id':state,'after_action':s['after_action'],'binding':binding,'snapshot_indices':indices,
                                         'top_reached':True,'bottom_reached':full,'stable_binding':True})
        return obs

    def transport(self,*,width=66,label=None,full=True,overlap=False,fail=False):
        def invoke(command,**kwargs):
            native_dir=Path(command[command.index('--output')+1]);native_dir.mkdir(parents=True)
            manifest=load(command[command.index('--fixtures')+1]);selected=[s['state_id']for s in manifest['execution_states']]
            event={'sequence':len(self.calls)+1,'synthetic':True,'command':command,'selected_states':selected,'failure':fail}
            self.calls.append(event);put(self.root/'transport-calls.json',self.calls)
            if not fail:
                obs=self.packet(selected,width=width,label=label,full=full,overlap=overlap)
                put(native_dir/'observation.json',obs)
                for snap in obs['snapshots']:shutil.copy2(DESIGN/'fixture'/snap['screenshot'],native_dir/snap['screenshot'])
            return type('SyntheticNativeResult',(),{'returncode':65 if fail else 0})()
        return patch.object(xp.subprocess,'run',side_effect=invoke)

    def cycle(self,name,**kw):
        transport=kw.pop('transport',{})
        with self.transport(**transport):out=loop.run_cycle(self.config,self.root/name,**kw)
        put(self.root/(name+'-public-return.json'),out);return out

    def initial(self,name='initial',final=True,**transport):
        c=self.cycle(name,final=final,transport=transport)
        return c,Path(c['capture_result']),c['capture_sha256']

    def submission(self,capture,actuals):
        obs=load(capture.parent/'native/observation.json');inds={s['state_id']:i for i,s in enumerate(obs['snapshots'])}
        return {'version':1,'catalog_sha256':d.digest(self.cat),'observation_sha256':sha(capture.parent/'native/observation.json'),
                'decisions':[{'review_id':r['review_id'],'actual':actuals[r['state']],'reason':'Synthetic original schematic: '+('caption clear'if actuals[r['state']]is True else'caption overlaps sample'if actuals[r['state']]is False else'not yet judged'),
                              'snapshot_indices':[inds[r['state']]]}for r in self.cat['rows']if r['state']in actuals]}

    def bind(self,capture,capture_sha,actuals,*,supersedes=(),revision_reason=None):
        self.serial+=1;p=put(self.root/f'submission-{self.serial}.json',self.submission(capture,actuals))
        ref=er.bind(self.config,capture,capture_sha,p,sha(p),self.root/f'reviews/review-{self.serial}',supersedes=supersedes,revision_reason=revision_reason)
        put(self.root/f'review-{self.serial}-public-return.json',ref);return ref

    def evaluated(self,capture,capture_sha):return er.reconstruct(self.config,capture,capture_sha,er.discover(self.config,capture_sha))

    def complete(self,name,cycle,refs=None):
        cpath=Path(cycle['capture_result']).parent.parent/'cycle.json'
        with self.transport():result=loop.complete_review(self.config,cpath,sha(cpath),refs,self.root/name)
        put(self.root/(name+'-public-return.json'),result);return result

def c01(root):
    l=Lab(root);_,cap,h=l.initial();l.bind(cap,h,{'front':True});n=len(l.calls)
    c=l.cycle('after-review',previous=cap,previous_sha=h);p=load(root/'after-review/retest-plan.json');r=load(root/'after-review/review-request.json')
    return {'next_work':'image_review'if any(j['kind']=='review_images'for j in p['jobs'])else p['status'],'sdk_calls':len(l.calls)-n,
            'queued_ids':sorted(v['id']for v in r['rows']),'complete':c['status']=='accepted'}

def c02(root):
    l=Lab(root);_,cap,h=l.initial(overlap=True);ref=l.bind(cap,h,{'front':True,'reverse':False})
    c=l.cycle('failed-review',previous=cap,previous_sha=h);report=load(root/'failed-review/before-evaluated.json');p=load(root/'failed-review/retest-plan.json')
    old=er.discover(l.config,h,all_entries=True)
    l.bind(cap,h,{'reverse':True},supersedes=[ref['sha256']],revision_reason='Synthetic scheduling mutation control; corrected actual, original retained.')
    l.cycle('corrected-review',previous=cap,previous_sha=h);new=load(root/'corrected-review/before-evaluated.json');q=load(root/'corrected-review/retest-plan.json')
    r=rows(report)['reverse/caption-clear']
    return {'first_failed_ids':failed(report),'first_failure_method':r.get('actual',{}).get('method'),'repair_states':p['repair_states'],
            'after_true_review_pending_ids':pending(new),'actual_review_changes_plan':p['status']!=q['status'] and old[0]['sha256']in [x['sha256']for x in er.discover(l.config,h,all_entries=True)]}

def c03(root):
    l=Lab(root);cycle,cap,h=l.initial();n=len(l.calls)
    l.bind(cap,h,{'reverse':True});a=l.complete('one-review',cycle);r1=load(root/'one-review/evaluated.json')
    unknown=l.bind(cap,h,{'front':None});u=l.complete('unknown-review',cycle);ru=load(root/'unknown-review/evaluated.json')
    l.bind(cap,h,{'front':True},supersedes=[unknown['sha256']],revision_reason='Front image inspection now completed; prior unknown retained.')
    b=l.complete('both-reviews',cycle);r2=load(root/'both-reviews/evaluated.json')
    return {'after_one_pending_ids':pending(r1),'after_unknown_pending_ids':pending(ru),'after_both_pending_ids':pending(r2),
            'sdk_calls':len(l.calls)-n,'complete_with_full_coverage':b['status']=='accepted'}

def c04(root):
    credited=[];rejected=[];retained=True
    for variant in ['source','input','image','state_action']:
        l=Lab(root/variant);_,cap,h=l.initial();l.bind(cap,h,{'front':True,'reverse':True})
        archive=l.root/'original';shutil.copytree(cap.parent,archive)
        if variant=='source':l.source.write_text(l.source.read_text()+'// changed source\n')
        if variant=='input':
            f=load(l.config['fixtures']);f['updates'][0]['reverse']=False;put(l.config['fixtures'],f)
        if variant=='image':(cap.parent/'native/reverse.png').write_bytes(b'tampered original image')
        if variant=='state_action':
            op=cap.parent/'native/observation.json';v=load(op);v['state_captures'][1]['after_action']=0;put(op,v)
        try:
            c=l.cycle('stale',previous=cap,previous_sha=h,intake=True)
            if c.get('review_current_source') and c['status']=='feedback_complete':credited.append(variant)
            if c.get('review_current_source')is False and load(l.root/'stale/retest-plan.json')['requires_fresh_capture']:rejected.append(variant)
        except Exception as e:put(l.root/'rejection.json',{'type':type(e).__name__,'message':str(e)});rejected.append(variant)
        retained=retained and sha(archive/'result.json')==h
    return {'variants':['source','input','image','state_action'],'credited_stale_variants':credited,'original_artifacts_retained':retained,'fresh_work_or_explicit_rejection':len(rejected)==4}

def c05(root):
    variants=['duplicate','unknown_id','injected_expectation','injected_unit','injected_status','catalog_digest','observation_digest','bound_rationale','stripped_binding','cross_state_image']
    credited=[];saved=[]
    for variant in variants:
        l=Lab(root/variant);_,cap,h=l.initial();sub=l.submission(cap,{'reverse':True})
        if variant in {'bound_rationale','stripped_binding'}:
            ref=l.bind(cap,h,{'reverse':True});rd=Path(ref['path']).parent;shutil.copytree(rd,l.root/'original-review')
            if variant=='bound_rationale':v=load(rd/'bound-manual.json');v['decisions'][1]['reason']='tampered rationale';put(rd/'bound-manual.json',v)
            else:v=load(ref['path']);v.pop('image_hashes');put(ref['path'],v);ref['sha256']=sha(ref['path'])
            try:er.reconstruct(l.config,cap,h,ref);credited.append(variant)
            except Exception as e:put(l.root/'rejection.json',{'type':type(e).__name__,'message':str(e)})
            saved.append((l.root/'original-review/submission.json').exists());continue
        decision=sub['decisions'][0]
        if variant=='duplicate':sub['decisions'].append(copy.deepcopy(decision))
        elif variant=='unknown_id':decision['review_id']='0'*64
        elif variant.startswith('injected_'):decision[{'injected_expectation':'expected','injected_unit':'unit','injected_status':'status'}[variant]]={'injected_expectation':True,'injected_unit':'bool','injected_status':'passed'}[variant]
        elif variant=='catalog_digest':sub['catalog_sha256']='0'*64
        elif variant=='observation_digest':sub['observation_sha256']='0'*64
        elif variant=='cross_state_image':decision['snapshot_indices']=[0]
        p=put(l.root/'malformed-original.json',sub)
        try:er.bind(l.config,cap,h,p,sha(p),l.root/'reviews/invalid');credited.append(variant)
        except Exception as e:put(l.root/'rejection.json',{'type':type(e).__name__,'message':str(e)})
        saved.append(p.exists())
    return {'variants':variants,'credited_invalid_variants':credited,'errors_counted_as_product_failures':len(credited),'rejected_originals_retained':all(saved)}

def c06(root):
    l=Lab(root);_,cap,h=l.initial(overlap=True);l.bind(cap,h,{'front':True,'reverse':False})
    l.source.write_text(l.source.read_text()+'// fix caption spacing\n')
    target=l.cycle('targeted',previous=cap,previous_sha=h);tc=Path(target['capture_result']);th=target['capture_sha256']
    target_execution=load(tc.parent/'execution.json');target_report=load(root/'targeted/after-evaluated.json');tp=load(root/'targeted/after-dispatch.json')
    l.bind(tc,th,{'reverse':True});l.cycle('targeted-reviewed',previous=tc,previous_sha=th,intake=True)
    before=load(root/'targeted-reviewed/retest-plan.json')
    # A full final cycle is explicitly requested; non-final scheduling is measured
    # separately below so full-final is not inferred from this caller request.
    final=l.cycle('full-final',previous=tc,previous_sha=th,final=True)
    fc=Path(final['capture_result']);fh=final['capture_sha256'];l.bind(fc,fh,{'front':True,'reverse':True});done=l.complete('full-reviewed',final)
    initial_plan=load(root/'targeted/retest-plan.json');owners=[o for o in l.coverage['obligations']if o['id']=='reverse/caption-clear']
    return {'denominator':len(rows(target_report)),'targeted_earns_full':target_execution['scope']=='full',
            'regression_ids':owners[0]['route']['regression_obligations'],
            'missing_full_sweep_scheduled':bool(before['states']) and set(before['states'])=={'front','reverse'},
            'full_sweep_then_review':len(load(root/'full-final/after-review-request.json')['rows'])==2,
            'unrelated_detection_credit':len([i for i in initial_plan['original_failed_ids']if i.startswith('front/')]),
            'complete_before_full_and_review':target['status']=='accepted' or final['status']=='accepted',
            'complete_after_full_and_review':done['status']=='accepted'}

def numeric(l,obs,rule=None):
    if rule is None:
        return native.evaluate(l.plan,obs,l.platform,None,None,None,l.lock,l.lock_sha)['assertions'][4]
    state=copy.deepcopy(l.plan['states'][1]);plan={'version':1,'states':[state],'assertions':[dict(id='diagnostic',state='reverse',**rule)]}
    return native.evaluate(plan,obs,l.platform)['assertions'][0]

def c07(root):
    l=Lab(root/'ios');a=Lab(root/'android','android');obs=l.packet(['reverse']);obs['snapshots'][0]['nodes'][1]['frame'].update(x=1e16,y=1e16)
    ios=numeric(l,obs);android_obs=a.packet(['reverse']);node=android_obs['snapshots'][0]['nodes'][1]
    node['native_geometry'].update(position_px=[825000.,1500000.]);node['unclipped_bounds_dp']=[330000,600000,330065.9999,600043.9999]
    prior=copy.deepcopy(node['unclipped_bounds_dp']);good=numeric(a,android_obs)
    bad_i=numeric(l,l.packet(['reverse'],width=65.75));bad_a=copy.deepcopy(android_obs);bad_a['snapshots'][0]['nodes'][1]['native_geometry']['size_px'][0]=164
    invalid=copy.deepcopy(android_obs);invalid['snapshots'][0]['nodes'][1]['native_geometry']['provider']='invented'
    gap={'kind':'geometry','target':{'identifier':'paper.sample'},'reference_target':{'identifier':'paper.caption'},'property':'gap_y','measurement':'accessibility_box','expected':12,'op':'eq'}
    missing=l.packet(['reverse']);missing['snapshots'][0]['nodes'].pop(0)
    cross=l.packet(['reverse']);other=copy.deepcopy(cross['snapshots'][0]);cross['snapshots'][0]['nodes'].pop(0);other['nodes'].pop(1);cross['snapshots'].append(other);cross['state_captures'][0]['snapshot_indices']=[0,1]
    height={'kind':'geometry','target':{'identifier':'paper.sample'},'property':'height','measurement':'accessibility_box','expected':44,'op':'eq'}
    heights={'ios':numeric(l,obs,height),'android':numeric(a,android_obs,height)}
    put(root/'height-controls.json',heights)
    results={'ios_exact':ios,'android_exact':good,'ios_real_violation':bad_i,'android_real_violation':numeric(a,bad_a),'invalid_packet':numeric(a,invalid),'missing_relation_box':numeric(l,missing,gap),'cross_frame_relation':numeric(l,cross,gap)}
    put(root/'raw-measurements.json',results)
    return {**{k:v['status']for k,v in results.items()},'ios_exact':ios['status']if heights['ios']['status']=='passed'else heights['ios']['status'],
            'android_exact':good['status']if heights['android']['status']=='passed'else heights['android']['status'],
            'threshold':l.plan['assertions'][4]['expected'],'tolerance':l.plan['assertions'][4].get('tolerance',0),'original_rounded_bounds_retained':node['unclipped_bounds_dp']==prior}

def c08(root):
    l=Lab(root);context={'os_version':'synthetic-0','screen_scale':2};fit_rows=[]
    for identifier,split,x,w,h in [('fold-fit','fit',1024,66,44),('fold-hold','heldout',2048,88,55)]:
        frame={'x':x,'y':x,'width':w,'height':h}
        fit_rows.append({'identifier':identifier,'split':split,'eligible_identity_transform_sample':True,'fully_within_viewport':True,
                         'raw_xcui_frame':frame,'reference_bounds':frame,'runtime':dict(context,bounds=frame,accessibility_frame=frame,
                            local_transform_identity=True,ancestor_transforms_identity=True,reference_identity=identifier)})
    extraction={'rows':fit_rows,'sample_split':{'fit':['fold-fit'],'heldout':['fold-hold']}}
    provenance={'synthetic':True,'specification_seal':sha(DESIGN/'seal.json'),'extraction_sha256':d.digest(extraction)}
    profile=ax.fit(extraction,context,provenance);put(root/'synthetic-profile.json',profile)
    # Separate scope controls: external AX geometry has no proved UIKit identity;
    # only the exact independently pinned synthetic probe row has that metadata.
    first=fit_rows[0];measurement={'ratio':[66,1],'property':'width','sources':[{'provider':'xcui_cgrect','sample':first['raw_xcui_frame']}]}
    outside=ax.classify(measurement,66,'eq',0,profile,context)
    pinned=copy.deepcopy(measurement);pinned['sources'][0]['calibration_reference']={'identifier':first['identifier'],'extraction_sha256':d.digest(extraction)}
    inside=ax.classify(pinned,66,'eq',0,profile,context)
    bad=copy.deepcopy(extraction);bad['rows'][0]['runtime']['local_transform_identity']=False
    rejected_profile=ax.fit(bad,context,provenance)
    put(root/'scope-guard-controls.json',{'all_inputs_synthetic':True,'external_unproved_leaf':outside,'exact_pinned_probe_row':inside,
                                        'changed_identity_transform_fit_status':rejected_profile['status'],'changed_identity_transform_rejections':rejected_profile['rejected_rows']})
    reports={}
    for name,kwargs in [('boundary',{'width':65.99999999999999}),('conflict',{'conflict':[65.99999999999999,66.00000000000001]}),('exact',{}),('violation',{'width':65.75})]:
        obs=l.packet(['reverse'],**kwargs);r=native.evaluate(l.plan,obs,'ios',None,None,None,l.lock,l.lock_sha);raw=copy.deepcopy(r)
        annotated=ax.annotate(l.plan,obs,r,profile);put(root/(name+'-raw.json'),raw);put(root/(name+'-annotated.json'),annotated)
        reports[name]=(raw,annotated)
    ar=rows(reports['boundary'][1])['reverse/sample-box'];rt=routes.route_findings(l.coverage,l.plan,reports['boundary'][1],l.packet(['reverse'],width=65.99999999999999))
    dispatch=retest.dispatch(l.coverage,l.plan,reports['boundary'][1],rt,changed_files=[],source_before='a',source_after='a',visual_ids={'front/caption-clear','reverse/caption-clear'})
    put(root/'calibration-dispatch.json',dispatch)
    # Exercise the default loop's actual calibration queue repeatedly. No
    # hard-coded boundedness classification is used by the normalized oracle.
    l.config['calibration']={'path':str(root/'synthetic-profile.json'),'sha256':sha(root/'synthetic-profile.json')}
    _,cap,h=l.initial(width=65.99999999999999);l.bind(cap,h,{'front':True,'reverse':True});history=[];statuses=[]
    for i in range(4):
        cyc=l.cycle(f'calibration-repeat-{i}',previous=cap,previous_sha=h,history=history)
        path=root/f'calibration-repeat-{i}/cycle.json';history.append({'path':str(path),'sha256':sha(path)});statuses.append(cyc['status'])
        if cyc['status'].startswith('blocked'):break
    put(root/'calibration-retry-statuses.json',{'synthetic':True,'statuses':statuses,'transport_calls_total':len(l.calls)})
    return {'boundary_strict_status':rows(reports['boundary'][0])['reverse/sample-box']['status'],'conflicting_status':rows(reports['conflict'][0])['reverse/sample-box']['status'],
            'stable_repeat_exact_status':rows(reports['exact'][0])['reverse/sample-box']['status'],'stable_repeat_violation_status':rows(reports['violation'][0])['reverse/sample-box']['status'],
            'threshold':l.plan['assertions'][4]['expected'],'tolerance':l.plan['assertions'][4].get('tolerance',0),
            'original_statuses_retained':all([r['status']for r in rows(raw).values()]==[r['status']for r in rows(annotated).values()] for raw,annotated in reports.values()),
            'automatic_product_attribution':any(r.get('cause_category')=='product'for _,report in reports.values()for r in rows(report).values()),
            'calibration_bounded':len(statuses)<=3 and statuses[-1].startswith('blocked')}

def c09(root):
    l=Lab(root);_,cap,h=l.initial(width=65.75,label='Back',overlap=True);l.bind(cap,h,{'front':True,'reverse':False});report=l.evaluated(cap,h)
    fails=failed(report);methods=[]
    for key in fails:
        rule=next(r for r in l.plan['assertions']if r['id']==key);row=rows(report)[key]
        methods.append('native_ax'if rule['kind']=='control'and row.get('actual')else'native_bounds'if row.get('geometry_evidence')else row.get('actual',{}).get('method'))
    unsupported=numeric(l,l.packet(['reverse']),{'kind':'geometry','target':{'identifier':'paper.sample'},'property':'width','measurement':'layout_box','expected':66,'op':'eq'})
    # A separate valid positive visual judgment cannot vote away undersize.
    other=Lab(root/'positive-visual');_,oc,oh=other.initial(width=65.75)
    other.bind(oc,oh,{'front':True,'reverse':True});positive=other.evaluated(oc,oh);put(root/'positive-visual-report.json',positive)
    put(root/'mixed-report.json',report);put(root/'unsupported-report.json',unsupported)
    return {'failed_ids':fails,'failed_methods':methods,'unsupported_layout_status':unsupported['status'],
            'visual_override_numeric':rows(positive)['reverse/sample-box']['status']!='failed','denominator':len(rows(report)),
            'state_scope':sorted({rows(report)[k]['state']for k in fails})}

def c10(root):
    l=Lab(root/'acquisition');history=[];attempts=[];previous=None;previous_sha=None
    for i in range(5):
        c=l.cycle(f'attempt-{i}',previous=previous,previous_sha=previous_sha,history=history,transport={'fail':True});attempts.append(c)
        cp=l.root/f'attempt-{i}/cycle.json';history.append({'path':str(cp),'sha256':sha(cp)})
        if c.get('capture_result'):previous=Path(c['capture_result']);previous_sha=c['capture_sha256']
        if c['status'].startswith('blocked'):break
    # Repeated failed image outcomes are independently imported and replanned.
    v=Lab(root/'image-review');_,cap,h=v.initial();last=None;review_attempts=[]
    for i in range(4):
        ref=v.bind(cap,h,{'front':True,'reverse':None},supersedes=[]if last is None else[last['sha256']],revision_reason=None if last is None else'Synthetic repeated review attempt, original remains unjudged.')
        c=v.cycle(f'attempt-{i}',previous=cap,previous_sha=h,history=review_attempts)
        path=v.root/f'attempt-{i}/cycle.json';review_attempts.append({'path':str(path),'sha256':sha(path)});last=ref
        if c['status'].startswith('blocked'):break
    # Additional unchanged-evidence control, separate from the fixed primary
    # per-work-item budget with newly registered honest-unknown reviews.
    u=Lab(root/'unchanged-review');_,uc,uh=u.initial();u.bind(uc,uh,{'front':True,'reverse':None});unchanged=[]
    for i in range(4):
        cyc=u.cycle(f'attempt-{i}',previous=uc,previous_sha=uh,history=unchanged);path=u.root/f'attempt-{i}/cycle.json'
        unchanged.append({'path':str(path),'sha256':sha(path)})
        if cyc['status'].startswith('blocked'):break
    put(root/'retry-summary.json',{'acquisition_statuses':[c['status']for c in attempts],'acquisition_calls':len(l.calls),
                                  'review_statuses':[load(x['path'])['status']for x in review_attempts],
                                  'unchanged_review_statuses':[load(x['path'])['status']for x in unchanged],
                                  'unchanged_review_new_native_calls':len(u.calls)-1})
    lastplan=load(l.root/f'attempt-{len(attempts)-1}/retest-plan.json');before=load(v.root/f'attempt-{len(review_attempts)-1}/before-evaluated.json')
    cap_admission=load(v.root/'initial/admission.json')
    return {'max_attempts_per_work_item':max(len(l.calls),len(review_attempts)),'stops_after_exhaustion':attempts[-1]['status'].startswith('blocked')and load(review_attempts[-1]['path'])['status'].startswith('blocked'),
            'unresolved_retained':len(lastplan['original_unknown_ids'])==6 and pending(before)==['reverse/caption-clear'],
            'all_attempts_retained':all(Path(x['path']).exists()for x in history+review_attempts),
            'threshold':v.plan['assertions'][4]['expected'],'tolerance':v.plan['assertions'][4].get('tolerance',0),
            'complete_with_required_unknown':cap_admission['status']=='accepted','complete_with_required_failure':routes.admission(v.coverage,v.plan,dict(before,assertions=[dict(r,status='failed')if r['id']=='reverse/sample-box'else r for r in before['assertions']]))['status']=='accepted',
            'complete_with_coverage_debt':routes.admission(v.coverage,v.plan,before,execution_scope='targeted')['status']=='accepted'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    seal=load(DESIGN/'seal.json')
    assert all(sha(DESIGN/name)==expected for name,expected in seal['files'].items()),'Original specification changed'
    spec=importlib.util.spec_from_file_location('sealed_neutral_oracle',DESIGN/'oracle.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    funcs=[c01,c02,c03,c04,c05,c06,c07,c08,c09,c10];cases=load(DESIGN/'cases.json')['cases'];results=[]
    for case,fn in zip(cases,funcs):
        try:observed=fn(out/case['id']);error=None
        except Exception as exc:observed={};error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()};put(out/(case['id']+'-exception.json'),error)
        result=oracle.verify(case['id'],observed);result.update(observed=observed,error=error);results.append(result);put(out/'results.json',{'synthetic_transport':True,'real_sdk_stage':'unexecuted','spec_seal_sha256':sha(DESIGN/'seal.json'),'results':results})
        print(json.dumps({'id':case['id'],'status':result['status'],'gaps':len(result['failures']),'error':error and error['message']}),flush=True)
    put(out/'production-input-hashes.json',{str(p.relative_to(REPO)):sha(p)for p in SCRIPTS.glob('*.py')})
    return 0 if all(r['status']=='passed'for r in results)else 1
if __name__=='__main__':raise SystemExit(main())
