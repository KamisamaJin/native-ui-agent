import pathlib,json,sys,time,hashlib,collections
R=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=R/'judgments/final/one/T1';sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'candidate-v9/scripts'));import design_contract
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
provenance=[];coverage=[];visual_count=collections.Counter();original_count=0
for p in sorted((R/'evaluation-inputs/final/T1').glob('*/*/*')):
 inp=json.loads((p/'inputs.json').read_text());dst=O/inp['source']/inp['platform']/inp['case'];inspection=json.loads((dst/'inspection.json').read_text());manifest=json.loads((R/inp['raw']/'manifest.json').read_text());sourcecat=json.loads((R/'source-evaluation-inputs/final/T1'/inp['source']/'catalog.json').read_text());suffix='ColdStorageTransferPanel.swift'if inp['platform']=='ios'else'ColdStorageTransferPanel.kt';declared=next(v['sha256']for k,v in sourcecat['files'].items()if k.endswith(suffix));observed=[v for k,v in manifest['source_hashes'].items()if k.endswith(suffix)];record={'bundle':str(dst.relative_to(O)),'metadata_reads':{},'source_sha_in_original_manifest':observed,'source_sha_in_capsule_catalog':declared,'manifest_source_hash_match':observed==[declared],'manifest_exit':manifest.get('test_exit_code',manifest.get('exit_code')),'selected_original_hash_mismatches':[]}
 for rel in [inp['observation'],inp['raw']+'/manifest.json',inp['environment'],inp['scope']+'/approval.json',inp['scope']+'/policy.json',inp['scope']+'/design-lock.json']:
  path=R/rel;actual=sha(path);expected=inp['original_files'].get(rel);record['metadata_reads'][rel]={'actual_sha256':actual,'input_sha256':expected,'matches_input':actual==expected if expected else None}
 for sid,state in inspection['states'].items():
  for im in state['originals']:
   original_count+=1;rel=str(pathlib.Path(im['path']).relative_to(R));expected=inp['original_files'].get(rel)
   if im['sha256']!=expected:record['selected_original_hash_mismatches'].append({'path':rel,'actual':im['sha256'],'input':expected})
  coverage.append({'bundle':str(dst.relative_to(O)),'state':sid,'eligible_indices':state['eligible_indices'],'complete_full_content':state['complete'],'binding':state['capture'].get('binding',{}),'coverage_reason':state['reason']})
 judge=json.loads((dst/'judge.json').read_text());visual_count.update('true'if x['actual']is True else'false'if x['actual']is False else'null'for x in judge['review']['decisions']);provenance.append(record)
(O/'provenance-checks.json').write_text(json.dumps(provenance,indent=2)+'\n');(O/'coverage-inspection.json').write_text(json.dumps(coverage,indent=2)+'\n')
summary=json.loads((O/'schema-check-summary.json').read_text());runtime=[x for x in summary if 'platform'in x];source=[x for x in summary if 'platform'not in x];counts={k:sum(x['counts'][k]for x in runtime)for k in ['passed','failed','unassessed']};scounts={k:sum(x['counts'][k]for x in source)for k in ['passed','failed','unassessed']}
summary_out={'task':'T1','phase':'final','panel':'one','runtime_bundles':len(runtime),'qualitative_actuals':dict(visual_count),'runtime_self_schema_check_counts':counts,'source_bundles':len(source),'source_self_schema_check_counts':scounts,'known_failures_requiring_attribution':0,'attribution_policy':'No strict native/pixel/visual/source F was supported; attribution arrays remain empty. Unknown samples have not been classified as failures.','unknowns':'For each anonymous source, Android P2 status-leading-clear remains U in all nine selected states. Eligible frames contain insufficient unambiguous solid-color support in the frozen whole-strip sampler; measured later frames cannot erase an eligible unmeasured frame. The diagnostic packets are retained.','scope':'One independent AI assessment. Same-request schema checks are not independent consensus or human gold. No SDK execution or source/expected repair was performed.','selected_original_occurrences_in_bound_states':original_count,'visualization_limits':'Viewed all 36 state catalogs and 12 native-bound status/primary crop catalogs, plus nine reference catalogs and original overview PNGs for all 12 bundles. Catalogs are viewport crops/stitches of SHA-retained original PNGs at logical width, sometimes downsampled by display; overlapping duplicate pixels can be overpainted in the reconstruction. Originals remain authoritative. Target-only states do not establish full-content absence. Full-content atoms cite their complete bound sweeps. No physical hit-region, generic computed style or older-OS runtime is inferred.'}
(O/'assessment-summary.json').write_text(json.dumps(summary_out,indent=2)+'\n')
commands={
 'read_operator':'cat validation/feedback-forward/operators/quality-final-one-T1-delivered.txt',
 'record_start':'python3: write phase.json actualStartUnix immediately after reading operator',
 'enumerate_inputs':'rg --files restricted to evaluation-inputs/final/T1 and source-evaluation-inputs/final/T1',
 'inspect_metadata':'Python JSON reads of every bundle inputs.json, plan.json, catalog.json, automatic.json and environment-check.json; original observation, permitted design lock/policy/approval/brief, original native manifest; compact field extraction',
 'inspect_source':'Python numbered full text of each exact anonymous production Swift/Kotlin file and approved Bridge.swift / ObserverBridge.kt; source catalog propositions; tools/implementation_audit.py and SOURCE-AUDIT.md',
 'frozen_tool_inspection':'rg and sed limited to candidate-v9/scripts/{acceptance,native_checks,review_contract}.py; candidate-v9 bound_state_evidence and resolve used for exact evidence indices',
 'catalog_generation':'python3 inspect_evidence.py; Python PIL original PNG viewport catalog and native-bound status/primary crop generation',
 'visual_reads':'view_image of reference-{P1,P2,H1}-{0,3,6}.png; every source/platform/case {closed-catalog,long-catalog,targets-catalog,control-crops}.png; original overview PNG for each bundle',
 'write_judgments':'python3 write_judgments.py',
 'schema_check':'python3 schema_check.py; frozen acceptance.evaluate with the SAME request in both panel slots once per bundle; tools/implementation_audit.py:bind on each source review',
 'unknown_diagnostics':'frozen native_pixels.sample restricted to original Android P2 status-leading-clear selected-state packets; persisted unassessed-pixel-diagnostics.json',
 'final_integrity':'python3 finish_assessment.py; exact metadata/source/image hash cross-checks, coverage inventory, summary and final complete-task SEAL',
 'failed_read_attempts':[{'command':'initial compact observation inspection expected observation.native_checks','exit_code':1,'error':'KeyError: native_checks','resolution':'Read frozen native_checks.bound_state_evidence and original observation state_captures; no judgment changed due to the read error.'}],
 'output_truncations':'Several broad initial metadata/source reads exceeded terminal output budget. Re-read relevant source gaps and compact fields. Huge original_files maps were parsed in full rather than treated as visual or product evidence.',
 'rejected_schema_attempts':[]}
(O/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
phase=json.loads((O/'phase.json').read_text());phase['actualEndUnix']=time.time();phase['status']='complete_runtime_and_source_assessment';(O/'phase.json').write_text(json.dumps(phase,indent=2)+'\n')
assert len(runtime)==12 and len(source)==2
assert all(x['schema_binding_check']=='accepted'for x in summary)
assert not any(x['selected_original_hash_mismatches']for x in provenance)
assert all(x['manifest_source_hash_match']for x in provenance)
assert len(list(O.glob('*/*/*/judge.json')))==12 and len(list(O.glob('*/source-judge.json')))==2
files={str(p.relative_to(O)):sha(p)for p in sorted(O.rglob('*'))if p.is_file()and p.name!='SEAL.json'and'__pycache__'not in p.parts}
sealed=time.time();(O/'SEAL.json').write_text(json.dumps({'sealedAtUnix':sealed,'files':files},indent=2)+'\n')
print(json.dumps({'sealedAtUnix':sealed,'sealedFiles':len(files),'runtime_bundles':12,'source_bundles':2,'runtime_counts':counts,'source_counts':scounts,'visual_actuals':dict(visual_count),'seal_sha256':sha(O/'SEAL.json')}))
