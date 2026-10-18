import subprocess,json,datetime,pathlib,sys
platform=sys.argv[1]
project="reply/Reply" if platform=="android" else "alerttoast"
records=[]
for name in ["expanded","narrow-rtl-accessibility","empty","edge-progress"]:
 output=f"self-review/{platform}/{name}"
 log=pathlib.Path(f"self-review/{platform}-{name}.log")
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with log.open("w") as stream:
  result=subprocess.run(["python3","capture.py","--platform",platform,"--project",project,"--fixture",f"self-review/{name}.json","--output",output],stdout=stream,stderr=subprocess.STDOUT)
 records.append({"case":name,"output":output,"log":str(log),"exit_code":result.returncode,"started_at":start,"completed_at":datetime.datetime.now(datetime.timezone.utc).isoformat()})
 pathlib.Path(f"self-review/{platform}-runs.json").write_text(json.dumps(records,indent=2)+"\n")
 print(json.dumps(records[-1]),flush=True)
