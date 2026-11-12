本审计确认“API 文档路径—所提供执行边界”存在可复核的不一致；原“文档位置未满足”判断保持原样，不能据此直接解释为视觉、业务回归或某 Skill 的质量失败。

已证明：五份 API.md 第19行均明确要求 Sources/AlertToast/Business/<组件>.swift。给定五个 initial-I iOS 配置的 production_api subject 与经 canonical JSON 哈希核验的 source-domain approval，则固定为 Sources/AlertToast/<组件>.swift。[P1–P2]

初版通用规则只写在 Sources/AlertToast“之下”，并将确切文件名交给 coordinator；该措辞本身未排除 Business 子目录。T1、T4、T5 笔记明确自述平铺路径遵从 coordinator，但自述不是原 dispatch 或例外授权。[E1，P4]

修复规则限定修改原两个新增组件文件，并冻结其余相关输入。守卫要求安装路径与实际配置 subject 精确一致；普通 source-shape 修订审批仅能追加同策略的源码版本，不能修改安装路径或其他固定配置。因此，在已给配置和该流程内，普通源码修订不能同时消除目录差异；这属于执行范围／合同冲突的证据，不能虚构迁移权限。[E2，E4–E5，P3]

被否证的推论包括：API 没有 Business 要求、给定配置已经采用 Business、普通同策略 shape 审批能改安装路径。审批范围也明确排除业务、样式、运行时、像素和行为通过；它不构成静默改写 API 的依据。[F1–F3]

尚未证明：五份原始 dispatch 的确切内容、当时谁具有何种优先级／豁免授权、每个实际修复配置的历史，以及物理上绝对不能迁移文件。两文件限制是明示授权范围；assert_source 在解锁窗口内并非已验证的两文件机械白名单。[U1–U2，E6]

完整交付解释须同时披露文档位置未闭合与上述范围不一致。仅凭路径项，不能归因人为注入、作者过错、自由修复机会下的失败或 Skill 因果效应。本附录未读取逐臂结果、映射或成本，不重算指标、不追加原 matcher 目录，也不改变任何原 case、alarm、actual 或其他业务／视觉判断。[U3]

证据编号、精确文件哈希、行号及 JSON pointers 见 evidence.json。
