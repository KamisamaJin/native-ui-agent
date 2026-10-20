#!/usr/bin/env python3
"""Post-reveal byte identity and actual proof adoption, without quality inference."""
import argparse,difflib,json
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def build():
 ex.gate.verify(R/'gates','reveal',R);a=ex.read(R/'private/assignment.json');tasks={}
 for task,aliases in a['gradeAliases'].items():
  bytool={a['units'][unit]['tool']:unit for unit in aliases.values()};v={}
  for phase in ['d0','final']:
   caps={k:R/'submissions'/u/phase for k,u in bytool.items()};files={k:ex.read(p/'seal.json')['files']for k,p in caps.items()};assert set(files['baseline-v6'])==set(files['candidate-v7'])
   pristine=ex.read(R/'operators/pristine-source.json')['units'][bytool['baseline-v6']];added=sorted(set(files['baseline-v6'])-set(pristine));rows=[]
   for rel in added:
    aa,bb=[(caps[k]/'source'/rel).read_text()for k in ['baseline-v6','candidate-v7']];rows.append({'path':rel,'baselineSHA256':files['baseline-v6'][rel],'candidateSHA256':files['candidate-v7'][rel],'byteIdentical':aa==bb,'lineSimilarityDiagnostic':difflib.SequenceMatcher(a=aa.splitlines(),b=bb.splitlines(),autojunk=False).ratio()})
   v[phase]={'newComponents':rows,'originalUpstreamFilesUnchanged':all(files[k].get(p)==h for k in files for p,h in pristine.items())}
  adoption={}
  for tool,u in bytool.items():
   reports=sorted((R/'submissions'/u/'own-checks/d0').glob('*/*/report.json'));assert len(reports)==4;proof=assertions=0
   for p in reports:
    d=ex.read(p)
    if not isinstance(d,dict)or'assertions'not in d:continue
    assertions+=len(d['assertions']);proof+=sum(bool(x.get('geometry_evidence')) for x in d['assertions'])
   adoption[tool]={'reportPaths':[str(p.relative_to(R))for p in reports],'assertionRowsScanned':assertions,'rowsWithGeometryEvidence':proof}
  v['proofAdoptionDiagnostic']=adoption;tasks[task]=v
 return {'tasks':tasks,'scope':'Byte identity and line-similarity diagnostics only, not independent defect counts or causal evidence. Both arms received the same approved public API/reference and already had contract generation. Original own report paths are listed; geometry-evidence field presence is a diagnostic, not a completeness claim.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();out=R/'implementation-comparison.json'
 if a.write:assert not out.exists();ex.save(out,v)
 else:assert ex.read(out)==v
 print('PASS: post-reveal source identity/proof adoption diagnostic')
if __name__=='__main__':main()
