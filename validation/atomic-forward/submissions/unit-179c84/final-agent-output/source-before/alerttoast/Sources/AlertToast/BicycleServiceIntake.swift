import SwiftUI

public struct BicycleServiceOption: Codable, Identifiable {
    public let id: String
    public let label: String
    public let detail: String
    public let available: Bool
    public let unavailableReason: String
    public let minutes: Int

    public init(id: String, label: String, detail: String, available: Bool,
                unavailableReason: String, minutes: Int) {
        self.id = id
        self.label = label
        self.detail = detail
        self.available = available
        self.unavailableReason = unavailableReason
        self.minutes = minutes
    }
}

public struct BicycleServiceIntakeModel: Codable {
    public let revision: String
    public let title: String
    public let subtitle: String
    public let notice: String
    public let footer: String
    public let guidance: String
    public let initialSelectedIDs: [String]
    public let initialDetailsExpanded: Bool
    public let services: [BicycleServiceOption]

    public init(revision: String, title: String, subtitle: String, notice: String,
                footer: String, guidance: String, initialSelectedIDs: [String],
                initialDetailsExpanded: Bool, services: [BicycleServiceOption]) {
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

@available(iOS 14, macOS 11, *)
public struct BicycleServiceIntake: View {
    public let model: BicycleServiceIntakeModel
    private let onToggle: (String, Bool) -> Void
    private let onDetailsChange: (Bool) -> Void
    private let onSubmit: ([String]) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .subheadline) private var supportingSize: CGFloat = 14
    @State private var selectedIDs: Set<String>
    @State private var detailsExpanded: Bool

    public init(model: BicycleServiceIntakeModel,
                onToggle: @escaping (String, Bool) -> Void,
                onDetailsChange: @escaping (Bool) -> Void,
                onSubmit: @escaping ([String]) -> Void) {
        self.model = model
        self.onToggle = onToggle
        self.onDetailsChange = onDetailsChange
        self.onSubmit = onSubmit
        let availableIDs = Set(model.services.filter { $0.available }.map { $0.id })
        _selectedIDs = State(initialValue: Set(model.initialSelectedIDs).intersection(availableIDs))
        _detailsExpanded = State(initialValue: model.initialDetailsExpanded)
    }

    private var palette: BicyclePalette { BicyclePalette(dark: colorScheme == .dark) }
    private var chosenServices: [BicycleServiceOption] {
        model.services.filter { $0.available && selectedIDs.contains($0.id) }
    }
    private var summary: String {
        let chosen = chosenServices
        guard !chosen.isEmpty else { return "No work selected · 0 min" }
        return "Work: \(chosen.map { $0.label }.joined(separator: " + ")) · \(chosen.reduce(0) { $0 + $1.minutes }) min"
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            VStack(alignment: .leading, spacing: 12) {
                copy(model.title, size: titleSize, weight: .semibold)
                    .accessibilityAddTraits(.isHeader)
                    .accessibilityIdentifier("bicycle.title")
                copy(model.subtitle, size: bodySize)
                VStack(alignment: .leading, spacing: 0) {
                    copy(model.notice, size: bodySize)
                }
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 10).fill(palette.notice))
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(model.notice)
                .accessibilityIdentifier("bicycle.notice")
            }

            serviceGroup("Inspection", services: model.services.filter { ["a", "b"].contains($0.id) })
            serviceGroup("Specialist work", services: model.services.filter { $0.id == "c" })
            serviceGroup("Care and adjustments", services: model.services.filter { !["a", "b", "c"].contains($0.id) })

            copy(summary, size: bodySize, weight: .semibold)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityLabel(summary)
                .accessibilityIdentifier("bicycle.summary")

            VStack(alignment: .leading, spacing: 12) {
                Button {
                    detailsExpanded.toggle()
                    onDetailsChange(detailsExpanded)
                } label: {
                    copy(detailsExpanded ? "Hide handover notes" : "Show handover notes",
                         size: bodySize, weight: .semibold)
                        .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .buttonStyle(PlainButtonStyle())
                .accessibilityLabel(detailsExpanded ? "Hide handover notes" : "Show handover notes")
                .accessibilityIdentifier("bicycle.disclosure")
                if detailsExpanded {
                    copy(model.guidance, size: bodySize)
                }
            }

            Button {
                guard !chosenServices.isEmpty else { return }
                onSubmit(chosenServices.map { $0.id })
            } label: {
                Text("Send service draft")
                    .font(.system(size: bodySize, weight: .semibold))
                    .foregroundColor(palette.onAction)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(16)
                    .frame(minHeight: 56)
                    .background(RoundedRectangle(cornerRadius: 10)
                        .fill(chosenServices.isEmpty ? palette.disabled : palette.enabled))
                    .contentShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(chosenServices.isEmpty)
            .accessibilityLabel("Send service draft")
            .accessibilityIdentifier("bicycle.submit")

            copy(model.footer, size: supportingSize)
                .accessibilityIdentifier("bicycle.footer")
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12).fill(palette.canvas))
        .foregroundColor(palette.ink)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("bicycle.canvas")
        .onChange(of: model.revision) { _ in
            let availableIDs = Set(model.services.filter { $0.available }.map { $0.id })
            selectedIDs = Set(model.initialSelectedIDs).intersection(availableIDs)
            detailsExpanded = model.initialDetailsExpanded
        }
    }

    private func copy(_ value: String, size: CGFloat, weight: Font.Weight = .regular) -> some View {
        Text(value)
            .font(.system(size: size, weight: weight))
            .foregroundColor(palette.ink)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder
    private func serviceGroup(_ title: String, services: [BicycleServiceOption]) -> some View {
        if !services.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                copy(title, size: bodySize, weight: .semibold)
                    .accessibilityAddTraits(.isHeader)
                ForEach(services) { service in
                    serviceButton(service)
                }
            }
        }
    }

    private func serviceButton(_ service: BicycleServiceOption) -> some View {
        let selected = service.available && selectedIDs.contains(service.id)
        return Button {
            guard service.available else { return }
            let nextSelected = !selectedIDs.contains(service.id)
            if nextSelected { selectedIDs.insert(service.id) }
            else { selectedIDs.remove(service.id) }
            onToggle(service.id, nextSelected)
        } label: {
            VStack(alignment: .leading, spacing: 12) {
                copy("\(selected ? "☑" : "☐") \(service.label)\(service.available ? "" : " · Unavailable")",
                     size: bodySize, weight: .semibold)
                if !service.available {
                    copy(service.unavailableReason, size: supportingSize)
                }
                if !service.detail.isEmpty {
                    copy(service.detail, size: supportingSize)
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 10)
                .fill(selected ? palette.selected : palette.surface))
            .contentShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!service.available)
        .accessibilityLabel(([service.label]
            + (service.available ? [] : ["Unavailable", service.unavailableReason])
            + (service.detail.isEmpty ? [] : [service.detail])).joined(separator: ". "))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("bicycle.choice.\(service.id)")
    }
}

private struct BicyclePalette {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let rgb = dark ? darkValue : light
        return Color(.sRGB, red: Double((rgb >> 16) & 255) / 255,
                     green: Double((rgb >> 8) & 255) / 255,
                     blue: Double(rgb & 255) / 255, opacity: 1)
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
