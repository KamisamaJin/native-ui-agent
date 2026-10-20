#!/usr/bin/env python3
"""Verify prospective frozen tools and their pre-business native validation."""
import ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):return {str(p.relative_to(root)):sha(p)for p in sorted(root.rglob('*'))if p.is_file()and '__pycache__'not in p.parts and p.name!='.DS_Store'}
def main():
 for tool in ['baseline-v5','candidate-v6']:
  freeze=read(R/(tool+'-freeze.json'));assert inventory(R/tool)==freeze['files']
 assert inventory(R/'baseline-v5')==inventory(REPO/'validation/state-forward/candidate-v5')
 live=inventory(REPO/'native-ui-agent');release=R/'RELEASE-BUNDLE.json'
 if release.exists():
  bundle=read(release);assert live==bundle['files'];expected=inventory(R/'candidate-v6');changed=sorted(k for k in live if live[k]!=expected[k]);assert changed==bundle['commonReleaseChanges']
  assert changed==['assets/ios-observer/CONTRACT.md','references/native-tools.md','scripts/ios_observe.py'];assert live['scripts/ios_observe.py']==sha(R/'runtime-candidate-v6/scripts/ios_observe.py');assert sha(R/'private/ASSIGNMENT-RELEASE.json')==bundle['assignmentReleaseSHA256']
 else:assert inventory(R/'candidate-v6')==live,'Live Skill changed after pre-business freeze'
 f=read(R/'candidate-v6-freeze.json');assert sha(R/'generic-summary.json')==f['rootGenericSummarySHA256']
 for name,key in [('FINAL-SUMMARY.md','independentSummarySHA256'),('FINAL-FREEZE.json','independentFinalFreezeSHA256'),('POST-FINAL-TRUST-GATE.json','independentTrustGateSHA256')]:assert sha(R/'independent-generic'/name)==f[key]
 independent=R/'independent-generic';assert sha(independent/'FINAL-SHA256SUMS.json')==read(independent/'FINAL-FREEZE.json')['file_inventory_sha256']
 for rel,h in read(independent/'FINAL-SHA256SUMS.json').items():assert sha(independent/rel)==h
 amendment=read(R/'COMMON-WIDTH-AMENDMENT.json')
 for tool,version in amendment['versions'].items():
  assert inventory(R/version['root'])==version['files'];assert [k for k,h in version['files'].items()if h!=inventory(R/tool)[k]]==['scripts/ios_observe.py']
 for rel,h in read(R/'generic-width/evidence/portable-sha256.json').items():assert sha(R/'generic-width/evidence'/rel)==h
 probe=read(R/'generic-width/RESULT.json');assert probe['native_test_count']==1 and probe['offered_widths']==[340]and probe['counts']=={'passed':15,'failed':0,'unassessed':12}
 assert sha(R/'PREREGISTRATION.md')==f['preregistrationSHA256']and sha(R/'OPERATIONS.md')==f['operationsSHA256']
 trees=[ast.parse((R/tool/'scripts/native_checks.py').read_text())for tool in ['baseline-v5','candidate-v6']]
 body=lambda t:ast.dump(next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='callback_verdict'),include_attributes=False)
 assert body(trees[0])==body(trees[1]),'Callback successful-dispatch gate changed'
 for records in read(R/'generic-runs.json').values():
  for command in records:assert command['finishedAtUnix']<f['frozenAtUnix']
 print('PASS: exact v5/v6 tools, unchanged callback gate, real pre-business controls and independent forward test')
if __name__=='__main__':main()
