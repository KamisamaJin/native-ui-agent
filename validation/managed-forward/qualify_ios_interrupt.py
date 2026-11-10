#!/usr/bin/env python3
"""Interrupt a real, journaled iOS XCTest, then independently check retirement.

The trigger is a real XCTest image-attachment acknowledgement plus a live owned
xcodebuild group. No decoded in-flight image or product acceptance is claimed.
SIGKILL recovery is performed only by the frozen resource-manager cleanup entry.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from qualify_cancel import group_members

R=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def after_device(uid):
    argv=['xcrun','simctl','list','devices','--json']
    result=subprocess.run(argv,env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer'),
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
    if result.returncode:raise RuntimeError(result.stderr)
    data=json.loads(result.stdout)
    return {'at_unix':time.time(),'argv':argv,'exit_code':result.returncode,
            'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),
            'target_rows':[{'runtime':runtime,**device}for runtime,rows in data['devices'].items()for device in rows if device['udid']==uid],
            'data_path_exists':(Path.home()/'Library/Developer/CoreSimulator/Devices'/uid).exists()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--mode',choices=['term','kill_reconcile'],required=True)
    parser.add_argument('--name',required=True)
    args=parser.parse_args()
    if Path(args.name).name!=args.name:raise ValueError('One fresh case name required')
    record_root=R/'operators'/args.name;record_root.mkdir(parents=True,exist_ok=False)
    output=R/'cache'/args.name;assert not output.exists()
    config=json.loads(args.config.read_text());config['resources']['root']=str(R/'cache'/(args.name+'-resources'))
    configuration=record_root/'config.json';configuration.write_text(json.dumps(config,indent=2)+'\n')
    journal=Path(config['resources']['root'])/'journal.json'
    sources=[Path(p)for p in config['source_roots']]
    before={str(p):sha(p)for p in sources}
    argv=[sys.executable,'-B',str(args.candidate.resolve()/'scripts/ui_loop.py'),'native',
          '--config',str(configuration),'--output',str(output),'--final']
    row={'mode':args.mode,'argv':argv,'started_at_unix':time.time(),'config_sha256':sha(configuration),
         'source_hashes_before':before,'precondition_wait_seconds':180,'exit_wait_seconds':180,
         'reconcile_command_timeout_seconds':180,'scope':__doc__}
    process=None;qualified=False
    try:
        with (record_root/'controller.log').open('x')as log:
            process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
            deadline=time.monotonic()+180
            while process.poll()is None and time.monotonic()<deadline:
                test_log=output/'capture/native/test.log'
                try:
                    content=test_log.read_text(errors='replace')if test_log.is_file()else''
                    state=json.loads(journal.read_text())if journal.is_file()else{}
                    owner=state.get('process',{});devices=state.get('devices',[])
                    members=group_members(owner['pgid'])if owner else[]
                    if (re.search(r"Added attachment named '[^']+\.png'",content)and
                            any(p['executable']=='xcodebuild'for p in members)and len(devices)==1):
                        (record_root/'pre-interrupt-test.log').write_bytes(test_log.read_bytes())
                        row.update(sdk_receipt_before=owner,device_before=devices[0],group_before=members,
                                   first_attachment_acknowledged=True,in_flight_image_decoded=False)
                        qualified=True;break
                except (ValueError,OSError,KeyError):pass
                time.sleep(.02)
            row['interruption_precondition_established']=qualified
            if process.poll()is None:
                row['signal_at_unix']=time.time()
                row['signal']=int(signal.SIGTERM if args.mode=='term'else signal.SIGKILL)
                process.send_signal(row['signal'])
            row['outer_exit_code']=process.wait(timeout=180)
        if qualified:
            group=row['sdk_receipt_before']['pgid'];row['after_outer_exit_group']=group_members(group)
            if args.mode=='kill_reconcile':
                recovery=[sys.executable,'-B',str(args.candidate.resolve()/'scripts/resource_manager.py'),
                          'cleanup','--config',str(configuration),'--output',str(record_root/'reconcile')]
                row['reconcile_started_at_unix']=time.time()
                with (record_root/'reconcile.log').open('x')as log:
                    result=subprocess.run(recovery,stdout=log,stderr=subprocess.STDOUT,timeout=180)
                row['reconcile_argv']=recovery;row['reconcile_exit_code']=result.returncode
                receipt_root=record_root/'reconcile'
                assert result.returncode==0
            else:receipt_root=output
            row['after_recovery_group']=group_members(group)
            row['device_after']=after_device(row['device_before']['udid'])
            row['resources']=json.loads((receipt_root/'resources.json').read_text())
            assert not row['after_recovery_group']and not row['device_after']['target_rows']and not row['device_after']['data_path_exists']
            assert not row['resources']['cleanup_errors']and not row['resources']['remaining_devices']and not row['resources']['remaining_directories']
        row['source_hashes_after']={str(p):sha(p)for p in sources}
        row['cycle_published']=(output/'cycle.json').exists()
        assert qualified and row['outer_exit_code']!=0 and not row['cycle_published']
        assert row['source_hashes_before']==row['source_hashes_after']
        row['status']='PASS'
    except BaseException as error:
        row['status']='not_qualified';row['error']={'type':type(error).__name__,'message':str(error)}
        # No harness process-group/device cleanup to manufacture a tool pass.
        # Any unresolved state remains for explicit, journaled recovery.
    finally:
        row['finished_at_unix']=time.time()
        (record_root/'result.json').write_text(json.dumps(row,indent=2)+'\n')
    print(json.dumps({key:row.get(key)for key in ['mode','status','outer_exit_code','error','interruption_precondition_established']}))
    return 0 if row['status']=='PASS'else 1


if __name__=='__main__':raise SystemExit(main())
