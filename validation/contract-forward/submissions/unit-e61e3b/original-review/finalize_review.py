from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json,hashlib
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward')
o=b/'cache/unit-e61e3b/agent-output'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def evidence(p):return {'path':str(p),'sha256':sha(p)}
roots={('ios','P1'):b/'own-corpora/unit-e61e3b/d0/ios/P1',('ios','P2'):b/'own-retries/unit-e61e3b/d0/ios/P2',('android','P1'):b/'own-corpora/unit-e61e3b/d0/android/P1',('android','P2'):b/'own-corpora/unit-e61e3b/d0/android/P2'}
assessed=[];unknown=[];references=[];findings=[];corpora=[]
for (p,c),d in roots.items():
 original_path=b/f'submissions/unit-e61e3b/own-checks/d0/{c}/{p}/report.json'
 original=read(original_path)
 plan_path=b/f'submissions/unit-e61e3b/initial-agent-output/plans/{c}/{p}/plan.json'
 plan=read(plan_path);items={x['id']:x for x in plan['assertions']}
 review_path=o/f'review-checks/{c}/{p}/report.json'
 report=read(review_path)
 observation=read(d/'observation.json')
 command=original_path.parent/'command.json'
 references.append({'case':c,'platform':p,'report':evidence(original_path),'command':evidence(command),
                    'log':evidence(original_path.parent/'command.log'),'original_counts':original['counts'],
                    'manual_enriched_report':evidence(review_path),'manual_enriched_counts':report['counts']})
 for row in report['assertions']:
  item=items[row['id']]
  unit=json.loads(item['source']).get('original_value',{}).get('unit')
  paths=[d/observation['snapshots'][i]['screenshot']for i in row['snapshot_indices']]
  erow={'case':c,'platform':p,'state':row['state'],'id':row['id'],
        'requirement_id':item['requirement_id'],'aspect':item.get('property',item['kind']),
        'expected':item.get('expected'),'unit':unit,'status':row['status'],
        'origin':'manual_visual' if item['kind']=='manual' else 'original_typed_native',
        'reason':row['reason'],'snapshot_indices':row['snapshot_indices'],
        'evidence':[evidence(review_path),evidence(original_path)]+[evidence(x)for x in paths]}
  if row['status']=='unassessed':
   if p=='ios' and item['kind']=='text_layout':
    erow['limit']='Unsupported generic SwiftUI computed style/ellipsis remains U; source/visual guesses cannot replace the native fact.'
   elif item['requirement_id']=='reserve-height' and p=='android':
    erow['limit']='Original plan requested ax_height, but this observer exports Android bounds rather than a frame. Native bounds retained separately; original row remains U.'
   elif item['requirement_id']=='activation':
    erow['limit']='Disabled action was not successfully dispatched. Empty callback interval cannot establish quiet behavior.'
   erow['actual']=row.get('actual');unknown.append(erow)
  else:
   # The full native value/resolution is retained by the SHA-bound original report.
   if item['kind']=='event':erow['actual']=row['actual']
   elif item['kind']=='manual':erow['actual']='Complete Reserve seats label visible with no clipped glyphs or ellipsis.'
   else:erow['actual_reference']={'report_path':str(original_path),'assertion_id':row['id']}
   assessed.append(erow)
  if row['status']=='failed':findings.append(erow)
 corpora.append({'case':c,'platform':p,'observation':evidence(d/'observation.json'),'manifest':evidence(d/'manifest.json'),
                 'test_log':evidence(d/'test.log'),'native_status':read(d/'manifest.json')['status'],
                 'full_initial_coverage':report['states']['browse'],
                 'runtime':observation.get('original_runtime',observation.get('configuration'))})
# Qualitative concerns are deliberately separate from selected numerical failures.
for c,state,index in [('P1','reserved',18),('P1','reserved-again',25),('P2','reserved',30)]:
 d=roots[('ios',c)];obs=read(d/'observation.json');shot=d/obs['snapshots'][index]['screenshot']
 findings.append({'case':c,'platform':'ios','state':state,'aspect':'Disabled text legibility',
   'requirement_id':'unmapped.disabled-readability','status':'needs_review','origin':'manual_only_qualitative',
   'expected':'Disabled options use native disabled affordance while remaining readable (BRIEF.md).',
   'unit':None,'actual':'Disabled option and Reserve text look substantially fainter than the surrounding total/status and enabled Edit label.',
   'reason':'Visual concern in the directly inspected reserved frame. All Reserve glyphs remain present and unclipped, so reserve-visible passes. No resolved color, contrast ratio, or precise legibility threshold is measured; this is not a confirmed numerical failure.',
   'snapshot_indices':[index],'evidence':[evidence(shot),evidence(d/'observation.json')]})
start=read(o/'review-start.json')['start_utc']
now=datetime.now(timezone.utc)
before=read(o/'review-before-hashes.json')
changed=[p for p,s in before.items()if sha(Path(p))!=s]
assert not changed,changed
source_hashes=read(o/'implementation.json')['source_sha256']
assert all(sha(Path(p))==s for p,s in source_hashes.items())
counts=Counter(x['status'] for x in assessed+unknown)
review={
 'phase':'Read-only original self-review', 'start_utc':start,'end_utc':now.isoformat(),
 'wall_seconds':(now-datetime.fromisoformat(start)).total_seconds(),'budget_wall_seconds':720,
 'status':'needs_review','findings':findings,'assessed_rows':assessed,'unassessed':unknown,
 'counts':dict(counts),'confirmed_failed_rows':sum(x['status']=='failed'for x in findings),
 'manual_visual_rows':sum(x['origin']=='manual_visual'for x in assessed),
 'original_typed_report_references':references,'corpora':corpora,
 'read_only_verification':{'source_matches_initial_delivery':True,'sealed_inputs_evidence_unchanged':True,
                           'verified_file_count':len(before),'before_hashes':evidence(o/'review-before-hashes.json')},
 'inspection_records':[
  {'status':'resolved','case':'P2','platform':'android','state':'replaced','snapshot_indices':[40],
   'reason':'A contact-sheet thumbnail display was uncertain. The full original screenshot and native-frame crop were inspected; Reserve label is complete. No product clipping finding was made.'},
  {'status':'retained_observer_failure','case':'P2','platform':'ios','state':'blocked','snapshot_indices':[11],
   'reason':'Native XCUITest executed once and failed with native control not enabled or no usable visible point; dispatch says enabled=false, attempted=false, succeeded=false. Later named states were still captured with successful dispatch receipts. Empty interval stays U.',
   'evidence':[evidence(roots[('ios','P2')]/'test.log'),evidence(roots[('ios','P2')]/'manifest.json')]},
  {'status':'retained_log_error','case':'P2','platform':'ios',
   'reason':'Original test.log also ends with xcrun unable to find simctl. No environment repair attempted; observation and manifests are preserved.',
   'evidence':[evidence(roots[('ios','P2')]/'test.log')]}
 ],
 'limits':[
  'No production, original plan/action, expected value, or original capture changed. No new native capture, application launch, or repair was performed.',
  'All four original typed reports had zero failed rows. After 22 separate SHA-bound Reserve-label visual decisions, the unchanged checker reports 467 passed, zero failed, and 57 unassessed assertions; 26 independent N/A matrix cells remain outside that assertion count.',
  'iOS generic title font lower/upper, title color, and detail ellipsis remain U in all 11 states. These 44 atomic rows cannot be established by these screenshots.',
  'Both P2 blocked-action callback rows remain U: a disabled activation was not successfully dispatched. Later course change, reservation, edit, and caller replacement callbacks are gated by successful native receipts.',
  'All 11 original Android Reserve-height rows remain U because the frozen plan used ax_height. Observed semantic bounds are retained in supplemental-native-geometry.json without changing the plans or upgrading the original verdict.',
  'Reserve-label visibility says only that the full label is present with no clipping/ellipsis. It does not establish resolved color/contrast, typography, padding, physical hit regions, or complete-card style acceptance.',
  'Browse has proven overlapping full-content coverage on all four captures. Later named states use target sets with complete=false; their target screenshots cannot establish full-state pixel coverage.',
  'Native iOS P2 retry reports a 300pt offered width, approximately 300.333pt content width after pixel rounding, and a 600pt viewport. Android is 300dp/640dp at fontScale1.3 RTL. Environment is taken from runtime facts.',
  'Root supplied the iOS P2 retry after the original frozen CLI rejected width300; no common adapter code or unrelated corpus was inspected. The retry failure is preserved and is not flattened into whole-run product success.',
  'Manual-only faint-disabled-text concerns were observed in exactly the listed iOS reserved frames; no exact style violation or copied state verdict is asserted.',
  'Wireframes guide structure and wrapping, not pixel-exact native font baselines. Whole-card similarity, course-description clipping and numerical nonselected visual tokens were not accepted by this review.',
 ],
 'next_phase':'Stopped after sealing read-only review. No repair until root resumes.'
}
(o/'review.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
reviewfiles=[p for p in o.glob('review*')if p.is_file() and p.name!='review-seal.json']+[o/'finalize_review.py']+[p for p in (o/'review-checks').rglob('*')if p.is_file()]
seal={'sealed_utc':datetime.now(timezone.utc).isoformat(),'scope':'Original read-only review artifacts; source/plans/native evidence unchanged.',
      'files':{str(p.relative_to(o)):sha(p)for p in sorted(set(reviewfiles))}}
(o/'review-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'start_utc':start,'end_utc':review['end_utc'],'wall_seconds':review['wall_seconds'],'counts':review['counts'],'manual_rows':review['manual_visual_rows'],'confirmed_failures':review['confirmed_failed_rows'],'qualitative_concerns':len(findings),'verified_unchanged_files':len(before),'sealed_review_files':len(seal['files'])},indent=2))
