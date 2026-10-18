# Native UI Agent

让 coding agent 在已有 iOS / Android 工程中实现 UI，通过真实原生渲染、看图、可测量断言和源码修正交付结果。

这个仓库包含可加载的 **Skill**、确定性的 **证据 runner**，以及两个真实开源工程的接入代码和实跑记录。模型由宿主 coding agent 提供；runner 不内置 LLM，也不假装提供通用完整的原生样式树。

## 已实际验证

2026-10-18 在固定上游提交上开发两个新增功能，独立设计与验收标准先于实现提交到 Git，未向生产代码注入已知错误：

| 项目 | 新增 UI | 最终结果 | 源码修正 |
| --- | --- | --- | --- |
| [Android Reply](https://github.com/android/compose-samples) | 邮件卡片附件摘要：数量、首个描述、长文省略、空态隐藏 | **5/5** 场景通过；真实 Activity 点击复验通过 | 首版达标，0 轮；未人为制造错误 |
| [iOS AlertToast](https://github.com/elai950/AlertToast) | 可选上传进度 HUD：百分比、进度条、长标题、旧调用兼容 | **6/6** 场景通过；旧调用像素不变 | 看图发现系统灰轨道偏离浅蓝参考，1 轮样式修正 |

干净检出固定上游提交、应用功能补丁和安装宿主后，两端又各实际渲染 1 次；结果与最终同状态图片一致。

![独立参考、首版及最终结果](validation/feature-development/comparison.png)

完整的[新增功能开发报告](validation/feature-development/README.md)、[设计冻结清单](validation/feature-development/design/freeze.json)、[机器可读结果](validation/feature-development/result-summary.json)。之前的[受控回归试验](validation/native-ui-pilot/README.md)单独保留，不能与新增开发试验混为一谈。

这不是独立盲测，也没有无 Skill 对照组，不能据此声称提升了某个百分比的 PR 质量。首次快速视觉检查曾漏过轨道色，详细设计核对才发现；原始通过、后续失败及修正记录均保留。字号、颜色、间距能否精确观测取决于平台和采样对象。

## 工作方式

1. 按当前需求、代码改动、调用位置和业务文字定位真实组件，不要求全项目登记业务 ID。
2. 实现前固定独立设计、规则来源及相关状态。新设计线框与原生截图不是同一种像素基准。
3. 生成薄测试宿主，调用生产 UI，控制数据、主题、时间与动画。
4. `capture` 执行真实原生命令，保存本轮图片、原生报告、源码/参考指纹和命令日志。
5. Agent 阅读实际图；`review` 汇总绑定本轮证据的视觉结论与数值/像素断言。
6. 有问题时修改生产源码，重新构建和渲染；组件通过后另做实际页面复验。

`captured` 只表示证据采集成功。缺测试、缺图、缺参考、无测量或未审图都不等于样式通过。不会自动覆盖正式 golden，也不能用旧截图声明新代码通过。

## 使用 Skill

将 [`native-ui-agent/`](native-ui-agent/SKILL.md) 作为宿主 coding agent 可加载的 Skill 目录，或让 agent 直接读取其 `SKILL.md`。该目录可独立复制；`validation/` 是工程接入及验证材料。

示例需求：

> 使用 native-ui-agent，在现有邮件卡片中增加附件摘要。先固定设计参考和验收，再复用工程主题、数据和组件生成测试宿主，渲染普通、长描述、深色和窄屏状态；按图与原生测量修正，提供页面复验及证据。

Skill 目前给出 SwiftUI/UIKit、Compose/Views 的接入指导；仓库实跑覆盖的是 **SwiftUI 和 Compose**。它不自动适配任意旧项目，也不替代业务数据、导航和后端契约测试。

## Runner

Python 3.9+，依赖见 [requirements.txt](native-ui-agent/scripts/requirements.txt)：

```sh
python3 -m pip install -r native-ui-agent/scripts/requirements.txt
python3 native-ui-agent/scripts/ui_loop.py capture \
  --project /path/to/native-project --profile /path/to/case.json \
  --output /path/to/new-evidence-directory
```

Agent 看图后按[协议](native-ui-agent/references/protocol.md)写 `visual-findings.json`：

```sh
python3 native-ui-agent/scripts/ui_loop.py review \
  --capture /path/to/new-evidence-directory/capture.json \
  --findings /path/to/visual-findings.json --output /path/to/new-review-directory
```

每个 profile 对应一个组件状态、一张 actual 图；项目命令使用 argv 数组执行。三类检查分别保留方法和边界：

| 检查 | 能证明什么 |
| --- | --- |
| visual | Agent/人工对实际图与独立参考的判断；可能漏检 |
| numeric | 宿主实际提供的特定测量与期望比较；缺数据为 needs_review |
| pixel | 同尺寸原生图的区域/整图 RGBA 差异；不证明业务或样式属性语义 |

平台接入看[平台适配](native-ui-agent/references/platforms.md)，配置结构看 [Android 示例](native-ui-agent/assets/profile.example.json)、[iOS 示例](native-ui-agent/assets/profile.ios.example.json)。

## 复跑双端新增功能

需要 macOS、已完成首次设置的 Xcode、已安装 iOS 模拟器、Android SDK 36 和 JDK 21；实跑版本与命令详见[报告](validation/feature-development/README.md#复跑)。

```sh
python3 validation/feature-development/prepare.py \
  --workspace /absolute/path/to/new-workspace \
  --android-sdk /absolute/path/to/Android/sdk \
  --java-home /absolute/path/to/jdk-21/Contents/Home \
  --ios-device YOUR_INSTALLED_SIMULATOR_UUID
```

此入口只接受新目录，检出固定提交、应用 host/生产功能补丁、复制测试宿主并生成本机 profiles。不会覆盖已有应用工作目录。功能交付为完整补丁和新文件，不把整个上游仓库及 SDK 上传到这里。

归档 capture 保留当时绝对路径和环境供追溯；迁移机器时使用 `prepare.py` 生成本机配置。不同系统/渲染器可能改变像素，不能直接更新基准消除差异。

## 验证

```sh
python3 -B -m unittest discover -s native-ui-agent/tests -v
python3 validation/feature-development/verify_evidence.py
```

第一条验证 runner 的 25 项协议/失效行为；第二条跨机器审计归档图片、报告、原生测试数、独立设计哈希和已发现的轨道颜色差异，不运行原生 SDK 或模型。GitHub CI 只执行这两类检查，不声称重新运行双端模拟器。

## 目录

```text
native-ui-agent/                  可复制的 Skill、runner、协议与测试
validation/feature-development/  新增 UI：冻结设计、功能补丁、宿主、复跑入口与证据
validation/native-ui-pilot/       历史受控回归试验、宿主接入记录及上游许可
```

## License

原创 Skill、runner、文档和宿主代码使用 [MIT](LICENSE)。上游派生组件补丁、截图与生成报告保留各自许可，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。克隆工程、构建缓存、SDK、签名文件和本地环境配置由 `.gitignore` 排除。本项目独立于 Android、Apple、Point-Free 及上述开源维护者。
