from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,collections
r=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/dispatch-forward');own=r/'evidence/own-d0/sample-e318ec';out=r/'private/submissions/sample-e318ec';assets=out/'review-assets'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ev(p,**kwargs):return {'path':str(p),'sha256':sha(p),**kwargs}
def native_ev(pl,case,ix):
 d=own/pl/case;o=json.loads((d/'observation.json').read_text());return [ev(d/'observation.json',snapshot=ix),ev(d/o['snapshots'][ix]['screenshot'],snapshot=ix)]
findings=[]
colors=[
 ('R001','waterRound.submit','disabled action surface color','#293C2F','#1F3126','134933 solid interior pixels'),
 ('R002','waterRound.submit','disabled action label foreground color','#92A396','#596A5E','2911 solid glyph-core pixels'),
 ('R003','waterRound.method.drip','disabled selected method surface color','#244F33','#1D3A28','172918 solid interior pixels'),
 ('R004','waterRound.method.drip','disabled selected method name foreground color','#E7F3E9','#829789','2200 solid glyph-core pixels in Drip lines'),
 ('R005','waterRound.method.drip','disabled selected method border color','#81D89B','#4F8962','7886 border/icon-color pixels'),
 ('R006','waterRound.method.drip','disabled selected method rate foreground color','#B2C8B8','#688170','1175 solid glyph-core pixels in 9 L per bed'),
 ('R007','waterRound.method.soak','disabled unselected method border color','#3B5242','#283C2F','6380 border-color pixels'),
 ('R008','waterRound.method.soak','disabled unselected method name foreground color','#E7F3E9','#7E8C83','2595 solid glyph-core pixels in Soak hoses'),
 ('R009','waterRound.method.soak','disabled unselected method rate foreground color','#B2C8B8','#64776A','1685 solid glyph-core pixels in 11 L per bed'),
]
for id,target,aspect,expected,observed,count in colors:
 findings.append({'id':id,'platform':'ios','case':'C04','checkpoint':'initial / cp-initial.full','category':'visual','method':'native_pixels + visual','target':target,'aspect':aspect,'certainty':'confirmed','claim':f'The rendered {aspect} is dimmed from the specified opaque dark palette.','expected':expected,'observed':f'{observed}; {count}; specified color absent from the sampled control region.','evidence':native_ev('ios','C04',3)+[ev(assets/'ios-C04-pixel-analysis.json',snapshot=3)],'related_cluster':'ios-disabled-native-style-opacity'})
rtl=[
 ('R010','waterRound.method.soak','fixed English method rate visual order','14 L per bed','L per bed 14'),
 ('R011','waterRound.required','numeric summary amount/unit visual order','70 L','L 70'),
 ('R012','waterRound.required','fixed English summary label punctuation order','Required:',':Required'),
]
for id,target,aspect,expected,observed in rtl:
 findings.append({'id':id,'platform':'android','case':'C02','checkpoint':'initial / cp-initial.full','category':'visual','method':'visual of original native PNG, cross-checked with native label','target':target,'aspect':aspect,'certainty':'confirmed','claim':f'The RTL layout reverses the fixed English run for this {aspect}.','expected':expected,'observed':observed,'evidence':native_ev('android','C02',5),'related_cluster':'android-fixed-runs-inherit-rtl'})
findings.append({'id':'U001','platform':'android','case':'C01','checkpoint':'initial / cp-initial.full','category':'visual','method':'native_text_layout + visual','target':'waterRound.method.drip / descendant native Text "Drip lines" (node 17)','aspect':'rendered text overflow/clipping','certainty':'uncertain','claim':'The native text layout reports hasVisualOverflow, but the image does not establish that a glyph is clipped.','expected':'All text visible without clipping.','observed':'Snapshot 2 node 17 has overflow=true, ellipsized=false, one line; the complete Drip lines string appears visible. This flag alone is not promoted to a confirmed clipping defect.','evidence':native_ev('android','C01',2)+[ev(assets/'additional-native-facts.json',snapshot=2)],'related_cluster':'android-text-layout-overflow-flag'})
inventory=[]
for pl in ['ios','android']:
 for c in ['C01','C02','C03','C04']:
  for name in ['observation.json','fixtures.json']:
   inventory.append(ev(own/pl/c/name,examined_by='native typed checks and independent model/action review'))
for c in ['C01','C02','C03','C04']:inventory.append(ev(r/f'private/inputs/d0-v2/{c}/mapping.json',examined_by='checkpoint/input mapping review'))
for item in json.loads((assets/'visual-inventory.json').read_text()):inventory.append({**item,'examined_by':'full original content through labeled contact sheet; R001-R012 representative originals also opened directly'})
for p in [r/'design/public/brief.md',r/'design/public/api.md',r/'design/public/reference.svg',r/'cache/unit-59af93/alerttoast/Sources/AlertToast/WaterRound.swift',r/'cache/unit-59af93/reply/Reply/app/src/main/java/com/example/reply/ui/waterround/WaterRound.kt',r/'opaque-collector/scripts/native_checks.py',r/'opaque-collector/assets/android-observer/NativeObserverTest.kt',out/'d0-corpus-seal.json']:
 inventory.append(ev(p,examined_by='assigned design/API, source provenance, relevant observer/check implementation'))
reports=[];counts=collections.Counter();eventcounts=collections.Counter()
for p in sorted(assets.glob('*-checks.json')):
 j=json.loads(p.read_text());counts.update(j['counts']);eventcounts.update(x['status']for x in j['assertions']if '-event-'in x['id']);reports.append({**ev(p),'counts':j['counts'],'coverage':'Only listed atomic assertions; no complete requirement claim.'})
report={
 'submission':'sample-e318ec','stage':'read_only_review','assigned_tool':'opaque-collector','start_utc':'2026-10-20 01:45:27 UTC','end_utc':datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
 'evidence_root':str(own),'corpus_seal':ev(out/'d0-corpus-seal.json'),'production_sources_unchanged':True,
 'checked_scope':[
  {'aspect':'native controls/content/calculations','scope':'Both platforms, C01-C04, initial and explicit caller-replaced full-content epochs; mapped action checkpoints assessed when actually visible.','method':'Assigned native_checks.py plans derived from public brief/API and original fixtures. Checked exact title/description/notice/fact/summary/status/action labels, conditional control presence, enabled/selected/checked state.','result':'No confirmed contradiction among available typed observations; offscreen/unsupported facts remain U in each report.'},
  {'aspect':'callbacks and caller replacements','scope':'Both platforms C01-C04 mapped triggers.','method':'Typed actual callback intervals; successful unique native dispatch and same input/session binding required.','result':dict(eventcounts),'limits':'Eight disabled activations had no demonstrated dispatch and therefore cannot establish handler silence. Replacements succeeded and established quietness for their actual intervals.'},
  {'aspect':'native visual content and layout','scope':'Both platforms C01-C04 initial and replaced epochs, all 57 selected original full-sweep PNGs.','method':'Full-content labeled contact sheets with original screenshot references; representative originals opened directly.','result':'Long text wraps and the sampled full-content sweeps reach the footer. Hierarchy, conditional content, selection, consent, status and progress visually inspected. Confirmed palette/RTL deviations are listed atomically.'},
  {'aspect':'native typography','scope':'Android tagged title, description, facts and status via TextLayout font_sp/font_weight/ellipsized, with explicit per-assertion results.','method':'Native exported TextLayout values; iOS unavailable fields left U.','limits':'No blanket typography pass; mixed/compound and iOS typography remain unmeasured where the observer does not expose them.'},
  {'aspect':'physical touch bounds','scope':'Android only, fully visible actual control samples within the selected full-content epochs.','method':'Native Compose touchBoundsInRoot values, not semantic bounds or screenshots.','result':'52 fully visible samples were at least 44 by 44 dp.','evidence':ev(assets/'additional-native-facts.json'),'limits':'This is a bound/sample result; no OS physical-touch route was executed. iOS physical hit regions remain U.'},
  {'aspect':'exact colors','scope':'iOS C04 initial disabled submit and method control native pixel regions.','method':'Exact opaque interior/core RGB counts in original PNG, native XCUI frames only used to locate regions.','evidence':ev(assets/'ios-C04-pixel-analysis.json')},
  {'aspect':'public source API and controlled ownership','scope':'Own two production files and supplied public API.','method':'Static source review, kept separate from runtime proof.','result':'Required immutable models/actions/entries present; no local remembered selection, consent or submitting state.'}
 ],
 'unassessed_scope':[
  'Exact iOS runtime font sizes/weights, all exact internal padding, and iOS physical hit regions: U; source constants and AX frames do not establish them.',
  'Native font family/monospaced-digit features and unsupported compound text run properties: U beyond visible appearance/source declaration.',
  'Shortfall-positive inputs, soakAllowed=false inputs, isEnabled=false together with isSubmitting=true, and other unprovided condition combinations were not present in this corpus.',
  'Already-selected method tap no-op and missing-consent activation-route behavior were not established by a successful matching activation in this corpus.',
  'No event/handler-silence claim for the eight blocked disabled activations; only their disabled native state is assessed.',
  'No independent pixel golden exists. Reference SVG is design intention; no screenshot-difference pass is claimed for native font rasterization.',
  'Android hasVisualOverflow flags on several native text leaves need interpretation; visible clipping is not confirmed by those flags alone.',
  'No OS-level Android physical touch, macOS runtime, unseen inputs, new native captures, or other submission evidence was reviewed.'
 ],
 'findings':findings,
 'related_clusters':[
  {'id':'ios-disabled-native-style-opacity','findings':['R001','R002','R003','R004','R005','R006','R007','R008','R009'],'independent_root_cause_count':1,'source_hypothesis':'PlainButtonStyle applies native disabled dimming after the explicit colors.','related_observed_recurrences':['iOS C04 cp-a03.full snapshot 13','iOS C02 cp-initial.full snapshot 5 disabled release'],'counting_note':'Nine independently sampled atomic color facets; one related root-cause cluster, not nine independent defects. Recurrences are not additional findings.'},
  {'id':'android-fixed-runs-inherit-rtl','findings':['R010','R011','R012'],'independent_root_cause_count':1,'source_hypothesis':'Fixed English TextStyle runs inherit RTL direction; native labels retain original string while pixel glyph order changes.','counting_note':'Three observed text-order facets; one related root-cause cluster. Other strings/epochs are not silently multiplied into findings.'},
  {'id':'android-text-layout-overflow-flag','findings':['U001'],'independent_root_cause_count':None,'counting_note':'Uncertain observation, not a confirmed product defect or a basis for speculative repair.'}
 ],
 'duplicates':[],
 'summary':{'confirmed_atomic_findings':12,'uncertain_findings':1,'confirmed_related_root_cause_clusters':2,'typed_assertion_counts':dict(counts),'typed_callback_assertion_counts':dict(eventcounts),'visual_original_png_count':57},
 'typed_check_reports':reports,
 'evidence_inventory':inventory,
 'derived_review_artifacts':[ev(p)for p in sorted(assets.glob('*'))if p.is_file()and p.suffix in ['.jpg','.json','.py']],
 'read_only_attestation':'No production source or host/bridge/test configuration was changed and no native capture was run during this review.'
}
(out/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(out/'review.json'),'end_utc':report['end_utc'],'summary':report['summary'],'inventory_count':len(inventory)},ensure_ascii=False))
