from pathlib import Path
import json,hashlib,importlib.util,shutil,collections
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'evaluation/paired-D0/T3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def save(p,d):assert not p.exists(),p;p.write_text(json.dumps(d,indent=2)+'\n')
bp=R/'evaluation-inputs/paired-D0/T3/batch.json';batch=json.loads(bp.read_text());spec=importlib.util.spec_from_file_location('tg',R/'design-v2/T3/private/grader.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
allpairs=[];allfull=[];sources={};integrity={'batch':ref(bp),'sources':{}};allgrade6=[];allgrade7=[]
for ent in batch['corpora']:
 alias=ent['anonymousID'];v6c=R/ent['v6Captures'];v7c=R/ent['v7Captures'];orig=R/ent['v7OriginalScores'];checks=[]
 for e in ent['exactCopies']:
  s=R/e['source'];d=R/e['destination'];assert sha(s)==sha(d)==e['sha256'];assert s.read_bytes()==d.read_bytes();checks.append({'source':ref(s),'destination':ref(d),'byte_exact':True})
 portable={}
 for tag,corp in [('v6',v6c),('v7',v7c)]:
  pm=corp/'portable-sha256.json';h=json.loads(pm.read_text());bad=[r for r,s in h.items() if not(corp/r).exists() or sha(corp/r)!=s];assert not bad;portable[tag]={'manifest':ref(pm),'corpus_seal':ref(corp/'corpus-seal.json'),'checked_files':len(h),'mismatches':bad}
 a=json.loads((v6c/'corpus.json').read_text());b=json.loads((v7c/'corpus.json').read_text());assert a['source']==b['source']
 units=[];rows6=[];rows7=[];native=[];full=[]
 for case in batch['cases']:
  for plat in ['ios','android']:
   out=O/alias/case/plat;out.mkdir(parents=True);op=v6c/plat/case/'observation.json';assert op.exists();gr6=g.grade(case,plat,op,manual=None,source_root=None,api_review=None);save(out/'native-grade-v6.json',gr6);save(out/'native-report-v6.json',gr6['native_report']);gr7p=orig/case/plat/'native-base-grade.json';rep7p=orig/case/plat/'native-base.json';shutil.copyfile(gr7p,out/'native-grade-v7.json');shutil.copyfile(rep7p,out/'native-report-v7.json');assert (out/'native-grade-v7.json').read_bytes()==gr7p.read_bytes();assert (out/'native-report-v7.json').read_bytes()==rep7p.read_bytes();gr7=json.loads(gr7p.read_text());assert gr7['native_report']==json.loads(rep7p.read_text());rows6+=gr6['rows'];rows7+=gr7['rows'];
   cmp=g.compare_pair(gr6,gr7);save(out/'compare-pair.json',cmp);native+=cmp['rows'];fi6={r['id']:r for r in gr6['rows']};fi7={r['id']:r for r in gr7['rows']};assert set(fi6)==set(fi7)
   for rid,r6 in fi6.items():
    r7=fi7[rid];fr={k:r6[k] for k in ['id','case','platform','state','requirement','class','expected','unit','op','tolerance']};fr.update(a=r6['status'],b=r7['status'],v6_evidence=r6['evidence'],v7_evidence=r7['evidence']);full.append(fr)
   m6=json.loads((op.parent/'manifest.json').read_text());m7=json.loads((v7c/plat/case/'manifest.json').read_text());f6=json.loads((op.parent/'fixtures.json').read_text());f7=json.loads((v7c/plat/case/'fixtures.json').read_text());f6.pop('actions',None);f7.pop('actions',None);assert f6==f7
   logs={}
   for tag,dir in [('v6',op.parent),('v7',v7c/plat/case)]:
    manifest=json.loads((dir/'manifest.json').read_text());extract={}
    for n in ['build.log','test.log']:
     p=dir/n
     if p.exists():extract[n]=[l for l in p.read_text(errors='replace').splitlines() if any(t in l.lower() for t in ['error:','failed','failure','build successful','executed 1 test'])][-7:]
    logs[tag]={'manifest':ref(dir/'manifest.json'),'observation':ref(dir/'observation.json'),'original_logs':[ref(dir/n) for n in ['build.log','test.log','junit.xml'] if (dir/n).exists()],'commands_and_results':{k:manifest[k] for k in ['status','command','build_command','test_command','exit_code','build_exit_code','test_exit_code','native_test_count','native_counts','native_summary'] if k in manifest},'diagnostics':extract}
   units.append({'case':case,'platform':plat,'v6_grade':ref(out/'native-grade-v6.json'),'v7_grade_byte_exact':ref(out/'native-grade-v7.json'),'v6_input_checks':gr6['input_checks'],'v7_input_checks':gr7['input_checks'],'source_and_caller_inputs_identical':True,'native_capture_evidence':logs})
   print(alias,case,plat,'v6',gr6['counts'],'v7',gr7['counts'],'native',cmp['counts'])
 agg=g.compare_pair({'rows':rows6},{'rows':rows7});assert agg['rows']==native;allpairs.extend([{'alias':alias,**x} for x in native]);allfull.extend([{'alias':alias,**x} for x in full]);allgrade6.extend(rows6);allgrade7.extend(rows7)
 # Full provenance for changes is derived from complete fixed rows, including their original observation/PNG hashes.
 changes=[]
 for x in full:
  if x['class']=='visual':continue
  if x['a']=='U' and x['b'] in ['P','F']:kind='U->'+x['b']
  elif x['a'] in ['P','F'] and x['b']=='U':kind=x['a']+'->U'
  elif x['a'] in ['P','F'] and x['b'] in ['P','F'] and x['a']!=x['b']:kind='assessed_conflict'
  else:continue
  changes.append({'kind':kind,**x})
 sources[alias]={'native_comparison':agg,'full_fixed_ledger_denominator':len(full),'full_fixed_rows':full,'changed_native_rows':changes,'units':units}
 integrity['sources'][alias]={'exact_v7_copy_checks':checks,'portable_checks':portable,'production_source_hashes_identical':True,'v6_source_record':ref(v6c/'corpus.json'),'v7_source_record':ref(v7c/'corpus.json')}
def summarize(rows):
 counts={tag:{s:sum(r[tag]==s for r in rows) for s in ['P','F','U','N/A']} for tag in ['a','b']};trans=collections.Counter(r['a']+'->'+r['b'] for r in rows)
 return {'denominator':len(rows),'counts':counts,'transition_counts':dict(trans),'U_to_P':sum(r['a']=='U' and r['b']=='P' for r in rows),'U_to_F':sum(r['a']=='U' and r['b']=='F' for r in rows),'P_to_U':sum(r['a']=='P' and r['b']=='U' for r in rows),'F_to_U':sum(r['a']=='F' and r['b']=='U' for r in rows),'assessed_conflicts':sum(r['a'] in ['P','F'] and r['b'] in ['P','F'] and r['a']!=r['b'] for r in rows)}
pooled=summarize(allpairs);byplat={p:summarize([r for r in allpairs if r['platform']==p]) for p in ['ios','android']};byclass={cl:summarize([r for r in allpairs if r['class']==cl]) for cl in sorted({r['class'] for r in allpairs})};cross={p:{cl:summarize([r for r in allpairs if r['platform']==p and r['class']==cl]) for cl in byclass} for p in ['ios','android']}
result={'schema_version':1,'task':'T3','stage':'paired-D0','a':'actual baseline-v6 distinct-session captures graded with unchanged accepted oracle','b':'byte-exact original sealed v7 D0 native-base-grade reuse','sources':sources,'pooled':pooled,'by_platform':byplat,'by_class':byclass,'by_platform_and_class':cross,'native_rows':allpairs,'all_fixed_row_denominator':len(allfull),'all_fixed_rows':allfull,'scope':'compare_pair includes business_current/business_transition/geometry/native_style only. Visual/API/input checks do not count as collector gains. All U and N/A stay in the complete native denominator; full fixed ledger retained separately. Changes across distinct native sessions may include coverage/scroll/timing. Not independent product bug experiments.'}
save(O/'input-integrity.json',integrity);save(O/'pair-comparison.json',result);print('POOLED',json.dumps(pooled));print('changes',[(a,len(x['changed_native_rows'])) for a,x in sources.items()])
