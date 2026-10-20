from pathlib import Path
import json,hashlib,importlib.util,collections,shutil,inspect
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'supplement/T1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ev(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def write(p,d):
 assert not p.exists(),str(p)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def aggregate(rows):return {'denominator':len(rows),'counts':{side:{s:sum(x[side]==s for x in rows)for s in ['P','F','U','N/A']}for side in ['a','b']},'transitions':dict(sorted(collections.Counter(x['a']+'->'+x['b']for x in rows).items())),'U_to_P_or_F':sum(x['a']=='U'and x['b']in['P','F']for x in rows),'P_or_F_to_U':sum(x['a']in['P','F']and x['b']=='U'for x in rows),'assessed_conflicts':sum(x['a']in['P','F']and x['b']in['P','F']and x['a']!=x['b']for x in rows)}
spec=importlib.util.spec_from_file_location('supplement_pair_oracle',R/'shared-environment-v1/oracle_common.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
spec=importlib.util.spec_from_file_location('primary_pair_oracle',R/'design-v2/oracle_common.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);assert inspect.getsource(g.compare_pair)==inspect.getsource(p.compare_pair)
import cohort_gate
for gate in ['fix','original-finalized']:cohort_gate.verify(R/'shared-environment-v1/gates',gate)
batch=read(R/'evaluation-inputs/paired-D0/T1/batch.json');pairs={};allpair=[];provenance=[];deltas=[];audit={'batch':ev(R/'evaluation-inputs/paired-D0/T1/batch.json'),'fixed_oracle':ev(R/'shared-environment-v1/oracle_common.py'),'compare_pair_source_unchanged':True,'sources':{}}
for entry in batch['corpora']:
 alias=entry['anonymousID'];a=[];b=[];v6root=R/entry['v6Captures'];v7root=R/entry['v7Captures'];assert read(v6root/'corpus.json')['source']==read(v7root/'corpus.json')['source'];portable=read(v6root/'portable-sha256.json');assert all(sha(v6root/rel)==h for rel,h in portable.items());audit['sources'][alias]={'source_identity_equal':True,'v6_portable_manifest':ev(v6root/'portable-sha256.json'),'all_manifest_hashes_match':True,'sessions':[]}
 for case in batch['cases']:
  for platform in ['ios','android']:
   out=O/'paired-D0'/alias/case/platform;d=v6root/platform/case;op=d/'observation.json';v7op=v7root/platform/case/'observation.json';old=g.grade_task(R/'design-v2/T1',case,platform,op,root=d,manual=None,source_root=None,api_review=None);write(out/'native-grade-v6.json',old);write(out/'native-report-v6.json',old['native_report']);v7grade=O/'D0'/alias/case/platform/'native-base-grade.json';v7report=O/'D0'/alias/case/platform/'native-base.json';out.mkdir(parents=True,exist_ok=True);shutil.copyfile(v7grade,out/'native-grade-v7.json');shutil.copyfile(v7report,out/'native-report-v7.json');new=read(v7grade);assert (out/'native-grade-v7.json').read_bytes()==v7grade.read_bytes();assert new['evidence'][0]['sha256']==sha(v7op);assert read(d/'fixtures.json')==read(v7op.parent/'fixtures.json')
   a.extend(old['rows']);b.extend(new['rows']);audit['sources'][alias]['sessions'].append({'case':case,'platform':platform,'v6_observation':ev(op),'v7_observation':ev(v7op),'v6_grade':ev(out/'native-grade-v6.json'),'v7_corrected_D0_base':ev(v7grade),'v7_byte_exact_copy':ev(out/'native-grade-v7.json'),'fixtures_equal':True,'v6_input_checks':old['input_checks'],'v7_input_checks':new['input_checks']})
   for side,gr,primaryfile,suppfile in [('a',old,R/f'evaluation/paired-D0/T1/{alias}/{case}/{platform}/native-grade-v6.json',out/'native-grade-v6.json'),('b',new,R/f'evaluation/paired-D0/T1/{alias}/{case}/{platform}/native-grade-v7.json',v7grade)]:
    original={r['id']:r for r in read(primaryfile)['rows']}
    for row in gr['rows']:
     if row['class']not in g.NATIVE_CLASSES:continue
     prior=original[row['id']];assert all(prior[k]==row[k]for k in ['expected','unit','op','tolerance','class']);deltas.append({'alias':alias,'side':side,'id':row['id'],'platform':platform,'class':row['class'],'primary':prior['status'],'supplement':row['status'],'transition':prior['status']+'->'+row['status'],'primary_grade':ev(primaryfile),'supplement_grade':ev(suppfile),'observation':ev(op if side=='a'else v7op)})
   ia={r['id']:r for r in old['rows']};ib={r['id']:r for r in new['rows']}
   for rid,row in ia.items():
    if row['class']not in g.NATIVE_CLASSES:continue
    rr=ib[rid];provenance.append({'alias':alias,'id':rid,'v6_row':row,'v7_row':rr,'v6_grade':ev(out/'native-grade-v6.json'),'v7_corrected_D0_base':ev(v7grade)})
   print(alias,case,platform,'v6',old['counts'],'v7',new['counts'])
 result=g.compare_pair({'rows':a},{'rows':b});pairs[alias]=result;allpair.extend(dict(x,alias=alias)for x in result['rows'])
write(O/'paired-D0/artifact-audit.json',audit);write(O/'paired-D0/rows-with-provenance.json',{'rows':provenance,'scope':'Four native classes only. Original raw captures under same fixed shared oracle; no manual/API scoring. Full rows preserve actuals and observation/PNG hashes.'})
original=read(R/'evaluation/paired-D0/T1/pair-comparison.json')
comparison={'denominator':len(allpair),'a':'actual original v6 native captures graded under fixed shared oracle, no manual/source/API','b':'corrected original v7 D0 native-base-grade bytes, no manual/source/API','scope':'POSTHOC shared infrastructure correction, weaker than primary blind evidence; not treatment benefit. Same unchanged compare_pair and four native classes.','sources':pairs,'primary_pair_comparison':ev(R/'evaluation/paired-D0/T1/pair-comparison.json'),'primary_pooled':original['pooled'],'pooled':aggregate(allpair),'per_platform':{p:aggregate([x for x in allpair if x['platform']==p])for p in ['ios','android']},'per_class':{cl:aggregate([x for x in allpair if x['class']==cl])for cl in sorted(g.NATIVE_CLASSES)},'per_platform_class':{p:{cl:aggregate([x for x in allpair if x['platform']==p and x['class']==cl])for cl in sorted(g.NATIVE_CLASSES)}for p in ['ios','android']},'row_provenance':ev(O/'paired-D0/rows-with-provenance.json'),'interpretation':['Shared Android gate correction applies to both original collector versions; cannot count restored assessment as v7 gain.','No visual or API/input integrity row enters the native paired denominator. No new native sessions or SDK calls.','Primary original Android U and all primary stage outputs remain immutable and equally prominent.','Repeated states/cases/sources are manifestations, not independent experiments. Same-frame diagnostic is separate and unchanged.']};write(O/'pair-comparison.json',comparison)
write(O/'paired-D0/primary-row-deltas.json',{'scope':'Primary-to-posthoc deltas by collector side. Shared Android gate unmasking only; no collector benefit attribution.','rows':deltas,'by_side':{side:{'transitions':dict(sorted(collections.Counter(x['transition']for x in deltas if x['side']==side).items())),'ios_changes':sum(x['primary']!=x['supplement']for x in deltas if x['side']==side and x['platform']=='ios')}for side in ['a','b']}})
print('PRIMARY',comparison['primary_pooled']);print('SUPPLEMENT',comparison['pooled'])
