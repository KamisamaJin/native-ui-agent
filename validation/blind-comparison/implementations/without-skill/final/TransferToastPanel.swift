import SwiftUI
#if canImport(UIKit)
import UIKit
#elseif canImport(AppKit)
import AppKit
#endif

public struct TransferToastItem {
    public let id: String
    public let name: String
    public let status: String
    public let progress: Double

    public init(id: String, name: String, status: String, progress: Double) {
        self.id = id
        self.name = name
        self.status = status
        self.progress = progress
    }
}

private struct TransferPanelPalette {
    let panel: Color
    let border: Color
    let primary: Color
    let neutral: Color
    let surface: Color
    let track: Color
    let accent: Color
    let error: Color
    let success: Color

    init(dark: Bool) {
        panel = Color(transferHex: dark ? 0x182235 : 0xFFFFFF)
        border = Color(transferHex: dark ? 0x34445F : 0xD7DFEB)
        primary = Color(transferHex: dark ? 0xF2F5FB : 0x17243B)
        neutral = Color(transferHex: dark ? 0xB9C5D9 : 0x526279)
        surface = Color(transferHex: dark ? 0x24324A : 0xF1F4F9)
        track = Color(transferHex: dark ? 0x34445F : 0xE2E8F2)
        accent = Color(transferHex: dark ? 0x9DBDFF : 0x275DD8)
        error = Color(transferHex: dark ? 0xFFADB3 : 0xB3313B)
        success = Color(transferHex: dark ? 0x7CDDBB : 0x13795B)
    }
}

private extension Color {
    init(transferHex value: UInt) {
        self.init(.sRGB, red: Double((value >> 16) & 255) / 255,
                  green: Double((value >> 8) & 255) / 255,
                  blue: Double(value & 255) / 255, opacity: 1)
    }
}

private func transferSafeProgress(_ value: Double) -> Double {
    value.isFinite ? min(1, max(0, value)) : 0
}

private func transferPercentage(_ value: Double) -> String {
    "\(Int(floor(value * 100 + 0.5)))%"
}

private struct TransferPanelWidthKey: PreferenceKey {
    static var defaultValue: CGFloat = 560
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = nextValue()
    }
}

private struct TransferTextStyle: ViewModifier {
    @ScaledMetric(relativeTo: .body) private var size: CGFloat = 14
    let weight: Font.Weight
    let color: Color

    init(_ size: CGFloat, _ weight: Font.Weight, _ color: Color) {
        self._size = ScaledMetric(wrappedValue: size, relativeTo: .body)
        self.weight = weight
        self.color = color
    }

    func body(content: Content) -> some View {
        content.font(.system(size: size, weight: weight)).foregroundColor(color)
    }
}

public struct TransferToastPanel: View {
    private let items: [TransferToastItem]
    private let expanded: Bool
    private let onToggle: () -> Void
    private let onRetry: (String) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.sizeCategory) private var sizeCategory
    @State private var panelWidth: CGFloat = 560
    @ScaledMetric(relativeTo: .body) private var countSize: CGFloat = 13

    public init(
        items: [TransferToastItem],
        expanded: Bool,
        onToggle: @escaping () -> Void,
        onRetry: @escaping (String) -> Void
    ) {
        self.items = items
        self.expanded = expanded
        self.onToggle = onToggle
        self.onRetry = onRetry
    }

    private var palette: TransferPanelPalette { TransferPanelPalette(dark: colorScheme == .dark) }
    private var compact: Bool { panelWidth <= 340 || sizeCategory.isAccessibilityCategory }
    private var failed: Int { items.filter { $0.status == "failed" }.count }
    private var running: Int { items.filter { $0.status == "running" }.count }
    private var queued: Int { items.filter { $0.status == "queued" }.count }
    private var done: Int { items.filter { $0.status == "done" }.count }
    private var summary: String {
        if items.isEmpty { return "No transfers" }
        if failed == 1 { return "1 needs retry" }
        if failed > 1 { return "\(failed) need retry" }
        if running > 0 { return "\(running) transferring" }
        if queued > 0 { return "\(queued) waiting" }
        return "All transfers complete"
    }
    private var tone: Color {
        if items.isEmpty { return palette.neutral }
        if failed > 0 { return palette.error }
        if running > 0 { return palette.accent }
        if queued > 0 { return palette.neutral }
        return palette.success
    }
    private var aggregate: Double {
        guard !items.isEmpty else { return 0 }
        return items.reduce(0.0) { total, item in
            total + (item.status == "done" ? 1 : item.status == "queued" ? 0 : transferSafeProgress(item.progress))
        } / Double(items.count)
    }
    private var visibleItems: [TransferToastItem] {
        items.count > 2 && !expanded ? Array(items.prefix(2)) : items
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
            HStack(alignment: .center, spacing: 8) {
                Circle().fill(tone).frame(width: 8, height: 8).accessibilityHidden(true)
                Text(summary)
                    .modifier(TransferTextStyle(14, .semibold, tone))
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("transfer.summary")
            }
            .padding(.top, 4)
            if items.isEmpty {
                Text("Add an attachment to get started.")
                    .modifier(TransferTextStyle(13, .regular, palette.neutral))
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(.top, 12)
                    .accessibilityIdentifier("transfer.empty")
            } else {
                countRow.padding(.top, 12)
                progress(aggregate, color: tone, height: 6,
                         label: "Overall transfer progress", identifier: "transfer.progress")
                    .padding(.top, 6)
                VStack(spacing: 0) {
                    ForEach(Array(visibleItems.enumerated()), id: \.element.id) { index, item in
                        fileRow(item)
                        if index < visibleItems.count - 1 {
                            Rectangle().fill(palette.track).frame(height: 1).accessibilityHidden(true)
                        }
                    }
                }
                .padding(.top, 16)
                .accessibilityElement(children: .contain)
                .accessibilityIdentifier("transfer.list")
                if items.count > 2 && !expanded {
                    let extra = items.count - 2
                    Text("+\(extra) more \(extra == 1 ? "attachment" : "attachments")")
                        .modifier(TransferTextStyle(12, .regular, palette.neutral))
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.top, 8)
                        .accessibilityIdentifier("transfer.more")
                }
            }
        }
        .padding(16)
        .frame(maxWidth: 560, alignment: .leading)
        .background(palette.panel)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .overlay(RoundedRectangle(cornerRadius: 20).strokeBorder(palette.border, lineWidth: 1))
        .background(GeometryReader { geometry in
            Color.clear.preference(key: TransferPanelWidthKey.self, value: geometry.size.width)
        })
        .onPreferenceChange(TransferPanelWidthKey.self) { panelWidth = $0 }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("transfer.panel")
        .frame(maxWidth: .infinity, alignment: .top)
    }

    private var title: some View {
        Text("Attachment transfers")
            .modifier(TransferTextStyle(20, .semibold, palette.primary))
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityIdentifier("transfer.title")
    }

    @ViewBuilder private var header: some View {
        if #available(iOS 16.0, macOS 13.0, *) {
            TransferHeaderLayout(forceCompact: sizeCategory.isAccessibilityCategory) {
                title
                if items.count > 2 { toggle }
            }
        } else if compact {
            VStack(alignment: .leading, spacing: 0) {
                title.frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
                if items.count > 2 { toggle }
            }
        } else {
            HStack(alignment: .center, spacing: 8) {
                title.frame(maxWidth: .infinity, alignment: .leading)
                if items.count > 2 { toggle }
            }.frame(minHeight: 48)
        }
    }

    private var toggle: some View {
        Button(action: onToggle) {
            HStack(spacing: 8) {
                Text(expanded ? "Show less" : "Show all")
                    .modifier(TransferTextStyle(14, .semibold, palette.accent))
                    .fixedSize(horizontal: false, vertical: true)
                TransferChevron(up: expanded)
                    .stroke(palette.accent, style: StrokeStyle(lineWidth: 1.6, lineCap: .round, lineJoin: .round))
                    .frame(width: 12, height: 12)
                    .accessibilityHidden(true)
            }
            .frame(minWidth: 48, minHeight: 48, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(PlainButtonStyle())
        .accessibilityLabel(expanded ? "Show fewer attachments" : "Show all attachments")
        .accessibilityValue(expanded ? "Expanded" : "Collapsed")
        .accessibilityIdentifier("transfer.toggle")
    }

    private var countLabel: String { "\(done) of \(items.count) complete" }

    private func textWidth(_ text: String, bold: Bool = false) -> CGFloat {
        #if canImport(UIKit)
        let font = UIFont.systemFont(ofSize: countSize, weight: bold ? .semibold : .regular)
        #elseif canImport(AppKit)
        let font = NSFont.systemFont(ofSize: countSize, weight: bold ? .semibold : .regular)
        #endif
        return (text as NSString).size(withAttributes: [.font: font]).width
    }

    private var countText: some View {
        Text(countLabel).modifier(TransferTextStyle(13, .regular, palette.neutral))
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityIdentifier("transfer.count")
    }
    private var percentageText: some View {
        Text(transferPercentage(aggregate)).modifier(TransferTextStyle(13, .semibold, palette.primary))
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityIdentifier("transfer.percent")
    }
    @ViewBuilder private var countRow: some View {
        if #available(iOS 16.0, macOS 13.0, *) {
            TransferCountLayout() {
                countText
                percentageText
            }
        } else if textWidth(countLabel) + textWidth(transferPercentage(aggregate), bold: true) + 12 <= panelWidth - 32 {
            HStack(alignment: .top, spacing: 12) {
                countText
                Spacer(minLength: 0)
                percentageText
            }
        } else {
            VStack(alignment: .leading, spacing: 4) {
                countText
                percentageText.frame(maxWidth: .infinity, alignment: .trailing)
            }
        }
    }

    private func fileTone(_ item: TransferToastItem) -> Color {
        switch item.status {
        case "running": return palette.accent
        case "failed": return palette.error
        case "done": return palette.success
        default: return palette.neutral
        }
    }
    private func fileStatus(_ item: TransferToastItem) -> String {
        switch item.status {
        case "running": return "\(transferPercentage(transferSafeProgress(item.progress))) sent"
        case "failed": return "Failed · retry available"
        case "done": return "Complete"
        default: return "Waiting"
        }
    }

    private func document(_ item: TransferToastItem) -> some View {
        ZStack {
            RoundedRectangle(cornerRadius: 8).fill(palette.surface)
            TransferDocument()
                .stroke(fileTone(item), style: StrokeStyle(lineWidth: 1.5, lineJoin: .round))
                .frame(width: 22, height: 24)
        }
        .frame(width: 32, height: 32)
        .accessibilityHidden(true)
    }

    private func fileText(_ item: TransferToastItem) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(item.name)
                .modifier(TransferTextStyle(16, .medium, palette.primary))
                .lineLimit(sizeCategory.isAccessibilityCategory ? 3 : 2)
                .truncationMode(.tail)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityLabel(item.name)
                .accessibilityIdentifier("transfer.name.\(item.id)")
            Text(fileStatus(item))
                .modifier(TransferTextStyle(13, .regular, fileTone(item)))
                .fixedSize(horizontal: false, vertical: true)
                .padding(.top, 4)
                .accessibilityIdentifier("transfer.status.\(item.id)")
            if item.status == "running" {
                progress(transferSafeProgress(item.progress), color: fileTone(item), height: 4,
                         label: "\(item.name) transfer progress", identifier: "transfer.progress.\(item.id)")
                    .padding(.top, 8)
            }
        }.frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder private func fileRowContents(_ item: TransferToastItem) -> some View {
        if #available(iOS 16.0, macOS 13.0, *) {
            TransferFileLayout(forceCompact: sizeCategory.isAccessibilityCategory) {
                document(item)
                fileText(item)
                if item.status == "failed" { retry(item) }
            }
        } else {
            HStack(alignment: .top, spacing: 12) {
                document(item)
                VStack(alignment: .leading, spacing: 0) {
                    fileText(item)
                    if compact && item.status == "failed" { retry(item).padding(.top, 8) }
                }.frame(maxWidth: .infinity, alignment: .leading)
                if !compact && item.status == "failed" { retry(item) }
            }
        }
    }

    private func fileRow(_ item: TransferToastItem) -> some View {
        fileRowContents(item)
            .padding(.vertical, 12)
            .accessibilityElement(children: .contain)
            .accessibilityIdentifier("transfer.row.\(item.id)")
    }

    private func retry(_ item: TransferToastItem) -> some View {
        Button(action: { onRetry(item.id) }) {
            Text("Retry")
                .modifier(TransferTextStyle(14, .semibold, palette.error))
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .frame(minWidth: 72, minHeight: 48)
                .background(palette.panel)
                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(palette.error, lineWidth: 1))
                .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(PlainButtonStyle())
        .accessibilityLabel("Retry \(item.name)")
        .accessibilityIdentifier("transfer.retry.\(item.id)")
    }

    private func progress(_ value: Double, color: Color, height: CGFloat,
                          label: String, identifier: String) -> some View {
        ProgressView(value: value, total: 1)
            .progressViewStyle(TransferTrackStyle(fill: color, track: palette.track, height: height))
            .accessibilityLabel(label)
            .accessibilityValue(transferPercentage(value))
            .accessibilityIdentifier(identifier)
    }
}

private struct TransferTrackStyle: ProgressViewStyle {
    let fill: Color
    let track: Color
    let height: CGFloat
    func makeBody(configuration: Configuration) -> some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                Capsule().fill(track)
                Capsule().fill(fill)
                    .frame(width: geometry.size.width * CGFloat(configuration.fractionCompleted ?? 0))
            }
        }.frame(height: height)
    }
}

private struct TransferChevron: Shape {
    let up: Bool
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.width * 0.15, y: rect.height * (up ? 0.65 : 0.35)))
        path.addLine(to: CGPoint(x: rect.width * 0.5, y: rect.height * (up ? 0.3 : 0.7)))
        path.addLine(to: CGPoint(x: rect.width * 0.85, y: rect.height * (up ? 0.65 : 0.35)))
        return path
    }
}

private struct TransferDocument: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        func point(_ x: CGFloat, _ y: CGFloat) -> CGPoint { CGPoint(x: rect.width * x, y: rect.height * y) }
        path.move(to: point(0.2, 0.08))
        path.addLine(to: point(0.61, 0.08))
        path.addLine(to: point(0.84, 0.3))
        path.addLine(to: point(0.84, 0.94))
        path.addLine(to: point(0.2, 0.94))
        path.closeSubpath()
        path.move(to: point(0.61, 0.08))
        path.addLine(to: point(0.61, 0.3))
        path.addLine(to: point(0.84, 0.3))
        path.move(to: point(0.33, 0.52))
        path.addLine(to: point(0.7, 0.52))
        path.move(to: point(0.33, 0.72))
        path.addLine(to: point(0.67, 0.72))
        return path
    }
}


// These layouts use the offered inner width (panel width minus its two insets).
// SwiftUI maps these logical layout coordinates to the native reading direction.
@available(iOS 16.0, macOS 13.0, *)
private struct TransferHeaderLayout: Layout {
    let forceCompact: Bool

    private func sizes(_ width: CGFloat, _ subviews: Subviews) -> [CGSize] {
        let stacked = forceCompact || width <= 308
        let toggle = subviews.count > 1 ? subviews[1].sizeThatFits(ProposedViewSize(width: width, height: nil)) : .zero
        let titleWidth = stacked || subviews.count == 1 ? width : max(0, width - toggle.width - 8)
        let title = subviews[0].sizeThatFits(ProposedViewSize(width: titleWidth, height: nil))
        return [title, toggle]
    }
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? 528
        let s = sizes(width, subviews)
        let height = forceCompact || width <= 308 ? max(48, s[0].height) + s[1].height : max(48, max(s[0].height, s[1].height))
        return CGSize(width: width, height: height)
    }
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let width = bounds.width
        let s = sizes(width, subviews)
        let stacked = forceCompact || width <= 308
        func place(_ index: Int, _ x: CGFloat, _ y: CGFloat, _ size: CGSize) {
            subviews[index].place(at: CGPoint(x: bounds.minX + x, y: bounds.minY + y),
                                  anchor: UnitPoint(x: 0, y: 0), proposal: ProposedViewSize(size))
        }
        place(0, 0, (stacked ? max(48, s[0].height) : bounds.height) / 2 - s[0].height / 2, s[0])
        if subviews.count > 1 {
            place(1, stacked ? 0 : width - s[1].width,
                  stacked ? max(48, s[0].height) : (bounds.height - s[1].height) / 2, s[1])
        }
    }
}

@available(iOS 16.0, macOS 13.0, *)
private struct TransferFileLayout: Layout {
    let forceCompact: Bool

    private func sizes(_ width: CGFloat, _ subviews: Subviews) -> [CGSize] {
        let compact = forceCompact || width <= 308
        let retry = subviews.count > 2 ? subviews[2].sizeThatFits(ProposedViewSize(width: max(0, width - 44), height: nil)) : .zero
        let textWidth = max(0, width - 44 - (compact || subviews.count < 3 ? 0 : retry.width + 12))
        let text = subviews[1].sizeThatFits(ProposedViewSize(width: textWidth, height: nil))
        return [CGSize(width: 32, height: 32), text, retry]
    }
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? 528
        let s = sizes(width, subviews)
        let compact = forceCompact || width <= 308
        let height = compact ? max(32, s[1].height + (subviews.count > 2 ? 8 + s[2].height : 0)) : max(32, max(s[1].height, s[2].height))
        return CGSize(width: width, height: height)
    }
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let width = bounds.width
        let s = sizes(width, subviews)
        let compact = forceCompact || width <= 308
        func place(_ index: Int, _ x: CGFloat, _ y: CGFloat, _ size: CGSize) {
            subviews[index].place(at: CGPoint(x: bounds.minX + x, y: bounds.minY + y),
                                  anchor: UnitPoint(x: 0, y: 0), proposal: ProposedViewSize(size))
        }
        place(0, 0, 0, s[0])
        place(1, 44, 0, s[1])
        if subviews.count > 2 {
            place(2, compact ? 44 : width - s[2].width,
                  compact ? s[1].height + 8 : (bounds.height - s[2].height) / 2, s[2])
        }
    }
}

@available(iOS 16.0, macOS 13.0, *)
private struct TransferCountLayout: Layout {
    private func sizes(_ width: CGFloat, _ subviews: Subviews) -> [CGSize] {
        subviews.map { $0.sizeThatFits(ProposedViewSize(width: width, height: nil)) }
    }
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? 528
        let s = sizes(width, subviews)
        let inline = s[0].width + s[1].width + 12 <= width
        return CGSize(width: width, height: inline ? max(s[0].height, s[1].height) : s[0].height + 4 + s[1].height)
    }
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let width = bounds.width
        let s = sizes(width, subviews)
        let inline = s[0].width + s[1].width + 12 <= width
        subviews[0].place(at: CGPoint(x: bounds.minX, y: bounds.minY),
                          anchor: UnitPoint(x: 0, y: 0), proposal: ProposedViewSize(s[0]))
        subviews[1].place(at: CGPoint(x: bounds.minX + width - s[1].width, y: bounds.minY + (inline ? 0 : s[0].height + 4)),
                          anchor: UnitPoint(x: 0, y: 0), proposal: ProposedViewSize(s[1]))
    }
}
