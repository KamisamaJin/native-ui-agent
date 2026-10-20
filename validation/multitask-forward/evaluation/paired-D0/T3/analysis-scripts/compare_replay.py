from pathlib import Path
import json,hashlib,shutil,collections
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'evaluation/paired-D0/T3';D=R/'precision-replay/T3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def save(p,d):assert not p.exists(),p;p.write_text(json.dumps(d,indent=2)+'\n')
def stat(s):return {'passed':'P','failed':'F','unassessed':'U'}.get(s,'U')
table=json.loads((R/'design-v2/T3/private/acceptance-table.json').read_text())['rows'];rows=[];unitproof=[];copyproof=[];rootcomparison=json.loads((D/'comparison.json').read_text());shutil.copyfile(D/'comparison.json',O/'original-precision-replay-comparison.json')
for alias in ['source-a','source-b']:
 for case in ['P1','P2']:
  for platform in ['ios','android']:
   sd=D/alias/case/platform;dest=O/'same-frame-replay'/alias/case/platform;dest.mkdir(parents=True);op=R/f'common-corpora/T3/{alias}/d0/{platform}/{case}/observation.json';obs=json.loads(op.read_text());commands=json.loads((sd/'commands.json').read_text());plan=R/f'design-v2/T3/public/compiled/{case}/{platform}/plan.json'
   for f in ['commands.json','baseline-v6.json','candidate-v7.json','baseline-v6.log','candidate-v7.log']:
    shutil.copyfile(sd/f,dest/f);assert (sd/f).read_bytes()==(dest/f).read_bytes();copyproof.append({'source':ref(sd/f),'preserved_output':ref(dest/f),'byte_exact':True})
   reports={k:json.loads((sd/(k+'.json')).read_text()) for k in ['baseline-v6','candidate-v7']};maps={k:{x['id']:x for x in rep['assertions']} for k,rep in reports.items()}
   for command in commands:
    assert command['observationSHA256']==sha(op);assert command['planSHA256']==sha(plan);assert command['SDKStarted']==False
    argv=command['argv'];assert Path(argv[argv.index('--observation')+1])==op;assert Path(argv[argv.index('--plan')+1])==plan
   assert all(rep['input_hashes']['observation']==sha(op) and rep['input_hashes']['plan']==sha(plan) for rep in reports.values())
   unitproof.append({'alias':alias,'case':case,'platform':platform,'same_original_observation':ref(op),'unchanged_plan':ref(plan),'reports':{k:ref(sd/(k+'.json')) for k in reports},'commands':ref(sd/'commands.json'),'command_statuses':[{'tool':c['tool'],'exitCode':c['exitCode'],'SDKStarted':c['SDKStarted']} for c in commands],'report_statuses':{k:rep['status'] for k,rep in reports.items()},'exit_interpretation':'Reports and nonzero assertion dispositions are retained exactly. Exit1 here indicates failed assertions in a valid produced report, not missing native evidence or a reason to force geometry passes.'})
   for req in table:
    if req['case']!=case or req['platform']!=platform or req['class']!='geometry':continue
    rec={'alias':alias,**req,'observation':ref(op),'plan':ref(plan),'reports':{k:ref(sd/(k+'.json')) for k in reports}};rec.pop('plan_assertion_id',None)
    if not req['applicable']:
     rec.update(before='N/A',after='N/A',before_assertion=None,after_assertion=None,original_reason=req['reason'],evidence=[])
    else:
     old=maps['baseline-v6'].get(req['plan_assertion_id']);new=maps['candidate-v7'].get(req['plan_assertion_id']);rec.update(before=stat(old.get('status')) if old else 'U',after=stat(new.get('status')) if new else 'U',before_assertion=old,after_assertion=new)
     indices=sorted(set((old or {}).get('snapshot_indices',[]))|set((new or {}).get('snapshot_indices',[])));ev=[]
     for i in indices:
      png=op.parent/obs['snapshots'][i]['screenshot'];ev.append({'snapshot_index':i,**ref(png)})
     rec['evidence']=ev;rec['actual_value_changed']=(old or {}).get('actual')!=(new or {}).get('actual');rec['geometry_evidence_changed']=(old or {}).get('geometry_evidence')!=(new or {}).get('geometry_evidence')
    rows.append(rec)
# Reconcile every preregistered applicable geometry row without adding/change to its expectation or tolerance.
ri={(r['alias'],r['case'],r['platform'],r['state']+'/'+r['requirement']):r for r in rows};assert len(ri)==144
for orig in rootcomparison['geometryRows']:
 key=(orig['alias'],orig['case'],orig['platform'],orig['id']);r=ri[key];assert r['applicable'];assert all(orig[k]==r[k] for k in ['expected','unit','op','tolerance']);assert stat(orig['before'])==r['before'] and stat(orig['after'])==r['after'];assert orig['observationSHA256']==r['observation']['sha256']
assert len(rootcomparison['geometryRows'])==sum(r['applicable'] for r in rows)
def stats(rs):
 return {'denominator':len(rs),'applicable':sum(r['applicable'] for r in rs),'original_NA':sum(not r['applicable'] for r in rs),'before':{s:sum(r['before']==s for r in rs) for s in ['P','F','U','N/A']},'after':{s:sum(r['after']==s for r in rs) for s in ['P','F','U','N/A']},'transition_counts':dict(collections.Counter(r['before']+'->'+r['after'] for r in rs)),'status_changes':sum(r['before']!=r['after'] for r in rs),'applicable_numeric_actual_changes':sum(r.get('actual_value_changed',False) for r in rs),'geometry_evidence_representation_changes':sum(r.get('geometry_evidence_changed',False) for r in rs)}
result={'schema_version':1,'task':'T3','stage':'paired-D0','scope':'Preregistered old/new checker replay on identical original v7 observations. All144 geometry cells retained:104 applicable plus40 original N/A. Same fixed approved expectations/tolerances. Pure arithmetic/evidence diagnostic, never collector or product quality gains. Android raw replay P does not alter original accepted-oracle U from input direction mismatch.','pooled':stats(rows),'by_platform':{p:stats([r for r in rows if r['platform']==p]) for p in ['ios','android']},'by_source':{a:stats([r for r in rows if r['alias']==a]) for a in ['source-a','source-b']},'rows':rows,'input_provenance':unitproof,'preserved_artifact_byte_checks':copyproof,'original_preregistered_comparison':ref(D/'comparison.json'),'all_root_applicable_geometry_rows_reconciled':True,'evaluator_replay_commands_run':0}
save(O/'same-frame-precision-comparison.json',result);print(json.dumps({'pooled':result['pooled'],'by_platform':result['by_platform']},indent=2))
