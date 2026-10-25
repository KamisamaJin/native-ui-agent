import copy,json,pathlib,hashlib,re
b=pathlib.Path(__file__).parent
root=b.parents[2]/'submissions/unit-40372769/final/source'
c=json.loads((b/'catalog.json').read_text());t=copy.deepcopy(json.loads((b/'template.json').read_text()));rows={r['review_id']:r for r in c['rows']}
sw='alerttoast/Sources/AlertToast/ListeningBreakPanel.swift';kt='reply/Reply/app/src/main/java/com/example/reply/ui/components/ListeningBreakPanel.kt'
texts={f:(root/f).read_text() for f in c['files']};lines={f:s.splitlines() for f,s in texts.items()}
for f,m in c['files'].items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==m['sha256']
def E(f,a,z=None):
 z=a if z is None else z
 assert 1<=a<=z<=len(lines[f])
 return {'file':f,'sha256':c['files'][f]['sha256'],'start_line':a,'end_line':z}
def spans(f,items):return [E(f,*x) if isinstance(x,tuple) else E(f,x) for x in items]
def both(sa,ka):return spans(sw,sa)+spans(kt,ka)
def loc(f,s):
 found=[i for i,l in enumerate(lines[f],1) if s in l];assert found,(f,s);return found
known={
 'A-file-scope':('The complete sealed files contain only the two public input/option value models, ListeningBreakPanel, and its private identity/state/text/action/color helpers. There is no network/audio engine, observer code or unrelated declaration/global side effect. This does not establish preservation of upstream files.',both([(1,271)],[(1,302)])),
 'A-api':('Swift declares public Equatable option/input models with all exact fields and public initializers, and a public SwiftUI View initializer receiving input/onStart/onCancel. Kotlin declares the matching data classes and package-level @Composable with the optional Modifier. The Swift surface uses APIs available at iOS14; this is a source API judgment, not a new compile, archive or runtime check.',both([(1,54),(80,92)],[(1,1),(41,69)])),
 'A-input-domain':('Both accept the value input without modifying its copy or reordering options; ForEach/forEach visits the caller list directly. Available selection is tested against that same input. The full files contain only local UI/state/callback logic and no audio/network operation. Valid input is the caller precondition; no rejection of its specified domain appears.',both([(1,271)],[(1,302)])),
 'A-identifiers':('The sealed Swift canvas explicitly contains its children; distinct title/introduction/note/acknowledge/status/primary/cancel/footer identifiers remain on their elements, conditional error/summary IDs are present, and each native option Button receives listening.option. plus its input ID. Kotlin tags the corresponding elements and buttons with the same exact names.',both([(99,169),(183,212)],[(71,138),(143,146),(184,235)])),
 'A-selection':('Each option handler guards started/unavailable, assigns the one selectedID to the activated ID and clears error. Re-selecting the same ID does not clear it. Disabled flags reject unavailable options and all options when started; no multi-selection collection exists.',both([(85,96),(183,212)],[(66,69),(89,110)])),
 'A-validation':('The editing primary handler first resolves an available selected option, then acknowledgement. Missing both sets the exact both-condition error; missing selection alone and missing acknowledgement alone set their exact strings. All failing branches return or stay in the validation branch before either callback; started is left false.',both([(94,96),(224,242)],[(198,220)])),
 'A-cancel':('Cancel has no disabled condition on either platform. Its handler resets all four local fields and invokes current onCancel with current input.sessionID once. The same handler therefore applies to empty, repeated and started Cancel activations.',both([(152,160),(245,249)],[(222,231),(239,244),(268,287)])),
 'A-edit-error':('Option activation replaces selectedID and clears only error; the editing switch setter accepts either Boolean and clears error without touching selectedID. Both setters are disabled/guarded when started. Turning acknowledgement off retains the selected option.',both([(114,126),(188,191)],[(97,102),(143,153)])),
 'A-replacement':('Swift keys its stateful private child to a Hashable identity whose equality compares the entire Equatable input and whose hash includes every ordered option field and all copy. Unequal input destroys the child state before rendering replacement content; equal input retains it. Kotlin remember(input) similarly replaces the complete state synchronously in composition on value inequality. No effect/onChange/task or callback participates in this reset.',both([(3,34),(49,92)],[(41,69),(239,244)])),
 'A-colors':('The sealed source defines the specified opaque sRGB/ARGB role constants and applies canvas to the padded column/Cancel, state-selected option fills and border, primary/white action ink, and the prescribed title/body/muted/error text roles. The component installs no shadow, gradient or translucent fill/opacity modifier. This judges declarations/composition; rendered pixels and native-control appearance remain separate evidence.',both([(99,221),(253,271)],[(71,138),(158,235),(268,302)])),
 'A-spacing':('The single leading column fills offered width, adds internal 20 pt/dp padding and 12 pt/dp major gaps; option pairs use 4 pt/dp gaps. Option/action horizontal padding is 16 and vertical padding 12; options use a 1-unit border and 12-unit circular rounded corners. Both actions fill the content width and have no side-band decoration; the action text is inside the padded label/content. These are source values, not inferred AX padding.',both([(99,99),(165,169),(193,221)],[(71,78),(103,124),(268,287)])),
 'A-type':('Swift uses @ScaledMetric bases 24/16/14 with system font and regular default, semibold heading/option title/actions. Kotlin explicitly sets 24/16/14 sp, FontFamily.Default, Normal default and SemiBold for the same roles. Introduction, note, status/error/summary and acknowledgement use regular 16; details/footer use regular 14. These are declared scaled system values, not computed native text measurements.',both([(90,92),(99,163),(172,180),(193,197),(215,216)],[(80,86),(126,138),(158,160),(184,235),(247,264),(268,287)])),
 'A-callback-boundaries':('The only callback call sites in either complete sealed file are valid Start and Cancel. Validation branches, option/switch setters, Choose again/reset, body/composition and input identity handling have no callback calls. Handler closures are rebuilt from current input/onStart/onCancel, with no remember of a prior callback. Start passes current session and chosen ID; Cancel passes current session.',both([(1,271)],[(1,302)])),
 'A-leading':('Swift VStack alignment, copy multilineTextAlignment and expanding frames are leading, including action labels; the native switch style places its switch after the leading expanding label. Kotlin Column/option Column use Start, Text uses TextAlign.Start and fills width, and acknowledgement gives its leading text weight 1 before the trailing Switch. The helper is shared by every named copy/action role.',both([(99,127),(172,180),(193,221)],[(71,87),(121,131),(143,182),(247,287)])),
 'A-start-transition':('In Swift valid primaryAction clears error, assigns started = true and immediately calls current onStart(sessionID, option.id) once. Kotlin valid onClick likewise assigns state.copy(started = true, error = null) before onStart. Validation precedes these lines and no task/timer/dispatch is interposed. This proves source ordering only, not synchronous pixel presentation.',both([(224,242)],[(203,220)])),
 'A-primary-fill-boundary':('Swift primary uses its padded, full-width actionLabel as the complete unmodified custom ButtonStyle label: the 16-unit horizontal inset is inside a 12-unit circular rounded painted/content-shape rectangle, with no border or side decorations. Kotlin applies the full-width/minimum-size/tag to the Button surface, uses RoundedCornerShape(12.dp), no border/icon, and 16.dp horizontal contentPadding around the full-width text. Thus source composition shares the painted/control layout boundary and leaves its side padding as fill. Native rectangle sizes, pixels and physical hit behavior are separate checks.',both([(144,150),(172,180),(215,221),(253,256)],[(198,203),(247,287)])),
}
unknown={
 'A-bridge-boundary':('The bound files show that identity, local state, validation and callback arguments are owned by production. They do not include either supplied bridge, so this source-only catalog cannot establish that a bridge never forces identity, injects product state or synthesizes outcomes. The complete bridge-boundary proposition is left unknown rather than inferred from component code.',both([(36,96),(224,249)],[(57,69),(198,244)])),
 'A-evidence-boundary':('This review treats source literals/modifiers as declarations only. The two bound production files do not establish how an integration report distinguishes computed native facts, AX geometry and physical hit regions; that evidence-method proposition cannot be decided from these files. No AX bounds are used as font/padding/color measurements here.',both([(90,92),(172,221)],[(103,119),(247,287)])),
 'A-callback-evidence':('Component call sites establish transition control flow but do not establish preimplementation sealing of six checkpoints/assertions or the integration dispatch/epoch-verdict procedure. Those are outside the two-file bound source catalog. This row is unknown; the separate final original capture may support its own runtime claims.',both([(224,249)],[(198,231)])),
}
# Independently observed color declarations and their role uses, not screenshot-derived values.
color_uses={
 'canvas':([(152,169)],[ (71,76),(222,231)]),
 'option':([(183,186),(203,203)],[(89,119)]),
 'selectedOption':([(183,186),(203,203)],[(89,119)]),
 'unavailableOption':([(183,186),(203,203)],[(89,119)]),
 'primary':([(125,125),(144,147)],[(158,179),(198,203)]),
 'primaryInk':([(144,147)],[(198,203)]),
 'title':([(99,102)],[(80,83)]),
 'body':([(104,156),(194,196)],[(84,86),(126,138),(158,160),(184,231)]),
 'muted':([(162,163),(194,197)],[(126,131),(233,235)]),
 'error':([(133,135)],[(188,190)]),
 'border':([(203,205)],[(111,112)]),
}
for dec in t['decisions']:
 r=rows[dec['review_id']];id=r['id'];datum=r['approved_datum']
 if id in known:reason,ev=known[id];actual=True
 elif id in unknown:reason,ev=unknown[id];actual=None
 elif id.startswith('A-color-'):
  role=id[len('A-color-'):];kn=role[0].upper()+role[1:];sm=re.search(r'static let '+re.escape(role)+r' = Color\(\.sRGB, red: ([^,]+), green: ([^,]+), blue: ([^,]+), opacity: ([^)]+)\)',texts[sw]);km=re.search(r'val '+re.escape(kn)+r' = Color\(0x([A-F0-9]+)\)',texts[kt]);assert sm and km
  def value(s):return float(s.split('/')[0].strip())/float(s.split('/')[1].strip()) if '/' in s else float(s)
  channels=[round(value(x)*255) for x in sm.groups()];sv=(channels[3]<<24)|(channels[0]<<16)|(channels[1]<<8)|channels[2];kv=int(km[1],16)
  actual=sv==kv==datum['value'] and datum['unit']=='argb';su,ku=color_uses[role];ev=both(su+loc(sw,'static let '+role+' ='),ku+loc(kt,'val '+kn+' ='))
  reason=f'The sealed Swift {role} constant explicitly uses .sRGB with normalized channels {sm[1]}, {sm[2]}, {sm[3]} and opacity {sm[4]}; Kotlin {kn} is 0x{km[1]}. Both declarations encode ARGB 0x{sv:08X}, and the cited call sites apply the role to its required content/surface. This is a declaration/role-use judgment, not a rendered-color measurement.'
 elif id.startswith('A-space-'):
  role,pl=id[len('A-space-'):].rsplit('-',1);f=sw if pl=='ios' else kt;unit='pt' if pl=='ios' else 'dp'
  entries={
   'canvasPadding':(20,[(165,167)] if pl=='ios' else [(71,78)],'canvas padding after filling the parent width'),
   'blockGap':(12,[99] if pl=='ios' else [77],'major column block and option spacing'),
   'optionTextGap':(4,[193] if pl=='ios' else [123],'internal option title/detail spacing'),
   'cornerRadius':(12,[(203,206),(220,221)] if pl=='ios' else loc(f,'shape = RoundedCornerShape(12.dp)'),'circular option and action rounded shapes'),
   'horizontalPadding':(16,[199,217] if pl=='ios' else loc(f,'contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp)'),'internal option/action horizontal content padding'),
   'verticalPadding':(12,[200,218] if pl=='ios' else loc(f,'contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp)'),'internal option/action vertical content padding'),
   'borderWidth':(1,[(204,205)] if pl=='ios' else [112],'option outline thickness'),
  };v,at,desc=entries[role];actual=(datum=={'value':v,'unit':unit});ev=spans(f,at);reason=f'The cited sealed {pl} declarations place {v} {unit} at the {desc}. This matches the approved native unit as a source modifier/shape value; no computed padding, painted geometry or hit-region measurement is inferred.'
 elif id.startswith('A-font-'):
  role,pl=id[len('A-font-'):].rsplit('-',1);f=sw if pl=='ios' else kt;unit='pt' if pl=='ios' else 'sp';values={'title':24,'body':16,'optionTitle':16,'detail':14,'action':16};v=values[role]
  anchors={'title':([(90,90),(99,102),(172,180)],[(80,83),(247,264)]),'body':([(91,91),(104,140),(172,180)],[(84,86),(136,138),(158,160),(184,195),(247,264)]),'optionTitle':([(91,91),(172,180),(193,197)],[(126,131),(247,264)]),'detail':([(92,92),(162,163),(172,180),(197,197)],[(131,131),(233,235),(247,264)]),'action':([(91,91),(172,180),(215,216)],[(247,287)])};ev=spans(f,anchors[role][0 if pl=='ios' else 1]);actual=datum=={'value':v,'unit':unit};reason=f'The sealed {pl} {role} uses a base size of {v} {unit}. '+('The @ScaledMetric supplies that base to Font.system(size:weight:), retaining system text scaling.' if pl=='ios' else 'The Text helper receives an explicit sp size and FontFamily.Default, retaining platform font scaling.')+' This is the declared base size and font family, not a computed runtime font measurement.'
 elif id.startswith('A-weight-'):
  role=id[len('A-weight-'):];v=400 if role in ['body','detail'] else 600
  anchors={'title':([(99,102),(172,175)],[(80,83),(247,260)]),'body':([(104,140),(172,175)],[(84,86),(136,138),(158,160),(184,195),(247,260)]),'optionTitle':([(193,197),(172,175)],[(126,131),(247,260)]),'detail':([(162,163),(172,175),(197,197)],[(131,131),(233,235),(247,260)]),'action':([(215,216),(172,175)],[(268,287),(247,260)])};sa,ka=anchors[role];ev=both(sa,ka);actual=datum=={'value':v,'unit':'scalar'};reason=f'For {role}, sealed Swift uses '+('the copy helper regular default' if v==400 else 'explicit .semibold')+' and sealed Kotlin uses '+('the helper FontWeight.Normal default' if v==400 else 'explicit FontWeight.SemiBold')+f', corresponding to the approved system weight {v}. This is source font selection, not an AX/computed-font measurement.'
 else:raise ValueError(id)
 assert actual is None or isinstance(actual,bool)
 assert set(x['file'] for x in ev)>=set(r['files']),id
 assert all(set(x)=={'file','sha256','start_line','end_line'} for x in ev)
 dec.update(actual=actual,reason=reason,evidence=ev)
(b/'submission.json').write_text(json.dumps(t,indent=2)+'\n')
print('Source decisions',len(t['decisions']),'true',sum(x['actual'] is True for x in t['decisions']),'false',sum(x['actual'] is False for x in t['decisions']),'unknown',sum(x['actual'] is None for x in t['decisions']))
