import SwiftUI
import UIKit
import CryptoKit

private func object(_ data: Data?) -> [String: Any] {
    guard let data, let value = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return [:] }
    return value
}
private func json(_ value: Any) -> String {
    guard let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]), let text = String(data: data, encoding: .utf8) else { return "{}" }
    return text
}

@main struct ObserverApp: App {
    var body: some Scene { WindowGroup { ObserverHost() } }
}

private struct ObserverHost: View {
    private let config = object(Data(base64Encoded: ProcessInfo.processInfo.environment["OBSERVER_CONFIG_BASE64"] ?? ""))
    private let instance = UUID().uuidString
    @State private var index = 0
    @State private var events: [[String: Any]] = []
    @State private var viewport = CGRect.zero
    @State private var contentFrame = CGRect.zero
    private var fixtures: [[String: Any]] { [config["initial"] as? [String: Any] ?? [:]] + (config["updates"] as? [[String: Any]] ?? []) }
    private var offeredWidth: CGFloat { CGFloat(config["width"] as? Double ?? 390) }
    private var typeSize: DynamicTypeSize {
        switch config["dynamic_type"] as? String ?? "large" {
        case "xSmall": return .xSmall
        case "small": return .small
        case "medium": return .medium
        case "xLarge": return .xLarge
        case "xxLarge": return .xxLarge
        case "xxxLarge": return .xxxLarge
        case "accessibility1": return .accessibility1
        case "accessibility2": return .accessibility2
        case "accessibility3": return .accessibility3
        case "accessibility4": return .accessibility4
        case "accessibility5": return .accessibility5
        default: return .large
        }
    }
    private var canvas: Color {
        guard let hex = config["canvas_color"] as? String, let value = UInt(hex.dropFirst(), radix: 16) else { return Color(uiColor: .systemBackground) }
        return Color(red: Double((value >> 16) & 255) / 255, green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255)
    }
    private var runtime: [String: Any] {
        ["pid": ProcessInfo.processInfo.processIdentifier, "instance": instance, "fixture_index": index,
              "input_sha256": SHA256.hash(data: Data(json(fixtures[index]).utf8)).map { String(format: "%02x", $0) }.joined(), "event_revision": events.count,
              "content_frame": ["x": contentFrame.minX, "y": contentFrame.minY, "width": contentFrame.width, "height": contentFrame.height],
              "screen_scale": UIScreen.main.scale, "offered_width": offeredWidth, "viewport_height": 600,
              "viewport": ["x": viewport.minX, "y": viewport.minY, "width": viewport.width, "height": viewport.height],
              "theme": config["theme"] as? String ?? "light", "direction": config["direction"] as? String ?? "ltr",
              "dynamic_type": config["dynamic_type"] as? String ?? "large", "canvas_color": config["canvas_color"] as? String ?? "systemBackground"]
    }
    var body: some View {
        VStack(spacing: 8) {
            ScrollView(.vertical) {
                VStack(alignment: .leading, spacing: 0) {
                    ObserverBridge.make(fixture: fixtures[index]) { name in
                        events.append(["event": name, "fixture_index": index, "uptime": ProcessInfo.processInfo.systemUptime])
                    }
                    Text("End of component").font(.caption2).padding(.vertical, 8)
                        .accessibilityIdentifier("__observer.bottom")
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 16).padding(.top, 24)
                .background(GeometryReader { proxy in
                    Color.clear.preference(key: ContentFrameKey.self, value: proxy.frame(in: .global))
                })
            }
            .onPreferenceChange(ContentFrameKey.self) { contentFrame = $0 }
            .frame(width: offeredWidth, height: 600)
            .background(canvas)
            .clipped()
            .background(GeometryReader { proxy in
                Color.clear.onAppear { viewport = proxy.frame(in: .global) }
                    .onChange(of: proxy.frame(in: .global)) { value in viewport = value }
            })
            .accessibilityIdentifier("__observer.scroll")
            VStack(spacing: 2) {
                Button("Apply next fixture") { if index + 1 < fixtures.count { index += 1 } }
                    .font(.system(size: 17))
                    .disabled(index + 1 >= fixtures.count).accessibilityIdentifier("__observer.next")
                Text("Observer callbacks: \(events.count)").font(.system(size: 10))
                    .accessibilityLabel(json(events)).accessibilityIdentifier("__observer.receipt")
                ObserverRuntimeLabel(runtime: runtime)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(canvas.ignoresSafeArea())
        .environment(\.dynamicTypeSize, typeSize)
        .environment(\.layoutDirection, config["direction"] as? String == "rtl" ? .rightToLeft : .leftToRight)
        .preferredColorScheme(config["theme"] as? String == "dark" ? .dark : .light)
    }
}

private struct ObserverRuntimeLabel: View {
    let runtime: [String: Any]
    @Environment(\.colorScheme) private var scheme
    @Environment(\.dynamicTypeSize) private var type
    @Environment(\.layoutDirection) private var direction
    @Environment(\.displayScale) private var scale
    var body: some View {
        let actual: [String: Any] = ["theme": scheme == .dark ? "dark" : "light", "dynamic_type": String(describing: type),
                                   "direction": direction == .rightToLeft ? "rtl" : "ltr", "display_scale": scale]
        Text("Observer runtime").font(.system(size: 10))
            .accessibilityLabel(json(runtime.merging(["actual_environment": actual]) { _, new in new }))
            .accessibilityIdentifier("__observer.runtime")
    }
}

private struct ContentFrameKey: PreferenceKey {
    static var defaultValue: CGRect = .zero
    static func reduce(value: inout CGRect, nextValue: () -> CGRect) { value = nextValue() }
}
