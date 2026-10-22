import json,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parent;O=R.with_name('independent-probe');data=json.loads((R/'results.json').read_text())
def diff(a,b,path=''):
 out=[]
 if type(a)!=type(b):return [{'path':path,'change':'type_or_value','before':a,'after':b}]
 if isinstance(a,dict):
  for key in sorted(set(a)|set(b)):
   p=path+'/'+key.replace('~','~0').replace('/','~1')
   if key not in a:out.append({'path':p,'change':'added','after':b[key]})
   elif key not in b:out.append({'path':p,'change':'removed','before':a[key]})
   else:out+=diff(a[key],b[key],p)
 elif isinstance(a,list):
  if len(a)!=len(b):out.append({'path':path,'change':'list_length','before':len(a),'after':len(b)})
  for i,(x,y)in enumerate(zip(a,b)):out+=diff(x,y,path+'/'+str(i))
 elif a!=b:out.append({'path':path,'change':'value','before':a,'after':b})
 return out
all_diffs={};totals={'state_count':0,'pixel_assertion_count':0,'sample_count':0,'measured_count':0,'ineligible_count':0,'eligible_unmeasurable_count':0,'false_pass_count':0}
ident=json.loads((R/'strict-state-identity-results.json').read_text());totals['state_count']=len(ident)
for run in data['runs']:
 key=run['run'];before=json.loads((O/'reviews'/key/'manual.json').read_text());after=json.loads((R/'reviews'/key/'manual.json').read_text());d=diff(before,after);all_diffs[key]={'old_bundle_vs_current_rebuild':d,'all_changes_are_added_pixel_sample_eligibility':all(x['change']=='added'and x['path'].endswith('/eligible')and'/actual/samples/'in x['path']for x in d),'old_report_vs_current_report':diff(json.loads((O/'reviews'/key/'report.json').read_text()),json.loads((R/'reviews'/key/'report.json').read_text()))}
 for atom in run['pixel_eligibility']:
  totals['pixel_assertion_count']+=1;totals['sample_count']+=atom['sample_count'];totals['measured_count']+=atom['measured_count'];totals['ineligible_count']+=atom['ineligible_count'];totals['eligible_unmeasurable_count']+=len(atom['eligible_unmeasurable']);totals['false_pass_count']+=atom['false_pass_with_eligible_unmeasurable']
(R/'exact-artifact-differences.json').write_text(json.dumps(all_diffs,indent=2,ensure_ascii=False)+'\n');(R/'eligibility-summary.json').write_text(json.dumps(totals,indent=2)+'\n')
print(json.dumps({'totals':totals,'diffs':{k:{'count':len(v['old_bundle_vs_current_rebuild']),'eligibility_only':v['all_changes_are_added_pixel_sample_eligibility'],'report_diff_count':len(v['old_report_vs_current_report'])}for k,v in all_diffs.items()}},indent=2))
# Read-only source evidence for the newly exercised strict gate and eligibility blocker.
for source,start,end in [('native_checks.py','def bound_state_evidence','def legacy_geometry_value'),('review_contract.py',"                incomplete = any",'                proofs =')]:
 text=(R.parents[2]/'native-ui-agent/scripts'/source).read_text();a=text.index(start);b=text.index(end,a)
 (R/(source+'.gate-excerpt.txt')).write_text(text[a:b])
