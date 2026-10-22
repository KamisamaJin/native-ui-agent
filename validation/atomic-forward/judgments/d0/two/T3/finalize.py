import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,time,datetime
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/two/T3';sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks
idx=json.loads((O/'evidence-index.json').read_text());counts={'true':0,'false':0,'unknown':0};attrs=0
for key,entry in idx.items():
 p=B/'evaluation-inputs/d0/T3'/key;cat=json.loads((p/'catalog.json').read_text());plan=json.loads((p/'plan.json').read_text());a=json.loads((p/'automatic.json').read_text());i=json.loads((p/'inputs.json').read_text());obs=json.loads((B/i['observation']).read_text());j=json.loads((O/key/'judge.json').read_text())
 assert set(j)=={'review','attributions'}
 assert set(j['review'])=={'version','catalog_sha256','observation_sha256','decisions'}
 assert j['review']['catalog_sha256']==cat['catalog_sha256']
 assert j['review']['observation_sha256']==hashlib.sha256((B/i['observation']).read_bytes()).hexdigest()
 visual={r['review_id']:r for r in cat['rows']if r['method']=='visual'}
 assert {d['review_id']for d in j['review']['decisions']}==set(visual)
 fids={f['id']for f in a['assertions']if f['status']=='failed'}
 for d in j['review']['decisions']:
  assert set(d)=={'review_id','actual','reason','snapshot_indices'}
  rule=visual[d['review_id']];st=next(s for s in plan['states']if s['id']==rule['state']);allowed={n for n,s in native_checks.bound_state_evidence(obs,st)[0]};assert set(d['snapshot_indices'])<=allowed
  counts['unknown'if d['actual']is None else str(d['actual']).lower()]+=1
  if d['actual']is False:fids.add(rule['id'])
 assert {t['id']for t in j['attributions']}==fids
 attrs+=len(j['attributions'])
 for t in j['attributions']:
  assert set(t)=={'id','cause','reason','snapshot_indices'};r=next(r for r in plan['assertions']if r['id']==t['id']);st=next(s for s in plan['states']if s['id']==r['state']);allowed={n for n,s in native_checks.bound_state_evidence(obs,st)[0]};assert t['snapshot_indices']and set(t['snapshot_indices'])<=allowed
notes={
 'review_identity':'Independent anonymous panel two / T3 / d0. No arm assignment or other reviewer material accessed.',
 'reference':'Approved independent T3 BRIEF/API, reference.json question pointers, policy ownership, lock/approval, bindings, fixtures and original expanded reference PNGs. P2 reference was also inspected as six consecutive original-pixel segments to avoid unreadable whole-strip downsizing. Candidate sources were never used as design baseline.',
 'visual_coverage':{'cases':8,'platforms':['android','ios'],'sources':['source-a','source-b'],'selected_states_per_case':7,'selected_exact_state_frames':652,'unique_viewport_pixel_groups_inspected':422,'case_contact_sheets_inspected':56,'reference_detail_sheets_inspected':2,'original_snapshot_files_hashed':1068,'outside_selected_visual_frames':'Initial, before-update and final duplicate/action frames beyond selected-state evidence were hashed; not every one of those extra frames was visually inspected. All selected-state viewport pixels were inspected, with exact duplicate crops mapped to every original state/index/hash in contact-sheets/index.json.','method':'Original PNGs retained in place. Contact sheets crop only the native iOS viewport (using original native-to-image mapping); Android uses the entire original PNG. Exact crop pixel duplicates are grouped only within the same anonymous source/platform/case. This reduces redundant viewing without using another candidate as reference. Direct original PNG checks confirmed all reported P2 disclosure clipping and representative strict iOS color/replacement failures.'},
 'independent_observations':{
  'android_P1_both_sources':'All three selected full sweeps support readable complete wrapping and separate content areas. Caller revision replacement visibly seeds b, reselecting a adds to b, callback intervals match; frozen numerical facts retained.',
  'android_P2_both_sources':'Both original sources show first-letter portions missing in the fully visible two-line disclosure at baseline, expanded and submitted. This independently answers both clipped-word wrapping and local occlusion propositions false. The two atom manifestations in one state are not distinct product bug counts; all six affected states arise from the same padding/rounded-boundary issue across each respective component. Other long text, service reasons/details, open guidance and updated notice were inspected through the footer.',
  'ios_both_sources':'Baseline disabled primary fill strictly differs from approved opaque role. Component owns final fill and native box lies inside the button; no host-background sampling explanation fits. Source code specifies the palette, while disabled native rendering changes the result. Typography weight remains unsupported U; visual appearance is not a font-weight measurement.',
  'ios_source_a_replacement':'Same-instance changed revision reaches the component (current new notice, input hash and fixture index), yet incoming b is unselected and summary empty; action is disabled. After a is selected, summary and submit callback contain only a. Product selection-replacement failure is supported; exact SwiftUI state/closure implementation mechanism remains an inference.',
  'ios_P2_word_breaks':'Long labels break within a word where its unbroken segment cannot fit the narrow enlarged-text area. BRIEF explicitly permits character breaks preserving all characters. This alone was not judged clipping or overlap.',
  'unknown_source_a_ios_P2_submitted':'The coherent full sweep ends at 5800 of 5805 native content units. Frozen bound_state_evidence withholds full-content coverage despite bottom_reached=true. Both whole-state visual atoms are null with empty cited indices; no supported F is manufactured from this gap. Reselected has the same five-unit coverage limit but no selected qualitative rows.'},
 'limits':['Only the selected catalog propositions are voted. They do not certify unsampled palette areas, every typography/spacing value, every possible incoming model, physical touch regions or full-brief features outside the selected ledger.','Native/pixel numerical results remain frozen-tool facts. Cause assessments are separately reasoned; schema acceptance is not evidence of product quality.','No independent disagreement can be measured without another judge, which was intentionally not read. Same-request duplication in self-check is not independent consensus or human gold.'],
 'decisions':counts,'failure_cause_assessments':attrs,'rejected_attempts':['prepare.rejected-01.py and prepare.rejected-01.txt preserve an f-string syntax failure.','An exploratory rg of a nonexistent iOS sources directory was rejected by the shell; corrected to the referenced compiled-project path.','Four accepted draft-01 judge files preserve an earlier attribution wording containing numeric pixel colors; final judge prose removes those manually supplied pixel actuals without changing the classification or cited evidence.'],
 'schema_validation':'Eight frozen acceptance.evaluate schema/evidence checks accepted, using the same own request as judge one and judge two. Only a later prose removal of manual hex pixel actuals was made; a final local exact-schema, state-scope, observation-hash and complete attribution-set check passed. No supported classification was changed to optimize a report.'
}
(O/'inspection-notes.json').write_text(json.dumps(notes,indent=2)+'\n')
commands={
 'cwd':'/Users/rex/Documents/ChatGPT/mobile-native-skill',
 'read_commands':['cat validation/atomic-forward/prompts/judge-d0-two-T3.txt','find validation/atomic-forward/evaluation-inputs/d0/T3 -type f | sort','Python JSON loads for inputs.json, plan.json, catalog.json, automatic.json, environment-check.json for all 8 cases (initial broad stdout was truncated; later compact extraction and full JSON parsing used instead).','find workspace -path *candidate-v8* -maxdepth 8 -type f | head -50','cat candidate-v8/references/atomic-review.md candidate-v8/references/state-evidence.md','cat design-v2/T3/public/BRIEF.md design-v2/T3/public/API.md; Python loads of policy/reference/approval/bindings/contract and fixtures','rg/sed frozen native_checks.py bound_state_evidence/state_evidence, review_contract.py bind, acceptance.py evaluate and native_pixels.py sample','cat both referenced source capsule BicycleServiceIntake.swift and BicycleServiceIntake.kt','rg/sed original common-corpora source-a iOS P1 compiled-project/ObserverApp.swift and Bridge.swift; Python loaded every original platform case fixture/actions file'],
 'executed_output_scripts':['python3 judgments/d0/two/T3/prepare.py (first rejected SyntaxError retained, corrected run completed)','python3 judgments/d0/two/T3/write_reviews.py','python3 judgments/d0/two/T3/self_check.py (once; output completed in own files after initial shell yield)','python3 judgments/d0/two/T3/finalize.py (this final local audit and seal)'],
 'image_tool':'functions tools.view_image used for both original reference PNGs, every case contact sheet listed in contact-sheets/index.json, reference/P2-0.png and P2-1.png, and direct original PNGs for the Android P2 disclosure baseline/expanded/submitted and iOS baseline/replaced disabled action. Exact original mappings/hashes are retained.',
 'mutations':'Only files under this output root. No production changes, acquisitions, commits, review cross-reading or agent messages.',
 'time_record':'phase.json records actual start immediately after prompt read and actual finish immediately before seal; per-command timestamps were not separately collected. Tool transcript contains execution timing.'
}
(O/'command-history.json').write_text(json.dumps(commands,indent=2)+'\n')
with(O/'commands.log').open('a')as f:f.write('Inspected independent P2 approved PNG at original-pixel segment size (two derived reference sheets). Ran finalize.py: exact JSON keys, observation hashes, all visual review IDs, exact bound-state index sets and complete supported-F attribution IDs checked locally. Finalize writes numeric actual finish time, then SHA256 seals every output file except SEAL.json and __pycache__; no output is edited afterward.\n')
phase=json.loads((O/'phase.json').read_text());t=time.time();phase.update({'finishedAtUnix':t,'finishedAtUTC':datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat(),'elapsedSeconds':t-phase['startedAtUnix'],'status':'complete','sealed':True});(O/'phase.json').write_text(json.dumps(phase,indent=2)+'\n')
files={str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(O.rglob('*'))if p.is_file()and p.name!='SEAL.json'and'__pycache__'not in p.parts}
(O/'SEAL.json').write_text(json.dumps({'files':files},indent=2)+'\n')
# Read-only seal validation; no files are edited after this point.
assert all(hashlib.sha256((O/p).read_bytes()).hexdigest()==h for p,h in files.items())
print(json.dumps({'sealed_files':len(files),'visual_decisions':counts,'attributions':attrs,'elapsedSeconds':phase['elapsedSeconds'],'seal_sha256':hashlib.sha256((O/'SEAL.json').read_bytes()).hexdigest()}))
