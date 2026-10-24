# OfflineAudioTourPanel public API

Implement a genuine production component, exported by AlertToast on iOS and by the Reply app on Android. The model declarations and component belong in these exact repository-relative production files:

- AlertToast repository: `Sources/AlertToast/OfflineAudioTourPanel.swift` (module `AlertToast`, iOS 14 compatible).
- Reply project (the upstream `Reply/` Gradle root): `app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt` (package `com.example.reply.ui.components`).

The neutral pinned host versions are AlertToast `76a1c1793cd3443001c20c6033beb84453b25d9f` and Reply `53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79`. These paths identify new production files; no existing source was inspected or copied to design a result.

Swift declarations below specify signatures, stored values, and exported types, not implementations:

```swift
import SwiftUI
public struct AudioTourChapter: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let body: String
    public init(id: String, title: String, body: String)
}
public struct OfflineAudioTour: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let language: String
    public let downloadSizeMB: Int
    public let availableMB: Int
    public let meteredConnection: Bool
    public let chapters: [AudioTourChapter]
    public init(id: String, title: String, language: String, downloadSizeMB: Int,
                availableMB: Int, meteredConnection: Bool, chapters: [AudioTourChapter])
}
public struct OfflineAudioTourPanel: View {
    public init(tour: OfflineAudioTour, onWifiOnlyChange: @escaping (Bool) -> Void,
                onDownload: @escaping (String, Bool) -> Void)
    public var body: some View { get }
}
```

Kotlin declarations (import `androidx.compose.runtime.Composable` and `androidx.compose.ui.Modifier`):

```kotlin
package com.example.reply.ui.components
data class AudioTourChapter(val id: String, val title: String, val body: String)
data class OfflineAudioTour(val id: String, val title: String, val language: String,
    val downloadSizeMB: Int, val availableMB: Int, val meteredConnection: Boolean,
    val chapters: List<AudioTourChapter>)
@Composable
fun OfflineAudioTourPanel(tour: OfflineAudioTour, onWifiOnlyChange: (Boolean) -> Unit,
    onDownload: (String, Boolean) -> Unit, modifier: Modifier = Modifier)
```

The callbacks are real production callbacks. Bridges only decode supplied caller values and forward callbacks. They own no UI, local state, layout, expected results, or replacement logic. IDs are stable strings, note/chapter IDs unique within a model. The observer calls `ObserverBridge.make(fixture:onEvent:) -> AnyView` or `org.nativeobserver.ObserverBridge.Content(current)` directly; all declared production initializers must therefore be public on Swift.

Semantic identifiers are literal `audio.canvas`, `.surface`, `.inkMark`, `.title`, `.subtitle`, `.status`, `.disclosure`, `.choice`, `.primary`, plus `.section.0.heading` / `.section.0.body` through `.section.7.heading` / `.section.7.body`. Each identifier belongs to exactly one actual native semantic node, not a duplicate proxy. Canvas and surface are noninteractive semantic containers that preserve descendant nodes. The ink mark is an explicitly accessible noninteractive solid rectangle labeled `Ink accent`, with its identifier on the rectangle's semantic allocation. Status is one semantic band with its label on the whole painted allocation. Its text must not create another copy of that identifier.

Use real native Buttons for disclosure, choice, and primary. Choice uses native selected semantics (SwiftUI selected trait; Compose `selected`), and primary uses native disabled semantics. A selected choice is still enabled until a request has been sent. On a request, disable both choice and primary. Disclosure stays enabled. For AX labels, exclude decorative check marks and do not concatenate status into a button label. The primary label fills its 56 pt/dp high rectangular native control allocation, with a matching content shape; the actual control boundary, rather than text glyph frame, is the geometry assertion basis. Do not merge all descendant Buttons into canvas/surface nodes.

All component state is production owned. When model identity changes, reset local disclosure, choice, and requested state synchronously with the rendered replacement, without callbacks. Preserve state across equivalent updates of the same ID. No wrapper `.id(...)` or Compose `key(...)` may be added by the bridge. Changing model ID is the independently fixed replacement stimulus.
