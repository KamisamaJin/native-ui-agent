# 平台适配

以下是接入方法，不表示 runner 已经自动适配所有原生工程。工程命令、测试宿主、输出位置和测量代码需由 agent 从当前项目确认或生成。runner 只执行 profile 中的真实参数数组。

## 选择执行路径

| 项目 | 组件反馈 | 页面集成 |
| --- | --- | --- |
| Android Compose | 已有 compose-ai-tools/Preview 优先；也可使用项目已有 Paparazzi | 现有 Android UI/E2E 工具、模拟器 |
| Android XML/Views | Paparazzi，继承工程资源与主题 | 现有 instrumentation/UI 工具 |
| iOS SwiftUI | SnapshotTesting 测试宿主；已有可用预览工具时可复用 | 实际 App + 已确认的模拟器控制工具 |
| iOS UIKit/Objective-C | SnapshotTesting 创建真实 View/VC；需要时用 Swift 测试宿主调用已有模块 | 实际 App + 已确认的模拟器控制工具 |

组件无法隔离、依赖系统能力或构建版本不兼容时，可改用现有页面截图路径，backend 填 simulator。该名称只标记执行路径，不额外安装或提供设备控制能力。

## Android Compose

复用已有 @Preview、主题和 fixture；新增 Preview 也应调用生产 Composable。不要以重新绘制一个近似组件代替实际生产组件。

compose-ai-tools 的 CLI 可渲染 Preview 并输出 PNG、布局等信息。先读取当前安装版本的 help，确认 list/render 的筛选与输出参数，再生成 profile。将输出定向到本次 {output} 下，避免把旧缓存图当作本轮已渲染的证据。其构建版本要求需逐项核对，不为普通 UI 改动自动升级旧工程。

已有 Paparazzi 时沿用它即可，不要求同时安装两种组件渲染器。

## Android Paparazzi / View / XML

确认 Gradle wrapper、AGP、JDK、Paparazzi 版本以及实际 module/variant。测试 source set 中调用真实 Composable 或加载真实 XML/View，沿用资源、字体、主题及生产数据绑定入口。

普通 test task 可用于生成渲染报告；verifyPaparazzi<Variant> 用于已有 golden 的回归。使用当前项目支持的单用例筛选方式，检查原生报告确实执行了对应测试。

capture profile 的实际图片 glob 要指向该用例的一张 actual 图，不能笼统收集整份报告中的实际图、参考图和差异图。确认当前版本的报告目录。首轮可使用 Gradle 的 --rerun-tasks 强制产生本轮产物；后续优化缓存时必须保留输入与缓存命中的可追溯证据。

recordPaparazzi<Variant> 会写 golden。验证流程使用普通渲染/verify；需要生成候选 golden 时在单独的临时工程目录中执行并收集候选，不把新图直接覆盖已批准基准。

数值检查额外生成 measurements.json。标准 View 可测量宿主坐标系中的实际边界，TextView 可按具体文本、主题和富文本覆盖读取有效样式。Compose 的语义树不保证提供所有绘制属性；可使用渲染器实际提供的测量数据或针对性测试，缺失时保留 needs_review。

### 真实工程接入时的检查

本仓库 Reply 试验使用 Paparazzi 的 HtmlReportWriter 导出实际图，从本轮 run 报告确认测试名和图片路径，并核对 JUnit XML 恰好执行了目标测试。不要假设 Android Kotlin 测试编译环境能直接引用 java.awt.BufferedImage 来实现自定义截图 handler。设备配置的物理尺寸也不一定等于导出 PNG 尺寸，须解码实际文件确认。

检查项目主题中的窗口副作用。LocalInspectionMode 与 View.isInEditMode 是两个独立条件；仅设置前者不保证能跳过 context as Activity。本次 Reply 在测试宿主提供 Preview 环境和 isInEditMode 为 true 的 LocalView，调用原有主题及生产组件；窗口行为另由真实 Activity 验证。将这种环境差异明确记入 profile，不能据此声明组件宿主覆盖了窗口行为。

存在现成 modifier 参数时，可在测试调用点增加 onGloballyPositioned，读取实际 LayoutCoordinates，无需修改生产组件或增加业务 ID。说明测量包含哪层 modifier；外层尺寸不能直接称为内部 padding、文字字号或字形边界。

## iOS SnapshotTesting

确认 workspace/project、scheme、测试 target、SDK/部署版本、实际模拟器标识与已安装 SnapshotTesting API。将依赖添加到测试 target，继承现有 UIKit/SwiftUI 架构。

UIKit 创建真实 View/VC 并运行实际配置入口，完成布局后截图。SwiftUI 使用承载真实 View 的测试宿主，注入主题、状态、字体及环境。涉及导航、安全区或生命周期时使用相应父容器。

建议测试宿主将本轮实际图片输出到 NATIVE_UI_OUTPUT；这是本包装层约定的环境变量，不是 SnapshotTesting 自带的图片输出开关。可在测试代码中使用已确认版本的 Snapshotting 图片策略捕获 UIImage 并写入该目录；不要仅设置变量就假设框架会导出图片。

必须在测试宿主内确认输出变量实际可读。runner 设置父进程环境，不保证 Xcode/模拟器或其他测试 worker 自动继承；使用当前工程确认可用的测试计划、环境配置或适配脚本传递。无法传递时，用已验证的测试附件导出流程产生本轮图片。iOS 示例 profile 只展示 xcodebuild 参数结构，不包含这个工程专用桥接。

复用现有 assertSnapshot 测试时，普通验证应使用当前版本的非记录策略，并从实际 xcresult/测试附件中导出 actual 图。仅有引用图片或截图路径文字不足以证明本轮产生了 actual。图片导出的具体命令需根据已安装 Xcode 的 xcresulttool help 确认。

新组件缺少基准时，候选录制与正式 golden 使用独立目录。正式参考和实际候选分开，记录模式导致的原生测试失败不能被当作整套构建通过；需要单独的候选捕获入口。

精确测量需在测试宿主额外实现。UIKit 的 frame、bounds、文字绘制范围、layoutMargins 和约束常量不是同一事实；统一坐标系，注明测量含义。颜色应解析当前 trait/主题和富文本覆盖，字体应区分默认字体与实际文本 run。SwiftUI 没有由本 Skill 提供的通用完整样式树。

本仓库 AlertToast 试验采用 build-for-testing 生成 xctestrun，在目标测试的 EnvironmentVariables 中写入本轮输出路径及场景，再 test-without-building。复制 xctestrun 到证据目录时，要保留 __TESTROOT__ 对原构建产物目录的含义。此方法已在试验使用的 Xcode 27.1 验证；其他版本先读本机 xctestrun 文档并确认格式。核对 xcresult 的目标测试、执行数及失败数，并确认测试宿主实际写出了本轮 PNG；仅 xcodebuild 成功不足以证明目标测试执行。

## 页面反馈

有 MobileBuildMCP、agent-device、项目既有 UI/E2E 工具时，使用已验证存在的能力来构建、启动、导航和截图；没有相应工具时不编造调用名称。固定页面状态并确认截图中是本次目标，再把对应命令包装进 profile。

组件检查与页面检查分别报告。布局在独立宿主中通过，不能自动证明页面中的滚动、键盘、导航和点击正确。

## 一手资料

- https://github.com/yschimke/compose-ai-tools
- https://github.com/yschimke/skills/tree/main/skills/compose-preview
- https://github.com/cashapp/paparazzi
- https://github.com/pointfreeco/swift-snapshot-testing
- https://github.com/getsentry/MobileBuildMCP
