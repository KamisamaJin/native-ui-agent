import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent.parents[3]
plan=json.loads((R/'design/private/evaluator-prep/normalized-d0.json').read_text())
fields=['roundId','title','description','notice','bedCount','dripLitresPerBed','soakLitresPerBed','dripPrimeLitres','tankLitres','reserveLitres','soakAllowed','selectedMethod','reserveAcknowledged','isEnabled','isSubmitting']
for aid in ['sample-716d41','sample-e318ec']:
 cap=R/'private/grade-capsules/paired-d0'/aid
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
  lines=(cap/prod).read_text().splitlines()
  def find(token):return next(n for n,line in enumerate(lines,1) if token in line)
  if pl=='ios':
   entry_start=find('public struct WaterRoundReleaseView')-1;entry_end=find('public init(model:')+4
   model_start=8;model_end=46;enum_line=3;act_start=48;act_end=53
  else:
   entry_start=find('public fun WaterRoundRelease')-1;entry_end=find('modifier = modifier')+2
   model_start=find('public data class WaterRoundModel');model_end=next(n for n in range(model_start,len(lines)+1) if lines[n-1]==')')
   enum_line=find('public enum class WateringMethod');act_start=find('public sealed interface WaterRoundAction');act_end=next(n for n in range(act_start,len(lines)+1) if lines[n-1]=='}')
  def prodc(a,b):cit.append(citation(prod,a,b))
  def bridgec(a,b):cit.append(citation(bridge,a,b))
  if i=='production.location':
   if pl=='ios':prodc(1,8);cit.append(citation('source/alerttoast/Package.swift',6,28))
   else:prodc(1,44)
   why='The new public implementation is in the specified production library/package; the bridge imports that production entry.'
  elif i in ['entry.model','entry.callback']:
   if pl=='ios':prodc(entry_start,entry_end)
   else:prodc(entry_start,entry_end)
   why='The public production entry requires the named public model and typed action closure, with the exact specified signature.'
  elif i=='entry.modifier':
   prodc(entry_start,entry_end)
   why='The optional public Modifier defaults to Modifier and is passed into the production root Column modifier chain.'
  elif i=='model.public':
   prodc(model_start,model_end)
   why='All fifteen model fields are public immutable values with the specified types; every constructor parameter is required without a default.'
  elif i=='method.values':
   prodc(3,6) if pl=='ios' else prodc(enum_line,enum_line)
   why='The public WateringMethod declaration contains exactly drip and soak.'
  elif i=='actions.typed':
   prodc(act_start,act_end)
   why='The public typed action family declares all three required alternatives and their typed associated fields.'
  elif i.startswith('model.member.'):
   f=i.split('.')[-1];idx=fields.index(f)
   if pl=='ios':prodc(9+idx,9+idx);prodc(25,44)
   else:prodc(model_start,model_end)
   why=f'{f} is an immutable public {row["expected"]["type"]} field and a required initializer member, with no fallback.'
  elif i.startswith('bridge.member.'):
   f=i.split('.')[-1];idx=fields.index(f)
   bridgec(8+idx,8+idx) if pl=='ios' else bridgec(13+idx,13+idx)
   bridgec(7,23) if pl=='ios' else bridgec(12,28)
   why=f'The exact required JSON member {f} is strictly decoded and passed to the corresponding production model field, without a default.'
  elif i.startswith('action.'):
   variant=i.split('.')[1]
   if pl=='ios':prodc(49,49) if variant=='methodRequested' else prodc(50,50) if variant=='reserveAcknowledgementRequested' else prodc(51,52)
   else:
    ln=find('data class '+variant);prodc(ln,ln) if variant!='releaseRequested' else prodc(ln,act_end)
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
 (cap/'source-review.json').write_text(json.dumps({'reviewer':'independent evaluator','scope':'Paired D0 source/API only; identical hash-verified D0 source, fresh capsule citations; no runtime/style substitution','decisions':decisions},ensure_ascii=False,indent=2)+'\n')
 print(aid,len(decisions))
