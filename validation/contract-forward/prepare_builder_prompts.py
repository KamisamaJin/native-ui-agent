from pathlib import Path
import json,time
from datetime import datetime,timezone
R=Path(__file__).resolve().parent;REPO=R.parents[1]
assignment=json.loads((R/'private/assignment.json').read_text())
common='''Complete ONLY the initial implementation phase of a native component forward test. Independently implement the same new WorkshopEnrollmentCard for iOS SwiftUI inside AlertToast and Android Compose inside Reply, following the fixed public business/visual design. Read your assigned frozen Skill and use its supported capabilities. Do not modify tools, bridge, host, design, expected source or action route. No commit/push.

Your production workspace: {workspace}
Your assigned Skill: {tool}
Allowed design inputs: {public}/BRIEF.md, API.md, reference.json, contract.json, bindings.json, design-lock.json, cases/, references/ and the two bridge files. Do NOT read public/compiled or validation-logs (precompiled tool outputs), private/, other arms, previous trial results or any other tool version. Do not inspect any rendered candidate screenshot, launch an app, run observer/Paparazzi previews, or render UI during this phase. You may read the independently frozen reference PNG/SVG and compile-only check production. Work only in your workspace and its agent-output/ directory; read common bootstrap/compile helper as needed. Inspect applicable project instructions. Keep native deployment/framework versions and existing production UI intact.

Approved independent public design canonical lock SHA256, pinned by root before your implementation:
c2548a601384046a016e98258728877982f30a4ed25be22455d9ec9ea4399bc1
This reference is not editable by the implementation. The assigned Skill may consume it as supported; preserve unsupported checks as unassessed/manual with correct scope. No self-created revised approval.

Initial phase budget: at most25 wall minutes from first action; early completion allowed. First record actual UTC start in agent-output/phase-start.json (use clock/Python, not an estimate). Implement production Swift/Kotlin API and behavior from API.md, rendering the actual component. Do not copy/recreate it in bridge/tests. Native labels/identities and same-instance caller replacement must follow design. You may run compile-only validation with:
python3 {compile} --workspace {workspace} --platform android --output FRESH_OWN_CACHE_DIR
python3 {compile} --workspace {workspace} --platform ios --bridge {public}/Bridge.swift --output FRESH_OWN_CACHE_DIR
These are identical common preflights and do not render. Preserve command/logs/time; max25min includes compile waits. Do not repair after this initial phase until root resumes you.

Before any rendered feedback create your ORIGINAL public self-check plans and observation-enriched native actions under agent-output/plans/P1/ios/{{plan.json,actions.json}}, P1/android/, P2/ios/, P2/android/. Use the fixed named states/original stimuli in public cases. Observation-only after_targets/after_target/observation_max_scrolls/observe_after fields may be added; do not change stimulus ordering, state identities or caller inputs. Use assigned native_checks supported plan schema; take selected expected values from the approved reference and preserve provenance. Cover the selected public rule/state aspects as supported, retain missing native capabilities and no-dispatch callback U; never fake computed styles. A helper for data preparation is permitted within your budget, but no other arm/tool or prior answers. Preserve matrices/scripts if used. Use public rule IDs/requirement_id where possible to support exact matching later. If your assigned Skill generates plans from a design lock, use its actual compiler in your own fresh output; do not hand-edit generated values/precision/coverage. If it does not, prepare supported self-check plans by your normal translation workflow. Do not use production values as your test oracle.

Write agent-output/plans-seal.json with SHA256 of original plans/actions/supporting plan scripts before ending. Write agent-output/implementation.json with start_utc,end_utc,changed_files,compile_commands/logs,plan_paths,coverage/limits. Record actual wall times. Preserve errors and failed attempts. End with a concise initial-delivery status, without claiming screenshot/style acceptance. Root will freeze BOTH initial sources, run original native captures, then separately resume a read-only self-review followed by one repair. No screenshot feedback is available now.
'''
for unit,data in assignment['units'].items():
 p=R/'prompts'/(unit+'-initial.txt');p.parent.mkdir(parents=True,exist_ok=True)
 message=common.format(workspace=R/'cache'/unit,tool=R/data['tool'],public=R/'design/public',compile=R/'compile_only.py')
 p.write_text(message)
print(json.dumps({'paths':[str(R/'prompts'/(u+'-initial.txt'))for u in assignment['units']],'preparedAtUTC':datetime.now(timezone.utc).isoformat()}))
