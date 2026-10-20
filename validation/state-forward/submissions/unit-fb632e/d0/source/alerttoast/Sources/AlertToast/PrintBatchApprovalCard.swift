import SwiftUI

public struct PrintBatchJob: Equatable {
    public let id: String
    public let title: String
    public let pages: Int
    public let copies: Int
    public let isColor: Bool
    public let selected: Bool
    public let locked: Bool
    public init(id: String, title: String, pages: Int, copies: Int, isColor: Bool, selected: Bool, locked: Bool) {
        self.id = id; self.title = title; self.pages = pages; self.copies = copies
        self.isColor = isColor; self.selected = selected; self.locked = locked
    }
}
public struct PrintBatchModel: Equatable {
    public let modelID: String
    public let budgetCredits: Int
    public let allowPriority: Bool
    public let initialPaperMode: String
    public let initialPriority: Bool
    public let initialExpanded: Bool
    public let jobs: [PrintBatchJob]
    public init(modelID: String, budgetCredits: Int, allowPriority: Bool, initialPaperMode: String, initialPriority: Bool, initialExpanded: Bool, jobs: [PrintBatchJob]) {
        self.modelID = modelID; self.budgetCredits = budgetCredits; self.allowPriority = allowPriority
        self.initialPaperMode = initialPaperMode; self.initialPriority = initialPriority
        self.initialExpanded = initialExpanded; self.jobs = jobs
    }
}
public struct PrintBatchPresentation {
    public let isDark: Bool
    public let textScale: Double
    public let isRTL: Bool
    public init(isDark: Bool, textScale: Double, isRTL: Bool) {
        self.isDark = isDark; self.textScale = textScale; self.isRTL = isRTL
    }
}

public struct PrintBatchApprovalCard: View {
    private let model: PrintBatchModel
    private let presentation: PrintBatchPresentation
    private let onEvent: (String, [String: Any]) -> Void
    public init(model: PrintBatchModel, presentation: PrintBatchPresentation, onEvent: @escaping (String, [String: Any]) -> Void) {
        self.model = model; self.presentation = presentation; self.onEvent = onEvent
    }
    public var body: some View {
        // The public component retains its position; a new model identity resets all local state together.
        PrintBatchCardContent(model: model, presentation: presentation, onEvent: onEvent)
            .id(model.modelID)
    }
}

private struct BatchPalette {
    let background: Color, surface: Color, text: Color, muted: Color, accent: Color, ready: Color, error: Color, onAccent: Color
    init(dark: Bool) {
        background = Color(hex: dark ? 0x10161F : 0xF5F7FA)
        surface = Color(hex: dark ? 0x1B2532 : 0xFFFFFF)
        text = Color(hex: dark ? 0xF2F5FA : 0x14243A)
        muted = Color(hex: dark ? 0xB7C4D5 : 0x53657A)
        accent = Color(hex: dark ? 0x8BB0FF : 0x265FE4)
        ready = Color(hex: dark ? 0x75D6AA : 0x167650)
        error = Color(hex: dark ? 0xFF9A96 : 0xB63835)
        onAccent = Color(hex: dark ? 0x14243A : 0xFFFFFF)
    }
}
private extension Color {
    init(hex: UInt32) { self.init(.sRGB, red: Double((hex >> 16) & 255) / 255, green: Double((hex >> 8) & 255) / 255, blue: Double(hex & 255) / 255, opacity: 1) }
}
private struct PrintBatchCardContent: View {
    let model: PrintBatchModel
    let presentation: PrintBatchPresentation
    let onEvent: (String, [String: Any]) -> Void
    @State private var selected: Set<String>
    @State private var mode: String
    @State private var priority: Bool
    @State private var expanded: Bool
    init(model: PrintBatchModel, presentation: PrintBatchPresentation, onEvent: @escaping (String, [String: Any]) -> Void) {
        self.model = model; self.presentation = presentation; self.onEvent = onEvent
        _selected = State(initialValue: Set(model.jobs.filter { $0.selected }.map { $0.id }))
        _mode = State(initialValue: model.initialPaperMode)
        _priority = State(initialValue: model.initialPriority)
        _expanded = State(initialValue: model.initialExpanded)
    }
    private var palette: BatchPalette { BatchPalette(dark: presentation.isDark) }
    private var chosen: [PrintBatchJob] { model.jobs.filter { selected.contains($0.id) } }
    private func ink(_ job: PrintBatchJob) -> Int { job.pages * job.copies * (job.isColor ? 3 : 1) }
    private func sheets(_ job: PrintBatchJob) -> Int { (mode == "duplex" ? (job.pages + 1) / 2 : job.pages) * job.copies }
    private var inkCost: Int { chosen.reduce(0) { $0 + ink($1) } }
    private var sheetCount: Int { chosen.reduce(0) { $0 + sheets($1) } }
    private var pageCount: Int { chosen.reduce(0) { $0 + $1.pages * $1.copies } }
    private var surcharge: Int { !chosen.isEmpty && priority ? 6 : 0 }
    private var total: Int { inkCost + sheetCount + surcharge }
    private var over: Bool { total > model.budgetCredits }
    private var canApprove: Bool { !chosen.isEmpty && !over }
    private var status: String { chosen.isEmpty ? "No jobs" : (over ? "Over budget" : "Ready") }
    private var statusColor: Color { chosen.isEmpty ? palette.muted : (over ? palette.error : palette.ready) }
    private var helper: String { !model.allowPriority ? "Priority unavailable for this batch." : (priority ? "Adds 6 cr to this batch." : "Add 6 cr for priority handling.") }
    private var approval: String {
        chosen.isEmpty ? "Select a job to approve" : (over ? "Over budget by \(total - model.budgetCredits) cr" : "Approve \(chosen.count) jobs · \(total) cr")
    }
    private var balance: String {
        chosen.isEmpty ? "No charge selected" : (over ? "Short by \(total - model.budgetCredits) cr" : "Balance after approval: \(model.budgetCredits - total) cr")
    }
    private func font(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        .system(size: size * CGFloat(presentation.textScale), weight: weight, design: .default)
    }
    private func label(_ text: String, _ id: String, size: CGFloat = 14, weight: Font.Weight = .regular, color: Color? = nil) -> some View {
        Text(text).font(font(size, weight)).foregroundColor(color ?? palette.text)
            .fixedSize(horizontal: false, vertical: true).multilineTextAlignment(.leading)
            .accessibilityIdentifier(id)
    }
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 8) {
                label("Print budget check", "printbatch.title", size: 20, weight: .semibold)
                    .frame(maxWidth: .infinity, alignment: .leading)
                label(status, "printbatch.status", size: 12, weight: .semibold, color: statusColor)
                    .padding(.horizontal, 10).padding(.vertical, 5)
                    .background(statusColor.opacity(0.13)).clipShape(RoundedRectangle(cornerRadius: 12))
            }
            VStack(alignment: .leading, spacing: 4) {
                label("Estimated charge", "printbatch.charge.caption", size: 12, color: palette.muted)
                label("\(total) cr", "printbatch.charge.value", size: 28, weight: .bold)
                label("\(chosen.count) jobs • \(pageCount) pages • \(sheetCount) sheets", "printbatch.summary", size: 12, color: palette.muted)
            }
            VStack(spacing: 0) {
                ForEach(Array(model.jobs.enumerated()), id: \.element.id) { index, job in
                    jobRow(job)
                    if index < model.jobs.count - 1 { Rectangle().fill(palette.muted.opacity(0.25)).frame(height: 1) }
                }
            }
            VStack(alignment: .leading, spacing: 8) {
                label("Paper mode", "printbatch.mode.title", weight: .semibold)
                HStack(spacing: 8) {
                    modeButton("single", title: "Single-sided")
                    modeButton("duplex", title: "Duplex")
                }
            }
            VStack(alignment: .leading, spacing: 4) {
                Toggle(isOn: Binding(get: { priority }, set: { next in
                    priority = next; onEvent("priorityChanged", ["priority": next])
                })) {
                    Text("Priority handling").font(font(14, .semibold))
                        .foregroundColor(model.allowPriority && !chosen.isEmpty ? palette.text : palette.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .toggleStyle(SwitchToggleStyle(tint: palette.accent))
                .frame(minHeight: 48)
                .disabled(!model.allowPriority || chosen.isEmpty)
                .accessibilityIdentifier("printbatch.priority")
                label(helper, "printbatch.priority.helper", size: 12, color: palette.muted)
            }
            Button(action: {
                expanded.toggle(); onEvent("breakdownChanged", ["expanded": expanded])
            }) {
                Text(expanded ? "Hide cost breakdown" : "Show cost breakdown")
                    .font(font(14, .semibold)).foregroundColor(palette.accent)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
                    .contentShape(Rectangle())
            }.buttonStyle(PlainButtonStyle())
                .accessibilityIdentifier("printbatch.breakdown.toggle")
                .accessibilityValue(expanded ? "Expanded" : "Collapsed")
            if expanded {
                VStack(spacing: 12) {
                    costRow("ink", "Ink", inkCost)
                    costRow("paper", "Paper", sheetCount)
                    costRow("priority", "Priority", surcharge)
                    costRow("total", "Total", total)
                }
            }
            label(balance, "printbatch.balance", weight: .semibold, color: over && !chosen.isEmpty ? palette.error : palette.text)
            Button(action: {
                onEvent("approve", ["modelID": model.modelID, "jobIDs": chosen.map { $0.id }, "paperMode": mode, "priority": priority, "totalCredits": total, "printedPages": pageCount, "sheets": sheetCount])
            }) {
                Text(approval).font(font(14, .semibold))
                    .foregroundColor(canApprove ? palette.onAccent : palette.muted)
                    .fixedSize(horizontal: false, vertical: true)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 12).padding(.vertical, 12)
                    .frame(maxWidth: .infinity, minHeight: 48)
                    .background(canApprove ? palette.accent : palette.muted.opacity(0.12))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                    .contentShape(RoundedRectangle(cornerRadius: 10))
            }.buttonStyle(PlainButtonStyle()).disabled(!canApprove)
                .accessibilityIdentifier("printbatch.approve")
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.surface).clipShape(RoundedRectangle(cornerRadius: 16))
        .environment(\.layoutDirection, presentation.isRTL ? .rightToLeft : .leftToRight)
        .accessibilityElement(children: .contain).accessibilityIdentifier("printbatch.card")
    }
    private func jobRow(_ job: PrintBatchJob) -> some View {
        let checked = selected.contains(job.id)
        return HStack(alignment: .center, spacing: 8) {
            Button(action: {
                if checked { selected.remove(job.id) } else { selected.insert(job.id) }
                onEvent("selectionChanged", ["jobIDs": model.jobs.filter { selected.contains($0.id) }.map { $0.id }])
            }) {
                ZStack {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(checked ? palette.accent.opacity(job.locked ? 0.45 : 1) : palette.surface)
                    RoundedRectangle(cornerRadius: 4).stroke(checked ? Color.clear : palette.muted, lineWidth: 1)
                    if checked { Image(systemName: "checkmark").font(.system(size: 13, weight: .bold)).foregroundColor(palette.onAccent) }
                }.frame(width: 20, height: 20).frame(width: 48, height: 48).contentShape(Rectangle())
            }.buttonStyle(PlainButtonStyle()).disabled(job.locked)
                .accessibilityLabel("\(checked ? "Deselect" : "Select") \(job.title)")
                .accessibilityValue(checked ? "Selected" : "Not selected")
                .accessibilityAddTraits(checked ? .isSelected : [])
                .accessibilityIdentifier("printbatch.job.\(job.id).toggle")
            VStack(alignment: .leading, spacing: 4) {
                label(job.title, "printbatch.job.\(job.id).title", weight: .semibold)
                label("\(job.pages) pages × \(job.copies) copies • \(job.isColor ? "Color" : "Mono")\(job.locked ? " • Locked" : "")", "printbatch.job.\(job.id).subtitle", size: 12, color: palette.muted)
            }.frame(maxWidth: .infinity, alignment: .leading)
            label("\(ink(job) + sheets(job)) cr", "printbatch.job.\(job.id).price")
                .layoutPriority(1)
        }.padding(.vertical, 12)
    }
    private func modeButton(_ value: String, title: String) -> some View {
        let active = mode == value
        return Button(action: {
            if mode != value { mode = value; onEvent("paperModeChanged", ["paperMode": value]) }
        }) {
            Text(title).font(font(14, .semibold)).foregroundColor(active ? palette.onAccent : palette.text)
                .fixedSize(horizontal: false, vertical: true).multilineTextAlignment(.center)
                .padding(8).frame(maxWidth: .infinity, minHeight: 48)
                .background(active ? palette.accent : palette.surface)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(active ? palette.accent : palette.muted.opacity(0.25), lineWidth: 1))
                .contentShape(RoundedRectangle(cornerRadius: 10))
        }.buttonStyle(PlainButtonStyle())
            .accessibilityIdentifier("printbatch.mode.\(value)")
            .accessibilityValue(active ? "Selected" : "Not selected")
            .accessibilityAddTraits(active ? .isSelected : [])
    }
    private func costRow(_ id: String, _ title: String, _ amount: Int) -> some View {
        HStack(spacing: 8) {
            label(title, "printbatch.breakdown.\(id).label", size: 12, color: palette.muted)
                .frame(maxWidth: .infinity, alignment: .leading)
            label("\(amount) cr", "printbatch.breakdown.\(id).value", size: 12, color: palette.muted)
        }
    }
}
