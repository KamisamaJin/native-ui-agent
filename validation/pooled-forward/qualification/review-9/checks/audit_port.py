from encoding_cases import *
import ast,difflib,subprocess,tarfile,io
pooled=ROOT.parents[1];original=pooled/'baseline-v12.6';common=pooled/'baseline-v12.6-common-5';candidate=pooled/'candidate-v13.8';changed=[];patches=[]
def filepaths(root):return {str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
for name in sorted(filepaths(original)|filepaths(common)):
 left=original/name;right=common/name
 if not left.is_file()or not right.is_file()or left.read_bytes()!=right.read_bytes():
  changed.append(name)
  if not name.startswith('tests/'):
   patches.append(''.join(difflib.unified_diff((left.read_text()if left.is_file()else'').splitlines(True),(right.read_text()if right.is_file()else'').splitlines(True),fromfile='original/'+name,tofile='common/'+name)))
(ROOT/'raw/independent-original-to-common5.diff').write_text(''.join(patches))
unchanged_files={name:sha(original/name)==sha(common/name)for name in['scripts/resource_manager.py','scripts/ui_loop.py','scripts/retest_plan.py','scripts/evidence_review.py','scripts/evidence_responsibility.py']}
unchanged_functions={}
for filename,names in{'scripts/ios_observe.py':['build_signature'],'scripts/execution_plan.py':['compile_execution','verify_execution'],'scripts/feedback_loop.py':['load_previous']}.items():
 def body(root,n):return ast.dump(next(v for v in ast.parse((root/filename).read_text()).body if isinstance(v,ast.FunctionDef)and v.name==n),include_attributes=False)
 for n in names:unchanged_functions[filename+':'+n]=body(original,n)==body(common,n)
module_presence={name:{'original':(original/'scripts'/name).exists(),'common':(common/'scripts'/name).exists()}for name in['workflow_state.py','capture_validity.py','source_identity.py','pool_watch.py']}
common_shared={name:sha(candidate/name)==sha(common/name)for name in['scripts/coverage_domain.py','scripts/scroll_coverage.py','scripts/native_checks.py','scripts/locator_diagnostics.py','assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift','assets/ios-observer/provider-conformance.json']}
expected={'assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift','assets/ios-observer/provider-conformance.json','assets/ios-observer/geometry-encoding.json','references/state-evidence.md','scripts/acceptance.py','scripts/coverage_domain.py','scripts/execution_plan.py','scripts/feedback_loop.py','scripts/ios_observe.py','scripts/locator_diagnostics.py','scripts/native_checks.py','scripts/requirement_routes.py','scripts/review_contract.py','scripts/scroll_coverage.py','tests/test_scroll_coverage.py','tests/test_coverage_domain.py','tests/test_native_checks.py'}
argv=['git','archive','--format=tar','e75dd9227203dd06350a923cc249b79ff710687f','native-ui-agent'];r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20);commit={'argv':argv,'exit_code':r.returncode,'stderr':r.stderr.decode(errors='replace'),'evidence_class':'HOST read-only original baseline public source; no validation or business material'}
if r.returncode==0:
 with tarfile.open(fileobj=io.BytesIO(r.stdout))as tf:hashes={m.name.removeprefix('native-ui-agent/'):hashlib.sha256(tf.extractfile(m).read()).hexdigest()for m in tf.getmembers()if m.isfile()}
 actual={name:sha(original/name)for name in filepaths(original)};commit.update(baseline_copy_matches_commit=hashes==actual,file_count=len(hashes),mismatches=sorted(k for k in set(hashes)|set(actual)if hashes.get(k)!=actual.get(k)))
save(ROOT/'raw/original-baseline-commit-verification.json',commit)
only_indicator=(common/'assets/ios-observer/ObserverApp.swift').read_text().replace('ScrollView(.vertical, showsIndicators: false)','ScrollView(.vertical)')==(original/'assets/ios-observer/ObserverApp.swift').read_text()
passed=set(changed)==expected and all(unchanged_files.values())and all(unchanged_functions.values())and all(common_shared.values())and all(v['original']==v['common']for v in module_presence.values())and only_indicator and commit.get('baseline_copy_matches_commit')
report={'id':'PORT01-common-equivalence-and-treatment-exclusion','status':'P'if passed else'F','evidence_class':'HOST source/AST/byte audit; no SDK behavior/timing claim','changed_paths':changed,'expected_paths':sorted(expected),'policy_files_unchanged':unchanged_files,'policy_functions_unchanged':unchanged_functions,'treatment_module_presence':module_presence,'common_source_byte_parity':common_shared,'host_only_indicator_constructor':only_indicator,'original_commit':commit,'source_diff':'raw/independent-original-to-common5.diff','manual_source_diff_review_pending':True,'test_contents_used_to_design_expectations':False}
save(ROOT/'raw/common-port-audit.json',report)
print(json.dumps(report,indent=2))
