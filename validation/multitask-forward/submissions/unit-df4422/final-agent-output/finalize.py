import datetime,hashlib,json,pathlib,time
w=pathlib.Path(__file__).resolve().parents[2];out=w/'agent-output/repair'
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/multitask-forward')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source='alerttoast/Sources/AlertToast/ExpeditionPackPanel.swift'
reviewpath=b/'submissions/unit-df4422/original-review/review.json';review=json.loads(reviewpath.read_text())
command_record=json.loads((out/'compile-command.json').read_text())
commands=[
 {'kind':'read instructions and first clock','command':['cat',str(b/'prompts/unit-df4422-repair.txt')],'exitCode':0,'timeUtc':'2026-10-20T15:32:55+00:00'},
 {'kind':'record start','command':'Python wrote agent-output/repair/phase-start.json with first-action UTC/Unix and actual record time.','exitCode':0},
 {'kind':'read original source and original feedback','command':'sed -n 45,290p alerttoast/Sources/AlertToast/ExpeditionPackPanel.swift; Python json.load of submissions/unit-df4422/original-review/review.json root_cause_clusters','exitCode':0},
 {'kind':'production edit','command':'Python replaced request-id-only onChange with PackSelectionSeed value handling and replaced PlainButtonStyle with PackButtonStyle; added the private seed snapshot and pass-through native ButtonStyle.','exitCode':0,'exactDiff':'agent-output/repair/production.diff','diffSHA256':sha(out/'production.diff')},
 {'kind':'preserve production diff','command':['git','-C','alerttoast','diff','--no-index',str(b/'submissions/unit-df4422/d0/source/alerttoast/Sources/AlertToast/ExpeditionPackPanel.swift'),'Sources/AlertToast/ExpeditionPackPanel.swift'],'output':'agent-output/repair/production.diff','expectedExitCode':1,'reason':'git diff --no-index uses 1 for recorded differences; no command error.'},
 {'kind':'compile-only','wrapper':['python3','agent-output/repair/run_compile.py'],**command_record},
 {'kind':'protected-file check','command':'Python SHA256 comparison against original agent-output/plans-seal.json for every plan/action/script and unchanged Android source.','exitCode':0,'record':'agent-output/repair/protected-files.json'},
 {'kind':'finalize repair handoff','command':['python3','agent-output/repair/finalize.py'],'exitCode':0}
]
(out/'commands.json').write_text(json.dumps(commands,indent=2))
protected=json.loads((out/'protected-files.json').read_text());assert all(x['unchanged'] for x in protected)
assert command_record['exitCode']==0
source_hashes={source:sha(w/source),'reply/Reply/app/src/main/java/com/example/reply/ui/components/ExpeditionPackPanel.kt':sha(w/'reply/Reply/app/src/main/java/com/example/reply/ui/components/ExpeditionPackPanel.kt')}
start=json.loads((out/'phase-start.json').read_text());finished=time.time()
addressed=[]
for cluster in review['root_cause_clusters']:
 addressed.append({'original_root_cause_cluster':cluster['id'],'scope':cluster['scope'],'original_finding_count':sum(x.get('root_cause_cluster')==cluster['id'] for x in review['findings']),'change': 'The onChange value now carries the replacement selectedIDs and normalized cover. Its equality compares request identity, preserving same-ID local choices, and the callback applies the new value rather than reading a captured request.' if cluster['id']=='ios-replacement-seed-reset' else 'A pass-through native ButtonStyle returns configuration.label without PlainButtonStyle disabled dimming. All native Buttons retain their existing disabled modifiers, selection traits, identifiers, bounds and callback guards.','status':'production_repair_applied_compile_verified','runtime_and_visual_confirmation':'not available in this phase'})
repair={
 'version':1,'phase':'one_repair_phase','status':'repaired_compile_only_final_acceptance_pending',
 'startedAtUnix':start['startedAtUnix'],'startedAtUtc':start['startedAtUtc'],'finishedAtUnix':finished,'finishedAtUtc':datetime.datetime.fromtimestamp(finished,datetime.timezone.utc).isoformat(),'elapsedSeconds':finished-start['startedAtUnix'],'budgetSeconds':900,
 'changed_files':[source],'source_sha256':source_hashes,
 'original_feedback':{'path':str(reviewpath),'sha256':sha(reviewpath)},
 'original_findings_addressed':addressed,
 'original_typed_failure_ids':[{'case':case,'platform':'ios','id':rule} for case in ['P1','P2'] for rule in ['replaced/option-enabled','replaced/derived-summary','replaced/eligibility-status','replaced/primary-enabled']],
 'unresolved_and_why':[
  {'aspect':'runtime replacement behavior and disabled palette appearance','reason':'No new runtime or rendered feedback is authorized. The supported production fixes compile, but final state/callback/visual verification remains pending.'},
  {'aspect':'generic iOS computed typography/color/ellipsis','reason':'Original observer support is unchanged; original U cells remain U. No expectation or check was edited.'},
  {'aspect':'P2 disabled optional-control callback behavior','reason':'The original requested action was blocked_disabled; absence of successful dispatch remains unassessed.'},
  {'aspect':'Android narrow-card word breaking','reason':'Original review classified this as a qualitative unassessed preference, not a confirmed violation. Android production source remains unchanged.'}
 ],
 'commands':'agent-output/repair/commands.json',
 'logs':['agent-output/repair/compile-command.log','agent-output/repair/build.log','agent-output/repair/record.json','agent-output/repair/compile-command.json','agent-output/repair/production.diff'],
 'verification':{'ios_compile_only_exit_code':0,'compile_record':'agent-output/repair/record.json','android_recompiled':False,'android_reason':'Android production source is unchanged and had no confirmed original defect.','original_plans_actions_scripts_unchanged':True,'protected_file_record':'agent-output/repair/protected-files.json'},
 'limits':['Only the assigned public design and original own feedback were used.','No SDK rendering, screenshots, observers, previews, app launch or second feedback/repair cycle was executed.','Original self-check plans/actions/expectations, frozen tools, bridges, host, public design and pinned framework/build settings were not edited.','No commits or pushes.','Final source handoff only; FINAL acceptance is not available, and no further repair is authorized.']
}
(out/'repair.json').write_text(json.dumps(repair,indent=2))
files={str(p.relative_to(w)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='repair-seal.json'}
(out/'repair-seal.json').write_text(json.dumps({'version':1,'sealedAtUnix':time.time(),'files':files,'production_source_sha256':source_hashes,'original_plans_actions_unchanged':True},indent=2))
print(json.dumps({'status':repair['status'],'elapsedSeconds':repair['elapsedSeconds'],'changed_files':repair['changed_files'],'source_sha256':source_hashes,'sealedFiles':len(files)},indent=2))
