"""Source-only exact alias checks; all body values are synthetic."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import unittest

HERE=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
    if not ok:raise AssertionError(message)
def encoded(value):return json.dumps(value,sort_keys=True,ensure_ascii=False).encode()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
def save(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');path.chmod(0o444)


def main():
    need(not (HERE/'RESULT.json').exists(),'Fresh result required');pins=json.loads((HERE/'SOURCE-PINS.json').read_bytes())
    for name,reference in pins.items():need(sha((HERE/'vendor'/name).read_bytes())==reference['sha256'],'Frozen source differs')
    original=load(HERE/'vendor/source_aliases.py','author_aliases');candidate=load(HERE/'source_aliases_v2.py','review_aliases');projection=load(HERE/'vendor/actual_projection_v2.py','review_actuals')
    sys.path.insert(0,str(HERE/'vendor'));author=load(HERE/'vendor/test_source_aliases.py','author_alias_controls')
    author_results=[]
    for name,module in [('original',original),('revision',candidate)]:
        author.module=module
        with (HERE/'HOST'/('author-'+name+'.log')).open('x') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(author))
        author_results.append({'backend':name,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()})
    controls=[];observations=[]
    def case(name,fn):
        try:controls.append({'name':name,'status':'passed','evidence':fn()})
        except BaseException as error:controls.append({'name':name,'status':'failed','error_type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
    def reject(fn):
        try:fn()
        except (ValueError,KeyError) as error:return str(error)
        raise AssertionError('Invalid source binding accepted')
    def fixture(family='private',platform='ios'):
        reader=author.Reader();members={};sources={};contracts={};placement={}
        roots=['/current/iOS','/current/Android'];source_bytes={0:b'synthetic ios component\n',1:b'synthetic android component\n'}
        for index in [0,1]:
            key=str(index)+'/Widget.src';alias='source/'+key;raw=source_bytes[index];members[alias]=reader.put('/packet/'+alias,raw);reader.put(roots[index]+'/Widget.src',raw);sources[key]={'sha256':members[alias],'bytes':len(raw)}
        for fam in ['public','private']:
            contracts[fam]={}
            for plat in ['ios','android']:
                bridge='contracts/'+fam+'/'+plat+'/Bridge.src';raw=('synthetic actual bridge '+fam+' '+plat+'\n').encode();members[bridge]=reader.put('/packet/'+bridge,raw);reader.put('/current/'+fam+'/'+plat+'/Bridge.src',raw)
                api='contracts/'+fam+'/'+plat+'/API.md';members[api]=reader.put('/packet/'+api,b'synthetic normative API only\n');contracts[fam][plat]={'bridge':bridge,'api':api}
        for plat in ['ios','android']:
            alias='source/placement/'+plat+'/Project.src';raw=('synthetic approved '+plat+' placement\n').encode();members[alias]=reader.put('/packet/'+alias,raw);reader.put('/current/'+plat+'/Project.src',raw);placement[plat]=alias
        packet={'anonymous_group':'Case00-X','fixed_source_file_count':2,'source_files':sources,'contracts':contracts,'production_placement':placement}
        members['PACKET.json']=reader.put('/packet/PACKET.json',encoded(packet));seal={'version':1,'kind':'anonymous-fixed-version-input-seal','anonymous_group':'Case00-X','files':members}
        reference={'path':'/packet/SEAL.json','sha256':reader.put('/packet/SEAL.json',encoded(seal))};bridge='/current/'+family+'/'+platform+'/Bridge.src';config={'source_roots':roots,'bridge':bridge}
        component=roots[0 if platform=='ios' else 1]+'/Widget.src';integration='/current/'+platform+'/Project.src'
        claims=[{'id':owner,'owner':owner,'method':'source','supported':True,'files':{target:sha(reader.files[target])}} for owner,target in [('component',component),('bridge',bridge),('integration',integration)]]
        return reader,reference,config,claims,packet
    def repin(reader,reference,packet):
        seal=json.loads(reader.files[reference['path']]);seal['files']['PACKET.json']=reader.put('/packet/PACKET.json',encoded(packet));reference['sha256']=reader.put(reference['path'],encoded(seal))
    def all_contexts():
        checked=[]
        for family in ['public','private']:
            for platform in ['ios','android']:
                reader,reference,config,claims,packet=fixture(family,platform);before=copy.deepcopy((reader.files,reference,config,claims))
                left=original.derive(reader,reference,'Case00-X',config,claims,family,platform);right=candidate.derive(reader,reference,'Case00-X',config,claims,family,platform)
                need(left==right and (reader.files,reference,config,claims)==before,'Valid aliases or caller changed')
                inventory,aliases,proof=right;need(len(aliases)==3 and not proof['unresolved_roles'],'Expected approved aliases missing')
                need(not any('API.md' in key for key in aliases),'Normative API aliased')
                component='source/'+('0' if platform=='ios' else '1')+'/Widget.src';need(aliases[component] in claims[0]['files'],'Stable source index moved')
                actual=[{'id':claim['id'],'observed':False if claim['owner']=='integration' else True,'reason':'Synthetic source observation','citations':[{'path':next(alias for alias,target in aliases.items() if target in claim['files']),'line':1}]} for claim in claims]
                submission,ledger=projection.source_rows(claims,actual,inventory,aliases,reader);need([r['observed'] for r in submission['observations']]==[True,True,False],'Actual-only integration changed actuals')
                checked.append([family,platform])
        return {'contexts':checked,'stable_root_indices':2,'valid_actuals_unchanged_in_separately_pinned_projection':True}
    case('both families/platforms exact stable aliases and actual-only integration',all_contexts)
    def unapproved_bridge():
        reader,reference,config,claims,packet=fixture();claims[1]['supported']=False
        old=original.derive(reader,reference,'Case00-X',config,claims,'private','ios');new=candidate.derive(reader,reference,'Case00-X',config,claims,'private','ios')
        need(not old[2]['unresolved_roles'] and old[:2]==new[:2],'Original metadata gap not reproduced')
        need(any(row['role']=='actual-bridge-source' for row in new[2]['unresolved_roles']),'Unapproved bridge not explicit')
        observations.append({'original_missing_unresolved_role':'selected bridge present but provider unsupported','original_aliases':old[1],'original_unresolved_roles':old[2]['unresolved_roles']})
        return {'no_new_alias_or_obligation':old[:2]==new[:2],'unsupported_bridge_explicit':True}
    case('unapproved selected bridge omission explicitly recorded without new alias',unapproved_bridge)
    def absent_placement():
        reader,reference,config,claims,packet=fixture();packet['production_placement'].pop('ios');repin(reader,reference,packet)
        old=original.derive(reader,reference,'Case00-X',config,claims,'private','ios');new=candidate.derive(reader,reference,'Case00-X',config,claims,'private','ios')
        need(not old[2]['unresolved_roles'] and old[:2]==new[:2] and any(x['role']=='production-placement' for x in new[2]['unresolved_roles']),'Missing placement diagnostic not explicit')
        observations.append({'original_missing_unresolved_role':'no selected-platform placement copy','original_unresolved_roles':old[2]['unresolved_roles']})
        return {'only_unresolved_metadata_changed':True}
    case('missing original placement remains explicit unresolved',absent_placement)
    def ambiguities():
        reader,reference,config,claims,packet=fixture();extra=copy.deepcopy(claims[-1]);extra['files']={'/another/Project.src':next(iter(extra['files'].values()))};claims.append(extra)
        inventory,aliases,proof=candidate.derive(reader,reference,'Case00-X',config,claims,'private','ios');need('source/placement/ios/Project.src' not in aliases and proof['unresolved_roles'][0]['candidate_count']==2,'Arbitrary integration chosen')
        claims.pop();conflict=copy.deepcopy(claims[0]);conflict['files'][next(iter(conflict['files']))]='0'*64;claims.append(conflict)
        return {'ambiguous_integration_left_unresolved':True,'conflicting_approved_hashes_rejected':reject(lambda:candidate.derive(reader,reference,'Case00-X',config,claims,'private','ios'))}
    case('ambiguous integration bytes and conflicting current subjects never guess',ambiguities)
    def indices():
        errors=[]
        for key in ['2/Widget.src','00/Widget.src','-1/Widget.src','0/../Widget.src','0/.git/Widget.src']:
            reader,reference,config,claims,packet=fixture();packet['source_files']={key:packet['source_files']['0/Widget.src']};packet['fixed_source_file_count']=1;repin(reader,reference,packet)
            errors.append(reject(lambda:candidate.derive(reader,reference,'Case00-X',config,claims,'private','ios')))
        return errors
    case('stable root index bounds and unsafe source members reject',indices)
    def wrong_pins():
        errors=[]
        for change in ['group','copy','current','bridge','count','bytes']:
            reader,reference,config,claims,packet=fixture();group='Case00-Y' if change=='group' else 'Case00-X'
            if change=='copy':reader.files['/packet/source/0/Widget.src']+=b'changed\n'
            elif change=='current':reader.files['/current/iOS/Widget.src']+=b'changed\n'
            elif change=='bridge':reader.files[config['bridge']]=b'normative source substitute\n';claims[1]['files'][config['bridge']]=sha(reader.files[config['bridge']])
            elif change=='count':packet['fixed_source_file_count']=1;repin(reader,reference,packet)
            elif change=='bytes':packet['source_files']['0/Widget.src']['bytes']+=1;repin(reader,reference,packet)
            errors.append(reject(lambda:candidate.derive(reader,reference,group,config,claims,'private','ios')))
        return errors
    case('own group copied/current/bridge bytes and original count/length pinned',wrong_pins)
    def role_unknown_projection():
        reader,reference,config,claims,packet=fixture();claims[1]['supported']=False
        inventory,aliases,proof=candidate.derive(reader,reference,'Case00-X',config,claims,'private','ios')
        actual=[{'id':'bridge','observed':True,'reason':'Synthetic unsupported supplied actual','citations':[{'path':packet['contracts']['private']['ios']['bridge'],'line':1}]}]
        submission,ledger=projection.source_rows(claims,actual,inventory,aliases,reader);need('bridge' not in {r['id'] for r in submission['observations']} and ledger['records'][1]['original_actual']['observed'] is True and ledger['records'][1]['binding']=='unsupported-compiled-provider','Unsupported source promoted or raw statement lost')
        return {'unsupported_provider_U_delegated_to_frozen_claim_audit':True,'raw_actual_retained_in_projection_proof':True}
    case('missing alias never supplies unsupported actual or hides raw statement',role_unknown_projection)
    def original_unchanged():
        need(sha((HERE.parent/'operators/source_aliases.py').read_bytes())==pins['source_aliases.py']['sha256'],'Original source edited')
        return {'source_unchanged':True,'caller_authentication_full_namespace_and_capture_eligibility_are_external':True}
    case('original author source unchanged and authentication limits explicit',original_unchanged)
    value={'version':1,'kind':'independent-synthetic-source-copy-alias-review','passed':sum(x['status']=='passed' for x in controls),'failed':sum(x['status']=='failed' for x in controls),'controls':controls,'author_tests':author_results,'retained_metadata_diagnostics':observations,
           'original_source_sha256':sha((HERE/'vendor/source_aliases.py').read_bytes()),'candidate_sha256':sha((HERE/'source_aliases_v2.py').read_bytes()),'actual_data_reads_or_dispatch':False,'source_criteria_or_original_values_changed':False,
           'scope':'Pure whole-file alias/diagnostic metadata and synthetic actual-only adapter integration, not product/source truth, complete current namespace, capture eligibility or new observations.',
           'limits':['Caller externally authenticates base seal, group/reveal, config/compiled claims and source scope. This adapter cannot authorize them.',
                     'Only listed source-copy identities are verified; full packet/namespace closure and live capture eligibility remain the unchanged controller/binders responsibility.',
                     'Unresolved-role metadata is diagnostic; it adds no source obligation, actual, expected value, unit, P/F/U grade or product credit.']}
    save(HERE/'RESULT.json',value);print(json.dumps({'passed':value['passed'],'failed':value['failed'],'author_tests':author_results,'result_sha256':sha((HERE/'RESULT.json').read_bytes()),'files':sum(p.is_file() for p in HERE.rglob('*'))}))
    raise SystemExit(0 if value['failed']==0 and all(r['passed'] for r in author_results) else 1)


if __name__=='__main__':main()
