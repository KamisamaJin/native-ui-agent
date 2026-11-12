"""HOST files and explicitly SIMULATED compiler receipts, never native proof."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import coverage_domain as domain
import design_contract as d


class CoverageDomainTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.package=self.root/'package';self.source=self.package/'Sources/Widget.swift'
        self.source.parent.mkdir(parents=True);self.source.write_text('public struct ClosedWidget {}\n')
        self.bridge=self.root/'Bridge.swift';self.bridge.write_text('import FixtureModule\n')
        self.fixtures=self.root/'fixtures.json';self.fixtures.write_text('{"initial":{"text":"sample"}}')
        self.lock={'independent':'immutable fixture contract'}
        self.shape={'ios':{'requested_offered_width_pt':32,'viewport_height_pt':120,'theme':'light','direction':'ltr','dynamic_type':'large'}}
        self.encoding=d.load(Path(__file__).resolve().parents[1]/'assets/ios-observer/geometry-encoding.json')
        self.plan={'design_contract':{'platform':'ios','lock_sha256':d.digest(self.lock)},'states':[{'id':'first','coverage':'full_content'}],'assertions':[{'id':'visible'}]}
        self.approval={'version':1,'approved_by':'independent synthetic owner','approved_at_utc':'fixed','scope':'synthetic_closed_component',
            'binds':{'design_lock_sha256':d.digest(self.lock),'required_native_assertions':1,'selected_state_ids':['first'],'full_content_state_ids':['first'],'environment_ios_canonical_sha256':'env'},
            'closed_domain':{'finite':True},'common_host_shape':self.shape,'common_host_shape_sha256':d.digest(self.shape),
            'geometry_encoding':self.encoding,'geometry_encoding_sha256':d.digest(self.encoding),
            'actual_subject_binding':{'component_subject':'widget','bridge_subject':'bridge'},
            'approved_inputs':{'initial':{'platform':'ios','fixture_canonical_sha256':d.digest(d.load(self.fixtures)),
                'fixture_file_sha256':domain.sha(self.fixtures),'launch_bridge_sha256':domain.sha(self.bridge)}},
            'platforms':{'ios':{'component_install_path':'Sources/Widget.swift','product':'FixtureModule','module':'FixtureModule',
                'exact_bridge':{'sha256':domain.sha(self.bridge)},'approved_component_revisions':{'first':{'sha256':domain.sha(self.source),'bytes':self.source.stat().st_size}}}}}
        skill=Path(__file__).resolve().parents[1]
        self.provider={'version':1,'status':'conforming','common_host_shape_sha256':d.digest(self.shape),
                       'files':{rel:domain.sha(skill/rel)for rel in ['assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift']}}
        self.config={'coverage_domain_ref':self.ref('approval.json',self.approval),'coverage_provider_ref':self.ref('provider.json',self.provider),
            'design_sha256':d.digest(self.lock),'environment_sha256':'env','fixtures':str(self.fixtures),'bridge':str(self.bridge),
            'source_roots':[str(self.source.parent)],'native_options':{'package':str(self.package),'product':'FixtureModule'},
            'evidence_subjects':{'widget':[str(self.source)],'bridge':[str(self.bridge)]}}

    def ref(self,name,value):
        p=self.root/name;p.write_text(json.dumps(value));return{'path':str(p),'sha256':d.digest(value)}
    def prepare(self):return domain.prepare(self.config,self.plan,self.lock)

    def test_exact_installed_revision_and_unused_copy_boundary(self):
        value=self.prepare();self.assertEqual(value['component']['sha256'],domain.sha(self.source))
        unused=self.root/'unused.swift';shutil.copy2(self.source,unused)
        self.config['evidence_subjects']['widget']=[str(unused)]
        with self.assertRaisesRegex(ValueError,'Unused/foreign'):self.prepare()

    def test_unapproved_patch_emits_source_review_task_without_being_behavioral_failure(self):
        self.source.write_text('public struct ChangedWidget {}\n')
        with self.assertRaises(domain.DomainReviewRequired)as ctx:self.prepare()
        self.assertEqual(ctx.exception.task['kind'],'review_source_domain')
        self.assertEqual(ctx.exception.task['component']['sha256'],domain.sha(self.source))
        self.assertEqual(ctx.exception.task['status'],'unassessed')

    def test_source_approval_does_not_change_policy_but_scope_edit_does(self):
        old=d.digest(domain.policy(self.approval));revised=copy.deepcopy(self.approval)
        revised['approved_at_utc']='new independent observation';revised['platforms']['ios']['approved_component_revisions']['next']={'sha256':'other','bytes':100}
        self.assertEqual(old,d.digest(domain.policy(revised)))
        revised['closed_domain']['finite']=False;self.assertNotEqual(old,d.digest(domain.policy(revised)))

    def test_missing_provider_files_foreign_design_and_fixture_never_admit(self):
        for mode in ['provider','design','fixture']:
            original=copy.deepcopy(self.config)
            if mode=='provider':
                p=copy.deepcopy(self.provider);p['files']={};self.config['coverage_provider_ref']=self.ref('other-provider.json',p)
            elif mode=='design':self.config['design_sha256']='foreign'
            else:self.fixtures.write_text('{"initial":{"text":"changed"}}')
            with self.assertRaises(ValueError):self.prepare()
            self.config=original

    def packet(self):
        value=self.prepare();parent=self.root/'packet';native=parent/'native';native.mkdir(parents=True)
        source_map={'0/Widget.swift':domain.sha(self.source)}
        for name,v in [('parent-plan.json',self.plan),('source-before.json',source_map),('coverage-domain-prepared.json',value)]:
            (parent/name).write_text(json.dumps(v))
        (parent/'request.json').write_text(json.dumps({'parent_plan_sha256':d.digest(self.plan),'source_sha256':d.digest(source_map),
            'source_roots':[str(self.source.parent)],'input_hashes':{'coverage-domain-prepared.json':domain.sha(parent/'coverage-domain-prepared.json')}}))
        for rel in self.provider['files']:
            for folder in ['tool-sources','compiled-project']:
                target=native/folder/Path(rel).name;target.parent.mkdir(exist_ok=True)
                shutil.copy2(Path(__file__).resolve().parents[1]/rel,target)
        (native/'compiled-build.log').write_text("SwiftCompile normal arm64 "+str(self.source)+" (in target 'FixtureModule' from project 'FixtureModule')\n")
        manifest={'source_hashes':{str(self.source):domain.sha(self.source),str(self.bridge):domain.sha(self.bridge)}}
        return value,native,manifest

    def test_original_compiler_subject_parent_and_actual_host_reconstruct(self):
        value,native,manifest=self.packet();domain.complete(value,manifest,native)
        self.assertEqual(domain.verify_packet(native)['component_sha256'],domain.sha(self.source))
        (native/'compiled-project/ObserverApp.swift').write_text('// unused matching tool-source copy cannot certify another compiled host')
        with self.assertRaisesRegex(ValueError,'compiled host changed'):domain.verify_packet(native)

    def test_no_compile_action_and_late_source_mutation_reject(self):
        value,native,manifest=self.packet()
        (native/'compiled-build.log').write_text('A filename in an informational message is not a native compile action.\n')
        with self.assertRaisesRegex(ValueError,'compile action'):domain.complete(value,manifest,native)
        (native/'compiled-build.log').write_text("SwiftCompile normal arm64 "+str(self.source)+" (in target 'FixtureModule' from project 'FixtureModule')\n")
        self.source.write_text('// changed while SDK work was running\n')
        with self.assertRaisesRegex(ValueError,'changed during'):domain.complete(value,manifest,native)

    def test_actual_runtime_shape_and_scale_cannot_borrow_another_domain(self):
        self.approval['common_host_shape']={'ios':{'requested_offered_width_pt':32,'viewport_height_pt':120,
                                                  'theme':'light','direction':'ltr','dynamic_type':'large'}}
        self.config['coverage_domain_ref']=self.ref('approval.json',self.approval)
        value,native,manifest=self.packet();domain.complete(value,manifest,native)
        vp={'x':0,'y':0,'width':32,'height':120}
        snap={'viewport':vp,'app_frame':vp,'screenshot_pixels':{'width':64,'height':240},
              'runtime':{'viewport':vp,'offered_width':32,'viewport_height':120,'screen_scale':2,'theme':'light','direction':'ltr','dynamic_type':'large',
                         'actual_environment':{'display_scale':2,'theme':'light','direction':'ltr','dynamic_type':'large'}}}
        self.assertEqual(domain.verify_packet(native,[(0,snap)])['runtime_shape_status'],'matched_approved_shape_and_native_scale')
        bad=copy.deepcopy(snap)
        for key in ['viewport','app_frame']:bad[key]={'x':0,'y':0,'width':16,'height':60}
        bad['runtime'].update(viewport=bad['viewport'],offered_width=16,viewport_height=60)
        with self.assertRaisesRegex(ValueError,'viewport differs'):domain.verify_packet(native,[(0,bad)])
        bad=copy.deepcopy(snap);bad['runtime']['screen_scale']=4
        with self.assertRaisesRegex(ValueError,'scale mapping'):domain.verify_packet(native,[(0,bad)])
