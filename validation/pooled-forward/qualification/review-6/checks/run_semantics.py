import sys,argparse,copy,shutil
sys.dont_write_bytecode=True
from domain_support import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import coverage_domain,native_checks,execution_plan,requirement_routes,scroll_coverage
base=ROOT/'work'/a.arm/'semantics';base.mkdir();rows=[]
def record(id,passed,detail):
 row={'id':id,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST evaluation/routing of SIMULATED native metadata/domain compile proof; no SDK','detail':detail};rows.append(row);save(base/(id+'-result.json'),row)
 if not passed:save(ROOT/'first-failures'/(a.arm+'--semantics--'+id+'.json'),row)
 print(a.arm+' '+id+': '+row['status'],flush=True)
config,domainplan,lock=setup_config(base/'admitted',arm);value=coverage_domain.prepare(config,domainplan,lock)
source=ROOT/'work'/a.arm/'geometry/positive-independent-encoded-strip';pristine=load(source/'observation.json');state=load(source/'state.json')
def evaluation(o,root,prop,expected):
 rid='state/'+prop+'/'+str(expected);plan={'version':1,'states':[state],'required_assertion_ids':[rid],'assertions':[{'id':rid,'state':state['id'],'kind':'control','target':{'identifier':'semantic-target'},'property':prop,'expected':expected,'op':'eq'}]}
 report=native_checks.evaluate(plan,o,'ios',root=root)
 return plan,report
for name,mode,prop,expected,expected_status in[
 ('Q01-lazy-present-seen-late','late','present',True,'passed'),
 ('Q02-lazy-unique-only-seen-late','late','unique',True,'passed'),
 ('Q03-absence-complete-never-present','absent','present',False,'passed'),
 ('Q04-present-late-contradicts-absence','late','present',False,'failed'),
 ('Q05-real-duplicate-then-one','duplicate','unique',True,'failed'),
 ('Q06-real-duplicate-retained-for-nonunique','duplicate','unique',False,'passed'),
 ('Q07-mixed-epoch-never-positive','mixed','present',True,'unassessed'),
 ('Q08-incomplete-sweep-never-negative','incomplete','present',False,'unassessed'),
 ('Q09-lazy-present-seen-early','early','present',True,'passed')]:
 folder=base/name;n=attach_packet(folder,config,domainplan,value,arm,source/'images');o=copy.deepcopy(pristine)
 if mode in{'late','mixed'}:
  o['snapshots'][2]['nodes'].append({'index':70,'parent_index':0,'identifier':'semantic-target','label':'late','role_raw':48,'enabled':True,'selected':False,'frame':rect(20,70,10,5),'fully_within_viewport':True,'intersects_viewport':True})
 if mode=='mixed':o['snapshots'][1]['binding']['event_revision']=99
 if mode in{'duplicate','early'}:
  for i,snap in enumerate(o['snapshots']):
   if mode=='early'and i>0:continue
   snap['nodes'].append({'index':70,'parent_index':0,'identifier':'semantic-target','label':'target','role_raw':48,'frame':rect(20,40,10,5),'fully_within_viewport':True,'intersects_viewport':True})
   if mode=='duplicate'and i==0:snap['nodes'].append({'index':71,'parent_index':0,'identifier':'semantic-target','label':'actual second target','role_raw':48,'frame':rect(30,50,10,5),'fully_within_viewport':True,'intersects_viewport':True})
 if mode=='incomplete':o['snapshots'][-1]['bottom_boundary']['hittable']=False
 plan,report=evaluation(o,n,prop,expected);save(folder/'evaluation-plan.json',plan);save(folder/'observation.json',o);save(folder/'evaluated.json',report);actual=report['assertions'][0]['status']
 record(name,actual==expected_status,{'expected_status':expected_status,'actual_status':actual,'state_complete':report['states'][state['id']]['complete'],'assertion':report['assertions'][0],'scope':'Generic state quantifier, separate from any native sample'})

# Certificate defects are also consumed as full-content/absence evidence.
for name in['sixteen-bit-rgb-lowbit-mismatch','joint-final-witness-inconsistency']:
 src=ROOT/'work'/a.arm/'geometry'/name;folder=base/('consumer-'+name);n=attach_packet(folder,config,domainplan,value,arm,src/'images');o=load(src/'observation.json');plan,report=evaluation(o,n,'present',False)
 execution={'execution_sha256':'e'*64,'scope':'full','platform':'ios','required_coverage':[{'state_id':state['id'],'coverage':'full_content','targets':[]}],'config':{'execution_state_definitions':[state]}}
 receipt=execution_plan.coverage_receipt(execution,o,n)
 # This source-independent synthetic route index is held fixed, not a changed product oracle.
 cov={'plan_sha256':canonical(plan),'design_lock_sha256':config['design_sha256'],'obligations':[{'id':'closed-absence','priority':'must','risk':'content','route_available':True,'assertion_ids':plan['required_assertion_ids']}]}
 failed_report=copy.deepcopy(report);failed_report['assertions'][0].update(status='failed',reason='SIMULATED deliberately contradictory actual for route probe')
 routed=requirement_routes.route_findings(cov,plan,failed_report,o,root=n);missing=requirement_routes.route_findings(cov,plan,failed_report,o,root=None)
 save(folder/'evaluated.json',report);save(folder/'coverage.json',receipt);save(folder/'routed.json',routed);save(folder/'routed-without-root.json',missing)
 record('Q10-consumer-'+name,not receipt['satisfied']and report['assertions'][0]['status']!='passed',{'expected':'No full/absence P from invalid original raster/joint witness','coverage_satisfied':receipt['satisfied'],'absence_status':report['assertions'][0]['status'],'route_actions':[t['action']for t in routed['tasks']],'missing_root_actions':[t['action']for t in missing['tasks']]})

# An all-visible repeated identity must be constrained globally after later frames.
folder=base/'Q11-repeated-visible-width-change';o,s=fixture(folder,joint=True);o['snapshots'][2]['nodes'][1]['frame']['width']=16;save(folder/'observation.json',o)
proof=scroll_coverage.certify(list(enumerate(o['snapshots'])),o['state_captures'][0]['binding'],folder/'images');save(folder/'proof.json',proof)
record('Q11-repeated-visible-width-change',not proof['complete'],{'proof':proof,'adjudication':'Separate valid regression for the earlier initial row that mutated an offscreen, ineligible leaf.'})
save(ROOT/'raw'/(a.arm+'-semantics-results.json'),rows)
