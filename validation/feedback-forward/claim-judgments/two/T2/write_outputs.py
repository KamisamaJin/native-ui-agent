from pathlib import Path
import json, hashlib, time, importlib.util, collections
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=ROOT/'claim-judgments/two/T2'
def read(rel): return json.loads((ROOT/rel).read_text())
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
d=read('claim-inputs/T2/inputs.json')
assert sha(ROOT/'claim-inputs/T2/inputs.json')==read('claim-inputs/T2/SEAL.json')['files']['inputs.json']
by={r['key']:r for r in d['initial']}
product=[r['key'] for r in d['initial'] if r['status']=='failed' and r.get('cause_category')=='product']
assert product==[]
viewed={'P1':[1,10,27,49,54],'P2':[2,17,44,80,88]}
observations={case:read(f'corpora/T2/d0/android/{case}/native/observation.json') for case in viewed}
judgment={'claims':{},'clusters':[]}
inspection=[]
for alias,u in d['units'].items():
 decisions={}
 for c in u['claims']:
  o=c['original']; scope=c['original_scope']; indices=o.get('snapshot_indices',[])
  if c['origin']=='machine':
   row=by[scope[0]]; case=row['case']; state=row['state']; selected=[x for x in o['actual']]
   assert all(x['value']=='✓, Wi-Fi only' for x in selected)
   assert row['expected']=='Wi-Fi only' and row['cause_category']=='uncertain'
   snaps=observations[case]['snapshots']
   inspected=[i for i in viewed[case] if snaps[i]['state_id']==state]
   assert inspected
   paths=[f'corpora/T2/d0/android/{case}/native/'+snaps[i]['screenshot'] for i in inspected]
   reason=(f"Original {c['raw']} assertion {o['id']}, snapshots {indices}, really records the strict literal label '✓, Wi-Fi only' against 'Wi-Fi only'; this measurement failure is retained. "
    f"Original PNG(s) {', '.join(paths)} (indices {inspected}) show the complete visible wording plus a decorative checked box. "
    "The original production source submissions/T2/d0/source/reply/Reply/app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt:189–208 exposes selected separately and applies clearAndSetSemantics {} to the decorative Box. "
    f"The original collector corpora/T2/d0/android/{case}/native/sources/NativeObserverTest.kt:88–89,137 walks the unmerged tree and synthesizes labels from descendant Text, including the checkmark. "
    f"evaluation/d0/T2/initial/android/{case}/acceptance.json retains cause uncertainty (the individual source assessments differ between uncertain and observation). "
    "No merged accessibility-service label is exported. This does not independently establish a D0 product failure, nor explicit product-negative evidence strong enough for FP; status U preserves that distinction. Scope remains this original state/label only; no later repair is used.")
   if alias=='source-a':
    inspection.append({'row':scope[0],'strict_status':row['status'],'cause_category':row['cause_category'],'original_snapshot_indices':indices,'viewed_original_snapshot_indices':inspected,'viewed_original_pngs':paths,'classification':'uncertain product attribution; not a confirmed product F','accepted_cause_assessments':row['cause_assessments']})
  elif c['original_status']!='failed':
   first=o.get('evidence',[{}])[0].get('path',c['raw'])
   if c['original_status']=='unassessed':
    reason=(f"Original nonfailure observation in {c['raw']} ({o.get('id')}) is explicitly unassessed, with no snapshot indices and evidence {first}. "
      f"Its exact original scope is {len(scope)} status-leading-clear rows; those rows remain unassessed in the D0 acceptance set. The original report says the full-strip pixel support is insufficient/conflicting. "
      "This is neither a product alarm nor evidence of a false product alarm; U, outside the alarm denominator. It gives no detection credit and is not expanded to other style or behavior rows.")
   else:
    extra=("The record has an empty original_scope, so no acceptance-row support may be manufactured from its descriptive text. " if not scope else f"Its {len(scope)} original scoped rows are nonfailure observations; no failure is asserted. ")
    reason=(f"Original passed visual observation in {c['raw']} ({o.get('id')}), original snapshot indices {indices}, evidence beginning {first}. "
      +extra+"U is the required nonalarm classification, outside the alarm denominator; it does not mean that the original visual pass was disproved. "
      "The qualitative/original scope is retained without converting it into a label, numeric-style, business-behavior, or later-repair alarm.")
  else:
   raise AssertionError('Unexpected alarm type')
  decisions[c['claim_id']]={'status':'U','supported_rows':[],'reason':reason}
 judgment['claims'][alias]=decisions
save('judgment.json',judgment)
save('d0-cause-assessment.json',{'confirmed_product_rows':product,'product_cause_groups':[],'strict_failures':inspection,'reason':'All ten strict failed D0 rows have unresolved product versus observation attribution; none is confirmed product. No product cause membership is asserted. The same original Android code path repeats across the states, but that alone does not promote uncertain measurement failures to product bugs.','source_acceptance_counts':read('evaluation/source/d0/T2/initial/acceptance.json')['counts']})
paths={
'operators/claims-two-T2-delivered.txt','claim-inputs/T2/inputs.json','claim-inputs/T2/SEAL.json','metrics.py',
'submissions/T2/d0/source/reply/Reply/app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt',
'evaluation/source/d0/T2/initial/acceptance.json',
'corpora/T2/d0/corpus.json','corpora/T2/d0/portable-scope.json',
'source-evaluation-inputs/d0/T2/initial/inputs.json','source-evaluation-inputs/d0/T2/initial/catalog.json',
'source-evaluation-inputs/final/T2/source-a/inputs.json','source-evaluation-inputs/final/T2/source-b/inputs.json',
'submissions/u-5184cc6d/agent-output/repair.json','submissions/u-695819ff/agent-output/repair.json'}
for p in ['android','ios']:
 for case in ['P1','P2']: paths.add(f'evaluation/d0/T2/initial/{p}/{case}/acceptance.json')
for case,obs in observations.items():
 for name in ['observation.json','sources/NativeObserverTest.kt']: paths.add(f'corpora/T2/d0/android/{case}/native/{name}')
 for name in ['request.json','source-before.json','automatic.json']:paths.add(f'corpora/T2/d0/android/{case}/{name}')
 for i in viewed[case]: paths.add(f'corpora/T2/d0/android/{case}/native/'+obs['snapshots'][i]['screenshot'])
evidence_checks=[]
for alias,u in d['units'].items():
 for c in u['claims']:
  paths.add(c['raw'])
  for e in c['original'].get('evidence',[]):
   p=Path(e['path']);p=p if p.is_absolute() else ROOT/p
   assert p.is_relative_to(ROOT)
   paths.add(str(p.relative_to(ROOT)))
   actual=sha(p)
   evidence_checks.append({'alias':alias,'claim_id':c['claim_id'],'path':str(p.relative_to(ROOT)),'expected_sha256':e.get('sha256'),'actual_sha256':actual,'matches':actual==e.get('sha256')})
assert all(e['matches'] for e in evidence_checks)
save('input-hashes.json',{'files':{p:sha(ROOT/p) for p in sorted(paths)},'original_claim_evidence_hash_checks':evidence_checks,'scope':'Hashes bind the permitted inputs and referenced original claim evidence. Hash verification is not a claim that every PNG received visual review. Final input metadata and repair-report keys were inspected to locate references; final success and later repairs were not used for original detection or D0 cause credit.'})
save('limits.json',{'task':'T2','panel':'two','original_record_counts':{a:dict(collections.Counter(c['original_status'] for c in u['claims'])) for a,u in d['units'].items()},'decision_counts':{a:dict(collections.Counter(v['status'] for v in x.values())) for a,x in judgment['claims'].items()},'limits':['AI judgment is not human gold.','All machine alarms retain their measured strict mismatch, while product attribution remains unresolved without a merged accessibility-service label. A screenshot cannot prove a TalkBack pass or failure.','No FP is asserted without explicit original-evidence-negative support; no TP is asserted without an independently confirmed product-F row.','All original passed/unassessed manual records receive U and remain outside the alarm denominator. Empty scopes are preserved.','The supplied D0 initial set contains no confirmed product-F rows, so the product cause-group list is empty; this is not a claim that unknown rows pass.','Only the ten listed original alarm PNGs were directly viewed; other original evidence PNGs were hash checked and nonalarm manual records were evaluated as records, not recertified visually.','No later repair success, hidden FINAL failure, shared source, or later state is used to expand original detection scope.','No source/expected changes, SDK calls, commits, other panel outputs, assignment contents, or messages to other agents were used.','An initial broad filename inventory under evaluation exposed other-task filenames only; no other-task contents were opened.','The start timestamp is the first recorded wall-clock reading after the operator text was read, before substantive claim inspection; earlier operator-read seconds were not separately timed.']})
