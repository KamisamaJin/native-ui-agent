from pathlib import Path
import json,hashlib,sys,importlib.util,datetime,time
from PIL import Image,ImageOps,ImageDraw,ImageFont
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/state-forward'); O=R/'evaluation/paired-D0'; D=R/'design/private'
def loadmod(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def save(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
batch=json.loads((R/'evaluation-inputs/paired-D0/batch.json').read_text());oracle=json.loads((D/'oracle.json').read_text());ledger=json.loads((D/'states-ledger.json').read_text())
helperpath=Path(batch['immutableHelper']);sys.path.insert(0,str(helperpath.parent));helper=loadmod('delivered_immutable_native_checks',helperpath)
mods={v:(loadmod('normalize_'+v,base/'normalize.py'),loadmod('grade_'+v,base/'grade.py')) for v,base in [('v4',D)]}
phaseStart=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.monotonic();verification=[];images=[]
for arm in batch['corpora']:
 aid=arm['anonymousID'];cap=Path(arm['v4Captures']);manifest=json.loads((cap/'portable-sha256.json').read_text());assert hashlib.sha256((cap/'portable-sha256.json').read_bytes()).hexdigest()==arm['portableManifests']['v4']
 for rel,sha in manifest.items():assert hashlib.sha256((cap/rel).read_bytes()).hexdigest()==sha,rel
 verification.append(dict(anonymousID=aid,portableManifest=str(cap/'portable-sha256.json'),filesVerified=len(manifest)))
 for version,(norm,grade) in mods.items():
  evidence=dict(schemaVersion=1,anonymousID=aid,stage='paired-D0',rawEvidence=[],records=[],adapterDiagnostics=[])
  for platform in ['android','ios']:
   for cid in ['P1','P2','P3','P4']:
    raw=cap/platform/cid/'observation.json';mapping=R/f'evaluation-inputs/D0/mappings/{cid}/mapping.{platform}.json'
    result=norm.normalize(oracle,ledger,json.loads(raw.read_text()),json.loads(mapping.read_text()),platform,cid,aid,'paired-D0',helper,str(raw),str(mapping))
    evidence['rawEvidence']+=result['rawEvidence'];evidence['records']+=result['records'];evidence['adapterDiagnostics']+=result.get('adapterDiagnostics',[])
    save(O/aid/version/'by-case'/f'{platform}-{cid}.json',result)
  save(O/aid/version/'native-normalized.json',evidence)
  save(O/aid/version/'native-grade.json',grade.grade(oracle,evidence))
 # Every delivered screenshot appears exactly once, in observation order (remaining PNGs sorted afterward).
 for platform in ['android','ios']:
  for cid in ['P1','P2','P3','P4']:
   root=cap/platform/cid;obs=json.loads((root/'observation.json').read_text());ordered=[]
   for i,s in enumerate(obs['snapshots']):
    rel=s.get('screenshot');path=root/rel if rel else None
    if path and path.is_file() and path.suffix.lower()=='.png' and path not in [x[0] for x in ordered]:ordered.append((path,i,s.get('state_id'),s.get('name'),s.get('binding')))
   for path in sorted(root.rglob('*.png')):
    if path not in [x[0] for x in ordered]:ordered.append((path,None,None,'extra delivered screenshot',None))
   tilew=260;tileh=580;cols=6;rows=(len(ordered)+cols-1)//cols
   sheet=Image.new('RGB',(cols*tilew,rows*tileh),'#D7DDE5');draw=ImageDraw.Draw(sheet)
   for n,(path,idx,state,name,binding) in enumerate(ordered):
    im=Image.open(path).convert('RGB');thumb=ImageOps.contain(im,(tilew-8,tileh-46));x=(n%cols)*tilew;y=(n//cols)*tileh
    sheet.paste(thumb,(x+(tilew-thumb.width)//2,y+42));draw.text((x+4,y+3),f'{aid} {platform} {cid} #{idx}',fill='black');draw.text((x+4,y+18),f'{state} / {name}'[:38],fill='black')
    images.append(dict(anonymousID=aid,platform=platform,caseID=cid,snapshotIndex=idx,stateID=state,name=name,binding=binding,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),contactSheet=str(O/aid/'v4/contact-sheets'/f'{platform}-{cid}.png'),contactTile=n))
   dest=O/aid/'v4/contact-sheets'/f'{platform}-{cid}.png';dest.parent.mkdir(parents=True,exist_ok=True);sheet.save(dest)
save(O/'delivery-verification.json',dict(verifiedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),corpora=verification))
save(O/'screenshot-inventory.json',dict(images=images,count=len(images)))
save(O/'normalization-cost.json',dict(phase='native_normalization_and_contact_sheets',startUTC=phaseStart,endUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),wallSeconds=time.monotonic()-start,helperSHA256=hashlib.sha256(helperpath.read_bytes()).hexdigest()))
print('screenshots',len(images))
for arm in batch['corpora']:
 for ver in ['v4']:
  g=json.loads((O/arm['anonymousID']/ver/'native-grade.json').read_text())
  print(arm['anonymousID'],ver,g['summary']['public'])
