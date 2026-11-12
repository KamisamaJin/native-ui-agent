from pathlib import Path
import json,sys
base=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward');out=base/'business-design-review'
lines=[]
for t in map(int,sys.argv[1:]):
 for phase in ['public','private']:
  p=base/f'business-design/T{t}/{phase}';f=json.loads((p/'fixtures.ios.json').read_text());o=json.loads((p/'outcomes.json').read_text());a=json.loads((p/'actions.ios.json').read_text())
  lines.append(f'\nT{t}/{phase}\n')
  for i,x in enumerate([f['initial']]+f['updates']):
   lines.append('input '+str(i)+': '+json.dumps(x,ensure_ascii=False)+'\n')
  lines.append('actions: '+json.dumps([{i:{k:v for k,v in x.items() if k in ['type','target','state_id','expect_callback']}} for i,x in enumerate(a)],ensure_ascii=False)+'\n')
  for s in o['states']:
   x=s['exact_business_state']; c=x['controls']
   lines.append(f'{s["id"]} input{s["input_index"]} action{s["after_action"]} stimulus{s.get("stimulus_action")} {s["coverage"]}: '+json.dumps({'controls':{k:{f:v[f] for f in ['enabled','selected'] if f in v} for k,v in c.items()},**{k:v for k,v in x.items() if k not in ['controls','description','entity']},'events':s['exact_callback_interval']},ensure_ascii=False)+'\n')
text=''.join(lines);(out/('business-compact-'+''.join(sys.argv[1:])+'.txt')).write_text(text);print(text)
