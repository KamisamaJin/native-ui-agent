#!/usr/bin/env python3
"""Common frontend policy repair; native observation/assertion code is unchanged."""
import ast,hashlib,importlib.util,json,shutil,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
GUARD='    if config.get("width", 390) not in (320, 390): raise ValueError("width must be 320 or 390 logical points")'
FUNCTION='''def validate_offered_width(width):
    # The existing native host consumes an explicit logical width. Public AX
    # viewport/content geometry still establishes actual coverage; allowing an
    # offered width does not certify that it fits a particular simulator.
    if type(width) not in (int, float) or not math.isfinite(width) or not 160 <= width <= 1024:
        raise ValueError("width must be a finite number from 160 to 1024 logical points")


'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 record={'recordedAtUTC':datetime.now(timezone.utc).isoformat(),'recordedAtUnix':time.time(),'reason':'Both original own-D0 iOS P2 calls rejected independent300pt design at frontend before native test; original H1 also offers360pt. Native host already transports a CGFloat offered width. Extend only common frontend input policy, equally for both frozen tools, preserving exact design/source/actions and all failed attempts.','attribution':'Common infrastructure amendment, not a v6 treatment benefit.','versions':{},'controls':{}}
 for tool in ['baseline-v5','candidate-v6']:
  src=R/tool;dst=R/('runtime-'+tool);assert not dst.exists();shutil.copytree(src,dst)
  p=dst/'scripts/ios_observe.py';text=p.read_text();assert text.count(GUARD)==1
  text=text.replace('def run(args) -> int:',FUNCTION+'def run(args) -> int:').replace(GUARD,'    validate_offered_width(config.get("width", 390))');p.write_text(text)
  changed=[str(f.relative_to(dst))for f in dst.rglob('*')if f.is_file()and sha(f)!=sha(src/f.relative_to(dst))];assert changed==['scripts/ios_observe.py']
  spec=importlib.util.spec_from_file_location('width_'+tool.replace('-','_'),p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  results=[]
  for width in [160,280,320,340,390,768,1024]:module.validate_offered_width(width);results.append({'width':width,'accepted':True})
  for width in [0,-1,159,1025,True,'340',float('nan'),float('inf')]:
   try:module.validate_offered_width(width)
   except ValueError:results.append({'width':repr(width),'rejected':True})
   else:raise AssertionError(width)
  record['controls'][tool]=results;record['versions'][tool]={'root':str(dst.relative_to(R)),'changed':changed,'originalCLI':sha(src/'scripts/ios_observe.py'),'runtimeCLI':sha(p),'files':{str(f.relative_to(dst)):sha(f)for f in sorted(dst.rglob('*'))if f.is_file()and '__pycache__'not in f.parts}}
 record['frozenAtUTC']=datetime.now(timezone.utc).isoformat();record['frozenAtUnix']=time.time();(R/'COMMON-WIDTH-AMENDMENT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'status':'PASS','changedOnly':'shared iOS frontend offered-width guard','versions':list(record['versions'])}))
if __name__=='__main__':main()
