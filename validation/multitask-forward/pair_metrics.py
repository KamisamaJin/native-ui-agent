#!/usr/bin/env python3
"""Separate collector-session changes from identical-frame checker arithmetic."""
import argparse,collections,importlib.util,json
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def transitions(rows,a,b):
 c=collections.Counter(r[a]+'->'+r[b]for r in rows)
 return {'denominator':len(rows),'transitions':dict(sorted(c.items())),'unknownToAssessed':sum(r[a]=='U'and r[b]in['P','F']for r in rows),'assessedToUnknown':sum(r[a]in['P','F']and r[b]=='U'for r in rows),'assessedConflicts':sum(r[a]in['P','F']and r[b]in['P','F']and r[a]!=r[b]for r in rows),'aCounts':dict(collections.Counter(r[a]for r in rows)),'bCounts':dict(collections.Counter(r[b]for r in rows))}
def build():
 ex.gate.verify(R/'gates','reveal',R);assignment=ex.read(R/'private/assignment.json');design=R/ex.read(R/'DESIGN-ROOT.json')['directory'];native=[];same=[]
 for task,aliases in assignment['gradeAliases'].items():
  spec=importlib.util.spec_from_file_location('paired_'+task,design/task/'private/grader.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
  for alias in aliases:
   aa=[];bb=[]
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     aa+=ex.read(R/'evaluation/paired-D0'/task/alias/case/platform/'native-grade-v6.json')['rows'];bb+=ex.read(R/'evaluation-inputs/paired-D0'/task/alias/'v7'/case/platform/'native-base-grade.json')['rows']
   for row in g.compare_pair({'rows':aa},{'rows':bb})['rows']:native.append(dict(row,task=task,alias=alias))
  status={'passed':'P','failed':'F','unassessed':'U'}
  for row in ex.read(R/'precision-replay'/task/'comparison.json')['geometryRows']:same.append(dict(row,task=task,a=status[row['before']],b=status[row['after']]))
 out={}
 for name,rows in [('collectorSessions',native),('sameFrameCheckers',same)]:
  out[name]={'pooled':transitions(rows,'a','b'),'byPlatform':{p:transitions([r for r in rows if r['platform']==p],'a','b')for p in ['ios','android']},'byTask':{t:transitions([r for r in rows if r['task']==t],'a','b')for t in ['T1','T2','T3']},'byClass':{c:transitions([r for r in rows if r.get('class','geometry')==c],'a','b')for c in sorted({r.get('class','geometry')for r in rows})},'rows':rows}
 out['scope']='a=baseline-v6, b=candidate-v7. Collector sessions use identical source/public inputs but distinct actual SDK sessions and the common fixed oracle. Same-frame checker diagnostic uses identical raw observation/approved plan bytes and zero native launches. Neither is an independent product-quality experiment; no visual/API/input grade is a collector gain.'
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();out=R/'pair-metrics.json'
 if a.write:assert not out.exists();ex.save(out,v)
 else:assert ex.read(out)==v
 print(json.dumps({'status':'PASS',**{k:v[k]['pooled']for k in ['collectorSessions','sameFrameCheckers']}}))
if __name__=='__main__':main()
