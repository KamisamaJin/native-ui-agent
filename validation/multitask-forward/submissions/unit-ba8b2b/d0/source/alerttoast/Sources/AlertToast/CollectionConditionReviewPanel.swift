import SwiftUI

public struct CollectionConditionObject: Codable {
    public let id: String
    public let title: String
    public let material: String
    public let inspectionNote: String
    public let status: String
    public let reason: String?
    public let editable: Bool
    public let required: Bool

    public init(id: String, title: String, material: String, inspectionNote: String, status: String, reason: String?, editable: Bool, required: Bool) {
        self.id = id
        self.title = title
        self.material = material
        self.inspectionNote = inspectionNote
        self.status = status
        self.reason = reason
        self.editable = editable
        self.required = required
    }
}

public struct CollectionConditionReviewRequest: Codable {
    public let id: String
    public let title: String
    public let context: String
    public let focusID: String
    public let queueWidth: Double
    public let notes: [String]
    public let objects: [CollectionConditionObject]

    public init(id: String, title: String, context: String, focusID: String, queueWidth: Double, notes: [String], objects: [CollectionConditionObject]) {
        self.id = id
        self.title = title
        self.context = context
        self.focusID = focusID
        self.queueWidth = queueWidth
        self.notes = notes
        self.objects = objects
    }
}

public struct CollectionConditionAssessment: Codable {
    public let id: String
    public let status: String
    public let reason: String?

    public init(id: String, status: String, reason: String?) {
        self.id = id
        self.status = status
        self.reason = reason
    }
}

private struct ConditionPalette {
    let canvas: Color
    let surface: Color
    let ink: Color
    let muted: Color
    let accent: Color
    let border: Color
    let primaryInk: Color

    init(dark: Bool) {
        func rgb(_ value: UInt32) -> Color {
            Color(red: Double((value >> 16) & 255) / 255,
                  green: Double((value >> 8) & 255) / 255,
                  blue: Double(value & 255) / 255)
        }
        canvas = rgb(dark ? 0x1C1424 : 0xFFFFFF)
        surface = rgb(dark ? 0x2A1D36 : 0xF6F1FA)
        ink = rgb(dark ? 0xEADDF6 : 0x432D58)
        muted = rgb(dark ? 0xC8B5D9 : 0x746181)
        accent = rgb(dark ? 0xD5B6F5 : 0x7750A6)
        border = rgb(dark ? 0x634E75 : 0xDACDE5)
        primaryInk = rgb(dark ? 0x1C1424 : 0xFFFFFF)
    }
}

public struct CollectionConditionReviewPanel: View {
    private let request: CollectionConditionReviewRequest
    private let onConfirm: (String, [CollectionConditionAssessment]) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @State private var focusID: String
    @State private var decisions: [String: CollectionConditionAssessment]
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 14
    @ScaledMetric(relativeTo: .body) private var controlSize: CGFloat = 16
    @ScaledMetric(relativeTo: .caption) private var captionSize: CGFloat = 13
    @ScaledMetric(relativeTo: .headline) private var summarySize: CGFloat = 18
    @ScaledMetric(relativeTo: .title3) private var inspectorSize: CGFloat = 20

    public init(request: CollectionConditionReviewRequest, onConfirm: @escaping (String, [CollectionConditionAssessment]) -> Void) {
        self.request = request
        self.onConfirm = onConfirm
        _focusID = State(initialValue: Self.initialFocus(request))
        _decisions = State(initialValue: Self.seed(request))
    }

    private static func initialFocus(_ request: CollectionConditionReviewRequest) -> String {
        request.objects.first(where: { $0.id == request.focusID })?.id ?? request.objects.first?.id ?? ""
    }

    private static func seed(_ request: CollectionConditionReviewRequest) -> [String: CollectionConditionAssessment] {
        var values: [String: CollectionConditionAssessment] = [:]
        for object in request.objects {
            values[object.id] = CollectionConditionAssessment(id: object.id, status: object.status,
                reason: object.status == "care" ? object.reason : nil)
        }
        return values
    }

    private var palette: ConditionPalette { ConditionPalette(dark: colorScheme == .dark) }
    private var focused: CollectionConditionObject? {
        request.objects.first(where: { $0.id == focusID }) ?? request.objects.first
    }
    private func decision(_ object: CollectionConditionObject) -> CollectionConditionAssessment {
        decisions[object.id] ?? CollectionConditionAssessment(id: object.id, status: object.status,
            reason: object.status == "care" ? object.reason : nil)
    }
    private func isComplete(_ value: CollectionConditionAssessment) -> Bool {
        value.status == "stable" || (value.status == "care" && ["surface", "structure"].contains(value.reason ?? ""))
    }
    private var remaining: Int {
        request.objects.filter { $0.required && !isComplete(decision($0)) }.count
    }
    private var ready: Bool { remaining == 0 }
    private var summary: String {
        let count = request.objects.filter { isComplete(decision($0)) }.count
        let care = request.objects.filter { decision($0).status == "care" }.count
        return "\(count) of \(request.objects.count) reviewed • \(care) follow-up\(care == 1 ? "" : "s")"
    }
    private var validation: String {
        if request.objects.contains(where: { $0.required && decision($0).status == "care" && !isComplete(decision($0)) }) {
            return "Choose a care category"
        }
        if remaining > 0 { return "\(remaining) required decision\(remaining == 1 ? "" : "s") remaining" }
        return "Ready to submit"
    }
    private func statusName(_ status: String) -> String {
        switch status {
        case "stable": return "Stable"
        case "care": return "Needs care"
        default: return "Pending"
        }
    }
    private func classify(_ object: CollectionConditionObject, as status: String) {
        guard object.editable, object.id == focused?.id else { return }
        let old = decision(object)
        decisions[object.id] = CollectionConditionAssessment(id: object.id, status: status,
            reason: status == "care" && old.status == "care" ? old.reason : nil)
    }
    private func setReason(_ object: CollectionConditionObject, _ reason: String) {
        guard object.editable, object.id == focused?.id, decision(object).status == "care" else { return }
        decisions[object.id] = CollectionConditionAssessment(id: object.id, status: "care", reason: reason)
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                text(request.title, size: titleSize, weight: .bold, color: palette.ink)
                    .accessibilityIdentifier("condition.title")
                text(request.context, size: bodySize, color: palette.muted)
            }
            VStack(alignment: .leading, spacing: 8) {
                text("Inspection queue", size: controlSize, weight: .semibold, color: palette.ink)
                ForEach(Array(request.objects.enumerated()), id: \.element.id) { index, object in
                    choice(label: "\(object.title), \(statusName(decision(object).status))",
                           identifier: "condition.queue\(index + 1)", selected: focused?.id == object.id,
                           enabled: true, minHeight: 64, exactHeight: nil,
                           width: CGFloat(request.queueWidth)) { focusID = object.id }
                }
            }
            if let object = focused {
                inspector(object)
            }
            VStack(alignment: .leading, spacing: 16) {
                text(summary, size: summarySize, weight: .semibold, color: palette.ink)
                    .accessibilityIdentifier("condition.summary")
                text(validation, size: bodySize, weight: .semibold, color: palette.accent)
                    .accessibilityIdentifier("condition.validation")
                Button(action: {
                    guard ready else { return }
                    onConfirm(request.id, request.objects.map { decision($0) }.sorted { $0.id < $1.id })
                }) {
                    Text("Submit review")
                        .font(.system(size: controlSize, weight: .semibold))
                        .foregroundColor(ready ? palette.primaryInk : palette.muted)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 12)
                        .frame(height: 56)
                        .background(ready ? palette.accent : palette.border)
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                        .contentShape(RoundedRectangle(cornerRadius: 10))
                }
                .buttonStyle(PlainButtonStyle())
                .disabled(!ready)
                .accessibilityLabel("Submit review")
                .accessibilityIdentifier("condition.primary")
            }
            VStack(alignment: .leading, spacing: 16) {
                text("Review notes", size: controlSize, weight: .semibold, color: palette.ink)
                    .accessibilityIdentifier("condition.notes")
                ForEach(Array(request.notes.enumerated()), id: \.offset) { _, note in
                    text(note, size: bodySize, color: palette.muted)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(palette.canvas)
        .onChange(of: request.id) { _ in
            decisions = Self.seed(request)
            focusID = Self.initialFocus(request)
        }
    }

    private func text(_ value: String, size: CGFloat, weight: Font.Weight = .regular, color: Color) -> some View {
        Text(value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(color)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func inspector(_ object: CollectionConditionObject) -> some View {
        let value = decision(object)
        return VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                text("Object inspector", size: captionSize, weight: .semibold, color: palette.accent)
                text(object.title, size: inspectorSize, weight: .semibold, color: palette.ink)
                    .accessibilityIdentifier("condition.focused")
                text(object.material, size: bodySize, color: palette.muted)
                if !object.editable {
                    text("Read only", size: bodySize, weight: .semibold, color: palette.muted)
                }
            }
            text(object.inspectionNote, size: bodySize, color: palette.muted)
                .accessibilityIdentifier("condition.inspectionNote")
            VStack(alignment: .leading, spacing: 8) {
                choice(label: "Stable", identifier: "condition.stable", selected: value.status == "stable",
                       enabled: object.editable) { classify(object, as: "stable") }
                choice(label: "Needs care", identifier: "condition.care", selected: value.status == "care",
                       enabled: object.editable) { classify(object, as: "care") }
            }
            if value.status == "care" {
                VStack(alignment: .leading, spacing: 8) {
                    text("Care category", size: bodySize, weight: .semibold, color: palette.ink)
                        .accessibilityIdentifier("condition.reasonGroup")
                    choice(label: "Surface", identifier: "condition.surface", selected: value.reason == "surface",
                           enabled: object.editable, exactHeight: 48) { setReason(object, "surface") }
                    choice(label: "Structure", identifier: "condition.structure", selected: value.reason == "structure",
                           enabled: object.editable, exactHeight: 48) { setReason(object, "structure") }
                }
            }
        }
    }

    private func choice(label: String, identifier: String, selected: Bool, enabled: Bool,
                        minHeight: CGFloat = 48, exactHeight: CGFloat? = nil, width: CGFloat? = nil,
                        action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: controlSize, weight: .semibold))
                .foregroundColor(enabled ? palette.ink : palette.muted)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 12)
                .padding(.vertical, exactHeight == nil ? 12 : 0)
                .frame(minHeight: minHeight)
                .frame(height: exactHeight)
                .frame(width: width)
                .background(enabled ? palette.surface : palette.border)
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .overlay(RoundedRectangle(cornerRadius: 10).stroke(selected ? palette.accent : palette.border, lineWidth: 1))
                .overlay(Group {
                    if selected { Circle().fill(palette.accent).frame(width: 4, height: 4).padding(4) }
                }, alignment: .topTrailing)
                .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!enabled)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(label)
        .accessibilityIdentifier(identifier)
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}
