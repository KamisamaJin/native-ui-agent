#!/usr/bin/env python3
"""Read-only closed-study integrity replay; no SDK and no judgment changes."""
import argparse,json,subprocess,sys
from pathlib import Path
import study as s
R=s.R

def run(script,*args):return subprocess.check_output([sys.executable,'-B',str(R/'run_operation.py'),str(R/script),*args],cwd=s.REPO)
def main():
 p=argparse.ArgumentParser();p.add_argument('--tracked',action='store_true');p.add_argument('--pretrial',action='store_true');a=p.parse_args()
 s.tool_verify();assert s.table(s.REPO/'native-ui-agent')==s.table(R/'candidate-v11')
 subprocess.run([sys.executable,'-B',str(R/'design/verify_design.py')],check=True,stdout=subprocess.DEVNULL)
 assert run('benchmark_results.py')==(R/'benchmark-results.json').read_bytes()
 if a.pretrial:
  sys.stdout.buffer.write(run('verify_native.py'));print('PASS frozen tools, approved-design bytes, complete same-code benchmark and original actuals');return
 s.gate.authorize(R/'gates-v1','d0-raw',R) # Original pre-SDK failure registry remains independently verifiable.
 assert s.read(R/'gates-v1/design-approved.json')['sealedAtUnix']<s.read(R/'operators/author-start.json')['dispatchedAtUnix']
 assert s.read(R/'RELEASE.json')['releasedAtUnix']<s.read(R/'design-v1/SEAL.json')['sealedAtUnix']
 for stage in ['design-approved','initial-source','d0-raw','all-self-closed','hidden','quality-inputs','quality-panels','revealed']:s.gate.authorize(R/'gates',stage,R)
 approved=s.read(R/'design/public/approval.json');allowed={('alerttoast/'if pl=='ios'else'reply/Reply/')+rel for pl,rows in approved['production_paths'].items()for rel in rows};stock=s.read(R/'operators/stock-production.json')['files'];initial=s.read(R/'submissions/initial/seal.json')['files']
 assert {k for k in set(stock)|set(initial)if stock.get(k)!=initial.get(k)}==allowed
 assignment=s.read(R/'private/assignment.json')['units']
 for unit in assignment:
  assert s.read(R/'submissions'/unit/'initial/seal.json')['files']==initial
 for seal in sorted((R/'submissions').rglob('seal.json')):
  if not(seal.parent/'source').exists():continue
  files={str(v.relative_to(seal.parent/'source')):s.sha(v)for v in(seal.parent/'source').rglob('*')if v.is_file()};assert files==s.read(seal)['files'],str(seal)
  assert {k for k in set(initial)|set(files)if initial.get(k)!=files.get(k)}<=allowed,str(seal)
 for script in ['verify_native.py','verify_quality.py','verify_adjudication.py','verify_calibration.py']:sys.stdout.buffer.write(run(script))
 for script,name in [('costs.py','costs.json'),('derive_results.py','results.json'),('execution_audit.py','execution-audit.json')]:assert run(script)==(R/name).read_bytes(),name
 sys.stdout.buffer.write(run('build_docs.py','--check'))
 sys.stdout.buffer.write(run('artifacts.py',*(['--tracked']if a.tracked else[])))
 print('PASS literal source, blind barriers, original native/review/quality actuals, final metrics and publication bytes')
if __name__=='__main__':main()
