from pathlib import Path
import copy, hashlib, json, os, shutil, subprocess, sys, time
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
OUT=ROOT/'validation/feedback-forward/source-neutral-forward'
DESIGN=OUT/'fixture/design'; SOURCE=OUT/'fixture/source'; AUDIT=ROOT/'tools/implementation_audit.py'

def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(p): return json.loads(p.read_text())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f: f.write(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def run(label,args):
    t=time.time(); p=subprocess.run([str(v) for v in args],cwd=ROOT,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    rec={'label':label,'startedAtUnix':t,'endedAtUnix':time.time(),'cwd':str(ROOT),'argv':[str(v) for v in args],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    write(OUT/'commands'/f'{label}.json',rec)
    print(json.dumps({'label':label,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
    return p
pin=load(OUT/'independent-pin.json'); cat=load(OUT/'catalog.json')
common=['--design-lock',DESIGN/'lock.json','--design-sha256',pin['lockCanonicalSha256'],'--policy',DESIGN/'implementation-audit.json','--policy-sha256',pin['policyCanonicalSha256'],'--source-root',SOURCE,'--design-root',DESIGN]
def bind_cli(label,submission,root=None,common_args=None):
    args=common.copy() if common_args is None else common_args.copy()
    if root is not None: args[args.index('--source-root')+1]=root
    return run(label,[sys.executable,AUDIT,'bind']+args+['--submission',submission,'--output',OUT/'cases'/label/'gate.json'])
def ref(file,start,end): return {'file':file,'sha256':cat['files'][file]['sha256'],'start_line':start,'end_line':end}
answers={
'swift-clamp':(True,'The complete one-line getter calls max(0, count); no mutation or alternate return exists in this getter.',[ref('BadgeModel.swift',10,10)]),
'swift-delegation':(True,'The label getter returns formatter.string(for: displayCount). This identifies a call site, not the result of the formatter.',[ref('BadgeModel.swift',11,11)]),
'kotlin-clamp':(True,'The complete one-line getter calls count.coerceAtLeast(0).',[ref('BadgeModel.kt',10,10)]),
'kotlin-delegation':(True,'The label getter returns formatter.stringFor(displayCount). This identifies a call site, not the formatter output.',[ref('BadgeModel.kt',11,11)]),
'kotlin-empty-fallback':(False,'The entire getter is a direct formatter return and contains no in-body empty-result replacement.',[ref('BadgeModel.kt',11,11)]),
'shared-identifier':(True,'Both declarations contain the exact independently specified accessibilityIdentifier source constant.',[ref('BadgeModel.swift',8,8),ref('BadgeModel.kt',6,8)]),
'formatter-localization':(None,'The declared files define formatter interfaces and injection points only. No configured formatter implementation, resource lookup, or wiring is present. The localization key cannot be established from this scope.',[ref('BadgeModel.swift',1,7),ref('BadgeModel.kt',1,5)])}
submission={'version':1,'catalog_sha256':digest(cat),'decisions':[dict(review_id=row['review_id'],actual=answers[row['id']][0],reason=answers[row['id']][1],evidence=answers[row['id']][2]) for row in cat['rows']]}
write(OUT/'honest-submission.json',submission)
run('009-bind-honest',[sys.executable,AUDIT,'bind']+common+['--submission',OUT/'honest-submission.json','--output',OUT/'honest-gate.json'])

def variant(label,mutator):
    value=copy.deepcopy(submission); mutator(value)
    p=OUT/'cases'/label/'TEMPORARY-submission.json';write(p,value)
    return bind_cli(label,p)
variant('010-expected-override',lambda s:s['decisions'][0].update(expected=True))
variant('011-status-override',lambda s:s['decisions'][0].update(status='passed'))
variant('012-unit-override',lambda s:s['decisions'][0].update(unit='bool'))
variant('013-catalog-hash-mismatch',lambda s:s.update(catalog_sha256='0'*64))
variant('014-source-evidence-hash',lambda s:s['decisions'][0]['evidence'][0].update(sha256='0'*64))
variant('015-zero-line',lambda s:s['decisions'][0]['evidence'][0].update(start_line=0))
variant('016-past-end-line',lambda s:s['decisions'][0]['evidence'][0].update(end_line=cat['files']['BadgeModel.swift']['line_count']+1))
variant('017-missing-declared-file',lambda s:s['decisions'][5].update(evidence=s['decisions'][5]['evidence'][:1]))
variant('018-foreign-evidence-file',lambda s:s['decisions'][0]['evidence'][0].update(file='Elsewhere.swift'))
variant('019-cross-review-id',lambda s:s['decisions'][0].update(review_id='0'*64))
variant('020-integer-actual',lambda s:s['decisions'][0].update(actual=1))
variant('021-duplicate-decision',lambda s:s['decisions'].append(copy.deepcopy(s['decisions'][0])))
variant('022-omit-known-decision',lambda s:s['decisions'].pop(0))
variant('023-all-unknown-no-evidence',lambda s:[item.update(actual=None,reason='Temporary boundary case: explicitly not reviewed.',evidence=[]) for item in s['decisions']])

changed=OUT/'cases/024-changed-source/TEMPORARY-source'
shutil.copytree(SOURCE,changed)
p=changed/'BadgeModel.swift';p.write_text(p.read_text().replace('max(0, count)','count'))
write(OUT/'cases/024-changed-source/change.json',{'temporaryOnly':True,'changedAtUnix':time.time(),'file':str(p.relative_to(OUT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'edit':'Replace the clamp expression with raw count in this temporary copy only.'})
bind_cli('024-changed-source',OUT/'honest-submission.json',changed)

symlink_root=OUT/'cases/025-outside-root-symlink/TEMPORARY-source';symlink_root.mkdir(parents=True)
(symlink_root/'BadgeModel.swift').symlink_to(SOURCE/'BadgeModel.swift')
shutil.copy2(SOURCE/'BadgeModel.kt',symlink_root/'BadgeModel.kt')
bind_cli('025-outside-root-symlink',OUT/'honest-submission.json',symlink_root)

bad_lock=copy.deepcopy(load(DESIGN/'lock.json'));bad_lock['sources']['neutral']['document']['presence']['value']=False
bad_lock_path=OUT/'cases/026-changed-lock/TEMPORARY-lock.json';write(bad_lock_path,bad_lock)
args=common.copy();args[args.index('--design-lock')+1]=bad_lock_path
bind_cli('026-changed-lock',OUT/'honest-submission.json',common_args=args)
bad_policy={'version':1,'index':{'source':'neutral','pointer':'/propositions'}}
bad_policy_path=OUT/'cases/027-changed-policy/TEMPORARY-policy.json';write(bad_policy_path,bad_policy)
args=common.copy();args[args.index('--policy')+1]=bad_policy_path
bind_cli('027-changed-policy',OUT/'honest-submission.json',common_args=args)
run('028-bind-missing-submission',[sys.executable,AUDIT,'bind']+common+['--output',OUT/'cases/028-bind-missing-submission/gate.json'])
run('029-existing-output',[sys.executable,AUDIT,'catalog']+common+['--output',OUT/'catalog.json'])

# Deliberately incorrect reviewer judgment against a temporary source copy.
# This case probes semantics; it is never an honest result or a product defect.
changed_common=common.copy();changed_common[changed_common.index('--source-root')+1]=changed
fresh_cat_path=OUT/'cases/030-unsupported-review/TEMPORARY-catalog.json'
run('030a-temporary-changed-catalog',[sys.executable,AUDIT,'catalog']+changed_common+['--output',fresh_cat_path])
fresh_cat=load(fresh_cat_path)
unsupported=copy.deepcopy(submission);unsupported['catalog_sha256']=digest(fresh_cat)
for row,item in zip(fresh_cat['rows'],unsupported['decisions']):
    item['actual']=row['expected']
    item['reason']='INTENTIONALLY DISHONEST TEMPORARY BOUNDARY CASE: assert the expected Boolean regardless of source semantics or unresolved formatter implementation.'
    item['evidence']=[{'file':f,'sha256':fresh_cat['files'][f]['sha256'],'start_line':1,'end_line':1} for f in row['files']]
unsupported_path=OUT/'cases/030-unsupported-review/TEMPORARY-dishonest-submission.json';write(unsupported_path,unsupported)
bind_cli('030b-unsupported-review-acceptance',unsupported_path,changed)

api_script=OUT/'api_probe.py'
api_script.write_text('''from pathlib import Path
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
with (out/'api-results.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
''')
run('031-direct-api-probes',[sys.executable,api_script])
# Capture a compact inspection of actual artifacts rather than assuming a zero exit implies a pass.
run('032-inspect-gates',[sys.executable,'-c',"from pathlib import Path; import json; o=Path("+repr(str(OUT))+"); ps=[o/'honest-gate.json',o/'cases/022-omit-known-decision/gate.json',o/'cases/023-all-unknown-no-evidence/gate.json',o/'cases/030b-unsupported-review-acceptance/gate.json']; [(print(json.dumps({'path':str(p.relative_to(o)), **{k:json.loads(p.read_text())[k] for k in ['status','counts','blocking_obligations']}}))) for p in ps]"])
