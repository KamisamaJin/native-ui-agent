from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,datetime
R=Path(__file__).resolve().parents[2];O=R/'evaluation/D0';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();put=lambda p,v:p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
summary={};allfail=[]
for alias in ['source-a','source-b']:
 a={}
 for phase in ['native-base','final']:
  runtime=[];checks=[];cases={}
  for case in ['P1','P2']:
   for platform in ['ios','android']:
    p=O/alias/phase/case/platform/'grade.json';g=json.loads(p.read_text());assert len(g['rows'])==(120 if case=='P1' else 144);runtime+=g['rows'];checks+=g['checks'];cases[case+'/'+platform]=g['counts']
  byclass={}
  for klass in sorted({r['class'] for r in runtime}):
   rows=[r for r in runtime if r['class']==klass];byclass[klass]={s:sum(r['status']==s for r in rows) for s in ['P','F','U','N/A']}
  a[phase]=dict(cells=len(runtime),counts=dict(Counter(r['status'] for r in runtime)),by_case_platform=cases,by_class=byclass,separate_check_counts=dict(Counter(r['status'] for r in checks)),natural_business_defect_detection_recall='N/A: no frozen business_current/business_transition F rows',natural_style_defect_detection_recall='N/A: no frozen style_native F rows')
  if phase=='final':allfail += [dict(alias=alias,**r) for r in runtime if r['status']=='F']
 a['natural_product_defect_sensitivity']=dict(established_failures=0,subresolution_frozen_F_claims=3 if alias=='source-a' else 0,natural_defect_recall='N/A: no established natural product defect denominator',note='Sensitivity panel only; frozen primary F/U counts and all rows remain unchanged. It does not transform F into P or redefine tolerance.')
 summary[alias]=a
put(O/'summary.json',dict(stage='D0',arms=summary,primary_failed_rows=allfail,viewport_note='iOS actual offered viewport is600pt; fixture requests640. No selected viewport-height assertion exists. Public widths remain390pt(P1)/300pt(P2).',limits_ledger='numerical-resolution-limits.json',scope='Public P1/P2 only; H1 remains sealed until both FINAL sources. Native-base grades precede manual/API adjudication. No original self-review or FINAL source inspected.'))
report='''# Anonymous D0 evaluation

Both anonymous public corpora were graded against the unchanged frozen design/grader. Each arm retains 528 runtime cells (24 families × 11 selected public states × two platforms), including every U and N/A. Source/API/input checks are separate. Hidden H1 was not used. No assignment, original review, own corpus, builder discussion, or FINAL source was read.

| Arm | Phase | P | F | U | N/A |
|---|---|---:|---:|---:|---:|
| source-a | native-base |439|3|60|26|
| source-a | final |461|3|38|26|
| source-b | native-base |445|0|57|26|
| source-b | final |467|0|35|26|

The difference between native-base and final is the 22 scoped visual rows per arm. The evaluator inspected all44 Reserve-label crops derived from SHA-bound original state screenshots. Every glyph was visible without clipping or ellipsis. This judges label visibility only; it is not a full visual match, exact iOS font/color measurement, physical-touch test, or effective-layout measurement. Native-base files remain byte-exact and have manual=None and no API adjudication. Final files retain the full rows/checks structure.

Both production APIs match public/API.md: type/field spellings, constructors, attendance cases and direct native entry signatures. Source SHA256 values were found in successful pinned-host build/test manifests (one native test each). Each final grade has separate API review decisions and original source/build artifact hashes. Exact fixture/actions manifest checks pass. There are16 final input/API check rows per arm, all P; these do not contribute runtime passes.

There are no frozen business_current, business_transition, style_native, native_content or visual failures in either arm. Natural business/style defect detection denominators are zero and recall is N/A. Current-state formula/status/selection facts do not establish that a requested action caused a transition. Callback behavior uses frozen successful-dispatch and assessed-state binding gates. The disabled P2 In-person activation remains U in both arms; an empty callback interval does not prove quiet disabled behavior. Missing acquisition/state/style evidence remains U, never a business logic failure.

Source-a has three primary raw native_geometry F rows: P2 Android browse, editing and replaced Reserve height. Each actual is47.99994000000004dp versus the frozen48dp lower bound. The comparison, F statuses, and raw base evidence remain unchanged. Three other source-a geometry rows remain U because bound values straddle that threshold inside the same state. The separate numerical-resolution ledger identifies exact rows, actual values and snapshots. A0.00006dp serialized-edge difference does not establish a natural product defect. A separately labeled sensitivity panel counts zero established product defects and three unresolved subresolution F claims; it does not change any grade, tolerance, observer or denominator. Source-b has no raw F rows.

Public iOS computed font/color/ellipsis rows remain U (33 per arm). iOS actual viewport is600pt despite the fixture's640 request; width stays390pt/300pt. No selected rule scores viewport height. The common frontend width recovery is infrastructure, excluded from treatment gains; earlier acquisition failures were outside the named batch and were not interpreted as product failures. All eight named common D0 captures have successful acquisition/build receipts.

Paths are consistent: `<alias>/native-base/<case>/<platform>/grade.json`, `<alias>/final/<case>/<platform>/grade.json`; final directories also contain `manual.json` and `api-review.json`. `source-build-verification.json`, `visual-candidates.json`, contact sheets, numerical-resolution-limits.json and summary.json retain the supporting evidence. Screenshot references resolve relative to each original capture. The first contact-sheet attempt could not locate iOS image coordinates in control-group copies; the v2 script reads the matching raw native node, and all44 candidates were then reviewed. That review-preparation failure affected no acquisition or grade.

No self-review detection or repair metrics are computed before the authorized later batches. D0 is sealed jointly for both anonymous arms before FINAL exposure.
'''
(O/'REPORT.md').write_text(report)
# Confirm approved design and grader files were not changed by evaluation.
seal=json.loads((R/'design/private/DESIGN-SEAL.json').read_text());mismatches=[p for p,h in seal['files'].items() if not (R/'design'/p).is_file() or sha(R/'design'/p)!=h];assert not mismatches,mismatches
put(O/'design-integrity-check.json',dict(design_seal_sha256=sha(R/'design/private/DESIGN-SEAL.json'),grader_seal_sha256=sha(R/'design/private/GRADER-SEAL.json'),all_design_files_match=True,native_checks_sha256=sha(R/'candidate-v6/scripts/native_checks.py')))
ts=datetime.datetime.now(datetime.timezone.utc);paths={str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in str(p)}
put(O/'SEAL.json',dict(stage='D0',sealedAtUTC=ts.isoformat(),sealedAtUnix=ts.timestamp(),files=paths,batch_sha256=sha(R/'evaluation-inputs/D0/batch.json'),scope='Both anonymous D0 arms jointly; native-base grades retained before manual/API; no FINAL or self-review inspected.',design_seal_sha256=sha(R/'design/private/DESIGN-SEAL.json'),grader_seal_sha256=sha(R/'design/private/GRADER-SEAL.json')))
print(json.dumps({'seal_sha256':sha(O/'SEAL.json'),'sealed_at':ts.isoformat(),'files':len(paths),'summary':summary},indent=2))
