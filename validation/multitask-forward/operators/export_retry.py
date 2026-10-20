#!/usr/bin/env python3
import importlib.util,json,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
export=Path(json.loads((R/'operators/export-audit/commands.json').read_text())['exportDirectory'])
spec=importlib.util.spec_from_file_location('inventory_retry',R/'artifacts.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
paths=set(subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().strip('\0').split('\0'))|set(a.enumerate_files())
for rel in sorted(paths):
 source=REPO/rel;target=export/rel
 if source.is_file()and(not target.is_file()or source.stat().st_mtime_ns!=target.stat().st_mtime_ns or source.stat().st_size!=target.stat().st_size):target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
out=R/'operators/export-audit-retry';out.mkdir();record={'startedAtUnix':time.time(),'exportDirectory':str(export),'commands':[],'scope':'Rerun repaired claims relocation and revised explanatory table against clean export; no source/grade/claim changes.'}
for i,name in enumerate(['verify_claims.py','build_supplement_tables.py'],1):
 row={'argv':[sys.executable,'-B',str(export/'validation/multitask-forward'/name)],'startedAtUnix':time.time(),'log':str((out/(str(i).zfill(2)+'.log')).relative_to(R))};record['commands'].append(row)
 with (R/row['log']).open('w')as f:row['exitCode']=subprocess.run(row['argv'],cwd=export,stdout=f,stderr=subprocess.STDOUT).returncode
 row['finishedAtUnix']=time.time();print(name,row['exitCode'],flush=True)
record['finishedAtUnix']=time.time();(out/'commands.json').write_text(json.dumps(record,indent=2)+'\n');assert all(x['exitCode']==0 for x in record['commands'])
