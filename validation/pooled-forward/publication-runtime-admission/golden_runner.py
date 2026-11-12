"""Replay fixed historical synthetic bytes on a separately pinned new runtime."""
import argparse
import json
from pathlib import Path

import fixture_utils as fx
import replay as rp


GOLDEN_SHA='60fc5c6ebb2fd8697636a6b0c3ff7e9d4e01b9c675f07d4de8b1d999bd50b9a9'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--golden',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    raw=(args.golden/'MANIFEST.json').read_bytes();rp.need(rp.sha(raw)==GOLDEN_SHA,'Fixed historical generic manifest changed')
    manifest=rp.strict_json(raw);rp.need(manifest['data_scope']=='synthetic-host-only','Only fixed generic synthetic evidence may qualify a runtime')
    outputs=[]
    for backend in ['A','B']:
        reader=fx.Reader(args.output/('originals-'+backend))
        for row in manifest['data_files']:
            raw=(args.golden/row['relative']).read_bytes();rp.need(rp.sha(raw)==row['sha256'] and len(raw)==row['bytes'],'Golden original bytes changed')
            reader.put(row['original_key'],raw)
        row=manifest['packets'][backend];raw=(args.golden/row['relative']).read_bytes()
        rp.need(rp.sha(raw)==row['sha256'] and len(raw)==row['bytes'],'Golden backend packet changed')
        packet=reader.put(row['original_key'],raw);inventory,worker=fx.code_refs();result=rp.replay(reader,packet,inventory,worker)
        rp.need(result['status']=='verified','New runtime could not reproduce fixed generic evidence: '+str(result.get('error')))
        for role,original in manifest['expected_artifacts'].items():
            expected=reader.read_json(original)
            if role=='catalog' and 'catalog_sha256' in expected:
                value={k:v for k,v in expected.items() if k!='catalog_sha256'};rp.need(rp.digest(value)==expected['catalog_sha256'],'Golden catalog self-pin changed');expected=value
            rp.need(result['backend_results'][role]==expected,'New runtime changed fixed historical '+role+' evidence')
        rp.need(result['backend_results']['report']['counts']==manifest['expected_counts'],'Fixed six-assertion expected counts changed')
        rp.need(result['source_responsibility_replay']=='unsupported' and result['current_source_delivery_verified'] is False,'Unsupported boundaries were weakened')
        outputs.append({'backend':backend,'status':'exact_fixed_evidence_match','packet':packet,'comparisons':['catalog','manual','report'],
                        'counts':result['backend_results']['report']['counts'],'unsupported_boundaries_preserved':True})
    value={'version':1,'kind':'current-runtime-fixed-historical-generic-evidence-result','status':'verified','golden_manifest_sha256':GOLDEN_SHA,
           'backends':outputs,'actual_study_data_used':False,'scope':'Only the fixed historical generic fixture; not arbitrary data, source-domain, source responsibility or delivery admission.'}
    path=args.output/'RESULT.json';path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'path':str(path),'sha256':rp.sha(path.read_bytes()),'status':'verified'}))


if __name__=='__main__':main()
