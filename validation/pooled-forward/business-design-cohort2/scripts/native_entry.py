#!/usr/bin/env python3
"""Mandatory guarded external entry for a later authorized, source-bound native run.

Never invoked during business-design authoring. SDK work remains forbidden until
all-five design sealing and independent design review have both completed.
"""
import argparse, subprocess, sys
from pathlib import Path
from admit_profile import load, verify

def main():
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--approval',type=Path,required=True);a.add_argument('--approval-sha256',required=True);a.add_argument('--platform',choices=['ios','android'],required=True);a.add_argument('--profile-id',required=True);a.add_argument('--config',type=Path,required=True);a.add_argument('--review-receipt',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--final',action='store_true');v=a.parse_args()
    root=v.root.resolve();approval=load(v.approval);config=load(v.config)
    verify(root,approval,v.approval_sha256,v.platform,v.profile_id,config,runtime=True)
    review=load(v.review_receipt)
    if review.get('cohort_seal_sha256')!=load(root/'SEAL-IDENTITY.json')['seal_file_sha256'] or review.get('scope')!='all-five-preimplementation-design' or review.get('decision')!='admit':raise ValueError('Independent all-five design review receipt required before native work')
    frozen=root.parents[0]/'candidate-v13.9/scripts'
    sys.dont_write_bytecode=True;sys.path.insert(0,str(frozen))
    import design_contract as d
    import evidence_responsibility as er
    compiled=er.compile_contract(config,d.load(Path(config['plan'])),d.load(Path(config['design_lock'])))
    if compiled['issues']:raise ValueError('Actual source responsibility capability is unsupported')
    argv=[sys.executable,'-B',str(frozen/'ui_loop.py'),'native','--config',str(v.config),'--output',str(v.output)]
    if v.final:argv.append('--final')
    raise SystemExit(subprocess.call(argv))
if __name__=='__main__':main()
