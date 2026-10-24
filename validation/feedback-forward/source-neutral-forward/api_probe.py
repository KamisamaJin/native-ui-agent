from pathlib import Path
import importlib.util, json, sys, time
root=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
out=root/'validation/feedback-forward/source-neutral-forward'
spec=importlib.util.spec_from_file_location('actual_implementation_audit',root/'tools/implementation_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
load=lambda p: json.loads(p.read_text())
pin=load(out/'independent-pin.json'); cat=load(out/'catalog.json'); sub=load(out/'honest-submission.json')
generated=audit.catalog(audit.d.load(out/'fixture/design/lock.json'),pin['lockCanonicalSha256'],audit.d.load(out/'fixture/design/implementation-audit.json'),pin['policyCanonicalSha256'],out/'fixture/source',out/'fixture/design')
result={'calledAtUnix':time.time(),'auditModulePath':str(audit.__file__),'transitiveDesignModulePath':str(audit.d.__file__),'apiCatalogEqualsCliCatalog':generated==cat,'apiBoundEqualsCliGate':audit.bind(cat,sub)==load(out/'honest-gate.json')}
try:
    audit.bind(load(out/'definitions.json'),sub)
    result['definitionBind']={'accepted':True}
except Exception as exc:
    result['definitionBind']={'accepted':False,'type':type(exc).__name__,'message':str(exc)}
with (out/'api-results.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
