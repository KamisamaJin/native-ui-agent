from pathlib import Path
import json,hashlib,time,datetime,collections
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/two/T2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
assert not (O/'SEAL.json').exists()
index=load(O/'inspection-index.json');checks=load(O/'schema-selfcheck-summary.json')['cases'];assert len(checks)==12 and all(c['accepted'] for c in checks)
judges=[load(O/e['case']/'judge.json') for e in index];assert len(judges)==12
for j in judges:
 assert set(j)=={'review','attributions'}
 assert len(j['review']['decisions'])==6
 assert all(set(x)=={'review_id','actual','reason','snapshot_indices'} for x in j['review']['decisions'])
expected={**load(O/'input-hashes.json'),**load(O/'additional-input-hashes.json')}
mismatches=[{'path':p,'before':h,'after':sha(Path(p)) if Path(p).is_file() else None} for p,h in expected.items() if not Path(p).is_file() or sha(Path(p))!=h]
assert not mismatches,mismatches
integrity={'checkedAtUnix':time.time(),'checked_input_files':len(expected),'unchanged':not mismatches,'mismatches':mismatches,'original_observation_sha_checks':[]}
for e in index:
 i=load(B/'evaluation-inputs/final/T2'/e['case']/'inputs.json');actual=sha(B/i['observation']);assert actual==i['observation_sha256'];integrity['original_observation_sha_checks'].append({'case':e['case'],'expected':i['observation_sha256'],'actual':actual})
(O/'final-input-integrity.json').write_text(json.dumps(integrity,indent=2)+'\n')
actuals=collections.Counter(str(x['actual']) for j in judges for x in j['review']['decisions'])
counts={s:sum(c['counts'][s] for c in checks) for s in ['passed','failed','unassessed']}
summary={'task':'T2','stage':'final','panel':'two','reviewer_scope':'Independent anonymous review; no other reviewer, assignment, original self-review or intended outcome read.','case_count':len(index),'state_count':sum(len(e['states']) for e in index),'bound_state_snapshot_count':sum(len(v['indices']) for e in index for v in e['states'].values()),'all_original_snapshot_count':sum(e['snapshot_count'] for e in index),'contact_sheet_pages_inspected':len(load(O/'contact-sheet-manifest.json')),'qualitative':{'true':actuals['True'],'false':actuals['False'],'unknown':actuals['None']},'schema_selfcheck_recomputed_counts':counts,'supported_failure_causes':[],'uncertainty':['source-b/ios/H1 submitted wrapping and overlap unknown: coherent captured union ends at 1640 of 1646 pt.','All 42 iOS selected title-native-weight facts remain unsupported U.','Six narrow iOS updated-notice pixel facts remain U because fully visible target sampling is unavailable.'],'disagreement':'Other judges were not read; no independent consensus or disagreement claim is made.','limits':'This selected-atom review does not certify every full-brief layout, typography, behaviour or arbitrary caller input. Same-request duplicate-slot evaluator checks are schema self-checks only.'}
(O/'status.json').write_text(json.dumps(summary,indent=2)+'\n')
phase=load(O/'phase.json');finished=time.time();phase['finishedAtUnix']=finished;phase['finishedAtUtc']=datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat();phase['elapsedSeconds']=finished-phase['startedAtUnix'];(O/'phase.json').write_text(json.dumps(phase,indent=2)+'\n')
files={str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in p.relative_to(O).parts}
(O/'SEAL.json').write_text(json.dumps({'files':files},indent=2)+'\n')
print(json.dumps({'sealed_files':len(files),'qualitative':summary['qualitative'],'states':summary['state_count'],'bound_snapshots':summary['bound_state_snapshot_count'],'all_snapshots':summary['all_original_snapshot_count'],'elapsedSeconds':phase['elapsedSeconds'],'seal_sha256':sha(O/'SEAL.json')},indent=2))
