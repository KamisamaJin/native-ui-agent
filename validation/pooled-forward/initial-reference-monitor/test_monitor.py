"""Small HOST-only ownership/superset controls; no SDK or monitor process."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest

from monitor import dependencies, extend, idle, slots


ROOT=Path(__file__).resolve().parent
HOST=ROOT/'HOST'
RESULTS=[]


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.module,_=dependencies()
    def setUp(self):
        HOST.mkdir(exist_ok=True);self.root=Path(tempfile.mkdtemp(prefix='synthetic-',dir=HOST))
        self.old=self.root/'old/journal.json';self.new=self.root/'initial/T/new/journal.json'
        self.base={'groups':{'whole_study':{'paths':[str(self.root)],'resource_journals':[str(self.old)]}},'sample_seconds':2,'max_total_allocated_bytes':32*2**30,'min_free_bytes':5*2**30,'filesystem_root':str(self.root)}
        self.declaration={'version':1,'kind':'common-initial-reference-meter-extension','owned_root':str(self.root/'initial'),'resource_journals':[str(self.new)]}
        self.journal(self.old,[]);self.journal(self.new,[])
    def tearDown(self): RESULTS.append({'test':self.id(),'root':str(self.root),'scope':'Retained synthetic journal fixtures only; no simctl/SDK/monitor execution'})
    def journal(self,p,devices):
        p.parent.mkdir(parents=True,exist_ok=True);s=p.parent.stat();token='a'*32
        (p.parent/'owner.json').write_text(json.dumps({'format':'native-ui-owned-resources-v1','token':token})+'\n')
        p.write_text(json.dumps({'format':'native-ui-owned-resources-v1','token':token,'root_identity':{'device':s.st_dev,'inode':s.st_ino},'devices':devices})+'\n')
    def device(self,n=1,udid=True):
        return [{'name':'NativeUI-'+('a'*12)+'-fixture'+str(i),**({'udid':'HOST-FAKE-'+str(i)} if udid else{})} for i in range(n)]
    def test_extended_spec_preserves_original_and_all_bounds(self):
        before=copy.deepcopy(self.base);full=extend(self.base,self.declaration)
        self.assertEqual(self.base,before)
        expected=copy.deepcopy(before);expected['groups']['whole_study']['resource_journals'].append(str(self.new));self.assertEqual(full,expected)
        self.assertTrue(idle(self.base,full,self.module.owned_device_paths)['all_clear'])
    def test_unclosed_original_slot_blocks_admission(self):
        self.journal(self.old,self.device())
        with self.assertRaises(ValueError): idle(self.base,extend(self.base,self.declaration),self.module.owned_device_paths)
    def test_new_intent_without_udid_still_counts_as_a_slot(self):
        self.journal(self.new,self.device(udid=False));full=extend(self.base,self.declaration)
        self.assertEqual(slots(full,self.module.owned_device_paths),1)
        with self.assertRaises(ValueError): idle(self.base,full,self.module.owned_device_paths)
    def test_whole_study_two_slot_cap_is_unchanged(self):
        self.journal(self.new,self.device(3))
        with self.assertRaises(RuntimeError): slots(extend(self.base,self.declaration),self.module.owned_device_paths)
    def test_foreign_token_and_replaced_root_identity_rejected(self):
        row=json.loads(self.new.read_text());row['token']='b'*32;self.new.write_text(json.dumps(row))
        with self.assertRaises(ValueError): slots(extend(self.base,self.declaration),self.module.owned_device_paths)
        self.journal(self.new,[]);row=json.loads(self.new.read_text());row['root_identity']['inode']+=1;self.new.write_text(json.dumps(row))
        with self.assertRaises(ValueError): slots(extend(self.base,self.declaration),self.module.owned_device_paths)
    def test_duplicate_foreign_and_traversal_journals_rejected(self):
        for values in [[str(self.new),str(self.new)],[str(self.old)],[str(self.root/'initial/../outside/journal.json')]]:
            d=copy.deepcopy(self.declaration);d['resource_journals']=values
            with self.assertRaises(ValueError): extend(self.base,d)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    HOST.mkdir(exist_ok=True)
    (HOST/('RESULT-'+str(time.time_ns())+'.json')).write_text(json.dumps({'version':1,'at_unix':time.time(),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'controls':RESULTS,'scope':'Author HOST ownership/superset checks only, no actual SDK/device/monitor or new business observations'},indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
