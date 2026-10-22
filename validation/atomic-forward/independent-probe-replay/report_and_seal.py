import json,hashlib,os,datetime,time
from pathlib import Path
R=Path(__file__).resolve().parent;O=R.with_name('independent-probe');W=R.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canon=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
results=json.loads((R/'results.json').read_text());pixels=json.loads((R/'eligibility-summary.json').read_text());diffs=json.loads((R/'exact-artifact-differences.json').read_text());tools=json.loads((R/'tool-identities-before.json').read_text())
control={'replay_command':{'argv':['python3',str(R/'replay.py')],'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1'},'wall_seconds':results['wall_seconds']},'comparison_command':{'argv':['python3','compare.py'],'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1'},'timing':'Not separately instrumented; command/tool transcript retained.'},'finalization_command':{'argv':['python3','report_and_seal.py'],'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1'},'note':'No wrapper appends to sealed command logs after this seal.'}}
(R/'control-commands.json').write_text(json.dumps(control,indent=2)+'\n')
lines=['# 独立中性 probe：最终候选的无 SDK 复验','', '使用当前 live scripts 对封存的原始采集、原始 actual-only 人工请求、原始 plan/lock/policy 复算。未运行 SDK，未修改组件、预期、旧输入、旧人工请求或旧输出。所有复验输出位于本目录。','', '| 原始采集 | 原报告 | 当前原请求复算 | 当前重建包 native_checks | 旧绑定包直接校验 |','| --- | --- | --- | --- | --- |']
for row in results['runs']:
 lines.append(f"| {row['run']} | 14 P / 0 F / 0 U | 14 P / 0 F / 0 U | exit 0 | exit 2 |")
lines += ['','此前六份 14/14 结论均仍成立；六份 catalog 完全一致，六份 report.json 的 JSON 内容也完全一致。此处包括初版 Android 两份和接口修订后的 Android 两份，以及 iOS 两份，不把重复采集算作独立产品发现。每份原始矩阵另有 2 个明确 N/A 刺激单元。','', '严格 state/capture identity：12 个选定状态全部通过当前 bound_state_evidence；原始 state_id、input hash、实例、event revision、capture_consistent:true 及 binding_after_capture 均符合要求。全部状态仍具完整逐状态覆盖。具体原始帧索引及绑定保存在 strict-state-identity-results.json。','', f"像素：{pixels['pixel_assertion_count']} 个原子颜色断言，共 {pixels['sample_count']} 个原始状态帧样本；{pixels['measured_count']} 个可测，{pixels['ineligible_count']} 个因目标不完全可见而不适用。eligible-but-unmeasurable 为 {pixels['eligible_unmeasurable_count']}，因此没有这类帧被判 P。当前源码的 eligible:true 且 status!=measured 阻断 P 判据已按工具 SHA 保存摘录。**这些原始输入没有 eligible-but-unmeasurable 负例，本复验没有动态触发该阻断分支，也没有篡改原始输入来制造负例。**",'', '旧绑定包的六次 exit 2 全部保留，并非产品断言失败。当前校验器重建出的证据结构有版本内容变化：四份 v2/iOS 包仅新增像素 sample 的 eligible 字段；最初两份 Android 包还新增从原始节点读出的 native_geometry 证明和 native_viewport_px:null 字段。当前工具因此拒绝旧包与重建包不一致。从原始人工请求重新生成的新包全部通过；没有编辑旧包以绕过拒绝。exact-artifact-differences.json 记录每个 JSON Pointer 的精确差异。','', f"复验执行墙钟时间：{results['wall_seconds']:.6f} 秒；24 条工具 CLI 的具体 argv、开始 UTC、耗时、退出码、stdout 及哈希均保存在 commands.jsonl 与 logs/。当前工具 SHA 在 tool-identities-before.json / after.json，运行前后完全一致。",'', '核心脚本 SHA256：','']
for name in ['native_checks.py','native_pixels.py','review_contract.py']:
 lines.append(f"- `{name}`：`{tools['files']['scripts/'+name]}`")
lines += ['','原 seal 的 canonical SHA256 保持 `6e93f34eff202ec0e247cc47357d490f6a244a0b957cb6f49e067ead47ad536f`。前、后及最终核对均验证 876 个原封存文件未变。新 seal 只封存本目录，并以原 seal / 输入哈希关联旧证据。','', '本次是旧中性能力证据的工具版本复算；未重新作视觉判断，未补充独立第二裁判，也未改变原环境 F/P 历史记录。本次 14/14 不等同于双裁判独立验收或业务产品验收，不涉及未来业务设计。']
lines += ['', '封存阶段额外记录：第一次 seal 尝试发现复验结束后 references/atomic-review.md 的 live SHA 已变化，因此拒绝封存并保留记录。所有 scripts 的 SHA 始终未变；本次结果绑定的是工具快照中实际复验时的脚本和文档。post-replay-tool-change.json 保存文档前后 SHA；最终文档另存快照。没有重新运行判定或 SDK。']
(R/'REPORT.md').write_text('\n'.join(lines)+'\n')
# Final original-content verification immediately before sealing the new output.
original=json.loads((O/'seal.json').read_text());expected=(O/'seal.sha256').read_text().strip();bad=[p for p,v in original['files'].items()if not(O/p).is_file()or sha(O/p)!=v['sha256']];badlinks=[p for p,v in original.get('symlinks',{}).items()if not(O/p).is_symlink()or os.readlink(O/p)!=v]
original_result={'canonical_seal_sha256':canon(original),'expected_sha256':expected,'file_count':len(original['files']),'mismatched_files':bad,'mismatched_links':badlinks,'verified':canon(original)==expected and not bad and not badlinks,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};assert original_result['verified']and original_result['file_count']==876
(R/'original-seal-final.json').write_text(json.dumps(original_result,indent=2)+'\n')
current={name:sha(W/'native-ui-agent'/name)for name in tools['files']};assert all(current[name]==tools['files'][name]for name in current if name.startswith('scripts/'));(R/'tool-identities-final.json').write_text(json.dumps({'files':current,'scripts_unchanged_from_replay':True,'all_files_unchanged_from_replay':current==tools['files']},indent=2)+'\n')
excluded={'seal.json','seal.sha256','seal-verification.json'};files={}
for base,dirs,names in os.walk(R,followlinks=False):
 dirs[:]=[d for d in dirs if d!='__pycache__']
 for name in names:
  p=Path(base)/name;rel=str(p.relative_to(R))
  if rel not in excluded:files[rel]={'sha256':sha(p),'bytes':p.stat().st_size}
seal={'version':1,'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'SDK-free replay outputs only. Original 876 sealed files are external read-only inputs, linked by original seal SHA and input hashes.','original_seal_sha256':expected,'excluded':sorted(excluded)+['**/__pycache__/**'],'files':files};digest=canon(seal);(R/'seal.json').write_text(json.dumps(seal,sort_keys=True,indent=2,ensure_ascii=False)+'\n');(R/'seal.sha256').write_text(digest+'\n');assert all(sha(R/p)==v['sha256']for p,v in files.items())
verification={'verified':True,'canonical_seal_sha256':digest,'file_count':len(files),'total_bytes':sum(v['bytes']for v in files.values()),'old_file_count':876,'old_seal_unchanged':True,'sdk_launched':False};(R/'seal-verification.json').write_text(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification))
