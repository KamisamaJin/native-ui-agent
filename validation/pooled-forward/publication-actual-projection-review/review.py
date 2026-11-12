"""Small synthetic actual-format review. No actual study body reads."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import sys
import traceback
import unittest

HERE=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
    if not ok:raise AssertionError(message)
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
def encoded(value):return (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def save(path,value):path.write_bytes(encoded(value));path.chmod(0o444)


def main():
    need(not (HERE/'RESULT.json').exists(),'Fresh retained result required')
    pins=json.loads((HERE/'SOURCE-PINS.json').read_bytes())
    for name,ref in pins.items():need(sha((HERE/'vendor'/name).read_bytes())==ref['sha256'],'Frozen source differs')
    original=load(HERE/'vendor/actual_projection.py','author_projection');reviewed=load(HERE/'actual_projection_v2.py','review_projection')
    archive=load(HERE/'vendor/archive.py','projection_archive');resolver=load(HERE/'vendor/resolver.py','projection_resolver')
    sys.path.insert(0,str(HERE/'vendor'));tests=load(HERE/'vendor/test_actual_projection.py','author_projection_controls')
    author_runs=[]
    for name,module in [('original',original),('revision',reviewed)]:
        tests.module=module
        with (HERE/'HOST'/('author-'+name+'.log')).open('x') as stream:
            result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        author_runs.append({'backend':name,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()})
    controls=[];observations=[]
    def case(name,fn):
        try:controls.append({'name':name,'status':'passed','evidence':fn()})
        except BaseException as error:controls.append({'name':name,'status':'failed','error_type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
    def rejected(fn):
        try:fn()
        except ValueError as error:return str(error)
        raise AssertionError('Malformed actual-only input accepted')
    def fixture():return tests.fixture()
    def unchanged():
        reader,claims,inventory,aliases,rows=fixture();before=copy.deepcopy((claims,inventory,aliases,rows))
        left=original.source_rows(claims,rows,inventory,aliases,reader);right=reviewed.source_rows(claims,rows,inventory,aliases,reader)
        need(left==right and (claims,inventory,aliases,rows)==before,'Valid actual or caller changed')
        need([r['observed'] for r in right[0]['observations']]==[True,False],'Valid Boolean changed')
        return {'valid_true_false_unchanged':True,'inputs_preserved':True}
    case('valid source actuals equivalent to author and caller preserved',unchanged)
    def owners():
        checked=[]
        for owner,kind in [('component','production-source'),('bridge','actual-bridge-source'),('integration','production-placement'),('integration','integration-source')]:
            reader,claims,inventory,aliases,rows=fixture();claims[0]['owner']=owner;inventory['source/A.swift']['kind']=kind
            result,_=reviewed.source_rows(claims,rows,inventory,aliases,reader);need(result['observations'][0]['observed'] is True,'Approved role lost')
            inventory['source/A.swift']['kind']='normative-api-document';result,proof=reviewed.source_rows(claims,rows,inventory,aliases,reader)
            need(result['observations'][0]['observed'] is None and result['observations'][1]['observed'] is False,'Role mismatch promoted or affected sibling')
            checked.append([owner,kind])
        return checked
    case('component bridge integration require exact authenticated subject kinds',owners)
    def alias_and_lines():
        details=[]
        for change in ['unknown-alias','foreign-subject','wrong-inventory-hash','boolean-line','zero-line','beyond-line','changed-bytes','invalid-utf8']:
            reader,claims,inventory,aliases,rows=fixture();rows[0]['observed']=False
            if change=='unknown-alias':rows[0]['citations'][0]['path']='unproved/A.swift'
            elif change=='foreign-subject':aliases['source/A.swift']='/current/B.swift'
            elif change=='wrong-inventory-hash':inventory['source/A.swift']['sha256']='0'*64
            elif change=='boolean-line':rows[0]['citations'][0]['line']=True
            elif change=='zero-line':rows[0]['citations'][0]['line']=0
            elif change=='beyond-line':rows[0]['citations'][0]['line']=999
            elif change=='changed-bytes':reader.files['/current/A.swift']+=b'changed\n'
            else:
                reader.files['/current/A.swift']=b'\xff';digest=sha(reader.files['/current/A.swift']);claims[0]['files']['/current/A.swift']=digest;inventory['source/A.swift']['sha256']=digest
            result,proof=reviewed.source_rows(claims,rows,inventory,aliases,reader)
            need(result['observations'][0]['observed'] is None and proof['records'][0]['original_actual']['observed'] is False and result['observations'][1]['observed'] is False,'Unbound false hidden/promoted or sibling lost')
            details.append(change)
        return {'invalid_inputs':details,'raw_false_retained':True,'other_valid_false_unchanged':True}
    case('alias line hash UTF8 errors isolate U and preserve raw false claim',alias_and_lines)
    def unknowns():
        reader,claims,inventory,aliases,rows=fixture();rows[0].update(observed=None,citations=[])
        result,proof=reviewed.source_rows(claims,rows,inventory,aliases,reader);need(result['observations'][0]['observed'] is None,'Null actual promoted')
        rows=rows[1:];result,proof=reviewed.source_rows(claims,rows,inventory,aliases,reader);need(result['observations'][0]['observed'] is None and proof['records'][0]['original_actual'] is None,'Missing actual promoted')
        claims[0].update(supported=False,unsupported_reason='Synthetic unsupported provider');result,proof=reviewed.source_rows(claims,rows,inventory,aliases,reader)
        need([r['id'] for r in result['observations']]==['b'] and proof['records'][0]['binding']=='unsupported-compiled-provider','Unsupported provider submitted as pass')
        return {'null_missing_unsupported_keep_unknown':True}
    case('null missing and unsupported provider remain explicit unknown',unknowns)
    def schema():
        messages=[]
        for change in ['expected','unit','duplicate','foreign-id']:
            reader,claims,inventory,aliases,rows=fixture()
            if change in ['expected','unit']:rows[0][change]=False if change=='expected' else 'invented'
            elif change=='duplicate':rows.append(copy.deepcopy(rows[0]))
            else:rows[0]['id']='foreign'
            messages.append(rejected(lambda:reviewed.source_rows(claims,rows,inventory,aliases,reader)))
        return messages
    case('actual-only schemas forbid expected unit duplicate and unknown IDs',schema)

    # Remaining visual and genuine frozen reader controls are below.
    context={'catalog_sha256':'a'*64,'observation_sha256':'b'*64}
    visual=[{'review_id':'r1','actual':False,'reason':'Synthetic visible counterexample','snapshot_indices':[1]},
            {'review_id':'r2','actual':True,'reason':'Synthetic original state','snapshot_indices':[2]}]
    def visual_valid():
        before=copy.deepcopy((context,visual));left=original.visual_rows(['r1','r2'],visual,context,context,{'r1':{1},'r2':{2}});right=reviewed.visual_rows(['r1','r2'],visual,context,context,{'r1':{1},'r2':{2}})
        need(left==right and (context,visual)==before,'Visual actuals or input mutated')
        need([r['actual'] for r in right[0]['decisions']]==[False,True],'Visual Boolean changed')
        return {'original_false_true_unchanged':True,'context_preserved':True}
    case('valid visual actuals and contexts equal author unchanged',visual_valid)
    def visual_bad_frames():
        checked=[]
        for indices in [[1],[2,2],[True],[],[-1],[[2]]]:
            rows=copy.deepcopy(visual);rows[1]['snapshot_indices']=indices
            result,proof=reviewed.visual_rows(['r1','r2'],rows,context,context,{'r1':{1},'r2':{2}})
            need(result['decisions'][0]['actual'] is False and result['decisions'][1]['actual'] is None and proof['records'][1]['original_actual']['actual'] is True,'Invalid visual promoted or other false hidden')
            checked.append(indices)
        return checked
    case('wrong state duplicate bool absent negative unhashable frames stay U',visual_bad_frames)
    def visual_context():
        wrong=dict(context,observation_sha256='c'*64)
        errors=[rejected(lambda:reviewed.visual_rows(['r1','r2'],visual,wrong,context,{'r1':{1},'r2':{2}})),
                rejected(lambda:reviewed.visual_rows(['r1','r1'],visual,context,context,{'r1':{1}}))]
        for key in ['expected','unit']:
            rows=copy.deepcopy(visual);rows[0][key]=None;errors.append(rejected(lambda:reviewed.visual_rows(['r1','r2'],rows,context,context,{'r1':{1},'r2':{2}})))
        result,proof=reviewed.visual_rows(['r1','r2'],visual[:1],context,context,{'r1':{1},'r2':{2}});need(result['decisions'][1]['actual'] is None and proof['records'][1]['original_actual'] is None,'Missing visual inferred')
        return {'bad_context_duplicate_and_schema_rejected':errors,'missing_actual_U':True}
    case('visual context cannot be rewritten missing observations not inferred',visual_context)
    def genuine_reader():
        source=HERE/'HOST/source';source.mkdir();files={'A.swift':b'first synthetic line\nsecond synthetic line\n','B.swift':b'other synthetic source\n'}
        for name,raw in files.items():(source/name).write_bytes(raw)
        rows=[]
        for name,raw in files.items():
            path=source/name;rows.append({'root':'source','path':str(path),'logical_path':'source/'+name,'sha256':sha(raw),'bytes':len(raw),'mode':format(stat.S_IMODE(path.stat().st_mode),'04o')})
        spec_path=HERE/'HOST/SPEC.json';save(spec_path,{'version':1,'roots':[{'id':'source','kind':'evidence','path':str(source)}],'files':rows})
        packed=archive.pack(spec_path,HERE/'HOST/archive',1);restored=archive.restore(HERE/'HOST/archive',HERE/'HOST/restored',packed['index_sha256'],readonly=True)
        mapping=Path(restored['mapping']);reader=resolver.Resolver(mapping,map_sha256=sha(mapping.read_bytes()),index_sha256=packed['index_sha256'])
        claims=[{'id':name,'method':'source','owner':'component','supported':True,'files':{str(source/file):sha(files[file])}} for name,file in [('a','A.swift'),('b','B.swift')]]
        inventory={'packet/'+file:{'sha256':sha(raw),'kind':'production-source'} for file,raw in files.items()};aliases={'packet/'+file:str(source/file) for file in files}
        actual=[{'id':name,'observed':value,'reason':'Synthetic sealed source actual','citations':[{'path':'packet/'+file,'line':1}]} for name,file,value in [('a','A.swift',True),('b','B.swift',False)]]
        source.rename(HERE/'HOST/removed-original-source')
        valid,_=reviewed.source_rows(claims,actual,inventory,aliases,reader);need([r['observed'] for r in valid['observations']]==[True,False],'Frozen Reader valid actuals changed')
        physical=reader.file(str(source/'A.swift'));raw=physical.read_bytes();physical.chmod(0o644);physical.write_bytes(b'X'+raw[1:]);physical.chmod(0o444)
        try:original.source_rows(claims,actual,inventory,aliases,reader)
        except ValueError as error:observations.append({'author_batch_abort_on_real_reader_integrity_error':str(error)})
        else:raise AssertionError('Author isolation boundary was not reproduced')
        before=copy.deepcopy(actual);projected,proof=reviewed.source_rows(claims,actual,inventory,aliases,reader)
        need(projected['observations'][0]['observed'] is None and projected['observations'][1]['observed'] is False,'Real reader failure did not isolate U')
        need(proof['records'][0]['original_actual']['observed'] is True and actual==before,'Raw actual lost or rewritten')
        return {'archive_index_sha256':packed['index_sha256'],'restore_map_sha256':sha(mapping.read_bytes()),'original_paths_absent':True,
                'real_resolver_corruption_rejected':observations[-1],'revision_bad_row_U_other_false_retained':True,
                'final_restored_source_intentionally_corrupt_after_verified_positive':True,'not_a_source_or_product_quality_verdict':True}
    case('genuine frozen Resolver integrity failure isolated after demonstrated author abort',genuine_reader)
    def original_unchanged():
        need(sha((HERE.parent/'operators/actual_projection.py').read_bytes())==pins['actual_projection.py']['sha256'],'Original source changed')
        return {'root_original_unchanged':True,'caller_authentication_not_supplied_or_selfapproved_by_adapter':True}
    case('original frozen source unchanged and external authority explicit',original_unchanged)
    value={'version':1,'kind':'independent-synthetic-actual-format-projection-review','passed':sum(c['status']=='passed' for c in controls),'failed':sum(c['status']=='failed' for c in controls),
        'author_tests':author_runs,'controls':controls,'retained_development_findings':observations,
        'code_sha256':{'original':sha((HERE/'vendor/actual_projection.py').read_bytes()),'revision':sha((HERE/'actual_projection_v2.py').read_bytes()),'tests':sha(Path(__file__).read_bytes())},
        'actual_study_body_reads_or_dispatch':False,'source_or_criteria_mutated':False,'backend_product_evaluation_claim':False,
        'scope':'Common actual-only format/isolation checks, not new observations or authentication. Real frozen archive/Resolver used with two synthetic text subjects, no PNG or actual source.',
        'limits':['Caller must externally authenticate consensus, compiled claims, inventory aliases, original observation/catalog and frozen allowed state frames.',
                  'An authenticated current-source inventory is not a source truth oracle. Invalid citations remain U; original supplied actuals stay in the projection proof.',
                  'Original frozen binders and failures remain authoritative; no product result, expected value, unit, actual or full-content evidence is invented.']}
    save(HERE/'RESULT.json',value);print(json.dumps({'passed':value['passed'],'failed':value['failed'],'author_runs':author_runs,'result_sha256':sha((HERE/'RESULT.json').read_bytes()),'files':sum(p.is_file() for p in HERE.rglob('*'))}))
    raise SystemExit(0 if value['failed']==0 and all(r['passed'] for r in author_runs) else 1)


if __name__=='__main__':main()
