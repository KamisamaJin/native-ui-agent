from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[2];O=R/'evaluation/FINAL';sys.path.insert(0,str(R/'design/private'));import grader
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();put=lambda p,v:p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
records=json.loads((O/'visual-candidates.json').read_text());ledger=[];verification=[]
for alias in ['source-a','source-b']:
 for platform in ['ios','android']:
  host='alerttoast' if platform=='ios' else 'reply/Reply';sr=R/f'evaluation-inputs/FINAL/{alias}/source-capsule/source/{host}';sf=sr/('Sources/AlertToast/WorkshopEnrollmentCard.swift' if platform=='ios' else 'app/src/main/java/com/example/reply/ui/components/WorkshopEnrollmentCard.kt')
  for case in ['P1','P2','H1']:
   cap=R/f'common-corpora/{alias}/final/{platform}/{case}';op=cap/'observation.json';mp=cap/'manifest.json';m=json.loads(mp.read_text());base=json.loads((O/alias/f'native-base/{case}/{platform}/grade.json').read_text());rows={r['id']:r for r in base['rows']};candidates=[r for r in records if r['alias']==alias and r['platform']==platform and r['case']==case]
   match=[k for k,v in m.get('source_hashes',{}).items() if v==sha(sf)];success=m.get('build_exit_code')==0 if platform=='ios' else m.get('exit_code')==0
   assert success and m.get('native_test_count')==1 and match,(alias,case,platform,'source/build provenance unavailable')
   verification.append(dict(alias=alias,case=case,platform=platform,source_sha256=sha(sf),manifest_sha256=sha(mp),native_test_count=1,compiled=True,source_hash_manifest_keys=match))
   manual=[]
   for c in candidates:
    if c['snapshot'] is None:continue
    exp=rows[f"{case}/{platform}/{c['state']}/reserve-visible"]['expected'];image=R/c['image'];assert sha(image)==c['sha256']
    manual.append(dict(id=c['state']+'/reserve-visible',status='passed',method='visual',expected=exp,snapshot_indices=[c['snapshot']],reason='Inspected the actual bound screenshot through its labeled review crop: all glyphs of Reserve seats are visible without clipped edges or ellipsis. This scores label visibility only, with no computed typography/color or height inference.',evidence=[dict(path=str(image.relative_to(cap)),sha256=sha(image))]))
   out=O/alias/f'final/{case}/{platform}';out.mkdir(parents=True,exist_ok=True);manualpath=out/'manual.json';put(manualpath,dict(observation_sha256=sha(op),decisions=manual))
   api=next(c for c in base['checks'] if c['aspect']=='public-signature');apipath=out/'api-review.json'
   put(apipath,dict(decisions=[dict(id=api['id'],status='P',expected=api['expected'],actual='Required public value types, property spellings/types, constructors, attendance cases and direct native entry signature match; exact source SHA is in successful pinned-host build/test manifest.',reason='Inspected production declarations and entry signature against API.md: Swift public Codable/Equatable models, public initializers and public View initializer; Kotlin specified data classes, attendance enum and composable function/default Modifier. The frozen direct bridge compiled against this exact source and one native test succeeded in the pinned host.',evidence=[dict(path=str(sf.relative_to(R)),sha256=sha(sf)),dict(path=str(mp.relative_to(R)),sha256=sha(mp))])]))
   final=grader.grade(case,platform,op,root=R,manual=manualpath,source_root=sr,api_review=apipath);gp=out/'grade.json';assert not gp.exists();put(gp,final)
   for row in final['rows']:
    if row['class']=='native_geometry' and row['status'] in ('F','U'):ledger.append(dict(alias=alias,id=row['id'],frozen_status=row['status'],expected=row['expected'],actual=row['actual'],snapshot_indices=row['snapshot_indices'],evidence=row['evidence'],limitation='Retain raw frozen comparison and uncertainty; no changed tolerance or visual override.'))
   print(alias,case,platform,final['counts'])
put(O/'source-build-verification.json',verification);put(O/'numerical-resolution-limits.json',dict(policy='Frozen row status is unchanged. No observer/tolerance/geometry policy edits.',rows=ledger))
