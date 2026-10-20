from pathlib import Path
import json,hashlib,importlib.util,collections
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward'); O=R/'evaluation/D0/T3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def save(p,d):assert not p.exists(),p;p.write_text(json.dumps(d,indent=2)+'\n')
batch=json.loads((R/'evaluation-inputs/D0/T3/batch.json').read_text()); delivery=R/'evaluation-inputs/D0/DELIVERY-SEAL.json';ds=json.loads(delivery.read_text());integrity={'delivery':ref(delivery),'batch':ref(R/'evaluation-inputs/D0/T3/batch.json'),'sources':{}}
for item in batch['corpora']:
 alias=item['anonymousID'];cap=R/item['sourceCapsule'];corp=R/item['captures'];sc=cap/'seal.json';pm=corp/'portable-sha256.json'; expected=json.loads(pm.read_text());bad=[rel for rel,h in expected.items() if not (corp/rel).is_file() or sha(corp/rel)!=h];assert not bad
 assert sha(sc)==item['sourceSealSHA256'];assert sha(pm)==item['portableManifestSHA256'];sm=json.loads(sc.read_text());print(alias,'source seal keys',list(sm))
 delivered={k:v for k,v in ds['files'].items() if k.startswith('T3/'+alias+'/') or k=='T3/batch.json'};dbad=[k for k,v in delivered.items() if sha(R/'evaluation-inputs/D0'/k)!=v];assert not dbad
 rec={'source_seal':ref(sc),'portable_manifest':ref(pm),'corpus_seal':ref(corp/'corpus-seal.json'),'portable_files_checked':len(expected),'portable_mismatches':bad,'delivery_scoped_files_checked':len(delivered),'delivery_mismatches':dbad,'cases':{}}
 for case in ['P1','P2']:
  for plat in ['ios','android']:
   d=corp/plat/case;op=d/'observation.json';obs=json.loads(op.read_text());m=json.loads((d/'manifest.json').read_text());rel='alerttoast/Sources/AlertToast/CollectionConditionReviewPanel.swift' if plat=='ios' else 'reply/Reply/app/src/main/java/com/example/reply/ui/components/CollectionConditionReviewPanel.kt';sp=cap/'source'/rel;h=sha(sp);bound=[v for k,v in m['source_hashes'].items() if k.endswith('/'+rel)]
   assert bound==[h],(alias,plat,case,bound,h)
   logs=[ref(d/n) for n in ['manifest.json','build.log','test.log','junit.xml'] if (d/n).exists()]
   rec['cases'][case+'/'+plat]={'observation':ref(op),'source':ref(sp),'source_hash_matches_native_manifest':True,'original_logs':logs,'recorded_commands':{k:m[k] for k in ['command','build_command','test_command','build_exit_code','test_exit_code','exit_code','native_test_count','native_counts'] if k in m},'native_test_summary':m.get('native_summary'),'configuration':obs.get('configuration'),'issues':obs.get('issues',[]),'coverage':obs.get('coverage')}
   manual={'observation_sha256':sha(op),'decisions':[],'reviewer':'anonymous T3 D0 independent acceptance evaluator','scope':'Original state screenshots only. Review aids are viewport crops; assertions cite each original PNG. Numeric iOS native style remains U.'}
   if plat=='ios':
    for state in ['loaded','reasoned','advanced','classified','submitted','replaced']:
     c=next(c for c in obs['state_captures'] if c['state_id']==state);ids=c['snapshot_indices'];evidence=[{'path':obs['snapshots'][i]['screenshot'],'sha256':sha(d/obs['snapshots'][i]['screenshot'])} for i in ids]
     fail=state in ({'loaded','reasoned','advanced','replaced'} if case=='P1' else {'advanced','classified','submitted'})
     common='Reviewed the original overlapping viewport PNGs at the native logical width, including every supplied note paragraph in order. Queue/inspector/action/notes hierarchy, label and inspection-note wrapping, selected border/marker, and spacing are readable with no overlapping or component-clipped content. Content outside one scroll viewport is not clipping. '
     reason=common+('FAIL: disabled '+('Submit review' if case=='P1' else 'Stable and Needs care')+' visibly applies an additional fade to the specified border-fill and muted-text palette roles. The faded label is visibly lighter in light mode / darker in dark mode than the nearby body muted role; original design BRIEF requires border fill and muted text, and P1 reference shows the unfaded disabled primary. Source sets those roles then uses PlainButtonStyle plus .disabled; actual native output does not preserve them. This is visual appearance, not a computed native iOS color measurement.' if fail else 'PASS for captured composition/appearance: palette and readable hierarchy visually follow the supplied brief/reference, and enabled controls retain their role colors. This does not assert exact native typography/color values, effective padding, or business state correctness. '+('The loaded/replaced original native interval union is complete.' if state in ['loaded','replaced'] else 'This decision covers the captured target regions; no uncaptured region is inferred.'))
     manual['decisions'].append({'id':state+'/visual-composition','state':state,'rule':'visual-composition','status':'failed' if fail else 'passed','method':'visual','snapshot_indices':ids,'reason':reason,'evidence':evidence})
   else:manual['unsupported_reason']='Native environment input integrity fails fixed direction comparison (Ltr versus ltr). No Android manual pass/fail is asserted; all applicable final oracle cells remain U.'
   save(O/alias/case/plat/'manual.json',manual)
   api={'source_sha256':h,'reviewer':'anonymous T3 D0 independent evaluator','status':'P','reason':'The sealed production source matches the public model fields, constructor order and component callback signature; state, eligibility, derived copy and callback assembly reside in production, and the frozen bridge only decodes/forwards. Original native build/test completed successfully for this exact source. This structural API disposition does not waive separately scored runtime or visual failures.','findings':[],'evidence':logs+[ref(sp),ref(R/'design-v2/T3/public/API.md')]}
   if plat=='ios':api['findings']=[{'category':'business_state','description':'Caller replacement updates caller context but resets local focus/decisions to the original seed in native evidence. Tracked in fixed business acceptance rows, not a compilation or signature issue.'}]
   save(O/alias/case/plat/'api-review.json',api)
 integrity['sources'][alias]=rec
save(O/'input-integrity.json',integrity)
spec=importlib.util.spec_from_file_location('t3grade',R/'design-v2/T3/private/grader.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
for alias in ['source-a','source-b']:
 for case in ['P1','P2']:
  for plat in ['ios','android']:
   out=O/alias/case/plat;op=R/f'common-corpora/T3/{alias}/d0/{plat}/{case}/observation.json'
   gr=g.grade(case,plat,op,manual=out/'manual.json',source_root=R/f'evaluation-inputs/D0/T3/{alias}/source-capsule/source',api_review=out/'api-review.json')
   save(out/'grade.json',gr);print(alias,case,plat,gr['counts'],[(x['id'],x['status']) for x in gr['input_checks']]);assert not any(x['id']=='native-evidence-validity' and x['status']=='F' for x in gr['input_checks'])
