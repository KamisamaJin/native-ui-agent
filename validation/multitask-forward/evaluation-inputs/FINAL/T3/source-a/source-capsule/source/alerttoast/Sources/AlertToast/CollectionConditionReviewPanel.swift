import SwiftUI

public struct CollectionConditionObject: Codable, Equatable {
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

public struct CollectionConditionReviewRequest: Codable, Equatable {
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

public struct CollectionConditionReviewPanel: View {
    private let request: CollectionConditionReviewRequest
    private let onConfirm: (String, [CollectionConditionAssessment]) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @State private var decisions: [String: CollectionConditionAssessment]
    @State private var focusID: String
    @State private var loadedRequestID: String
    @ScaledMetric(relativeTo: .body) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 14
    @ScaledMetric(relativeTo: .body) private var rowSize: CGFloat = 16
    @ScaledMetric(relativeTo: .body) private var captionSize: CGFloat = 13
    @ScaledMetric(relativeTo: .body) private var summarySize: CGFloat = 18
    @ScaledMetric(relativeTo: .body) private var inspectorSize: CGFloat = 20

    public init(request: CollectionConditionReviewRequest, onConfirm: @escaping (String, [CollectionConditionAssessment]) -> Void) {
        self.request = request
        self.onConfirm = onConfirm
        _decisions = State(initialValue: Self.seed(request))
        _focusID = State(initialValue: Self.initialFocus(request))
        _loadedRequestID = State(initialValue: request.id)
    }

    private static func seed(_ request: CollectionConditionReviewRequest) -> [String: CollectionConditionAssessment] {
        Dictionary(uniqueKeysWithValues: request.objects.map {
            ($0.id, CollectionConditionAssessment(id: $0.id, status: $0.status, reason: $0.status == "care" ? $0.reason : nil))
        })
    }

    private static func initialFocus(_ request: CollectionConditionReviewRequest) -> String {
        request.objects.contains(where: { $0.id == request.focusID }) ? request.focusID : (request.objects.first?.id ?? "")
    }

    private var palette: ConditionPalette { ConditionPalette(dark: colorScheme == .dark) }
    private func decision(for object: CollectionConditionObject) -> CollectionConditionAssessment {
        decisions[object.id] ?? CollectionConditionAssessment(id: object.id, status: object.status, reason: object.status == "care" ? object.reason : nil)
    }
    private func complete(_ decision: CollectionConditionAssessment) -> Bool {
        decision.status == "stable" || (decision.status == "care" && ["surface", "structure"].contains(decision.reason ?? ""))
    }
    private var ready: Bool { request.objects.filter(\.required).allSatisfy { complete(decision(for: $0)) } }
    private var summary: String {
        let completed = request.objects.filter { complete(decision(for: $0)) }.count
        let care = request.objects.filter { decision(for: $0).status == "care" }.count
        return "\(completed) of \(request.objects.count) reviewed • \(care) follow-up\(care == 1 ? "" : "s")"
    }
    private var validation: String {
        let required = request.objects.filter(\.required)
        if required.contains(where: { decision(for: $0).status == "care" && !complete(decision(for: $0)) }) {
            return "Choose a care category"
        }
        let remaining = required.filter { !complete(decision(for: $0)) }.count
        return remaining > 0 ? "\(remaining) required decision\(remaining == 1 ? "" : "s") remaining" : "Ready to submit"
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                text(request.title, size: titleSize, weight: .bold, color: palette.ink)
                    .accessibilityIdentifier("condition.title")
                text(request.context, size: bodySize, color: palette.muted)
            }
            VStack(alignment: .leading, spacing: 12) {
                text("Inspection queue", size: rowSize, weight: .semibold, color: palette.ink)
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(Array(request.objects.enumerated()), id: \.element.id) { index, object in
                        queueRow(object, index: index)
                    }
                }
            }
            if let object = request.objects.first(where: { $0.id == focusID }) ?? request.objects.first {
                inspector(object)
            }
            VStack(alignment: .leading, spacing: 16) {
                text(summary, size: summarySize, weight: .semibold, color: palette.ink)
                    .accessibilityIdentifier("condition.summary")
                text(validation, size: bodySize, weight: .semibold, color: palette.accent)
                    .accessibilityIdentifier("condition.validation")
                Button {
                    guard ready else { return }
                    let assessments = request.objects.map { decision(for: $0) }.sorted { $0.id < $1.id }
                    onConfirm(request.id, assessments)
                } label: {
                    Text("Submit review")
                        .font(.system(size: rowSize, weight: .semibold))
                        .foregroundColor(ready ? palette.primaryInk : palette.muted)
                        .padding(.horizontal, 12)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .frame(height: 56)
                        .background(RoundedRectangle(cornerRadius: 10).fill(ready ? palette.accent : palette.border))
                        .contentShape(Rectangle())
                }
                .buttonStyle(ConditionButtonStyle())
                .disabled(!ready)
                .accessibilityIdentifier("condition.primary")
            }
            VStack(alignment: .leading, spacing: 16) {
                text("Review notes", size: rowSize, weight: .semibold, color: palette.ink)
                    .accessibilityIdentifier("condition.notes")
                ForEach(Array(request.notes.enumerated()), id: \.offset) { _, note in
                    text(note, size: bodySize, color: palette.muted)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .onChange(of: request) { updatedRequest in
            guard updatedRequest.id != loadedRequestID else { return }
            loadedRequestID = updatedRequest.id
            decisions = Self.seed(updatedRequest)
            focusID = Self.initialFocus(updatedRequest)
        }
    }

    private func text(_ value: String, size: CGFloat, weight: Font.Weight = .regular, color: Color) -> some View {
        Text(value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(color)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func queueRow(_ object: CollectionConditionObject, index: Int) -> some View {
        let status = decision(for: object).status
        let caption = status == "stable" ? "Stable" : (status == "care" ? "Needs care" : "Pending")
        let label = "\(object.title), \(caption)"
        let selected = focusID == object.id
        return Button { focusID = object.id } label: {
            Text(label)
                .font(.system(size: rowSize, weight: .semibold))
                .foregroundColor(palette.ink)
                .fixedSize(horizontal: false, vertical: true)
                .padding(12)
                .frame(maxWidth: .infinity, minHeight: 64, alignment: .leading)
                .background(controlBackground(selected: selected, enabled: true))
                .overlay(selectedMarker(selected), alignment: .topTrailing)
                .contentShape(Rectangle())
        }
        .buttonStyle(ConditionButtonStyle())
        .frame(width: CGFloat(request.queueWidth))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(label)
        .accessibilityIdentifier("condition.queue\(index + 1)")
        .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private func inspector(_ object: CollectionConditionObject) -> some View {
        let current = decision(for: object)
        return VStack(alignment: .leading, spacing: 16) {
            text("Object inspector", size: captionSize, weight: .semibold, color: palette.accent)
            VStack(alignment: .leading, spacing: 8) {
                text(object.title, size: inspectorSize, weight: .semibold, color: palette.ink)
                    .accessibilityIdentifier("condition.focused")
                text(object.material, size: bodySize, color: palette.muted)
                if !object.editable {
                    text("Read only", size: captionSize, weight: .semibold, color: palette.muted)
                }
            }
            text(object.inspectionNote, size: bodySize, color: palette.muted)
                .accessibilityIdentifier("condition.inspectionNote")
            VStack(alignment: .leading, spacing: 8) {
                choice("Stable", identifier: "condition.stable", selected: current.status == "stable", enabled: object.editable) {
                    classify(object, status: "stable")
                }
                choice("Needs care", identifier: "condition.care", selected: current.status == "care", enabled: object.editable) {
                    classify(object, status: "care")
                }
            }
            if current.status == "care" {
                VStack(alignment: .leading, spacing: 8) {
                    text("Care category", size: rowSize, weight: .semibold, color: palette.ink)
                        .accessibilityIdentifier("condition.reasonGroup")
                    choice("Surface", identifier: "condition.surface", selected: current.reason == "surface", enabled: object.editable, exactHeight: 48) {
                        setReason(object, reason: "surface")
                    }
                    choice("Structure", identifier: "condition.structure", selected: current.reason == "structure", enabled: object.editable, exactHeight: 48) {
                        setReason(object, reason: "structure")
                    }
                }
            }
        }
    }

    private func choice(_ label: String, identifier: String, selected: Bool, enabled: Bool, exactHeight: CGFloat? = nil, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: rowSize, weight: .semibold))
                .foregroundColor(enabled ? palette.ink : palette.muted)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 12)
                .padding(.vertical, exactHeight == nil ? 12 : 0)
                .frame(maxWidth: .infinity, minHeight: exactHeight == nil ? 48 : nil, alignment: .leading)
                .frame(height: exactHeight)
                .background(controlBackground(selected: selected, enabled: enabled))
                .overlay(selectedMarker(selected), alignment: .topTrailing)
                .contentShape(Rectangle())
        }
        .buttonStyle(ConditionButtonStyle())
        .disabled(!enabled)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(label)
        .accessibilityIdentifier(identifier)
        .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private func controlBackground(selected: Bool, enabled: Bool) -> some View {
        RoundedRectangle(cornerRadius: 10)
            .fill(enabled ? palette.surface : palette.border)
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(selected ? palette.accent : palette.border, lineWidth: 1))
    }

    private func selectedMarker(_ selected: Bool) -> some View {
        Circle().fill(palette.accent).frame(width: 4, height: 4)
            .padding(4).opacity(selected ? 1 : 0).accessibilityHidden(true)
    }

    private func classify(_ object: CollectionConditionObject, status: String) {
        guard object.editable, object.id == focusID else { return }
        let old = decision(for: object)
        decisions[object.id] = CollectionConditionAssessment(id: object.id, status: status, reason: status == "care" && old.status == "care" ? old.reason : nil)
    }

    private func setReason(_ object: CollectionConditionObject, reason: String) {
        guard object.editable, object.id == focusID, decision(for: object).status == "care" else { return }
        decisions[object.id] = CollectionConditionAssessment(id: object.id, status: "care", reason: reason)
    }
}

private struct ConditionButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

private struct ConditionPalette {
    let surface: Color
    let ink: Color
    let muted: Color
    let accent: Color
    let border: Color
    let primaryInk: Color

    init(dark: Bool) {
        surface = Self.color(dark ? 0x2A1D36 : 0xF6F1FA)
        ink = Self.color(dark ? 0xEADDF6 : 0x432D58)
        muted = Self.color(dark ? 0xC8B5D9 : 0x746181)
        accent = Self.color(dark ? 0xD5B6F5 : 0x7750A6)
        border = Self.color(dark ? 0x634E75 : 0xDACDE5)
        primaryInk = Self.color(dark ? 0x1C1424 : 0xFFFFFF)
    }

    private static func color(_ rgb: UInt) -> Color {
        Color(red: Double((rgb >> 16) & 255) / 255, green: Double((rgb >> 8) & 255) / 255, blue: Double(rgb & 255) / 255)
    }
}
