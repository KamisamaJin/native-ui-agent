from pathlib import Path
import json,hashlib,datetime
from PIL import Image
root=Path.cwd();absolute=lambda p:str(root/p)
d0=json.loads((root/'submission-d0.json').read_text())
sources=[]
for source in d0['sources']:
 p=Path(source['path']);digest=hashlib.sha256(p.read_bytes()).hexdigest()
 sources.append({'path':str(p),'sha256':digest,'d0_sha256':source['sha256'],'changed_from_d0':digest!=source['sha256']})
receipts=json.loads((root/'repair/final-source-receipts.json').read_text())
ocr=json.loads((root/'repair/final-ios-ocr.json').read_text())
measurements=[]
for result in ocr:
 case=Path(result['image']).parent.name
 observations=[]
 for item in result['observations']:
  if any(part in item['text'] for part in ['Attachment','transfers','Show all','Show less','Retry']):
   x,y,w,h=item['bounds_normalized_bottom_origin'];height=800 if case in ['I04','I05'] else 620
   observations.append({'text':item['text'],'bounds_points_top_origin':[320*x,height*(1-y-h),320*w,height*h]})
 measurements.append({'case':case,'image':absolute(result['image']),'native_ocr_text_bounds':observations})
checks=[
 {'rule_id':'TQ-LAYOUT-04','case':'I04','platform':'ios','result':'observed_corrected','method':'native PNG inspection and Apple Vision OCR','observation':'At 288-point supplied panel width, Show less is below the single-line title and aligned to the leading inset.','evidence':[absolute('repair/final-v2/ios/I04/actual.png'),absolute('repair/final-ios-ocr.json')]},
 {'rule_id':'TQ-LAYOUT-04','case':'I06','platform':'ios','result':'observed_corrected','method':'native PNG inspection and Apple Vision OCR','observation':'At 288-point supplied panel width, Show all is below the title.','evidence':[absolute('repair/final-v2/ios/I06/actual.png'),absolute('repair/final-ios-ocr.json')]},
 {'rule_id':'TQ-LAYOUT-05','case':'I06','platform':'ios','result':'observed_corrected','method':'native PNG inspection and Apple Vision OCR','observation':'RTL compact Show all is at logical leading/right beneath the right-aligned title; document cells remain at right and aggregate percentage remains at logical trailing/left.','evidence':[absolute('repair/final-v2/ios/I06/actual.png'),absolute('repair/final-ios-ocr.json')]},
 {'rule_id':'TQ-LAYOUT-04','case':'I05','platform':'ios','result':'observed','method':'native PNG inspection','observation':'Accessibility layout keeps toggle below title, Retry below status at logical leading/right of text column, and wraps the aggregate percent onto a second line.','evidence':[absolute('repair/final-v2/ios/I05/actual.png')]},
 {'rule_id':'TQ-COLOR-01','case':'I04','platform':'android','result':'observed','method':'native PNG inspection, pixel sampling and exported native configuration','observation':'Unchanged Android source uses the dark palette when the common host supplies native night-mode mask 32. Earlier self-review light-panel observation came from the prior common host configuration.','evidence':[absolute('repair/final-v2/android/I04/actual.png'),absolute('repair/final-v2/android/I04/native-report.json')]}
]
im=Image.open(root/'repair/final-v2/android/I04/actual.png').convert('RGB');scale=im.width/320
checks[-1]['sample_logical_xy']=[200,40];checks[-1]['actual_panel_rgb']=list(im.getpixel((round(200*scale),round(40*scale))))
checks[-1]['expected_panel_rgb']=[24,34,53]
(root/'repair/final-visual-checks.json').write_text(json.dumps({'checks':checks,'ocr_measurements':measurements},ensure_ascii=False,indent=2)+'\n')
limits=[
 {'item':'iOS runtime accessibility actions','status':'not_executed','detail':'Common iOS AX export remains unavailable. Requested actions were not treated as executed or passing; inspect each native-report.json for its actual activation result.'},
 {'item':'Oldest OS runtime and fallback arrangement','status':'not_executed','detail':'iOS 14 and macOS 11 compiler type checks succeeded on final source. Native Layout is guarded by availability, with the existing preference-based fallback preserved. Runtime layout on these old systems was not exercised.'},
 {'item':'Lower viewport content at accessibility text size','status':'not_executed','detail':'I05 lower offscreen rows were not scrolled into view. Parent-owned scrolling is preserved; invisible native bounds do not establish clipping.'},
 {'item':'Physical touch','status':'not_executed','detail':'Android callback checks used native Compose accessibility OnClick actions, not physical taps.'},
 {'item':'Holdouts and acceptance','status':'not_executed','detail':'No holdout material or hidden results were read. Successful builds and focused checks do not establish acceptance.'}
]
submission={
 'started_at':json.loads((root/'phase-repair-start.json').read_text())['started_at'],
 'submitted_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'sources':sources,
 'final_native_captures':receipts,
 'final_native_capture_count':len(receipts),
 'final_source_receipts_all_match':all(r['matches_final_source'] for r in receipts),
 'checks':{'android_measured_checks':absolute('repair/final-measured-checks.json'),'android_check_count':len(json.loads((root/'repair/final-measured-checks.json').read_text())),'visual_checks':absolute('repair/final-visual-checks.json'),'ios_ocr':absolute('repair/final-ios-ocr.json'),'ios14_api_typecheck':{'exit_code':0,'log':absolute('repair/ios14-typecheck-final.log')},'macos11_api_typecheck':{'exit_code':0,'log':absolute('repair/macos11-typecheck-retry.log')}},
 'cause_change_notes':[
  {'cause':'Source used a deferred geometry preference and state value to select compact layout. This source-level mechanism was inspected; its exact internal runtime value was not measured.','change':'On iOS 16/macOS 13 and newer, custom native Layout implementations choose header, file/retry, and count arrangement synchronously from actual offered inner width; threshold 308 inner points corresponds to 340 panel points. Existing older-OS fallback remains availability guarded.'},
  {'cause':'The first repair draft redundantly mirrored custom Layout coordinates in RTL even though SwiftUI already maps logical coordinates.','change':'Removed the redundant mirror and verified right-side compact controls and document cells in I06 and I05.'},
  {'cause':'No confirmed Android production failures were disclosed. The earlier dark self-review observation was a common host configuration mismatch.','change':'Android production source is unchanged; it was rebuilt and captured on all six inputs with the corrected native appearance host.'}
 ],
 'confirmed_feedback_findings_checked':['submission-06e6f6-I04-compact-header','submission-06e6f6-I06-compact-header','submission-06e6f6-I06-rtl-leading'],
 'unresolved_confirmed_feedback_findings':[],
 'unresolved_or_unexecuted_items':limits,
 'intermediate_attempt_notes':['First direct iOS API type-check command could not locate the SDK under default Command Line Tools; rerun with the configured Xcode SDK succeeded.','First direct macOS API type check used mismatched Command Line Tools macro support; rerun with the configured Xcode toolchain and SDK succeeded.','Intermediate repair capture directories are preserved separately; final-v2 receipts are authoritative for submitted source.'],
 'production_edit_scope':['alerttoast/Sources/AlertToast/TransferToastPanel.swift'],
 'common_harness_modified_by_agent':False,
 'protocol_deviations':[]
}
(root/'submission-final.json').write_text(json.dumps(submission,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'submitted_at':submission['submitted_at'],'sources':sources,'native_captures':len(receipts),'all_receipts_match':submission['final_source_receipts_all_match'],'unresolved_confirmed_feedback_findings':[]},indent=2))
