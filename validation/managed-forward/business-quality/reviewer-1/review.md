匿名组件质量独立评审 1

在固定配置范围内，initial 不接受，A、B 接受。确认的初始共因为 **1 个 iOS 视觉实现问题**：初版在已指定明确禁用色的按钮标签外继续使用 `PlainButtonStyle`，平台禁用处理又淡化了整张不可用/已发送选项卡与禁用动作。A/B 均通过返回实际 `configuration.label` 的自定义样式修复此问题；两份最终实现没有确认的残留或新增回归。本结论没有识别或推测版本、工具映射。

| 候选 | 必需记录 | P | F | U | 确认产品共因 |
|---|---:|---:|---:|---:|---:|
| initial | 1280 | 1266 | 14 | 0 | 1 |
| A | 1280 | 1280 | 0 | 0 | 0 残留、0 回归 |
| B | 1280 | 1280 | 0 | 0 | 0 残留、0 回归 |

每个候选覆盖 public/private × iOS/Android。每个端/范围有303条原生、事件、几何及图像原子，加17条源码职责；原始矩阵仍为312格，其中9格由独立设计明确不适用。源码职责在两范围相同，68个分范围源码职责记录对应34个候选内端/源码判断。14条失败记录是12个分范围禁用发送色原子和2个分范围源码palette职责，均归于同一原因；不是14个缺陷。公开的两组D0是同一个initial的复证，不增加缺陷分母。

原始初版 [Swift源码](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/packet-public/source/initial/MenuChangeReviewPanel.swift:137) 的颜色常量正确，选项、数量、发送分别在284、325、452行使用普通样式；[发送标签](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/packet-public/source/initial/MenuChangeReviewPanel.swift:440) 也明确指定了禁用色。产品呈现事实另由原生框和原始PNG建立，不能仅从常量推导。公开禁用发送的批准区域实测为 `#FFE7EAE3`，规定为 `#FFD9E2DC`；隐藏深色环境为 `#FF223229`，规定为 `#FF344A3C`。每范围的 draft、replacement、quantityChanged、sent、revised、sentRevised 六个状态均复现，启用状态的accent色通过。独立复核保持原采样区域、12像素下限、0.9支持率及1通道容差。18条原始F告警（含重复公开D0）均为TP，12个唯一分范围原子归为一个原因；FP和未裁定均为0。

具体原图例：[公开initial draft快照10](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/packet-public/native/A/public/D0/ios/native/attachments/47E0DD1C-517F-4C46-AC50-8E18AD943E1A.png)、[隐藏initial draft快照15](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/packet-initial-hidden/initial/ios/native/attachments/1174D858-157B-46F0-886C-DF602A050D37.png)。其状态、PNG哈希、输入/事件epoch、实际控件图像框和支持像素在 [公开复核](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/reviewer-1/public-send-independent-pixel-check.json) 与 [隐藏复核](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/reviewer-1/hidden-send-independent-pixel-check.json) 中逐项保存。不可用卡的整体淡化也在相同初版身份原图中确认；没有引入额外对比度阈值或屏幕阅读器结论。

A/B 当前源码的 [A自定义样式](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/packet-public/source/A/MenuChangeReviewPanel.swift:159)、[B自定义样式](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/packet-public/source/B/MenuChangeReviewPanel.swift:159) 与其实际按钮调用相符。两份当前原图均恢复 light 禁用 `#FFD9E2DC` / 启用 `#FF216B4A`，dark 禁用 `#FF344A3C` / 启用 `#FF8DDBAF`。选择、数量、积分、接受、发送及同一实例修订的247条原始标签/控件/几何/回调事实，在每端每范围单独重算通过。隐藏路径证实选择不可用后清空、原期望份数保留、积分撤回、重新选择时上限夹取及两次精确负余额回调。未确认业务、accessibility或testability类初始共因。

每端每范围32条图像命题全部完成独立实际判断：完整标题换行可读、三个选项描述未被卡片截断、余额无重叠、标题视觉强于章节标题。灰淡问题单独计入palette原因，不冒充裁切失败。少数余额卡没有单张完全落在视口内的快照，原始重叠片段覆盖卡片顶端与底端，并有共同稳定输入/实例绑定；未用拼图接缝判断缺陷。每个实际值均保留当前源身份、准确状态、原始图路径/哈希和快照索引。

原先每组32个自动U及初评阶段private303个待采集U都保留在原始报告和历史记录中，随后由原始补充与显式图像实际值关闭，未删项或改预期。最终必需未评估项为0。[完整账本](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/reviewer-1/required-obligation-ledger.json)、[U历史](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/reviewer-1/mandatory-unknown-history.json)、[204条分范围源码实际值](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/reviewer-1/source-actuals-final.json) 与 [最终判定](/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality/reviewer-1/quality.json) 提供逐项引用。六份隐藏模板submission保留各自原始catalog/observation摘要，可由协调者只读绑定。

三个输入包SEAL与共1831个文件全部核验，结尾再次核验未变。公开初评及隐藏最终阶段封存文件保持字节不变。源码审查、JSON重算及PNG解码/原图查看以外未执行生产组件、SDK或模拟器，未修改任何输入或实现，未读取其他评估者、映射或生产者source-claims实际声明。

接受范围为嵌入的MenuChangeReviewPanel、固定decode/direct桥接与独立设计配置的两条八状态连续案例：公开390单位浅色LTR默认文字；隐藏320单位深色RTL大文字的一个组合环境。它不宣称全应用、所有输入笛卡尔组合、真实网络、物理触摸、OS读屏行为或未测computed style。原生几何仅为实际可访问性/控件框；字体基值和间距为源码职责。未运行独立验收CLI，CLI成功也不是此质量结论的替代证据。
