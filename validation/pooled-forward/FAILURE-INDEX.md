# 保留的失败与限制

此索引用于找到原记录，不是成功用例列表，也不是按日志行数统计产品缺陷。原始绝对路径是出版归档中的键；清理后应使用 `REPRODUCE.md` 的只读重放读取，不能将已清理路径解释为原证据丢失。

| 类别 | 原记录入口 | 处理与统计边界 |
| --- | --- | --- |
| 首批设计在首采前被拒 | `business-prestudy-rejected-cohort1/FAILURE.json`、`PRESERVATION-CHECK.json` | 两份已编译自然初版、来源清单、编译命令/日志/状态及 xcresult 原件保留；UI采集为0。随后改用五个不同需求，没有把此失败算作五任务产品缺陷。 |
| 首批失败原件的出版选择遗漏 | `operators/rejected-precode-preservation-v2/ADDITION.json` | 原有限计划只涵盖失败摘要，遗漏迁移后的原始编译/源码材料。新增214个精确原件引用；原计划其他字段不变，历史嵌入路径不改写、不映射为现在复用的输入路径，不补做旧需求评审。 |
| 上述附加出版首次输出目录失败 | `operators/rejected-precode-preservation-v2-setup-failure-v1/` | 冻结的 HOST 父目录只读，第一次建目录失败。保留原脚本和异常，随后仅改用新的 operator 输出目录，没有 chmod 或改写独立冻结目录。 |
| 预代码整数域、Kotlin 类型与宿主 ABI 不匹配 | `business-design-cohort2-v2/` 的原审批与修订链 | 在生产初版和业务 UI 之前修正；原拒绝及修订均保留，不把它们计作 AI 初版自然产品缺陷。 |
| 共同控制器引用通道和中断计时问题 | `business-tools-v1/` 至 `business-tools-v4/`、`operators/cohort2/coordination/` | 缺失独立源码审核入口及中断恢复计时问题保留。v4沿原D0写前证明恢复同一期限，没有给某组延长源码窗口。 |
| 共同冻结与资格验证的被拒修订 | 各 `COMMON-*`、`CANDIDATE-*` 冻结文件与 `qualification/` | 对照共同正确性修复与新版优化分别归因。资格小任务中的受控修复只作机制验证，不进入自然业务缺陷分母。 |
| 原公开业务验证未接受 | `operators/cohort2/coordination/T*-*-closure-verification.json` | T1–T3两组均未接受；T4–T5公开接受。所有十次尝试都保留在时间和交付分母中。公开接受不等于独立完整交付。 |
| 原生采集记录命名冲突及未派发失败 | `cache/business/independent-evaluation/`、`operators/cohort2/coordination/independent_native_v*.py` | v1命名冲突、v2派发前失败和v3首执行延续均保留。只延续未成功派发的原请求，不重新采样来挑选更好图片。 |
| 原生采集时序争议 | `operators/cohort2/coordination/AUDITED-COST-BASES-v1.json` | T5初始参照跨进程时钟差异未确定，保留原值与说明；不猜测校正。各阶段采用有明确边界的原始内核时钟。 |
| AX精度、图像状态绑定、来源引用缺口 | 原 `evaluated.json`、`admission.json` 与最终固定覆盖接合回执 | 必需缺失/无效项保留U；不放宽阈值、不删除不利引用、不将预先不适用计为P，不用后验视觉判断覆盖原工具结果。 |
| 封存后首次来源绑定的权限失败 | `cache/business/independent-evaluation/post-consensus-validation-v1/FIRST-ENVIRONMENT-FAILURE-AUDIT.json` | 原108.136416792秒失败计入共同初始I一次。审计证明没有派发内层子进程；只以相同输入在新记录位置延续一次，原失败没有改成成功。 |
| 五个目录要求与执行范围冲突 | `publication-initial-scope-audit-v1/REPORT.md`、`evidence.json`、`SEAL.json` | 原目录项及固定统计保留，单独披露执行范围/契约不一致。不能把它们解释成五个视觉缺陷、故意故障注入或某组质量劣势。 |
| 产品视觉缺陷 | 原封存共因匹配中的 Case05 | iOS禁用Button导致角色填充色改变，两组都修复。它不是点击命中范围问题；原始和最终PNG均保留。 |
| 独立判读分歧与未裁定结论 | 原30份cause、30份alarm输出及 `cache/business/blind-quality/correspondence/original-v1/` | 原判读、交叉核验、分歧、共识与不确定项全部保留。匹配封存前不揭示A/B，封存后的发现不算原开发循环已检出。 |
| 出版器/评估器的被拒通用版本 | `publication-actual-projection-review/`、`publication-source-alias-review/`、`publication-source-only-binding-review/`、`publication-consumer-review/` 等 | 原版本、独立控制失败与修正保留。不能以输出文件存在或CLI退出0代替来源/作用域/字节验证。 |
| 主选择首次被文档旧哈希拦截 | `cache/publication-archives/closed-business-main-v1/FAILED.json`、`operators/main-preservation-plan-v3/REVISION.json` | 仅README/.gitignore两个出版文档更新，不在原native/public读集中；刷新出版引用并保留首次失败目录、结构和仪表前缀。所有原业务输入、源码、实际值和判读不改。 |
| 传输副本共享的权限竞争 | `publication-cold-links-review-v1/FINDINGS.json` | operator v1 在只读检查后、link前权限变为0644时误报成功；旧源码/原失败保留。v2复用受检只读链接，链接后、替换后及完整校验后再验身份/权限，14项独立控制通过。仅共同出版存储，不计新版原生工具收益。 |
| 传输控制测试开发错误 | `operators/cold-links-author-attempt-1/`、`publication-cold-links-review-v1/DEVELOPMENT-FAILURES.json` | 破坏数据实际被zlib拒绝，首测试未列该异常；另有导入原测试类导致重复执行、扁平结果字段误读。保留原脚本和日志，修测试没有放松数据校验。 |
| 再生空间审计的非候选symlink误阻塞 | `operators/regenerable-headroom-independent-v1/EXPANDED-FIRST-FAILURE.json` | 原qualification的7个敌意fixture链接始终不跟随、不删除；首次审计把它们误作整树阻塞。修审计后原82,407普通文件SHA/bytes/mode全等，候选仍只取精确已核对成员。benchmark缺原namespace证明而保留。 |
| 合成 fixture 清理中断 | `operators/closed-fixture-cleanup-v1/FAILED.json`、`operators/closed-fixture-cleanup-v2/END.json` | 只读目录导致unlink失败，原中断保留。重新核验尚存成员与inode后，只修改已证实归属的目录权限并继续清理，未改证据内容。 |
| 设备池在业务阶段未命中 | `operators/cohort2/coordination/PUBLIC-POOL-TEMPORAL-OCCURRENCES-v1.json` | 三次入池后约300秒到期清理；后续需要设备更晚，没有出池复用。没有为当前样本改过期时间。 |
| 业务完整包复用未授权 | 原独立设计与 `PUBLIC-FEATURE-OCCURRENCES-v1.json` | 两组完整包采用均为0，保持新鲜最终采集；没有追认授权以套用资格验证收益。 |
| 历史后端不能跨环境重算 | `REPRODUCE.md`、`verify_publication.py` 的最终回执 | source-domain和source-responsibility历史判定的可移植重算明确unsupported。原生历史/控制器来源及固定算术重放通过，不代表新项目当前可交付。 |

最终固定指标输入、完整原结果行、成本边界、未评估分母和清理回执由最终出版清单绑定。中间进度、预检CI或一次工具退出成功，均不构成最终已发布声明。

后续封存保留：

- `operators/residual-original-cleanup-v1/FAILED.json`：删除共享JDK副本的首个名字改变了同inode其他名字的nlink/ctime，原严格清理器拒绝继续。v2只接受精确已删除别名能解释的变化，逐文件重验原inode/模式/所有者/mtime/字节和SHA，原失败不覆盖。
- `operators/final-meter-closure-v1/PUBLIC-WINDOW-FIRST-FAILURE.json`：全流磁盘统计拒绝一条在全部公开窗口之后的反向Unix扫描。完整流原字节保留；公开窗口统计改用按原窗口边界机械截取的精确字节前缀，证明全部可能重叠的扫描均纳入。异常不夹断为零、不改原行。
- `publication-replay-cleanup/FREEZE-v1.json` 与 `FREEZE-v2.json`：v1要求冷输入只读，合法Git 0644 checkout会被拒绝；v2仅允许输入保持其原权限，仍校验原SHA和前后身份，输出只读约束不变。原31项控制、失败对照与v2的34项控制均保留。

- `operators/terminal-scratch-cleanup-v1/FAILED.json`、`v2/FAILED.json`及`v3/FAILED.json`：分别保留APFS分配块数变化、只读边界父目录和父级先于子级要求为空的预检中断。普通文件删除前仍要求精确原字节/身份；最终只清理原inode空目录，并立即恢复外层父目录原权限，完成回执位于 `operators/terminal-scratch-cleanup-v4/END.json`。

- `operators/final-publication-replay-external-pin-failure-v1.json`：一次操作命令传入了错误字面SHA，消费者在创建输出之前正确拒绝。随后从原 `PUBLICATION.sha256` 读取实际外部pin，未改清单、证据或评估器。
