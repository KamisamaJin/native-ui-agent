from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'evaluation/FINAL/T3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def save(p,x):assert not p.exists(),p;p.write_text(json.dumps(x,indent=2)+'\n')
batch=json.loads((R/'evaluation-inputs/FINAL/T3/batch.json').read_text());ds=R/'evaluation-inputs/FINAL/DELIVERY-SEAL.json';delivery=json.loads(ds.read_text());index=[];integrity={'batch':ref(R/'evaluation-inputs/FINAL/T3/batch.json'),'delivery':ref(ds),'sources':{}}
for b in batch['corpora']:
 alias=b['anonymousID'];corp=R/b['captures'];cap=R/b['sourceCapsule'];seal=cap/'seal.json';portable=corp/'portable-sha256.json';assert sha(seal)==b['sourceSealSHA256'];assert sha(portable)==b['portableManifestSHA256'];sp=json.loads(seal.read_text());pm=json.loads(portable.read_text());sm=[x for x,h in sp['files'].items() if not(cap/'source'/x).exists() or sha(cap/'source'/x)!=h];mismatch=[x for x,h in pm.items() if not(corp/x).exists() or sha(corp/x)!=h];assert not(sm or mismatch)
 df={k:h for k,h in delivery['files'].items() if k.startswith('T3/'+alias+'/') or k=='T3/batch.json'};dm=[k for k,h in df.items() if sha(R/'evaluation-inputs/FINAL'/k)!=h];assert not dm
 rec={'source_seal':ref(seal),'source_seal_files_checked':len(sp['files']),'portable_manifest':ref(portable),'portable_files_checked':len(pm),'delivery_scoped_files_checked':len(df),'mismatches':sm+mismatch+dm,'cases':{}}
 for case in batch['cases']:
  for platform in ['ios','android']:
   d=corp/platform/case;op=d/'observation.json';obs=json.loads(op.read_text());m=json.loads((d/'manifest.json').read_text());rel='alerttoast/Sources/AlertToast/CollectionConditionReviewPanel.swift' if platform=='ios' else 'reply/Reply/app/src/main/java/com/example/reply/ui/components/CollectionConditionReviewPanel.kt';source=cap/'source'/rel;bound=[h for k,h in m['source_hashes'].items() if k.endswith('/'+rel)];assert bound==[sha(source)]
   logs=[ref(d/n) for n in ['manifest.json','build.log','test.log','junit.xml'] if (d/n).exists()];extract={}
   for n in ['build.log','test.log']:
    p=d/n
    if p.exists():extract[n]=[l for l in p.read_text(errors='replace').splitlines() if any(t in l.lower() for t in ['error:','failed','failure','build successful','test succeeded','executed 1 test'])][-8:]
   cr={'observation':ref(op),'source':ref(source),'source_matches_native_manifest':True,'original_logs':logs,'commands_and_results':{k:m[k] for k in ['status','command','build_command','test_command','build_exit_code','test_exit_code','exit_code','native_test_count','native_counts'] if k in m},'native_summary':m.get('native_summary'),'log_diagnostics':extract,'configuration':obs.get('configuration'),'issues':obs.get('issues',[]),'coverage':obs.get('coverage'),'dispatches':[{'state':s['state_id'],'outcome':s.get('outcome'),'dispatch':s.get('dispatch'),'callback_delta':s.get('callback_delta')} for s in obs.get('steps',[])]}
   rec['cases'][case+'/'+platform]=cr
   print(alias,case,platform,'native',cr['commands_and_results'].get('status'),cr['commands_and_results'].get('test_exit_code',cr['commands_and_results'].get('exit_code')))
   if platform!='ios':continue
   for state in ['loaded','reasoned','advanced','classified','submitted','replaced']:
    capture=next(x for x in obs['state_captures'] if x['state_id']==state);tiles=[];ev=[]
    for i in capture['snapshot_indices']:
     s=obs['snapshots'][i];path=op.parent/s['screenshot'];im=Image.open(path).convert('RGB');v=s['viewport'];a=s['app_frame'];sx=im.width/a['width'];sy=im.height/a['height'];box=(round((v['x']-a['x'])*sx),round((v['y']-a['y'])*sy),round((v['x']-a['x']+v['width'])*sx),round((v['y']-a['y']+v['height'])*sy));im=im.crop(box).resize((round(v['width']),round(v['height'])));tile=Image.new('RGB',(im.width,im.height+28),'#eeeeee');tile.paste(im,(0,28));ImageDraw.Draw(tile).text((4,5),f'{alias} {case} {state} #{i}',fill='black');tiles.append(tile);ev.append({'snapshot_index':i,**ref(path)})
    w=max(t.width for t in tiles);h=max(t.height for t in tiles);cols=min(4,len(tiles));sheet=Image.new('RGB',(cols*w,math.ceil(len(tiles)/cols)*h),'#dddddd')
    for j,t in enumerate(tiles):sheet.paste(t,((j%cols)*w,(j//cols)*h))
    dest=O/alias/case/platform/f'review-{state}.png';sheet.save(dest);index.append({'sheet':str(dest.relative_to(O)),'observation':ref(op),'state':state,'complete':capture['complete'],'snapshot_indices':capture['snapshot_indices'],'evidence':ev})
 integrity['sources'][alias]=rec
save(O/'input-integrity.json',integrity);save(O/'visual-index.json',index);print('review sheets',len(index))
