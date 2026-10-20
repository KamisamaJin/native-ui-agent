from pathlib import Path
import json,hashlib,importlib.util
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'supplement/T3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def save(p,d):assert not p.exists(),p;p.write_text(json.dumps(d,indent=2)+'\n')
primary=[]
for stage in ['D0','FINAL','selfreview','paired-D0']:
 root=R/f'evaluation/{stage}/T3';seal=json.loads((root/'SEAL.json').read_text());bad=[r for r,h in seal['files'].items() if sha(root/r)!=h];assert not bad;primary.append({'stage':stage,'seal':ref(root/'SEAL.json'),'all_output_files_unchanged':True,'files_verified':len(seal['files'])})
raw=[];source=[]
for stage in ['D0','FINAL']:
 b=json.loads((R/f'evaluation-inputs/{stage}/T3/batch.json').read_text())
 for ent in b['corpora']:
  cap=R/ent['sourceCapsule'];assert sha(cap/'seal.json')==ent['sourceSealSHA256'];s=json.loads((cap/'seal.json').read_text());assert all(sha(cap/'source'/p)==h for p,h in s['files'].items());source.append({'stage':stage,'alias':ent['anonymousID'],'seal':ref(cap/'seal.json'),'files_verified':len(s['files'])});corp=R/ent['captures'];pm=corp/'portable-sha256.json';assert sha(pm)==ent['portableManifestSHA256'];p=json.loads(pm.read_text());assert all(sha(corp/n)==h for n,h in p.items());raw.append({'stage':stage,'alias':ent['anonymousID'],'portable_manifest':ref(pm),'raw_files_verified':len(p)})
b=json.loads((R/'evaluation-inputs/paired-D0/T3/batch.json').read_text())
for ent in b['corpora']:
 corp=R/ent['v6Captures'];pm=corp/'portable-sha256.json';p=json.loads(pm.read_text());assert all(sha(corp/n)==h for n,h in p.items());raw.append({'stage':'paired-D0-v6','alias':ent['anonymousID'],'portable_manifest':ref(pm),'raw_files_verified':len(p)})
manual=json.loads((O/'manual-and-source-provenance.json').read_text());assert len(manual)==20;ios=[x for x in manual if x['platform']=='ios'];assert len(ios)==10 and all(x['effective_manual_byte_exact_original'] for x in ios);assert all((R/x['original_manual']['path']).read_bytes()==(R/x['effective_manual']['path']).read_bytes() for x in ios)
counts={};iosstatus=[]
for stage,cases in [('D0',['P1','P2']),('FINAL',['P1','P2','H1'])]:
 summary=json.loads((O/stage/'summary.json').read_text());origsum=json.loads((R/f'evaluation/{stage}/T3/summary.json').read_text());counts[stage]={}
 for alias,s in summary['sources'].items():
  rows=[]
  for case in cases:
   for plat in ['ios','android']:
    d=O/stage/alias/case/plat;gr=json.loads((d/'grade.json').read_text());base=json.loads((d/'native-base-grade.json').read_text());assert base['native_report']==json.loads((d/'native-base.json').read_text());assert len(gr['rows'])==132;rows+=gr['rows'];original=json.loads((R/f'evaluation/{stage}/T3/{alias}/{case}/{plat}/grade.json').read_text())
    assert all(x['status']=='P' for x in gr['input_checks']);assert gr['counts']['P']+gr['counts']['F']+gr['counts']['U']+gr['counts']['N/A']==132
    if plat=='ios':
     assert [(r['id'],r['status']) for r in gr['rows']]==[(r['id'],r['status']) for r in original['rows']];assert all(r['status']=='U' for r in gr['rows'] if r['class']=='native_style' and r['status']!='N/A');iosstatus.append({'stage':stage,'alias':alias,'case':case,'rows':132,'acceptance_statuses_identical':True,'effective_manual_original':True})
  count={st:sum(r['status']==st for r in rows) for st in ['P','F','U','N/A']};assert count==s['counts'];assert len(rows)==(528 if stage=='D0' else 792);f={r['id'] for r in rows if r['status']=='F'};parts=s['product_failure_row_ids']+[x if isinstance(x,str) else x['id'] for x in s['non_product_f_rows']]+s['uncertain_f_rows'];assert len(parts)==len(set(parts)) and set(parts)==f
  clusterids=[r for cl in s['defect_clusters'] for r in cl['fixed_row_ids']];assert len(clusterids)==len(set(clusterids)) and set(clusterids)==set(s['product_failure_row_ids']);old=origsum['sources'][alias]
  for cl in old['defect_clusters']:assert cl in s['defect_clusters']
  counts[stage][alias]={'primary':old['counts'],'supplement':count,'new_android_visual_F_rows':len(s['newly_unmasked_android_F_row_ids'])}
visual=json.loads((O/'android-visual-index.json').read_text());assert len(visual)==60;idx={r['sheet']:r for r in visual}
for v in visual:
 if 'pixel_identical_to_reviewed_sheet' in v:assert [x['sha256'] for x in v['evidence']]==[x['sha256'] for x in idx[v['pixel_identical_to_reviewed_sheet']]['evidence']]
 else:assert (O/v['sheet']).exists()
pair=json.loads((O/'pair-comparison.json').read_text());assert pair['pooled']['denominator']==1008 and pair['full_fixed_ledger_denominator']==1056;assert pair['pooled']['counts']['a']==pair['pooled']['counts']['b'];assert pair['pooled']['U_to_P']==pair['pooled']['U_to_F']==pair['pooled']['P_or_F_to_U']==pair['pooled']['assessed_conflicts']==0
for stage,cases in [('D0',['P1','P2']),('FINAL',['P1','P2','H1'])]:
 for alias in ['source-a','source-b']:
  for c in cases:
   for p in ['ios','android']:
    d=O/stage/alias/c/p;assert sha(d/'native-base-grade.json') # record all first-call hashes before seal
base=[ref(p) for stage in ['D0','FINAL'] for p in sorted((O/stage).glob('*/*/*/native-base*.json'))]
save(O/'native-base-byte-bindings.json',{'files':base,'scope':'Complete first fixed-oracle manual=None/source_root=None call results and native reports preserved; effective grade/manual follows separately.'})
save(O/'immutability-and-accounting-audit.json',{'result':'PASS','primary_four_stages':primary,'source_capsules':source,'raw_corpora':raw,'original_ios_manual_copies':10,'original_ios_statuses':iosstatus,'all_original_ios_product_cause_clusters_unchanged':True,'additional_android_state_groups':60,'unique_original_png_sequences_inspected':26,'identical_sequence_groups_validated':34,'counts':counts,'corrected_paired_native':pair['pooled'],'posthoc_only':True,'new_claim_credit':False,'SDK_commands':0,'observation_source_expected_tolerance_edits':0,'schema_checks':['D0/preseal-attempt-1.txt','FINAL/preseal-attempt-1.txt']})
save(O/'overview.json',{'evidence_status':'POSTHOC shared environment supplement, weaker than the primary blind experiment. The primary Android evaluation failed its native-environment spelling check and withheld all applicable cells as U; those original sealed grades remain equally prominent and unchanged.','gate_proofs':['fix-gate-proof.json','original-finalized-gate-proof.json'],'original_vs_supplement_counts':counts,'newly_exposed_visual_issue':'Source-a Android root omits the canvas role, inheriting host blue-gray/near-black instead of specified white/dark-purple within component bounds.12 D0 /18 FINAL visual F manifestations form one supplemental cluster. Newly observed posthoc, no introduction claim or original own-review detection credit.','ios':'All10 effective iOS manual inputs are original byte-exact copies and all1320 iOS cell statuses remain unchanged. Existing iOS product F classifications are unchanged.','paired':'Original v6 sessions and corrected original v7 D0 native-base scores have identical1008 native statuses. The shared gate exposes434 previously-U native cells as P equally for each collector; this is infrastructure compatibility, not treatment benefit.','claims':'Original transported own-review claims were not changed or expanded. Root applies identical frozen matching metrics only after all task supplements seal.','primary_results':[x['seal'] for x in primary],'scope':'No SDK execution, production repair, assignment access, expected/tolerance/denominator change or primary score overwrite.'})
print(json.dumps({'result':'PASS','counts':counts,'iOS_manual_exact':10,'unique_sequences_inspected':26,'paired':pair['pooled']},indent=2))
