import SwiftUI

public enum WateringMethod: String {
    case drip
    case soak
}

public struct WaterRoundModel {
    public let roundId: String
    public let title: String
    public let description: String
    public let notice: String
    public let bedCount: Int
    public let dripLitresPerBed: Int
    public let soakLitresPerBed: Int
    public let dripPrimeLitres: Int
    public let tankLitres: Int
    public let reserveLitres: Int
    public let soakAllowed: Bool
    public let selectedMethod: WateringMethod
    public let reserveAcknowledged: Bool
    public let isEnabled: Bool
    public let isSubmitting: Bool

    public init(roundId: String, title: String, description: String, notice: String,
                bedCount: Int, dripLitresPerBed: Int, soakLitresPerBed: Int,
                dripPrimeLitres: Int, tankLitres: Int, reserveLitres: Int,
                soakAllowed: Bool, selectedMethod: WateringMethod,
                reserveAcknowledged: Bool, isEnabled: Bool, isSubmitting: Bool) {
        self.roundId = roundId
        self.title = title
        self.description = description
        self.notice = notice
        self.bedCount = bedCount
        self.dripLitresPerBed = dripLitresPerBed
        self.soakLitresPerBed = soakLitresPerBed
        self.dripPrimeLitres = dripPrimeLitres
        self.tankLitres = tankLitres
        self.reserveLitres = reserveLitres
        self.soakAllowed = soakAllowed
        self.selectedMethod = selectedMethod
        self.reserveAcknowledged = reserveAcknowledged
        self.isEnabled = isEnabled
        self.isSubmitting = isSubmitting
    }
}

public enum WaterRoundAction {
    case methodRequested(roundId: String, method: WateringMethod)
    case reserveAcknowledgementRequested(roundId: String, acknowledged: Bool)
    case releaseRequested(roundId: String, method: WateringMethod, bedCount: Int,
                          requestedLitres: Int, remainingLitres: Int, reserveUsedLitres: Int)
}

private struct WaterRoundProjection {
    let required: Int
    let spendable: Int
    let reserveNeeded: Int
    let remaining: Int
    let shortfall: Int
    let consentVisible: Bool
    let controlsEnabled: Bool
    let releaseEnabled: Bool
    let status: String

    init(_ model: WaterRoundModel) {
        let rate = model.selectedMethod == .drip ? model.dripLitresPerBed : model.soakLitresPerBed
        required = model.bedCount * rate + (model.selectedMethod == .drip ? model.dripPrimeLitres : 0)
        spendable = model.tankLitres - model.reserveLitres
        reserveNeeded = max(0, required - spendable)
        remaining = max(0, model.tankLitres - required)
        shortfall = max(0, required - model.tankLitres)
        consentVisible = reserveNeeded > 0 && shortfall == 0
        controlsEnabled = model.isEnabled && !model.isSubmitting
        releaseEnabled = controlsEnabled && shortfall == 0 && (reserveNeeded == 0 || model.reserveAcknowledged)
        if !model.isEnabled {
            status = "Round paused"
        } else if model.isSubmitting {
            status = "Preparing release…"
        } else if shortfall > 0 {
            status = "Not enough water"
        } else if reserveNeeded > 0 && !model.reserveAcknowledged {
            status = "Approve reserve use"
        } else {
            status = "Ready to release"
        }
    }
}

private struct WaterRoundPalette {
    let dark: Bool
    private func color(_ light: UInt32, _ darkValue: UInt32) -> Color {
        let rgb = dark ? darkValue : light
        return Color(.sRGB, red: Double((rgb >> 16) & 255) / 255,
                     green: Double((rgb >> 8) & 255) / 255,
                     blue: Double(rgb & 255) / 255, opacity: 1)
    }
    var surface: Color { color(0xFFFFFF, 0x15251C) }
    var border: Color { color(0xD7E3D8, 0x3B5242) }
    var foreground: Color { color(0x183A25, 0xE7F3E9) }
    var muted: Color { color(0x526B59, 0xB2C8B8) }
    var accent: Color { color(0x216B3B, 0x81D89B) }
    var accentOn: Color { color(0xFFFFFF, 0x102C19) }
    var selectedSurface: Color { color(0xE5F2E8, 0x244F33) }
    var warning: Color { color(0x865400, 0xFFD28A) }
    var warningSurface: Color { color(0xFFF1D5, 0x493715) }
    var disabledSurface: Color { color(0xE5EBE6, 0x293C2F) }
    var disabledText: Color { color(0x65756A, 0x92A396) }
}

// The view supplies the complete enabled and disabled palette. Keep SwiftUI's
// disabled semantics without adding a second visual opacity to that palette.
@available(iOS 14, macOS 11, *)
private struct WaterRoundButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
    }
}

@available(iOS 14, macOS 11, *)
public struct WaterRoundReleaseView: View {
    public let model: WaterRoundModel
    private let onAction: (WaterRoundAction) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .headline) private var titleSize: CGFloat = 20
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 14
    @ScaledMetric(relativeTo: .subheadline) private var summaryLabelSize: CGFloat = 13
    @ScaledMetric(relativeTo: .body) private var summaryValueSize: CGFloat = 17
    @ScaledMetric(relativeTo: .headline) private var controlSize: CGFloat = 16

    public init(model: WaterRoundModel, onAction: @escaping (WaterRoundAction) -> Void) {
        self.model = model
        self.onAction = onAction
    }

    private var palette: WaterRoundPalette { WaterRoundPalette(dark: colorScheme == .dark) }
    private var projection: WaterRoundProjection { WaterRoundProjection(model) }

    public var body: some View {
        let values = projection
        VStack(alignment: .leading, spacing: 12) {
            Text(verbatim: model.title)
                .font(.system(size: titleSize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("waterRound.title")
            bodyText(model.description, identifier: "waterRound.description", color: palette.muted)
            VStack(alignment: .leading, spacing: 8) {
                bodyText("Beds: \(model.bedCount)", identifier: "waterRound.beds")
                bodyText("Tank: \(model.tankLitres) L", identifier: "waterRound.tank")
                bodyText("Protected reserve: \(model.reserveLitres) L", identifier: "waterRound.reserve")
                bodyText("Drip prime: \(model.dripPrimeLitres) L", identifier: "waterRound.dripPrime")
            }
            VStack(spacing: 8) {
                methodButton(.drip, name: "Drip lines", rate: model.dripLitresPerBed, enabled: values.controlsEnabled)
                methodButton(.soak, name: "Soak hoses", rate: model.soakLitresPerBed,
                             enabled: values.controlsEnabled && model.soakAllowed)
            }
            VStack(alignment: .leading, spacing: 8) {
                summary("Required", value: values.required, identifier: "waterRound.required")
                summary("Outside reserve", value: values.spendable, identifier: "waterRound.spendable")
                summary("Reserve needed", value: values.reserveNeeded, identifier: "waterRound.reserveNeeded")
                summary("Remaining", value: values.remaining, identifier: "waterRound.remaining")
                if values.shortfall > 0 {
                    summary("Shortfall", value: values.shortfall, identifier: "waterRound.shortfall")
                }
            }
            if values.consentVisible {
                Toggle(isOn: Binding(get: { model.reserveAcknowledged }, set: { acknowledged in
                    guard projection.consentVisible, projection.controlsEnabled else { return }
                    onAction(.reserveAcknowledgementRequested(roundId: model.roundId, acknowledged: !model.reserveAcknowledged))
                })) {
                    Text(verbatim: "Use \(values.reserveNeeded) L from the protected reserve")
                        .font(.system(size: bodySize))
                        .fixedSize(horizontal: false, vertical: true)
                }
                .toggleStyle(SwitchToggleStyle())
                .accentColor(palette.accent)
                .frame(minHeight: 44)
                .disabled(!values.controlsEnabled)
                .accessibilityIdentifier("waterRound.reserveConsent")
            }
            if !model.notice.isEmpty {
                bodyText(model.notice, identifier: "waterRound.notice")
            }
            Text(verbatim: values.status)
                .font(.system(size: bodySize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .foregroundColor(values.status == "Ready to release" ? palette.foreground : palette.warning)
                .background(values.status == "Ready to release" ? palette.selectedSurface : palette.warningSurface)
                .cornerRadius(12)
                .accessibilityIdentifier("waterRound.status")
            Button(action: {
                let current = projection
                guard current.releaseEnabled else { return }
                onAction(.releaseRequested(roundId: model.roundId, method: model.selectedMethod,
                                           bedCount: model.bedCount, requestedLitres: current.required,
                                           remainingLitres: current.remaining, reserveUsedLitres: current.reserveNeeded))
            }) {
                HStack(spacing: 8) {
                    if model.isEnabled && model.isSubmitting {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: palette.disabledText))
                            .accessibilityIdentifier("waterRound.progress")
                    }
                    Text(verbatim: "Release \(values.required) L")
                        .font(.system(size: controlSize, weight: .semibold))
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(12)
                .frame(maxWidth: .infinity, minHeight: 48)
                .foregroundColor(values.releaseEnabled ? palette.accentOn : palette.disabledText)
                .background(values.releaseEnabled ? palette.accent : palette.disabledSurface)
                .cornerRadius(12)
                .contentShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(WaterRoundButtonStyle())
            .disabled(!values.releaseEnabled)
            .accessibilityLabel(Text(verbatim: "Release \(values.required) L"))
            .accessibilityIdentifier("waterRound.submit")
        }
        .foregroundColor(palette.foreground)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(palette.surface)
        .cornerRadius(20)
        .overlay(RoundedRectangle(cornerRadius: 20).strokeBorder(palette.border, lineWidth: 1))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("waterRound.root")
    }

    private func bodyText(_ value: String, identifier: String, color: Color? = nil) -> some View {
        Text(verbatim: value)
            .font(.system(size: bodySize))
            .foregroundColor(color ?? palette.foreground)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityIdentifier(identifier)
    }

    private func summary(_ label: String, value: Int, identifier: String) -> some View {
        (Text(verbatim: "\(label): ").font(.system(size: summaryLabelSize)) +
         Text(verbatim: "\(value) L").font(.system(size: summaryValueSize, weight: .semibold).monospacedDigit()))
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityIdentifier(identifier)
    }

    private func methodButton(_ method: WateringMethod, name: String, rate: Int, enabled: Bool) -> some View {
        let selected = model.selectedMethod == method
        return Button(action: {
            guard enabled, model.selectedMethod != method else { return }
            onAction(.methodRequested(roundId: model.roundId, method: method))
        }) {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: selected ? "largecircle.fill.circle" : "circle")
                    .font(.system(size: controlSize))
                    .foregroundColor(selected ? palette.accent : palette.muted)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 4) {
                    Text(verbatim: name).font(.system(size: controlSize, weight: .semibold))
                    Text(verbatim: "\(rate) L per bed")
                        .font(.system(size: bodySize)).foregroundColor(palette.muted)
                }
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .foregroundColor(palette.foreground)
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
            .background(selected ? palette.selectedSurface : palette.surface)
            .cornerRadius(12)
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(selected ? palette.accent : palette.border, lineWidth: 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(WaterRoundButtonStyle())
        .disabled(!enabled)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text(verbatim: "\(name), \(rate) L per bed"))
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("waterRound.method.\(method.rawValue)")
    }
}
