from pathlib import Path
from collections import Counter
import json,hashlib,datetime
R=Path(__file__).resolve().parents[2];O=R/'evaluation/FINAL';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();put=lambda p,v:p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');summary={};acquisition=[]
for alias in ['source-a','source-b']:
 data={}
 for phase in ['native-base','final']:
  rows=[];checks=[];states={}
  for case in ['P1','P2','H1']:
   for platform in ['ios','android']:
    g=json.loads((O/alias/phase/case/platform/'grade.json').read_text());assert len(g['rows'])==(144 if case=='P2' else 120);rows+=g['rows'];checks+=g['checks'];states[case+'/'+platform]=g['counts']
    if phase=='native-base':
     cap=R/f'common-corpora/{alias}/final/{platform}/{case}';m=json.loads((cap/'manifest.json').read_text());obs=json.loads((cap/'observation.json').read_text());acquisition.append(dict(alias=alias,case=case,platform=platform,manifest=str((cap/'manifest.json').relative_to(R)),manifest_sha256=sha(cap/'manifest.json'),status=m.get('status'),native_test_count=m.get('native_test_count'),exit_code=m.get('build_exit_code') if platform=='ios' else m.get('exit_code'),unassessed_rows=[dict(id=r['id'],**{'class':r['class']},reason=r['reason'],evidence=r['evidence']) for r in g['rows'] if r['status']=='U' and r['class']!='visual']))
  data[phase]=dict(cells=len(rows),counts={s:sum(r['status']==s for r in rows) for s in ['P','F','U','N/A']},by_case_platform=states,by_class={klass:{s:sum(r['class']==klass and r['status']==s for r in rows) for s in ['P','F','U','N/A']} for klass in sorted({r['class'] for r in rows})},separate_input_API_checks={s:sum(r['status']==s for r in checks) for s in ['P','F','U','N/A']},natural_business_defect_recall='N/A: zero established natural business defects',natural_style_defect_recall='N/A: zero established natural style defects')
  assert len(rows)==768
  if phase=='final':assert all(r['status']=='P' for r in checks)
 summary[alias]=data
put(O/'summary.json',dict(stage='FINAL',cases=['P1','P2','H1'],arms=summary,scope='Independent anonymous FINAL grades only. No paired collector captures or original self-reviews inspected. No comparison/repair metrics before separately authorized self-review batch.',numerical_resolution_ledger='numerical-resolution-limits.json',primary_failed_rows=[]));put(O/'acquisition-and-coverage-ledger.json',dict(policy='Acquisition gaps are U, not product defects. Runtime current facts are distinct from successful-stimulus transition evidence.',captures=acquisition))
(O/'REPORT.md').write_text('''# Anonymous FINAL evaluation

Both anonymous FINAL arms were graded against the unchanged design and SDK-free grader. P1/P2 and the previously hidden H1 are included. Each arm retains the complete768 runtime cells:24 families ×16 selected states ×two platforms, with all U and N/A intact. No assignment, builder discussion, original review, own corpus, paired collector capture, or source repair was accessed or performed. D0 files were not written.

| Arm | Phase | P | F | U | N/A |
|---|---|---:|---:|---:|---:|
| source-a | native-base |642|0|82|44|
| source-a | final |674|0|50|44|
| source-b | native-base |642|0|82|44|
| source-b | final |674|0|50|44|

Every per-case/platform native-base grade was retained with manual=None and no API adjudication before visual/source review. Final adds32 scoped visual passes per arm. All64 Reserve-label images were inspected through crops from the exact bound original screenshots; all glyphs are visible without clipping or ellipsis. Each manual decision names its original screenshot, SHA256, state and snapshot index. This establishes label visibility only, not exact computed font/color, full visual similarity, physical touch or internal layout allocation.

Both APIs match public/API.md: public model/type/property/constructor and entry signatures, attendance cases and default Kotlin Modifier. The source hash appears in each successful pinned-host build/native-test receipt. Each arm has24 separate final input/API rows, all P. These checks do not add runtime passes. Exact frozen fixture/action hashes match. All12 named acquisitions succeeded with one native test each; no acquisition failure is treated as a logic defect. Acquisition/coverage-ledger.json preserves each receipt and unassessed row reason.

There are no frozen F rows in either arm, including H1 course removal, capacity reconciliation and fully unavailable catalog states. Natural business/style defect recall is N/A because those denominators are zero. This does not establish behavior outside selected states or unscored visual tokens. All current-state formula/selection/status observations remain distinct from business-transition proof. Disabled P2 In-person activations remain U for callback behavior on both platforms because successful dispatch was not established; quiet intervals cannot pass that behavior check.

The50 final U rows per arm are48 public-iOS computed text style/layout cells plus two gated disabled-action callback cells. Android typography uses actual exported TextLayout facts. The32 semantic/control minimum-height cells per arm pass the frozen comparison. No new numerical-resolution contradiction was observed; the numerical-resolution ledger is empty. No tolerance, observer, native assertion asset or geometry policy was changed. iOS actual viewport is600pt despite the640 fixture request; no selected viewport-height rule exists. Original public390/300 widths and hidden360 width are retained.

Outputs follow `<alias>/native-base/<case>/<platform>/grade.json` and `<alias>/final/<case>/<platform>/grade.json`, with manual.json/api-review.json beside final grades. source-build-verification.json, visual-candidates.json, contact sheets, acquisition/coverage ledger and summary.json retain exact provenance. Runtime screenshots are relative to their own capture. Both arms are jointly sealed before any original self-review matching or repair analysis.
''')
# Integrity checks read only sealed design and D0 seal identity; no D0 capture or grade is reopened.
seal=json.loads((R/'design/private/DESIGN-SEAL.json').read_text());mismatch=[p for p,h in seal['files'].items() if not (R/'design'/p).is_file() or sha(R/'design'/p)!=h];assert not mismatch,mismatch
d0=sha(R/'evaluation/D0/SEAL.json');assert d0=='3857f152ed6ee1a5615506b537643381896f18c4e884be27ff8d0929dfab76d4'
put(O/'integrity-check.json',dict(design_files_unchanged=True,design_seal_sha256=sha(R/'design/private/DESIGN-SEAL.json'),grader_seal_sha256=sha(R/'design/private/GRADER-SEAL.json'),D0_seal_unchanged=True,D0_seal_sha256=d0))
ts=datetime.datetime.now(datetime.timezone.utc);files={str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in str(p)};put(O/'SEAL.json',dict(stage='FINAL',sealedAtUTC=ts.isoformat(),sealedAtUnix=ts.timestamp(),files=files,batch_sha256=sha(R/'evaluation-inputs/FINAL/batch.json'),scope='Both anonymous FINAL arms jointly; native-base before manual/API; complete P1/P2/H1 denominator; no original self-review or paired collector captures inspected.',design_seal_sha256=sha(R/'design/private/DESIGN-SEAL.json'),grader_seal_sha256=sha(R/'design/private/GRADER-SEAL.json')));print(json.dumps({'seal_sha256':sha(O/'SEAL.json'),'sealed_at':ts.isoformat(),'files':len(files),'arms':{a:{p:v['counts'] for p,v in d.items()} for a,d in summary.items()}},indent=2))
