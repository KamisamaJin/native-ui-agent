from pathlib import Path
import json,hashlib,sys,time,subprocess,shutil
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'supplement/T1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ev(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def write(p,d):
 assert not p.exists(),str(p)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
assert not (O/'SEAL.json').exists()
sys.path.insert(0,str(R/'candidate-v7/scripts'));import cohort_gate
proofs={gate:cohort_gate.verify(R/'shared-environment-v1/gates',gate)for gate in ['fix','original-finalized']}
checks=[]
for stage in ['D0','FINAL','selfreview','paired-D0']:
 d=R/f'evaluation/{stage}/T1';seal=read(d/'SEAL.json');assert all(sha(d/p)==h for p,h in seal['files'].items());checks.append({'stage':stage,'seal':ev(d/'SEAL.json'),'all_original_sealed_files_unchanged':True,'file_count':len(seal['files'])})
raw=[]
for stage in ['D0','FINAL']:
 batch=read(R/f'evaluation-inputs/{stage}/T1/batch.json')
 for entry in batch['corpora']:
  root=R/entry['captures'];manifest=root/'portable-sha256.json';files=read(manifest);assert all(sha(root/rel)==h for rel,h in files.items());raw.append({'stage':stage,'alias':entry['anonymousID'],'manifest':ev(manifest),'all_original_portable_hashes_match':True,'file_count':len(files)})
  alias=entry['anonymousID'];s=read(O/stage/'summary.json')['sources'][alias];primary=read(R/f'evaluation/{stage}/T1/summary.json')['sources'][alias];assert s['defect_clusters']==primary['defect_clusters'];assert s['product_failure_row_ids']==primary['product_failure_row_ids']
  for case in batch['cases']:
   for platform in ['ios','android']:
    out=O/stage/alias/case/platform;old=R/f'evaluation/{stage}/T1/{alias}/{case}/{platform}';manual=out/'manual.json';g=read(out/'grade.json');base=read(out/'native-base-grade.json');assert read(out/'native-base.json')==base['native_report'];assert (out/'original-manual.json').read_bytes()==(old/'manual.json').read_bytes();assert len(g['rows'])==132 and len({x['id']for x in g['rows']})==132;assert all(x['status']=='P'for x in g['api_checks'])
    if platform=='ios':
     assert manual.read_bytes()==(old/'manual.json').read_bytes();assert [(x['id'],x['status'])for x in g['rows']]==[(x['id'],x['status'])for x in read(old/'grade.json')['rows']]
    else:
     assert manual.read_bytes()==(out/'supplementary-manual.json').read_bytes();assert len(read(manual)['decisions'])==6;env=next(x for x in g['input_checks']if x['id']=='native-environment');assert env['status']=='P'and env['direction_encoding_proof']['canonical']=='ltr';assert all(x['status']in['P','U','N/A']for x in base['rows'])
for src in ['base.py','finish_grades.py','paired.py','seal.py']:
 dst=O/'evaluator-scripts'/src;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'cache/eval-supplement-T1'/src,dst)
account=[]
for stage,cases in [('D0',['P1','P2']),('FINAL',['P1','P2','H1'])]:
 cmd=[sys.executable,'-B',str(R/'evaluation_schema.py'),str(O/stage),'--cases',*cases];start=time.time();result=subprocess.run(cmd,capture_output=True,text=True);finish=time.time();record={'stage':stage,'command':cmd,'startedAtUnix':start,'finishedAtUnix':finish,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr};account.append(record);assert result.returncode==0,record
write(O/'accounting-verification.json',{'checks':account,'earlier_completed_checks':[{'stage':'D0','exit_code':0,'stdout':'PASS: complete anonymous task denominator, cause partition and cluster provenance shape\n'},{'stage':'FINAL','exit_code':0,'stdout':'PASS: complete anonymous task denominator, cause partition and cluster provenance shape\n'}],'reason_for_final_repeat':'Capture actual command timestamps/output within sealed task output after all grading artifacts finalized.'})
write(O/'final-integrity.json',{'verifiedAtUnix':time.time(),'gates_reverified':list(proofs),'original_sealed_stages':checks,'original_raw_corpora':raw,'ios_effective_manual_byte_exact_and_all_acceptance_statuses_unchanged':True,'original_ios_product_clusters_and_failure_classification_unchanged':True,'no_SDK_or_product_repair_or_fixture_expectation_tolerance_claim_changes':True,'assignment_not_read':True,'supplement_scope':'Shared posthoc direction compatibility only; Android additional visual inspection independent. No treatment or own-review discovery credit.','all_f_preserved_and_partitioned':True})
text='''# T1 posthoc environment supplement

This is a separately gated shared-infrastructure supplement with weaker evidence than the primary blind experiment. Primary results remain immutable and equally prominent. Direction compatibility correction cannot be attributed to v7; no new own-review detection credit is awarded.

| Stage | Source | Primary P/F/U/N/A | Supplement P/F/U/N/A |
|---|---|---|---|
| D0 | source-a | 175 / 20 / 293 / 40 | 418 / 20 / 50 / 40 |
| D0 | source-b | 175 / 20 / 293 / 40 | 406 / 32 / 50 / 40 |
| FINAL | source-a | 292 / 0 / 440 / 60 | 656 / 0 / 76 / 60 |
| FINAL | source-b | 292 / 0 / 440 / 60 | 638 / 18 / 76 / 60 |

Every original iOS manual input is reused byte-exact, every iOS acceptance status is unchanged, and all original iOS confirmed product clusters/F classifications remain unchanged. Native computed iOS style and blocked-callback U remain U. Android initial native bases have no F; their visual rows are assessed separately using the original PNGs.

Source-b has 12 D0 and 18 FINAL Android visual F rows for inherited canvas #EDF1F6 / #0D1420 instead of approved #FFFFFF / #101A14. These F rows are retained in uncertain_f_rows. Original host literals conflict with fixture canvas; source-b production root is transparent, and the frozen brief/API does not explicitly assign canvas painting ownership. This establishes the actual mismatch and attribution uncertainty, not a new confirmed product cluster. Source-a paints correct component-interior canvas; exterior host bands are recorded separately. No host, source, fixture, expected value or tolerance is changed.

| Native paired result | v6 P/F/U/N/A | v7 P/F/U/N/A |
|---|---|---|
| Primary, 1,008 cells | 350 / 16 / 562 / 80 | 350 / 16 / 562 / 80 |
| Posthoc, same 1,008 cells | 812 / 16 / 100 / 80 | 812 / 16 / 100 / 80 |

Unchanged compare_pair reports all paired statuses equal: no collector U-to-assessed gain, assessed-to-U loss or assessed conflict. Shared correction unmasks 462 primary U to P on each side. Visual/API/input checks are excluded from the native pair. Same-frame diagnostics remain separate and unchanged. Repeated rows are manifestations, not independent experiments.

Complete raw-bound grades, native reports, byte-exact effective manual inputs, additional Android manual decisions, PNG hashes/indices, cause evidence, primary-to-supplement row deltas and accounting/integrity proofs are in this sealed directory. Original claims were not replayed or modified here; root applies the identical frozen metric functions only after all three task supplements seal.
'''
(O/'README.md').write_text(text)
phase=read(O/'phase.json');assert 'finishedAtUnix'not in phase;phase['finishedAtUnix']=time.time();(O/'phase.json').write_text(json.dumps(phase,indent=2)+'\n')
files={str(p.relative_to(O)):sha(p)for p in sorted(O.rglob('*'))if p.is_file()and p.name!='SEAL.json'and '__pycache__'not in p.parts and p.suffix!='.pyc'};seal={'task':'T1','stage':'POSTHOC-shared-environment-supplement','sealedAtUnix':time.time(),'files':files,'scope':'All primary grades remain immutable; direction-only shared posthoc correction and separate Android visual review, no treatment credit.'};write(O/'SEAL.json',seal);assert all(sha(O/p)==h for p,h in files.items());print(json.dumps({'seal':str(O/'SEAL.json'),'sha256':sha(O/'SEAL.json'),'files':len(files),'phase':phase,'duration_seconds':phase['finishedAtUnix']-phase['startedAtUnix']},indent=2))
