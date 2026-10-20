# 原始图片与修复范围

参考线框表达结构与明确标注，不与原生字体进行跨渲染器像素回归。下面链接来自共同验收逐状态证据的原始 PNG；完整滚动和其他状态仍在各 observation.json。

![独立 P2 参考](design/public/references/P2.png)

| 组/平台，P2 browse 的 Reserve 可见帧 | 首版 | 修复后 |
| --- | --- | --- |
| candidate-v6/ios | ![candidate-v6 ios D0](common-corpora/source-a/d0/ios/P2/attachments/A67621DB-79C9-42BD-B505-B56608C2BD3F.png) | ![candidate-v6 ios FINAL](common-corpora/source-a/final/ios/P2/attachments/EC59B25B-5EEE-40F2-9A17-7F2BDE7403C6.png) |
| candidate-v6/android | ![candidate-v6 android D0](common-corpora/source-a/d0/android/P2/013-state_browse_6.png) | ![candidate-v6 android FINAL](common-corpora/source-a/final/android/P2/013-state_browse_6.png) |
| baseline-v5/ios | ![baseline-v5 ios D0](common-corpora/source-b/d0/ios/P2/attachments/D358FE98-06AE-4AD4-8271-3D6F0797094E.png) | ![baseline-v5 ios FINAL](common-corpora/source-b/final/ios/P2/attachments/E6CBFC8E-6C2F-43C8-9F47-F47EA4361A69.png) |
| baseline-v5/android | ![baseline-v5 android D0](common-corpora/source-b/d0/android/P2/013-state_browse_6.png) | ![baseline-v5 android FINAL](common-corpora/source-b/final/android/P2/013-state_browse_6.png) |

两组 iOS 修改了显式按钮样式以回应自身原始的禁用文本可读性疑虑；它属于未定量、未确认的质性问题，不能计为已验证 F→P。新版还把 Android Reserve 最小高度改为49dp；原始48dp设计下的数值边界 F 保留，不因此声称修复了用户可见产品缺陷。

截图不证明 iOS 计算字号、颜色、框架 padding 或物理点击区域。局部可见目标不代表全页内容已完整检查。
