#!/usr/bin/env python3
"""Run assigned typed checker after decoding the public bridge's JSON callback transport.

This never changes source observations, snapshots, native dispatch, bindings or frames.
The public API promises JSON dictionary values, not a dictionary serialization key order.
"""
import argparse, copy, hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--observation',type=Path,required=True);p.add_argument('--platform',choices=['android','ios'],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--manual',type=Path);p.add_argument('--root',type=Path);args=p.parse_args()
    checker=ROOT/'skill/scripts/native_checks.py'
    spec=importlib.util.spec_from_file_location('assigned_native_checks',checker);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    raw=json.loads(args.observation.read_text());observed=copy.deepcopy(raw);normalizations=[]
    for index,step in enumerate(observed.get('steps',[])):
        delta=step.get('callback_delta')
        if not isinstance(delta,list):continue
        for receipt_index,receipt in enumerate(delta):
            event=receipt.get('event') if isinstance(receipt,dict) else receipt
            if not isinstance(event,str):continue
            try:decoded=json.loads(event)
            except (ValueError,TypeError):continue
            # Only the exact public envelope is decoded. Invalid or extra transport stays raw.
            if not isinstance(decoded,dict) or set(decoded)!={'name','payload'} or not isinstance(decoded['name'],str) or not isinstance(decoded['payload'],dict):continue
            if isinstance(receipt,dict):receipt['event']=decoded
            else:delta[receipt_index]={'event':decoded}
            normalizations.append({'action_index':index,'receipt_index':receipt_index,'raw_event':event,'decoded_event':decoded})
    manual=json.loads(args.manual.read_text()) if args.manual else None
    report=native.evaluate(json.loads(args.plan.read_text()),observed,args.platform,manual,args.root or args.observation.parent,sha(args.observation))
    report['input_hashes']={'plan':sha(args.plan),'observation':sha(args.observation),'assigned_checker':sha(checker),'review_wrapper':sha(Path(__file__))}
    if args.manual:report['input_hashes']['manual']=sha(args.manual)
    report['callback_transport_normalization']={'rule':'JSON-decode name/payload envelope only; retain all original native dispatch, binding and interval gates. Original observation file untouched.','records':normalizations}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'counts':report['counts'],'decoded_receipts':len(normalizations)}))
    raise SystemExit(1 if report['counts']['failed'] else 3 if report['counts']['unassessed'] else 0)
if __name__=='__main__':main()
