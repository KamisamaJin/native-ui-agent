from pathlib import Path
import json,hashlib,shutil,sys,importlib.util,math
from PIL import Image,ImageDraw
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'supplement/T1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
 assert not p.exists(),str(p)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def ev(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
sys.path.insert(0,str(R/'candidate-v7/scripts'));import cohort_gate
for stage in ['fix','original-finalized']:cohort_gate.verify(R/'shared-environment-v1/gates',stage)
spec=importlib.util.spec_from_file_location('fixed_oracle',R/'shared-environment-v1/oracle_common.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
import native_checks as nc
index=[];seen={};audit={'scope':'Posthoc direction-only environment compatibility supplement. Primary artifacts unchanged.','batches':[],'manual_provenance':[],'original_seals':[]}
for stage in ['D0','FINAL','selfreview','paired-D0']:
 d=R/f'evaluation/{stage}/T1';seal=read(d/'SEAL.json');assert all(sha(d/p)==h for p,h in seal['files'].items());audit['original_seals'].append(ev(d/'SEAL.json'))
for stage in ['D0','FINAL']:
 batch=read(R/f'evaluation-inputs/{stage}/T1/batch.json');audit['batches'].append(ev(R/f'evaluation-inputs/{stage}/T1/batch.json'))
 for entry in batch['corpora']:
  s=entry['anonymousID'];co=R/entry['captures']
  for c in batch['cases']:
   for platform in ['ios','android']:
    d=co/platform/c;out=O/stage/s/c/platform;op=d/'observation.json';base=g.grade_task(R/'design-v2/T1',c,platform,op,root=d,manual=None,source_root=None,api_review=None);write(out/'native-base-grade.json',base);write(out/'native-base.json',base['native_report']);primary=R/f'evaluation/{stage}/T1/{s}/{c}/{platform}';shutil.copyfile(primary/'manual.json',out/'original-manual.json');shutil.copyfile(primary/'api-review.json',out/'api-review.json')
    if platform=='ios':shutil.copyfile(primary/'manual.json',out/'manual.json');assert (primary/'manual.json').read_bytes()==(out/'manual.json').read_bytes()
    audit['manual_provenance'].append({'stage':stage,'alias':s,'case':c,'platform':platform,'original_manual':ev(primary/'manual.json'),'preserved_copy':ev(out/'original-manual.json'),'byte_exact':True,'effective_ios_byte_exact':platform=='ios','original_api_review':ev(primary/'api-review.json'),'preserved_api_review':ev(out/'api-review.json')})
    print(stage,s,c,platform,base['counts'],'F',[r['id'] for r in base['rows'] if r['status']=='F'])
    if platform!='android':continue
    obs=read(op);design='private'if c=='H1'else'public';plan=read(R/f'design-v2/T1/{design}/compiled/{c}/{platform}/plan.json')
    for state in plan['states']:
     found,complete,why,binding=nc.state_evidence(obs,state);proofs=[{'snapshot_index':i,'path':snap['screenshot'],'sha256':sha(d/snap['screenshot'])} for i,snap in found];sig=tuple(p['sha256'] for p in proofs)
     if sig not in seen:
      tiles=[]
      for i,snap in found:
       im=Image.open(d/snap['screenshot']).convert('RGB');h=round(im.height*360/im.width);tile=Image.new('RGB',(360,h+32),'#eeeeee');tile.paste(im.resize((360,h)),(0,32));ImageDraw.Draw(tile).text((4,6),f'{stage} {s} {c} {state["id"]} #{i}',fill='#000');tiles.append(tile)
      cols=min(4,len(tiles));th=max(t.height for t in tiles);sheet=Image.new('RGB',(cols*360,math.ceil(len(tiles)/cols)*th),'#dddddd')
      for j,tile in enumerate(tiles):sheet.paste(tile,((j%cols)*360,(j//cols)*th))
      name=f'{stage}-{s}-{c}-{state["id"]}.png';path=O/'review'/name;path.parent.mkdir(exist_ok=True);sheet.save(path);seen[sig]=name
     index.append({'stage':stage,'alias':s,'case':c,'platform':platform,'state':state['id'],'complete':complete,'coverage_reason':why,'observation':ev(op),'snapshot_indices':[i for i,_ in found],'original_snapshots':proofs,'review_sheet':seen[sig],'identical_original_png_sequence_group':list(sig)})
write(O/'artifact-audit.json',audit);write(O/'review/index.json',index);print('Unique review sheets',len(seen),'state observations',len(index))
