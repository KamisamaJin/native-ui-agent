#!/usr/bin/env python3
"""Post-verdict cleanup of exact recorded fixture identities, never native devices."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE=Path(__file__).resolve().parent
def state(pid):
    p=subprocess.run(['ps','-p',str(pid),'-o','lstart=','-o','pgid=','-o','stat=','-o','command='],text=True,capture_output=True)
    return p.stdout.strip() if p.returncode==0 else None
rows=[]
for path in sorted((HERE/'cache').rglob('processes.jsonl')):
    for line in path.read_text().splitlines():
        try:record=json.loads(line)
        except json.JSONDecodeError:continue
        current=state(record['pid'])
        row={'record_path':str(path),'record':record,'actual_before':current,'post_verdict_harness_only':True}
        if current and record['token'] in current and str(HERE/'fixture_process.py') in current:
            try:os.kill(record['pid'],signal.SIGTERM)
            except ProcessLookupError:pass
            time.sleep(.1)
            again=state(record['pid'])
            if again and record['token'] in again and str(HERE/'fixture_process.py') in again:
                try:os.kill(record['pid'],signal.SIGKILL)
                except ProcessLookupError:pass
            row['action']='reclaim exact remaining probe fixture after immutable verdict'
        else:row['action']='no live matching fixture; no signal'
        row['actual_after']=state(record['pid']);rows.append(row)
out=HERE/'post-verdict-fixture-teardown.json';trial=1
while out.exists():
    trial+=1;out=HERE/('post-verdict-fixture-teardown-'+str(trial)+'.json')
out.write_text(json.dumps({'scope':'exact record PID plus random argv token plus fixture path; no global process enumeration','rows':rows},indent=2)+'\n')
print(json.dumps({'recorded_identities_checked':len(rows),'post_verdict_reclaims':sum(r['action'].startswith('reclaim') for r in rows)}))
