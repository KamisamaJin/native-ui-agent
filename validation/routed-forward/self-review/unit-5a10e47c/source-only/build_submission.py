import json, pathlib, hashlib, collections
here=pathlib.Path(__file__).resolve().parent
root=here.parents[2]
sealed=root/'submissions/unit-5a10e47c/final/source'
catalog=json.loads((here/'catalog.json').read_text())
sub=json.loads((here/'template.json').read_text())
S='alerttoast/Sources/AlertToast/ListeningBreakPanel.swift'
K='reply/Reply/app/src/main/java/com/example/reply/ui/components/ListeningBreakPanel.kt'
for f,m in catalog['files'].items():
    assert hashlib.sha256((sealed/f).read_bytes()).hexdigest()==m['sha256']
# Each judgment below was made from the exact sealed lines displayed in this review.
# Ranges cite declared values/control flow; none are computed rendering measurements.
observations={
'A-file-scope':(True,'Both complete files contain only the public option/input models, panel and necessary private state, identity, text/action/style and color helpers. Their initializers only store values; there is no audio, network, unrelated declaration or global side effect.',[(1,275)],[(1,302)]),
'A-api':(True,'Swift declares public Equatable value models with all named public properties and initializers, and the exact public View initializer with escaping callbacks, explicitly available on iOS 14. Kotlin declares the matching data classes and public composable in the required package with the default modifier. This is signature/availability source review, not a new compiler or runtime claim.',[(3,54)],[(1,1),(41,66)]),
'A-input-domain':(True,'The models retain all valid supplied strings/options without filtering or reordering. ForEach/forEach iterates the caller array/list, and handlers use session and option IDs directly. Neither file imports or owns an audio engine or networking operation.',[(3,34),(96,114),(226,245)],[(41,55),(67,95),(198,235)]),
'A-identifiers':(True,'The Swift containing canvas has its own identifier; fields, toggle, actions and dynamic option buttons each declare the required separate stable identifier. Kotlin declares the corresponding test tags, including conditional error and summary and the option ID suffix.',[(100,171),(185,214)],[(71,146),(184,234),(267,286)]),
'A-selection':(True,'Each available option activation assigns only its ID, so reselecting keeps it and another selection replaces it. Both the native enabled condition and handler guard reject unavailable options and all option edits after starting.',[(185,214)],[(89,110)]),
'A-validation':(True,'The primary handlers first handle Choose again, then require an available selected option and acknowledgement. All invalid branches assign exactly the applicable both/selection/acknowledgement string and return or bypass callback execution; the valid branch alone calls onStart.',[(226,245),(96,98)],[(198,220)]),
'A-cancel':(True,'Cancel has no state-dependent disable, resets all local fields, and directly invokes current onCancel with current input.sessionID once per activation, including repeated empty editing activations.',[(154,162),(247,252)],[(222,244),(267,287)]),
'A-edit-error':(True,'Available option selection clears error while preserving acknowledgement. The editing toggle writes the new Boolean and clears error without changing selected ID, so switching off preserves selection. Started controls cannot edit.',[(116,129),(185,194)],[(96,102),(143,154),(239,244)]),
'A-replacement':(True,'Swift keys its stateful child by an identity whose equality is synthesized full input equality and whose hash includes every ordered option field. Kotlin remember(input) creates fresh initial local state on unequal value input; equal value input retains state. Neither reset path calls a callback or defers replacement handling.',[(3,34),(50,98),(247,252)],[(41,69),(239,244)]),
'A-bridge-boundary':(None,'The listed production files place identity, state transitions and callback argument selection inside the components, but these two files do not contain the supplied bridges. Their complete proposition that neither bridge forces identity, state or events cannot be established by this source-only catalog. No bridge-content pass is inferred from component code.',[(50,98),(226,252)],[(57,69),(198,244)]),
'A-colors':(True,'Both palettes explicitly declare the exact opaque sRGB role values and the view call sites assign those roles to canvas, available/selected/unavailable surfaces, title/body/detail/footer/error and actions. The source declares no custom shadows, gradients or opacity modifiers. This judgment concerns declared source styling; native pixel color is independently checked from the original captures.',[(100,169),(185,223),(255,275)],[(71,138),(184,234),(267,302)]),
'A-spacing':(True,'Both panels declare a filling leading column with 20-unit canvas padding and 12-unit block spacing, option pairs with a 4-unit gap, circular rounded 12-unit option/action shapes, 16-horizontal and 12-vertical content padding and 1-unit option outlines. The primary label is inside the inset with only fill outside it, and actions fill column width.',[(100,101),(167,182),(195,223)],[(71,78),(103,131),(275,286)]),
'A-type':(True,'Swift scales 24/16/14 system fonts through ScaledMetric, using semibold for heading, option titles and actions and regular for remaining copy. Kotlin uses the same 24/16/14 sp sizes, system FontFamily.Default, explicit SemiBold for heading/options/actions and Normal otherwise. These are source font inputs, not measured rendered sizes.',[(92,94),(100,165),(174,199),(217,218)],[(80,138),(158,159),(184,194),(232,264),(286,286)]),
'A-evidence-boundary':(None,'The production source exposes font, padding and color declarations, but it cannot establish how the integration review separates them from AX/native rectangle evidence. This source-only audit does not promote these declarations into computed native typography, padding, color or physical hit-region measurements.',[(92,94),(174,223)],[(246,286)]),
'A-callback-evidence':(None,'The source contains real native handlers and direct callbacks, but the two production files cannot establish that six checkpoints/assertions were fixed before implementation or prove enabled-target dispatch and same-process caller replacement. Those facts belong to separate integration receipts and original native observations, not this source-only decision.',[(146,162),(226,252)],[(96,110),(143,154),(198,244)]),
'A-callback-boundaries':(True,'Only the valid start branch and Cancel activation invoke caller callbacks. Selection/toggle setters, invalid-start branches, Choose again and input-identity state construction contain no callback invocation. Current input and current callback properties/parameters are used directly without storing stale closures.',[(38,54),(116,122),(154,156),(190,194),(226,252)],[(57,69),(96,102),(147,154),(198,244)]),
'A-leading':(True,'Swift copy uses leading multiline alignment and full-width leading frames for every field/action; both VStack levels also lead, and the native switch toggle keeps its label before its trailing switch. Kotlin TextAlign.Start, Alignment.Start, full-width text and a weighted acknowledgement label before the Switch implement the same leading/trailing layout.',[(100,129),(174,223)],[(71,87),(121,131),(143,182),(246,286)]),
'A-start-transition':(True,'Swift clears error then sets started=true at line 243 immediately before onStart at 244. Kotlin assigns state.copy(started=true,error=null) at 217 immediately before onStart at 218. Both use current sessionID and selected available option ID once with no timer/task/dispatch deferral. This establishes source ordering only.',[(226,245)],[(203,219)]),
'A-primary-fill-boundary':(True,'Swift renders the padded, minimum-sized action label inside a circular rounded fill and matching content shape, with a ButtonStyle returning that label unchanged. Kotlin paints its Button shape at the same full-width control bounds, with 16-unit content inset, no action border/icons/decoration and 12-unit rounded corners. Text is confined to the inner layout area. This is composition review, separate from native rectangle measurements.',[(146,152),(174,182),(217,223),(255,259)],[(198,202),(246,264),(267,287)]),
}
colors={
'canvas':(264,291,'#FFF2F6F4',[(154,169)],[(71,76),(222,226)]),
'option':(265,292,'#FFFFFFFF',[(185,188),(205,205)],[(89,118)]),
'selectedOption':(266,293,'#FFE8F3EF',[(185,188),(205,205)],[(89,118)]),
'unavailableOption':(267,294,'#FFF0F2F1',[(185,188),(205,205)],[(89,118)]),
'primary':(268,295,'#FF176B58',[(146,149),(217,223)],[(198,202),(275,284)]),
'primaryInk':(269,296,'#FFFFFFFF',[(146,149),(217,223)],[(198,202),(275,286)]),
'title':(270,297,'#FF172F2A',[(102,104),(174,178)],[(80,83),(254,259)]),
'body':(271,298,'#FF38564E',[(106,165),(195,198)],[(84,86),(126,138),(158,159),(184,194),(222,226)]),
'muted':(272,299,'#FF687A75',[(164,165),(195,199)],[(126,131),(232,234)]),
'error':(273,300,'#FFB0382C',[(135,137)],[(188,189)]),
'border':(274,301,'#FFABC6BC',[(205,207)],[(111,112)]),
}
for name,(sl,kl,color,suses,kuses) in colors.items():
 observations['A-color-'+name]=(True,f'The Swift opaque sRGB channels and the Kotlin 0xFF ARGB literal both declare {color}; the cited call sites apply the {name} role to its specified source surfaces/text. This is an exact declaration/role review, not a sampled pixel value.',[(sl,sl)]+suses,[(kl,kl)]+kuses)
spaces={
'canvasPadding':(20,[(167,169)],[(71,78)],'internal canvas padding'),
'blockGap':(12,[(100,101)],[(71,78)],'major-block column spacing'),
'optionTextGap':(4,[(195,199)],[(121,131)],'title/detail gap inside each option'),
'cornerRadius':(12,[(205,208),(222,223)],[(111,112),(282,284)],'option/action circular rounded corner radius'),
'horizontalPadding':(16,[(201,202),(217,223)],[(119,119),(284,284)],'option and action horizontal content padding'),
'verticalPadding':(12,[(201,202),(217,223)],[(119,119),(284,284)],'option and action vertical content padding'),
'borderWidth':(1,[(205,207)],[(111,112)],'option outline width'),
}
for name,(value,sranges,kranges,placement) in spaces.items():
 for pl,ranges,unit in [('ios',sranges,'pt'),('android',kranges,'dp')]:
  observations[f'A-space-{name}-{pl}']=(True,f'The {pl} source declares {value} {unit} for {placement} at the cited placement. This is the source constant/modifier input, not a measured native inset.',ranges if pl=='ios' else [],ranges if pl=='android' else [])
fonts={
'title':(24,600,[(92,92),(102,104),(174,182)],[(80,83),(254,264)]),
'body':(16,400,[(93,93),(106,142),(174,182)],[(84,86),(136,159),(184,194),(246,264)]),
'optionTitle':(16,600,[(93,93),(195,199),(174,182)],[(126,131),(254,264)]),
'detail':(14,400,[(94,94),(164,165),(174,182),(199,199)],[(131,131),(232,234),(246,264)]),
'action':(16,600,[(93,93),(174,182),(217,218)],[(275,286),(254,264)]),
}
for name,(size,weight,sranges,kranges) in fonts.items():
 for pl,ranges,unit in [('ios',sranges,'pt'),('android',kranges,'sp')]:
  observations[f'A-font-{name}-{pl}']=(True,f'The {name} source text uses base size {size} {unit}. Swift combines ScaledMetric with system fonts; Kotlin sp and FontFamily.Default use platform system scaling. No computed runtime font size is inferred.',ranges if pl=='ios' else [],ranges if pl=='android' else [])
 observations[f'A-weight-{name}']=(True,f'The {name} source text selects '+('semibold (system weight 600)' if weight==600 else 'regular/Normal (system weight 400)')+' through the cited helper defaults or explicit overrides on both platforms; this is a source font-weight judgment.',sranges,kranges)
rows={r['review_id']:r for r in catalog['rows']}
assert set(observations)=={r['id'] for r in catalog['rows']}
for d in sub['decisions']:
 r=rows[d['review_id']];actual,reason,sranges,kranges=observations[r['id']]
 d['actual']=actual;d['reason']=reason;d['evidence']=[]
 for f,ranges in [(S,sranges),(K,kranges)]:
  if f not in r['files']:continue
  for start,end in ranges:
   assert 1<=start<=end<=catalog['files'][f]['line_count']
   d['evidence'].append({'file':f,'sha256':catalog['files'][f]['sha256'],'start_line':start,'end_line':end})
 if actual is not None:assert {e['file'] for e in d['evidence']}==set(r['files'])
 assert all(set(e)=={'file','sha256','start_line','end_line'} for e in d['evidence'])
(here/'submission.json').write_text(json.dumps(sub,indent=2)+'\n')
print('Source observations',dict(collections.Counter(str(d['actual']) for d in sub['decisions'])))
print('Unknown ids',[rows[d['review_id']]['id'] for d in sub['decisions'] if d['actual'] is None])
