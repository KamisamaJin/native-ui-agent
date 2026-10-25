from pathlib import Path
import json,hashlib,datetime,collections
B=Path('validation/routed-forward/quality-inputs');O=Path('validation/routed-forward/quality-panels/panel-two');D=Path('validation/routed-forward/design')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
reasons={
'A-file-scope':'Both complete declared files contain only the public value models, component, and necessary private state, identity, text, button-style and palette helpers. No unrelated declaration or global side effect appears. This does not establish upstream-byte preservation.',
'A-api':'Swift public Equatable value structs, public initializers and View initializer match the independent API; Kotlin data classes, package, composable signature and default modifier match. The source uses the iOS 14 API surface; this is a declaration/API review, not an iOS 14 runtime claim.',
'A-input-domain':'The files consume the ordered options directly with their supplied ASCII IDs and copy, preserving valid caller order, and contain no audio or networking operation. Invalid caller inputs are outside the stated valid-input domain.',
'A-identifiers':'The specified constant identifiers and option-ID-derived identifier are attached in production source. This source-only judgment concerns declarations and composition; runtime selector exposure is a separate native fact.',
'A-selection':'Available option handlers assign one selected ID without toggling it off, overwrite a previous ID, and clear error. Availability and started guards plus disabled state prevent unavailable choice selection.',
'A-validation':'The editing handler first resolves an available selected option and checks acknowledgement; all three error branches match the exact API strings, return without callbacks and leave started false.',
'A-cancel':'Cancel has no disabled condition, resets all four local values, and invokes current onCancel with current sessionID once on each activation, including an already empty editing state.',
'A-edit-error':'Option and acknowledgement change handlers clear error; acknowledgement assignment changes only acknowledgement/error and preserves selected ID. The editing toggle accepts false.',
'A-replacement':'Swift identity equality compares the complete Equatable input, hashing every ordered field, and places local State inside that identity. Kotlin remember(input) creates default local state on unequal value input. Equal values preserve state; identity/reset constructors emit no callback.',
'A-callback-boundaries':'Only the valid primary branch and Cancel call supplied callbacks. Selection, toggle, validation, reset/Choose again and input identity replacement contain no callback call; handler closures use current input and callback arguments.',
'A-leading':'The shared Swift copy helper sets multiline and frame alignment leading, its columns lead, and the labeled native Toggle places its switch after the label. Kotlin TextAlign.Start/full-width text, start columns, and weighted label before the Switch declare the corresponding alignment for all fields/actions.',
'A-start-transition':'The successful Swift branch assigns started=true immediately before one onStart(input.sessionID, option.id); Kotlin assigns state.copy(started=true,error=null) immediately before one onStart with current input/option. No timer, task or dispatch separates these statements. This proves source order only.',
'A-primary-fill-boundary':'Primary uses the shared full-width action label/control composition with 16 horizontal and 12 vertical padding, circular radius 12, opaque primary fill, no border/icons/decorations, and a plain Swift button style. Kotlin paints its Button boundary around its padded content. Source declarations establish composition only, not a measured physical hit region.',
'A-colors':'All independent opaque sRGB palette values are declared exactly and referenced in the required roles, including unavailable/selected surfaces, border, error, primary ink, canvas and Cancel. No source shadow, gradient or translucency is declared. This is source-only and does not assert computed pixels.',
'A-spacing':'The source declares a parent-width column, 20 canvas padding, 12 major/option spacing and circular corners, 4 within each option, 16/12 option/action insets, 1 option stroke and full-width actions. Action content is inside the shared painted shape. These are source declarations, not computed padding measurements.',
'A-type':'Swift @ScaledMetric sizes 24/16/14 flow into system fonts; Kotlin sp sizes 24/16/14 use the default system family. Title, option title and actions use semibold; other content uses regular/normal. This establishes declared scaling and base values, not computed runtime font sizes.'}
unknowns={
'A-bridge-boundary':'The catalog declares only the two production component files. They own product state, but the proposition also constrains supplied caller bridges, whose source is outside this declared evidence scope. Unknown for that complete proposition.',
'A-evidence-boundary':'This is a rule about how source and native evidence are interpreted. The two declared product files cannot establish evaluator/reviewer evidence policy. No computed style or physical hit-size conclusion is inferred.',
'A-callback-evidence':'Preimplementation freezing, native dispatch qualification and callback interval adjudication concern plans/observers outside the two declared production files. Source handler code cannot prove that integration evidence proposition.'}
# Identical typed source audit datums were checked independently across all six catalogs.
for catpath in sorted((B/'source-review').glob('*/*/catalog.json')):
 scope,candidate=catpath.parent.relative_to(B/'source-review').parts;cat=read(catpath);sub=read(catpath.parent/'template.json');rows={r['review_id']:r for r in cat['rows']}
 for x in sub['decisions']:
  r=rows[x['review_id']];aid=r['id'];x['actual']=None if aid in unknowns or (candidate=='candidate-d1cbcd54' and aid=='A-identifiers') else True
  if aid in unknowns:x['reason']='Source-only unknown: '+unknowns[aid]
  elif candidate=='candidate-d1cbcd54' and aid=='A-identifiers':x['reason']='Source-only unknown: every required identifier string is declared, but the canvas identifier is applied to an uncontained VStack and the option accessibility wrapper adds another semantic level. Stable runtime exposure cannot be established solely from declarations in these two files. Native identifier evidence is reported separately in extra-findings.'
  elif aid in reasons:x['reason']='Source-only: '+reasons[aid]
  elif aid.startswith('A-color-'):
   role=aid[len('A-color-'):];x['reason']=f'Source-only: exact {role} ARGB datum {r["approved_datum"]["value"]} is declared in the palette and used for its required role. No runtime pixel or computed-style claim.'
  elif aid.startswith('A-space-'):x['reason']=f'Source-only: the declared {aid[len("A-space-"):]} value/placement is {r["approved_datum"]["value"]} {r["approved_datum"]["unit"]}, matching the independent typed datum; geometry is assessed separately.'
  elif aid.startswith('A-font-'):x['reason']=f'Source-only: system/scaled text declares base size {r["approved_datum"]["value"]} {r["approved_datum"]["unit"]} for {aid[len("A-font-"):]}; Swift ScaledMetric or Kotlin sp supplies platform scaling. No computed font-size inference.'
  elif aid.startswith('A-weight-'):x['reason']=f'Source-only: {aid[len("A-weight-"):]} text declares system weight {r["approved_datum"]["value"]} (semibold/SemiBold for 600; regular/Normal for 400), matching the typed datum.'
  else:raise RuntimeError(aid)
  x['evidence']=[]
  for f in r['files']:
   desc=cat['files'][f];p=B/candidate/'source'/f;assert sha(p)==desc['sha256'];lines=p.read_text().splitlines();end=len(lines)
   if aid=='A-api':start=1;end=67 if f.endswith('.kt') else 56
   elif aid.startswith('A-font-') or aid.startswith('A-weight-') or aid=='A-type':start=71 if f.endswith('.kt') else 90
   elif aid.startswith('A-color-') or aid=='A-colors':start=71 if f.endswith('.kt') else 99
   elif aid.startswith('A-space-') or aid in ['A-spacing','A-leading','A-primary-fill-boundary']:start=71 if f.endswith('.kt') else 99
   elif aid in ['A-validation','A-start-transition']:start=198 if f.endswith('.kt') else 224
   elif aid=='A-selection':start=89 if f.endswith('.kt') else 182;end=134 if f.endswith('.kt') else 215
   else:start=1
   x['evidence'].append(dict(file=f,sha256=desc['sha256'],start_line=start,end_line=end))
 save(O/'source'/scope/candidate/'submission.json',sub)
# Original image inspection maps include exact hashes, qualification, source frame and unaltered crop pixels.
image_map=read(O/'inspection/image-map.json')
for p in sorted(B.glob('candidate-*/native/*/*/*')):
 candidate,_,scope,platform,case=p.relative_to(B).parts;cat=read(p/'review-catalog.json');sub=read(p/'review-template.json');obs=read(p/'native/observation.json');idx=read(p/'state-image-index.json');rows={r['review_id']:r for r in cat['rows']};steps={s['state_id']:s for s in obs['steps']}
 for x in sub['decisions']:
  r=rows[x['review_id']];state=r['state'];atom=r['requirement_id'];qualified=[m['snapshot_index'] for m in image_map if all(m[k]==v for k,v in dict(candidate=candidate,scope=scope,platform=platform,case=case,state=state).items())]
  fail=candidate=='candidate-d1cbcd54' and platform=='ios' and state!='ready'
  if fail:
   x['actual']=None;x['snapshot_indices']=[]
   if state=='replaced':x['reason']='Unknown for the required dirty-replacement checkpoint: caller_fixture_update succeeded in the same process and replacement images visibly show new copy, but prerequisite option/acknowledgement actions 9 and 10 were unavailable and not dispatched. A complete sweep alone cannot establish the required dirty-state action checkpoint.'
   else:x['reason']=f'Unknown: original steps for {state} report unavailable and dispatch.succeeded=false (the required child selectors are missing). Qualified sweep indices {idx[state]["indices"]} show an unchanged editing UI, but do not demonstrate this requested action state. No visual pass or behavioral failure is inferred from that unsuccessful stimulus.'
   continue
  assert idx[state]['complete'] and qualified
  if state!='ready':assert steps[state]['dispatch']['succeeded']
  x['actual']=True;x['snapshot_indices']=qualified
  if atom=='content-complete':rationale='the complete supplied title/introduction, all three ordered option title/detail pairs, note/footer and exact fixed acknowledgement/status/action labels are visibly readable; applicable validation error or started summary is present, and nonapplicable conditional text is absent'
  elif atom=='vertical-order':rationale='the sweep places title, introduction, three option title/detail pairs, note, acknowledgement, status, applicable error/summary, primary, Cancel and footer in that order; every option title precedes its detail. Presence and wrapping were judged separately'
  elif atom=='text-wrap':rationale='all supplied fields and fixed labels are readable across the overlapping viewport sweep; lines wrap within the column without visible ellipsis, horizontal clipping, horizontal scrolling, or text scaled down to fit. This does not measure computed fonts'
  elif atom=='content-overlap':rationale='text lines, the three option surfaces, acknowledgement row, status, applicable error/summary, actions and footer remain separated with no visible mutual overlap across the whole sweep'
  elif atom=='replacement-exclusion':rationale='each complete replacement field (including options matched by ID) appears without a separately retained complete initial-field instance. Public replacement title Harbor bells — still unavailable legitimately contains the old title Harbor bells; that shared substring is not an independent stale-copy instance'
  else:raise RuntimeError(atom)
  x['reason']=f'Original {scope}/{platform}/{case} {state} images, indices {qualified}, checked against the independently sealed input and checkpoint proposition: {rationale}. Exact original PNG hashes/frame/crop map: inspection/image-map.json. '+('Successful native action/replacement and stable epoch are recorded in original observation steps.' if state!='ready' else 'Initial binding and full vertical coverage are recorded in the original observation.')
 save(O/'visual'/candidate/scope/platform/case/'submission.json',sub)
print('wrote source and visual submissions')
