# 执行与证据协议

## 运行边界

ui_loop.py 使用 Python 3.9+ 和 Pillow，依赖见 scripts/requirements.txt。Pillow 用于确认实际图片可解码以及像素比较。宿主 coding agent 必须能读本地图片并执行工具，runner 不包含模型 SDK、原生 SDK 或测试依赖的安装器。

一个 profile 对应一个平台、一个组件状态和一张实际图片。先从工程确认命令和测试入口，再编写 profile。目标源码、主题、字体、图片及影响此次组件的配置应列入 target.sources。源码指纹只覆盖列出的文件/目录，不声称覆盖整个依赖图。

## Profile

参考 ../assets/profile.example.json。替换示例路径、类名、图片名及期望来源。字段含义：

- version：整数 1。
- platform/backend：ios 配 snapshot-testing 或 simulator；android 配 paparazzi、compose-preview 或 simulator。
- target.description：业务组件和状态描述；target.sources：存在的工程相对输入路径。
- environment：实际设备/渲染配置、主题、字体缩放、系统及工具版本。由适配器真正设置，runner 只记录，不替你应用这些配置。
- commands：按顺序执行的 argv 数组、工程内 cwd、timeout_seconds 和可选 env；不经 shell。只有 argv 中的 {output} 替换成本轮 native 输出目录，NATIVE_UI_OUTPUT 也指向该目录。
- artifacts：base 为 project 或 output，glob 为相对该根的文件模式，role 为 actual、measurement 或 native-report。role 是接入者声明，需要确认文件实际含义。
- protected_paths：正式 golden 等工程相对目录/文件。pixel 检查的 reference 自动加入保护列表。
- checks：非空检查清单，每项有唯一 id、kind、description、source、可选 required（默认 true）。至少一项必需检查。

输出目录必须是新目录，并位于声明源码和正式基准之外。runner 记录源码与受保护目录前后内容指纹；变化将导致 error。此机制检测写入，不能阻止第三方命令写入或自动恢复基准，所以仍需选择正确命令。

## Capture

~~~bash
python3 /path/to/native-ui-agent/scripts/ui_loop.py capture \
  --project /path/to/app \
  --profile /path/to/case.android.json \
  --output /path/to/evidence/attempt-1
~~~

capture 保存实际 argv、逐条日志、执行状态、源码/基准指纹和复制后的产物 SHA256。命令必须全部成功，并且恰好收集到一张本轮更新/新建、可解码的 actual 图片，才返回 captured。mtime 和内容均未变化的旧文件不计入本轮证据。终端输出 capture_sha256，用于绑定本轮视觉 findings。

这些检查不能代替原生测试报告审查：agent 仍需确认目标测试被发现并执行，图片确实来自生产组件和本次状态。缓存图应由适配器根据当前渲染输入验证后复制到新的本轮目录，不能直接读取旧报告假装重新渲染。

每轮新建输出目录。修改代码后重新 capture；review 会检查已声明生产输入和正式基准是否仍匹配本轮指纹。

## 三类检查

### visual

agent 阅读 actual 图及独立参考后生成 findings：

~~~json
{
  "capture_sha256": "填写本轮 capture 命令输出的真实 SHA256",
  "checks": [
    {
      "id": "badge-visible",
      "status": "passed",
      "observed": "整张卡片与局部图中均能看见待付款标签，长标题未覆盖标签。"
    }
  ]
}
~~~

findings 绑定本轮 capture_sha256，只接受 profile 预先声明的 visual id。不能复用上一轮 findings，也不能覆盖 numeric 或 pixel 的自动结果。未提供的 visual 项保留 needs_review。视觉结论属于模型/人工判断，不证明字号等精确属性。

### numeric

check 增加 measurement、expected、unit、可选 tolerance（默认 0）。原生测试宿主产生 role 为 measurement 的 JSON，形如：

~~~json
{
  "title_badge_gap": {
    "value": 8,
    "unit": "dp",
    "method": "已完成布局后，在同一宿主坐标系中计算两个 View 边界的水平间距"
  }
}
~~~

此数据必须来自实际测试宿主测量，不能让 agent 根据截图编写。runner 验证有限数值和单位，并计算实际差值。单位不同、数据缺少或无 method 时为 needs_review。runner 不能验证测量代码的业务含义；需要审查其采样对象、坐标、主题和文本覆盖。

### pixel

check 增加 reference（项目内参考图片）、可选 region（x,y,width,height，实际图片像素）、channel_tolerance（整数 0..255，默认 0）、max_changed_fraction（0..1，默认 0）。

实际图和参考图尺寸必须相同；不自动拉伸或配准。缺图为 needs_reference，尺寸不匹配为 needs_review。比较 RGBA 各通道的最大绝对差，超过 channel_tolerance 才计为变化像素；变化比例不超过配置值才通过。

每项像素检查分别输出区域 actual/reference/diff。diff 是差异强度红色图，不是语义缺陷定位。给细小关键元素单独设置检查区域，可避免整图比例掩盖局部缺陷。区域和阈值来自预先约定，不能为使失败通过而缩小区域或放宽阈值。

## Review

~~~bash
python3 /path/to/native-ui-agent/scripts/ui_loop.py review \
  --capture /path/to/evidence/attempt-1/capture.json \
  --findings /path/to/visual-findings.json \
  --output /path/to/evidence/review-1
~~~

只有 numeric/pixel 时不需要 findings。已声明输入或参考改变、复制后的产物缺失/被改动会拒绝 review，需要重新 capture。输出 report.json，保留期望来源和每项结果。

必需项的汇总优先级：failed、needs_reference、needs_review、passed。可选项失败保留在清单，但不改变总体必需项结论。原生执行故障是 capture error，不冒充视觉失败。

退出码：capture 成功 0、执行/产物故障 1、配置或证据问题 2、中断 130；review 通过 0、必需项失败 1、配置/证据问题 2、缺参考/待确认 3。

报告只覆盖已配置的组件状态。原生编译/执行、像素、数值和 AI 视觉判断分别保留其证据边界，页面集成另行复验。

## 包装层验证

在包含本 Skill 的工作区，使用 Python 3 和 scripts/requirements.txt 中的依赖：

~~~bash
python3 -B -m unittest discover -s native-ui-agent/tests -v
~~~

这些测试使用合成图片和测试渲染器，验证执行/证据/判定协议，不证明 Xcode、Paparazzi 或 Compose Preview 的实际工程接入。接入原生工程后，另行运行真实组件和页面场景。
