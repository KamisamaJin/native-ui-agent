from pathlib import Path
import json
import hashlib

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "cause-matching"

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

source_index = read(BASE / "packet-public/SOURCE-INDEX.json")
cohorts = read(OUT / "cohort-core-checks.json")
pixels = read(OUT / "send-pixel-independent-recheck.json")["rows"]
ledger = read(OUT / "coverage-ledger.json")
source_cross = read(OUT / "cross-review-source-actuals.json")
visual_cross = read(OUT / "cross-review-visual-actuals.json")
submissions = read(OUT / "submission-binding-independent-checks.json")
raw_alerts = read(OUT / "original-alert-rows.json")
assert len(raw_alerts) == 18
assert source_cross["summary"]["semantic_disagreements"] == 0
assert visual_cross["summary"]["semantic_disagreements"] == 0
assert visual_cross["summary"]["evidence_binding_errors"] == 0
assert not any(x["errors"] for x in submissions)

expected_seals = {
    "reviewer-1": "6e18c1fdd9db3571ece8c6d1aa63601074f8512186eee54dce71257155a2fc8f",
    "reviewer-2": "b7f14246777e2da940d08729682cd63b50199c3f45d0f97d71b6787ca82bce47",
}
identity = {
    "role": "independent anonymous common-cause matcher and disagreement reviewer",
    "reviewer_seals": {r: {"expected_raw_sha256": expected, "observed_raw_sha256": sha(BASE / r / "seal.json"), "match": sha(BASE / r / "seal.json") == expected} for r, expected in expected_seals.items()},
    "input_packet_seals": {r: sha(BASE / r / "SEAL.json") for r in ("packet-public", "packet-hidden-finals", "packet-initial-hidden")},
    "permitted_roots": ["reviewer-1", "reviewer-2", "packet-public", "packet-hidden-finals", "packet-initial-hidden"],
    "version_mapping_not_read_or_inferred": True,
    "business_administration_not_read": True,
    "external_repairer_narratives_or_other_experiments_not_read": True,
    "producer_source_claims_not_used_or_semantically_read": True,
    "source_comments_not_used_as_evidence_of_runtime_success": True,
    "SDK_observer_production_or_acceptance_code_not_run": True,
    "all_writes_confined_to_new_cause_matching_directory": True,
    "integrity_scope": "All 1939 files in the five permitted roots are hashed, including opaque producer-claim files solely for integrity. Content analysis uses the two sealed reviews, fixed design/API/source and original native/image evidence.",
}
assert all(x["match"] for x in identity["reviewer_seals"].values())

disabled_states = ["draft", "replacement", "quantityChanged", "sent", "revised", "sentRevised"]
requirement_refs = []
for scope in ("public", "private"):
    path = f"packet-public/design/{scope}/reference.json"
    requirement_refs += [
        {"path": path, "pointer": "/responsibilities/12", "id": "component.palette", "clause": "The source chooses each light/dark palette role and does not attenuate the complete unavailable row.", "sha256": sha(BASE / path)},
        {"path": path, "pointer": "/obligations/12", "id": "action-appearance", "clause": "The actual send control uses its appropriate enabled/disabled solid fill and current wording.", "sha256": sha(BASE / path)},
        {"path": path, "pointers": [f"/expected/{state}/send-fill" for state in disabled_states], "id": "send-fill", "approved_disabled_argb": "#FFD9E2DC" if scope == "public" else "#FF344A3C"},
    ]

def source_ref(candidate, start, end, fact):
    source = source_index[candidate]["ios"]
    return {"path": "packet-public/" + source["packet"], "sha256": source["sha256"], "line_start": start, "line_end": end, "fact": fact}

source_refs = [
    source_ref("initial", 137, 156, "Opaque exact light/dark role constants exist, including disabled fill/ink."),
    source_ref("initial", 261, 290, "The option label supplies explicit role colors, followed by PlainButtonStyle and native disabled state."),
    source_ref("initial", 313, 328, "The quantity label likewise supplies explicit disabled roles, followed by PlainButtonStyle."),
    source_ref("initial", 420, 454, "The send label explicitly selects the required disabled fill before PlainButtonStyle and disabled."),
]

def example_pixel(candidate, scope, atom="draft/send-fill"):
    rows = [x for x in pixels if x["candidate"] == candidate and x["scope"] == scope and x["id"] == atom]
    # Pick the bottom original in the complete public sweep, common in both reviews.
    row = rows[-1] if scope == "private" else next((x for x in rows if x["cohort"].startswith("A/") and x["snapshot_index"] == 10), rows[-1])
    return {k: row[k] for k in ("cohort", "id", "image", "image_sha256", "snapshot_index", "source_sha256", "binding", "native_image_box", "fixed_sampling", "fixed_expected_argb", "interior", "fractional_edge_superset")}

dispositions = {}
for arm in ("A", "B"):
    dispositions[arm] = {
        "status": "repaired", "repaired": True, "residual": False, "unresolved": False,
        "by_scope": {"public": "repaired", "private": "repaired"},
        "reviewer_1_original": {"cause_id": "initial-ios-disabled-button-attenuation", "overall": "repaired", "residual": False, "unresolved": False},
        "reviewer_2_original": {"cause_id": "initial-ios-disabled-label-attenuation", "status": "repaired"},
        "current_source_refs": [
            source_ref(arm, 161, 165, "Executable custom ButtonStyle returns configuration.label without a second whole-label treatment."),
            source_ref(arm, 292, 298, "Option Button uses the custom style and retains native disabled/selection semantics."),
            source_ref(arm, 321, 336, "Quantity Button uses the same custom style and retains native disabled state."),
            source_ref(arm, 448, 462, "Send Button keeps explicit palette branches, custom style and native disabled state."),
        ],
        "current_original_pixel_examples": [example_pixel(arm, scope) for scope in ("public", "private")],
        "all_configured_send_atoms": {"public": "8 P, including all 6 disabled states", "private": "8 P, including all 6 disabled states"},
        "native_control_semantics_and_callbacks": "All 247 native control/label/geometry/callback atoms independently rederived for each current platform/scope; no F/U.",
        "core_visual_refs": ["core-original-image-review.json", "cross-review-visual-actuals.json"],
    }

cause = {
    "common_id": "CC-001",
    "category": "visual",
    "platform": "ios",
    "scopes": ["public", "private"],
    "reviewer_id_mapping": {"reviewer-1": ["initial-ios-disabled-button-attenuation"], "reviewer-2": ["initial-ios-disabled-label-attenuation"]},
    "description": "Initial iOS native disabled Button styling attenuates the whole already-colored label. This violates the explicit disabled send palette and the prohibition on fading complete unavailable rows. It is one composition cause across states and configurations.",
    "matching_basis": "Both reviewers identify the same initial source hash, three button-style call sites, unavailable/sent row treatment, the same six disabled send states and the same light/dark actual pixels. The different IDs and the additional action-appearance umbrella in reviewer-1 do not change the causal claim.",
    "requirement_refs": requirement_refs,
    "initial_source_refs": source_refs,
    "initial_native_and_image_refs": {
        "complete_pixel_rows": "send-pixel-independent-recheck.json",
        "native_property_rederivation": "native-independent-recheck.json",
        "before_after_source_state_environment_binding": "cohort-core-checks.json",
        "direct_original_image_inspection": "core-original-image-review.json",
        "examples": [example_pixel("initial", scope) for scope in ("public", "private")],
        "public_disabled_actual": "#FFE7EAE3", "private_disabled_actual": "#FF223229",
        "approved_pixel_support": 0.0,
        "enabled_send_control_samples": "Approved light #FF216B4A and dark #FF8DDBAF pass in initial and both final candidates.",
    },
    "status_by_arm": dispositions,
    "counting": {"confirmed_initial_common_causes": 1, "raw_original_F_rows": 18, "canonical_scope_state_send_alerts": 12, "canonical_source_palette_F_rows": 2, "initial_total_required_F_records_after_followup": 14, "duplicate_D0_and_scroll_samples_do_not_increase_causes": True},
    "confidence": "high for the configured component evidence",
    "classification_boundary": "No business logic, native accessibility or testability defect is inferred from palette attenuation. No contrast threshold, exact computed opacity or screen-reader behavior is claimed. The quantity style is an additional same-source call site, not a separately measured new defect.",
}

differences = [
    {"id": "DIFF-01", "kind": "naming_and_requirement_crosswalk", "reviewer_1": "initial-ios-disabled-button-attenuation; component.palette/action-appearance/send-fill", "reviewer_2": "initial-ios-disabled-label-attenuation; component.palette/send-fill", "resolution": "One-to-one CC-001. action-appearance is the independent parent obligation for the same send-fill atom, not a second cause. Original requirement lists retained.", "unresolved": False},
    {"id": "DIFF-02", "kind": "pixel_rasterization_boundary", "reviewer_1": "Uses wholly interior integer pixels; public draft snapshot 10 begins x=139,y=1742.", "reviewer_2": "Its public draft sample begins x=138,y=1741, including one fractional boundary row/column.", "resolution": "Do not erase either recorded rectangle. Independently recomputed exact original pixels on both the wholly interior rectangle and a superset containing every fractional edge. All 60 iOS send samples keep the same result; uniform disabled actuals/support 0 in initial and approved actuals/support 1 in finals. Frozen normalized region, minimum 12, support 0.9 and channel tolerance 1 remain unchanged.", "evidence": "send-pixel-independent-recheck.json", "unresolved": False},
    {"id": "DIFF-03", "kind": "record_count_and_snapshot_scope", "reviewer_1": "448 raw visual decision records include the duplicate public D0; hidden submissions usually cite the whole stable sweep.", "reviewer_2": "384 canonical final visual records; hidden submissions usually cite target originals, retaining the complete sweep separately.", "resolution": "Compare by candidate/platform/scope/assertion ID. All 384 canonical Boolean results and all 204 source results agree; duplicate initial public records agree internally. All original source/image/state bindings and all 12 reviewer submissions are valid. Raw counts and both evidence styles are retained.", "evidence": ["cross-review-source-actuals.json", "cross-review-visual-actuals.json", "submission-binding-independent-checks.json"], "unresolved": False},
]
save("disagreement-review.json", {"semantic_conclusion_disagreements": [], "recorded_differences": differences, "unresolved": [], "forced_consensus": False, "rule": "A shared result alone is not truth; match only exact requirement/source/native/image-backed causes. Unknowns may not be converted to passes."})

alerts_by_arm = {}
for arm in ("A", "B"):
    alerts_by_arm[arm] = {
        "TP": [{"common_id": "CC-001", "category": "visual", "public_initial_own_D0_F_rows": 6, "common_initial_hidden_F_rows": 6, "classification_basis": "The original failed send-fill alerts have correct approved expectations, source/stable-state/native-control binding and independent contradictory original pixels."}],
        "FP": [], "U": [],
        "deduplicated_common_cause_counts": {"TP": 1, "FP": 0, "U": 0},
        "original_row_counts": {"own_public_D0_F": 6, "shared_initial_hidden_F": 6, "initial_F_applicable_to_this_arm": 12, "own_current_public_final_F": 0, "own_current_hidden_final_F": 0},
        "original_current_raw_U_rows_before_image_followup": 128,
        "required_U_remaining_after_explicit_image_actuals": 0,
        "current_confirmed_residual_causes": [], "current_confirmed_regression_causes": [],
        "shared_hidden_counting_note": "The common initial hidden 6 rows are applicable to both arms, but exist only once in the global raw corpus. Do not add per-arm applicable totals to derive global original alert rows.",
    }

conditions = [
    {"condition": "Both public/private product contracts and fixed environments have independent prior approval.", "status": "P", "evidence": "packet-public/design/original-independent-approval.json"},
    {"condition": "Anonymous current source matches source-before/source-after in all native evidence; fixed plan and environment identity preserved.", "status": "P", "evidence": "cohort-core-checks.json"},
    {"condition": "17 source duties per platform/scope, including direct/decode bridges, have explicit current-source actuals and no final F/U.", "status": "P", "evidence": ["cross-review-source-actuals.json", "core-source-review.json"]},
    {"condition": "303 configured required native/image duties per platform/scope are accounted, with 9 independently inapplicable cells retained.", "status": "P", "evidence": "coverage-ledger.json"},
    {"condition": "Every original required manual U is retained and closed by an explicit source/image/state-bound Boolean actual; no unknown was silently dropped.", "status": "P", "evidence": ["cross-review-visual-actuals.json", "submission-binding-independent-checks.json"]},
    {"condition": "The confirmed initial cause is repaired in both configured scopes; no confirmed residual, new regression or mandatory unresolved item remains.", "status": "P", "evidence": ["common-causes.json#/initial_causes/0/status_by_arm", "send-pixel-independent-recheck.json", "native-independent-recheck.json"]},
]
delivery = {}
for arm in ("A", "B"):
    delivery[arm] = {"accepted": True, "judgment": "accepted_within_fixed_embedded_component_scope", "conditions": conditions, "required_U": [], "required_U_count": 0, "confirmed_residual_causes": [], "confirmed_regression_causes": [], "complete_required_counts": ledger["summary"][arm], "independent_quality_review_closed": True, "limits": "No whole-app, physical-touch, screen-reader, unmeasured computed-style or unconfigured input/environment acceptance. The coordinator may bind the exact already-reviewed templates; this reviewer performed a read-only identity/precondition audit and did not execute an acceptance CLI."}

result = {
    "version": 1, "status": "sealed-independent-anonymous-common-cause-review", "identity": identity,
    "initial_causes": [cause],
    "initial_category_counts": {"business": 0, "visual": 1, "accessibility": 0, "testability": 0},
    "regressions": {
        arm: {"confirmed": [], "unresolved": [], "by_category": {"business": [], "visual": [], "accessibility": [], "testability": []}, "coverage": "All final source duties, configured native assertions and both sealed reviewers' original image decisions are covered. Direct original-image core checks and source/pixel/native rederivations corroborate the no-regression judgment; final code changes only the label-preserving style.", "reviewer_originals": {"reviewer-1": [], "reviewer-2": []}, "evidence": ["core-source-review.json", "native-independent-recheck.json", "cohort-core-checks.json", "cross-review-visual-actuals.json"]} for arm in ("A", "B")
    },
    "unresolved": [], "mandatory_U": [],
    "disagreement_review": {"semantic_conclusion_disagreements": [], "recorded_method_or_accounting_differences": differences, "unresolved": [], "original_judgments_changed": False},
    "alerts_by_arm": alerts_by_arm,
    "alerts_global": {"original_failed_rows": 18, "original_failed_row_reference": "original-alert-rows.json", "raw_classification_counts": {"TP": 18, "FP": 0, "U": 0}, "deduplicated_common_cause_counts": {"TP": 1, "FP": 0, "U": 0}, "unique_scope_state_alerts": 12, "duplicate_public_D0_replications": 2, "common_initial_hidden_rows": 6, "provider_host_oracle_integration_F_causes_confirmed": [], "original_raw_U_rows_retained": 448, "canonical_visual_U_followed_up": 384, "final_mandatory_U_remaining": 0},
    "complete_delivery": delivery,
    "initial_delivery": {"accepted": False, "reason": "CC-001 remains in original initial source/rendering.", "required_U": [], "counts": ledger["summary"]["initial"]},
    "verification": {"all_five_input_roots_file_count": 1939, "three_original_packets_file_count_including_SEAL": 1834, "three_original_packets_sealed_payload_file_count": 1831, "reviewer_sealed_member_counts": {"reviewer-1": 66, "reviewer-2": 37}, "original_native_cohorts": 14, "canonical_candidate_scope_platform_groups": 12, "independently_rederived_native_rows_including_duplicate_D0": 3458, "independently_rederived_native_nonpass": 0, "iOS_send_original_pixel_samples": 60, "pixel_samples_are_not_alert_rows_or_defect_counts": True, "source_actuals_agreed": 204, "canonical_visual_actuals_agreed_and_bound": 384, "hidden_reviewer_submissions_identity_checked": 12, "direct_core_original_PNGs_inspected": 8, "not_a_third_full_384_visual_reassessment": True},
    "scope_limits": ["Public: one 390-unit light LTR default-text continuous eight-state case per platform.", "Private: one combined 320-unit dark RTL large-text continuous eight-state case per platform, 600-unit host viewport. It is one environment, not four independent trials.", "Repeated D0 captures, scroll frames, multiple atomic F and duplicate source clauses do not create additional product causes or independent trials.", "Configured native control/AX geometry is not a physical touch-region or OS screen-reader claim; source values are not measured computed style.", "No version/tool mapping or named-version winner is inferred. No production, input or prior assessment was changed."]
}
save("common-causes.json", result)

review = """独立匿名共因匹配审查

确认初版只有 1 个配置内真实共因（CC-001，iOS 视觉）：原生禁用按钮样式对已经明确设色的整张 label 再次衰减。它同时解释不可用/已发送选项整行变淡和禁用发送色错误。A、B 均修复；没有确认的残留、新增回归、未裁定产品共因或必需 U。结论保留为匿名 A/B，不涉及工具或版本映射。

两评审的原始 ID 分别为 `initial-ios-disabled-button-attenuation` 与 `initial-ios-disabled-label-attenuation`。两者对应同一初版 Swift SHA、相同样式调用、相同六个禁用状态及同一组原图像素。评审 1 额外列出的 `action-appearance` 是 `send-fill` 的上层需求，不构成第二个原因。业务、无障碍、可测性未确认初始共因；颜色衰减不自动变成对比度或读屏缺陷。

| 对象 | 必需记录 | P | F | U | 配置内判断 |
|---|---:|---:|---:|---:|---|
| initial | 1280 | 1266 | 14 | 0 | 不接受，1 个视觉共因 |
| A | 1280 | 1280 | 0 | 0 | 接受，已修复，0 残留/回归 |
| B | 1280 | 1280 | 0 | 0 | 接受，已修复，0 残留/回归 |

每个对象是 public/private × iOS/Android 四组，每组 303 项原生/图像职责加 17 项源码职责。原矩阵 312 格中的 9 个独立明确不适用单元仍逐一保留。初版 14 个失败记录为 12 个配置/状态发送色原子及 2 个分范围 palette 源码记录，不能算成 14 个缺陷。两次公开 D0 是同一初版复证。

需求依据是两个 reference.json 的 `/responsibilities/12`（palette，禁止整行衰减）、`/obligations/12`（action-appearance）及各状态的 `/expected/<state>/send-fill`。初版 Swift 第 137–156 行存在正确不透明色，第 284、325、452 行仍使用 PlainButtonStyle；第 440–450 行又已明确指定发送的禁用色。源常量本身不能证明呈现错误。原始唯一真实 Button 框与 PNG 独立重采样显示：浅色批准 `#FFD9E2DC`，初版实际 `#FFE7EAE3`；深色批准 `#FF344A3C`，初版实际 `#FF223229`。初版禁用样本批准色支持率为 0；启用色正确。所有六个禁用状态均在两个配置复现。

A/B 的可执行改动同为第 161–165 行的 ButtonStyle 直接返回 `configuration.label`，并在第 292、333、460 行用于三个原按钮，保留真实禁用语义。两份 Swift 仅第 159、160 行注释不同；三份 Android 字节完全相同。修复结论另由各自当前源码绑定的原图建立：A/B 浅色禁用/启用分别为 `#FFD9E2DC` / `#FF216B4A`，深色为 `#FF344A3C` / `#FF8DDBAF`，支持率均为 1。没有从修复者说明或样式名称直接推导通过。

14 份原始采集中，3,458 条标签/控件/几何/回调原子已从原始节点、祖先关系、原生精确尺寸及 callback_delta 独立重算，全部通过。每条状态断言至少有完整可见的当前原生目标；额外半出视口的滚动帧保留为未采用的片段，并没有变造为新增必需断言。每个选定状态的完整采集、稳定实例/输入/事件绑定、当前源码前后哈希、固定 plan 和批准环境均匹配。隐藏路径两次精确回调保持 −2850 / −1625 cents；修订时撤下选择、保留期望份数、撤销零额信用、随后夹到新上限，更新区间没有回调。无需把视觉缺陷扩展为业务或原生语义缺陷。

两评审的 204 条分范围源码实际值及 384 条去重图审实际值在语义上无分歧。评审 1 的 448 条原始图审记录包括重复 D0；评审 2 最终文件列 384 个规范项。所有引用原图哈希、snapshot、候选源码身份和稳定状态均逐项核验，12 份隐藏 submission 也与原模板 ID、原 observation SHA 和固定 catalog 头一致。原请求只是省略 catalog 中重复的摘要字段，正文未变，不能因此认定产品缺陷。

本匹配者直接查看了 8 张核心原图，包括初版浅/深不可用整行、A/B 当前不可用卡、窄 RTL 大字标题和难以单帧完整容纳的余额卡。余额卡的两个原始重叠片段覆盖顶端与底端，同属同一稳定状态，文字无重叠；没有用拼图接缝作判断。完整 384 项图审仍由两份独立封存评估承担，本审查未声称进行了第三次逐项完整图审；其身份、显式 Boolean 覆盖及核心依据已独立核验。

保留一处方法记录差异：评审 1 的公开 draft 原图采样从 x=139,y=1742 的整内像素开始，评审 2 从 x=138,y=1741 开始，包含了分数像素边界。未覆盖或替换任一原记录。本次在同一批准归一化区域内同时检查整内像素及包含所有边缘的超集；60 个 iOS 发送原图样本在两种边界处理下结论一致。原来的 12 像素下限、0.9 支持率和 1 通道容差没有变化。这个证据表示差异已被稳健原像素验证消解，不是被强制统一。

原始失败告警共 18 行（公开两份 D0 各 6 行、共享隐藏初版 6 行），均是 CC-001 的 TP；FP=0、未裁定=0。去重后是 12 个配置/状态告警、1 个共因。按 arm 统计各有 6 行自身公开 D0 加 6 行共享隐藏初版，但共享部分全局只计一次，不能合计成 24 个原始失败。最终 A/B 原始 F 都为 0。原始 448 行 U 全部仍留在输入，通过额外显式图审实际值关闭；未删除未知、改阈值或让未知自动通过。

A/B 的接受条件是：两个配置的当前源码身份和设计预期固定；四组全部 68 条源码与 1212 条原生/图像必需记录完成；原始图审 U 有有效当前原图补评；共因修复且无残留/回归和必需 U。所有条件在本质量审查范围满足。这里没有执行 SDK、模拟器、生产组件或验收 CLI；协调者可将两份评审各六个身份已核验的模板交给只读绑定流程，CLI 成功不替代产品事实。

结论仅覆盖嵌入组件、固定 decode/direct 桥接、公开 390 单位浅色 LTR 默认字号案例和隐藏 320 单位深色 RTL 大字/600 单位视口的一个组合案例。它不承诺全应用、所有输入组合、实体触摸、OS 读屏、真实网络或未测 computed style；这些不在固定必需项内，未被伪装成已测通过。

两份 reviewer seal 原始 SHA 与授权给定值一致，66/37 个成员全部通过；三个原包共 1831 个封存成员（另有 3 个 SEAL）通过核验。五个允许根的全部 1939 个文件保留读取前后清单。仅在 cause-matching 新目录写出本审查，未改任何输入或此前评估，未读取管理目录、工具映射、外部修复叙述或其他实验。
"""
(OUT / "review.md").write_text(review)
print("common cause count", len(result["initial_causes"]), "A/B accepted", [result["complete_delivery"][a]["accepted"] for a in ("A", "B")], "mandatory U", len(result["mandatory_U"]))
