import raw_review as rr,paired_grader as pg,copy,pathlib,json,datetime,sys
sys.path.insert(0,str(rr.EVAL));import evaluator as ev
W=rr.HERE/pg.SUB;prior=rr.load(W/'decision-ledger.json');updated=copy.deepcopy(prior);G=pg.PairedGrader(pg.SUB)
rows={r['assessmentId']:r for r in rr.PLAN}
for e in updated['assessments']:
 row=rows[e['assessmentId']];d=G.state(row['contextId'],row['platform']);b=e['binding'];op=d['path']/'observation.json';refs=b['provenanceRefs'];refs.extend(G.ref(op,f'/snapshots/{i}/'+('binding' if row['platform']=='android' else 'callbacks')) for i in d['indices']);refs.append(G.ref(op,f'/steps/{d["protocol"]["capture_action_index"]}'))
 ti=d['protocol']['trigger_action_index']
 if ti is not None:refs.append(G.ref(op,f'/steps/{ti}'))
 b['provenanceRefs']=list({(x['path'],json.dumps(x['locator'],sort_keys=True)):x for x in refs}.values())
assert [dict(x,binding=None) for x in updated['assessments']]==[dict(x,binding=None) for x in prior['assessments']]
rr.write(W/'decision-ledger-v002.json',updated)
out=W/'assembled-runtime-002.json'
ev.assemble('D0',pg.SUB,W/'raw-index.json',W/'decision-ledger-v002.json',out,[rr.ROOT/'validation/tool-forward/paired-evidence/d0'],[rr.ROOT/'validation/tool-forward/implementations/d0'/pg.SUB,rr.ROOT/'validation/tool-forward/common-host/Package.swift'])
g=rr.load(out);old=rr.load(rr.EVAL/'paired-sealed'/pg.SUB/'grade.json');sourceRows=rr.load(rr.HERE/'source-rows.json');sourceBy={x['assessmentId']:x for x in sourceRows};entries={x['assessmentId']:x for x in updated['assessments']}
for i,r in enumerate(g['results']):
 if r['sourceOnly']:g['results'][i]=copy.deepcopy(sourceBy[r['assessmentId']])
 else:r.update(observedValue=entries[r['assessmentId']].get('observedValue'),runtimeEvidenceCorpus='paired-evidence/d0',observationMethodLimitsRetained=True)
g['sourceOnlyReuse']=old['sourceOnlyReuse'];g['runtimeCorpus']=old['runtimeCorpus'];g['generatedAtUTC']=ev.now();g['rollups']=ev.rollups(g['results']);ev.validate_report(g)
assert [(x['assessmentId'],x['outcome'],x['reason']) for x in g['results']]==[(x['assessmentId'],x['outcome'],x['reason']) for x in old['results']]
dest=rr.EVAL/'paired-sealed'/pg.SUB/'grade-v002.json';assert not dest.exists();rr.write(dest,g)
rr.write(W/'provenance-addition-audit.json',dict(addedExactBindingPointersOnly=True,allAtomicDecisionsAndReasonsUnchanged=True,allSourceRowsIdentical=True,priorUnsealedDraft=dict(path=str(rr.EVAL/'paired-sealed'/pg.SUB/'grade.json'),sha256=rr.sha(rr.EVAL/'paired-sealed'/pg.SUB/'grade.json')),selectedFinalGrade=dict(path=str(dest),sha256=rr.sha(dest)),timestampUTC=ev.now()))
print('Paired exact binding provenance completed; atomic decisions unchanged')
