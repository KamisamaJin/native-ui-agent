import hashlib,json,pathlib,sys
out=pathlib.Path(__file__).resolve().parent.parent
base=out.parents[1]
q=base/'quality-inputs'
def read(p):return json.loads(p.read_text())
def save(p,v):
 assert not p.exists(),f'Original exists: {p}'
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
sw='alerttoast/Sources/AlertToast/CollectionAuthorizationCard.swift'
kt='reply/Reply/app/src/main/java/com/example/reply/ui/components/CollectionAuthorizationCard.kt'
# Independently read declaration and application locations, not runtime computed properties.
styles={
'ios-titleSize':([(62,62),(89,93)],'ScaledMetric starts at 22 pt and the title Text applies that system font with semibold weight.'),
'ios-rowTitleSize':([(63,63),(202,204)],'ScaledMetric starts at 16 pt and choice-title Text applies it.'),
'ios-bodySize':([(64,64),(111,128),(148,154)],'ScaledMetric starts at 15 pt; acknowledgment, status and notes body apply it.'),
'ios-metadataSize':([(65,65),(187,192),(205,207)],'ScaledMetric starts at 13 pt; caller metadata and choice details apply it.'),
'ios-semiboldWeight':([(89,90),(202,204)],'System font semibold is explicitly applied to title and choice titles; this is the source weight declaration, not a measured font.'),
'ios-regularWeight':([(113,116),(187,190),(205,207)],'System font regular is explicitly applied to acknowledgment, metadata and choice details.'),
'ios-cardPadding':([(285,285),(174,177)],'20 pt cardPadding is applied to the outer VStack.'),
'ios-rowPadding':([(286,286),(217,218),(163,165)],'16 pt rowPadding is applied inside both choice buttons and horizontally inside confirmation.'),
'ios-sectionGap':([(287,287),(86,88),(163,165)],'12 pt sectionGap is applied between VStack sections and vertically inside confirmation.'),
'ios-textGap':([(288,288),(87,88),(199,201)],'8 pt textGap is applied within metadata and row text groups.'),
'ios-cardRadius':([(289,289),(176,177)],'20 pt cardRadius is applied to the filled card RoundedRectangle.'),
'ios-controlRadius':([(290,290),(165,168),(218,224)],'12 pt controlRadius is applied to confirmation and choice backgrounds/content shapes.'),
'ios-selectedBorderWidth':([(291,291),(221,223)],'1 pt selectedBorderWidth is applied with accent when selected and a clear stroke otherwise.'),
'ios-rowMinHeight':([(292,292),(217,220)],'80 pt rowMinHeight is applied as a minimum, allowing choice content to grow.'),
'ios-primaryMinHeight':([(293,293),(163,168)],'48 pt primaryMinHeight is declared and applied with frame(minHeight:). This source match does not resolve the separate native AX height alarm.'),
'ios-disclosureMinHeight':([(294,294),(140,143)],'48 pt disclosureMinHeight is applied to the notes Button label frame.'),
'android-titleSize':([(355,355),(97,100),(330,339)],'22.sp is passed to CollectionText for title; TextStyle applies fontSize.'),
'android-rowTitleSize':([(356,356),(303,306),(330,339)],'16.sp is passed to CollectionText for each choice title and applied by TextStyle.'),
'android-bodySize':([(357,357),(143,145),(179,186),(220,224),(330,339)],'15.sp is passed for acknowledgment, status and notes body and applied by TextStyle.'),
'android-metadataSize':([(358,358),(101,108),(307,310),(330,339)],'13.sp is passed for caller metadata and row details and applied by TextStyle.'),
'android-semiboldWeight':([(97,100),(303,306),(330,339)],'FontWeight.SemiBold is passed for title and row titles and applied to TextStyle.fontWeight.'),
'android-regularWeight':([(101,108),(143,145),(307,310),(330,339)],'FontWeight.Normal is passed for metadata, acknowledgment and details and applied to TextStyle.fontWeight.'),
'android-cardPadding':([(362,362),(86,94)],'20.dp cardPadding is applied inside the outer Column background.'),
'android-rowPadding':([(363,363),(292,292),(249,252)],'16.dp rowPadding is applied through choice contentPadding and horizontal confirmation contentPadding.'),
'android-sectionGap':([(364,364),(93,93),(249,252)],'12.dp sectionGap is applied between main Column sections and vertically inside confirmation.'),
'android-textGap':([(365,365),(96,96),(294,302)],'8.dp textGap is applied inside metadata and row text groups.'),
'android-cardRadius':([(366,366),(86,92)],'20.dp cardRadius is applied to the outer surface RoundedCornerShape.'),
'android-controlRadius':([(367,367),(241,241),(282,282)],'12.dp controlRadius is applied to confirmation and choice RoundedCornerShape.'),
'android-selectedBorderWidth':([(368,368),(289,290)],'1.dp selectedBorderWidth is applied as an accent BorderStroke for selected rows only.'),
'android-rowMinHeight':([(369,369),(278,282)],'80.dp rowMinHeight is applied using heightIn(min), allowing content growth.'),
'android-primaryMinHeight':([(370,370),(237,241)],'48.dp primaryMinHeight is applied using heightIn(min) to confirmation.'),
'android-disclosureMinHeight':([(371,371),(195,200)],'48.dp disclosureMinHeight is applied using heightIn(min) to the notes TextButton.'),
}
color_use_sw={'surface':[(176,177)],'ink':[(89,91),(113,116),(148,151),(202,204)],'secondary':[(123,128),(187,190),(205,207)],'neutralRow':[(165,167),(218,220)],'selectedRow':[(218,220)],'accent':[(118,118),(140,140),(165,167),(221,223)],'disabledInk':[(158,162),(202,213)],'primaryInk':[(158,162)]}
color_use_kt={'surface':[(86,92)],'ink':[(97,100),(143,145),(220,223),(303,305)],'secondary':[(101,108),(179,185),(307,310)],'neutralRow':[(242,247),(274,288)],'selectedRow':[(274,288)],'accent':[(161,170),(198,198),(242,247),(289,290)],'disabledInk':[(242,247),(254,258),(283,288),(303,315)],'primaryInk':[(161,170),(242,247),(254,258)]}
branches={
'notes-close-source':({sw:[(130,146),(148,155),(255,260)],kt:[(189,224)]},'Source-only: the notes button inverts notesExpanded, commits it, and has one request-bound event call choosing closed when false; the body is conditional on notesExpanded. The selected native route did not execute closing.'),
'self-choice-source':({sw:[(82,84),(98,101),(111,121),(233,242),(271,274)],kt:[(74,84),(111,128),(137,148),(343,345)]},'Source-only: the self row calls the common chooser; a different unsent choice assigns self, clears acknowledgment and calls the request-bound collector event once. Self makes valid true and excludes the acknowledgment branch. No self-after-delegate native activation was exercised.'),
'ack-false-source':({sw:[(82,84),(185,185),(244,253)],kt:[(74,76),(147,157)]},'Source-only: the guarded acknowledgment setter accepts a changed false value before submission, commits false and calls one current-request ack event. Delegate validity then requires the now-false acknowledgment. The runtime route only toggled true.'),
'self-submit-source':({sw:[(82,84),(157,172),(185,185),(262,274)],kt:[(74,76),(179,181),(227,259),(343,345)]},'Source-only: self is valid, confirmation is enabled while unsent, and the guarded handler records submitted before one submit event using self raw/event value. Submitted controls, label and status read submitted. Native confirmation covered delegate only.'),
'same-choice-quiet-source':({sw:[(233,242)],kt:[(78,84)]},'Source-only: equality with the current collector returns before state mutation and the sole collector event call. No same-choice dispatch or empty runtime event interval is inferred.'),
'disabled-callback-guard-source':({sw:[(185,185),(197,199),(226,227),(233,253),(262,268)],kt:[(78,84),(111,128),(147,157),(227,237),(275,288)]},'Source-only: native enabled/disabled bindings are paired with business guards. Choice returns for submitted or unavailable delegate; acknowledgment requires unsent available delegate and a changed value; confirmation requires unsent and valid. No disabled-control runtime activation was attempted.'),
'ios14-public-api-source':({sw:[(1,70),(118,120),(178,182)]},'Source-only preliminary review: public data fields/initializer and public View init match the unchanged Bridge.swift caller; ScaledMetric and onChange are used inside an iOS 14-available component. The sealed separate minimum-api record for every candidate reports real-module emission and unchanged-caller typechecking at arm64-apple-ios14.0-simulator with both exits 0; that record is separate evidence, not iOS 14 runtime, link or rendering proof.'),
}
for scope in ['public','private']:
 root=q/'source-review'/scope;cat=read(root/'shared-identical-sources/catalog.json');identity=read(root/'identity.json');temp=read(root/'shared-identical-sources/template.json')
 assert identity['shared'] and temp['catalog_sha256']==digest(cat)
 for c,files in identity['candidate_files'].items():
  for f,v in cat['files'].items():
   assert files[f]['sha256']==v['sha256']==sha(q/c/'source'/f)
 decisions=[]
 for row in cat['rows']:
  rid=row['id']; ev=[]
  if rid in styles:
   ranges,reason=styles[rid];paths={sw:ranges} if rid.startswith('ios-') else {kt:ranges}
  elif rid.startswith(('light-','dark-')):
   theme,name=rid.split('-',1);decl_sw=(313,317) if theme=='light' else (318,322);decl_kt=(385,390) if theme=='light' else (391,396)
   paths={sw:[decl_sw,(78,80)]+color_use_sw[name],kt:[decl_kt,(73,73)]+color_use_kt[name]}
   value=f"0x{row['approved_datum']['value']:08X}"
   reason=f'Source-only: {theme} {name} is declared as {value} in both production palettes; the environment chooses the palette and the cited component modifier/style calls apply this role. Swift ARGB conversion preserves all four channels. This is no computed color or pixel assertion.'
  else:paths,reason=branches[rid]
  assert set(paths)==set(row['files'])
  for f,ranges in paths.items():
   for start,end in ranges:ev.append({'file':f,'sha256':cat['files'][f]['sha256'],'start_line':start,'end_line':end})
  decisions.append({'review_id':row['review_id'],'actual':True,'reason':reason+' Source declaration/branch review only; no unexecuted runtime proof.','evidence':ev})
 save(out/'source'/scope/'shared-identical-sources/submission.json',{'version':1,'catalog_sha256':temp['catalog_sha256'],'decisions':decisions})

state_details={
'ready':'title, summary and pickup window precede two separate choice rows, status, collapsed notes and confirmation',
'notes_open':'the opened notes follow the choice/status/disclosure section; all paragraphs continue across overlapping frames and end before confirmation',
'delegate_chosen':'the selected delegate row is followed by a wrapped acknowledgment label and separate native switch, invalid status, open notes, and disabled confirmation',
'authorized':'the acknowledged delegate section, valid status, open notes and enabled confirmation remain separated',
'submitted':'the retained delegate selection and switch, sent status, readable open notes, and disabled sent button remain separated',
'replacement':'the replacement title/summary/window, self and disabled delegate rows, unavailability explanation, status, collapsed notes and enabled confirmation remain separated',
}
alarms=[];coverage_summaries=[]
manifest=read(out/'inspection/image-manifest.json')
for case in sorted(q.glob('candidate-*/native/*/*/*')):
 candidate,scope,platform,scenario=case.parts[-5],case.parts[-3],case.parts[-2],case.name
 cat=read(case/'review-catalog.json');temp=read(case/'review-template.json');obs=read(case/'native/observation.json');states=read(case/'state-image-index.json');ec=read(case/'execution-coverage.json');auto=read(case/'automatic.json');env=read(case/'environment-check.json')
 assert temp['catalog_sha256']==digest(cat) and temp['observation_sha256']==sha(case/'native/observation.json')
 assert ec['satisfied'] and env['status']=='P' and read(case/'source-before.json')==read(case/'source-after.json')
 stsum=[];decisions=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  state=row['state'];indices=states[state]['indices'];caps=[c for c in obs['state_captures'] if c.get('state_id')==state and c.get('snapshot_indices')==indices]
  assert states[state]['complete'] and len(caps)==1
  cap=caps[0];assert cap['complete'] and cap['top_reached'] and cap['bottom_reached'] and cap['stable_binding'] and cap['max_gap']==0
  if row['aspect']=='overlap':
   reason=f'Original full-content {state} scan reviewed at every cited frame: {state_details[state]}. No text/control collision or unintended overlap is visible; viewport-edge cutoffs are covered by neighboring original frames.'
  else:
   assert row['aspect']=='wrapping'
   mode='larger-font dark RTL' if scope=='private' else 'normal-font light LTR'
   reason=f'Original {mode} full-content {state} scan reviewed at every cited frame. Caller labels and visible paragraphs stay within the card content width and wrap to additional lines; no horizontal clipping or ellipsis is visible. The complete scan includes the final visible content and bottom action.'
  decisions.append({'review_id':row['review_id'],'actual':True,'reason':reason,'snapshot_indices':indices})
 assert len(decisions)==12
 save(out/'visual'/candidate/scope/platform/scenario/'submission.json',{'version':1,'catalog_sha256':temp['catalog_sha256'],'observation_sha256':temp['observation_sha256'],'decisions':decisions})
 for state,rec in states.items():
  cap=next(c for c in obs['state_captures'] if c.get('state_id')==state and c.get('snapshot_indices')==rec['indices'])
  stsum.append({k:cap.get(k) for k in ['state_id','snapshot_indices','complete','top_reached','bottom_reached','stable_binding','max_gap','binding','intervals','content_height']})
 steps=[]
 request='PRINT-4821' if scope=='public' else 'PRINT-7316'
 expected=[f'notes:{request}:open',f'collector:{request}:delegate',f'ack:{request}:true',f'submit:{request}:delegate']
 action_steps=[s for s in obs['steps'] if s.get('dispatch',{}).get('attempted')]
 assert len(action_steps)==5
 for n,step in enumerate(action_steps):
  d=step['dispatch'];cb=[v['event'] if isinstance(v,dict) else v for v in step['callback_delta']]
  assert d['succeeded'] is True and d['event_start']==min(n,4) and d['event_end']==min(n+1,4)
  assert cb==([expected[n]] if n<4 else [])
  before=d['binding_before'];after=step['binding_after'];assert before['instance']==after['instance']
  if n<4:assert d['matches']==d['native_controls']==1 and d['enabled'] and before['input_sha256']==after['input_sha256'] and before['fixture_index']==after['fixture_index']==0
  else:assert d['method']=='caller_fixture_update' and before['fixture_index']==0 and after['fixture_index']==1 and before['input_sha256']!=after['input_sha256']
  steps.append({'state':step.get('state_id'),'dispatch':d,'callbacks':cb,'binding_after':after,'activation_target':step.get('activation_target'),'semantic_node':step.get('semantic_node'),'activation_node':step.get('activation_node')})
 coverage_summaries.append({'case_path':str(case.relative_to(q)),'observation_sha256':sha(case/'native/observation.json'),'source_before_after_equal':True,'environment_status':env['status'],'automatic_counts':auto['counts'],'original_failed_assertion_ids':auto['failed_assertion_ids'],'states':stsum,'actions':steps})
 for a in auto['assertions']:
  if a['status']!='failed':continue
  assert a['id']=='ready/primary-min-height' and platform=='ios' and scope=='public'
  image=next(v for v in manifest if v['candidate']==candidate and v['scope']==scope and v['platform']==platform and v['snapshot_index']==2)
  ev=[{'file':str((case/'automatic.json').relative_to(base)),'sha256':sha(case/'automatic.json'),'assertion_id':a['id'],'actual':a['actual'],'snapshot_indices':a['snapshot_indices']},
      {'file':str((case/'native/observation.json').relative_to(base)),'sha256':sha(case/'native/observation.json'),'pointer':'/snapshots/2/control_groups','selector':{'identifier':'collection.confirm'},'frame':{'height':47.99999999999994,'width':318,'x':42,'y':476.3333333333333}},
      {'file':'quality-inputs/'+image['file'],'sha256':image['sha256'],'snapshot_index':2},
      {'file':str((q/candidate/'source'/sw).relative_to(base)),'sha256':sha(q/candidate/'source'/sw),'start_line':163,'end_line':172},
      {'file':str((q/candidate/'source'/sw).relative_to(base)),'sha256':sha(q/candidate/'source'/sw),'start_line':293,'end_line':293},
      {'file':'design/public/reference.json','sha256':sha(base/'design/public/reference.json'),'pointer':'/style/layout/ios/primaryMinHeight','value':48,'unit':'pt'},
      {'file':'candidate-v10/scripts/native_geometry.py','sha256':sha(base/'candidate-v10/scripts/native_geometry.py'),'start_line':1,'end_line':85}]
  alarms.append({'candidate':candidate,'scope':scope,'platform':platform,'case':scenario,'assertion_id':a['id'],'cause':'uncertain','reason':'The original strict native comparison fails: the unique fully visible confirmation control reports 47.99999999999994 pt against gte 48 pt, with no tolerance. I preserve that measured F exactly. Production declares 48 and applies frame(minHeight:) to the real Button label, and the original image shows a normal complete button, but declarations and pixels cannot establish the exact observed accessibility rectangle. A floating-point/AX representation artifact is plausible; no demonstrated serialization mistake or product layout cause is available from these records. I therefore establish neither a product defect nor a false alarm, and do not round the actual, modify the design, or claim a native pass.','evidence':ev})
save(out/'alarm-judgments.json',alarms)
save(out/'extra-findings.json',[])
save(out/'inspection/native-evidence-summary.json',coverage_summaries)
print('Written source submissions',2,'source decisions',sum(len(read(p)['decisions']) for p in out.glob('source/*/*/submission.json')),'visual submissions',len(list(out.glob('visual/*/*/*/*/submission.json'))),'visual decisions',sum(len(read(p)['decisions']) for p in out.glob('visual/*/*/*/*/submission.json')),'alarms',len(alarms))
