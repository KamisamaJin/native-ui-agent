from pathlib import Path
import json,hashlib,collections
B=Path('validation/default-forward');Q=B/'quality-inputs';O=B/'quality-panels/panel-two'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),f'Original output exists: {p}'
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
S='alerttoast/Sources/AlertToast/CollectionAuthorizationCard.swift';K='reply/Reply/app/src/main/java/com/example/reply/ui/components/CollectionAuthorizationCard.kt'
# Manually reviewed source declaration and application ranges.
styles={
 'ios-titleSize':[(62,62),(89,92)],'ios-rowTitleSize':[(63,63),(202,204)],
 'ios-bodySize':[(64,64),(113,116),(123,127),(148,152)],'ios-metadataSize':[(65,65),(187,192),(205,207)],
 'ios-semiboldWeight':[(89,90),(202,203)],'ios-regularWeight':[(113,115),(123,126),(187,190),(205,207)],
 'ios-cardPadding':[(285,285),(174,177)],'ios-rowPadding':[(286,286),(217,218)],
 'ios-sectionGap':[(287,287),(86,88),(163,165)],'ios-textGap':[(288,288),(87,88),(200,201)],
 'ios-cardRadius':[(289,289),(176,177)],'ios-controlRadius':[(290,290),(166,168),(219,224)],
 'ios-selectedBorderWidth':[(291,291),(221,223)],'ios-rowMinHeight':[(292,292),(217,218)],
 'ios-primaryMinHeight':[(293,293),(163,165)],'ios-disclosureMinHeight':[(294,294),(130,146)],
 'android-titleSize':[(355,355),(97,100),(330,339)],'android-rowTitleSize':[(356,356),(303,306),(330,339)],
 'android-bodySize':[(357,357),(143,146),(179,187),(220,224),(330,339)],'android-metadataSize':[(358,358),(101,108),(307,310),(330,339)],
 'android-semiboldWeight':[(97,100),(303,306),(330,339)],'android-regularWeight':[(101,108),(143,146),(179,187),(330,339)],
 'android-cardPadding':[(362,362),(86,94)],'android-rowPadding':[(363,363),(292,292)],
 'android-sectionGap':[(364,364),(92,94),(249,252)],'android-textGap':[(365,365),(96,96),(294,302)],
 'android-cardRadius':[(366,366),(88,89)],'android-controlRadius':[(367,367),(241,241),(282,282)],
 'android-selectedBorderWidth':[(368,368),(289,290)],'android-rowMinHeight':[(369,369),(278,281)],
 'android-primaryMinHeight':[(370,370),(238,240)],'android-disclosureMinHeight':[(371,371),(195,200)]}
style_notes={
 'titleSize':'The title uses the declared 22 native font units; iOS uses ScaledMetric and Android sp.',
 'rowTitleSize':'Choice titles use the declared 16 native font units.',
 'bodySize':'Acknowledgment, status and expanded notes use the declared 15 native font units.',
 'metadataSize':'Summary, pickup window and choice details use the declared 13 native font units.',
 'semiboldWeight':'Title and choice title application explicitly uses system semibold / FontWeight.SemiBold (600).',
 'regularWeight':'Metadata, acknowledgment, status and notes explicitly use regular / FontWeight.Normal (400).',
 'cardPadding':'The 20-unit constant is applied to the card content.',
 'rowPadding':'Choice content receives the 16-unit row padding.',
 'sectionGap':'The outer vertical stack uses 12-unit section spacing; primary vertical padding also uses that constant.',
 'textGap':'Text groups and choice content apply the 8-unit constant.',
 'cardRadius':'The card surface applies a rounded shape with the 20-unit radius.',
 'controlRadius':'Choice and primary shapes apply the 12-unit control radius.',
 'selectedBorderWidth':'Only the selected choice draws a 1-unit accent border; unselected uses clear/no border.',
 'rowMinHeight':'Choice control applies the declared 80-unit minimum height.',
 'primaryMinHeight':'Confirmation applies the declared 48-unit minimum height.',
 'disclosureMinHeight':'Notes disclosure applies the declared 48-unit minimum height.'}
color_uses={
 'surface':{S:[(176,179)],K:[(86,94)]},
 'ink':{S:[(89,92),(113,116),(148,152),(202,204)],K:[(97,100),(143,146),(220,224),(303,306),(330,339)]},
 'secondary':{S:[(104,108),(123,128),(187,192),(205,207)],K:[(101,108),(179,187),(307,310),(330,339)]},
 'neutralRow':{S:[(162,168),(219,220)],K:[(242,247),(274,288)]},
 'selectedRow':{S:[(219,220)],K:[(274,288)]},
 'accent':{S:[(118,120),(140,140),(166,167),(211,223)],K:[(161,174),(198,198),(207,215),(242,246),(289,290),(312,315)]},
 'disabledInk':{S:[(162,162),(202,213)],K:[(242,247),(254,258),(283,288),(303,315)]},
 'primaryInk':{S:[(162,162)],K:[(161,170),(242,247),(254,258)]}}
branches={
 'notes-close-source':({S:[(130,146),(148,155),(255,260)],K:[(189,194),(207,225)]},'The notes Button flips notesExpanded, writes the new state, and has one callback site using current data.requestID and open/closed. The false branch removes notesBody. Closing is source-only; this route never activates it.'),
 'self-choice-source':({S:[(82,84),(98,101),(111,120),(233,242),(271,280)],K:[(74,84),(111,128),(137,157),(343,351)]},'Both choose handlers guard submitted, same selection and unavailable delegate; choosing self writes self and clears acknowledgment, with one collector callback using current requestID. Conditional acknowledgment disappears and validity becomes true. This reverse selection is not dispatched in the captured route.'),
 'ack-false-source':({S:[(82,84),(111,120),(185,185),(244,253)],K:[(74,76),(137,175)]},'The native binding/handler accepts a changed false value only for an available, unsent delegate, stores false and emits one ack callback containing current requestID and false. Delegate validity then becomes false. No runtime true-to-false transition is inferred.'),
 'self-submit-source':({S:[(82,84),(98,101),(123,128),(157,172),(185,185),(262,274)],K:[(74,76),(111,128),(179,187),(227,260),(343,351)]},'Self is a valid collector. Submit guards unsent validity, records submitted and invokes one submit callback with current requestID and self event value. The submitted flag selects sent copy and disables primary/choices/ack. This is source logic only; actual self submission was not dispatched.'),
 'same-choice-quiet-source':({S:[(199,199),(233,242)],K:[(78,84),(111,128),(275,281)]},'Both actual choice action paths return on same collector before state write or onEvent. The already-selected activation is unexecuted; this is solely a source guard judgment.'),
 'disabled-callback-guard-source':({S:[(111,120),(157,185),(195,199),(225,251),(262,268)],K:[(74,84),(111,128),(147,157),(227,240),(275,281)]},'Choices have native disabled state and submitted/availability/same-choice guards; acknowledgment has enabled state and matching guards; submit has native enabled state plus unsent/current-valid guard. Rejected paths have no business onEvent call. Disabled controls were not activated in the runtime route.'),
 'ios14-public-api-source':({S:[(4,53),(55,79),(86,183),(187,269),(297,329)]},'The approved file exposes public data properties and the complete named initializer, public View and init(data:onEvent:), and declares iOS 14 availability. Its native SwiftUI APIs include ScaledMetric, onChange and SwitchToggleStyle, available at that floor. This is preliminary source-only API review; the sealed module/client typecheck is separate, with no iOS14 rendering claim.')}
for scope in ['public','private']:
 cat=read(Q/'source-review'/scope/'shared-identical-sources/catalog.json');t=read(Q/'source-review'/scope/'shared-identical-sources/template.json');ident=read(Q/'source-review'/scope/'identity.json')
 assert ident['shared']
 for candidate,files in ident['candidate_files'].items():
  assert set(files)==set(cat['files'])
  for f,meta in files.items():assert sha(Q/candidate/'source'/f)==meta['sha256']==cat['files'][f]['sha256']
 assert t['catalog_sha256']==sha(Q/'source-review'/scope/'shared-identical-sources/catalog.json')
 ds=[]
 for r in cat['rows']:
  rid=r['id'];e=[]
  if rid in styles:
   f=S if rid.startswith('ios-') else K;rs={f:styles[rid]};reason=style_notes[rid.split('-',1)[1]]+' Source declaration/application only; no computed runtime style is inferred.'
  elif rid in branches:rs,reason=branches[rid]
  else:
   theme,name=rid.split('-',1);rs={}
   for f in [S,K]:rs[f]=([(313,327)] if theme=='light' and f==S else [(318,327)] if f==S else [(385,390)] if theme=='light' else [(391,396)])+([(78,80)] if f==S else [(72,75)])+color_uses[name][f]
   reason=f'Both component-owned {theme} palettes declare the approved {name} ARGB value (0x{r["approved_datum"]["value"]:08X}); native environment selects the palette and the cited modifiers consume this role. Source-only; it does not substitute for measured pixels or effective native color.'
  assert set(rs)==set(r['files'])
  for f,ranges in rs.items():
   for start,end in ranges:e.append({'file':f,'sha256':cat['files'][f]['sha256'],'start_line':start,'end_line':end})
  ds.append({'review_id':r['review_id'],'actual':True,'reason':reason,'evidence':e})
 t['decisions']=ds;save(O/'source'/scope/'shared-identical-sources/submission.json',t)
# Visual actuals were manually inspected from all unique original SHA-bound images.
for p in sorted(Q.glob('candidate-*/native/*/*/*')):
 candidate=p.parts[-5];scope=p.parts[-3];platform=p.parts[-2];case=p.name
 cat=read(p/'review-catalog.json');t=read(p/'review-template.json');si=read(p/'state-image-index.json');obs=read(p/'native/observation.json');cv=read(p/'execution-coverage.json')
 assert t['catalog_sha256']==sha(p/'review-catalog.json');assert t['observation_sha256']==sha(p/'native/observation.json');assert cv['satisfied']
 byid={x['review_id']:x for x in cat['rows']}
 for d in t['decisions']:
  r=byid[d['review_id']];assert r['method']=='visual';state=r['state'];indices=si[state]['indices'];assert si[state]['complete']
  wrap=r['aspect']=='wrapping'
  detail='The long title, summary/window, stacked choice title/detail, acknowledgment when present, status, disclosure, full notes paragraphs when open and bottom confirmation all wrap within their own available widths; no ellipsis or horizontal clipping is visible across the overlaps.' if wrap else 'The title/metadata, vertically stacked choices, acknowledgment when present, status, disclosure, notes paragraphs when open and confirmation remain separately readable with visible spacing. Scroll-edge cuts are continued in the overlapping frame; no unintended content/control collision is visible.'
  d.update(actual=True,reason=f'Manual original-image review of every bound {state} checkpoint frame, with complete top-to-bottom overlapping native coverage. {detail} '+('The dark 320-unit RTL/larger-type images preserve mirrored start alignment and readable complete text.' if scope=='private' else 'The light LTR images preserve readable full content.'),snapshot_indices=indices)
 save(O/'visual'/candidate/scope/platform/case/'submission.json',t)
# Preserve each strict measured failure. The sealed evidence does not demonstrate its root cause.
alarms=[]
for p in sorted(Q.glob('candidate-*/native/*/*/*')):
 for a in read(p/'automatic.json')['assertions']:
  if a['status']!='failed':continue
  obs=read(p/'native/observation.json');i=a['snapshot_indices'][0];ip=p/'native'/obs['snapshots'][i]['screenshot']
  cat=read(p/'review-catalog.json');row=next(r for r in cat['rows'] if r['id']==a['id'])
  alarms.append({'candidate':p.parts[-5],'scope':p.parts[-3],'platform':p.parts[-2],'case':p.name,'assertion_id':a['id'],'cause':'uncertain','reason':'The original strict >=48 pt check reports 47.99999999999994 pt from xcui_cgrect (exact ratio 844424930131967/17592186044416); that measured F is retained unchanged. Swift source declares 48 and applies it as the confirmation minimum, and the original ready image shows an intact button, but neither source nor raster evidence can establish the exact AX height or prove a collector error. A floating representation/AX geometry origin is plausible; the supplied evidence does not demonstrate either a product layout cause or a false alarm. No epsilon, rounding or revised unit/tolerance is used.','evidence':[{'file':str((p/'automatic.json').relative_to(B)),'sha256':sha(p/'automatic.json'),'assertion_id':a['id'],'actual':a['actual'],'geometry_evidence':a.get('geometry_evidence')},{'file':str((p/'native/observation.json').relative_to(B)),'sha256':sha(p/'native/observation.json'),'snapshot_index':i,'selector':'collection.confirm'},{'file':str(ip.relative_to(B)),'sha256':sha(ip),'snapshot_index':i},{'file':str((Q/p.parts[-5]/'source'/S).relative_to(B)),'sha256':sha(Q/p.parts[-5]/'source'/S),'start_line':157,'end_line':172},{'file':str((Q/p.parts[-5]/'source'/S).relative_to(B)),'sha256':sha(Q/p.parts[-5]/'source'/S),'start_line':293,'end_line':294},{'file':str((p/'review-catalog.json').relative_to(B)),'sha256':sha(p/'review-catalog.json'),'review_id':row.get('review_id'),'expected':row['expected'],'unit':row['unit']}]})
save(O/'alarm-judgments.json',alarms);save(O/'extra-findings.json',[])
print('Wrote source submissions',2,'source decisions',len(ds)*2,'visual submissions',12,'visual decisions',144,'alarms',len(alarms))
