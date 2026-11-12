from pathlib import Path
import sys,json,hashlib
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
OUT=BASE/'business-design-review'
allowed=[BASE/'business-design',BASE/'candidate-v13.9']
log=json.loads((OUT/'READSET.json').read_text())
name=sys.argv[1]
parts=[]
for x in sys.argv[2:]:
 p=(BASE/x).resolve()
 if not any(p.is_relative_to(a) for a in allowed): raise RuntimeError('out of scope')
 b=p.read_bytes(); h=hashlib.sha256(b).hexdigest()
 if not any(e['path']==str(p) and e['sha256']==h for e in log):log.append({'path':str(p),'sha256':h,'bytes':len(b),'operation':'review-content-read'})
 t=b.decode()
 parts.append('\nFILE '+str(p)+'\n'+''.join(f'{i:4} {l}\n' for i,l in enumerate(t.splitlines(),1)))
text=''.join(parts)
(OUT/'READSET.json').write_text(json.dumps(log,indent=2)+'\n')
(OUT/(name+'.txt')).write_text(text)
print(text)
