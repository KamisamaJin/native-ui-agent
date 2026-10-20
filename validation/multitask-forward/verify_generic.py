#!/usr/bin/env python3
"""SDK-free replay of actual neutral native geometry evidence and barriers."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');a=parser.parse_args()
    sys.path.insert(0,str(REPO/'native-ui-agent/scripts'));import native_checks,cohort_gate
    cohort_gate.verify(R/'generic-v2/gates','sources',R)
    result=[]
    for row in read(R/'generic-runs-v2.json'):
        platform,case,tool=(row[k]for k in ['platform','case','tool']);key='v2-'+platform+'-'+case+'-'+tool;root=R/'generic-evidence-v2'/key
        assert row['exitCode']==0
        for rel,h in read(root/'portable-sha256.json').items():assert sha(root/rel)==h,rel
        obs=read(root/'observation.json');native_count=read(root/'manifest.json')['native_test_count'];assert native_count>0
        plan=read(R/'generic-v2'/case/('plan.'+platform+'.json'))
        # Candidate metrology applies identically to legacy data: packets absent
        # must retain strict legacy semantics and cannot acquire precision credit.
        report=native_checks.evaluate(plan,obs,platform,root=root)
        witness_matches=0
        if platform=='android'and tool=='candidate-v7':
            witnesses={tuple(line.split('|')[0:1]+line.split('|')[3:6])for line in(root/'layout-witness.txt').read_text().splitlines()}
            for snap in obs['snapshots']:
                for node in snap['nodes']:
                    if node.get('identifier')not in ['neutral.primary','neutral.secondary','neutral.footer']:continue
                    g=node['native_geometry'];sample=(node['identifier'],str(g['size_px'][0]),str(g['size_px'][1]),str(g['density']))
                    assert sample in witnesses,('native layout witness mismatch',sample);witness_matches+=1
            assert witness_matches>0
            for item in report['assertions']:
                if 'geometry_evidence'in item:
                    for proof in item['geometry_evidence']:assert 'ratio'in proof
        if platform=='android'and tool=='baseline-v6':assert not any(n.get('native_geometry')for s in obs['snapshots']for n in s['nodes'])
        result.append({'platform':platform,'case':case,'tool':tool,'counts':report['counts'],'nativeTests':native_count,'witnessMatches':witness_matches,'assertions':report['assertions']})
    assert len(result)==8
    original=read(R/'generic-runs.json');assert len(original)==8 and all(r['exitCode']!=0 for r in original)
    for r in original:
        log=R/'operators'/('-'.join([r['platform'],r['case'],r['tool']])+'.log')
        assert 'initial/final are reserved'in log.read_text()
    refused=read(R/'operators/early-launch-refused-v2.json');assert not refused['nativeCommandStarted']
    value={'actualNativeCommands':8,'preservedPreNativeCallerFailures':8,'results':result,'scope':'Neutral controls only; not natural product defects. Android packet extents cross-checked against independent onGloballyPositioned layout receipts.'}
    target=R/'generic-summary.json'
    if a.write:
        assert not target.exists();target.write_text(json.dumps(value,indent=2)+'\n')
    else:assert read(target)==value
    print(json.dumps({'status':'PASS','actualNativeCommands':8,'rows':[dict((k,v)for k,v in row.items()if k!='assertions')for row in result]}))
if __name__=='__main__':main()
