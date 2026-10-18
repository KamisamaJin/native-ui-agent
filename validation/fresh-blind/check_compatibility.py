#!/usr/bin/env python3
"""Replay minimum-target source typechecks, without claiming old-runtime coverage."""
import argparse,concurrent.futures,hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--implementations',type=Path,default=R/'implementations/final');p.add_argument('--output',type=Path,required=True);p.add_argument('--developer-dir',default=os.environ.get('DEVELOPER_DIR','/Applications/Xcode.app/Contents/Developer'));a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=False);env=dict(os.environ,DEVELOPER_DIR=a.developer_dir)
 sdks={name:subprocess.check_output(['xcrun','--sdk',name,'--show-sdk-path'],env=env,text=True).strip()for name in ['iphonesimulator','macosx']}
 def one(source):
  files=sorted((source/'alerttoast/Sources/AlertToast').glob('*.swift'));assert files;out=a.output/source.name;out.mkdir();results=[]
  for sdk,target,name in [('iphonesimulator','arm64-apple-ios14.0-simulator','ios14'),('macosx','arm64-apple-macosx11.0','macos11')]:
   argv=['xcrun','--sdk',sdk,'swiftc','-typecheck','-sdk',sdks[sdk],'-target',target]+[str(p)for p in files]
   result=subprocess.run(argv,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);log=out/(name+'.log');log.write_text(result.stdout);results.append({'target':target,'argv':argv,'exitCode':result.returncode,'log':log.name,'logSha256':sha(log)})
  report={'checkedAtUTC':datetime.now(timezone.utc).isoformat(),'submission':source.name,'productionArchiveManifestSha256':sha(source/'manifest.json'),'sourceFiles':{str(p.relative_to(source)):sha(p)for p in files},'commands':results,'scope':'Source typechecks againstminimumOS targets; no runtime14/macOS11 visual or behavior claim.'};(out/'compatibility.json').write_text(json.dumps(report,indent=2)+'\n');return {'submission':source.name,'exitCodes':[x['exitCode']for x in results]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  results=list(pool.map(one,sorted(a.implementations.resolve().glob('submission-*'))))
 print(json.dumps(results));return 0 if results and all(all(code==0 for code in row['exitCodes'])for row in results)else 1
if __name__=='__main__':raise SystemExit(main())
