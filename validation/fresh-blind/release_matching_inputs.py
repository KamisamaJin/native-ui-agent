#!/usr/bin/env python3
"""Release complete findings only after all independent final grades are sealed."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 seals=read(R/'final-grade-seals.json')['files'];assert len(seals)==6
 for path,h in seals.items():
  p=R/path;assert sha(p)==h and read(p)['sealedAtUTC'] and read(p)['blinding']['armMappingUnknown']
 output=R/'matching-inputs';output.mkdir(exist_ok=False);receipt={}
 for source in sorted((R/'phase-reports').glob('submission-*/readonly-review/reports/self-review.json')):
  sub=source.parents[2].name;raw=read(source);assert isinstance(raw['findings'],list)
  value={'submission':sub,'sourceReportSha256':sha(source),'findings':raw['findings']};target=output/(sub+'.json');target.write_text(json.dumps(value,indent=2)+'\n')
  assert read(target)['findings']==raw['findings'];receipt[sub]={'sourceReport':str(source.relative_to(R)),'sourceReportSha256':sha(source),'findingCopy':str(target.relative_to(R)),'findingCopySha256':sha(target)}
 assert len(receipt)==3
 (output/'release-receipt.json').write_text(json.dumps({'releasedAtUTC':datetime.now(timezone.utc).isoformat(),'allFinalGradesSealed':True,'sourceFinalGradeSealsSha256':sha(R/'final-grade-seals.json'),'submissions':receipt,'scope':'Complete finding arrays verbatim; workflow/timing metadata omitted, originals preserved. Contents may still suggest a workflow; procedural blindness only.'},indent=2)+'\n');print('Released three complete finding-only copies after final scoring seals')
if __name__=='__main__':main()
