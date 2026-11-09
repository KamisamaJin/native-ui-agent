#!/usr/bin/env python3
"""Read-only replay with the actual captured Python runtime, never an SDK."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('name',choices=['android-candidate-positive','android-candidate-negative']);parser.add_argument('--capture-root',type=Path);a=parser.parse_args()
 root=a.capture_root or P/'evidence/probes'/a.name;capture=root/'capture';runtime=capture/'tool-runtime'
 receipt=read(capture/'result.json')
 for rel,expected in receipt['tool_files'].items():assert sha(runtime/rel)==expected,rel
 sys.path.insert(0,str(runtime/'scripts'))
 import design_contract as d,native_checks as nc,execution_plan as xp,action_guard as ag,acceptance as ac,evidence_responsibility as er
 positive=a.name.endswith('positive');scope=P/'probes/native'/('prepared-positive'if positive else'prepared')
 config=read(scope/'android/config.json');lock=read(scope/'android/lock.json');plan=read(capture/'parent-plan.json');execution=read(capture/'execution.json');fixtures=read(scope/'fixtures.json')
 xp.verify_execution(execution,plan,lock,config['design_sha256'],fixtures,sha(P/'probes/native/ObserverBridge.kt'))
 op=capture/'native/observation.json';obs=read(op);xp.verify_capture_images(receipt,op.parent)
 assert ag.verify_observation(execution['actions'],obs,'android')==receipt['action_prerequisites']
 report=nc.evaluate(plan,obs,'android',root=op.parent,observation_sha256=sha(op),design_lock=lock,design_sha256=config['design_sha256'])
 report['environment']=ac.environment(obs,read(scope/'android/environment.json'),'android')
 assert report==read(capture/'automatic.json')
 assert report['counts']==({'passed':6,'failed':0,'unassessed':0}if positive else{'passed':8,'failed':0,'unassessed':6})
 before=read(capture/'source-before.json');assert before==read(capture/'source-after.json')
 assert before['0/NeutralCounter.swift']==sha(P/'evidence/probes/production/alerttoast/Sources/AlertToast/NeutralCounter.swift')
 assert before['1/NeutralCounter.kt']==sha(P/'evidence/probes/production/reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt')
 manifest=read(capture/'native/manifest.json');assert manifest['native_test_count']==1 and manifest['exit_code']==0
 compiled=read(root/'evidence-responsibility.json')
 # Restore only the lookup location of immutable original source-review bytes.
 # Subject namespaces, claim IDs/hashes, actuals, units and verdicts stay literal.
 closed=er.evaluate({'source_review_store':str(P/'evidence/probes/source-reviews/android')},compiled,report)
 expected=read(root/'responsibility-results.json')
 for actual,old in zip(closed['rows'],expected['rows']):
  assert {k:v for k,v in actual.items()if k!='evidence'}=={k:v for k,v in old.items()if k!='evidence'}
  assert {v['sha256']for v in actual['evidence']}=={v['sha256']for v in old['evidence']}
  for ref in actual['evidence']:assert sha(Path(ref['path']))==ref['sha256']
 assert not closed['blocking_claims']
 cycle=read(root/'cycle.json');resource=read(root/'resources.json')
 assert cycle['resources_sha256']==sha(root/'resources.json')and not resource['cleanup_errors']and not resource['remaining_devices']and not resource['remaining_directories']
 assert cycle['status']==('accepted'if positive else'awaiting_diagnosis')
 print(json.dumps({'status':'PASS','case':a.name,'native_counts':report['counts'],'source_rows':len(closed['rows']),
  'scope':'Original real Android native packet, typed facts, source/claim/image binding and managed finalization replay; no new SDK execution or product-quality claim.'}))
if __name__=='__main__':main()
