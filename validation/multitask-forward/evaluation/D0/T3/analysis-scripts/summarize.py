from pathlib import Path
import json,hashlib,importlib.util,collections
from PIL import Image
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward');O=R/'evaluation/D0/T3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p,**kw):return {'path':str(p.relative_to(R)),'sha256':sha(p),**kw}
def save(p,d):assert not p.exists(),p;p.write_text(json.dumps(d,indent=2)+'\n')
base_refs=[];summary={'schema_version':1,'stage':'D0','task':'T3','scope':'Anonymous symmetric independent acceptance review, public P1/P2 on iOS/Android. No new native capture or production edit. Frozen grader statuses and all 528 cells per source retained.','sources':{},'unasserted_scope':[],'interpretation':'Rows/states/platforms are manifestations of the two delivered sources, not independent experiments. Categories never change oracle statuses. No claims about introduction timing; D0 is the first scoped evidence reviewed.'}
brief=ref(R/'design-v2/T3/public/BRIEF.md');style=ref(R/'design-v2/T3/public/STYLE-PRECISION.md');api=ref(R/'design-v2/T3/public/API.md');samples=[]
for alias in ['source-a','source-b']:
 allrows=[];business=[];visual=[];ev_business=[];ev_visual=[];env=[];per_case={};source=R/f'evaluation-inputs/D0/T3/{alias}/source-capsule/source/alerttoast/Sources/AlertToast/CollectionConditionReviewPanel.swift'
 for c in ['P1','P2']:
  for p in ['ios','android']:
   d=O/alias/c/p;gr=json.loads((d/'grade.json').read_text());allrows+=gr['rows'];per_case[c+'/'+p]=gr['counts'];base_refs.append(ref(d/'native-base-grade.json'));base_refs.append(ref(d/'native-base.json'))
   if p=='android':
    env.append({'case':c,'input_check':next(x for x in gr['input_checks'] if x['id']=='native-environment'),'evidence':gr['evidence']})
   for row in gr['rows']:
    if row['status']=='F':
     if row['class']=='visual':visual.append(row['id']);ev_visual.extend(row['evidence'])
     else:business.append(row['id']);ev_business.extend(row['evidence'])
   if p=='ios':
    op=R/f'common-corpora/T3/{alias}/d0/ios/{c}/observation.json';obs=json.loads(op.read_text());
    for state,target in ([('loaded','condition.primary')] if c=='P1' else [('advanced','condition.stable')]):
     cap=next(x for x in obs['state_captures'] if x['state_id']==state)
     for i in cap['snapshot_indices']:
      s=obs['snapshots'][i];nodes=[n for n in s['nodes'] if n.get('identifier')==target and n.get('fully_within_viewport')]
      if not nodes:continue
      n=nodes[0];box=n['frame'];im=Image.open(op.parent/s['screenshot']).convert('RGB');app=s['app_frame'];sx=im.width/app['width'];sy=im.height/app['height'];x=round((box['x']-app['x']+box['width']*.75)*sx);y=round((box['y']-app['y']+box['height']*.5)*sy)
      samples.append({'alias':alias,'case':c,'platform':'ios','state':state,'target':target,'snapshot_index':i,'original':ref(op.parent/s['screenshot']),'sample_pixel_xy':[x,y],'sample_rgb':list(im.getpixel((x,y))),'role_design_hex':'#DACDE5' if c=='P1' else '#634E75','scope':'Rendered-pixel corroboration of visually obvious additional disabled fade only. This is not a native computed style measurement and cannot pass native_style rows.'});break
 def unique(ev):
  return list({(e['path'],e['sha256']):e for e in ev}.values())
 cluster1={'cluster_id':alias+'-ios-replacement-seed','category':'business_state','description':'A successful same-process caller replacement changes context to Study room but focuses Botanical folio and reinstates the initial decisions instead of the replacement seed (Harbor sketch focus, bowl care/structure, sketch pending). P1 shows 1 reviewed/0 follow-ups rather than 2/1; P2 shows 3 reviewed/0 rather than 2/1 and incorrectly enables submission. These are related manifestations of one replacement-state failure. Source has request-id onChange reset logic, but runtime evidence proves that its resulting state is wrong; the precise closure/framework mechanism is not asserted.','fixed_row_ids':business,'evidence':[brief,api,ref(source),ref(R/'design-v2/T3/public/Bridge.swift'),ref(R/'candidate-v7/assets/ios-observer/ObserverApp.swift')]+[ref(R/f'design-v2/T3/public/cases/{c}/fixtures.json') for c in ['P1','P2']]+unique(ev_business)}
 cluster2={'cluster_id':alias+'-ios-disabled-palette','category':'visual_layout','description':'The disabled primary in light mode and disabled read-only classification controls in dark mode receive a visible extra fade beyond the brief’s border fill and muted text roles. The primary appears much paler than the reference disabled primary; dark disabled labels and fills are substantially dimmer than the assigned roles. Source explicitly selects border/muted colors and then applies PlainButtonStyle with disabled, consistent with the observed additional framework treatment. This is an appearance defect, not a claim that unsupported native iOS color measurements became available.','fixed_row_ids':visual,'evidence':[brief,style,ref(source),ref(R/'design-v2/T3/public/references/P1-loaded.png'),ref(R/'design-v2/T3/public/references/P1-reasoned.png')]+unique(ev_visual)}
 summary['sources'][alias]={'counts':{s:sum(r['status']==s for r in allrows) for s in ['P','F','U','N/A']},'counts_by_case_platform':per_case,'denominator':len(allrows),'defect_clusters':[cluster1,cluster2],'product_failure_row_ids':business+visual,'non_product_f_rows':[],'uncertain_f_rows':[],'unsupported_scope':[{'scope':'Android applicable acceptance cells in P1 and P2 (230 total)','reason':'Fixed native-environment input check rejects recorded direction Ltr versus expected ltr; exact font scale and night mode otherwise match. Preserve all applicable rows U; no case is dropped. This is an observation/representation discrepancy, not evidence of an actual RTL product bug.','evidence':env},{'scope':'iOS native title font size/weight/ink and inspector-wrap (24 applicable rows per case)','reason':'Generic computed SwiftUI typography/color/ellipsis unavailable; native_style stays U. Visual review and pixels do not synthesize native measurements.'},{'scope':'P2 iOS classified activation-callback','reason':'Read-only Stable tap is blocked_disabled without successful dispatch; empty callback interval cannot establish callback behavior. Current disabled/selected facts remain independently assessable.'}],'source_api_issues':[],'source_api_disposition':'Both exact sealed platform sources expose required API and native builds/tests completed successfully. Structural API review is source-hash and original-build bound. Runtime replacement behavior is reported in the business cluster; no signature/compilation issue found.','unasserted_source_only_concerns':[],'symmetry':'Identical review scope, fixed checks and visual criteria applied to each anonymous source.'}
save(O/'rendered-appearance-corroboration.json',{'samples':samples,'warning':'Appearance corroboration only; native_style remains U on iOS.'})
save(O/'native-base-byte-bindings.json',{'files':base_refs,'policy':'First calls used manual=None, source_root=None, api_review=None. Full native-base-grade and native_report bytes preserved without revision.'})
summary['unasserted_scope']=[
 {'requirement':'Exact fonts, weights and colors for every non-title role, all surface/canvas/border/primary roles, corner radius10, inset12, major16 and stacked8 gaps.','gap':'Selected ledger has exact native title style and selected control boxes only. A broad visual decision assesses hierarchy/readability/appearance but does not numerically prove every style or spacing detail.','evidence':[brief,style]},
 {'requirement':'Every queue row identity/label and active selected state, third-row navigation, long labels growing above64, and caption/name role styling.','gap':'Ledger directly checks second-row selection/status and queue width, with other identities seen visually; it is not exhaustive row-by-row semantics or large caller-text stress validation.','evidence':[brief]},
 {'requirement':'Exact caller context, material, focused inspection-note content, Review notes identity and every supplied paragraph.','gap':'Title and focused title have exact copy assertions; note wrapping has a selected native-style family, and broad visual review checks ordered paragraphs. There are no separate exact-copy/identifier cells for all other text nodes and notes.','evidence':[brief]},
 {'requirement':'Unknown focusID fallback; optional pending inclusion; care seed with absent/invalid reason; validation-priority combinations; care reselect retains reason; Stable clears prior reason; re-entering care clears a prior stable reason; switching Surface/Structure.','gap':'These are brief requirements without separate selected22-family cells covering each transition/input combination in P1/P2. Do not infer comprehensive business coverage from the delivered actions.','evidence':[brief,api]},
 {'requirement':'Read-only care reason editing, every read-only navigation path, callbacks after replacement, sorted optional-pending payload, no nested native OnClick, and state persistence across all focus sequences.','gap':'Selected ledger tests some current control/callback states and one replacement route; structural source review adds context but does not invent acceptance cells or successful dispatches.','evidence':[brief,api]},
 {'requirement':'No duplicate outer padding/nested vertical scrolling and all dedicated text/heading identities.','gap':'Broad composition and structural review are relevant but fixed geometry cells measure only primary height, queue width and conditional care-control height. They do not independently quantify every host/component allocation.','evidence':[brief,style]}
]
save(O/'summary.json',summary)
spec=importlib.util.spec_from_file_location('tg',R/'design-v2/T3/private/grader.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
native_pairs=[];full_pairs=[]
for c in ['P1','P2']:
 for p in ['ios','android']:
  a=json.loads((O/'source-a'/c/p/'grade.json').read_text());b=json.loads((O/'source-b'/c/p/'grade.json').read_text());native_pairs+=g.compare_pair(a,b)['rows']
  assert len(a['rows'])==len(b['rows'])==132
  for ar,br in zip(a['rows'],b['rows']):
   assert ar['id']==br['id'];full_pairs.append({'id':ar['id'],'case':c,'platform':p,'state':ar['state'],'requirement':ar['requirement'],'class':ar['class'],'expected':ar['expected'],'unit':ar['unit'],'op':ar['op'],'tolerance':ar['tolerance'],'source-a':ar['status'],'source-b':br['status']})
save(O/'pair-comparison.json',{'full_denominator':len(full_pairs),'full_rows':full_pairs,'native_compare_pair_denominator':len(native_pairs),'native_compare_pair_rows':native_pairs,'scope':'Full paired528-cell ledger is retained including all U/N/A and visual cells. Frozen compare_pair separately retains its defined504-cell native-only denominator; no favorable filtering.'})
print('summary counts',{a:s['counts'] for a,s in summary['sources'].items()},'paired',len(full_pairs),len(native_pairs))
