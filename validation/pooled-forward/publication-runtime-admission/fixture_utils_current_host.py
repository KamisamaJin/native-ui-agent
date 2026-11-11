"""Small synthetic fixtures; no business/grade/alarm/model data."""
import base64
import json
from pathlib import Path, PurePosixPath
import struct
import zlib

import replay as rp


HERE=Path(__file__).resolve().parent


class Reader:
    def __init__(self,physical):self.physical=Path(physical);self.physical.mkdir(parents=True,exist_ok=False);self.files={};self.reads=[]
    def put(self,original,value):
        original=str(original);raw=value if isinstance(value,bytes) else (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
        self.files[original]=raw;p=self.physical/original.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        return {'path':original,'sha256':rp.sha(raw)}
    def read_bytes(self,original):
        original=str(original);self.reads.append(original)
        if original in self.files:return (self.physical/original.lstrip('/')).read_bytes()
        p=Path(original)
        if not p.is_relative_to(HERE):raise KeyError('Synthetic original absent: '+original)
        return p.read_bytes()
    def read_json(self,p):return rp.strict_json(self.read_bytes(p))
    def hash(self,p):return rp.sha(self.read_bytes(p))
    def directory(self,original):
        original=str(original)
        if any(k.startswith(original.rstrip('/')+'/') for k in self.files):return self.physical/original.lstrip('/')
        p=Path(original)
        if p.is_relative_to(HERE) and p.is_dir():return p
        raise KeyError('Synthetic directory absent: '+original)
    def restore(self,folder):
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);namespace=folder/'files';namespace.mkdir()
        originals=dict(self.files)
        inv_path=HERE/'CODE-INVENTORY.json';inv=rp.strict_json(inv_path.read_bytes());originals[str(inv_path)]=inv_path.read_bytes()
        for label,tool in inv['backends'].items():
            originals[tool['freeze']['path']]=Path(tool['freeze']['path']).read_bytes()
            for row in tool['files'].values():originals[row['path']]=Path(row['path']).read_bytes()
        for row in inv['runtime']['files'].values():originals[row['path']]=Path(row['path']).read_bytes()
        # Current-host transport includes separately pinned sibling wheel libraries.
        for row in inv['runtime'].get('support_files',{}).values():originals[row['path']]=Path(row['path']).read_bytes()
        worker=HERE/'runner/worker.py';originals[str(worker)]=worker.read_bytes()
        mappings={}
        for original,raw in originals.items():
            logical=original.lstrip('/');p=namespace/logical;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            mappings[original]={'physical_path':str(p),'logical_path':logical,'sha256':rp.sha(raw),'bytes':len(raw),'original_mode':'0644','restored_mode':'0644'}
        index=rp.sha(b'synthetic evaluator external archive index')
        value={'format':'explicit-file-lossless-v1','version':1,'index_sha256':index,'namespace':str(namespace),'mappings':mappings,'scope':'Synthetic evaluator only; no actual study data.'}
        mapping=folder/'RESTORED-MAP.json';mapping.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
        return mapping,rp.sha(mapping.read_bytes()),index


def code_refs():
    inventory=HERE/'CODE-INVENTORY.json';worker=HERE/'runner/worker.py'
    return {'path':str(inventory),'sha256':rp.sha(inventory.read_bytes())},{'path':str(worker),'sha256':rp.sha(worker.read_bytes())}


def png(fill,canvas):
    def rgb(value):return bytes.fromhex(value.lstrip('#'))
    pixels=[]
    for y in range(120):
        row=b''.join(rgb(fill if 10<=x<70 and 20<=y<50 else canvas) for x in range(100));pixels.append(b'\x00'+row)
    def chunk(kind,raw):return struct.pack('>I',len(raw))+kind+raw+struct.pack('>I',zlib.crc32(kind+raw)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',100,120,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(pixels)))+chunk(b'IEND',b'')


_PREPARED=None


def prepare(reader):
    global _PREPARED
    if _PREPARED is not None:return _PREPARED
    inventory_ref,worker_ref=code_refs();a=rp.Access(reader);job,worker=rp.code_job(a,inventory_ref,worker_ref,'B')
    base=HERE/'vendor/frozen/B/assets/atomic-example';raw={n:(base/(n+'.json')).read_bytes() for n in ['lock','policy','bindings','actions']}
    job.update(mode='prepare_synthetic_fixture',synthetic_only=True,inputs={n:{'raw_base64':base64.b64encode(v).decode(),'sha256':rp.sha(v)} for n,v in raw.items()},
               lock_canonical_sha256=rp.digest(rp.strict_json(raw['lock'])),policy_canonical_sha256=rp.digest(rp.strict_json(raw['policy'])))
    result=rp.execute(job,worker);_PREPARED=(raw,result);return _PREPARED


def fixture(physical,*,backend='A',mutation=None):
    f=Reader(physical);raw,prepared=prepare(f);root=PurePosixPath('/recorded/evaluator');capture=root/'capture';native=capture/'native'
    plan=rp.strict_json(json.dumps(prepared['plan']));catalog=rp.strict_json(json.dumps(prepared['catalog']))
    refs={}
    for key in ['lock','policy']:
        refs[key]=f.put(root/(key+'.json'),raw[key]);refs[key]['canonical_sha256']=rp.digest(rp.strict_json(raw[key]))
    refs['plan']=f.put(root/'plan.json',plan)
    observation={'snapshots':[],'state_captures':[],'configuration':{'direction':'Ltr','font_scale':1.0,'night_mode_mask':16}}
    for i,(state,fill,canvas) in enumerate([('observed','#397A91','#D6E8F3'),('changed','#976038','#ECE2D1')]):
        f.put(native/(state+'.png'),png(fill,canvas));binding={'fixture_index':i,'instance':'synthetic-native-epoch','event_revision':0,'input_sha256':str(i)*64}
        nodes=[{'identifier':'probe.'+uid,'node_id':n+1,'parent_id':-1,'intersects_viewport':True,'fully_visible':True,'unclipped_bounds_dp':bounds}
               for n,(uid,bounds) in enumerate([('canvas',[0,0,100,120]),('tile',[10,20,70,50]),('title',[10,2,70,18])])]
        observation['snapshots'].append({'state_id':state,'binding':binding,'capture_consistent':True,'binding_after_capture':dict(binding),
            'screenshot':state+'.png','screenshot_pixels':{'width':100,'height':120},'logical_viewport_dp':{'width':100,'height':120},'nodes':nodes,
            'scroll_offset_dp':0,'scroll_max_dp':0,'viewport_height_dp':120})
        observation['state_captures'].append({'state_id':state,'after_action':0 if i==0 else 2,'binding':binding,'snapshot_indices':[i],
                                            'top_reached':True,'bottom_reached':True,'stable_binding':True})
    if mutation and mutation[0]=='observation':mutation[1](observation)
    refs['observation']=f.put(native/'observation.json',observation)
    submission={'version':1,'catalog_sha256':rp.digest(catalog),'observation_sha256':refs['observation']['sha256'],'decisions':[
       {'review_id':row['review_id'],'actual':True,'reason':'Synthetic original proposition actual','snapshot_indices':[0 if row['state']=='observed' else 1]}
       for row in catalog['rows'] if row['method']=='visual']}
    if mutation and mutation[0]=='submission':mutation[1](submission)
    refs['submission']=f.put(root/'submission.json',submission)
    images={name:rp.sha(f.files[str(native/name)]) for name in ['observed.png','changed.png']}
    request={'version':1,'parent_plan_sha256':rp.digest(plan),'input_hashes':{}}
    if mutation and mutation[0]=='request':mutation[1](request)
    refs['capture_request']=f.put(capture/'request.json',request)
    receipt={**request,'observation_sha256':refs['observation']['sha256'],'image_hashes':images,'source_unchanged':True}
    refs['capture_receipt']=f.put(capture/'result.json',receipt)
    packet={'version':1,'kind':'original-fact-evaluator-replay-packet-v1','data_scope':'synthetic-host-only','backend':backend,'platform':'android',
            **refs,'native_root':str(native),'image_hashes':images,'expected_artifacts':{}}
    if mutation and mutation[0]=='packet':mutation[1](packet)
    packet_ref=f.put(root/'PACKET.json',packet)
    return f,packet_ref,packet
