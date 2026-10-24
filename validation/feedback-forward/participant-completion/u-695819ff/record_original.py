import json,pathlib,hashlib,time,shutil
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward/corpora/T2/d0');d=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward/design/T2/public')
findings=[]
for platform in ['ios','android']:
 for case in ['P1','P2']:
  p=b/platform/case/'native/observation.json';o=json.load(open(p));c=json.load(open(d/'compiled'/case/platform/'review-catalog.json'))
  for st in o['state_captures']:
   if st['state_id'] not in ['overview','permitted','requested','requested-closed','replaced']:continue
   ev=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]
   for idx in st['snapshot_indices']:
    q=pathlib.Path(o['snapshots'][idx]['screenshot']);q=q if q.is_absolute() else p.parent/q
    ev.append({'path':str(q),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
   findings.append({'id':f"original-{platform}-{case}-{st['state_id']}-visual",'origin':'manual','status':'passed','platform':platform,'case':case,'assertion_ids':[r['id'] for r in c['rows'] if r['method']=='visual' and r['state']==st['state_id']],'reason':'Reviewed the original overlapping full-state PNG sweep via labeled contact sheet: supplied text wraps visibly, title/section hierarchy is clear, content stays within horizontal bounds, rows do not overlap, flow remains in one column, painted status/primary/ink are square rectangular silhouettes without border strokes, and painted primary fills its visible allocation. Expanded chapter pairs remain ordered and readable through the footer; collapsed states show no chapter text. This qualitative judgment does not assert computed fonts, color, padding or physical hit areas.','snapshot_indices':st['snapshot_indices'],'evidence':ev})
pathlib.Path('agent-output/claims.json').write_text(json.dumps({'findings':findings},indent=2))
orig=pathlib.Path('agent-output/source-versions/original');orig.mkdir(parents=True,exist_ok=True)
for p in ['alerttoast/Sources/AlertToast/OfflineAudioTourPanel.swift','reply/Reply/app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt']:
 q=orig/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
pathlib.Path('agent-output/diagnosis-original.json').write_text(json.dumps({'atUnix':time.time(),'source_original_bound':True,'automatic_failures':'Android P1/P2 have five selected-choice label failures each. The actual raw node label aggregates decorative checkmark with Wi-Fi only.','cause_limit':'Assigned NativeObserverTest.kt label(n) recursively aggregates unmerged descendant Text without respecting an ancestor clearAndSetSemantics boundary. The original Box already clears semantics; this evidence alone does not prove a TalkBack defect.','directed_change':'Also clear semantics on the decorative glyph Text leaf itself, making the label independent of consumer traversal. No behavior or visual layout change is intended.','unresolved_original':'Android P1 has 5 additional automatic U beyond qualitative U; preserve observation limitations for final fresh review.'},indent=2))
