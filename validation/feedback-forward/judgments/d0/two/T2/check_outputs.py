from pathlib import Path
import sys,json,hashlib,time,importlib.util,traceback
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=B/'judgments/d0/two/T2';sys.path.insert(0,str(B/'candidate-v9/scripts'))
import acceptance,design_contract as d

def load(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock=load(B/'design/T2/public/design-lock.json');policy=load(B/'design/T2/public/policy.json')
records=[]
for plat in ['android','ios']:
 for case in ['P1','P2']:
  inpdir=B/'evaluation-inputs/d0/T2/initial'/plat/case;inp=load(inpdir/'inputs.json');dest=O/'initial'/plat/case;judge=load(dest/'judge.json');obs=load(B/inp['observation']);plan=load(inpdir/'plan.json');env=load(B/inp['environment']);record={'platform':plat,'case':case,'checkedAtUnix':time.time(),'judge_sha256':sha(dest/'judge.json'),'mode':'same anonymous judgment passed as both panels solely for schema validation; not independent consensus'}
  try:
   report=acceptance.evaluate(plan,lock,d.digest(lock),policy,d.digest(policy),obs,inp['observation_sha256'],B/inp['raw'],plat,env,judge,judge)
   save(dest/'schema-check-same-judgment-twice.json',report);record['schema_valid']=True;record['status']=report.get('status');record['counts']=report.get('counts');print(plat,case,record['status'],record['counts'])
  except Exception as e:
   record.update(schema_valid=False,error=str(e),traceback=traceback.format_exc());save(dest/'rejected-schema-attempt-1.json',record);print(plat,case,'REJECTED',str(e))
  records.append(record)
# The expressly permitted source sidecar bind validates the original provided catalog.
spec=importlib.util.spec_from_file_location('implementation_audit','/Users/rex/Documents/ChatGPT/mobile-native-skill/tools/implementation_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
cat=load(B/'source-evaluation-inputs/d0/T2/initial/catalog.json');judge=load(O/'initial/source-judge.json');record={'mode':'source-bound schema validation only; original source manually inspected','checkedAtUnix':time.time(),'judge_sha256':sha(O/'initial/source-judge.json')}
try:
 result=audit.bind(cat,judge['review']);save(O/'initial/source-schema-check.json',result);record.update(schema_valid=True,status=result['status'],counts=result['counts']);print('source',result['status'],result['counts'])
except Exception as e:
 record.update(schema_valid=False,error=str(e),traceback=traceback.format_exc());save(O/'initial/rejected-source-schema-attempt-1.json',record);print('source REJECTED',str(e))
records.append(record);save(O/'schema-check-records.json',records)
