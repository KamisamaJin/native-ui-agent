"""A missing or stale member prevents native launch authorization."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cohort_gate as g

class CohortGateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.registry=self.root/'gates';self.registry.mkdir()
        for member in ['a','b']:(self.root/(member+'.txt')).write_text(member)
        self.spec={'version':1,'artifact_root':str(self.root),'stages':{'design':{'members':['owner'],'requires':[]},'sources':{'members':['a','b'],'requires':['design']}}};self.write()
    def write(self):(self.registry/'config.json').write_text(json.dumps(self.spec))
    def test_early_launch_and_partial_membership_are_rejected(self):
        with self.assertRaises(ValueError):g.authorize(self.registry,'sources')
        with self.assertRaises(ValueError):g.seal(self.registry,'sources',{'a':['a.txt']})
        with self.assertRaises(ValueError):g.seal(self.registry,'sources',{'a':['a.txt'],'b':['b.txt']})
        self.assertFalse((self.registry/'sources.json').exists())
    def test_exact_complete_membership_authorizes_once_and_checks_upstream(self):
        g.seal(self.registry,'design',{'owner':['a.txt']});g.seal(self.registry,'sources',{'a':['a.txt'],'b':['b.txt']})
        self.assertEqual(g.authorize(self.registry,'sources')['cohortMembers'],['a','b'])
        with self.assertRaises(FileExistsError):g.seal(self.registry,'sources',{'a':['a.txt'],'b':['b.txt']})
        (self.root/'b.txt').write_text('changed')
        with self.assertRaises(ValueError):g.authorize(self.registry,'sources')
    def test_modified_membership_graph_and_escaping_artifact_are_rejected(self):
        g.seal(self.registry,'design',{'owner':['a.txt']});self.spec['stages']['sources']['members']=['a'];self.write()
        with self.assertRaises(ValueError):g.authorize(self.registry,'design')
        with self.assertRaises(ValueError):g.seal(self.registry,'sources',{'a':['../outside']})
    def test_cycles_and_backdated_stage_order_rejected(self):
        self.spec['stages']['design']['requires']=['sources'];self.write()
        with self.assertRaises(ValueError):g.config(self.registry)
        self.spec['stages']['design']['requires']=[];self.write();g.seal(self.registry,'design',{'owner':['a.txt']});g.seal(self.registry,'sources',{'a':['a.txt'],'b':['b.txt']})
        path=self.registry/'sources.json';s=g.load(path);s['sealedAtUnix']=0;path.write_text(json.dumps(s))
        with self.assertRaises(ValueError):g.authorize(self.registry,'sources')
if __name__=='__main__':unittest.main()
