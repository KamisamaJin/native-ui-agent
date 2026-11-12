#!/usr/bin/env python3
"""Static QA of independent authored data only. No SDK, candidate, or tool implementation."""
import hashlib,json,re
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
def load(p):return json.loads(p.read_text())
def validate(v,s,p='$'):
    ty=s['type'];types={'string':str,'integer':int,'boolean':bool,'array':list,'object':dict}
    assert type(v) is types[ty],(p,ty,type(v).__name__)
    if ty=='object':
        assert set(s['required'])<=set(v),(p,'required')
        assert s.get('additionalProperties',True) or set(v)<=set(s['properties']),(p,'unknown property')
        for k,x in v.items():validate(x,s['properties'][k],p+'/'+k)
    elif ty=='array':
        assert s.get('minItems',0)<=len(v)<=s.get('maxItems',len(v)),(p,'array bounds')
        if s.get('uniqueItems'):assert len({json.dumps(x,sort_keys=True) for x in v})==len(v),(p,'unique items')
        for i,x in enumerate(v):validate(x,s['items'],p+'/'+str(i))
    elif ty=='string':
        assert s.get('minLength',0)<=len(v)<=s.get('maxLength',len(v)),(p,'string bounds',len(v))
        if 'pattern' in s:assert re.search(s['pattern'],v),(p,'pattern')
    elif ty=='integer':assert s.get('minimum',v)<=v<=s.get('maximum',v),(p,'number bounds')
    if 'enum' in s:assert v in s['enum'],(p,'enum')
summary=[]
for task in ('T1','T2','T3','T4','T5'):
    pub=load(ROOT/task/'public/reference.json');hid=load(ROOT/task/'private/reference.json')
    assert pub['business_rules']==hid['business_rules'] and pub['tokens']==hid['tokens'] and pub['questions']==hid['questions']
    hidden_ids=[load(ROOT/task/'private/fixtures.ios.json')['initial']['entityId'],load(ROOT/task/'private/fixtures.ios.json')['updates'][-1]['entityId']]
    for p in (ROOT/task/'public').glob('*'):
        if p.is_file():assert not any(x in p.read_text() for x in hidden_ids),(p,'hidden entity leak')
    for family in ('public','private'):
        p=ROOT/task/family;contract=load(p/'contract.json');lock=load(p/'lock.json');seal=load(p/'seal.json');policy=load(p/'policy.json');out=load(p/'outcomes.json');denom=load(p/'denominator.json');fixture=load(p/'fixtures.ios.json');schema=load(p/'fixture.schema.json');bind=load(p/'bindings.ios.json')
        fixtures=[fixture['initial']]+fixture['updates']
        for f in fixtures:
            validate(f,schema)
            for k in ('lots','slots','methods','audiences'):
                if k in f:
                    assert len({x['id'] for x in f[k]})==len(f[k]);assert len({x['label'] for x in f[k]})==len(f[k])
        assert digest(lock)==seal['design_lock_sha256']==policy['design_lock_sha256'];assert digest(contract)==lock['contract_sha256']
        assert digest(policy)==seal['policy_sha256'];assert digest(load(p/'routes.json'))==seal['routes_sha256']
        for source in contract['sources']:
            raw=(p/source['path']).read_bytes();assert sha(raw)==source['sha256']==lock['sources'][source['id']]['sha256'];assert raw.decode()==lock['sources'][source['id']]['raw_utf8']
        scenario=next(iter(contract['scenarios'].values()));assert len(scenario['actions'])<=40
        assert len(denom['cells'])*2==denom['total_cells']==denom['assess_cells']+denom['not_applicable_cells']
        assert len({(x['requirement'],x['state']) for x in denom['cells']})==len(denom['complete_rule_ids'])*len(denom['complete_state_ids'])
        assert set(policy['ownership'].values())=={'component'}
        assert {a['rule_id'] for a in policy['atoms']}=={r['id'] for r in contract['rules'] if r['kind']=='manual'}
        for a in policy['atoms']:
            if a['method']=='native_pixels':
                s=a['sampling'];assert s['channel_tolerance']==0 and s['minimum_support']==0.95
                if a['rule_id'] not in ('surface-fill','primary-fill'):
                    assert s['region']==[0.94,0.25,0.98,0.75]
                    for w in (326,325.81818):assert s['region'][0]*w>w-24 and s['region'][2]*w<w
        epoch=0
        for i,a in enumerate(scenario['actions']):
            assert a['type'] in ('sweep','tap','checkpoint','apply_next_fixture')
            if a['type']=='apply_next_fixture':epoch+=1
            if a['type']=='tap':assert a['target'] in bind and any(c['property']=='enabled' and c['expected'] is True for c in a['preconditions'])
            for state in scenario['states']:
                if state['after_action']==i:assert state['input_index']==epoch
        previous=None
        for s in out['states']:
            e=s['exact_business_state'];f=fixtures[s['input_index']];event=s['exact_callback_interval'];cs=e['controls']
            assert len({v['label'] for v in cs.values()})==len(cs)
            if 'stimulus_action' in s:
                a=scenario['actions'][s['stimulus_action']]
                if a['type']=='tap':
                    k=a['target'];assert previous is not None
                    assert previous['primary_enabled'] if k=='primary' else previous['controls'][k]['enabled']
                    for c in a['preconditions']:
                        if c['property']=='selected':assert previous['controls'][k]['selected']==c['expected']
                else:assert event==[]
            if e['submitted']:
                assert not e['primary_enabled'] and all(not c['enabled'] for c in cs.values())
                assert len(event)==1
                if task=='T1':
                    selected=[x['id'] for i,x in enumerate(f['lots']) if cs['lot'+chr(65+i)]['selected']];expected='release|'+f['entityId']+'|'+','.join(sorted(selected))
                elif task=='T2':
                    mode='video' if cs['video']['selected'] else 'in_person';slot=next(x['id'] for i,x in enumerate(f['slots']) if cs['slot'+chr(65+i)]['selected']);expected=f"reschedule|{f['entityId']}|{mode}|{slot}"
                elif task=='T3':
                    applied=min(f['creditCents'],f['dueCents']) if cs['credit']['selected'] else 0;remaining=f['dueCents']-applied;method=next((x['id'] for i,x in enumerate(f['methods']) if cs['method'+chr(65+i)]['selected']),'credit');assert remaining!=0 or method=='credit';expected=f"settle|{f['entityId']}|{applied}|{remaining}|{method}"
                elif task=='T4':
                    audience=next(x for i,x in enumerate(f['audiences']) if cs['audience'+chr(65+i)]['selected']);steps='on' if cs['workaround']['selected'] else 'off';expected=f"publish|{f['entityId']}|{audience['id']}|{audience['recipients']}|steps:{steps}";assert e['preview'] is not None and cs['approve']['selected']
                else:
                    route=next(k for k in ('restock','repair','recycle') if cs[k]['selected']);power='pass' if cs['power']['selected'] else 'unchecked';data='erased' if f['dataBearing'] else 'not-required';assert cs['accessories']['selected'] and (not f['dataBearing'] or cs['data']['selected']);expected=f"route-return|{f['entityId']}|{route}|power:{power}|data:{data}|accessories:counted"
                assert event==[expected]
            else:assert event==[]
            previous=e
        for platform,ext in (('ios','swift'),('android','kt')):
            launch=load(p/'launch.json')[platform];assert digest(load(p/f'fixtures.{platform}.json'))==launch['fixtures_sha256'];assert sha((p/f'ObserverBridge.{ext}').read_bytes())==launch['bridge_sha256'];assert digest(load(p/f'environment.{platform}.json'))==seal['environment_sha256'][platform]
        for name in ('reference-initial.svg','reference-ready.svg'):
            tree=ET.parse(p/name);assert int(tree.getroot().attrib['width'])==780 and int(tree.getroot().attrib['height'])>600
        summary.append(dict(task=task,family=family,rules=len(contract['rules']),states=len(scenario['states']),actions=len(scenario['actions']),full_states=sum(s['coverage']=='full_content' for s in scenario['states']),denominator=denom['total_cells'],design_lock_sha256=digest(lock)))
report=dict(version=1,result='passed static author QA',checks=['fixture JSON-schema subset: exact properties/types/bounds/enums/patterns/uniqueness','public/private business rules/tokens/questions identical; hidden entity IDs absent from public bytes','canonical lock/contract/policy/routes/environment and launch source/fixture/bridge identity','complete rule×state×platform denominator','all manual rules exactly in atomic policy; component-owned suitable fixed gutter regions','original supported action kinds, input epochs and native enabled/selected preconditions','all independently authored successful submit payloads match selected business facts and integer arithmetic','submitted controls locked; non-submit and caller-update intervals empty','annotated SVG XML validity without rendering'],not_performed=['existing design_contract/review_contract compiler: delegated to independent format reviewer','SDK/native rendering or candidate inspection'],families=summary)
(ROOT/'AUTHOR-QA.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(result=report['result'],families=len(summary),cells=sum(x['denominator'] for x in summary))))
