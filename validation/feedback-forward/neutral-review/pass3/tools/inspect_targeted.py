from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import time
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]; BASE = ROOT.parents[1]
NEUTRAL = BASE / 'neutral'; SNAPSHOT = BASE / 'development/candidate-attempt-3'; CAP = BASE / 'neutral-targeted'
sys.path.insert(0, str(SNAPSHOT / 'scripts'))
import design_contract as design
import execution_plan
import native_checks
import acceptance

def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v): (ROOT / n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')

def main():
    begun=time.time(); fixed=load(BASE/'operators/targeted-neutral-request.json'); approval=load(NEUTRAL/'APPROVAL.json')
    lock=load(NEUTRAL/'design/lock.json'); plan=load(NEUTRAL/'generated/ordinary400/design/plan.json')
    fixtures=load(NEUTRAL/'inputs/ordinary400.json'); execution=load(CAP/'execution.json'); result=load(CAP/'result.json')
    seal=load(NEUTRAL/'SEAL.json')
    assert all(sha(NEUTRAL/p)==h for p,h in seal['source_and_test_inputs_sha256'].items())
    assert execution==fixed['execution']
    expected=execution_plan.compile_execution(plan,lock,approval['design_lock_sha256'],fixtures,approval['bridge_sha256'],launch_ref={'source':'launch','pointer':'/ordinary400'},states=['replaced'],strategy='coalesced')
    assert expected==execution
    assert load(CAP/'parent-plan.json')==plan and load(CAP/'fixtures.json')==execution['config'] and load(CAP/'actions.json')==execution['actions']
    assert execution_plan.source_fingerprint([NEUTRAL/'source/Bridge.swift'])==load(CAP/'source-before.json')==load(CAP/'source-after.json')
    assert design.digest(load(CAP/'source-before.json'))==result['source_sha256']
    assert sha(CAP/'native/compiled-project/Bridge.swift')==approval['bridge_sha256']
    assert sha(CAP/'native/observation.json')==result['observation_sha256'] and sha(CAP/'automatic.json')==result['automatic_sha256']
    assert all(sha(CAP/p)==h for p,h in result['input_hashes'].items())
    environment=load(CAP/'expected-environment.json'); assert environment==fixed['environment']
    assert design.digest(environment)==fixed['environment_sha256']==result['environment_expectation_sha256']
    obs=load(CAP/'native/observation.json'); manifest=load(CAP/'native/manifest.json')
    env=acceptance.environment(obs,environment,'ios'); assert env==load(CAP/'environment-check.json') and env['status']=='P'
    save('environment-recomputed.json',env)
    report=native_checks.evaluate(plan,obs,'ios',root=CAP/'native',observation_sha256=sha(CAP/'native/observation.json'),design_lock=lock,design_sha256=approval['design_lock_sha256'])
    report['environment']=env; assert report==load(CAP/'automatic.json');save('automatic-recomputed.json',report)
    receipt=execution_plan.coverage_receipt(execution,obs);assert receipt==load(CAP/'execution-coverage.json');save('coverage-recomputed.json',receipt)
    frames=[]; hashes=[design.digest(f) for f in [fixtures['initial'],*fixtures['updates']]]
    for snap in obs['snapshots']:
        b=snap['binding'];assert b['input_sha256']==hashes[b['fixture_index']]
        assert snap['binding_after_capture']==b and snap['capture_consistent'] is True
        assert len(snap['callbacks'])==b['event_revision']
        assert all(v['event']=='notes.reviewed.A' and v['fixture_index']==0 for v in snap['callbacks'])
        assert sha(CAP/'native'/snap['screenshot']) in manifest['image_hashes'].values()
        frames.append({'index':snap['index'],'binding':b,'png':snap['screenshot'],'png_sha256':sha(CAP/'native'/snap['screenshot'])})
    state=next(s for s in plan['states'] if s['id']=='replaced')
    evidence,complete,reason,_=native_checks.bound_state_evidence(obs,state);assert complete
    intervals=[];target_rows=[]
    for i,snap in evidence:
        vp=snap['viewport'];c=snap['runtime']['content_frame'];offset=max(0,vp['y']-c['y']);intervals.append([offset,min(c['height'],offset+vp['height'])])
    intervals.sort();end=0
    for start,stop in intervals:assert start<=end;end=max(end,stop)
    assert intervals[0][0]==0 and end==2346.333333333333
    assert next(n for n in evidence[-1][1]['nodes'] if n.get('identifier')=='__observer.bottom')['fully_within_viewport'] is True
    for target in execution['required_coverage'][0]['targets']:
        visible=[]
        for i,snap in evidence:
            node=native_checks.resolve(snap,target,'ios')['semantic']
            if node.get('fully_within_viewport'):visible.append(i)
        assert visible;target_rows.append({'selector':target,'fully_visible_indices':visible})
    events=[]
    for index,expected_events,stimulus in [(1,['notes.reviewed.A'],'activation'),(2,[],'caller_update')]:
        step=obs['steps'][index];verdict=native_checks.callback_verdict(step,expected_events,'ios',stimulus=stimulus);assert verdict['status']=='passed'
        events.append({'action_index':index,'outcome':step['outcome'],'dispatch':step['dispatch'],'callback_delta':step['callback_delta'],'binding_after':step['binding_after'],'immediate_after':step['immediate_after'],'after':step['after'],'verdict':verdict})
    native_identity=[]
    for name in ['assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift','scripts/ios_observe.py','scripts/observation_contract.py']:
        current=sha(SNAPSHOT/name);original=sha(BASE/'development/candidate-attempt-1'/name);assert current==original
        native_identity.append({'path':name,'final_sha256':current,'original_benchmark_sha256':original,'same':True})
    for pos in [0,4]:
        batch=evidence[pos:pos+4];canvas=Image.new('RGB',(1216,1880),'white');draw=ImageDraw.Draw(canvas)
        for n,(i,snap) in enumerate(batch):
            vp=snap['viewport'];im=Image.open(CAP/'native'/snap['screenshot']).convert('RGB');x=(n%2)*608;y=(n//2)*940
            draw.text((x+5,y+8),f'targeted replaced original i{i}',fill='black')
            crop=im.crop((round(vp['x']*3),round(vp['y']*3),round((vp['x']+vp['width'])*3),round((vp['y']+vp['height'])*3)))
            canvas.paste(crop.resize((600,900)),(x,y+35))
        canvas.save(ROOT/'images'/f'replaced-{pos//4}.jpg',quality=97)
    action_i=next(i for t in target_rows if t['selector']['identifier']=='notes.action' for i in t['fully_visible_indices']);snap=obs['snapshots'][action_i]
    f=next(n for n in snap['nodes'] if n.get('identifier')=='notes.action')['image_frame'];box=(round(f['x']+30),round(f['y']+10),round(f['x']+f['width']-30),round(f['y']+f['height']-10))
    colors=Counter(Image.open(CAP/'native'/snap['screenshot']).convert('RGB').crop(box).getdata())
    save('rendered-diagnostic.json',{'index':action_i,'png':str(CAP/'native'/snap['screenshot']),'sha256':sha(CAP/'native'/snap['screenshot']),'interior_box':box,'colors':[{'rgb':'#%02X%02X%02X'%rgb,'count':n}for rgb,n in colors.most_common(5)],'scope':'Diagnostic picking for visual review; no new automatic pixel policy.'})
    input_paths=[BASE/'operators/targeted-neutral-request.json',NEUTRAL/'SEAL.json']
    input_paths += [p for p in CAP.rglob('*') if p.is_file()]
    input_paths += [SNAPSHOT/'SKILL.md',SNAPSHOT/'references/decision-feedback.md'] + list((SNAPSHOT/'scripts').glob('*.py'))
    save('inputs-sha256.json',{'recorded_unix':begun,'files':{str(p):sha(p)for p in input_paths}})
    save('inspection.json',{'version':1,'started_unix':begun,'finished_unix':time.time(),'capture_result_sha256':sha(CAP/'result.json'),'frozen_manifest_reconstructed':True,'source_input_identities_verified':True,
        'native_identity':native_identity,'frames':frames,'selected_state':{'id':'replaced','complete':complete,'reason':reason,'intervals':intervals,'targets':target_rows,'input_event_binding':evidence[0][1]['binding']},'events':events,
        'retained_parent_rows':len(report['assertions']),'automatic_counts':report['counts'],'incidental_native_pass_ids':[r['id']for r in report['assertions']if r['status']=='passed'and not r['id'].startswith('replaced/')],
        'sdk_executed_by_reviewer':False})
    print(json.dumps({'counts':report['counts'],'selected_coverage':receipt['satisfied'],'environment':env['status'],'fresh_instance':evidence[0][1]['binding'],'native_assets_identical':True},indent=2))

if __name__=='__main__':main()
