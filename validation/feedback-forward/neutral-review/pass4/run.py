import sys,subprocess,json,time,shlex
from pathlib import Path
root=Path(__file__).resolve().parent
label=sys.argv[1]
argv=sys.argv[2:]
start=time.time()
p=subprocess.run(argv,capture_output=True,text=True,env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'})
end=time.time()
(root/'commands').mkdir(exist_ok=True)
record={'label':label,'argv':argv,'command':shlex.join(argv),'startedAtUnix':start,'endedAtUnix':end,'elapsedSeconds':end-start,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
(root/'commands'/f'{label}.json').write_text(json.dumps(record,indent=2)+'\n')
(root/'commands'/f'{label}.stdout.txt').write_text(p.stdout)
(root/'commands'/f'{label}.stderr.txt').write_text(p.stderr)
print(json.dumps({k:record[k] for k in ['label','startedAtUnix','endedAtUnix','elapsedSeconds','exit_code']},indent=2))
print(p.stdout[:28000])
if len(p.stdout)>28000: print('DISPLAY TRUNCATED; complete stdout retained in commands/'+label+'.stdout.txt')
if p.stderr: print('STDERR: '+p.stderr[:12000])
