# 默认执行服务

新增/修改原生 UI 使用 `python scripts/ui_loop.py native --config PROJECT.json --output NEW_DIR`。集成端固定项目配置并保存 cycle、原始 capture、任务队列及摘要。每轮传上一原始 `--previous RESULT --previous-sha256 SHA`；交付传 `--final`，重复历史传 `--history PINNED_CYCLE_LIST`。模型不能覆盖预期或手选状态。

配置字段：`plan`、`design_lock`、`design_sha256`、`routes`、`routes_sha256`、`fixtures`、`bridge`、`launch_ref`、`source_roots`、`native_options`、`environment`、`environment_sha256`；可选独立批准的 `policy`/`policy_sha256`。有视觉原子项时必须配置生产源码目录以外的 `review_store`，供集成端保存追加式审查注册表；不是临时传给模型的可选开关。摘要由独立批准方保留，配置不产生新预期。

固定链路：重建原始采集 → 自动读取该 capture 的审查注册表 → 重建绑定的实际观察 → 需求路由 → 定位诊断 → 按工作类型派发。`review_images`、`repair_source`、`review_measurement` 和定位/能力诊断在源码未变时不启动 SDK。缺少状态证据才进入 `acquire_native`；源码修改后依据实际差异、原始发现和批准回归依赖选择定向复验；未知影响或上一包不完整时回退全量。最终总是新鲜完整采集。

集成端把 `before-review-request.json` / `after-review-request.json` 派给看图工作者，读取原始帧并填写 template 的 actual、reason、snapshot_indices；预期、单位、责任与出处由批准契约生成。提交：

```sh
python scripts/ui_loop.py bind-native-review --config PROJECT.json \
  --capture-result RESULT --capture-sha256 SHA \
  --submission ORIGINAL_ACTUALS --submission-sha256 SHA --output REVIEW_STORE/NEW
```

工具验证源码/输入/状态/图像/策略身份、重新计算结论并自动注册；下一次 `native` 自动加载，模型无需记住 review 参数。多个不重叠审查可合并；矛盾不能 last-wins，必须用 `--supersedes-sha256` 和 `--revision-reason` 明确保存原判断与修订。原始采集目录不可覆写。已修改源码可以使用历史发现规划修复范围，不能获得当前通过信用。

最终采集后仍有图审查时，绑定新图的实际观察，再执行 `finish-native-review --config PROJECT.json --cycle FINAL_CYCLE --cycle-sha256 SHA --output NEW`。该入口重建最终原包并强制当前源码一致、全量覆盖和完整门控，不再次采集。定向包或普通反馈 cycle 不能用于交付接受。CLI `native` 的 0 表示已完成派发（也可能在等审查/修复），1 表示阻塞，2 表示配置/证据错误；只有结果的 `status: accepted` 表示交付门控通过。

缺失叶节点、重复身份、未取得状态、无法测量分别保留原始节点/帧和源码引用。候选不替代批准选择器；源码声明不冒充运行时属性。相同源码/问题的两次反馈采集后，历史阻止无效重跑；任何未知、环境错误或阻塞不能写成通过。此服务执行工具和任务队列，不自动理解设计或修改代码。
