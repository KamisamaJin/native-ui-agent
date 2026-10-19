import sys,pathlib,json,datetime,copy
import raw_review as rr
sys.path.insert(0,str(rr.EVAL))
import evaluator as ev
SUB='submission-4f4364';WORK=rr.HERE/SUB
out=WORK/'assembled-runtime-001.json'
ev.assemble('D0',SUB,WORK/'raw-index.json',WORK/'decision-ledger.json',out,[rr.ROOT/'validation/tool-forward/paired-evidence/d0'],[rr.ROOT/'validation/tool-forward/implementations/d0'/SUB,rr.ROOT/'validation/tool-forward/common-host/Package.swift'])
grade=rr.load(out);sources=rr.load(rr.HERE/'source-rows.json');sourceBy={x['assessmentId']:x for x in sources};entries={x['assessmentId']:x for x in rr.load(WORK/'decision-ledger.json')['assessments']}
for i,row in enumerate(grade['results']):
 if row['sourceOnly']:grade['results'][i]=copy.deepcopy(sourceBy[row['assessmentId']])
 else:
  e=entries[row['assessmentId']];row['observedValue']=e.get('observedValue');row['runtimeEvidenceCorpus']='paired-evidence/d0';row['observationMethodLimitsRetained']=True
assert [x for x in grade['results'] if x['sourceOnly']]==sources
assert sum(not x['sourceOnly'] for x in grade['results'])==1830
assert sum(x['sourceOnly'] for x in grade['results'])==379
assert all('/paired-evidence/d0/' in z['path'] for x in grade['results'] if not x['sourceOnly'] for z in x['exactSources']+x['consideredSources'])
grade['runtimeCorpus']='paired legacy only; main current-collector runtime not used'
grade['sourceOnlyReuse']=dict(policy='All sourceOnly rows are exact unchanged full-row copies, explicitly authorized because the D0 production capsule and neutral host are identical. No main runtime row or runtime evidence is reused.',originalGrade=dict(path=str(rr.EVAL/'d0-sealed'/SUB/'grade.json'),sha256='72cb5aeada8ecb2dd200d2857143c3eebe68db6da11c822dc9aed982e77abb36'),reusedRows=dict(path=str(rr.HERE/'source-rows.json'),sha256=rr.sha(rr.HERE/'source-rows.json')),evidenceRecordNamespace='Source-only E identifiers resolve to the original sealed source assessment; paired runtime PL identifiers resolve to this paired raw packet. Exact source rows remain byte-content-equivalent as JSON objects.')
grade['generatedAtUTC']=ev.now();grade['rollups']=ev.rollups(grade['results']);ev.validate_report(grade)
dest=rr.EVAL/'paired-sealed'/SUB;dest.mkdir(parents=True,exist_ok=True);p=dest/'grade.json';assert not p.exists();rr.write(p,grade)
rr.write(WORK/'assembly-audit.json',dict(valid=True,sourceRowsExact=True,runtimeOnlyPaired=True,fullExpectedKeySet=True,grade=dict(path=str(p),bytes=p.stat().st_size,sha256=rr.sha(p)),runtimeAssemblerArtifact=dict(path=str(out),sha256=rr.sha(out)),generatedAtUTC=ev.now()))
print('Paired grade assembled; local contract validation passed')
