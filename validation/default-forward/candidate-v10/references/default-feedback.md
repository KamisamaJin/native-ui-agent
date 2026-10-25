# 默认执行服务

新增/修改原生 UI 使用 `python scripts/ui_loop.py native --config PROJECT.json --output NEW_DIR`。集成端固定项目配置并保留返回的 `cycle.json`、原始 `capture/result.json` 及摘要。修复后传 `--previous ORIGINAL_RESULT --previous-sha256 PINNED_SHA`；交付用 `--final`。集成端传 `--history PINNED_CYCLE_LIST` 以限制同源码重复采集。不要让模型选择状态、覆盖范围或预期；API 不接受这些覆盖参数。

项目配置字段：`plan`、`design_lock`、`design_sha256`、`routes`、`routes_sha256`、`fixtures`、`bridge`、`launch_ref`（独立来源及 pointer）、`source_roots`、`native_options`、`environment`、`environment_sha256`，可选独立 `policy` 与 `policy_sha256`。路径是集成端实际路径；原生参数与 execution_plan 相同。SHA 由独立批准方保留，不能由实现者重新批准。配置不是新预期来源。

固定执行顺序：重建原始证据 → 需求路由 → 状态绑定定位诊断 → 复验规划 → 统一原生执行 → 新证据路由/诊断 → 完整性门控。缺失叶节点、重复身份、未取得状态、无法测量分别保留原始节点/帧和源码字面引用。候选不能自动替代批准选择器；源码声明不能冒充运行时属性或断言通过。

复验规划包含原始失败和未知项及批准的回归依赖；未请求状态留待全量检查，不是新定位失败。上一包本身是定向包时回退完整计划，避免遗失更早未关闭状态。源码影响不能由依赖图证明；最终始终新鲜完整执行。相同源码/同问题的两次反馈采集后，服务历史会阻止继续无效重跑；修复原因后换源码，或执行必需全量最终验证。任何阻止、未知、环境错误均不能交付通过。

此服务自动执行工具，不自动解释设计含义或改代码。模型仍负责看图、源码诊断和有依据的修复；原子视觉判断与独立最终质量评估保留其适用范围。旧 `capture/review` profile 是兼容入口；复杂业务的默认集成必须调用 `native`，不能绕过服务后宣称执行了本流程。
