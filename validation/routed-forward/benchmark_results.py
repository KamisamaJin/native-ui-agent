#!/usr/bin/env python3
"""Recompute paired unchanged-code service/review cost; never infer PR quality."""
import json,statistics
import benchmark as b
R=b.R

def duration(v):return v['finishedAtUnix']-v['startedAtUnix']
def reviewer(name):
 root=R/'benchmark-reviews'/name
 return b.read(root/'timing-end.json')['finishedAtUnix']-b.read(root/'timing-start.json')['startedAtUnix']
def main():
 release=b.read(R/'RELEASE.json');names=['sealed-old-a','sealed-new-a','sealed-new-b','sealed-old-b','sealed-old-final','sealed-new-final'];cycles={n:b.read(R/'operators/benchmark'/(n+'.json'))for n in names};d0=b.read(R/'operators/benchmark/sealed-d0.json');fingerprints={d0['source_sha256']}
 for n,c in cycles.items():
  assert c['startedAtUnix']>release['releasedAtUnix']
  fingerprints.add(c.get('source_sha256')or b.read(R/'evidence/benchmark'/n/'capture/result.json')['source_sha256'])
  if c['native_executed']:
   packet=b.read(R/'evidence/benchmark'/n/'capture/result.json');assert packet['coverage_satisfied']and packet['scope']=='full'
   evaluated=b.read(R/'evidence/benchmark-review-store'/n/'evaluated.json')
   assert evaluated['counts']=={'passed':28,'failed':0,'unassessed':0}
  else:
   assert n in {'sealed-new-a','sealed-new-b'}and c['status']=='feedback_complete'and c['review_current_source']
   evaluated=b.read(R/'evidence/benchmark'/n/'before-evaluated.json');assert evaluated['counts']=={'passed':28,'failed':0,'unassessed':0}
 assert len(fingerprints)==1
 old=[duration(cycles[n])for n in ['sealed-old-a','sealed-old-b']];new=[duration(cycles[n])for n in ['sealed-new-a','sealed-new-b']]
 shared=duration(d0)+reviewer('sealed-d0');result={'version':1,'required_applicable':28,'not_applicable':2,'visual_cells':6,'source_sha256':next(iter(fingerprints)),'old_feedback_service_seconds':old,'new_feedback_service_seconds':new,'mean_service_reduction':1-statistics.mean(new)/statistics.mean(old),'scope':'Two order-reversed actual native service pairs. All required coverage unchanged and original image reviews completed. Empirical neutral n=1; no PR quality/population claim. Processing sums exclude cross-condition operator scheduling, which is reported separately in raw timing.'}
 occupied={}
 for arm,feedback,final in [('old','sealed-old-a','sealed-old-final'),('new','sealed-new-a','sealed-new-final')]:
  completion=b.read(R/'evidence/benchmark-completions'/final/'completion.json');assert completion['status']=='accepted'
  occupied[arm]={'shared_D0_plus_review_seconds':shared,'feedback_service_seconds':duration(cycles[feedback]),'feedback_fresh_review_seconds':reviewer(feedback)if arm=='old'else 0,'fresh_full_final_service_seconds':duration(cycles[final]),'fresh_final_review_seconds':reviewer(final),'original_bound_completion_status':completion['status'],'observed_first_feedback_to_final_bound_wall_seconds':completion['finishedAtUnix']-cycles[feedback]['startedAtUnix']}
  occupied[arm]['processing_seconds']=sum(v for k,v in occupied[arm].items()if k.endswith('_seconds')and not k.startswith('observed_'))
 result['full_coverage_processing']=occupied
 print(json.dumps(result,indent=2))
if __name__=='__main__':
 from pathlib import Path
 main()
