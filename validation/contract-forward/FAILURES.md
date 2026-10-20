# 失败与未评估记录

保留 46 条试验采集命令、12 次非零退出、1599 个快照记录。命令数包含两次原生测试前的输入策略拒绝。

| 语料 | 平台/场景 | 退出 | 命令秒数 | 实际原因 |
| --- | --- | ---: | ---: | --- |
| [own-corpora/unit-092e15/d0](own-corpora/unit-092e15/d0/ios/P2-command.json) | ios/P2 | 2 | 0.066 | Original frontend rejected offered width before native test. |
| [own-corpora/unit-092e15/final](own-corpora/unit-092e15/final/ios/P2-command.json) | ios/P2 | 1 | 122.544 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [own-corpora/unit-e61e3b/d0](own-corpora/unit-e61e3b/d0/ios/P2-command.json) | ios/P2 | 2 | 0.072 | Original frontend rejected offered width before native test. |
| [own-corpora/unit-e61e3b/final](own-corpora/unit-e61e3b/final/ios/P2-command.json) | ios/P2 | 1 | 137.924 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [own-retries/unit-092e15/d0](own-retries/unit-092e15/d0/ios/P2-command.json) | ios/P2 | 1 | 133.055 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [own-retries/unit-e61e3b/d0](own-retries/unit-e61e3b/d0/ios/P2-command.json) | ios/P2 | 1 | 147.961 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [common-corpora/source-a/d0](common-corpora/source-a/d0/ios/P2-command.json) | ios/P2 | 1 | 123.202 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [common-corpora/source-a/final](common-corpora/source-a/final/ios/P2-command.json) | ios/P2 | 1 | 123.290 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [common-corpora/source-b/d0](common-corpora/source-b/d0/ios/P2-command.json) | ios/P2 | 1 | 123.182 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [common-corpora/source-b/final](common-corpora/source-b/final/ios/P2-command.json) | ios/P2 | 1 | 123.293 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [paired-corpora/source-a/v5](paired-corpora/source-a/v5/ios/P2-command.json) | ios/P2 | 1 | 139.591 | XCTAssertTrue failed - native control not enabled or no usable visible point |
| [paired-corpora/source-b/v5](paired-corpora/source-b/v5/ios/P2-command.json) | ios/P2 | 1 | 139.093 | XCTAssertTrue failed - native control not enabled or no usable visible point |

原始两次 iOS P2 width300 拒绝没有观测或截图；共同 frontend 修复后在独立目录重试，原始语料保持不变。其他非零退出有实际原生观测，但 XCUITest 失败和缺目标仍保留，不能把有效数据等同于整例通过。

未完整动作后观察集：0；完整 target/dispatch/binding 见 [JSON](failure-index.json)。缺失目标和禁用刺激后的回调继续计 U。

首次独立 FINAL 报告曾将有源文件/构建绑定的观测误写为采集全部成功；[独立事实更正](evaluation/factual-addenda/FINAL-acquisition.json)保留原文、实际两次 exit1 和证据哈希，不重写已封存评分。

工具 alpha 中 AX/layout 范围误用、独立通用探针的初始选择器拒绝/CLI 参数错误、设计批准前的脚本与控制错误也保留在 development/、independent-generic/ 和 design/private/preapproval-attempt-*；它们发生在业务源代码之前，不作为本轮产品修复成功案例。
