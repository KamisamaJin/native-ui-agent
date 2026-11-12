from pathlib import Path
import json,re,collections
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward');ROOT=BASE/'business-design';OUT=BASE/'business-design-review'
def load(p):return json.loads(p.read_text())
def schema_check(v,s,path=''):
 errors=[];t=s.get('type')
 good={'object':isinstance(v,dict),'array':isinstance(v,list),'string':isinstance(v,str),'integer':type(v) is int,'boolean':type(v) is bool}
 if t and not good[t]:return [path+': type '+t]
 if 'enum'in s and v not in s['enum']:errors.append(path+': enum')
 if isinstance(v,str):
  if len(v)<s.get('minLength',0) or len(v)>s.get('maxLength',float('inf')):errors.append(path+': length')
  if 'pattern'in s and re.fullmatch(s['pattern'],v) is None:errors.append(path+': pattern')
 if type(v)is int and not s.get('minimum',-float('inf'))<=v<=s.get('maximum',float('inf')):errors.append(path+': numeric range')
 if isinstance(v,list):
  if not s.get('minItems',0)<=len(v)<=s.get('maxItems',float('inf')):errors.append(path+': array length')
  if s.get('uniqueItems') and len({json.dumps(x,sort_keys=True) for x in v})!=len(v):errors.append(path+': uniqueness')
  for i,x in enumerate(v):errors+=schema_check(x,s['items'],path+'/'+str(i))
 if isinstance(v,dict):
  if set(s.get('required',[]))-set(v):errors.append(path+': required')
  if s.get('additionalProperties')is False and set(v)-set(s.get('properties',{})):errors.append(path+': additional')
  for k,x in v.items():
   if k in s.get('properties',{}):errors+=schema_check(x,s['properties'][k],path+'/'+k)
 return errors
families=[]
for t in range(1,6):
 for phase in ['public','private']:
  p=ROOT/f'T{t}'/phase;c=load(p/'contract.json');s=next(iter(c['scenarios'].values()));den=load(p/'denominator.json');ref=load(p/'reference.json');err=[];schema_errors=[]
  for platform in ['ios','android']:
   fixture=load(p/f'fixtures.{platform}.json');schema=load(p/'fixture.schema.json')
   for i,f in enumerate([fixture['initial']]+fixture['updates']):
    schema_errors += [{'platform':platform,'input_index':i,'error':e} for e in schema_check(f,schema)]
    for k,v in f.items():
     if isinstance(v,list) and v and isinstance(v[0],dict):
      for field in ['id','label']:
       if len({x[field] for x in v})!=len(v):schema_errors.append({'field':field,'input':i,'error':'duplicate group identity'})
  rules={r['id']:r for r in c['rules']};states={x['id'] for x in s['states']}
  expected={(rid,st)for rid in rules for st in states};actual={(x['requirement'],x['state'])for x in den['cells']}
  if expected!=actual or len(den['cells'])!=len(expected):err.append('Cartesian denominator missing/duplicate cells')
  assess=na=0
  for row in den['cells']:
   rid,st=row['requirement'],row['state'];cell=s['values'][rid][st]
   for platform,d in row['platforms'].items():
    value=cell if 'not_applicable'in cell else cell[platform]
    if 'not_applicable'in value:
     na+=1
     if d.get('disposition')!='not_applicable' or d.get('reason')!=value['not_applicable']:err.append([rid,st,platform,'N/A reason mismatch'])
    else:
     assess+=1
     source=ref
     for key in value['pointer'].strip('/').split('/'):source=source[key.replace('~1','/').replace('~0','~')]
     if d.get('expected')!=source['value'] or d.get('unit')!=source['unit'] or d.get('disposition')!='assess' or d.get('operator')!=rules[rid].get('op','eq'):err.append([rid,st,platform,'source expectation/operator mismatch'])
  if den['total_cells']!=assess+na or den['assess_cells']!=assess or den['not_applicable_cells']!=na:err.append('denominator count metadata mismatch')
  counterpart=load(ROOT/f'T{t}'/('private' if phase=='public' else 'public')/'reference.json')
  invariant_errors=[k for k in ['business_rules','tokens','scope','questions','visual']if ref[k]!=counterpart[k]]
  families.append({'family':f'T{t}/{phase}','schema_validator':'independent stdlib validator of every used JSON-Schema constraint (object/required/additionalProperties,array cardinality/items/uniqueness,string bounds/pattern,integer bounds,bool,enum); installed jsonschema package unavailable','fixture_payloads_checked':6,'schema_errors':schema_errors,'denominator_total':assess+na,'assess':assess,'N/A':na,'denominator_errors':err,'shared_public_private_invariant_errors':invariant_errors})
(OUT/'denominator-schema-audit.json').write_text(json.dumps(families,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'families':len(families),'fixture_payloads_checked':sum(f['fixture_payloads_checked']for f in families),'schema_errors':sum(len(f['schema_errors'])for f in families),'denominator_errors':sum(len(f['denominator_errors'])for f in families),'shared_rule_token_proposition_errors':sum(len(f['shared_public_private_invariant_errors'])for f in families),'assess_cells':sum(f['assess']for f in families),'NA_cells':sum(f['N/A']for f in families)},indent=2))
