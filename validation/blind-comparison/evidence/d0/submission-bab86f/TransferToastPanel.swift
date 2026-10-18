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

private func safeTransferFraction(_ value: Double) -> Double {
    value.isFinite ? min(1, max(0, value)) : 0
}

private func transferPercentage(_ value: Double) -> String {
    "\(Int(floor(value * 100 + 0.5)))%"
}

private struct TransferColors {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let rgb = dark ? darkValue : light
        return Color(.sRGB, red: Double((rgb >> 16) & 255) / 255,
                     green: Double((rgb >> 8) & 255) / 255, blue: Double(rgb & 255) / 255, opacity: 1)
    }
    var panel: Color { color(0xFFFFFF, 0x182235) }
    var border: Color { color(0xD7DFEB, 0x34445F) }
    var primary: Color { color(0x17243B, 0xF2F5FB) }
    var secondary: Color { color(0x526279, 0xB9C5D9) }
    var surface: Color { color(0xF1F4F9, 0x24324A) }
    var track: Color { color(0xE2E8F2, 0x34445F) }
    var accent: Color { color(0x275DD8, 0x9DBDFF) }
    var error: Color { color(0xB3313B, 0xFFADB3) }
    var success: Color { color(0x13795B, 0x7CDDBB) }
}

private struct TransferWidthPreference: PreferenceKey {
    static var defaultValue: CGFloat = 358
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) { value = nextValue() }
}

public struct TransferToastPanel: View {
    private let items: [TransferToastItem]
    private let expanded: Bool
    private let onToggle: () -> Void
    private let onRetry: (String) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.sizeCategory) private var sizeCategory
    @State private var panelWidth: CGFloat = 358
    @ScaledMetric(relativeTo: .body) private var titleSize: CGFloat = 20
    @ScaledMetric(relativeTo: .body) private var nameSize: CGFloat = 16
    @ScaledMetric(relativeTo: .body) private var labelSize: CGFloat = 14
    @ScaledMetric(relativeTo: .body) private var detailSize: CGFloat = 13
    @ScaledMetric(relativeTo: .body) private var captionSize: CGFloat = 12

    public init(items: [TransferToastItem], expanded: Bool,
                onToggle: @escaping () -> Void, onRetry: @escaping (String) -> Void) {
        self.items = items
        self.expanded = expanded
        self.onToggle = onToggle
        self.onRetry = onRetry
    }

    private var colors: TransferColors { TransferColors(dark: colorScheme == .dark) }
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
    private var summaryTone: Color {
        if items.isEmpty { return colors.secondary }
        if failed > 0 { return colors.error }
        if running > 0 { return colors.accent }
        if queued > 0 { return colors.secondary }
        return colors.success
    }
    private var aggregate: Double {
        guard !items.isEmpty else { return 0 }
        return items.reduce(0) { result, item in
            result + (item.status == "done" ? 1 : item.status == "queued" ? 0 : safeTransferFraction(item.progress))
        } / Double(items.count)
    }
    private var visibleItems: [TransferToastItem] {
        items.count > 2 && !expanded ? Array(items.prefix(2)) : items
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
            summaryView.padding(.top, 4)
            if items.isEmpty {
                Text("Add an attachment to get started.")
                    .font(.system(size: detailSize)).foregroundColor(colors.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("transfer.empty")
                    .padding(.top, 12)
            } else {
                aggregateView.padding(.top, 12)
                VStack(spacing: 0) {
                    ForEach(Array(visibleItems.enumerated()), id: \.element.id) { index, item in
                        fileRow(item)
                        if index < visibleItems.count - 1 {
                            colors.track.frame(height: 1).accessibilityHidden(true)
                        }
                    }
                }
                .accessibilityElement(children: .contain)
                .accessibilityIdentifier("transfer.list")
                .padding(.top, 16)
                if items.count > 2 && !expanded {
                    Text(items.count == 3 ? "+1 more attachment" : "+\(items.count - 2) more attachments")
                        .font(.system(size: captionSize)).foregroundColor(colors.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("transfer.more")
                        .padding(.top, 8)
                }
            }
        }
        .padding(16)
        .frame(maxWidth: 560, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 20).fill(colors.panel))
        .overlay(RoundedRectangle(cornerRadius: 20).strokeBorder(colors.border, lineWidth: 1))
        .background(GeometryReader { geometry in
            Color.clear.preference(key: TransferWidthPreference.self, value: geometry.size.width)
        })
        .onPreferenceChange(TransferWidthPreference.self) { panelWidth = $0 }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("transfer.panel")
        .frame(maxWidth: .infinity, alignment: .center)
        .fixedSize(horizontal: false, vertical: true)
    }

    private var title: some View {
        Text("Attachment transfers")
            .font(.system(size: titleSize, weight: .semibold)).foregroundColor(colors.primary)
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityIdentifier("transfer.title")
    }

    @ViewBuilder private var header: some View {
        if compact {
            VStack(alignment: .leading, spacing: 0) {
                title
                if items.count > 2 { toggle }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        } else {
            HStack(alignment: .center, spacing: 8) {
                title.frame(maxWidth: .infinity, alignment: .leading)
                if items.count > 2 { toggle }
            }
            .frame(minHeight: 48)
        }
    }

    private var toggle: some View {
        Button(action: onToggle) {
            HStack(spacing: 6) {
                Text(expanded ? "Show less" : "Show all")
                    .font(.system(size: labelSize, weight: .semibold))
                    .fixedSize(horizontal: false, vertical: true)
                Image(systemName: expanded ? "chevron.up" : "chevron.down")
                    .font(.system(size: 12, weight: .semibold)).accessibilityHidden(true)
            }
            .foregroundColor(colors.accent)
            .frame(minWidth: 48, minHeight: 48, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(PlainButtonStyle())
        .accessibilityLabel(Text(expanded ? "Show fewer attachments" : "Show all attachments"))
        .accessibilityValue(Text(expanded ? "Expanded" : "Collapsed"))
        .accessibilityIdentifier("transfer.toggle")
    }

    private var summaryView: some View {
        HStack(alignment: .center, spacing: 8) {
            Circle().fill(summaryTone).frame(width: 8, height: 8).accessibilityHidden(true)
            Text(summary).font(.system(size: labelSize, weight: .semibold)).foregroundColor(summaryTone)
                .fixedSize(horizontal: false, vertical: true).accessibilityIdentifier("transfer.summary")
        }
    }

    private var countText: String { "\(done) of \(items.count) complete" }
    private var percentText: String { transferPercentage(aggregate) }
    private var countsFit: Bool {
        textWidth(countText, size: detailSize, semibold: false)
            + textWidth(percentText, size: detailSize, semibold: true) + 8 <= panelWidth - 32
    }

    private var count: some View {
        Text(countText).font(.system(size: detailSize)).foregroundColor(colors.secondary)
            .fixedSize(horizontal: false, vertical: true).accessibilityIdentifier("transfer.count")
    }
    private var percentage: some View {
        Text(percentText).font(.system(size: detailSize, weight: .semibold)).foregroundColor(colors.primary)
            .fixedSize(horizontal: false, vertical: true).accessibilityIdentifier("transfer.percent")
    }

    private var aggregateView: some View {
        VStack(alignment: .leading, spacing: 6) {
            if countsFit {
                HStack(alignment: .top, spacing: 8) { count; Spacer(minLength: 0); percentage }
            } else {
                VStack(alignment: .leading, spacing: 4) {
                    count
                    percentage.frame(maxWidth: .infinity, alignment: .trailing)
                }
            }
            progressBar(aggregate, tone: summaryTone, height: 6,
                        label: "Overall transfer progress", identifier: "transfer.progress")
        }
    }

    private func tone(_ item: TransferToastItem) -> Color {
        switch item.status {
        case "done": return colors.success
        case "running": return colors.accent
        case "failed": return colors.error
        default: return colors.secondary
        }
    }

    private func status(_ item: TransferToastItem) -> String {
        switch item.status {
        case "done": return "Complete"
        case "running": return "\(transferPercentage(safeTransferFraction(item.progress))) sent"
        case "failed": return "Failed · retry available"
        default: return "Waiting"
        }
    }

    private func fileRow(_ item: TransferToastItem) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "doc.text")
                .font(.system(size: 22, weight: .regular)).foregroundColor(tone(item))
                .frame(width: 32, height: 32)
                .background(RoundedRectangle(cornerRadius: 8).fill(colors.surface))
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 0) {
                Text(item.name).font(.system(size: nameSize, weight: .medium)).foregroundColor(colors.primary)
                    .lineLimit(sizeCategory.isAccessibilityCategory ? 3 : 2).truncationMode(.tail)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityLabel(Text(item.name)).accessibilityIdentifier("transfer.name.\(item.id)")
                Text(status(item)).font(.system(size: detailSize)).foregroundColor(tone(item))
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("transfer.status.\(item.id)").padding(.top, 4)
                if item.status == "running" {
                    progressBar(safeTransferFraction(item.progress), tone: tone(item), height: 4,
                                label: "\(item.name) transfer progress", identifier: "transfer.progress.\(item.id)")
                        .padding(.top, 8)
                }
                if compact && item.status == "failed" { retry(item).padding(.top, 8) }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .layoutPriority(1)
            if !compact && item.status == "failed" { retry(item) }
        }
        .padding(.vertical, 12)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("transfer.row.\(item.id)")
    }

    private func retry(_ item: TransferToastItem) -> some View {
        Button(action: { onRetry(item.id) }) {
            Text("Retry").font(.system(size: labelSize, weight: .semibold)).foregroundColor(colors.error)
                .multilineTextAlignment(.center).fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 12).padding(.vertical, 8)
                .frame(minWidth: 72, minHeight: 48)
                .background(RoundedRectangle(cornerRadius: 10).fill(colors.panel))
                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(colors.error, lineWidth: 1))
                .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(PlainButtonStyle())
        .accessibilityLabel(Text("Retry \(item.name)"))
        .accessibilityIdentifier("transfer.retry.\(item.id)")
    }

    private func progressBar(_ value: Double, tone: Color, height: CGFloat,
                             label: String, identifier: String) -> some View {
        ProgressView(value: value, total: 1)
            .progressViewStyle(TransferProgressStyle(tone: tone, track: colors.track, height: height))
            .frame(height: height)
            .accessibilityLabel(Text(label)).accessibilityValue(Text(transferPercentage(value)))
            .accessibilityIdentifier(identifier)
    }

    private func textWidth(_ text: String, size: CGFloat, semibold: Bool) -> CGFloat {
        #if canImport(UIKit)
        let font = UIFont.systemFont(ofSize: size, weight: semibold ? .semibold : .regular)
        #elseif canImport(AppKit)
        let font = NSFont.systemFont(ofSize: size, weight: semibold ? .semibold : .regular)
        #endif
        return (text as NSString).size(withAttributes: [.font: font]).width
    }
}

private struct TransferProgressStyle: ProgressViewStyle {
    let tone: Color
    let track: Color
    let height: CGFloat
    func makeBody(configuration: Configuration) -> some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                Capsule().fill(track)
                Capsule().fill(tone).frame(width: geometry.size.width * CGFloat(configuration.fractionCompleted ?? 0))
            }
        }
        .frame(height: height)
    }
}
