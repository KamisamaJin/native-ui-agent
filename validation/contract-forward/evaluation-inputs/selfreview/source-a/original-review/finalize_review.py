from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,collections
base=Path(__file__).resolve().parent.parent;out=base/'agent-output'
r=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p)}
implementation=json.loads((out/'implementation.json').read_text())
source_verified={path:sha(path)==digest for path,digest in implementation['source_sha256'].items()}
assert all(source_verified.values())
seal=json.loads((out/'plans-seal.json').read_text());plans_verified={name:sha(out/name)==digest for name,digest in seal['files'].items()};assert all(plans_verified.values())
assessed=[];unassessed=[];findings=[];original_reports=[];review_reports=[];original_unassessed=[];na=[];corpora=[];original_counts=collections.Counter();updated_counts=collections.Counter()
for case in ['P1','P2']:
 for platform in ['ios','android']:
  orig=r/'submissions/unit-092e15/own-checks/d0'/case/platform/'report.json'
  fresh=out/'review-checks'/case/platform/'report.json'
  corpus=r/('own-retries' if platform=='ios' and case=='P2' else 'own-corpora')/'unit-092e15/d0'/platform/case
  obs_path=corpus/'observation.json';obs=json.loads(obs_path.read_text())
  manifest=json.loads((corpus/'manifest.json').read_text())
  plan_path=r/'submissions/unit-092e15/initial-agent-output/plans'/case/platform/'plan.json';plan=json.loads(plan_path.read_text())
  assert sha(plan_path)==sha(out/'plans'/case/platform/'plan.json')
  expected={a['id']:a for a in plan['assertions']}
  a=json.loads(orig.read_text());b=json.loads(fresh.read_text());original_counts.update(a['counts']);updated_counts.update(b['counts'])
  original_reports.append({'case':case,'platform':platform,**ref(orig),'counts':a['counts'],'command':ref(orig.parent/'command.json'),'command_log':ref(orig.parent/'command.log')})
  review_reports.append({'case':case,'platform':platform,**ref(fresh),'counts':b['counts'],'manual':ref(fresh.parent/'manual.json')})
  original_unassessed.extend({'case':case,'platform':platform,**row} for row in a['assertions'] if row['status']=='unassessed')
  for cell in a['matrix_contract']['cells']:
   if cell.get('disposition')=='not_applicable' or cell.get('status')=='not_applicable':na.append({'case':case,'platform':platform,**cell})
  for row in b['assertions']:
   exp=expected[row['id']];manual=exp['kind']=='manual'
   evidence=[ref(fresh if manual else orig)]
   evidence.extend(ref(corpus/obs['snapshots'][i]['screenshot']) for i in row['snapshot_indices'])
   entry={'case':case,'platform':platform,'state':row['state'],'id':row['id'],'requirement_id':exp.get('requirement_id'),'kind':exp['kind'],'origin':'manual_visual_review' if manual else 'original_typed_native_check','status':row['status'],'expected':exp.get('expected'),'unit':exp.get('unit'),'actual':row.get('actual'),'reason':row['reason'],'snapshot_indices':row['snapshot_indices'],'evidence':evidence}
   (unassessed if row['status']=='unassessed' else assessed).append(entry)
   if row['status']=='failed':
    entry=dict(entry);entry['aspect']=exp.get('requirement_id');entry['finding_id']=f'{case}/{platform}/{row["id"]}';entry['duplicate_of_original_typed_failure']=True
    entry['interpretation']='The frozen checker exports 47.99994000000004dp and strictly compares it with the independent 48dp lower bound. This exact typed contradiction is retained. The size difference is not visually resolvable here; serialization/coordinate precision is a possible explanation, not an established excuse or permission to change expected values. No failure is copied into the three states with conflicting geometry.'
    findings.append(entry)
  corpora.append({'case':case,'platform':platform,'observation':ref(obs_path),'manifest':ref(corpus/'manifest.json'),'test_log':ref(corpus/'test.log'),'manifest_status':manifest['status'],'native_test_exit':manifest.get('test_exit_code',manifest.get('exit_code')),'actual_environment':manifest.get('actual_environment',obs.get('configuration')),'actual_viewport':manifest.get('actual_viewport',obs['snapshots'][0].get('logical_viewport_dp')),'complete_initial_browse':next(s for s in obs['state_captures'] if s['state_id']=='browse')['complete']})
# A candid visual concern, outside the selected numeric rule families. No invented failure.
concern_corpus=r/'own-corpora/unit-092e15/d0/ios/P1';concern_obs=json.loads((concern_corpus/'observation.json').read_text());ci=19
findings.append({'finding_id':'P1/ios/reserved/disabled-readability-concern','case':'P1','platform':'ios','state':'reserved','aspect':'disabled-readability','requirement_id':None,'origin':'manual_visual_review','status':'needs_review','expected':'Disabled options retain readable labels while showing a native disabled affordance (BRIEF.md prose; outside the 24 selected numerical families).','actual':'Disabled option text and selected surfaces are very pale in the light-theme confirmation frame. Labels are still decipherable when inspected, but readability is visibly weaker than the enabled options and the public wireframe.','reason':'Qualitative concern only. No computed color, contrast ratio, or categorical readability failure is established from this review. It does not duplicate the height findings and is not copied to other states.','snapshot_indices':[ci],'evidence':[ref(concern_corpus/concern_obs['snapshots'][ci]['screenshot'])]})
start=json.loads((out/'review-start.json').read_text())['start_utc'];end=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
review={
 'phase':'read_only_original_self_review','start_utc':start,'end_utc':end,'wall_seconds':(datetime.fromisoformat(end.replace('Z','+00:00'))-datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds(),'budget_minutes':12,
 'approved_design_lock_sha256':'c2548a601384046a016e98258728877982f30a4ed25be22455d9ec9ea4399bc1',
 'status':'typed_failures_and_unassessed_retained','findings':findings,'assessed_rows':assessed,'unassessed':unassessed,
 'original_typed_report_references':original_reports,'manual_enriched_report_references':review_reports,'original_typed_counts':dict(original_counts),'after_manual_counts':dict(updated_counts),'original_typed_unassessed_rows_preserved':original_unassessed,
 'matrix_dispositions':{'original_total_cells':528,'original_assertions':502,'not_applicable_cells':26,'note':'Independent N/A dispositions remain in the original and fresh reports unchanged.'},
 'capture_references':corpora,
 'visual_inspection':{'browse':'Viewed every overlapping browse image for all four case/platform pairs, spanning initial content to the bottom. These frozen public cases exercise light/LTR and narrow/dark/RTL/large text.','transitions':'Viewed the full target-frame unions for each named action and replacement state via contact sheets, with actual indices and original image paths in the two review-artifacts image-index JSON files.','reserve_label':'22 exact state/platform manual rows passed only the complete Reserve seats label visibility check. Each decision is bound to its observation digest, actual original screenshot hash and snapshot index.','comparison':'Compared structure, vertical stacking, wrapping, direction, selected-state appearance and label visibility with the frozen P1/P2 reference PNGs already read during implementation. Native font baselines are not treated as pixel exact.','additional_confirmed_manual_failures':0},
 'source_unchanged_verification':source_verified,'original_plans_support_unchanged_verification':plans_verified,
 'limits':[
  'Read-only review: no production changes, plan/expected-value edits, new native render, app launch or repair.',
  'Original typed reports are authoritative within their exported scope and are preserved; manual decisions only add Reserve-label visibility judgments.',
  '33 iOS title font/color/detail ellipsis cells remain U because public AX does not expose these computed fields. Pixels and source declarations do not replace them.',
  'Both P2 blocked/activation callback rows remain U: enabled=false and no attempted successful dispatch. Empty event intervals are not callback-behavior passes.',
  'Android P2 reserve-height remains U for blocked, course-changed and reserved because the same-state frames disagree between 48.0 and 47.99994dp. These are not treated as passes or copied failures.',
  'Three Android P2 reserve-height typed failures remain exactly as supplied: browse, editing, replaced. No tolerance or design value was changed.',
  'iOS P2 uses the explicit common width-adapter retry. Runtime actual viewport is 300 by 600pt, not the requested 640pt height. Its manifest/test status is failed after the expected disabled control was unavailable; later bound snapshots and successful requested dispatches still exist and are assessed individually. The original failure is not hidden.',
  'Android uses native Compose semantic OnClick, not physical touchscreen dispatch. Native selected/enabled facts are distinct from OS touch coverage.',
  'Only browse has complete overlapping full-content evidence in these selected plans. Post-action target unions do not establish a full-page or whole-card visual acceptance claim.',
  'Exact internal padding, corner radius, gaps, other fonts/colors, layout allocations, course-description clipping and whole-card similarity are outside the selected numerical denominator. No unmeasured prose style token is silently passed.',
  'Manual review is fallible. The pale disabled iOS P1 confirmation labels are recorded as a qualitative concern, not an invented categorical failure.'
 ],
 'inspection_attempts':[
  {'status':'preserved','description':'All original command exit codes/logs and typed P/F/U results are referenced. Four fresh manual-enriched checker invocations ran successfully as check processes and retain their semantic exit statuses 3,0,3,1.'},
  {'status':'uncertain','description':'The Android 0.00006dp lower-bound discrepancy may involve exported coordinate precision; no new capture was permitted and no causal claim is made.'}
 ]
}
(out/'review.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
artifacts=[out/'review.json',out/'review-start.json',out/'review_sheets.py',out/'review_remaining_sheets.py',out/'review_manual_checks.py',Path(__file__)]
artifacts+=sorted(p for folder in [out/'review-artifacts',out/'review-checks'] for p in folder.rglob('*') if p.is_file())
(out/'review-seal.json').write_text(json.dumps({'sealed_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'artifacts':{str(p):sha(p) for p in artifacts},'source_unchanged':all(source_verified.values()),'original_plans_unchanged':all(plans_verified.values())},indent=2)+'\n')
print(json.dumps({'start_utc':start,'end_utc':end,'wall_seconds':review['wall_seconds'],'original_typed_counts':dict(original_counts),'after_manual_counts':dict(updated_counts),'failed_findings':sum(f['status']=='failed' for f in findings),'manual_concerns':sum(f['status']=='needs_review' for f in findings),'sealed_artifacts':len(artifacts)},indent=2))
