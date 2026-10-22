import SwiftUI

public struct RiverSensorIncident: Codable, Identifiable {
    public var id: String
    public var label: String
    public var detail: String
    public var available: Bool
    public var unavailableReason: String
    public var severity: String

    public init(id: String, label: String, detail: String, available: Bool,
                unavailableReason: String, severity: String) {
        self.id = id
        self.label = label
        self.detail = detail
        self.available = available
        self.unavailableReason = unavailableReason
        self.severity = severity
    }
}

public struct RiverSensorTriageModel: Codable {
    public var revision: String
    public var title: String
    public var subtitle: String
    public var notice: String
    public var footer: String
    public var guidance: String
    public var initialSelectedID: String?
    public var initialDetailsExpanded: Bool
    public var incidents: [RiverSensorIncident]

    public init(revision: String, title: String, subtitle: String, notice: String,
                footer: String, guidance: String, initialSelectedID: String?,
                initialDetailsExpanded: Bool, incidents: [RiverSensorIncident]) {
        self.revision = revision
        self.title = title
        self.subtitle = subtitle
        self.notice = notice
        self.footer = footer
        self.guidance = guidance
        self.initialSelectedID = initialSelectedID
        self.initialDetailsExpanded = initialDetailsExpanded
        self.incidents = incidents
    }
}

@available(iOS 14, macOS 11, *)
public struct RiverSensorTriageBoard: View {
    public var model: RiverSensorTriageModel
    private let onSelect: (String) -> Void
    private let onDetailsChange: (Bool) -> Void
    private let onAcknowledge: (String) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .footnote) private var supportingSize: CGFloat = 14
    @State private var draft: Draft

    private struct Draft {
        var revision: String
        var selectedID: String?
        var expanded: Bool
    }

    public init(model: RiverSensorTriageModel,
                onSelect: @escaping (String) -> Void,
                onDetailsChange: @escaping (Bool) -> Void,
                onAcknowledge: @escaping (String) -> Void) {
        self.model = model
        self.onSelect = onSelect
        self.onDetailsChange = onDetailsChange
        self.onAcknowledge = onAcknowledge
        _draft = State(initialValue: Self.initialDraft(model))
    }

    private static func initialDraft(_ model: RiverSensorTriageModel) -> Draft {
        Draft(revision: model.revision,
              selectedID: model.incidents.first { $0.id == model.initialSelectedID && $0.available }?.id,
              expanded: model.initialDetailsExpanded)
    }

    private var currentDraft: Draft {
        draft.revision == model.revision ? draft : Self.initialDraft(model)
    }

    private var selectedIncident: RiverSensorIncident? {
        model.incidents.first { $0.id == currentDraft.selectedID && $0.available }
    }

    private var colors: RiverColors { RiverColors(dark: colorScheme == .dark) }

    private func copy(_ value: String, supporting: Bool = false, semibold: Bool = false) -> some View {
        Text(value)
            .font(.system(size: supporting ? supportingSize : bodySize,
                          weight: semibold ? .semibold : .regular))
            .foregroundColor(colors.ink)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(model.title)
                .font(.system(size: titleSize, weight: .semibold))
                .foregroundColor(colors.ink)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("river.title")

            copy(model.subtitle)

            VStack(alignment: .leading, spacing: 0) {
                copy(model.notice)
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 10).fill(colors.notice))
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(Text(model.notice))
            .accessibilityIdentifier("river.notice")

            VStack(alignment: .leading, spacing: 12) {
                Button(action: {
                    var next = currentDraft
                    next.expanded.toggle()
                    draft = next
                    onDetailsChange(next.expanded)
                }) {
                    copy(currentDraft.expanded ? "Hide reading dossier" : "Show reading dossier", semibold: true)
                        .padding(.vertical, 4)
                        .contentShape(Rectangle())
                }
                .buttonStyle(RiverButtonStyle())
                .accessibilityLabel(Text(currentDraft.expanded ? "Hide reading dossier" : "Show reading dossier"))
                .accessibilityIdentifier("river.disclosure")

                if currentDraft.expanded && selectedIncident == nil {
                    copy(model.guidance)
                        .padding(.vertical, 4)
                }

                VStack(alignment: .leading, spacing: 12) {
                    ForEach(model.incidents) { incident in
                        VStack(alignment: .leading, spacing: 12) {
                            incidentButton(incident)
                            if currentDraft.expanded && selectedIncident?.id == incident.id {
                                copy(incident.detail)
                                    .padding(.leading, 24)
                                    .padding(.vertical, 4)
                            }
                        }
                    }
                }
            }
            .padding(.top, 8)

            copy(selectedIncident.map { "Reviewing: \($0.label)" } ?? "No alert selected", semibold: true)
                .accessibilityIdentifier("river.summary")
                .padding(.top, 8)

            Button(action: {
                if let selected = selectedIncident { onAcknowledge(selected.id) }
            }) {
                Text("Acknowledge alert")
                    .font(.system(size: bodySize, weight: .semibold))
                    .foregroundColor(colors.onAction)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 18)
                    .padding(.vertical, 16)
                    .frame(minHeight: 56)
                    .background(RoundedRectangle(cornerRadius: 10).fill(selectedIncident == nil ? colors.disabled : colors.enabled))
                    .contentShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(RiverButtonStyle())
            .disabled(selectedIncident == nil)
            .accessibilityLabel(Text("Acknowledge alert"))
            .accessibilityIdentifier("river.submit")
            .padding(.top, 8)

            copy(model.footer, supporting: true)
                .accessibilityIdentifier("river.footer")
                .padding(.top, 8)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12).fill(colors.canvas))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("river.canvas")
        .onChange(of: model.revision) { _ in draft = Self.initialDraft(model) }
    }

    private func incidentButton(_ incident: RiverSensorIncident) -> some View {
        let selected = selectedIncident?.id == incident.id
        return Button(action: {
            guard incident.available else { return }
            var next = currentDraft
            next.selectedID = incident.id
            draft = next
            onSelect(incident.id)
        }) {
            VStack(alignment: .leading, spacing: 12) {
                copy(incident.available ? incident.label : incident.label + " · Unavailable", semibold: true)
                copy(incident.severity.uppercased(), supporting: true, semibold: true)
                if !incident.available {
                    copy(incident.unavailableReason, supporting: true)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 10).fill(selected ? colors.selected : colors.surface))
            .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(RiverButtonStyle())
        .disabled(!incident.available)
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("river.choice.\(incident.id)")
        .padding(.leading, 12)
        .overlay(Rectangle().fill(colors.enabled).frame(width: 2).padding(.leading, 4).accessibilityHidden(true), alignment: .leading)
    }
}

private struct RiverButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View { configuration.label }
}

private struct RiverColors {
    let dark: Bool
    private func color(_ light: UInt32, _ dark: UInt32) -> Color {
        let value = self.dark ? dark : light
        return Color(.sRGB, red: Double((value >> 16) & 255) / 255,
                     green: Double((value >> 8) & 255) / 255,
                     blue: Double(value & 255) / 255, opacity: 1)
    }
    var canvas: Color { color(0xF5F2EB, 0x14282D) }
    var notice: Color { color(0xE7DED0, 0x2D4245) }
    var enabled: Color { color(0x315F68, 0x8CC7C7) }
    var disabled: Color { color(0xAAA99F, 0x52666A) }
    var ink: Color { color(0x172D32, 0xE6F1EF) }
    var surface: Color { color(0xFFFFFF, 0x20383D) }
    var selected: Color { color(0xD6E6E5, 0x31575C) }
    var onAction: Color { color(0xF8FBFA, 0x102D30) }
}
