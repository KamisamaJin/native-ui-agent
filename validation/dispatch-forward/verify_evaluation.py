#!/usr/bin/env python3
"""Replay frozen grading on original artifacts after formal assignment release."""
import importlib.util,json,tempfile
from pathlib import Path
from contract import R,read,sha
from verify_blind_stages import stages
def main():
 assert (R/'private/assignment-release.json').is_file();stages()
 spec=importlib.util.spec_from_file_location('dispatch_v3_evaluator',R/'design/private/evaluator-prep/v3/evaluator.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
 execution=read(R/'evaluation-execution-commitment.json')
 for rel,h in execution['files'].items():assert sha(R/rel)==h
 cache_spec=importlib.util.spec_from_file_location('dispatch_png_cache',R/execution['wrapper']);cache_module=importlib.util.module_from_spec(cache_spec);cache_spec.loader.exec_module(cache_module);original=e.read_png;cache=cache_module.install(e);assert cache.original is original
 s=importlib.util.spec_from_file_location('dispatch_exact_rows',R/'design/private/evaluator-prep/report-conventions/exact_rows.py');joins=importlib.util.module_from_spec(s);s.loader.exec_module(joins)
 evaluation=R/'design/private/evaluation';mapping=read(R/'private/grade-assignment.json')['mapping'];n=0
 with tempfile.TemporaryDirectory(prefix='dispatch-grade-replay-')as tmp:
  for phase in ['d0','final','paired-d0']:
   for anon in mapping:
    report=evaluation/phase/anon/('paired-grade.json'if phase=='paired-d0'else'grade.json');expected=read(report);capsule=R/'private/grade-capsules'/phase/anon
    candidates=[p for p in capsule.rglob('manifest*.json')if sha(p)==expected['manifest_sha256']];assert candidates,('Exact reviewed manifest missing',report)
    actual=e.grade(candidates[0],Path(tmp)/(str(n)+'.json'));assert actual==expected,('Frozen grade replay differs',report);n+=1;cache.clear()
  for anon in mapping:
   d0=read(evaluation/'d0'/anon/'grade.json');final=read(evaluation/'final'/anon/'grade.json');paired=read(evaluation/'paired-d0'/anon/'paired-grade.json');matching=read(evaluation/'selfreview'/anon/'matching.json')
   expected=joins.review_match(d0,final,matching['matches'])
   for key,value in expected.items():assert matching[key]==value,('Matching arithmetic differs',anon,key)
   a=read(R/'private/grade-capsules/d0'/anon/'source-identity.json')['sourceFilesCommitment'];b=read(R/'private/grade-capsules/paired-d0'/anon/'source-identity.json')['sourceFilesCommitment'];assert a==b
   expected=joins.paired_d0(d0,paired,[a,b]);comparison=read(evaluation/'paired-d0'/anon/'comparison.json')
   for key,value in expected.items():assert comparison[key]==value,('Paired arithmetic differs',anon,key)
 print(json.dumps({'status':'PASS','replayed_full_grades':n,'blind_source_pairs':len(mapping),'scope':'Frozen native/pixel/source-citation matchers and exact-row arithmetic; qualitative image judgments remain independent human/AI review assertions.'}))
if __name__=='__main__':main()
