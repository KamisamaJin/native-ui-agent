from foundation_cases import *
import ast,difflib,subprocess,tarfile,io
folder=ROOT.parents[1];original=folder/'baseline-v12.6';common=folder/'baseline-v12.6-common-1';candidate=folder/'candidate-v13.4';before=folder/'candidate-v13.3';changed=[];patches=[]
files={str(p.relative_to(original))for p in original.rglob('*')if p.is_file()}|{str(p.relative_to(common))for p in common.rglob('*')if p.is_file()}
for name in sorted(files):
 a=original/name;b=common/name
 if not a.is_file()or not b.is_file()or a.read_bytes()!=b.read_bytes():
  changed.append(name)
  if not name.startswith('tests/'):
   left=a.read_text()if a.is_file()else'';right=b.read_text()if b.is_file()else'';patches.append(''.join(difflib.unified_diff(left.splitlines(True),right.splitlines(True),fromfile='original/'+name,tofile='common/'+name)))
(ROOT/'raw'/'independent-baseline-common-source.diff').write_text(''.join(patches))
functions={}
for filename,names in {'scripts/ios_observe.py':['build_signature','prepare_build'],'scripts/execution_plan.py':['compile_execution','verify_execution'],'scripts/feedback_loop.py':['run_cycle','load_previous']}.items():
 def body(root,name):
  tree=ast.parse((root/filename).read_text());node=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))and n.name==name);return ast.dump(node,include_attributes=False)
 for name in names:functions[filename+':'+name]={'unchanged_from_original_baseline':body(original,name)==body(common,name)}
unchanged_files=['scripts/resource_manager.py','scripts/ui_loop.py','scripts/retest_plan.py','scripts/evidence_review.py','scripts/evidence_responsibility.py'];unchanged={name:(original/name).read_bytes()==(common/name).read_bytes()for name in unchanged_files}
modules={name:{'original':(original/'scripts'/name).exists(),'common':(common/'scripts'/name).exists()}for name in ['workflow_state.py','capture_validity.py','source_identity.py','pool_watch.py']}
host_same=(candidate/'assets/ios-observer/ObserverApp.swift').read_bytes()==(common/'assets/ios-observer/ObserverApp.swift').read_bytes();only_indicator=(common/'assets/ios-observer/ObserverApp.swift').read_text().replace('ScrollView(.vertical, showsIndicators: false)','ScrollView(.vertical)')==(original/'assets/ios-observer/ObserverApp.swift').read_text()
provider_same=(candidate/'scripts/scroll_coverage.py').read_bytes()==(common/'scripts/scroll_coverage.py').read_bytes();same_roots={name:sha(candidate/name)==sha(common/name)for name in ['scripts/scroll_coverage.py','assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift']}
expected={'assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift','references/state-evidence.md','scripts/acceptance.py','scripts/execution_plan.py','scripts/feedback_loop.py','scripts/ios_observe.py','scripts/locator_diagnostics.py','scripts/native_checks.py','scripts/requirement_routes.py','scripts/review_contract.py','scripts/scroll_coverage.py','tests/test_scroll_coverage.py'}
argv=['git','archive','--format=tar','e75dd9227203dd06350a923cc249b79ff710687f','native-ui-agent'];r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20);git_record={'argv':argv,'exit_code':r.returncode,'stderr':r.stderr.decode(errors='replace'),'scope':'Read-only original baseline source verification, no SDK/native/product cases'}
if r.returncode==0:
 hashes={}
 with tarfile.open(fileobj=io.BytesIO(r.stdout))as tf:
  for m in tf.getmembers():
   if m.isfile():hashes[m.name.removeprefix('native-ui-agent/')]=hashlib.sha256(tf.extractfile(m).read()).hexdigest()
 actual={str(p.relative_to(original)):sha(p)for p in original.rglob('*')if p.is_file()};git_record.update(source_files=len(hashes),baseline_copy_matches_commit=hashes==actual,mismatches=sorted(k for k in set(hashes)|set(actual)if hashes.get(k)!=actual.get(k)))
save(ROOT/'raw'/'original-baseline-commit-check.json',git_record)
passed=set(changed)==expected and all(unchanged.values())and all(v['unchanged_from_original_baseline']for v in functions.values())and all(v['original']==v['common']for v in modules.values())and host_same and only_indicator and provider_same
report={'id':'I05-equivalent-common-baseline-port','status':'P'if passed else'F','evidence_class':'HOST source/hash/AST audit; SDK behavior not proven','changed_paths':changed,'expected_common_only_paths':sorted(expected),'unchanged_files':unchanged,'unchanged_functions':functions,'treatment_modules_presence':modules,'provider_same_bytes':provider_same,'Swift_host_same_bytes':host_same,'host_change_is_only_indicator_constructor':only_indicator,'common_runtime_byte_parity':same_roots,'source_diff':'raw/independent-baseline-common-source.diff','original_commit_check':'raw/original-baseline-commit-check.json','test_file_contents_used_to_design_expectations':False,'treatment_gains_backported':'No treatment retention/registry/adoption/environment/build-key changes observed in this port; original policy-bearing files/functions above remain exact.'}
save(ROOT/'raw'/'common-port-audit.json',report)
if not passed:save(ROOT/'first-failures'/'common-port-audit.json',report)
# Preserve the deliberately altered image member as a separate negative copy, then restore the exact independently retained original byte member.
relocations=[]
for name in ['candidate-v13.4','baseline-v12.6-common-1']:
 base=ROOT/'work'/name/'integration';output=base/'collector-output';bad=base/'tampered-packet-copy';shutil.copytree(output,bad);pristine=base/'pristine-frame-1.png';target=output/'attachments'/'frame-1.png';old=sha(target);expected_hash=json.loads((output/'manifest.json').read_text())['image_hashes']['attachments/frame-1.png']
 if sha(pristine)!=expected_hash:raise RuntimeError('Retained original member differs from original collector pin')
 shutil.copyfile(pristine,target);relocations.append({'arm':name,'original_output':str(output),'negative_working_copy':str(bad),'altered_member_sha256':old,'independently_retained_original':str(pristine),'original_member_sha256':expected_hash,'restored_exact_original_bytes':sha(target)==expected_hash,'note':'I04 intentionally corrupted a working member after I02/I03; source-images and pristine-frame already retained original bytes. Altered bytes are preserved in tampered-packet-copy; no new native collection or regrading.'})
save(ROOT/'raw'/'negative-image-copy-preservation.json',relocations)
print(json.dumps({'port_status':report['status'],'changed_paths':len(changed),'provider_same_bytes':provider_same,'Swift_host_same_bytes':host_same,'policy_files_unchanged':all(unchanged.values()),'baseline_copy_matches_commit':git_record.get('baseline_copy_matches_commit'),'native_runs':0},indent=2))
