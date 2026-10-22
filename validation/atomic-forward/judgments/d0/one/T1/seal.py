import pathlib,json,hashlib,time,datetime
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/one/T1'
assert not (O/'SEAL.json').exists(),'Already sealed; no edits permitted'
coverage=json.loads((O/'coverage.json').read_text());total=0
for p in sorted((B/'evaluation-inputs/d0/T1').glob('*/*/*')):
 key=str(p.relative_to(B/'evaluation-inputs/d0/T1'));judge=json.loads((O/key/'judge.json').read_text());cat=json.loads((p/'catalog.json').read_text());inp=json.loads((p/'inputs.json').read_text());assert set(judge)=={'review','attributions'};review=judge['review'];assert set(review)=={'version','catalog_sha256','observation_sha256','decisions'};assert review['version']==1;assert review['catalog_sha256']==cat['catalog_sha256'];assert review['observation_sha256']==inp['observation_sha256'];visual={r['review_id']:r for r in cat['rows'] if r['method']=='visual'};assert set(visual)=={d['review_id'] for d in review['decisions']};assert len(review['decisions'])==len(visual)
 for d in review['decisions']:
  assert set(d)=={'review_id','actual','reason','snapshot_indices'};assert d['actual'] is None or type(d['actual'])is bool;assert set(d['snapshot_indices'])<=set(coverage[key][visual[d['review_id']]['state']]['indices']);total+=1
 for a in judge['attributions']:assert set(a)=={'id','cause','reason','snapshot_indices'}
assert total==48
checks=json.loads((O/'schema-self-checks.json').read_text());assert len(checks)==8 and all(x['schema_valid'] for x in checks)
hashes=json.loads((O/'input-hashes.json').read_text())
for rel,expected in hashes.items():assert hashlib.sha256((B/rel).read_bytes()).hexdigest()==expected,rel
phase=json.loads((O/'phase.json').read_text());assert type(phase['startedAtUnix'])in [int,float];end=time.time();phase.update({'finishedAtUnix':end,'finishedAtUTC':datetime.datetime.fromtimestamp(end,datetime.timezone.utc).isoformat(),'durationSeconds':end-phase['startedAtUnix'],'status':'complete; sealed immediately after final audit','deliveries':8,'selectedStatesInspected':56,'selectedOriginalFrames':560,'qualitativeDecisions':48,'supportedMeasuredFailureAttributions':4,'schemaSelfChecks':8});(O/'phase.json').write_text(json.dumps(phase,indent=2)+'\n')
files={str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SEAL.json' and '__pycache__'not in p.parts};(O/'SEAL.json').write_text(json.dumps({'files':files},indent=2)+'\n')
# From this point only read/verify; never mutate any output.
seal=json.loads((O/'SEAL.json').read_text());actual={str(p.relative_to(O)) for p in O.rglob('*') if p.is_file() and p.name!='SEAL.json' and '__pycache__'not in p.parts};assert actual==set(seal['files'])
for rel,expected in seal['files'].items():assert hashlib.sha256((O/rel).read_bytes()).hexdigest()==expected,rel
print(json.dumps({'sealed':True,'files':len(files),'inputHashesVerified':len(hashes),'startedAtUnix':phase['startedAtUnix'],'finishedAtUnix':phase['finishedAtUnix'],'durationSeconds':phase['durationSeconds'],'qualitativeDecisions':total,'strictMeasuredFailuresWithProductAttribution':4,'unsupportedIOSFontWeightCells':28}))
