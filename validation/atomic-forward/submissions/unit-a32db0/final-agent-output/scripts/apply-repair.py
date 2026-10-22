from pathlib import Path
import json,hashlib,shutil,time
root=Path(__file__).resolve().parents[3]
base=root.parents[1]
out=root/'agent-output/repair'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[]
for p in (root/'agent-output/plans').rglob('*.json'):protected.append(p)
for p in (base/'submissions/unit-a32db0/initial-agent-output/plans').rglob('*.json'):protected.append(p)
for rel in ['alerttoast/Package.swift','reply/Reply/app/build.gradle.kts','reply/Reply/gradle/libs.versions.toml','reply/Reply/gradle/wrapper/gradle-wrapper.properties']:protected.append(root/rel)
for name in ['design-lock.json','contract.json','reference.json','policy.json','bindings.json','approval.json','Bridge.swift','ObserverBridge.kt']:protected.append(base/'design-v2/T2/public'/name)
protected.append(base/'candidate-v8/scripts/design_contract.py');protected.append(base/'candidate-v8/scripts/review_contract.py');protected.append(base/'compile_only.py')
(out/'protected-before.json').write_text(json.dumps([{'path':str(p),'sha256':sha(p)} for p in protected],indent=2)+'\n')
paths=[root/'alerttoast/Sources/AlertToast/RiverSensorTriageBoard.swift',root/'reply/Reply/app/src/main/java/com/example/reply/ui/components/RiverSensorTriageBoard.kt']
for p in paths:
 q=out/'before'/p.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
p=paths[0];s=p.read_text();assert s.count('.buttonStyle(PlainButtonStyle())')==3
s=s.replace('.buttonStyle(PlainButtonStyle())','.buttonStyle(RiverSensorButtonStyle())')
s+='''\nprivate struct RiverSensorButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}
'''
p.write_text(s)
p=paths[1];s=p.read_text();s=s.replace('import androidx.compose.ui.text.font.FontWeight','import androidx.compose.ui.text.font.FontWeight\nimport androidx.compose.ui.text.style.Hyphens\nimport androidx.compose.ui.text.style.LineBreak')
assert s.count('style = TextStyle(fontSize = size, lineHeight = size * 1.3f, fontWeight = weight),')==1
s=s.replace('style = TextStyle(fontSize = size, lineHeight = size * 1.3f, fontWeight = weight),','''style = TextStyle(
            fontSize = size,
            lineHeight = size * 1.3f,
            fontWeight = weight,
            lineBreak = LineBreak.Paragraph,
            hyphens = Hyphens.None,
        ),''')
p.write_text(s)
(out/'edit-record.json').write_text(json.dumps({'startedAtUnix':time.time(),'script':'agent-output/repair/scripts/apply-repair.py','changed_files':[str(p.relative_to(root)) for p in paths],'afterHashes':[{'path':str(p),'sha256':sha(p)} for p in paths]},indent=2)+'\n')
print('Patched actual SwiftUI ButtonStyle and Compose native paragraph line-break configuration.')
