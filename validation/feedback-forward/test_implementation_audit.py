import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
sys.path.insert(0,str(REPO/'tools'))
import implementation_audit as audit
import design_contract as d
class SourceAuditTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  reference=d.load(REPO/'native-ui-agent/assets/atomic-example/reference.json')
  reference['audit-question']={'value':'Does the declared component own its local state?','unit':'string'};reference['audit-expected']={'value':True,'unit':'bool'}
  reference['implementation_audits']=[{'id':'local-state','clause':'Component owns local state.','priority':'must','files':['Component.swift'],'proposition':{'source':'reference','pointer':'/audit-question'},'expected':{'source':'reference','pointer':'/audit-expected'}}]
  ref=self.root/'reference.json';ref.write_text(json.dumps(reference));contract=d.load(REPO/'native-ui-agent/assets/atomic-example/contract.json');contract['sources'][0]['sha256']=audit.sha(ref);(self.root/'contract.json').write_text(json.dumps(contract))
  self.lock=d.seal(self.root/'contract.json',self.root);self.lock_sha=d.digest(self.lock);self.policy={'version':1,'index':{'source':'reference','pointer':'/implementation_audits'}}
  self.production=self.root/'production';self.production.mkdir();(self.production/'Component.swift').write_text('// Neutral source\nlet localState = false\n')
  self.cat=self.catalog();self.sub={'version':1,'catalog_sha256':d.digest(self.cat),'decisions':[{'review_id':self.cat['rows'][0]['review_id'],'actual':True,'reason':'Original source lines reviewed','evidence':[{'file':'Component.swift','sha256':audit.sha(self.production/'Component.swift'),'start_line':1,'end_line':2}]}]}
 def catalog(self):return audit.catalog(self.lock,self.lock_sha,self.policy,d.digest(self.policy),self.production,self.root)
 def test_expected_status_and_unit_come_from_independent_source(self):
  result=audit.bind(self.cat,self.sub);self.assertEqual(result['status'],'accepted');self.assertTrue(result['rows'][0]['expected']);self.assertEqual(result['rows'][0]['unit'],'bool')
  for field in ['status','expected','unit']:
   bad=copy.deepcopy(self.sub);bad['decisions'][0][field]='override'
   with self.assertRaises(ValueError):audit.bind(self.cat,bad)
 def test_unknown_and_supported_negative_are_distinct_and_block(self):
  for actual,status in [(None,'unassessed'),(False,'failed')]:
   sub=copy.deepcopy(self.sub);sub['decisions'][0]['actual']=actual
   result=audit.bind(self.cat,sub);self.assertEqual(result['rows'][0]['status'],status);self.assertEqual(result['status'],'not_accepted')
 def test_changed_source_catalog_or_line_identity_is_rejected(self):
  for field,value in [('sha256','0'*64),('end_line',99),('file','Foreign.swift')]:
   bad=copy.deepcopy(self.sub);bad['decisions'][0]['evidence'][0][field]=value
   with self.assertRaises(ValueError):audit.bind(self.cat,bad)
  (self.production/'Component.swift').write_text('changed source\n')
  with self.assertRaises(ValueError):audit.bind(self.catalog(),self.sub)
 def test_policy_repin_missing_source_or_escape_cannot_be_a_pass(self):
  with self.assertRaises(ValueError):audit.catalog(self.lock,self.lock_sha,self.policy,'0'*64,self.production,self.root)
  (self.production/'Component.swift').unlink()
  with self.assertRaises(ValueError):self.catalog()
  definitions=audit.catalog(self.lock,self.lock_sha,self.policy,d.digest(self.policy),self.production,self.root,definition_only=True)
  self.assertEqual(definitions['mode'],'definition_only')
  with self.assertRaises(ValueError):audit.bind(definitions,dict(self.sub,catalog_sha256=d.digest(definitions)))
if __name__=='__main__':unittest.main()
