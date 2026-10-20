import pathlib,subprocess,sys,time,json,datetime
P=pathlib.Path(__file__).resolve().parent
label=sys.argv[1];command=sys.argv[2:];start=time.time()
(P/'logs').mkdir(exist_ok=True)
with (P/'logs'/f'{label}.log').open('w') as f:
 r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
record={'command':command,'cwd':str(pathlib.Path.cwd()),'start_utc':datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),'wall_seconds':time.time()-start,'exit_code':r.returncode}
(P/'logs'/f'{label}.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
raise SystemExit(r.returncode)
