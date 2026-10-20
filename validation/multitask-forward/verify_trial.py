#!/usr/bin/env python3
"""SDK-free exact source, native evidence and whole-cohort temporal audit."""
import json
from pathlib import Path
import experiment as ex
import costs
R=Path(__file__).resolve().parent

def check(root,files):
 for rel,h in files.items():assert ex.sha(root/rel)==h,(root,rel)
def local(path):
 p=Path(path);marker='/validation/multitask-forward/'
 return R/str(path).split(marker,1)[1]if marker in str(path)else p

def main():
 config=ex.read(R/'gates/config.json');proofs={s:ex.gate.verify(R/'gates',s,R)for s in config['stages']};assignment=ex.read(R/'private/assignment.json');units=assignment['units'];caps={}
 for directory in ['design',ex.read(R/'DESIGN-ROOT.json')['directory']]:
  d=R/directory;cohort=ex.read(d/'COHORT-SEAL.json');check(d,cohort['files'])
  for task in ['T1','T2','T3']:check(d,ex.read(d/task/'SEAL.json')['files'])
 d=R/ex.read(R/'DESIGN-ROOT.json')['directory'];pristine=ex.read(R/'operators/pristine-source.json')
 assert len({json.dumps(v,sort_keys=True)for v in pristine['units'].values()})==1
 for unit,data in units.items():
  base=R/'submissions'/unit
  for phase in ['d0','final']:
   cap=base/phase;seal=ex.read(cap/'seal.json');check(cap/'source',seal['files']);check(cap,seal['upstreamLicenses']);assert set(seal['files'])=={str(p.relative_to(cap/'source'))for p in(cap/'source').rglob('*')if p.is_file()};caps[unit,phase]=seal
   assert all(seal['files'].get(rel)==h for rel,h in pristine['units'][unit].items()),(unit,phase,'Existing upstream production code changed')
   assert len(set(seal['files'])-set(pristine['units'][unit]))==2,(unit,phase,'Expected exactly one new component per platform')
  for name,folder,limit,gate in [('implementation','initial-agent-output',1500,'design'),('review','original-review',720,'own-d0'),('repair','final-agent-output',900,'reviews')]:
   row=costs.phase(ex.read(base/folder/(name+'.json')));assert row['wallSeconds']<=limit,(unit,name,row);assert row['startedAtUnix']>=proofs[gate]['sealedAtUnix'],(unit,name,'early phase')
   endpoint={'implementation':caps[unit,'d0']['sealedAtUnix'],'review':ex.read(base/'review-submission.json')['submittedAtUnix'],'repair':caps[unit,'final']['sealedAtUnix']}[name]
   assert row['finishedAtUnix']<=endpoint,(unit,name,'phase ended after its immutable submission')
  public=d/data['task']/'public';lock=ex.read(public/'design-lock.json');digest=ex.read(public/'approval.json')['design_lock_sha256']
  import sys;sys.path.insert(0,str(R/'candidate-v7/scripts'));import design_contract
  for case in ['P1','P2']:
   for platform in ['ios','android']:design_contract.verify_generated(ex.read(base/'initial-agent-output/plans'/case/platform/'plan.json'),lock,digest,platform)
 record=ex.read(R/'operators/metrics-implementation-record.json');check(R,record['files']);assert record['recordedAtUnix']<=proofs['grade-d0']['sealedAtUnix']
 for stage,gate,prior in [('D0','grade-d0','own-final'),('FINAL','grade-final','grade-d0'),('selfreview','grade-selfreview','grade-final'),('paired-D0','grade-pair','grade-selfreview')]:
  delivery=ex.read(R/'evaluation-inputs'/stage/'DELIVERY-SEAL.json')
  for task in ['T1','T2','T3']:
   folder=R/'evaluation'/stage/task;clock=costs.phase(ex.read(folder/'phase.json'));sealed=ex.read(folder/'SEAL.json')['sealedAtUnix']
   assert clock['startedAtUnix']>=max(delivery['sealedAtUnix'],proofs[prior]['sealedAtUnix']),(stage,task,'Independent phase started before complete upstream delivery')
   assert clock['finishedAtUnix']<=sealed<=proofs[gate]['sealedAtUnix'],(stage,task,'Independent phase ended after seal')
 registry=[]
 for unit,data in units.items():
  for phase in ['d0','final']:registry.append((R/'own-corpora'/unit/phase,unit,phase,data['tool'],4))
 for task,aliases in assignment['gradeAliases'].items():
  for alias,unit in aliases.items():
   for phase,n in [('d0',4),('final',6)]:registry.append((R/'common-corpora'/task/alias/phase,unit,phase,'candidate-v7',n))
   registry.append((R/'paired-corpora'/task/alias/'v6',unit,'d0','baseline-v6',4))
 commands=nonzero=frames=native_tests=0
 for path,unit,phase,tool,count in registry:
  check(path,ex.read(path/'portable-sha256.json'));seal=ex.read(path/'corpus-seal.json');assert seal['portableManifestSHA256']==ex.sha(path/'portable-sha256.json');c=ex.read(path/'corpus.json');start=ex.read(path/'started.json');assert c['source']==start['source']==seal['source']==caps[unit,phase]['files'];assert c['tool']==tool
  required=c['requiredStage'];assert start['startedAtUnix']>=proofs[required]['sealedAtUnix'];assert start['operatorSHA256']==ex.sha(path/'operator-source.py')
  runs=[(platform,row)for platform,rows in c['platformRuns'].items()for row in rows];assert len(runs)==count
  for platform,row in runs:
   commands+=1;nonzero+=row['exitCode']!=0;receipt=row['authorization'];assert receipt['requiredStage']==required and receipt['stageSealSHA256']==ex.sha(R/'gates'/(required+'.json'));assert proofs[required]['sealedAtUnix']<=receipt['authorizedAtUnix']<=row['startedAtUnix'];assert row['sourceSealSHA256']==ex.sha(R/'submissions'/unit/phase/'seal.json')
   assert row['startedAtUnix']>=caps[unit,phase]['sealedAtUnix'];assert abs(row['wallSeconds']-(row['finishedAtUnix']-row['startedAtUnix']))<1e-6
   for kind in ['fixtures.json','actions.json','bridge']:
    flag={'fixtures.json':'--fixtures','actions.json':'--actions','bridge':'--bridge'}[kind];p=local(row['argv'][row['argv'].index(flag)+1]);assert ex.sha(p)==row['inputHashes'][kind]
   raw=path/platform/row['case'];mp=raw/'manifest.json';op=raw/'observation.json'
   if mp.is_file():native_tests+=ex.read(mp).get('native_test_count',0)
   if op.is_file():frames+=len(ex.read(op)['snapshots'])
   if row['exitCode']==0:assert mp.is_file()and ex.read(mp).get('native_test_count',0)>0 and op.is_file(),'No SDK success without real native test/evidence'
  assert seal['sealedAtUnix']>=c['finishedAtUnix']
 release=ex.read(R/'private/ASSIGNMENT-RELEASE.json');assert release['releasedAtUnix']>=proofs['grade-pair']['sealedAtUnix'];assert release['gradeAliases']==assignment['gradeAliases']
 supplement=ex.gate.verify(R/'shared-environment-v1/gates','graded',R);assert release['releasedAtUnix']>=supplement['sealedAtUnix'],'Assignment released before all posthoc task outputs sealed'
 for task in ['T1','T2','T3']:
  folder=R/'supplement'/task;clock=costs.phase(ex.read(folder/'phase.json'));sealed=ex.read(folder/'SEAL.json')['sealedAtUnix'];assert clock['startedAtUnix']>=proofs['grade-pair']['sealedAtUnix'];assert clock['finishedAtUnix']<=sealed<=supplement['sealedAtUnix']
 # Actual acquisition occupancy, including the original pre-lock batch, must
 # respect the shared two-unit cap; iOS/Android within a unit may overlap.
 intervals=[]
 for p in sorted((R/'operators').glob('*-unit-*.json')):
  row=ex.read(p)
  if 'phase'in row and 'finishedAtUnix'in row:intervals += [(row['startedAtUnix'],1),(row['finishedAtUnix'],-1)]
 active=peak=0
 for _,delta in sorted(intervals,key=lambda x:(x[0],x[1])):active+=delta;peak=max(peak,active);assert active<=2,'Shared native slot cap exceeded'
 assert active==0
 early=ex.read(R/'operators/actual-wrapper-early-launch.json');assert early['blockedBeforeSDK']and not early['outputExists']
 print(json.dumps({'status':'PASS','wholeCohortStages':len(proofs),'plannedCandidateNativeCommands':commands,'actualNativeTests':native_tests,'nonzeroNativeExits':nonzero,'snapshots':frames,'peakNativeUnits':peak,'originalRejectedDesignPreserved':True}))
if __name__=='__main__':main()
