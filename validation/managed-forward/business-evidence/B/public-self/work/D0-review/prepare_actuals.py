import json,hashlib
from pathlib import Path
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/cache/study/arms/B');out=b/'work/D0-review'
source_paths={
 'ios':b/'workspace/alerttoast/Sources/AlertToast/MenuChangeReviewPanel.swift',
 'android':b/'workspace/reply/Reply/app/src/main/java/com/example/reply/ui/components/MenuChangeReviewPanel.kt'}
lines={
'ios': {'api':[3,25,62,80,167,181],'state':[85,94,100,170,190,216],'selection':[116,252,258,458],'quantity':[109,293,315,463,468],'balance':[120,124,159,361,382],'credit':[90,107,120,331],'acceptance':[104,332,421,424,464,473],'revision':[100,190,216],'submission':[80,458,468,477],'typography':[172,221,231,236,265,389,442],'layout':[194,208,211,221,252,276,372,404,421],'controls':[277,315,322,440,446],'palette':[137,187,278,284,325,445,449,452],'direction':[194,221,295,252,159],'accessibility':[214,238,285,326,346,351,378,435,454]},
'android': {'api':[48,58,74,82,158],'state':[87,96,129,163,166],'selection':[110,207,212,396],'quantity':[103,214,224,235,249,434],'balance':[113,116,152,272,519],'credit':[92,104,257,266],'acceptance':[105,217,238,252,305,315,341],'revision':[96,166,169,183,272,291],'submission':[82,209,235,266,315,323],'typography':[183,185,365,384,423,454,524,536,353],'layout':[173,180,183,207,291,293,305,365,388],'controls':[342,351,408,416,446],'palette':[137,169,201,273,345,403,414,423,490],'direction':[182,207,224,365,152],'accessibility':[176,187,243,273,298,342,409,420,447,463,481,505,531]}}
reasons={
'api':'Exports the exact required DTO fields, initializers/data classes, typed submission, wire format and component API; private product helpers reside in this file. D0 successfully rendered this production component; this is source/API evidence, not a fresh compile.',
'state':'Draft initializes no selection, requested count, credit/acceptance/sent false inside component state. Reconciliation returns existing state for identical request/revision and resets through initial(model) for a different request.',
'selection':'Iterates caller option order and stable IDs, resolves only available options, disables unavailable/sent buttons, ignores selecting the current ID and clears acceptance on changed selection.',
'quantity':'Selection and revision reconciliation clamp current count to inclusive bounds. Each guarded action changes by one and clears acceptance. Native buttons disable with no valid choice, at the relevant bound or after send.',
'balance':'Uses Int cents for price times servings minus prepaid minus applied credit. Currency helper uses ASCII dollar/decimal with two digits and no grouping; negative balance uses absolute money and Refund, zero uses No balance due. Display derives from current model.',
'credit':'Credit starts false, is available for positive credit before send independently of selection, toggling clears acceptance, and revision reconciliation forces false when offered credit becomes zero.',
'acceptance':'Selection, count and credit changes plus revision clear acceptance. Switch requires a valid selection and unsent state; send additionally requires acceptance and an unsent valid selection.',
'revision':'Same request/new revision retains only a still available option ID, clamps current servings, retains only positive offered credit and clears accepted/sent. UI uses new model fields immediately at the stable call site; no .id/key recreation.',
'submission':'Only the send handler calls onSubmit with current model request/revision, selected ID, current count/credit/signed balance, then marks sent; all edit and reconciliation paths are silent and guards block resending.',
'typography':'Reviewed source base roles: eyebrow 12/500, title 28/700, detail/context 13/400, section 18/600, body 15/400, option title 15/600, amount 26/700, button 16/600 and count 20/600. Native system fonts; Swift uses iOS-14 ScaledMetric and Compose uses sp, without a scale cap. These are source declarations, not computed runtime styles.',
'layout':'Non-scrolling vertical flow preserves all text. Source uses outer 16, sections 20, card padding 12/radius16/border1/gap8, option gap8, paragraph gap10, footer16 and root radius20 in native units; wrapping has no line limit/ellipsis/fixed text height.',
'controls':'Actual option control labels have min height64, quantity min width/height44, send min height52 and horizontal16/vertical14 padding. Text can grow vertically and quantity buttons share one row with a flexible wrapping count.',
'palette':'Every light/dark role matches the public palette and is selected from caller theme. Cards remain solid surfaces, selected options use selection/accent, unavailable titles/details use secondary, refunds accent, enabled/disabled send colors are explicit; no complete-row opacity.',
'direction':'Uses native leading/start alignment and native horizontal flow, never forces LTR/RTL or reverses caller arrays. Quantity uses normal integer interpolation and money retains required ASCII formatting.',
'accessibility':'Production container/child IDs are unique, options have one actual native button with exact title label/selected state, and credit/acceptance are actual native switches with labels/state. Summary preserves child targets, last note has its ID, and no hidden product clone or test style readback exists.'}
for pl in ['ios','android']:
 root=b/'runs/D0'/pl/'cycle';req=json.loads((root/'after-review-request.json').read_text());o=json.loads((root/'capture/native/observation.json').read_text());states={s['state_id']:s['snapshot_indices'] for s in o['state_captures']};sub=req['submission_template'];by={r['review_id']:r for r in req['rows']}
 for dec in sub['decisions']:
  row=by[dec['review_id']];state,rule=row['id'].split('/');indices=states[state]
  dec['actual']=True
  if rule=='title-wrapping':dec['snapshot_indices']=[indices[0]];dec['reason']=f'{pl} {state}: the full current Cedar Hall occasion title is visible in wrapped lines, including its ending, without truncation or ellipsis.'
  elif rule=='title-hierarchy':dec['snapshot_indices']=indices[:2];dec['reason']=f'{pl} {state}: the occasion title is visibly larger and bolder than Choose a replacement and other section headings.'
  elif rule=='option-clipping':dec['snapshot_indices']=indices[:3];dec['reason']=f'{pl} {state}: overlapping original frames show every option description through its final sentence, plus price/range/unavailable text, within growing cards. '+('The iOS disabled card is visibly faded; that separate palette defect does not clip its text.' if pl=='ios' else 'No clipped description is visible.')
  elif rule=='balance-overlap':dec['snapshot_indices']=indices[3:5];dec['reason']=f'{pl} {state}: the balance card uses separate vertical rows for selection, totals, prepaid, credit and balance; the balance label/amount do not overlap adjacent text.'
 (out/f'{pl}-image-actuals.json').write_text(json.dumps(sub,ensure_ascii=False,indent=2)+'\n')
 source=json.loads((root/'source-review-template.json').read_text())
 bridge=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-design/public')/('Bridge.swift' if pl=='ios' else 'ObserverBridge.kt')
 for obs in source['observations']:
  if obs['id'].startswith('component.'):
   key=obs['id'].split('.')[1];obs['observed']=True;obs['reason']=reasons[key];obs['citations']=[{'path':str(source_paths[pl]),'line':n} for n in lines[pl][key]]
   if key=='palette' and pl=='ios':obs['observed']=False;obs['reason']='Palette constants match the contract, but each custom-colored Button uses PlainButtonStyle before .disabled. Original D0 frames show full unavailable rows and disabled send/quantity labels faded; native pixel send-fill fails in six disabled states. Thus complete-row attenuation violates the palette duty despite correct declared colors. Cause hypothesis: PlainButtonStyle applies disabled opacity.'
  else:
   obs['observed']=True;obs['reason']='Fixed bridge decodes the current immutable DTO and directly calls the imported production component at one stable call site; it forwards submission.wireValue without selection/count/money/revision state or keyed recreation.';obs['citations']=[{'path':str(bridge),'line':n} for n in ([7,8,9,10] if pl=='ios' else [11,14,27,41,43])]
 (out/f'{pl}-source-actuals.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
print('Prepared original actuals for both platforms without changing source or expected values.')
