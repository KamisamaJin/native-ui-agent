# 覆盖与运行时观测

## 先区分三类结论

1. 原生执行/测量：真实节点、同一坐标系边界、文字布局结果、实际事件及状态变化。
2. 静态审查：API、名义样式、控制状态和旧系统回退声明。不能通过运行时交互。
3. 看图：本轮图片上的可见表现与独立预期。OCR 是字形框，不是布局 frame 或字号。

先用无业务复杂度的探针校验适配器：已知可观测按钮、确定的状态更新、超高内容和末尾目标。记录实际系统外观、字号类别、方向、视口、测试数、节点与事件。若探针失效，修正适配器后在同一配置重试；不把能力故障扣为产品缺陷，也不把失败探针改成通过基准。

## 需求账本

从本次已确认需求生成计划；`cases`是本次实际会执行的场景，`aspects`拆分可独立缺证据的方面。下例仅演示格式，不是通用测试清单：

```json
{
  "version": 1,
  "requirements": [
    {
      "id": "choice-action",
      "description": "选择操作发送一次回调",
      "source": "本次需求文档",
      "cases": ["ordinary", "long-content"],
      "related": ["choice-state"],
      "aspects": [{"id": "callback", "methods": ["native_action"], "runtime": "action"}]
    },
    {
      "id": "choice-state",
      "description": "调用方更新后显示新选择",
      "source": "本次需求文档",
      "cases": ["ordinary", "long-content"],
      "aspects": [{"id": "selected-value", "methods": ["native_ax"], "runtime": "state"}]
    }
  ]
}
```

观察记录是 `{"records":[...]}`，每项精确对应 `requirement`、`case`、`aspect`，含 `status`、`execution`、`method`、`observation`和 `evidence:[{"path":"相对证据根的路径","sha256":"真实SHA256"}]`。

方法为 native_ax、native_bounds、native_text_layout、native_action、native_pixels、source_review、visual。账本声明允许的方法；运行时动作只能使用实际 native_action，来源审查和视觉不能代替它。状态为 passed、failed、needs_review、not_executed、unavailable。缺少记录会留下 needs_review，不会被排除出分母后称为全部通过。

```sh
python3 scripts/coverage.py --plan /path/requirements.json \
  --observations /path/observations.json --root /path/evidence \
  --output /path/new-coverage-report.json
```

退出码0通过、1确认失败、3待评估、2输入/证据错误。产物指纹只证明完整性，不证明测量代码的业务含义或观察声明真实性；原生生产来源、场景与源码指纹仍须核对。

`related`只生成复核队列，不推断关联规则自动失败或获得检出信用。记录问题的实际症状、触发条件、根因假设、已核对的规则。报告根因簇数和规则×场景失败数，避免把同一根因说成多个独立问题。

## 长内容与受控状态

顶部图不能覆盖完整长组件。滚动采样保持真实视口和字体，用重叠内容连接相邻图片，记录实际到达底部、关键目标可见和点击是否成功。上/中/下截图缺一部分时不要从源码或离屏节点推断该部分视觉通过。

动作检查分别保留：操作前节点、实际目标/坐标、动作返回、回调增量、操作后节点和图片。调用方持有状态时，先确认操作只产生允许的回调，再由宿主明确更新输入；记录同进程/同 App 的前后状态。单独重启一个新 fixture 不能证明已有组件响应运行时更新。

## iOS实际 App路径

`scripts/ios_observe.py`与 `assets/ios-observer/`提供可接入真实 SwiftUI组件的 App/XCUITest 薄宿主。桥接代码负责输入解码和调用生产 View，禁止重画近似组件。环境、host-only receipt/update 控件与业务区域分开记录。先执行附带通用 probe 再用于产品判断，具体 CLI/输出格式以该适配器说明为准。

XCUI 元素 frame 是辅助功能边界，可能合并子节点；不等于内部 padding、字形边界或有效字体。实际 App AX 成功也不能推出单测宿主 AX 同样可用。精确样式继续使用已验证的 UIKit/文字布局测量或原生像素采样，SwiftUI无法读取的值保持未评估。最低 OS 的可用性声明与真正运行结果分别报告。
