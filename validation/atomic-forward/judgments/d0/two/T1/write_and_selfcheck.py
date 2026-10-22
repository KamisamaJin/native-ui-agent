import json,pathlib,sys,time,traceback,hashlib,datetime
sys.dont_write_bytecode=True
root=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');out=root/'judgments/d0/two/T1';sys.path.insert(0,str(root/'candidate-v8/scripts'))
import acceptance,design_contract as design
states=json.loads((out/'state-evidence.json').read_text());checks=[]
for key,evidence in states.items():
 p=root/'evaluation-inputs/d0/T1'/key
 inp=design.load(p/'inputs.json');cat=design.load(p/'catalog.json');plan=design.load(p/'plan.json');native=design.load(out/key/'recomputed-native-pixel.json');decisions=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  state=row['state'];info=evidence['states'][state];expanded=state=='expanded';updated=state=='submitted'
  if row['aspect']=='wrapping':
   reason='I inspected the complete bound '+state+' original-PNG content sweep from header through footer. Title, subtitle, notice, all six choice labels and visible details, literal Unavailable status and caller reason, summary, disclosure label, Request station and footer are present with every word/character preserved in wrapped lines, without ellipsis or clipped glyphs.'
   reason+= ' The expanded global guidance is present in full between the disclosure and action.' if expanded else ' The global guidance body is deliberately collapsed and excluded.'
   if updated:reason+=' This is caller input 1: the updated notice and the newly unavailable first choice with its replacement reason are readable, and the selected second-choice summary is readable.'
   if key.endswith('ios/P2'):reason+=' Unavailable breaks before its final e because the unbroken segment exceeds the available width; the brief explicitly permits character breaking and no character is lost.'
   if key.startswith('source-b/ios'):reason+=' Disabled controls are visibly dimmed; their text remains decipherable and fully present. This decision assesses wrapping, not palette or contrast compliance.'
  else:
   reason='Across the complete bound '+state+' original-PNG sweep, header, notice, six cards with their labels/details and status/reasons, summary, disclosure, '+('expanded guidance, ' if expanded else '')+'primary action and footer occupy separate successive areas. I observed no unintended text/control overlap or occlusion. Cropping at a scroll viewport edge is resolved by the overlapping exact-state frames; contact-sheet column boundaries are assembly boundaries, not product clipping.'
  decisions.append({'review_id':row['review_id'],'actual':True if info['complete'] else None,'reason':reason,'snapshot_indices':info['indices'] if info['complete'] else []})
 attributions=[]
 for finding in native['manual']['review_contract']['findings']:
  if finding['status']!='failed':continue
  assert key.startswith('source-b/ios/') and finding['id'].endswith('/primary-surface-color')
  colors='opaque #CFCDC5 instead of the approved #AAA99F' if key.endswith('P1') else 'opaque #33474C instead of the approved #52666A'
  reason='Product cause: recomputed samples are '+colors+' in a solid glyph-free strip inside the uniquely resolved workshop.submit semantic box, fully within the native viewport. The original PNG shows the dimmed actual disabled primary button, not outer host background or an overlaid child. The submitted component applies PlainButtonStyle() and .disabled(selected == nil) to its own painted label; its palette declares the approved disabled color but the rendered button has the default disabled dimming. The approved bridge only decodes the model/maps callbacks and does not repaint the button. Enabled states render the intended enabled fill. The likely mechanism is default button-style disabled opacity; exact internal SwiftUI compositing is inferred, while component ownership and the rendered mismatch are directly evidenced.'
  attributions.append({'id':finding['id'],'cause':'product','reason':reason,'snapshot_indices':finding['snapshot_indices']})
 judge={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':decisions},'attributions':attributions}
 dest=out/key/'judge.json';dest.write_text(json.dumps(judge,ensure_ascii=False,indent=2)+'\n')
 started=time.time()
 try:
  report=acceptance.evaluate(plan,design.load(root/inp['design_root']/'design-lock.json'),inp['approval']['design_lock_sha256'],design.load(root/inp['design_root']/'policy.json'),inp['approval']['policy_sha256'],design.load(root/inp['observation']),inp['observation_sha256'],root/inp['root'],inp['platform'],design.load(root/inp['environment']),judge,judge)
  result={'schema_self_check':'accepted','independent_consensus':False,'same_request_in_both_slots':True,'counts_for_schema_diagnostics_only':report['counts'],'environment':report['environment']['status'],'unassessed_ids':[row['id'] for row in report['rows'] if row['status']=='unassessed'],'failed_ids':[row['id'] for row in report['rows'] if row['status']=='failed'],'startedAtUnix':started,'finishedAtUnix':time.time()}
 except Exception as err:
  result={'schema_self_check':'rejected','error':repr(err),'traceback':traceback.format_exc(),'startedAtUnix':started,'finishedAtUnix':time.time()}
  (out/key/'schema-rejected-attempt-1.json').write_text(json.dumps({'request':judge,'result':result},indent=2)+'\n')
 (out/key/'schema-self-check.json').write_text(json.dumps(result,indent=2)+'\n');checks.append({'case':key,**result});print(key,result['schema_self_check'],result.get('counts_for_schema_diagnostics_only'),flush=True)
(out/'self-check-index.json').write_text(json.dumps(checks,indent=2)+'\n')
