from pathlib import Path
import json,hashlib,subprocess,datetime
root=Path.cwd();base=root/'self-review'
ocr=json.loads((base/'ios-ocr.json').read_text());geometries=[]
for record in ocr:
 case=Path(record['image']).parts[-3]
 if case not in ['narrow-light','narrow-dark-rtl']:continue
 f=json.loads((base/'fixtures'/f'{case}.json').read_text());entries=[]
 for t in record['texts']:
  if t['text'] in ['Attachment','transfers','Retry','Failed • retry','available'] or 'Show less' in t['text']:
   b=t['normalized_bounds_bottom_left'];entries.append({'text':t['text'],'glyph_bounds_logical_top_left':[b[0]*f['width'],(1-b[3])*f['height'],b[2]*f['width'],(1-b[1])*f['height']]})
 geometries.append({'case':case,'measurements':entries,'method':'Apple Vision glyph bounding boxes converted to viewport logical units; not native layout frames'})
(base/'ios-narrow-glyph-measurements.json').write_text(json.dumps(geometries,indent=2)+'\n')
review_paths=[]
for platform in ['android','ios']:
 for c in sorted((base/'captures'/platform).glob('*/capture.json')):
  case=c.parent.name;data=json.loads(c.read_text());fixture=json.loads((base/'fixtures'/f'{case}.json').read_text());sha=hashlib.sha256(c.read_bytes()).hexdigest()
  layoutFailure=platform=='ios' and case in ['narrow-light','narrow-dark-rtl']
  paletteFailure=platform=='android' and fixture.get('dark',False)
  hierarchyStatus='failed' if layoutFailure else 'needs_review' if case in ['largest-narrow','large-compact'] else 'passed'
  findings={'capture_sha256':sha,'checks':[{'id':'queue-hierarchy','status':hierarchyStatus,'observed':'At 288-point supplied panel width the title and toggle share the header, and Retry remains beside the failed text; compact controls are required.' if layoutFailure else 'Visible content has readable hierarchy and separated controls; content below the viewport has not been visually inspected.' if hierarchyStatus=='needs_review' else 'Inspected native render (or exact identical empty-state counterpart) has separated title, summary, aggregate, file rows and controls in the inspected viewport. This is visual judgment within this case only.'},{'id':'adaptive-colors','status':'failed' if paletteFailure else 'passed','observed':'Dark host surrounds a white component: sampled panel RGB 255,255,255; specified dark panel RGB 24,34,53. Light primary/state colors are also present.' if paletteFailure else 'Native flat panel RGB matches the specified appearance; visible track and status colors follow the requested palette by visual inspection.'}]}
  fp=base/'findings'/platform/f'{case}.json';fp.parent.mkdir(parents=True,exist_ok=True);fp.write_text(json.dumps(findings,indent=2)+'\n')
  out=base/'skill-reviews'/platform/case
  result=subprocess.run(['python3','skill/scripts/ui_loop.py','review','--capture',str(c),'--findings',str(fp),'--output',str(out)],capture_output=True,text=True)
  review_paths.append({'platform':platform,'case':case,'report':str(out/'report.json'),'exit_code':result.returncode,'output':result.stdout.strip(),'error':result.stderr.strip()})
(base/'skill-review-index.json').write_text(json.dumps(review_paths,indent=2)+'\n')
measurements=json.loads((base/'measured-checks.json').read_text())
issues=[{
 'issue_id':'SR-ANDROID-001','rule_id':'TQ-COLOR-01','platform':'android',
 'triggering_input_condition':{'fixtures':[str(base/'fixtures/narrow-dark-rtl.json'),str(base/'fixtures/large-compact.json')],'dark':True},
 'actual_observation':'Both fresh dark-host captures render the component with the light palette: the panel interior is RGB (255,255,255), with dark primary text and light accent/error colors. The host background is dark.',
 'public_requirement':'In dark appearance the panel must use #182235 (RGB 24,34,53), primary #F2F5FB, and the specified dark tone/track colors.',
 'evidence_paths':[str(base/'captures/android/narrow-dark-rtl/native/actual.png'),str(base/'captures/android/large-compact/native/actual.png'),str(base/'captures/android/narrow-dark-rtl/native/semantics.json'),str(base/'measured-checks.json')],
 'execution_method':'Real production Compose capture under the common dark fixture; full-image inspection and Pillow flat-interior RGB sampling. Native semantic text colors independently show light-palette values.',
 'execution':'observed'
},{
 'issue_id':'SR-IOS-001','rule_id':'TQ-LAYOUT-04','platform':'ios',
 'triggering_input_condition':{'fixtures':[str(base/'fixtures/narrow-light.json'),str(base/'fixtures/narrow-dark-rtl.json')],'viewport_width':320,'supplied_panel_width':288,'font_category':'large','expanded':True},
 'actual_observation':'In both LTR light and RTL dark native captures, Show less remains beside the title, forcing Attachment transfers onto two lines; the failed Retry button remains in the trailing column beside the file name/status. In the LTR capture OCR places Show less glyphs around y=59–71 while title glyphs span y=43–85; Retry glyphs are around y=336–352 and the failed status is below them around y=364–391.',
 'public_requirement':'At supplied width 340 or less, the toggle must be on its own line below the title at logical leading; Retry must be below the status with an 8-point gap at the text column leading edge.',
 'evidence_paths':[str(base/'captures/ios/narrow-light/native/actual.png'),str(base/'captures/ios/narrow-dark-rtl/native/actual.png'),str(base/'ios-ocr.json'),str(base/'ios-narrow-glyph-measurements.json')],
 'execution_method':'Fresh real SwiftUI simulator captures using the unchanged common host, full-image inspection and Apple Vision OCR glyph-position evidence. OCR boxes are not SwiftUI layout frames.',
 'execution':'observed'
}]
review={'phase':'read-only self-inspection','observed_issues':issues,
 'measured_checks':measurements,'additional_native_text_measurements':str(base/'text-measurements.json'),
 'visual_review_reports':review_paths,
 'observed_nondefect_results':[{'rule_ids':['TQ-STATE-01','TQ-STATE-02','TQ-STATE-04','TQ-STATE-06'],'scope':'progress-edges captures','observation':'Visible native labels show NaN/infinity/negative as 0%, over-one running as 100% sent, done with zero progress as Complete, queued with full progress as Waiting, and full-progress failure with Retry. Aggregate is 43% with 1 of 7 complete. Android normalized progress values are checked in measured-checks.json.'},{'rule_ids':['TQ-ACT-01','TQ-ACT-02','TQ-ACT-03'],'scope':'Android real semantic actions','observation':'Retry activation produced exactly [retry:archive]; toggle produced exactly [toggle]; informational failed-row activation had no OnClick and produced no event. These are native semantics actions, not physical touch.'},{'rule_ids':['TQ-STATE-05'],'scope':'Both platforms fresh empty and empty-collapsed captures','observation':'Empty native PNGs are pixel-identical for the two expansion values.'},{'rule_ids':['TQ-LAYOUT-04'],'scope':'large-compact and largest-narrow','observation':'Accessibility categories/font scale select stacked controls in the visible portions; very tall content continues below the viewport and was not treated as component clipping.'}],
 'unassessed_items':[{'item':'iOS action execution and native accessibility export','execution':'not_executed','reason':'The common host exported no iOS AX elements, including for action requests. This is a documented infrastructure limitation, not a detected UI defect or an executed tap.'},{'item':'Screen-reader focus sequence and physical touch','execution':'not_executed'},{'item':'Live caller-driven updates in a running app and theme/font changes after presentation','execution':'not_executed'},{'item':'Full business-screen integration and scrolling beyond initial viewport','execution':'not_executed'},{'item':'Every combination of summary priority, all nonfinite tokens and all widths through 560','execution':'not_executed','reason':'Only the explicit self-chosen fixtures in the capture index were run.'},{'item':'Offscreen portions of the largest accessibility panels','execution':'not_executed','reason':'Common captures show the initial viewport; no screenshot claim is made about lower offscreen content.'}],
 'speculative_risks':[],
 'limitations':['Observed issues are limited to public requirements and own fixtures. No hidden fixtures or results were used.','314 measured checks passed and 2 failed in this configured check set; these counts do not imply whole-component acceptance. Three iOS action requests were not executed.','Android TextLayoutResult hasVisualOverflow flags are preserved as raw measurements and were not converted to clipping defects without visible evidence.','SwiftUI AX and full style-tree introspection are unavailable in the common host; iOS geometry evidence is image/OCR-based.','The D0 Skill artifact collection path issue was corrected only in new self-review profiles. All new Skill captures collected their actual PNG successfully.','No production files were changed during self-inspection.']}
(root/'self_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'observed_issues':len(issues),'skill_reviews':len(review_paths),'measured_checks':measurements['totals']},indent=2))
