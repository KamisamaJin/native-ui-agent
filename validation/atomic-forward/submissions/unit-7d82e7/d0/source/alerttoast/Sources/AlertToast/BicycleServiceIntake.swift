import SwiftUI

public struct BicycleServiceOption: Codable, Identifiable {
    public var id: String
    public var label: String
    public var detail: String
    public var available: Bool
    public var unavailableReason: String
    public var minutes: Int

    public init(id: String, label: String, detail: String, available: Bool, unavailableReason: String, minutes: Int) {
        self.id = id
        self.label = label
        self.detail = detail
        self.available = available
        self.unavailableReason = unavailableReason
        self.minutes = minutes
    }
}

public struct BicycleServiceIntakeModel: Codable {
    public var revision: String
    public var title: String
    public var subtitle: String
    public var notice: String
    public var footer: String
    public var guidance: String
    public var initialSelectedIDs: [String]
    public var initialDetailsExpanded: Bool
    public var services: [BicycleServiceOption]

    public init(revision: String, title: String, subtitle: String, notice: String, footer: String, guidance: String, initialSelectedIDs: [String], initialDetailsExpanded: Bool, services: [BicycleServiceOption]) {
        self.revision = revision
        self.title = title
        self.subtitle = subtitle
        self.notice = notice
        self.footer = footer
        self.guidance = guidance
        self.initialSelectedIDs = initialSelectedIDs
        self.initialDetailsExpanded = initialDetailsExpanded
        self.services = services
    }
}

public struct BicycleServiceIntake: View {
    private let model: BicycleServiceIntakeModel
    private let onToggle: (String, Bool) -> Void
    private let onDetailsChange: (Bool) -> Void
    private let onSubmit: ([String]) -> Void

    public init(model: BicycleServiceIntakeModel, onToggle: @escaping (String, Bool) -> Void, onDetailsChange: @escaping (Bool) -> Void, onSubmit: @escaping ([String]) -> Void) {
        self.model = model
        self.onToggle = onToggle
        self.onDetailsChange = onDetailsChange
        self.onSubmit = onSubmit
    }

    public var body: some View {
        BicycleServiceDraft(model: model, onToggle: onToggle, onDetailsChange: onDetailsChange, onSubmit: onSubmit)
            .id(model.revision)
    }
}

private struct BicycleServiceDraft: View {
    let model: BicycleServiceIntakeModel
    let onToggle: (String, Bool) -> Void
    let onDetailsChange: (Bool) -> Void
    let onSubmit: ([String]) -> Void
    @State private var selectedIDs: Set<String>
    @State private var detailsExpanded: Bool
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .subheadline) private var supportingSize: CGFloat = 14

    init(model: BicycleServiceIntakeModel, onToggle: @escaping (String, Bool) -> Void, onDetailsChange: @escaping (Bool) -> Void, onSubmit: @escaping ([String]) -> Void) {
        self.model = model
        self.onToggle = onToggle
        self.onDetailsChange = onDetailsChange
        self.onSubmit = onSubmit
        let valid = Set(model.services.filter { $0.available }.map { $0.id })
        _selectedIDs = State(initialValue: Set(model.initialSelectedIDs).intersection(valid))
        _detailsExpanded = State(initialValue: model.initialDetailsExpanded)
    }

    private var palette: BicyclePalette { BicyclePalette(dark: colorScheme == .dark) }
    private var selectedServices: [BicycleServiceOption] {
        model.services.filter { $0.available && selectedIDs.contains($0.id) }
    }
    private var summary: String {
        let current = selectedServices
        guard !current.isEmpty else { return "No work selected · 0 min" }
        return "Work: \(current.map { $0.label }.joined(separator: " + ")) · \(current.reduce(0) { $0 + $1.minutes }) min"
    }
    private var disclosureLabel: String { detailsExpanded ? "Hide handover notes" : "Show handover notes" }

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            VStack(alignment: .leading, spacing: 12) {
                copy(model.title, size: titleSize, weight: .semibold)
                    .accessibilityAddTraits(.isHeader)
                    .accessibilityIdentifier("bicycle.title")
                copy(model.subtitle, size: bodySize)
                copy(model.notice, size: bodySize)
                    .padding(16)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 10).fill(palette.notice))
                    .accessibilityElement(children: .combine)
                    .accessibilityLabel(model.notice)
                    .accessibilityIdentifier("bicycle.notice")
            }

            VStack(alignment: .leading, spacing: 20) {
                serviceGroup("Inspection", services: model.services.filter { ["a", "b"].contains($0.id) })
                serviceGroup("Specialist work", services: model.services.filter { $0.id == "c" })
                serviceGroup("Care and adjustments", services: model.services.filter { !["a", "b", "c"].contains($0.id) })
            }

            copy(summary, size: bodySize, weight: .semibold)
                .accessibilityLabel(summary)
                .accessibilityIdentifier("bicycle.summary")

            VStack(alignment: .leading, spacing: 12) {
                Button(action: {
                    detailsExpanded.toggle()
                    onDetailsChange(detailsExpanded)
                }) {
                    copy(disclosureLabel, size: bodySize, weight: .semibold)
                        .frame(minHeight: 56, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .buttonStyle(PlainButtonStyle())
                .accessibilityLabel(disclosureLabel)
                .accessibilityIdentifier("bicycle.disclosure")
                if detailsExpanded {
                    copy(model.guidance, size: bodySize)
                }
            }

            Button(action: {
                let current = selectedServices
                guard !current.isEmpty else { return }
                onSubmit(current.map { $0.id })
            }) {
                Text("Send service draft")
                    .font(.system(size: bodySize, weight: .semibold))
                    .foregroundColor(palette.onAction)
                    .fixedSize(horizontal: false, vertical: true)
                    .multilineTextAlignment(.leading)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 16)
                    .frame(minHeight: 56)
                    .background(RoundedRectangle(cornerRadius: 10).fill(selectedServices.isEmpty ? palette.disabled : palette.enabled))
                    .contentShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(selectedServices.isEmpty)
            .accessibilityLabel("Send service draft")
            .accessibilityIdentifier("bicycle.submit")

            copy(model.footer, size: supportingSize)
                .accessibilityIdentifier("bicycle.footer")
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12).fill(palette.canvas))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("bicycle.canvas")
    }

    private func copy(_ value: String, size: CGFloat, weight: Font.Weight = .regular) -> some View {
        Text(value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(palette.ink)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder private func serviceGroup(_ name: String, services: [BicycleServiceOption]) -> some View {
        if !services.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                copy(name, size: bodySize, weight: .semibold)
                    .accessibilityAddTraits(.isHeader)
                ForEach(services) { service in
                    serviceButton(service)
                }
            }
        }
    }

    private func serviceButton(_ service: BicycleServiceOption) -> some View {
        let isSelected = service.available && selectedIDs.contains(service.id)
        return Button(action: {
            guard service.available else { return }
            let next = !selectedIDs.contains(service.id)
            if next { selectedIDs.insert(service.id) } else { selectedIDs.remove(service.id) }
            onToggle(service.id, next)
        }) {
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: isSelected ? "checkmark.square.fill" : "square")
                        .font(.system(size: bodySize))
                        .foregroundColor(palette.ink)
                        .accessibilityHidden(true)
                    copy(service.label + (service.available ? "" : " · Unavailable"), size: bodySize, weight: .semibold)
                }
                if !service.available {
                    copy(service.unavailableReason, size: supportingSize)
                }
                if !service.detail.isEmpty {
                    copy(service.detail, size: supportingSize)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 10).fill(isSelected ? palette.selected : palette.surface))
            .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!service.available)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
        .accessibilityIdentifier("bicycle.choice.\(service.id)")
    }
}

private struct BicyclePalette {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let value = dark ? darkValue : light
        return Color(.sRGB, red: Double((value >> 16) & 255) / 255, green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255, opacity: 1)
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
