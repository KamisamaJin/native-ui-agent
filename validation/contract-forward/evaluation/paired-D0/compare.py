from pathlib import Path
from collections import Counter
import json,hashlib,datetime
R=Path(__file__).resolve().parents[2];O=R/'evaluation/paired-D0';I=R/'evaluation-inputs/paired-D0';B=json.loads((I/'batch.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
allowed={'native_content','business_current','business_transition','style_native','native_geometry'};commands=[];proof=[];sensitivity=[];summary={};failures=[]
for c in B['corpora']:
 alias=c['anonymousID'];versions={}
 for version,key in [('v5','newV5Captures'),('v6','reuseV6Captures')]:
  rows=[];checks=[]
  for case in B['cases']:
   for platform in ['ios','android']:
    g=json.loads((O/alias/version/'native-base'/case/platform/'grade.json').read_text());rows+=g['rows'];checks+=g['checks']
    cp=R/c[key]/platform/f'{case}-command.json';cmd=json.loads(cp.read_text());cap=R/c[key]/platform/case;m=json.loads((cap/'manifest.json').read_text())
    suffix='WorkshopEnrollmentCard.swift' if platform=='ios' else 'WorkshopEnrollmentCard.kt'
    receipt=dict(alias=alias,version=version,case=case,platform=platform,command=str(cp.relative_to(R)),command_sha256=sha(cp),exitCode=cmd['exitCode'],wallSeconds=cmd['wallSeconds'],startedAtUTC=cmd['startedAtUTC'],finishedAtUTC=cmd['finishedAtUTC'],inputHashes=cmd['inputHashes'],buildCacheHit=m.get('build_cache',{}).get('hit'),buildExitCode=m.get('build_exit_code'),manifestStatus=m.get('status'),manifest_sha256=sha(cap/'manifest.json'),componentHashes={k:v for k,v in m.get('source_hashes',{}).items() if k.endswith(suffix)})
    commands.append(receipt)
    if cmd['exitCode']!=0:
     ns=cap/'native-summary.json';native=json.loads(ns.read_text());obs=json.loads((cap/'observation.json').read_text());sets=[dict(index=i,state=s.get('state_id'),all_targets_observed=s['observation_set'].get('all_targets_observed'),binding_stable=s['observation_set'].get('binding_stable')) for i,s in enumerate(obs['steps']) if s.get('observation_set')]
     failures.append(dict(**receipt,native_summary=str(ns.relative_to(R)),native_summary_sha256=sha(ns),failure_texts=[x['failureText'] for x in native.get('testFailures',[])],native_result=native.get('result'),coverage=obs.get('coverage'),post_action_sets=sets,incomplete_post_action_sets=sum(x['all_targets_observed'] is not True for x in sets),blocked_dispatch=obs['steps'][1].get('dispatch'),blocked_callback_delta=obs['steps'][1].get('callback_delta'),interpretation='Requested native activation encountered an expected-disabled option; assertion failure is not a product handler defect. Callback behavior remains U under unchanged successful-dispatch gate.'))
  native=[r for r in rows if r['class'] in allowed];assert len(rows)==528 and len(native)==506
  value=dict(rows=rows,checks=checks,counts={s:sum(r['status']==s for r in rows) for s in ['P','F','U','N/A']},native_comparison_counts={s:sum(r['status']==s for r in native) for s in ['P','F','U','N/A']},scope='Manual=None, source_root=None, api_review=None. All rows retained; five native classes alone contribute paired comparison.')
  assert not (O/alias/version/'grade.json').exists();put(O/alias/version/'grade.json',value);versions[version]=value
 a={r['id']:r for r in versions['v5']['rows'] if r['class'] in allowed};b={r['id']:r for r in versions['v6']['rows'] if r['class'] in allowed};assert set(a)==set(b)
 changes={k:[] for k in ['gains','losses','assessed_conflicts','other_disposition_changes','unchanged']}
 for id,x in a.items():
  y=b[id];assert x['expected']==y['expected'] and x['class']==y['class'] and x['unit']==y['unit']
  if x['status']=='U' and y['status'] in ['P','F']:key='gains'
  elif x['status'] in ['P','F'] and y['status']=='U':key='losses'
  elif x['status'] in ['P','F'] and y['status'] in ['P','F'] and x['status']!=y['status']:key='assessed_conflicts'
  elif x['status']!=y['status']:key='other_disposition_changes'
  else:key='unchanged'
  changes[key].append(dict(id=id,**{'class':x['class']},v5=x,v6=y) if key!='unchanged' else dict(id=id,status=x['status'],**{'class':x['class']}))
  if x['class']=='native_geometry' and (x['status'] in ['F','U'] or y['status'] in ['F','U']):sensitivity.append(dict(alias=alias,id=id,v5=x,v6=y,limitation='Raw F/U retained; near48dp serialized bounds straddle the frozen lower bound. No natural-product-defect inference at subresolution, no tolerance change.'))
 for case in B['cases']:
  for p in ['ios','android']:
   x=next(t for t in commands if t['alias']==alias and t['version']=='v5' and t['case']==case and t['platform']==p);y=next(t for t in commands if t['alias']==alias and t['version']=='v6' and t['case']==case and t['platform']==p)
   record=dict(alias=alias,case=case,platform=p,same_input_hashes=x['inputHashes']==y['inputHashes'],same_component_hashes=bool(x['componentHashes']) and set(x['componentHashes'].values())==set(y['componentHashes'].values()),v5_input_hashes=x['inputHashes'],v6_input_hashes=y['inputHashes'],v5_component_hashes=x['componentHashes'],v6_component_hashes=y['componentHashes']);assert record['same_input_hashes'] and record['same_component_hashes'];proof.append(record)
 times={v:{p:sum(x['wallSeconds'] for x in commands if x['alias']==alias and x['version']==v and x['platform']==p) for p in ['ios','android']} for v in ['v5','v6']}
 result=dict(native_cells=506,native_classes=sorted(allowed),counts={v:versions[v]['native_comparison_counts'] for v in ['v5','v6']},change_counts={k:len(v) for k,v in changes.items()},actual_command_sums_seconds_by_platform=times,**changes);put(O/alias/'comparison.json',result);summary[alias]={k:result[k] for k in ['native_cells','counts','change_counts','actual_command_sums_seconds_by_platform']}
put(O/'commands.json',commands);put(O/'native-failure-ledger.json',failures);put(O/'same-input-source-verification.json',proof);put(O/'numerical-resolution-sensitivity.json',sensitivity)
totals={v:{p:sum(x['wallSeconds'] for x in commands if x['version']==v and x['platform']==p) for p in ['ios','android']} for v in ['v5','v6']}
put(O/'summary.json',dict(arms=summary,total_actual_command_sums_seconds_by_platform=totals,failed_commands=4,scope='Native classes only; no visual/API/input credit.',limitations=['V5 actual acquisition followed V6 actual D0; nonrandomized/noninterleaved order.','V6 raw and per-case native grades are exact reuse, not reacquisition.','Build/cache state, shared Mac contention and failed native assertions limit causal speed attribution.','All command durations including failures are retained; summed process wall time is not concurrent workflow elapsed time.','Natural business/style defect denominators are zero: detection recall N/A.','P2 failures are expected-disabled native activation assertions, not incomplete target sets or product handler defects.']))
print(json.dumps(dict(arms=summary,totals=totals,failures=[dict(alias=x['alias'],version=x['version'],exitCode=x['exitCode'],texts=x['failure_texts'],incomplete_sets=x['incomplete_post_action_sets']) for x in failures]),indent=2))
