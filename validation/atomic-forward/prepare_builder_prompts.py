# coding: utf-8
from pathlib import Path
import json
R=Path(__file__).resolve().parent
assignment=json.loads((R/'private/assignment.json').read_text())
T='''Use the assigned native-ui-agent Skill to implement ONLY the initial phase of this independently designed new UI task, for SwiftUI in AlertToast AND Compose in Reply. Do not deliberately insert defects or optimize for scoring. No commits/pushes. Keep tool versions, assignments and experiment labels out of production comments/UI so later source review can stay anonymous.
Workspace (write only here): {workspace}
Assigned frozen Skill (read only): {tool}
Public independent design (read only): {public}
Read BRIEF.md, API.md, reference.json, contract.json, policy.json, bindings.json, approval.json, cases/ and reference SVG/PNGs. Do not read public/compiled or validation logs, design/private, private assignment, other candidates, other Skill versions, old trial cases/reports, evaluation or common-corpora. Inspect applicable project instructions in your own workspace. Both arms receive the same public atomic policy and approved reference. Your assigned Skill determines executable capabilities; do not access another version. No direct SDK rendering, previews, observers, screenshots or app launch in this initial phase. You may inspect the independent reference PNGs and run compile-only.

Root pins the approved lock canonical digest BEFORE your first implementation: {digest}
Use the actual compiler in your assigned Skill to generate your ORIGINAL self-check plans/actions from that lock; never hand-edit generated expected values, units, coverage or numerical precision. Never use implementation values as the oracle. Generate plans for P1/P2 × ios/android under agent-output/plans/<case>/<platform>/ with plan.json/actions.json. Use original public stimulus routes and preserve unsupported checks. Preserve source matrices/scripts if used. Design API and selectors must be implemented by actual production component code, never reconstructed in a bridge/test.

Budget at most25 wall minutes from FIRST action (including compile waits), early finish allowed. Immediately record actual UTC/Unix start in agent-output/phase-start.json using clock/Python. Implement the public API/production files and all business rules. Keep pinned framework/build settings and unrelated existing UI intact. Optional no-render preflights:
python3 {compile} --workspace {workspace} --platform android --output <fresh-own-cache-dir>
python3 {compile} --workspace {workspace} --platform ios --bridge {public}/Bridge.swift --output <fresh-own-cache-dir>
Place compile outputs under your workspace/cache/ (not agent-output), copy only build logs/record JSON into agent-output. No rendering commands are authorized. Do not repair after this phase until root explicitly resumes you. End by recording agent-output/implementation.json with actual startedAtUnix/finishedAtUnix, changed_files, commands/logs, plan paths and limits; plans-seal.json hashes all ORIGINAL plans/actions/scripts. Preserve every failed attempt and command record. Deliver a concise initial status without claiming screenshot acceptance. All SIX initial sources/plans must seal before ANY rendered feedback.
'''
for unit,data in assignment['units'].items():
 public=R/json.loads((R/'DESIGN-ROOT.json').read_text())['directory']/data['task']/'public';approval=json.loads((public/'approval.json').read_text());digest=approval['design_lock_sha256']
 p=R/'prompts'/(unit+'-initial.txt');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(T.format(workspace=R/'cache'/unit,tool=R/data['tool'],public=public,digest=digest,compile=R/'compile_only.py'))
print('Prepared six task-specific initial prompts; no hidden or assignment details are delivered.')
