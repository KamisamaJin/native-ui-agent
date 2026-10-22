import hashlib, json
from pathlib import Path
BASE = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT = BASE / 'claim-judgments/two/T3'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, v): (OUT/name).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def pointer(v, p):
    for part in p.strip('/').split('/'):
        part=part.replace('~1','/').replace('~0','~')
        v=v[int(part)] if isinstance(v,list) else v[part]
    return v
integrity={}; inspection={}; common={}
for source in ['source-a','source-b']:
    transport=BASE/'evaluation-inputs/claims/T3'/source/'claims.json'
    d=read(transport); checks=[]
    for rel,expected in d['original_files'].items():
        p=BASE/rel; actual=sha(p) if p.is_file() else None
        checks.append({'path':rel,'expected':expected,'actual':actual,'matches':actual==expected})
    pointers=[]; observations={}; entries=[]; originals={}
    for c in d['claims']:
        p=BASE/c['original_json']
        if str(p) not in originals: originals[str(p)]=read(p)
        original=pointer(originals[str(p)],c['original_pointer'])
        pointers.append({'claim_id':c['claim_id'],'matches':original==c['original']})
        if c['original_status']!='failed' or c.get('duplicate_of'): continue
        root=BASE/c['observation_root']; op=root/'observation.json'
        if str(op) not in observations: observations[str(op)]=read(op)
        obs=observations[str(op)]
        indices=c['original'].get('snapshot_indices',[])
        if not indices and c['original'].get('id','').endswith('successful-activation-callback'):
            indices=[s['index']for s in obs['snapshots']if s.get('state_id')=='submitted'][-3:]
        snaps=[]
        for i in indices:
            s=obs['snapshots'][i]
            groups=[]
            for g in s.get('control_groups',[]):
                if g.get('selector',{}).get('identifier') in ['bicycle.summary','bicycle.submit','bicycle.choice.a','bicycle.choice.b','bicycle.disclosure']:
                    groups.append(g)
            snaps.append({'index':i,'state_id':s.get('state_id'),'screenshot':str(root/s['screenshot']),
                          'screenshot_sha256':sha(root/s['screenshot']),'binding':s.get('binding'),
                          'binding_after_capture':s.get('binding_after_capture'),'capture_consistent':s.get('capture_consistent'),
                          'control_groups':groups,'callbacks':s.get('callbacks')})
        entries.append({'claim_id':c['claim_id'],'original_scope':c['original_scope'],
                        'original_expected':(c.get('original_plan')or c['original']).get('expected'),
                        'original_unit':(c.get('original_plan')or c['original']).get('unit'),
                        'snapshots':snaps,'original_evidence':c['original'].get('evidence',[]),
                        'raw_steps':obs['steps'] if c['platform']=='ios' and source=='source-a' else []})
    integrity[source]={'transport_sha256':sha(transport),'original_file_checks':checks,'original_pointer_checks':pointers,
                       'file_mismatch_count':sum(not x['matches']for x in checks),
                       'pointer_mismatch_count':sum(not x['matches']for x in pointers)}
    inspection[source]=entries
    common[source]=[]
    for p in sorted((BASE/'evaluation/d0/T3'/source).glob('*/*/acceptance.json')):
        plat,case=p.parts[-3:-1]; rows=read(p)['rows']
        for r in rows:
            if r['status']=='failed'and r.get('cause_category')=='product':
                common[source].append({'key':f'{case}/{plat}/{r["id"]}',**r})
write('input-integrity.json',integrity)
write('original-evidence-extract.json',inspection)
write('common-confirmed-product-rows.json',common)
print(json.dumps({s:{'original_files':len(v['original_file_checks']),'mismatches':v['file_mismatch_count'],
                     'pointer_checks':len(v['original_pointer_checks']),'pointer_mismatches':v['pointer_mismatch_count'],
                     'product_rows':len(common[s])}for s,v in integrity.items()},indent=2))
