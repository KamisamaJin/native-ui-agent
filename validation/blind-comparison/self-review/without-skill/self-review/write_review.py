import json,pathlib,hashlib,datetime
from PIL import Image
root=pathlib.Path.cwd();absname=lambda p:str(root/p)
colors=json.loads((root/'self-review/color-samples.json').read_text())
for record in colors:
 im=Image.open(record['path']).convert('RGB');scale=im.width/record['logical_width']
 record['host_sample_logical_xy']=[8,8];record['host_sample_rgb']=list(im.getpixel((round(8*scale),round(8*scale))))
(root/'self-review/color-samples.json').write_text(json.dumps(colors,indent=2)+'\n')
issues=[{
 'issue_id':'ANDROID-COLOR-001','rule_id':'TQ-COLOR-01','platform':'android',
 'triggering_input':{'fixture':'self-review/empty.json','dark':True,'width':390,'font_scale':1},
 'actual_observation':'In the common dark host, the panel interior remains #FFFFFF, with light-palette primary text #17243B and neutral text #526279. A second dark RTL/accessibility capture also has a white panel.',
 'public_requirement':'The dark panel must be #182235, primary text #F2F5FB, and neutral text #B9C5D9.',
 'evidence_paths':[absname('self-review/android/empty/actual.png'),absname('self-review/android/empty/semantics.json'),absname('self-review/android/narrow-rtl-accessibility/actual.png'),absname('self-review/color-samples.json')],
 'measured_evidence':{'panel_sample_logical_xy':[200,40],'actual_panel_rgb':[255,255,255],'expected_panel_rgb':[24,34,53],'host_background_rgb':[12,20,36]},
 'execution_method':'Observed native PNGs, Pillow flat-color sampling, and native Compose text-color semantics. The fixture uses the common host’s original Reply dark theme; global OS night-mode switching was not independently exercised.'
},{
 'issue_id':'IOS-REFLOW-001','rule_id':'TQ-LAYOUT-04','platform':'ios',
 'triggering_input':{'fixture':'self-review/narrow-normal.json','viewport_width':320,'supplied_panel_width':288,'font_category':'large','expanded':True,'dark':True},
 'actual_observation':'At 288 points supplied width, Show less remains trailing beside the two-line title. The failed row Retry remains trailing beside its file text. Both controls retain the wide arrangement.',
 'public_requirement':'At supplied width 340 or less, put toggle on its own leading-aligned line below the title and retry below the failed status with an 8-point gap, aligned to the text column’s leading edge.',
 'evidence_paths':[absname('self-review/ios/narrow-normal/actual.png'),absname('self-review/narrow-normal.json'),absname('self-review/ios-ocr.json'),absname('alerttoast/Sources/AlertToast/TransferToastPanel.swift')],
 'execution_method':'Observed simulator native PNG and Apple Vision OCR positions, corroborated by read-only production source inspection. The common snapshot captures the native component’s rendered state; no later event-loop settling behavior was separately measured.'
}]
checks=json.loads((root/'self-review/measured-checks.json').read_text())
visual=[
 {'platform':'both','case':'public-smoke and expanded','rule_ids':['TQ-VIS-01','TQ-STATE-03','TQ-STATE-04','TQ-LIST-01'],'result':'observed','observation':'Quiet aligned card; collapsed shows first two files and +2 more attachments; expanded shows four in input order, 1 needs retry, 1 of 4 complete, 45%.','evidence_paths':[absname('draft/android/actual.png'),absname('draft/ios-retry-1/actual.png'),absname('self-review/android/expanded/actual.png'),absname('self-review/ios/expanded/actual.png')]},
 {'platform':'both','case':'edge-progress','rule_ids':['TQ-STATE-01','TQ-STATE-02','TQ-STATE-04','TQ-STATE-06'],'result':'observed','observation':'NaN running value renders 0% sent with empty track; infinity failed stays failed with Retry; 0.425 running reads 43% sent; queued at 1 remains Waiting; done at 0 remains Complete; aggregate 29% with 1 of 5 complete. NaN and Infinity in these file names are intentional original input names.','evidence_paths':[absname('self-review/android/edge-progress/actual.png'),absname('self-review/ios/edge-progress/actual.png'),absname('self-review/ios-ocr.json')]},
 {'platform':'both','case':'empty','rule_ids':['TQ-STATE-05'],'result':'observed','observation':'Title, No transfers, and helper present; count, percent, progress, list, overflow, and toggle absent. Android color mismatch is separately reported.','evidence_paths':[absname('self-review/android/empty/actual.png'),absname('self-review/ios/empty/actual.png')]},
 {'platform':'android','case':'narrow-rtl-accessibility','rule_ids':['TQ-LAYOUT-04','TQ-LAYOUT-05','TQ-STATE-02'],'result':'observed','observation':'Compact toggle and retry stack; document cell at logical leading/right; 75% aggregate fills from right; zero running track is empty, full running track is filled; long name ends in ellipsis after three lines. Lower content continues below viewport in the parent scroll host.','evidence_paths':[absname('self-review/android/narrow-rtl-accessibility/actual.png'),absname('self-review/android/narrow-rtl-accessibility/semantics.json')]},
 {'platform':'ios','case':'narrow-rtl-accessibility','rule_ids':['TQ-LAYOUT-04','TQ-LAYOUT-05'],'result':'observed','observation':'Accessibility category forces stacked toggle/retry, scales text and preserves the long name limit, keeps document at logical leading/right, and fills aggregate from right. Visible content is tall; lower rows are below viewport and were not scrolled into view.','evidence_paths':[absname('self-review/ios/narrow-rtl-accessibility/actual.png'),absname('self-review/ios-ocr.json')]},
 {'platform':'ios','case':'dark empty and narrow-normal','rule_ids':['TQ-COLOR-01'],'result':'measured','observation':'Interior pixel sample is [24,34,53], matching dark panel #182235.','evidence_paths':[absname('self-review/color-samples.json')]}
]
limitations=[
 {'item':'iOS retry execution and AX semantics','execution':'not_executed','detail':'Common host exported ax_elements=[]; requested transfer.retry.archive had activation_executed=false and events=[]. This is not recorded as a UI defect or a passing tap. Declarations use native Button labels/identifiers and ProgressView; runtime AX behavior remains unassessed.','evidence_paths':[absname('self-review/ios/expanded/native-report.json'),absname('alerttoast/Sources/AlertToast/TransferToastPanel.swift')]},
 {'item':'Physical touch and complete host navigation','execution':'not_executed','detail':'Android actions were native accessibility OnClick invocations after layout, not physical taps. Native capture hosts exclude full application navigation.'},
 {'item':'Live caller recomposition, all summary priority combinations, negative infinity and negative finite inputs, <=2 row toggle thresholds','execution':'not_executed','detail':'Source was reviewed, but these additional cases were not independently rendered or driven in this timed phase.'},
 {'item':'Minimum supported OS runtimes and macOS build','execution':'not_executed','detail':'Successful common iOS build/capture does not prove execution on iOS 14 or macOS 11.'},
 {'item':'Content below viewport','execution':'not_executed','detail':'The large RTL fixtures extend below the parent viewport. Offscreen rows were not scrolled into view; zero clipped semantics bounds are not treated as component clipping.'},
 {'item':'Global Android system night-mode switching','execution':'not_executed','detail':'Dark checks used the common original-theme host with dark=true. No separate real-device OS appearance transition was performed.'},
 {'item':'Overall acceptance','execution':'not_executed','detail':'These captures and measured checks are focused public self-checks, not hidden evaluation or acceptance.'}
]
review={'phase':'read-only self-inspection','observed_issues':issues,'measured_checks':checks,'color_measurements':colors,'visual_checks':visual,'ocr_evidence':absname('self-review/ios-ocr.json'),'speculative_risks':[],'unassessed_or_not_executed':limitations}
(root/'self_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
d0=json.loads((root/'submission-d0.json').read_text());sources=[]
for f in d0['sources']:
 p=pathlib.Path(f['path']);digest=hashlib.sha256(p.read_bytes()).hexdigest();sources.append({'path':str(p),'sha256':digest,'d0_sha256':f['sha256'],'unchanged':digest==f['sha256']})
captures=[]
for manifest in sorted((root/'self-review').glob('*/*/capture.json')):
 m=json.loads(manifest.read_text());captures.append({'path':str(manifest.parent),'manifest':str(manifest),'status':m['status'],'command_exit_codes':[c['exit_code'] for c in m['commands']]})
submission={'started_at':json.loads((root/'phase-self-review-start.json').read_text())['started_at'],'submitted_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_hashes':sources,'sources_unchanged':all(s['unchanged'] for s in sources),'self_review_path':absname('self_review.json'),'captures':captures,'check_paths':[absname('self-review/measured-checks.json'),absname('self-review/color-samples.json'),absname('self-review/ios-ocr.json'),absname('self-review/check_semantics.py'),absname('self-review/ocr.swift')],'observed_issue_count':len(issues),'measured_check_count':len(checks),'limitations':limitations,'protocol_deviations':[],'production_edits_during_self_review':False}
(root/'submission-self-review.json').write_text(json.dumps(submission,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'submitted_at':submission['submitted_at'],'sources_unchanged':submission['sources_unchanged'],'observed_issue_count':len(issues),'measured_checks':len(checks),'own_successful_native_captures':len(captures)},indent=2))
