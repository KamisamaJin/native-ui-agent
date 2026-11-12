"""Finite synthetic matcher-preparation API review; no actual study inputs."""
import ast
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
AUTHOR_SHA = '32c1ad36c57e4623bfa920f8688a0bb377ed87a5d5c49d4234f14f2f43dc1092'
DISPATCH_FREEZE = 'd3ec147a4c91562cc2624c9c41cfb03345f2927c9cf0527344b325b49e899184'
BATCH_FREEZE = '704d360588ae6b22f36ff3852bb1f5fec516bd82375e51b16beba933ea940d84'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok, why):
    if not ok:raise ValueError(why)
def encoded(value):return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)+'\n').encode()
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path);module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class Reader:
    def __init__(self, inventories, overlay=None):
        self.inventories = inventories;self.overlay = {} if overlay is None else overlay;self.reads = []
    def clone(self):return Reader(self.inventories, dict(self.overlay))
    def read_bytes(self, original):
        path = Path(original);need(path.is_absolute() and '..' not in path.parts, 'Synthetic canonical original key required')
        self.reads.append(str(path))
        if str(path) in self.overlay:return self.overlay[str(path)]
        roots = [p for p in self.inventories if path.is_relative_to(p)]
        need(roots, 'Outside declared synthetic namespaces')
        root = max(roots, key=lambda p:len(p.parts));need(not any(p.is_symlink() for p in [path,*path.parents]), 'Synthetic symlink forbidden')
        raw = path.read_bytes();expected = self.inventories[root]
        if expected is not None:
            key = path.relative_to(root).as_posix();need(key in expected and sha(raw) == expected[key], 'Borrowed frozen synthetic input changed')
        return raw
    def directory(self, original):
        path = Path(original);need(path.is_absolute() and any(path.is_relative_to(root) for root in self.inventories), 'Outside declared synthetic directories')
        need(path.is_dir() and not any(p.is_symlink() for p in [path,*path.parents]), 'Synthetic regular directory required')
        return path


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--tag',default='');args=parser.parse_args()
    need(not args.tag or (args.tag.isascii() and args.tag.isalnum()),'Fresh simple run tag required')
    suffix='-'+args.tag if args.tag else '';result_path=HERE/('RESULT'+suffix+'.json')
    need(not result_path.exists(), 'Fresh one-shot result required')
    pins = json.loads((HERE/'SOURCE-PINS.json').read_bytes())
    for name,ref in pins.items():need(sha((HERE/'vendor'/name).read_bytes()) == ref['sha256'], 'Vendored source pin differs')
    need(sha((HERE/'vendor/prepare_matcher_input.py').read_bytes()) == AUTHOR_SHA, 'Author source differs')
    sys.path.insert(0,str(HERE/'vendor'));phase = load(HERE/'vendor/phase_barriers.py','review_pinned_phase')
    candidate = load(HERE/'prepare_matcher_input_v2.py','review_matcher_v2')
    batch = ROOT/'publication-batch-review';dispatch = ROOT/'publication-dispatch-review'
    raw = (batch/'REVIEW-FREEZE.json').read_bytes();need(sha(raw) == BATCH_FREEZE, 'External batch freeze differs')
    inventory = json.loads(raw)['files_excluding_this_freeze'];batch_inv = {p:r['sha256'] for p,r in inventory.items()}
    raw = (dispatch/'FREEZE.json').read_bytes();need(sha(raw) == DISPATCH_FREEZE, 'External dispatch freeze differs')
    dispatch_inv = json.loads(raw)['files']
    reader = Reader({batch:batch_inv,dispatch:dispatch_inv,HERE:None})
    def reference(path):return {'path':str(path),'sha256':sha(reader.read_bytes(str(path)))}
    refs = phase.original(reader,reference(dispatch/'SYNTHETIC/REFS.json'))
    cause = phase.original(reader,refs['cause_ref']);packets = phase.original(reader,refs['packets_ref'])
    causes = {r['group']:r for r in cause['groups']};packet_rows = {r['group']:r for r in packets['groups']}
    # Extract exact author AST statements, not a handwritten weaker emulation.
    tree = ast.parse((HERE/'vendor/prepare_matcher_input.py').read_bytes());author_main = next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name == 'main')
    packet_ast = copy.deepcopy(next(x for x in author_main.body if isinstance(x,ast.FunctionDef) and x.name == 'verify_packet'))
    loop = next(x for x in author_main.body if isinstance(x,ast.For) and ast.unparse(x.iter) == "alarm['groups']")
    bind = copy.deepcopy(loop.body[2:7]);need([ast.unparse(x).split('=')[0].strip() for x in bind[:2]] == ['base_refs','alarm_refs'], 'Author AST selection changed')
    bind += [ast.Return(value=ast.Tuple(elts=[ast.Name(id='base_ref',ctx=ast.Load()),ast.Name(id='alarm_packet_ref',ctx=ast.Load())],ctx=ast.Load()))]
    bind_ast = ast.FunctionDef(name='author_bind',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=n) for n in ['original','row','group']],kwonlyargs=[],kw_defaults=[],defaults=[]),body=bind,decorator_list=[])
    judge_loop = next(x for x in loop.body if isinstance(x,ast.For))
    history_body = copy.deepcopy(judge_loop.body[:4]);history_body.append(ast.Return(value=ast.Name(id='historical',ctx=ast.Load())))
    history_ast = ast.FunctionDef(name='author_history',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=n) for n in ['original','group','judge']],kwonlyargs=[],kw_defaults=[],defaults=[]),body=history_body,decorator_list=[])
    env = {'Path':Path,'phase':phase,'reader':reader,'sha':sha,'need':need,'ref':reference}
    extracted = ast.fix_missing_locations(ast.Module(body=[packet_ast,bind_ast,history_ast],type_ignores=[]));exec(compile(extracted,'exact-author-AST','exec'),env)
    root = HERE/('SYNTHETIC'+suffix);root.mkdir()
    def put(path,value=None,raw=None):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded(value) if raw is None else raw);path.chmod(0o444);return reference(path)
    def base_packet(folder, group):
        members={'PACKET.json':encoded({'version':1,'anonymous_group':group,'scope':'Different synthetic base bytes; no product proposition'}),
                 'GRADE-TEMPLATE.json':encoded({'version':1,'anonymous_group':group}),'INSTRUCTIONS.md':b'SYNTHETIC instructions\n'}
        files={name:put(folder/name,raw=raw)['sha256'] for name,raw in members.items()}
        return put(folder/'SEAL.json',{'version':1,'kind':'anonymous-fixed-version-input-seal','anonymous_group':group,'files':files})
    alternate = base_packet(root/'alternate-base','Case01-I')
    empty = put(root/'header-only/SEAL.json',{'version':1,'kind':'anonymous-fixed-version-input-seal','anonymous_group':'Case01-I','files':{}})
    observations=[];controls=[];hostiles=[]
    def case(name,fn):
        try:controls.append({'name':name,'status':'passed','evidence':fn()})
        except BaseException as error:controls.append({'name':name,'status':'failed','error_type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
    def reject(fn, text):
        try:fn()
        except (ValueError,KeyError,FileNotFoundError) as error:
            need(text in str(error),'Wrong rejecting boundary: '+str(error));return str(error)
        raise AssertionError('Hostile synthetic record accepted')
    def admission(label, value):observations.append({'author_v1_admitted':label,'returned':value})
    def positive_cause():
        result=phase.verify_index(reader,refs['cause_ref'],'cause');need(result['status']=='verified' and result['groups']==15 and result['distinct_contexts']==30,'Borrowed original cause fixture failed')
        return {'groups':15,'contexts':30,'scope':'Genuine frozen record verifier, synthetic grade identity bodies only; no alarm barrier claimed'}
    case('genuine cached all15 cause/30-context record barrier',positive_cause)
    def all_packets():
        groups=[]
        for group,row in causes.items():
            base=row['inputs'][0];alarm=packet_rows[group]['packet_seal'];alarm_row={'inputs':[base,alarm]}
            got=candidate.group_packets(phase,reader,row,alarm_row,group);need(got==(base,alarm),'Returned packet ref changed');groups.append(group)
        return {'groups':len(groups),'base_and_alarm_packets':2*len(groups),'scope':'Exact cached packet bytes; not a synthetic all30 alarm role barrier or full CLI'}
    case('all15 genuine base and alarm packet inventories and identities',all_packets)
    def empty_control():
        admitted=env['verify_packet'](empty,'Case01-I','anonymous-fixed-version-input-seal');admission('header-only base with no core members',admitted)
        return reject(lambda:candidate.verify_packet(phase,reader,empty,'Case01-I','anonymous-fixed-version-input-seal'),'Packet core members')
    case('header-only packet author admission then v2 rejection',empty_control)
    group='Case01-I';original=causes[group];alarm_ref=packet_rows[group]['packet_seal'];normal_alarm={'inputs':[original['inputs'][0],alarm_ref]}
    def mismatched_base():
        alarm_row={'inputs':[alternate,alarm_ref]};admitted=env['author_bind'](original,alarm_row,group);admission('alarm context different same-group original base',admitted)
        return reject(lambda:candidate.group_packets(phase,reader,original,alarm_row,group),'exact original base reference')
    case('exact cause/alarm original base binding',mismatched_base)
    def repinned_member(reference, member, changes, kind, label):
        clone=reader.clone();seal=phase.original(reader,reference);folder=Path(reference['path']).parent
        document=phase.original(reader,{'path':str(folder/member),'sha256':seal['files'][member]});document.update(changes);raw=encoded(document)
        clone.overlay[str(folder/member)]=raw;seal['files'][member]=sha(raw);seal_raw=encoded(seal);clone.overlay[reference['path']]=seal_raw;new_ref={'path':reference['path'],'sha256':sha(seal_raw)}
        saved=env['reader'];env['reader']=clone
        try:admission(label,env['verify_packet'](new_ref,group,kind))
        finally:env['reader']=saved
        hostiles.append({'name':label,'registered_original_overlays':{str(folder/member):raw.decode(),reference['path']:seal_raw.decode()},'repinned_ref':new_ref})
        return reject(lambda:candidate.verify_packet(phase,clone,new_ref,group,kind),'core member group differs')
    case('repinned base PACKET wrong-group rejected',lambda:repinned_member(alternate,'PACKET.json',{'anonymous_group':'Case02-X'},'anonymous-fixed-version-input-seal','wrong-group sealed base PACKET'))
    case('repinned base template wrong-group rejected',lambda:repinned_member(alternate,'GRADE-TEMPLATE.json',{'anonymous_group':'Case02-X'},'anonymous-fixed-version-input-seal','wrong-group sealed base template'))
    case('repinned alarm PACKET wrong-group rejected',lambda:repinned_member(alarm_ref,'PACKET.json',{'anonymous_group':'Case02-X'},'anonymous-alarm-material-seal','wrong-group sealed alarm PACKET'))
    def corrupt():
        clone=reader.clone();seal=phase.original(reader,alarm_ref);path=str(Path(alarm_ref['path']).parent/'INSTRUCTIONS.md');clone.overlay[path]=b'changed synthetic instructions\n'
        return reject(lambda:candidate.verify_packet(phase,clone,alarm_ref,group,'anonymous-alarm-material-seal'),'Input bytes differ')
    case('changed member with unchanged seal still rejected',corrupt)
    def duplicate_base():
        duplicate=copy.deepcopy(normal_alarm);duplicate['inputs'].append(original['inputs'][0])
        return reject(lambda:candidate.group_packets(phase,reader,original,duplicate,group),'Exactly one')
    case('duplicate base references do not collapse silently',duplicate_base)
    # Four genuine own-role directories and two pinned original pair ENDs.
    firsts={};currents={}
    for judge in ['J1','J2']:
        for phase_name,dest in [('cause',firsts),('cause-supplement',currents)]:
            folder=root/'lineage'/judge/phase_name;grade=put(folder/'grade.json',{'anonymous_group':group,'judge_id':judge,'scope':'Synthetic role identity, no product conclusion'})
            dest[judge]=put(folder/'SEAL.json',{'version':1,'kind':'independent-blind-cause-grade-seal','anonymous_group':group,'judge_id':judge,'files':{'grade.json':grade['sha256']}})
    first_start=put(root/'lineage/original-START.json',{'anonymous_group':group,'judges':['J1','J2']})
    second_start=put(root/'lineage/supplement-START.json',{'anonymous_group':group,'judges':['J1','J2']})
    initial_end=put(root/'lineage/original-END.json',{'version':1,'kind':'parallel-original-cause-episode-sealed','anonymous_group':group,'start':first_start,'independent_original_grade_seals':firsts})
    supplement_end=put(root/'lineage/supplement-END.json',{'version':1,'kind':'parallel-source-contract-supplement-episode-sealed','anonymous_group':group,'start':second_start,'grade_seals':currents})
    aggregate_value={'version':1,'kind':'independent-cause-version-final-seal-index','anonymous_group':group,'grade_seals':currents,'original_episode':initial_end,'complete_input_supplement_episode':supplement_end}
    aggregate=put(root/'lineage/aggregate-END.json',aggregate_value);lineage={'seals':currents,'episode_end':aggregate}
    def complete_lineage():
        result={j:candidate.earlier_causes(phase,reader,lineage,group,j) for j in ['J1','J2']};need(result=={j:[firsts[j]] for j in firsts},'Historical original ref not retained')
        return result
    case('genuine pinned original and supplement episodes retain both original roles',complete_lineage)
    def unregistered_history():
        clone=reader.clone();no_lineage={'anonymous_group':group,'grade_seals':currents};raw=encoded(no_lineage);clone.overlay[aggregate['path']]=raw
        row={'seals':currents,'episode_end':{'path':aggregate['path'],'sha256':sha(raw)}}
        admission('unregistered existing earlier first seal is live-hashed',env['author_history'](row,group,'J1'))
        hostiles.append({'name':'missing predecessor refs','overlay':no_lineage})
        return reject(lambda:candidate.earlier_causes(phase,clone,row,group,'J1'),'Pinned original/supplement cause lineage')
    case('existing first cause cannot self-authorize without pinned episode lineage',unregistered_history)
    def missing_first():
        folder=Path(firsts['J1']['path']).parent;retained=folder.with_name('retained-absent-cause');folder.rename(retained)
        try:
            returned=env['author_history'](lineage,group,'J1');need(returned==[],'Author did not skip missing first');admission('missing earlier original silently omitted',returned)
            return reject(lambda:candidate.earlier_causes(phase,reader,lineage,group,'J1'),'No such file')
        finally:retained.rename(folder)
    case('missing earlier original blocks rather than disappearing',missing_first)
    def effective_ref_change():
        clone=reader.clone();wrong=phase.original(reader,supplement_end);wrong['grade_seals']=firsts;raw=encoded(wrong);clone.overlay[supplement_end['path']]=raw
        changed=copy.deepcopy(aggregate_value);changed['complete_input_supplement_episode']={'path':supplement_end['path'],'sha256':sha(raw)};raw2=encoded(changed);clone.overlay[aggregate['path']]=raw2
        row={'seals':currents,'episode_end':{'path':aggregate['path'],'sha256':sha(raw2)}}
        return reject(lambda:candidate.earlier_causes(phase,clone,row,group,'J1'),'changes effective cause refs')
    case('supplement END must bind exact effective role refs',effective_ref_change)
    def changed_first_pin():
        clone=reader.clone();old=phase.original(reader,firsts['J1']);old['unregistered_metadata']=True;raw=encoded(old);clone.overlay[firsts['J1']['path']]=raw
        saved=env['reader'];env['reader']=clone
        # The nested original ref closure hashes through the same reader global.
        saved_ref=env['ref'];env['ref']=lambda path:{'path':str(path),'sha256':sha(clone.read_bytes(str(path)))}
        try:admission('changed earlier seal accepted through a fresh live hash',env['author_history'](lineage,group,'J1'))
        finally:env['reader']=saved;env['ref']=saved_ref
        hostiles.append({'name':'changed prior seal','original_overlay':{firsts['J1']['path']:raw.decode()}})
        return reject(lambda:candidate.earlier_causes(phase,clone,lineage,group,'J1'),'Original review/input bytes differ')
    case('changed earlier seal cannot replace the original episode pin',changed_first_pin)
    def unknown_lineage():
        clone=reader.clone();changed=phase.original(reader,initial_end);changed['kind']='unknown-historical-end';raw=encoded(changed);clone.overlay[initial_end['path']]=raw
        aggregate2=copy.deepcopy(aggregate_value);aggregate2['original_episode']={'path':initial_end['path'],'sha256':sha(raw)};raw2=encoded(aggregate2);clone.overlay[aggregate['path']]=raw2
        row={'seals':currents,'episode_end':{'path':aggregate['path'],'sha256':sha(raw2)}}
        return reject(lambda:candidate.earlier_causes(phase,clone,row,group,'J1'),'Unknown or cross-scope')
    case('unregistered historical episode kind blocks',unknown_lineage)
    def wrong_start():
        clone=reader.clone();changed={'anonymous_group':'Case02-X','judges':['J1','J2']};raw=encoded(changed);clone.overlay[first_start['path']]=raw
        end=phase.original(reader,initial_end);end['start']={'path':first_start['path'],'sha256':sha(raw)};raw2=encoded(end);clone.overlay[initial_end['path']]=raw2
        aggregate2=copy.deepcopy(aggregate_value);aggregate2['original_episode']={'path':initial_end['path'],'sha256':sha(raw2)};raw3=encoded(aggregate2);clone.overlay[aggregate['path']]=raw3
        row={'seals':currents,'episode_end':{'path':aggregate['path'],'sha256':sha(raw3)}}
        return reject(lambda:candidate.earlier_causes(phase,clone,row,group,'J1'),'START belongs to another group')
    case('pinned earlier START must retain own anonymous group',wrong_start)
    def alarm_template():
        clone=reader.clone();seal=phase.original(reader,alarm_ref);path=str(Path(alarm_ref['path']).parent/'GRADE-TEMPLATE.json');value=phase.original(reader,{'path':path,'sha256':seal['files']['GRADE-TEMPLATE.json']});value['anonymous_group']=group;raw=encoded(value);clone.overlay[path]=raw
        seal['files']['GRADE-TEMPLATE.json']=sha(raw);raw2=encoded(seal);clone.overlay[alarm_ref['path']]=raw2
        return reject(lambda:candidate.verify_packet(phase,clone,{'path':alarm_ref['path'],'sha256':sha(raw2)},group,'anonymous-alarm-material-seal'),'Fixed prospective alarm controls differ')
    case('alarm template remains exact prospective bytes with null group/judge',alarm_template)
    def projections():
        verified=phase.verify_index(reader,refs['cause_ref'],'cause');before=encoded(verified);projection=candidate.disclosed_barrier(phase,verified)
        need(encoded(verified)==before,'Caller verified proof mutated');need('index' not in projection and refs['cause_ref']['path'] not in encoded(projection).decode(),'Operator index ref leaked')
        need(len(projection['verified_roles'])==15 and projection['verified_roles']==verified['verified_roles'],'Role refs/counts changed')
        extra=copy.deepcopy(verified);extra['operator_episode']={'path':'/synthetic/operator/secret.json'}
        top=reject(lambda:candidate.disclosed_barrier(phase,extra),'Unknown verified barrier projection')
        extra=copy.deepcopy(verified);extra['verified_roles'][0]['roles']['J1']['actor']='/root/private-operator'
        nested=reject(lambda:candidate.disclosed_barrier(phase,extra),'Unknown role projection fields')
        return {'operator_barrier_ref_removed_only_in_new_projection':True,'caller_unchanged':True,'original_role_refs_preserved':30,'unexpected_top_and_nested_private_fields_rejected':[top,nested]}
    case('allowlisted role-only barrier disclosure drops operator refs and preserves caller',projections)
    def author_unmutated():
        need(sha((ROOT/'operators/prepare_matcher_input.py').read_bytes())==AUTHOR_SHA,'Root helper mutated')
        need(sha((batch/'REVIEW-FREEZE.json').read_bytes())==BATCH_FREEZE and sha((dispatch/'FREEZE.json').read_bytes())==DISPATCH_FREEZE,'Borrowed freeze mutated')
        # Source checks only: unchanged all30 barriers precede packet disclosure;
        # the fixed five153-member supplement and policy anchors remain literal.
        source=(HERE/'prepare_matcher_input_v2.py').read_text()
        need(source.index("cause_verified = phase.verify_index")<source.index('groups = []') and source.index("alarm_verified = phase.verify_index")<source.index('groups = []'),'Barrier ordering changed')
        need('9f3bf306a5a57875cfb6149fdf9365b6476599074486f60b1d0c65fb304453bc' in source and 'len(expected) == 153' in source,'Original supplement anchor altered')
        return {'root_and_borrowed_freezes_unchanged':True,'full_cli_and_all30_alarm_barrier_not_executed':True,'supplement_source_checks_only':True}
    case('frozen originals unchanged and full barrier/supplement source checks retained',author_unmutated)
    value={'version':1,'kind':'independent-source-and-synthetic-matcher-preparation-review','author_source_sha256':AUTHOR_SHA,
        'candidate_source_sha256':sha((HERE/'prepare_matcher_input_v2.py').read_bytes()),'borrowed_freezes':{'batch':BATCH_FREEZE,'dispatch':DISPATCH_FREEZE},
        'passed':sum(x['status']=='passed' for x in controls),'failed':sum(x['status']=='failed' for x in controls),'controls':controls,'author_admissions':observations,
        'retained_hostile_inputs':hostiles,'unique_original_synthetic_read_keys':sorted(set(reader.reads)),
        'actual_study_reads_or_dispatch':False,'borrowed_fixture_mutations':False,'full_cli_or_all30_alarm_barrier_claim':False,
        'limits':['Existing all15 cause/30-context and all15 base/alarm byte fixtures are genuine; no completed all30 alarm fixture was manufactured.',
                  'Full CLI, five153-member supplement application and actual final closure remain root-owned checks after all original alarms seal.',
                  'No product truth, actual-grade findings, assignment, cost, source responsibility or freshness is evaluated.']}
    put(result_path,value);print(json.dumps({'passed':value['passed'],'failed':value['failed'],'author_admissions':len(observations),'result_sha256':sha(result_path.read_bytes()),'files':sum(p.is_file() for p in HERE.rglob('*'))}))
    raise SystemExit(0 if value['failed']==0 else 1)


if __name__=='__main__':main()
