from pathlib import Path
p=Path('alerttoast/Sources/AlertToast/TransferToastPanel.swift')
s=p.read_text().replace('@Environment(\\.sizeCategory) private var sizeCategory','@Environment(\\.sizeCategory) private var sizeCategory\n    @Environment(\\.layoutDirection) private var layoutDirection')
s=s.replace('''        if compact {
            VStack(alignment: .leading, spacing: 0) {
                title.frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)''','''        if #available(iOS 16.0, macOS 13.0, *) {
            TransferHeaderLayout(forceCompact: sizeCategory.isAccessibilityCategory,
                                 rtl: layoutDirection == .rightToLeft) {
                title
                if items.count > 2 { toggle }
            }
        } else if compact {
            VStack(alignment: .leading, spacing: 0) {
                title.frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)''',1)
s=s.replace('''        if textWidth(countLabel) + textWidth(transferPercentage(aggregate), bold: true) + 12 <= panelWidth - 32 {''','''        if #available(iOS 16.0, macOS 13.0, *) {
            TransferCountLayout(rtl: layoutDirection == .rightToLeft) {
                countText
                percentageText
            }
        } else if textWidth(countLabel) + textWidth(transferPercentage(aggregate), bold: true) + 12 <= panelWidth - 32 {''',1)
start=s.index('    private func fileRow(_ item: TransferToastItem) -> some View {')
end=s.index('    private func retry(_ item: TransferToastItem) -> some View {',start)
s=s[:start]+'''    private func document(_ item: TransferToastItem) -> some View {
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
                .accessibilityIdentifier("transfer.name.\\(item.id)")
            Text(fileStatus(item))
                .modifier(TransferTextStyle(13, .regular, fileTone(item)))
                .fixedSize(horizontal: false, vertical: true)
                .padding(.top, 4)
                .accessibilityIdentifier("transfer.status.\\(item.id)")
            if item.status == "running" {
                progress(transferSafeProgress(item.progress), color: fileTone(item), height: 4,
                         label: "\\(item.name) transfer progress", identifier: "transfer.progress.\\(item.id)")
                    .padding(.top, 8)
            }
        }.frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder private func fileRowContents(_ item: TransferToastItem) -> some View {
        if #available(iOS 16.0, macOS 13.0, *) {
            TransferFileLayout(forceCompact: sizeCategory.isAccessibilityCategory,
                               rtl: layoutDirection == .rightToLeft) {
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
            .accessibilityIdentifier("transfer.row.\\(item.id)")
    }

'''+s[end:]
s+='''

// These layouts use the offered inner width (panel width minus its two insets).
// All positions are logical, then mapped to the environment's reading direction.
@available(iOS 16.0, macOS 13.0, *)
private struct TransferHeaderLayout: Layout {
    let forceCompact: Bool
    let rtl: Bool

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
            subviews[index].place(at: CGPoint(x: bounds.minX + (rtl ? width - x - size.width : x), y: bounds.minY + y),
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
    let rtl: Bool

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
            subviews[index].place(at: CGPoint(x: bounds.minX + (rtl ? width - x - size.width : x), y: bounds.minY + y),
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
    let rtl: Bool
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
        subviews[0].place(at: CGPoint(x: bounds.minX + (rtl ? width - s[0].width : 0), y: bounds.minY),
                          anchor: UnitPoint(x: 0, y: 0), proposal: ProposedViewSize(s[0]))
        subviews[1].place(at: CGPoint(x: bounds.minX + (rtl ? 0 : width - s[1].width), y: bounds.minY + (inline ? 0 : s[0].height + 4)),
                          anchor: UnitPoint(x: 0, y: 0), proposal: ProposedViewSize(s[1]))
    }
}
'''
p.write_text(s)
