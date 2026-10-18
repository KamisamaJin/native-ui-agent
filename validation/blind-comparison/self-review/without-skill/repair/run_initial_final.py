import pathlib,subprocess,sys,datetime,json
platform=sys.argv[1];records=[]
project='reply/Reply' if platform=='android' else 'alerttoast'
for index in range(1,7):
 case=f'I{index:02d}';out=f'repair/final-v2/{platform}/{case}';log=f'repair/final-v2-{platform}-{case}.log'
 with pathlib.Path(log).open('w') as stream:
  result=subprocess.run(['python3','capture.py','--platform',platform,'--project',project,'--fixture',f'feedback/initial-inputs/{case}-input.json','--output',out],stdout=stream,stderr=subprocess.STDOUT)
 records.append({'case':case,'output':out,'log':log,'exit_code':result.returncode,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 pathlib.Path(f'repair/final-v2-{platform}-runs.json').write_text(json.dumps(records,indent=2)+'\n')
 print(json.dumps(records[-1]),flush=True)
