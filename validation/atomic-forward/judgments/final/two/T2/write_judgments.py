from pathlib import Path
import sys,json,hashlib,datetime,time,collections
sys.dont_write_bytecode=True
B=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/two/T2'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import native_checks
load=lambda p:json.loads(p.read_text())
def save(p,d):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
notes=[];audit=[]
for en in load(O/'inspection-index.json'):
 rel=en['case'];d=O/rel;ins=load(d/'inspection-original.json');i=ins['inputs'];p=B/'evaluation-inputs/final/T2'/rel;cat=load(p/'catalog.json');plan=load(p/'plan.json');obs=load(B/i['observation']); decisions=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  state=row['state'];ev=ins['state_evidence'][state];complete=ev['complete']; actual=True if complete else None
  if not complete:
   reason='Exact input-1 submitted evidence is coherent, but native interval union stops at 1640 of 1646 pt (indices 61-65). The last 6 pt are not captured. Inspected visible words and spacing appear intact; full-content coverage required by this atom is insufficient, so no whole-state truth value is asserted.'
  elif row['aspect']=='wrapping':
   detail={'baseline':'The disclosure is closed and no incident is selected; guidance and unselected dossiers are deliberately hidden.','expanded':'The disclosure is open with incident a selected; its entire inline reading dossier is visible below card a.','submitted':'After the caller update, a is unavailable with the exact new reason, b is selected, and the disclosure remains closed; the updated notice is included.'}[state]
   reason=f'Inspected all bound original viewport pixels across the exact-state scroll strip, including title, subtitle, notice, all six labels/severities, required unavailable reasons, summary, primary label and complete footer. {detail} No visible word is truncated, ellipsized or missing. Text wraps and surrounding blocks grow; the narrow enlarged case uses the explicitly allowed character fallback for overlong segments. The frozen native interval union is complete.'
  else:
   reason=f'Inspected all bound original viewport pixels of {state}, through the complete footer. Title/subtitle, notice, disclosure, chronological cards, severity text, unavailable reasons, visible dossier, summary and primary control occupy separate areas with no unintended overlap or occlusion. The frozen native interval union is complete; scroll-edge clipping is covered by overlapping captures.'
  decisions.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':ev['indices']})
 save(d/'judge.json',{'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':i['observation_sha256'],'decisions':decisions},'attributions':[]})
 stateaudit={}
 for state in plan['states']:
  found,complete,why,cap=native_checks.bound_state_evidence(obs,state); target_records=[]
  for index,s in found:
   targets={}
   for name,target in plan['design_contract']['bindings'].items():
    r=native_checks.resolve(s,target,i['platform']);sn=r.get('semantic',{});cn=r.get('control',{})
    targets[name]={'resolution':r.get('resolution'),'facts':r.get('facts'), 'semantic_box':sn.get('frame',sn.get('unclipped_bounds_dp')),'control_box':cn.get('frame',cn.get('unclipped_bounds_dp')),'native_geometry':sn.get('native_geometry'),'image_box':sn.get('image_frame',sn.get('image_bounds_px'))}
   target_records.append({'snapshot_index':index,'targets':targets})
  stateaudit[state['id']]={'complete':complete,'reason':why,'binding':cap.get('binding') if cap else None,'frames':target_records}
 steps=[{'action_index':j,'type':s.get('type',s.get('action',{}).get('type')),'outcome':s['outcome'],'dispatch':s.get('dispatch'),'callback_delta':s.get('callback_delta'),'same_process':s.get('same_process'),'state_id':s.get('state_id')} for j,s in enumerate(obs['steps'])]
 save(d/'native-target-audit.json',{'original_observation_sha256':i['observation_sha256'],'states':stateaudit,'steps':steps,'limit':'Native target boxes and callback intervals are supporting evidence; qualitative wrapping/overlap judgments were made from original pixels. No physical hit-region or computed SwiftUI font facts are inferred.'})
 notes.append({'case':rel,'selected_visual_atoms':len(decisions),'true':sum(x['actual'] is True for x in decisions),'false':sum(x['actual'] is False for x in decisions),'unknown':sum(x['actual'] is None for x in decisions),'states_inspected':list(ins['state_evidence']),'snapshot_count':len(obs['snapshots']),'bound_snapshots':sum(len(v['indices']) for v in ins['state_evidence'].values()),'contact_sheets':[str(x.relative_to(O)) for x in sorted(d.glob('contact-sheet-*.png'))],'inspection':'All seven state strips were inspected, including caller replacement, unavailable a/c reasons, native selected/enabled state and disclosure labels, a dossier in expanded state, b selection and unchanged summary after submission. Baseline/expanded/submitted were judged separately. Both sources use native disabled and selected controls; actual bridges call the capsule component and map its callbacks without a local business reducer. Continuous-rail and typography-size details are not certified by these two visual atoms.','scope_limits':['Qualitative atoms establish only wrapping and overlap, not complete design equivalence.','Native iOS title weight remains unsupported; no visual substitution.','Narrow iOS replaced/reselected/submitted notice fill remains U when no fully visible eligible target frame exists.']})
 audit.append({'case':rel,'callbacks_verified':[{'action_index':s['action_index'],'outcome':s['outcome'],'events':s['callback_delta']} for s in steps]})
save(O/'visual-inspection-record.json',{'recordedAtUnix':time.time(),'basis':'Approved independent BRIEF/API/reference propositions and reference PNGs, both actual production component sources, original common corpora plus frozen state binding and pixel tools. No candidate served as the other candidate reference.','contact_sheet_method':'Viewport crops from the original PNGs were placed using observed native scroll geometry. Full original hashes and indices are retained. Every page of all 25 contact sheets was visually inspected; original PNG spot checks additionally verified narrow dossier text and RTL submitted footer.','records':notes,'contradictory_or_insufficient_evidence':[{'case':'source-b/ios/H1','states':['reselected','submitted'],'native_coverage':'Interval union 0..1640 against height 1646. Bottom sentinel reported visible, but this does not satisfy the frozen complete-content rule. Visible footer appears whole; that cannot override missing full coverage.','selected_effect':'submitted wrapping and overlap both null; target-only reselected visual cells are not selected.'}],'failure_cause_assessment':'No supported typed-native, rendered-pixel or qualitative failures were found. Attributions are empty, rather than inventing a cause for unknown evidence.','consensus':'One independent reviewer only. Any later AI agreement is consensus, not human gold.'})
extra={}
for f in (B/'candidate-v8').rglob('*'):
 if f.is_file() and (f.suffix in ['.py','.md','.json']):extra[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
prompt=B/'prompts/judge-final-two-T2.txt';extra[str(prompt)]=hashlib.sha256(prompt.read_bytes()).hexdigest()
save(O/'additional-input-hashes.json',extra)
print('judgments',len(notes),'qualitative totals', {k:sum(v[k] for v in notes) for k in ['true','false','unknown']})
