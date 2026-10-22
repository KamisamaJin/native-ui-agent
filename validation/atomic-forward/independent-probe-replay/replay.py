import os,sys,json,time,hashlib,datetime,subprocess,shutil
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;W=R.parents[2];S=W/'native-ui-agent/scripts';O=R.with_name('independent-probe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canon=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
start=time.time();commands=[]
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def verify_original(stage):
 manifest=json.loads((O/'seal.json').read_text());digest=canon(manifest);expected=(O/'seal.sha256').read_text().strip();bad=[p for p,v in manifest['files'].items()if not(O/p).is_file()or sha(O/p)!=v['sha256']];badlinks=[p for p,v in manifest.get('symlinks',{}).items()if not(O/p).is_symlink()or os.readlink(O/p)!=v];result={'stage':stage,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_seal_sha256':digest,'expected_sha256':expected,'file_count':len(manifest['files']),'mismatched_files':bad,'mismatched_links':badlinks,'verified':digest==expected and not bad and not badlinks};write(R/f'original-seal-{stage}.json',result);return result
before=verify_original('before');assert before['verified']and before['file_count']==876
files=[S.parent/'SKILL.md',S.parent/'references/atomic-review.md']+sorted(S.glob('*.py'))
toolbefore={str(p.relative_to(S.parent)):sha(p)for p in files};write(R/'tool-identities-before.json',{'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':toolbefore})
for p in files:
 dest=R/'tool-snapshot'/p.relative_to(S.parent);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
def run(argv,tag):
 begin=time.time();stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');p=subprocess.run(argv,cwd=R,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);log=R/'logs'/f'{len(commands):02d}-{tag}.log';log.parent.mkdir(exist_ok=True);log.write_text(p.stdout);entry={'argv':argv,'cwd':str(R),'started_utc':stamp,'wall_seconds':time.time()-begin,'exit_code':p.returncode,'log':str(log.relative_to(R)),'log_sha256':sha(log),'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1'}};commands.append(entry)
 with(R/'commands.jsonl').open('a')as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
 print(tag,'exit',p.returncode,p.stdout.strip()[-600:],flush=True);return p.returncode
approval=json.loads((O/'APPROVAL.json').read_text());results=[]
for key in ['android-normal','android-narrow-large','android-normal-v2','android-narrow-large-v2','ios-normal','ios-narrow-large']:
 platform=key.split('-')[0];base=key.removesuffix('-v2');plan=O/'generated'/base/'plan.json';obs=O/'captures'/key/'observation.json';sub=O/'submissions'/f'{key}.json';prior=O/'reviews'/key
 catalog=R/'catalogs'/f'{key}.json';catalog.parent.mkdir(exist_ok=True)
 common=['--plan',str(plan),'--design-lock',str(O/'design/lock.json'),'--design-sha256',approval['design_lock_sha256'],'--policy',str(O/'design/policy.json'),'--policy-sha256',approval['policy_sha256'],'--platform',platform]
 row={'run':key,'input_hashes':{'plan':sha(plan),'observation':sha(obs),'submission':sha(sub),'original_manual':sha(prior/'manual.json'),'lock':sha(O/'design/lock.json'),'policy':sha(O/'design/policy.json')},'original_report_counts':json.loads((prior/'report.json').read_text())['counts']}
 row['catalog_exit']=run([sys.executable,str(S/'review_contract.py'),'catalog']+common+['--output',str(catalog)],key+'-catalog')
 if catalog.exists():row['catalog_unchanged']=json.loads(catalog.read_text())==json.loads((O/'generated'/base/'catalog.json').read_text())
 out=R/'reviews'/key
 row['review_exit']=run([sys.executable,str(S/'review_contract.py'),'review']+common+['--observation',str(obs),'--submission',str(sub),'--output',str(out)],key+'-review-original-request')
 report=out/'report.json'
 if report.exists():
  new=json.loads(report.read_text());old=json.loads((prior/'report.json').read_text());row['replayed_report_counts']=new['counts'];row['report_status_changes']=[{'id':n['id'],'before':next(a['status']for a in old['assertions']if a['id']==n['id']),'after':n['status']}for n in new['assertions']if n['status']!=next(a['status']for a in old['assertions']if a['id']==n['id'])]
 checks=['--plan',str(plan),'--observation',str(obs),'--platform',platform,'--design-lock',str(O/'design/lock.json'),'--design-sha256',approval['design_lock_sha256'],'--review-policy',str(O/'design/policy.json'),'--review-policy-sha256',approval['policy_sha256']]
 for label,manual in [('original-bound-bundle',prior/'manual.json'),('rebuilt-original-request',out/'manual.json')]:
  if not manual.exists():row[label]={'skipped':'No rebuilt manual emitted; original failure preserved'};continue
  dest=R/'checks'/f'{key}-{label}.json';dest.parent.mkdir(exist_ok=True)
  code=run([sys.executable,str(S/'native_checks.py')]+checks+['--manual',str(manual),'--output',str(dest)],key+'-check-'+label);row[label]={'exit_code':code,'counts':json.loads(dest.read_text()).get('counts')if dest.exists()else None}
 if (out/'findings.json').exists():
  findings=json.loads((out/'findings.json').read_text());pixel=[]
  for f in findings:
   if f.get('aspect')not in {'rendered_fill','rendered_canvas'}:continue
   samples=f.get('actual',{}).get('samples',[]);bad=[s for s in samples if s.get('eligible')is True and s['status']!='measured'];pixel.append({'id':f['id'],'status':f['status'],'sample_count':len(samples),'measured_count':sum(s['status']=='measured'for s in samples),'ineligible_count':sum(s.get('eligible')is False for s in samples),'eligible_unmeasurable':bad,'false_pass_with_eligible_unmeasurable':bool(bad)and f['status']=='passed'})
  row['pixel_eligibility']=pixel
 results.append(row)
# Independently inspect the actual new state identity gate on sealed original packets.
sys.path.insert(0,str(S));import native_checks,design_contract
identities=[]
for row in results:
 key=row['run'];base=key.removesuffix('-v2');plan=json.loads((O/'generated'/base/'plan.json').read_text());obs=json.loads((O/'captures'/key/'observation.json').read_text())
 for state in plan['states']:
  found,complete,reason,capture=native_checks.bound_state_evidence(obs,state)
  identities.append({'run':key,'state_id':state['id'],'original_indices':capture.get('snapshot_indices')if capture else None,'eligible_indices':[i for i,s in found],'complete':complete,'reason':reason,'binding':capture.get('binding')if capture else None})
write(R/'strict-state-identity-results.json',identities)
toolafter={str(p.relative_to(S.parent)):sha(p)for p in files};write(R/'tool-identities-after.json',{'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':toolafter,'unchanged_during_replay':toolbefore==toolafter})
after=verify_original('after');write(R/'results.json',{'started_epoch':start,'finished_epoch':time.time(),'wall_seconds':time.time()-start,'sdk_launched':False,'original_seal_verified_before_and_after':before['verified']and after['verified'],'tool_sources_unchanged_during_replay':toolbefore==toolafter,'runs':results,'scope':'Current tools replay the sealed original observations and original actual-only manual requests. Stored old bound bundles are also attempted separately; all rejection/differences are retained. No input, component, expectation, action, original seal or old file is changed.'})
print('DONE',[(r['run'],r.get('replayed_report_counts'),r.get('original-bound-bundle'))for r in results])
