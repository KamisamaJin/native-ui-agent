from pathlib import Path
import hashlib, json, subprocess, sys, time
ROOT = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
OUT = ROOT / 'validation/feedback-forward/source-neutral-forward'
DESIGN = OUT / 'fixture/design'
SOURCE = OUT / 'fixture/source'
AUDIT = ROOT / 'tools/implementation_audit.py'
FROZEN = ROOT / 'validation/feedback-forward/candidate-v9/scripts/design_contract.py'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
def run(label, argv):
    started = time.time()
    p = subprocess.run([str(v) for v in argv], cwd=ROOT, capture_output=True, text=True, env={**__import__('os').environ, 'PYTHONDONTWRITEBYTECODE':'1'})
    record = {'label':label,'startedAtUnix':started,'endedAtUnix':time.time(),'cwd':str(ROOT),'argv':[str(v) for v in argv],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    write(OUT/'commands'/f'{label}.json',record)
    print(json.dumps({'label':label,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))
    return p

DESIGN.mkdir(parents=True, exist_ok=True)
rows = [
 ('swift-clamp','BadgeModel.swift','The Swift displayCount getter clamps count to a minimum of zero.',True,'The Swift component derives a nonnegative display count.'),
 ('swift-delegation','BadgeModel.swift','The Swift label getter passes displayCount to the supplied formatter.',True,'The Swift component delegates label creation using its derived count.'),
 ('kotlin-clamp','BadgeModel.kt','The Kotlin displayCount getter clamps count to a minimum of zero.',True,'The Kotlin component derives a nonnegative display count.'),
 ('kotlin-delegation','BadgeModel.kt','The Kotlin label getter passes displayCount to the supplied formatter.',True,'The Kotlin component delegates label creation using its derived count.'),
 ('kotlin-empty-fallback','BadgeModel.kt','The Kotlin label getter contains an in-body replacement for empty formatter output.',False,'The Kotlin label getter preserves the supplied formatter result.'),
 ('shared-identifier',['BadgeModel.swift','BadgeModel.kt'],'Both model declarations expose the source constant neutral.badge.count as accessibilityIdentifier.',True,'The source identifier constant is shared across both model declarations.'),
 ('formatter-localization',['BadgeModel.swift','BadgeModel.kt'],'The configured formatter implementations resolve their label through localization resource key badge.count.',True,'Configured formatter implementations must resolve the independent localization key.')
]
reference = {'presence':{'value':True,'unit':'bool'},'propositions':{},'expectations':{},'source_audit':[]}
for key,files,proposition,expected,clause in rows:
    reference['propositions'][key]={'value':proposition,'unit':'string'}
    reference['expectations'][key]={'value':expected,'unit':'bool'}
    reference['source_audit'].append({'id':key,'clause':clause,'priority':'must','files':[files] if isinstance(files,str) else files,'proposition':{'source':'neutral','pointer':'/propositions/'+key},'expected':{'source':'neutral','pointer':'/expectations/'+key}})
write(DESIGN/'reference.json',reference)
contract={'version':1,'design_owner':'Independent neutral source-only forward test author','approval_reference':'source-neutral-forward/independent-pin.json; local synthetic fixture approval only','sources':[{'id':'neutral','path':'reference.json','sha256':sha(DESIGN/'reference.json')}],'required_rule_ids':['scaffold-presence'],'rules':[{'id':'scaffold-presence','kind':'control','target':'neutral-model','property':'present'}],'scenarios':{'neutral':{'states':[{'id':'unobserved','after_action':-1}],'actions':[],'values':{'scaffold-presence':{'unobserved':{'ios':{'source':'neutral','pointer':'/presence'},'android':{'source':'neutral','pointer':'/presence'}}}}}}}
write(DESIGN/'contract.json',contract)
policy={'version':1,'index':{'source':'neutral','pointer':'/source_audit'}}
write(DESIGN/'implementation-audit.json',policy)
write(OUT/'planning.json',{'fixedAtUnix':time.time(),'scope':'A tiny neutral model source fixture, independently authored in this folder. No business design or product source is used. No native observation or compilation is planned.','sourceExistsAtPlanning':SOURCE.exists(),'obligations':reference['source_audit'],'unknownPlan':'Formatter implementations and their localization resources are deliberately outside the declared model fixture; do not infer implementation of the localization obligation.','contractScaffold':'The generic design-lock schema requires a native rule/state scaffold. It is unobserved and never used as source acceptance or a rendered claim.','sourceOnlyRulesBeforeSource':True})
p=run('005-seal-lock',[sys.executable,FROZEN,'seal','--contract',DESIGN/'contract.json','--root',DESIGN,'--output',DESIGN/'lock.json'])
if p.returncode: raise SystemExit('Independent lock generation failed')
lock=json.loads((DESIGN/'lock.json').read_text()); lock_sha=digest(lock); policy_sha=digest(policy)
write(OUT/'independent-pin.json',{'pinnedAtUnix':time.time(),'lockCanonicalSha256':lock_sha,'policyCanonicalSha256':policy_sha,'referenceByteSha256':sha(DESIGN/'reference.json'),'contractByteSha256':sha(DESIGN/'contract.json'),'sourceRootExists':SOURCE.exists(),'approval':'Author approval of this synthetic independent fixture only; not approval of any real design.'})
base=[sys.executable,AUDIT]
common=['--design-lock',DESIGN/'lock.json','--design-sha256',lock_sha,'--policy',DESIGN/'implementation-audit.json','--policy-sha256',policy_sha,'--source-root',SOURCE,'--design-root',DESIGN]
p=run('006-definitions-before-source',base+['definitions']+common+['--output',OUT/'definitions.json'])
if p.returncode: raise SystemExit('Definition generation failed')
SOURCE.mkdir(parents=True)
(SOURCE/'BadgeModel.swift').write_text('''protocol LabelFormatting {
    func string(for count: Int) -> String
}

struct BadgeModel {
    let count: Int
    let formatter: any LabelFormatting
    static let accessibilityIdentifier = "neutral.badge.count"

    var displayCount: Int { max(0, count) }
    var label: String { formatter.string(for: displayCount) }
}
''')
(SOURCE/'BadgeModel.kt').write_text('''interface LabelFormatting {
    fun stringFor(count: Int): String
}

data class BadgeModel(val count: Int, val formatter: LabelFormatting) {
    companion object {
        const val accessibilityIdentifier = "neutral.badge.count"
    }

    val displayCount: Int get() = count.coerceAtLeast(0)
    val label: String get() = formatter.stringFor(displayCount)
}
''')
write(OUT/'fixture-fixed.json',{'fixedAtUnix':time.time(),'files':{str(p.relative_to(OUT)):{'sha256':sha(p),'bytes':p.stat().st_size,'lineCount':len(p.read_text().splitlines())} for p in SOURCE.iterdir()},'sourceAuthoring':'Original neutral fixture, authored after independent propositions and definitions. No build or runtime observation.'})
p=run('007-source-catalog',base+['catalog']+common+['--output',OUT/'catalog.json'])
if p.returncode: raise SystemExit('Actual catalog failed')
run('008-read-original-source',[sys.executable,'-c',"from pathlib import Path; p=Path("+repr(str(SOURCE))+"); [(print(f'FILE {f.name}\\n'+''.join(f'{i}: {line}\\n' for i,line in enumerate(f.read_text().splitlines(),1)))) for f in sorted(p.iterdir())]"])
