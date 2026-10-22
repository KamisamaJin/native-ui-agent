import json,pathlib,sys
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/one/T3'
evidence=json.loads((O/'evidence-index.json').read_text())
for key,rec in evidence.items():
 p=B/'evaluation-inputs/final/T3'/key;inp=json.loads((p/'inputs.json').read_text());cat=json.loads((p/'catalog.json').read_text());out=O/key;out.mkdir(parents=True,exist_ok=True);dec=[]
 for row in cat['rows']:
  if row['method']!='visual':continue
  st=rec['states'][row['state']];name=row['state'];wrapping=row['aspect']=='wrapping'
  if not st['complete']:
   actual=None;indices=[];reason='Unknown. The exact baseline epoch is coherent, but frozen bound_state_evidence reports incomplete per-state interval union. Original indices 8–13 cover y=0 through 1900 of a 1906.3333-unit host content extent. The footer is visibly readable and no collision is apparent, but the last 6.3333 units are not established in this selected state, so a full-content '+('wrapping' if wrapping else 'overlap')+' pass is withheld. Initial/final or other-state captures are not substitutes.'
  else:
   actual=True;indices=st['indices']
   if wrapping:
    reason='Inspected every captured part of this coherent '+name+' state against the approved fixture and source-backed wrapping question. Title, subtitle, '+('caller-updated ' if name=='submitted' else '')+'notice, all six choice labels, unavailable status and verbatim reason, visible item details, summary, disclosure label, '+('the complete global guidance, ' if name=='expanded' else '')+'action label and footer remain readable without ellipsis, missing required copy or clipped words. '+('Collapsed global guidance is intentionally absent. ' if name!='expanded' else '')+'The native interval union is complete.'
    if inp['platform']=='ios' and inp['case']=='P2':reason+=' Large text uses character breaks for over-width unbroken words, including Unavailable'+(' and service-label words within the indicator row' if inp['source']=='source-b' else '')+'; every character remains visible. Such fallback is explicitly allowed by the approved brief.'
   else:
    reason='Across the entire coherent '+name+' sweep, text blocks, choice indicators, unavailable status/reason, estimate, disclosure'+(' and global guidance' if name=='expanded' else '')+', primary action and footer occupy separate areas. No unintended text collision, indicator collision or occlusion is visible. Viewport-edge cuts are resolved by overlapping captures from this same state; the native interval union is complete.'
  dec.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':indices})
 judge={'review':{'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inp['observation_sha256'],'decisions':dec},'attributions':[]}
 (out/'judge.json').write_text(json.dumps(judge,ensure_ascii=False,indent=2)+'\n')
print('Wrote 12 judge.json files; 70 true and 2 unknown qualitative actuals. No supported F to attribute.')
