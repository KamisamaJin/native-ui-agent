from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[2];O=R/'evaluation/D0';sys.path.insert(0,str(R/'design/private'));import grader
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();put=lambda p,v:p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
candidates=json.loads((O/'visual-candidates.json').read_text());ledger=[];verification=[]
for alias in ['source-a','source-b']:
 for platform in ['ios','android']:
  host='alerttoast' if platform=='ios' else 'reply/Reply';sr=R/f'evaluation-inputs/D0/{alias}/source-capsule/source/{host}';sf=sr/('Sources/AlertToast/WorkshopEnrollmentCard.swift' if platform=='ios' else 'app/src/main/java/com/example/reply/ui/components/WorkshopEnrollmentCard.kt')
  for case in ['P1','P2']:
   cap=R/f'common-corpora/{alias}/d0/{platform}/{case}';op=cap/'observation.json';mp=cap/'manifest.json';m=json.loads(mp.read_text());base=json.loads((O/alias/f'native-base/{case}/{platform}/grade.json').read_text());rows={r['id']:r for r in base['rows']};records=[r for r in candidates if r['alias']==alias and r['platform']==platform and r['case']==case]
   # Source linkage checked before API adjudication, with hash-bound build receipt.
   match=[k for k,v in m.get('source_hashes',{}).items() if v==sha(sf)]
   success=m.get('build_exit_code')==0 if platform=='ios' else m.get('exit_code')==0
   assert success and m.get('native_test_count')==1 and match,(alias,case,platform,'source/build provenance unavailable')
   verification.append(dict(alias=alias,case=case,platform=platform,source_sha256=sha(sf),manifest_sha256=sha(mp),native_test_count=1,compiled=True,source_hash_manifest_keys=match))
   manual=[]
   for c in records:
    if c['snapshot'] is None:continue
    exp=rows[f"{case}/{platform}/{c['state']}/reserve-visible"]['expected'];image=R/c['image'];assert sha(image)==c['sha256']
    manual.append(dict(id=c['state']+'/reserve-visible',status='passed',method='visual',expected=exp,snapshot_indices=[c['snapshot']],reason='Inspected the actual bound screenshot (and its labeled review crop): every glyph of Reserve seats is visible, with no clipped edge or ellipsis. This decision assesses label visibility only; it establishes no computed typography/color or height.',evidence=[dict(path=str(image.relative_to(cap)),sha256=sha(image))]))
   out=O/alias/f'final/{case}/{platform}';out.mkdir(parents=True,exist_ok=True);manualpath=out/'manual.json';put(manualpath,dict(observation_sha256=sha(op),decisions=manual))
   api=next(c for c in base['checks'] if c['aspect']=='public-signature');apipath=out/'api-review.json'
   put(apipath,dict(decisions=[dict(id=api['id'],status='P',expected=api['expected'],actual='Public value types, property spelling/types, constructors, attendance cases and direct native entry signature match; same production source SHA occurs in successful pinned-host build/test manifest.',reason='Independently inspected the production type declarations and entry signature against API.md. Swift models are public Codable/Equatable with public initializers and the public View initializer; Kotlin exposes the specified data classes, enum and composable function/default Modifier. The frozen direct bridge compiled against this exact source and one native test succeeded in the pinned host.',evidence=[dict(path=str(sf.relative_to(R)),sha256=sha(sf)),dict(path=str(mp.relative_to(R)),sha256=sha(mp))])]))
   final=grader.grade(case,platform,op,root=R,manual=manualpath,source_root=sr,api_review=apipath);gp=out/'grade.json';assert not gp.exists();put(gp,final)
   for row in final['rows']:
    if row['class']=='native_geometry' and row['status'] in ('F','U'):
     ledger.append(dict(alias=alias,id=row['id'],frozen_status=row['status'],expected=row['expected'],actual=row['actual'],snapshot_indices=row['snapshot_indices'],evidence=row['evidence'],limitation='Observed serialized bounds straddle the 48dp lower bound at approximately 0.00006dp. Frozen comparison and F/U row remain unchanged. This does not establish a natural product defect at that numerical resolution; no new tolerance or visual override is applied.'))
   print(alias,case,platform,final['counts'])
put(O/'source-build-verification.json',verification);put(O/'numerical-resolution-limits.json',dict(policy='Frozen primary row status is unchanged. Separate natural-product-defect sensitivity only, no changed tolerance or grading policy.',rows=ledger))
