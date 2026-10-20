"""Neutral non-business contract fixed before any new native capture."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
R=Path(__file__).resolve().parent
REPO=R.parents[2]
sys.path.insert(0,str(REPO/'native-ui-agent/scripts'))
import design_contract as d
example=REPO/'native-ui-agent/assets/design-example'
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
source=d.load(example/'reference.json');contract=d.load(example/'contract.json')
for name,prefix in [('footer','End '),('secondary','Continue ')]:
 source[name]={x:{'value':prefix+x,'unit':'string'}for x in ['A','B']}
 rule={'id':name+'-label','kind':'control','target':name,'property':'label'}
 contract['rules'].append(rule);contract['required_rule_ids'].append(rule['id'])
save(R/'reference.json',source)
contract['sources'][0]['sha256']=hashlib.sha256((R/'reference.json').read_bytes()).hexdigest()
old=d.load(REPO/'validation/state-forward/generic/actions-base.json')
bindings=d.load(example/'bindings.json')
for k in ['footer','secondary','disabled','missing']:bindings[k]={'identifier':'probe.'+k}
bindings.pop('missing')
scenario=contract['scenarios']['neutral'];scenario['states']=[{'id':sid,'input_index':inp,'after_action':idx,'coverage':'targets'}for sid,inp,idx in [('expanded',0,1),('continued',0,2),('updated',1,4),('disabled',1,5)]]
# Preserve the explicit zero-budget unavailable target probe outside the design
# assertions; it is acquisition diagnostics, not an asserted business rule.
scenario['actions']=copy.deepcopy(old)
for a in scenario['actions']:
 if a.get('type')=='tap':a['target']=a['target']['identifier'].split('.',1)[1]
scenario['values']={}
for rule in contract['rules']:
 cells={}
 for state in scenario['states']:
  sid=state['id'];token='A'if state['input_index']==0 else'B'
  if rule['id'] in ['activate','update']:
   applies=sid in ['expanded','continued']if rule['id']=='activate'else sid=='updated'
   if not applies:cells[sid]={'not_applicable':'No corresponding successful stimulus class in this state'};continue
   p='/business/activated'if sid=='expanded'else'/business/secondary'if sid=='continued'else'/business/quiet'
   cell={k:{'source':'reference','pointer':p}for k in ['ios','android']}
  elif rule['kind']=='geometry':
   key='width'if rule['id']=='marker-width'else'gap'
   cell={k:{'source':'reference','pointer':'/geometry/'+k+'/'+key}for k in ['ios','android']}
   cell['tolerance']={k:{'source':'reference','pointer':'/geometry/'+k+'/tolerance'}for k in ['ios','android']}
  else:
   p='/labels/'+token if rule['id']=='header-label'else'/style/ink'if rule['id']=='ink'else'/'+rule['target']+'/'+token
   cell={k:{'source':'reference','pointer':p}for k in ['ios','android']}
  cells[sid]=cell
 scenario['values'][rule['id']]=cells
source['business']['secondary']={'value':['secondary'],'unit':'events'};save(R/'reference.json',source)
contract['sources'][0]['sha256']=hashlib.sha256((R/'reference.json').read_bytes()).hexdigest()
save(R/'contract.json',contract);save(R/'bindings.json',bindings);save(R/'actions-base.json',old)
lock=d.seal(R/'contract.json',R);save(R/'design-lock.json',lock);save(R/'approval.json',{'canonicalSHA256':d.digest(lock),'scope':'Neutral probe fixed before native acquisition; no new business domain'})
for platform in ['ios','android']:
 plan,actions=d.compile_contract(lock,d.digest(lock),'neutral',platform,bindings,old)
 save(R/('plan.'+platform+'.json'),plan);save(R/('actions.'+platform+'.json'),actions)
fixtures=d.load(REPO/'validation/state-forward/generic/fixtures.json')
fixtures['observation_targets'] += [bindings[k]for k in ['markerA','markerB','ink']]
save(R/'fixtures.json',fixtures)
for name in ['Bridge.swift','ObserverBridge.kt']:shutil.copy2(REPO/'validation/state-forward/generic'/name,R/name)
p=R/'Bridge.swift';s=p.read_text().replace('            Button(expanded ?', '''            HStack(spacing: 10) {
                Text("A").frame(width: 72, height: 32).accessibilityElement(children: .ignore).accessibilityLabel("Marker A").accessibilityIdentifier("probe.markerA")
                Text("B").frame(width: 72, height: 32).accessibilityElement(children: .ignore).accessibilityLabel("Marker B").accessibilityIdentifier("probe.markerB")
            }
            Text("Ink").foregroundColor(Color(red: 39.0/255, green: 97.0/255, blue: 69.0/255)).accessibilityIdentifier("probe.ink")
            Button(expanded ?''');p.write_text(s)
p=R/'ObserverBridge.kt';s=p.read_text().replace('   Button({expanded', '''   Row(horizontalArrangement=Arrangement.spacedBy(10.dp)) {
    Text("A",Modifier.size(72.dp,32.dp).testTag("probe.markerA"))
    Text("B",Modifier.size(72.dp,32.dp).testTag("probe.markerB"))
   }
   Text("Ink",Modifier.testTag("probe.ink"),color=androidx.compose.ui.graphics.Color(0xFF276145))
   Button({expanded''');p.write_text(s)
print({'lock':d.digest(lock),'cells':len(plan['matrix_contract']['cells']),'assertions':len(plan['assertions'])})
