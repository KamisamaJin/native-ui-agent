"""Synthetic hostile controls for raw historical preservation and reader view."""
import copy
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
import time
import unittest

import checkpoint as cp
import history_view as hv


HERE=Path(__file__).resolve().parent
RUN=HERE/'HOST'/('synthetic-'+str(time.time_ns()));RUN.mkdir(parents=True,exist_ok=False)
for name in ['history_view.py','checkpoint.py','test_history.py']:(RUN/name).write_bytes((HERE/name).read_bytes())
RESULTS=[]
ROOT='/recorded/native-study'


class Synthetic:
    def __init__(self, directory, pending=False):
        self.physical=Path(directory);self.physical.mkdir(parents=True,exist_ok=False)
        self.files={};self.reads=[];self.block_workflows=False
        for scope in hv.EXPECTED_SCOPES:
            if pending and scope=='T5/B/android':continue
            task,arm,profile=scope.split('/');record=PurePosixPath(ROOT)/('cache/business/independent-evaluation/continuations/'+scope+'/native')
            claim={'version':1,'task':task,'arm':arm,'profile':profile,'action':'native','record':str(record)}
            self.put(PurePosixPath(ROOT)/('cache/business/independent-evaluation/native-continuation-claims/'+scope+'.json'),claim)
            refs={}
            for name in ['owner.json','ios.lock','ios.json','ios-backup.json']:
                raw=b'' if name.endswith('.lock') else (json.dumps({'synthetic':task,'file':name},indent=2)+'\n').encode()
                original=str(hv.workflow_root(ROOT,task)/name);self.put(original,raw);refs[name]={'path':original,'sha256':hv.sha(raw)}
            proof={'current_platform_fresh':True,'workflow':'registered_same_arm_sibling_only','owner':refs['owner.json'],'sibling_files':refs}
            self.put(record/'fresh-platform-context.json',proof)
        self.put(PurePosixPath(ROOT)/'ordinary/untouched.txt',b'unchanged non-workflow bytes\n')

    def put(self,original,value):
        original=str(original);raw=value if isinstance(value,bytes) else (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
        self.files[original]=raw
        physical=self.physical/original.lstrip('/');physical.parent.mkdir(parents=True,exist_ok=True);physical.write_bytes(raw)
        return {'path':original,'sha256':hv.sha(raw)}

    def ref(self,original):return {'path':str(original),'sha256':hv.sha(self.files[str(original)])}
    def read_bytes(self,original):
        original=str(original);self.reads.append(original)
        if self.block_workflows and '/hidden-workflow/' in original:raise AssertionError('Mutable original workflow bytes were read')
        if original not in self.files:raise KeyError('Synthetic original absent: '+original)
        return self.files[original]
    def read_json(self,original):return hv.strict_json(self.read_bytes(original))
    def hash(self,original):return hv.sha(self.read_bytes(original))
    def directory(self,original):
        out=self.physical/str(original).lstrip('/')
        if not out.is_dir():raise KeyError('Synthetic directory absent')
        return out
    def observe(self,original):
        original=str(original);raw=self.read_bytes(original);p=self.physical/original.lstrip('/');s=p.stat()
        identity={'device':s.st_dev,'inode':s.st_ino,'bytes':len(raw),'mode':s.st_mode,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
        return raw,{'original_path':original,'sha256':hv.sha(raw),'stable_read':True,'identity_before':identity,'identity_after':dict(identity),
                    'read_started_at_unix':1.0,'read_finished_at_unix':2.0,'observation_scope':'Synthetic mapped originals only.'}
    def add_checkpoint(self,path):
        for p in Path(path).rglob('*'):
            if p.is_file():self.files[str(p)]=p.read_bytes()
    def restore(self,folder):
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);namespace=folder/'files';namespace.mkdir();mappings={}
        for original,raw in self.files.items():
            logical=original.lstrip('/');p=namespace/logical;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            mappings[original]={'physical_path':str(p),'logical_path':logical,'sha256':hv.sha(raw),'bytes':len(raw),'original_mode':'0644','restored_mode':'0644'}
        index=hv.sha(b'synthetic externally pinned history archive index')
        value={'format':'explicit-file-lossless-v1','version':1,'index_sha256':index,'namespace':str(namespace),'mappings':mappings,'scope':'Synthetic history only.'}
        mapping=folder/'RESTORED-MAP.json';mapping.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
        return mapping,hv.sha(mapping.read_bytes()),index


class Controls(unittest.TestCase):
    def setup_fixture(self,pending=False):
        label=self.id().rsplit('.',1)[-1];f=Synthetic(RUN/label/'originals',pending=pending)
        ref,value=cp.create_checkpoint(f,ROOT,RUN/label/'checkpoint');f.add_checkpoint(Path(ref['path']).parent)
        return f,ref,value

    def reject(self,fn,message):
        with self.assertRaisesRegex((ValueError,KeyError,OSError),message):fn()
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True,'expected_rejection':message})

    def reseal(self,f,ref,value):
        raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode();f.files[ref['path']]=raw
        return {**ref,'sha256':hv.sha(raw),'bytes':len(raw)}

    def test_01_complete_raw_checkpoint(self):
        f,ref,v=self.setup_fixture();self.assertEqual(v['status'],'complete');self.assertEqual(len(v['versions']),20)
        reader=hv.HistoryReader(f,ref)
        for row in v['versions']:
            self.assertEqual(reader.read_bytes(row['original_path']),f.files[row['copy']['path']])
            self.assertEqual((Path(row['copy']['path']).stat().st_mode&0o777),0o444)
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True,'ledger':ref,'preserved_versions':20})

    def test_02_later_current_bytes_never_read(self):
        f,ref,v=self.setup_fixture()
        for row in v['versions']:f.files[row['original_path']]=b'final changed workflow bytes'
        f.block_workflows=True;f.reads=[];reader=hv.HistoryReader(f,ref)
        for row in v['versions']:self.assertEqual(reader.hash(row['original_path']),row['required_sha256'])
        self.assertFalse(any('/hidden-workflow/' in p for p in f.reads))
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True,'mutable_workflow_reads':0})

    def test_03_missing_copy_has_no_current_fallback(self):
        f,ref,v=self.setup_fixture();reader=hv.HistoryReader(f,ref);row=v['versions'][0];f.files.pop(row['copy']['path']);f.block_workflows=True
        self.reject(lambda:reader.read_bytes(row['original_path']),'Synthetic original absent')

    def test_04_changed_copy_rejected(self):
        f,ref,v=self.setup_fixture();reader=hv.HistoryReader(f,ref);row=v['versions'][0];f.files[row['copy']['path']]=b'changed copy'
        self.reject(lambda:reader.read_bytes(row['original_path']),'Pinned history/proof bytes differ')

    def test_05_unselected_current_platform_denied(self):
        f,ref,v=self.setup_fixture();reader=hv.HistoryReader(f,ref);original=str(hv.workflow_root(ROOT,'T1')/'android.json');f.files[original]=b'current bytes'
        self.reject(lambda:reader.read_bytes(original),'not selected')

    def test_06_mixed_workflow_directory_denied(self):
        f,ref,v=self.setup_fixture();reader=hv.HistoryReader(f,ref)
        self.reject(lambda:reader.directory(str(hv.workflow_root(ROOT,'T1'))),'mix historical and final')

    def test_07_ancestor_directory_mixture_denied(self):
        f,ref,v=self.setup_fixture();reader=hv.HistoryReader(f,ref)
        self.reject(lambda:reader.directory(ROOT),'mix historical and final')

    def test_08_normal_files_and_directories_forward(self):
        f,ref,v=self.setup_fixture();reader=hv.HistoryReader(f,ref);original=ROOT+'/ordinary/untouched.txt'
        self.assertEqual(reader.read_bytes(original),f.files[original]);self.assertEqual(reader.directory(ROOT+'/ordinary'),f.directory(ROOT+'/ordinary'))
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True})

    def test_09_wrong_external_ledger_pin(self):
        f,ref,v=self.setup_fixture();self.reject(lambda:hv.HistoryReader(f,{**ref,'sha256':'0'*64}),'Pinned history/proof bytes differ')

    def test_10_source_override_resealed_is_rejected(self):
        f,ref,v=self.setup_fixture();v['versions'][0]['original_path']=ROOT+'/source/Screen.swift';ref=self.reseal(f,ref,v)
        self.reject(lambda:hv.HistoryReader(f,ref),'Unregistered or missing historical override')

    def test_11_native_measurement_override_resealed_is_rejected(self):
        f,ref,v=self.setup_fixture();v['versions'][0]['original_path']=ROOT+'/cache/business/independent-evaluation/continuations/T1/B/android/native/service/capture/result.json';ref=self.reseal(f,ref,v)
        self.reject(lambda:hv.HistoryReader(f,ref),'Unregistered or missing historical override')

    def test_12_multiple_versions_are_ambiguous(self):
        f,ref,v=self.setup_fixture();row=copy.deepcopy(v['versions'][0]);row['required_sha256']='0'*64;v['versions'].append(row);ref=self.reseal(f,ref,v)
        self.reject(lambda:hv.HistoryReader(f,ref),'Ambiguous multiple historical versions')

    def test_13_duplicate_same_version_is_rejected(self):
        f,ref,v=self.setup_fixture();v['versions'].append(copy.deepcopy(v['versions'][0]));ref=self.reseal(f,ref,v)
        self.reject(lambda:hv.HistoryReader(f,ref),'duplicates or omits')

    def test_14_wrong_inode_provenance(self):
        f,ref,v=self.setup_fixture();v['versions'][0]['original_observation']['identity_after']['inode']+=1;ref=self.reseal(f,ref,v)
        self.reject(lambda:hv.HistoryReader(f,ref),'identity/provenance')

    def test_15_foreign_proof_path(self):
        f,ref,v=self.setup_fixture();v['selection']['registered_proofs'][0]['proof']['path']=ROOT+'/source/fresh-platform-context.json';ref=self.reseal(f,ref,v)
        self.reject(lambda:hv.HistoryReader(f,ref),'Foreign native context-proof')

    def test_16_partial_requires_explicit_selection(self):
        f,ref,v=self.setup_fixture(pending=True);self.assertEqual(v['status'],'partial');self.assertEqual(len(v['versions']),16)
        self.reject(lambda:hv.HistoryReader(f,ref),'Complete historical scope selection')
        reader=hv.HistoryReader(f,ref,require_complete=False)
        self.assertEqual(reader.hash(v['versions'][0]['original_path']),v['versions'][0]['required_sha256'])

    def test_17_changed_required_original_is_explicit_failure(self):
        label=self.id().rsplit('.',1)[-1];f=Synthetic(RUN/label/'originals');target=str(hv.workflow_root(ROOT,'T1')/'ios.json');f.files[target]=b'later changed bytes'
        ref,v=cp.create_checkpoint(f,ROOT,RUN/label/'checkpoint');f.add_checkpoint(Path(ref['path']).parent)
        self.assertEqual(v['status'],'failed');self.assertEqual(len(v['versions']),19);self.assertTrue(v['failures'][0].get('observed_sha256'))
        self.reject(lambda:hv.HistoryReader(f,ref),'failed or ambiguous checkpoint')

    def test_18_changed_registration_during_copy_fails(self):
        label=self.id().rsplit('.',1)[-1];f=Synthetic(RUN/label/'originals');old=f.observe;once=[True]
        def race(p):
            out=old(p)
            if once[0]:
                once[0]=False;key=next(k for k in f.files if k.endswith('fresh-platform-context.json'));f.files[key]=b'{}\n'
            return out
        f.observe=race;ref,v=cp.create_checkpoint(f,ROOT,RUN/label/'checkpoint');f.add_checkpoint(Path(ref['path']).parent)
        self.assertEqual(v['status'],'failed');self.assertTrue(any(x['stage']=='post_copy_registration_recheck' for x in v['failures']))
        self.reject(lambda:hv.HistoryReader(f,ref),'failed or ambiguous checkpoint')

    def test_19_ledger_change_after_construction(self):
        f,ref,v=self.setup_fixture();reader=hv.HistoryReader(f,ref);f.files[ref['path']]=b'changed ledger'
        self.reject(lambda:reader.hash(v['versions'][0]['original_path']),'ledger changed')

    def test_20_real_resolver_after_final_changes(self):
        f,ref,v=self.setup_fixture()
        for row in v['versions']:f.files[row['original_path']]=b'changed final-state original'
        mapping,map_sha,index_sha=f.restore(RUN/'real-resolver')
        spec=importlib.util.spec_from_file_location('history_real_resolver',HERE/'vendor/schema-code/resolver.py');rm=importlib.util.module_from_spec(spec);spec.loader.exec_module(rm)
        base=rm.Resolver(mapping,map_sha256=map_sha,index_sha256=index_sha);reader=hv.HistoryReader(base,ref)
        for row in v['versions']:
            self.assertEqual(reader.hash(row['original_path']),row['required_sha256']);self.assertNotEqual(base.hash(row['original_path']),row['required_sha256'])
        self.assertFalse(Path(ROOT).exists())
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True,'map_sha256':map_sha,'index_sha256':index_sha,'original_root_exists':False})

    def test_21_frozen_native_chain_api_without_mutable_reads(self):
        sys.path.insert(0,str(HERE/'vendor'))
        import native_chain as nc
        from synthetic import Fixture
        self.assertEqual(hv.sha((HERE/'vendor/native_chain.py').read_bytes()),'7c255b750389c5b5de2b90244e2952d4da55d0b3ff1819b9e0c2fbe8ce28028f')
        # Align the synthetic producer's configurable workflow root with the
        # actual registered hidden-workflow namespace before it writes files.
        # The frozen native verifier and history whitelist remain unchanged.
        class RegisteredFixture(Fixture):
            def edit(self,stage,value):
                if stage.startswith('config:') and '/B/' in stage and 'workflow' in value:
                    value['workflow']['root']=value['workflow']['root'].replace('/workflow','/hidden-workflow')
                return super().edit(stage,value)
        label=self.id().rsplit('.',1)[-1];f=RegisteredFixture(RUN/label/'native-fixture')
        class Merged:
            def __init__(self):self.extra={};self.trap=False;self.mutable_reads=0
            def read_bytes(self,p):
                p=str(p)
                if self.trap and '/hidden-workflow/' in p:
                    self.mutable_reads+=1;raise AssertionError('Frozen native verifier attempted mutable workflow read')
                return self.extra[p] if p in self.extra else f.read_bytes(p)
            def read_json(self,p):return hv.strict_json(self.read_bytes(p))
            def hash(self,p):return hv.sha(self.read_bytes(p))
            def directory(self,p):return f.directory(p)
            def observe(self,p):
                raw=self.read_bytes(p);physical=f.physical/str(p).lstrip('/');s=physical.stat()
                identity={'device':s.st_dev,'inode':s.st_ino,'bytes':len(raw),'mode':s.st_mode,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
                return raw,{'original_path':str(p),'sha256':hv.sha(raw),'stable_read':True,'identity_before':identity,'identity_after':dict(identity),'read_started_at_unix':1.0,'read_finished_at_unix':2.0}
        base=Merged();ref,v=cp.create_checkpoint(base,ROOT,RUN/label/'checkpoint')
        self.assertEqual(v['status'],'complete',v['failures']);self.assertEqual(len(v['versions']),20)
        for p in Path(ref['path']).parent.rglob('*'):
            if p.is_file():base.extra[str(p)]=p.read_bytes()
        for row in v['versions']:
            original=row['original_path'];f.files[original]=b'changed final workflow version';(f.physical/original.lstrip('/')).write_bytes(f.files[original])
        ordinary=nc.verify_chain(base,ROOT,f.snapshot_ref);self.assertEqual(ordinary['status'],'failed')
        base.trap=True;reader=hv.HistoryReader(base,ref);result=nc.verify_chain(reader,ROOT,f.snapshot_ref)
        self.assertEqual(result['status'],'verified',result);self.assertTrue(result['acquisition_complete']);self.assertEqual(base.mutable_reads,0)
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True,'frozen_verifier_sha256':hv.sha((HERE/'vendor/native_chain.py').read_bytes()),
                        'ordinary_final_view_status':ordinary['status'],'historical_view_status':result['status'],'mutable_workflow_reads':0,'synthetic_only':True})

    def test_22_checkpoint_rejects_foreign_claim_before_read(self):
        label=self.id().rsplit('.',1)[-1];f=Synthetic(RUN/label/'originals')
        claim=ROOT+'/cache/business/independent-evaluation/native-continuation-claims/T1/B/android.json'
        value=hv.strict_json(f.files[claim]);value['record']=ROOT+'/source';f.files[claim]=(json.dumps(value)+'\n').encode()
        ref,v=cp.create_checkpoint(f,ROOT,RUN/label/'checkpoint')
        self.assertEqual(v['status'],'failed');self.assertNotIn(ROOT+'/source/fresh-platform-context.json',f.reads)
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True,'foreign_proof_reads':0,'ledger':ref})

    def test_23_copy_cannot_alias_live_original(self):
        f,ref,v=self.setup_fixture();v['versions'][0]['copy']['path']=v['versions'][0]['original_path'];ref=self.reseal(f,ref,v);f.block_workflows=True
        self.reject(lambda:hv.HistoryReader(f,ref),'copy aliases an original')

    def test_24_contract_reference_is_not_whitelisted(self):
        label=self.id().rsplit('.',1)[-1];f=Synthetic(RUN/label/'originals')
        proof=ROOT+'/cache/business/independent-evaluation/continuations/T1/B/android/native/fresh-platform-context.json'
        value=hv.strict_json(f.files[proof]);foreign=ROOT+'/contracts/plan.json';value['sibling_files']['ios.json']['path']=foreign
        f.files[proof]=(json.dumps(value)+'\n').encode();ref,v=cp.create_checkpoint(f,ROOT,RUN/label/'checkpoint')
        self.assertEqual(v['status'],'failed');self.assertNotIn(foreign,f.reads)
        RESULTS.append({'control':self.id().rsplit('.',1)[-1],'passed':True,'foreign_contract_reads':0,'ledger':ref})

    def test_25_malformed_provenance_timestamp_rejected(self):
        f,ref,v=self.setup_fixture();v['versions'][0]['original_observation']['read_started_at_unix']='yesterday';ref=self.reseal(f,ref,v)
        self.reject(lambda:hv.HistoryReader(f,ref),'identity/provenance')

    def test_26_checkpoint_requires_fresh_directory(self):
        f,ref,v=self.setup_fixture();original=Path(ref['path']).read_bytes()
        self.reject(lambda:cp.create_checkpoint(f,ROOT,Path(ref['path']).parent),'fresh immutable output directory')
        self.assertEqual(Path(ref['path']).read_bytes(),original)

    def test_27_duplicate_ledger_json_rejected(self):
        f,ref,v=self.setup_fixture();raw=b'{"version":1,"version":1}\n';f.files[ref['path']]=raw;ref={**ref,'sha256':hv.sha(raw),'bytes':len(raw)}
        self.reject(lambda:hv.HistoryReader(f,ref),'Duplicate JSON key')


def main():
    with (RUN/'RUN.log').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    value={'kind':'author-synthetic-workflow-history-controls','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
           'passed':result.wasSuccessful(),'controls':RESULTS,'code_pins':{n:hv.sha((RUN/n).read_bytes()) for n in ['history_view.py','checkpoint.py','test_history.py']},
           'native_sdk_execution':False,'actual_product_results_or_grades_read':False,'synthetic_only':True}
    target=RUN/'RESULT.json';target.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'path':str(target),'sha256':hv.sha(target.read_bytes()),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
