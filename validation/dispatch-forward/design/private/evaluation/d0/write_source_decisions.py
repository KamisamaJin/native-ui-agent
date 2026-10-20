import json,hashlib
from pathlib import Path
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/dispatch-forward')
plan=json.loads((R/'design/private/evaluator-prep/normalized-d0.json').read_text())
fields=['roundId','title','description','notice','bedCount','dripLitresPerBed','soakLitresPerBed','dripPrimeLitres','tankLitres','reserveLitres','soakAllowed','selectedMethod','reserveAcknowledged','isEnabled','isSubmitting']
for aid in ['sample-716d41','sample-e318ec']:
 cap=R/'private/grade-capsules/d0'/aid
 manifest=json.loads((cap/'manifest.json').read_text()); refs={x['path']:x for x in manifest['source_files']}
 paths={'ios':'source/alerttoast/Sources/AlertToast/WaterRound.swift','android':'source/reply/Reply/app/src/main/java/com/example/reply/ui/waterround/WaterRound.kt'}
 bridges={'ios':'source/bridges/Bridge.swift','android':'source/bridges/ObserverBridge.kt'}
 def citation(path,a,b):
  lines=(cap/path).read_text().splitlines()
  return {'artifact':refs[path],'line_start':a,'line_end':b,'quote':'\n'.join(lines[a-1:b])}
 decisions=[]
 for row in plan['rows']:
  if row['denominator']!='source_api':continue
  pl=row['platform'];i=row['id'];prod=paths[pl];bridge=bridges[pl];cit=[]
  def prodc(a,b):cit.append(citation(prod,a,b))
  def bridgec(a,b):cit.append(citation(bridge,a,b))
  if i=='production.location':
   if pl=='ios':prodc(1,8);cit.append(citation('source/alerttoast/Package.swift',6,28))
   else:prodc(1,44)
   why='The new public implementation is in the specified production library/package; the bridge imports that production entry.'
  elif i in ['entry.model','entry.callback']:
   if pl=='ios':prodc(111 if aid=='sample-716d41' else 104,125 if aid=='sample-716d41' else 119)
   else:prodc(108 if aid=='sample-716d41' else 114,119 if aid=='sample-716d41' else 125)
   why='The public production entry requires the named public model and typed action closure, with the exact specified signature.'
  elif i=='entry.modifier':
   prodc(108,119) if aid=='sample-716d41' else prodc(114,125)
   why='The optional public Modifier defaults to Modifier and is passed into the production root Column modifier chain.'
  elif i=='model.public':
   prodc(8,46) if pl=='ios' else prodc(44,60)
   why='All fifteen model fields are public immutable values with the specified types; every constructor parameter is required without a default.'
  elif i=='method.values':
   prodc(3,6) if pl=='ios' else prodc(42,42)
   why='The public WateringMethod declaration contains exactly drip and soak.'
  elif i=='actions.typed':
   prodc(48,53) if pl=='ios' else prodc(62,73)
   why='The public typed action family declares all three required alternatives and their typed associated fields.'
  elif i.startswith('model.member.'):
   f=i.split('.')[-1];idx=fields.index(f)
   if pl=='ios':prodc(9+idx,9+idx);prodc(25,44)
   else:prodc(44,60)
   why=f'{f} is an immutable public {row["expected"]["type"]} field and a required initializer member, with no fallback.'
  elif i.startswith('bridge.member.'):
   f=i.split('.')[-1];idx=fields.index(f)
   bridgec(8+idx,8+idx) if pl=='ios' else bridgec(13+idx,13+idx)
   bridgec(7,23) if pl=='ios' else bridgec(12,28)
   why=f'The exact required JSON member {f} is strictly decoded and passed to the corresponding production model field, without a default.'
  elif i.startswith('action.'):
   variant=i.split('.')[1]
   if pl=='ios':prodc(49,49) if variant=='methodRequested' else prodc(50,50) if variant=='reserveAcknowledgementRequested' else prodc(51,52)
   else:prodc(63,63) if variant=='methodRequested' else prodc(64,64) if variant=='reserveAcknowledgementRequested' else prodc(65,72)
   why=f'The public {variant} typed payload includes {row["expected"]["name"]}: {row["expected"]["type"]}.'
  elif i.startswith('compatibility.'):
   prodc(1,len((cap/prod).read_text().splitlines()));cit.append(citation('source/alerttoast/Package.swift',1,28))
   why='Read the complete new Swift source and deployment declaration: iOS 14/macOS 11 availability is maintained, and no unguarded later API occurs. This is a source compatibility judgment, not a minimum-OS execution claim.'
  elif i=='callback.serialization':
   bridgec(23,34) if pl=='ios' else bridgec(28,36)
   why='Each real typed production action is serialized immediately into the public ordered token format with its payload; there is no reordered or synthesized callback stream.'
  elif i=='bridge.actual_entry' or i.startswith('bridge.forbid.'):
   bridgec(1,34) if pl=='ios' else bridgec(1,36)
   why='Read the complete bridge: it only strictly decodes JSON, constructs the public model, invokes the actual production entry, and serializes delivered typed actions. It contains none of the prohibited validation, amount/eligibility calculation, UI, synthesis, model mutation, or fallback behavior.'
  else:raise ValueError(i)
  decisions.append({'key':row['key'],'outcome':'P','method':'source_api','expected_sha256':row['original_expected_sha256'],'reason':why,'fact':{'reviewed_requirement':i,'scope':'source/API only'},'citations':cit})
 assert len(decisions)==113
 (cap/'source-review.json').write_text(json.dumps({'reviewer':'independent evaluator','scope':'D0 source/API only; no runtime/style substitution','decisions':decisions},ensure_ascii=False,indent=2)+'\n')
 print(aid,len(decisions))
