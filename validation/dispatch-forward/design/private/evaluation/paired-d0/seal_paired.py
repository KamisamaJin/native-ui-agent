import json,hashlib,datetime,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[3];REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def ref(p,base):return {'path':str(p.relative_to(base)),'sha256':sha(p)}
active='af39b8846cf1da53d777f9f031b00a61661dd4fbc336d55214af1db4c9119d55'
conventions='a1d7c014b70422b75ab60278cf9799440982a14524d6cfde1982bad00fa71c1f'
plan=read(R/'design/private/evaluator-prep/normalized-d0.json')
execution=read(R/'evaluation-execution-commitment.json')
helper_path=R/'design/private/evaluator-prep/report-conventions/exact_rows.py'
sp=importlib.util.spec_from_file_location('sealed_paired_join',helper_path);helper=importlib.util.module_from_spec(sp);sp.loader.exec_module(helper)
for rel,expected in execution['files'].items():assert sha(R/rel)==expected
for aid in ['sample-716d41','sample-e318ec']:
 cap=R/'private/grade-capsules/paired-d0'/aid;out=HERE/aid;original=read(cap/'capsule-seal.json')
 for rel,expected in original['files'].items():assert sha(cap/rel)==expected,rel
 manifest=read(cap/'manifest-reviewed.json');base=read(cap/'manifest.json')
 assert {k:v for k,v in manifest.items() if k not in ['visual_review','source_review']}==base
 report=read(out/'paired-grade.json');assert report['anonymous_id']==aid and report['phase']=='d0'
 assert len(report['rows'])==3185 and {r['key'] for r in report['rows']}==set(plan['required_keys'])
 assert report['manifest_sha256']==sha(cap/'manifest-reviewed.json')
 assert report['evaluator_adapter']=='v3' or report.get('evaluator_adapter',{}).get('version')==3
 for k in ['visual_review','source_review']:
  assert sha(cap/manifest[k]['path'])==manifest[k]['sha256']
 source=read(cap/'source-identity.json');source_seal=read(cap/'source-seal.json')
 # Both the source artifact seal and its path->hash map commitment are retained independently.
 assert source['sourceSealSHA256']==sha(cap/'source-seal.json')
 assert source['sourceFilesCommitment']==hashlib.sha256(canonical(source_seal['files']).encode()).hexdigest()
 timing=read(out/'decoder-timing.json');assert timing['output_sha256']==sha(out/'paired-grade.json') and timing['manifest_sha256']==sha(cap/'manifest-reviewed.json')
 anchor_cap=R/'private/grade-capsules/d0'/aid
 anchor_out=R/'design/private/evaluation/d0'/aid
 anchor_identity=read(anchor_cap/'source-identity.json')
 assert anchor_identity['sourceFilesCommitment']==source['sourceFilesCommitment']
 pair_input=read(out/'paired-input.json')
 assert pair_input['source_commitments']==[anchor_identity['sourceFilesCommitment'],source['sourceFilesCommitment']]
 expected=helper.paired_d0(read(anchor_out/'grade.json'),report,pair_input['source_commitments'])
 comparison=read(out/'comparison.json')
 assert {k:comparison[k] for k in expected}==expected
 for platform in ['ios','android']:
  for bucket in helper.BUCKETS:
   subset=[r for r in comparison['rows'] if r['platform']==platform and r['denominator']==bucket]
   matrix={x+'->'+y:sum(r['anchor']==x and r['paired']==y for r in subset) for x in helper.OUTCOMES for y in helper.OUTCOMES}
   assert comparison['platform_counts'][platform][bucket]['matrix']==matrix
   assert sum(matrix.values())==len(subset)
 output_files=[p for p in out.iterdir() if p.is_file() and p.name!='SEAL.json']
 inputs=[cap/'capsule-seal.json',cap/'manifest.json',cap/'manifest-reviewed.json',cap/'visual-review.json',cap/'source-review.json',cap/'source-seal.json',cap/'source-identity.json',cap/'acquisition-records.json',R/'private/grade-deliveries/paired-d0.json',R/'evaluation-execution-commitment.json',R/'evaluator-v3-commitment.json',R/'matching-conventions-commitment.json',R/'design/private/evaluator-prep/normalized-d0.json',R/'design/private/evaluator-prep/v3/V3-SEAL.json']
 inputs += [anchor_cap/'capsule-seal.json',anchor_cap/'manifest.json',anchor_cap/'source-seal.json',anchor_cap/'source-identity.json',anchor_cap/'acquisition-records.json',anchor_out/'grade.json',anchor_out/'SEAL.json',out/'paired-input.json',R/'design/private/evaluation/selfreview'/aid/'SEAL.json']
 inputs += [p for p in helper_path.parent.iterdir() if p.is_file()]
 # Raw capability availability is explicitly an original-field inventory outside grades.
 for entry in read(anchor_cap/'manifest.json')['observations']:
  if entry['platform']=='android':inputs.append(anchor_cap/entry['observation']['path'])
 for relative in execution['files']:inputs.append(R/relative)
 inputs.append(R/'design/private/evaluation/d0/run_cached_grade.py')
 for p in HERE.iterdir():
  if p.is_file():inputs.append(p)
 # Original manifest refs are transitively sealed, and explicitly included for audit convenience.
 for entry in manifest['observations']:
  for key in ['observation','mapping','fixture']:
   if key in entry and isinstance(entry[key],dict) and 'path' in entry[key]:inputs.append(cap/entry[key]['path'])
 for entry in manifest['source_files']:inputs.append(cap/entry['path'])
 inputs=sorted(set(inputs))
 assert all(p.exists() for p in inputs),[str(p) for p in inputs if not p.exists()]
 payload={'phase':'paired-d0','anonymous_id':aid,'sealed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'active_evaluator_commitment':active,
 'report_conventions_commitment':conventions,'files':[ref(p,out) for p in sorted(output_files)],'inputs':[ref(p,REPO) for p in inputs],
 'required_rows':3185,'source_files_commitment':source['sourceFilesCommitment'],'paired_input_sha256':sha(out/'paired-input.json'),'original_capsule_seal_sha256':sha(cap/'capsule-seal.json'),'reviewed_manifest_sha256':sha(cap/'manifest-reviewed.json'),
 'execution_optimization':{'scope':'COMMON exact decoder cache only; no matcher, gate, expected, tolerance or measurement change','wrapper_sha256':execution['files']['design/private/evaluation/d0/png_decode_cache.py'],'timing_file':'decoder-timing.json'}}
 result={'commitment_sha256':hashlib.sha256(canonical(payload).encode()).hexdigest(),'payload':payload}
 seal=out/'SEAL.json';assert not seal.exists();seal.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'anonymous_id':aid,'paired_grade_path':str((out/'paired-grade.json').relative_to(REPO)),'paired_grade_sha256':sha(out/'paired-grade.json'),'comparison_path':str((out/'comparison.json').relative_to(REPO)),'comparison_sha256':sha(out/'comparison.json'),'seal_path':str(seal.relative_to(REPO)),'seal_sha256':sha(seal),'commitment_sha256':result['commitment_sha256'],'completed':True}))
