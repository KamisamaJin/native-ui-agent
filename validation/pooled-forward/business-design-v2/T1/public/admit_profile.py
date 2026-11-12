#!/usr/bin/env python3
"""External profile-admission check. It does not modify or extend frozen native tools."""
import argparse,hashlib,json
from pathlib import Path
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def verify(root,approval,approval_sha,platform,config):
    if digest(approval)!=approval_sha:raise ValueError('Approval manifest differs from externally pinned canonical digest')
    if platform not in approval['profiles']:raise ValueError('Unapproved platform')
    p=approval['profiles'][platform]
    for field in ('design_sha256','policy_sha256','routes_sha256','environment_sha256'):
        if config.get(field)!=p[field]:raise ValueError('Wrong approved '+field)
    for field in ('design_lock','plan','policy','routes','environment','fixtures','bridge'):
        actual=Path(config[field]).resolve();expected=(root/p['paths'][field]).resolve()
        if actual!=expected:raise ValueError('Wrong approved '+field+' path')
        data=actual.read_bytes();observed=hashlib.sha256(data).hexdigest() if field=='bridge' else digest(json.loads(data))
        if observed!=p['hashes'][field]:raise ValueError('Changed approved '+field+' bytes/content')
    plan=json.loads(Path(config['plan']).read_text())
    if plan['design_contract']['platform']!=platform or plan['design_contract']['lock_sha256']!=p['design_sha256']:raise ValueError('Plan/profile platform or lock mismatch')
    if config.get('launch_ref')!=p['launch_ref']:raise ValueError('Wrong sealed launch reference')
    return {'status':'admitted_profile','platform':platform,'design_sha256':p['design_sha256'],'plan_sha256':p['hashes']['plan'],'scope':'Only this intended-platform projection is approved. Opposite expression slots are schema-only, never runtime claims.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--approval',type=Path,required=True);p.add_argument('--approval-sha256',required=True);p.add_argument('--platform',choices=['ios','android'],required=True);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.root.resolve(),json.loads(a.approval.read_text()),a.approval_sha256,a.platform,json.loads(a.config.read_text()))))
if __name__=='__main__':main()
