from pathlib import Path
import json,sys,hashlib,math,time
from PIL import Image,ImageDraw,ImageFont
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT=BASE/'judgments/d0/one/T3'
sys.path.insert(0,str(BASE/'candidate-v8/scripts'))
import native_checks
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',12)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
audit={}; coverage={}; hashes={}; inspected={}
for p in sorted((BASE/'evaluation-inputs/d0/T3').glob('*/*/*')):
    so,pl,ca=p.parts[-3:]; key='/'.join([so,pl,ca]);ds={n:json.loads((p/(n+'.json')).read_text()) for n in ['inputs','plan','catalog','automatic','environment-check']}
    for n in ds:hashes[str((p/(n+'.json')).relative_to(BASE))]=sha(p/(n+'.json'))
    i=ds['inputs'];root=BASE/i['root'];o=json.loads((BASE/i['observation']).read_text());audit[key]={'input_hash_check':sha(BASE/i['observation'])==i['observation_sha256'],'states':{}}
    for rel,expected in i['original_files'].items():
        if rel not in hashes:hashes[rel]=sha(BASE/rel)
        if hashes[rel]!=expected:audit[key].setdefault('original_hash_mismatches',[]).append(rel)
    coverage[key]={}
    for state in ds['plan']['states']:
        found,complete,why,capture=native_checks.bound_state_evidence(o,state);sid=state['id']
        coverage[key][sid]={'indices':[n for n,_ in found],'complete':complete,'reason':why,'capture':capture}
        frames=[]
        for idx,snap in found:
            path=root/snap['screenshot'];im=Image.open(path).convert('RGB');w,h=im.size
            hashes[str(path.relative_to(BASE))]=sha(path)
            if pl=='ios':
                vp=snap['viewport'];app=snap['app_frame'];sx=w/app['width'];sy=h/app['height'];box=(round((vp['x']-app['x'])*sx),round((vp['y']-app['y'])*sy),round((vp['x']+vp['width']-app['x'])*sx),round((vp['y']+vp['height']-app['y'])*sy));im=im.crop(box)
                offset=vp['y']-snap['runtime']['content_frame']['y']
            else:offset=snap['scroll_offset_dp']
            # Viewport crops only; no stitching, omissions, recoloring or target replacement.
            width=360 if ca=='P1' else 300
            im=im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS)
            frames.append((idx,offset,im))
        cols=4 if ca=='P2' else min(5,max(1,len(frames)));cw=(360 if ca=='P1' else 300)+10;ch=max((im.height for _,_,im in frames),default=1)+58
        sheet=Image.new('RGB',(cols*cw,math.ceil(len(frames)/cols)*ch),(242,242,242));d=ImageDraw.Draw(sheet)
        for n,(idx,off,im) in enumerate(frames):
            x=(n%cols)*cw;y=(n//cols)*ch
            d.text((x+4,y+4),f'{so} {pl} {ca}',font=font,fill='black');d.text((x+4,y+20),f'{sid} index={idx} offset={off:.2f}',font=font,fill='black');sheet.paste(im,(x+4,y+40))
        sp=OUT/'contact-sheets'/so/pl/ca/(sid+'.png');sp.parent.mkdir(parents=True,exist_ok=True);sheet.save(sp)
        targets=[]
        for idx,snap in found:
            for ident in ['bicycle.canvas','bicycle.title','bicycle.notice','bicycle.choice.a','bicycle.choice.b','bicycle.choice.c','bicycle.choice.f','bicycle.summary','bicycle.disclosure','bicycle.submit','bicycle.footer']:
                r=native_checks.resolve(snap,{'identifier':ident},pl);sem=r.get('semantic',{}); facts=r.get('facts',{})
                if sem.get('intersects_viewport',sem.get('visible',True)):
                    targets.append({'index':idx,'identifier':ident,'facts':facts,'semantic':sem,'control':r.get('control')})
        audit[key]['states'][sid]={'indices':[n for n,_ in found],'complete':complete,'reason':why,'binding':capture.get('binding') if capture else None,'targets':targets}
    steps=[]
    for n,st in enumerate(o['steps']):steps.append({'action_index':n,**{k:v for k,v in st.items() if k in ['action','state_id','outcome','callback_delta','events','dispatch','binding_after','binding_before','after','before','immediate_after','target','activation_target']}})
    audit[key]['steps']=steps
    audit[key]['automatic_failures']=[r for r in ds['automatic']['assertions'] if r['status']=='failed']
    inspected[key]={'original_snapshot_count':len(o['snapshots']),'bound_state_frames':sum(len(s['indices']) for s in coverage[key].values()),'source_capsule':i['source_capsule']}
dump(OUT/'input-hashes.json',hashes);dump(OUT/'coverage.json',coverage);dump(OUT/'evidence-audit.json',audit);dump(OUT/'inspection-inventory.json',inspected)
print(json.dumps(inspected,indent=2))
