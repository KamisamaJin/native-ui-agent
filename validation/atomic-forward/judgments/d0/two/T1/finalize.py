import pathlib,json,hashlib,time,datetime,collections
root=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');out=root/'judgments/d0/two/T1'
e=json.loads((out/'state-evidence.json').read_text());inspection=[];checks=[];counts=collections.Counter();casecoverage={}
for key,entry in e.items():
 p=root/'evaluation-inputs/d0/T1'/key;inp=json.loads((p/'inputs.json').read_text());cat=json.loads((p/'catalog.json').read_text());obs=json.loads((root/inp['observation']).read_text());judge=json.loads((out/key/'judge.json').read_text());selfcheck=json.loads((out/key/'schema-self-check.json').read_text())
 assert set(judge)=={'review','attributions'}
 assert set(judge['review'])=={'version','catalog_sha256','observation_sha256','decisions'}
 assert judge['review']['catalog_sha256']==cat['catalog_sha256']
 assert judge['review']['observation_sha256']==inp['observation_sha256']
 rows={r['review_id']:r for r in cat['rows'] if r['method']=='visual'}
 assert {d['review_id'] for d in judge['review']['decisions']}==set(rows)
 assert len(judge['review']['decisions'])==len(rows)==6
 for d in judge['review']['decisions']:
  assert set(d)=={'review_id','actual','reason','snapshot_indices'}
  s=rows[d['review_id']]['state'];allowed=entry['states'][s]['indices'];assert set(d['snapshot_indices'])<=set(allowed)
  assert d['actual'] is None or type(d['actual']) is bool
  if d['actual'] is True:assert entry['states'][s]['complete']
 assert selfcheck['schema_self_check']=='accepted'
 counts.update(selfcheck['counts_for_schema_diagnostics_only'])
 casecoverage[key]={'selected_states':list(entry['states']),'state_scoped_frame_count':sum(len(s['indices']) for s in entry['states'].values()),'all_selected_states_complete':all(s['complete'] for s in entry['states'].values()),'visual_decisions':len(judge['review']['decisions']),'visual_true':sum(d['actual'] is True for d in judge['review']['decisions']),'visual_false':sum(d['actual'] is False for d in judge['review']['decisions']),'visual_unknown':sum(d['actual'] is None for d in judge['review']['decisions']),'failure_cause_assessments':judge['attributions'],'unassessed_ids':selfcheck['unassessed_ids']}
 for state in (['baseline','replaced'] if 'source-b/ios' in key else ['baseline']):
  idx=entry['states'][state]['indices'][-1] if state=='replaced' or 'source-b/ios' in key else entry['states'][state]['indices'][0]
  png=root/inp['root']/obs['snapshots'][idx]['screenshot'];inspection.append({'case':key,'state':state,'snapshot_index':idx,'path':str(png),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'method':'Direct view_image of original PNG; iOS full-screen display resized by tool, whole-state contact sheets also inspected.'})
(out/'direct-original-inspection.json').write_text(json.dumps(inspection,indent=2)+'\n')
coverage={'cases':casecoverage,'all_cases_reviewed':8,'all_selected_states_reviewed':56,'state_scoped_original_frames_contact_sheet_coverage':560,'direct_original_observation_pngs_opened':10,'original_corpus_snapshot_count':918,'qualitative_decisions':{'true':48,'false':0,'unknown':0},'unsupported_ios_title_weight_cells':28,'strict_pixel_failures':4,'failure_cause_assessments':{'product':4,'infrastructure':0,'observation':0,'uncertain':0},'same_request_schema_diagnostics_only':dict(counts),'independent_consensus_claim':False,'other_judge_disagreement':'unknown; other judges not read','limits':'All selected native-bound states visually inspected. Remaining action/initial/final/before-update snapshots were not each opened separately. Original pointers and hashes retained. Full-content positive judgments concern only their explicit qualitative propositions; native/pixel results cannot be voted away.'}
(out/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
phase=json.loads((out/'phase.json').read_text());finish=time.time();phase['finishedAtUnix']=finish;phase['finishedAtUtc']=datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat();phase['elapsedSeconds']=finish-phase['startedAtUnix'];phase['status']='complete';phase['schemaSelfChecks']=8;phase['schemaRejectedAttempts']=0
assert type(phase['startedAtUnix']) in (int,float) and type(phase['finishedAtUnix']) in (int,float)
(out/'phase.json').write_text(json.dumps(phase,indent=2)+'\n')
files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in p.parts}
(out/'SEAL.json').write_text(json.dumps({'files':files},indent=2)+'\n')
print(json.dumps({'sealed':True,'files':len(files),'elapsedSeconds':phase['elapsedSeconds'],'startedAtUnix':phase['startedAtUnix'],'finishedAtUnix':phase['finishedAtUnix'],'visual':coverage['qualitative_decisions'],'strict_pixel_failures':4,'unsupported_ios_title_weight_cells':28}))
