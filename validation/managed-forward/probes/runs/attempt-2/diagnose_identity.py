#!/usr/bin/env python3
"""Read-only identity comparison on one newly owned generic probe launcher."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import run_resources as probe

r=probe.Row('diagnostic-only','launcher-identity-comparison')
try:
    r.start('tree-hang')
    ready=r.tree_ready()
    comparison={'actual_tree_ready':ready,'not_a_new_sealed_case':True}
    if ready:
        journal=probe.load(r.root/'journal.json')
        row=journal['process'];actual=subprocess.run(['ps','-ww','-p',str(row['pid']),'-o','lstart=','-o','pgid=','-o','command='],text=True,capture_output=True)
        comparison.update(journal_process=row,actual_raw=actual.stdout.strip(),identity_exact_match=actual.stdout.strip()==row['identity'],token_in_actual=row['token'] in actual.stdout)
        probe.dump(r.raw/'read-only-identity-comparison.json',comparison)
    if r.worker.poll() is None:os.kill(r.worker.pid,signal.SIGTERM)
    r.wait()
    r.finish('U','Read-only diagnostic only; not an additional sealed score row',comparison)
finally:
    pass
