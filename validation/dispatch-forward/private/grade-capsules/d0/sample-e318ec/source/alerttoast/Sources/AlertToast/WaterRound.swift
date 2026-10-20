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
        required = model.bedCount * (model.selectedMethod == .drip ? model.dripLitresPerBed : model.soakLitresPerBed)
            + (model.selectedMethod == .drip ? model.dripPrimeLitres : 0)
        spendable = model.tankLitres - model.reserveLitres
        reserveNeeded = max(0, required - spendable)
        remaining = max(0, model.tankLitres - required)
        shortfall = max(0, required - model.tankLitres)
        consentVisible = reserveNeeded > 0 && shortfall == 0
        controlsEnabled = model.isEnabled && !model.isSubmitting
        releaseEnabled = controlsEnabled && shortfall == 0 && (reserveNeeded == 0 || model.reserveAcknowledged)
        if !model.isEnabled { status = "Round paused" }
        else if model.isSubmitting { status = "Preparing release…" }
        else if shortfall > 0 { status = "Not enough water" }
        else if reserveNeeded > 0 && !model.reserveAcknowledged { status = "Approve reserve use" }
        else { status = "Ready to release" }
    }
}

private struct WaterRoundPalette {
    let dark: Bool
    private func color(_ light: UInt32, _ dark: UInt32) -> Color {
        let rgb = self.dark ? dark : light
        return Color(.sRGB, red: Double((rgb >> 16) & 255) / 255,
                     green: Double((rgb >> 8) & 255) / 255, blue: Double(rgb & 255) / 255, opacity: 1)
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

@available(iOS 14, macOS 11, *)
public struct WaterRoundReleaseView: View {
    public let model: WaterRoundModel
    private let onAction: (WaterRoundAction) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.sizeCategory) private var sizeCategory
    @ScaledMetric(relativeTo: .headline) private var titleSize: CGFloat = 20
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 14
    @ScaledMetric(relativeTo: .body) private var labelSize: CGFloat = 13
    @ScaledMetric(relativeTo: .body) private var numberSize: CGFloat = 17
    @ScaledMetric(relativeTo: .headline) private var controlSize: CGFloat = 16

    public init(model: WaterRoundModel, onAction: @escaping (WaterRoundAction) -> Void) {
        self.model = model
        self.onAction = onAction
    }

    private var palette: WaterRoundPalette { WaterRoundPalette(dark: colorScheme == .dark) }
    private var projection: WaterRoundProjection { WaterRoundProjection(model) }
    private func number(_ value: Int) -> String { String(value) }

    public var body: some View {
        let p = projection
        VStack(alignment: .leading, spacing: 12) {
            Text(verbatim: model.title)
                .font(.system(size: titleSize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("waterRound.title")
            bodyText(model.description, id: "description", color: palette.muted)
            VStack(alignment: .leading, spacing: 8) {
                bodyText("Beds: " + number(model.bedCount), id: "beds")
                bodyText("Tank: " + number(model.tankLitres) + " L", id: "tank")
                bodyText("Protected reserve: " + number(model.reserveLitres) + " L", id: "reserve")
                bodyText("Drip prime: " + number(model.dripPrimeLitres) + " L", id: "dripPrime")
            }
            VStack(spacing: 8) {
                method(.drip, name: "Drip lines", rate: model.dripLitresPerBed, enabled: p.controlsEnabled)
                method(.soak, name: "Soak hoses", rate: model.soakLitresPerBed, enabled: p.controlsEnabled && model.soakAllowed)
            }
            VStack(alignment: .leading, spacing: 12) {
                summary("Required", value: p.required, id: "required")
                summary("Outside reserve", value: p.spendable, id: "spendable")
                summary("Reserve needed", value: p.reserveNeeded, id: "reserveNeeded")
                summary("Remaining", value: p.remaining, id: "remaining")
                if p.shortfall > 0 { summary("Shortfall", value: p.shortfall, id: "shortfall") }
            }
            if p.consentVisible { consent(p) }
            if !model.notice.isEmpty { bodyText(model.notice, id: "notice") }
            Text(verbatim: p.status)
                .font(.system(size: bodySize, weight: .semibold))
                .foregroundColor(p.status == "Ready to release" ? palette.foreground : palette.warning)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(p.status == "Ready to release" ? palette.selectedSurface : palette.warningSurface)
                .cornerRadius(12)
                .accessibilityIdentifier("waterRound.status")
            release(p)
        }
        .foregroundColor(palette.foreground)
        .multilineTextAlignment(.leading)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(palette.surface)
        .cornerRadius(20)
        .overlay(RoundedRectangle(cornerRadius: 20).strokeBorder(palette.border, lineWidth: 1))
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("waterRound.root")
    }

    private func bodyText(_ text: String, id: String, color: Color? = nil) -> some View {
        Text(verbatim: text)
            .font(.system(size: bodySize))
            .foregroundColor(color ?? palette.foreground)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityIdentifier("waterRound." + id)
    }

    private func method(_ choice: WateringMethod, name: String, rate: Int, enabled: Bool) -> some View {
        let selected = model.selectedMethod == choice
        let rateText = number(rate) + " L per bed"
        return Button(action: {
            guard enabled, model.selectedMethod != choice else { return }
            onAction(.methodRequested(roundId: model.roundId, method: choice))
        }) {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: selected ? "largecircle.fill.circle" : "circle")
                    .font(.system(size: 18))
                    .foregroundColor(selected ? palette.accent : palette.muted)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 4) {
                    Text(verbatim: name).font(.system(size: controlSize, weight: .semibold))
                        .foregroundColor(palette.foreground)
                    Text(verbatim: rateText).font(.system(size: bodySize)).foregroundColor(palette.muted)
                }
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 56, alignment: .leading)
            .background(selected ? palette.selectedSurface : palette.surface)
            .cornerRadius(12)
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(selected ? palette.accent : palette.border, lineWidth: 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!enabled)
        .accessibilityLabel(Text(verbatim: name + ", " + rateText))
        .accessibility(addTraits: selected ? .isSelected : [])
        .accessibilityIdentifier("waterRound.method." + choice.rawValue)
    }

    private func summary(_ label: String, value: Int, id: String) -> some View {
        Group {
            if sizeCategory.isAccessibilityCategory {
                VStack(alignment: .leading, spacing: 8) {
                    Text(verbatim: label + ":").font(.system(size: labelSize))
                    Text(verbatim: number(value) + " L")
                        .font(.system(size: numberSize, weight: .semibold)).monospacedDigit()
                }
            } else {
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text(verbatim: label + ":").font(.system(size: labelSize))
                    Spacer(minLength: 0)
                    Text(verbatim: number(value) + " L")
                        .font(.system(size: numberSize, weight: .semibold)).monospacedDigit()
                }
            }
        }
        .fixedSize(horizontal: false, vertical: true)
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text(verbatim: label + ": " + number(value) + " L"))
        .accessibilityIdentifier("waterRound." + id)
    }

    private func consent(_ p: WaterRoundProjection) -> some View {
        Toggle(isOn: Binding(get: { model.reserveAcknowledged }, set: { _ in
            guard p.controlsEnabled, p.consentVisible else { return }
            onAction(.reserveAcknowledgementRequested(roundId: model.roundId, acknowledged: !model.reserveAcknowledged))
        })) {
            Text(verbatim: "Use " + number(p.reserveNeeded) + " L from the protected reserve")
                .font(.system(size: bodySize))
                .foregroundColor(palette.foreground)
                .fixedSize(horizontal: false, vertical: true)
        }
        .toggleStyle(SwitchToggleStyle(tint: palette.accent))
        .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
        .padding(12)
        .background(palette.warningSurface)
        .cornerRadius(12)
        .disabled(!p.controlsEnabled)
        .accessibilityIdentifier("waterRound.reserveConsent")
    }

    private func release(_ p: WaterRoundProjection) -> some View {
        let label = "Release " + number(p.required) + " L"
        return Button(action: {
            guard p.releaseEnabled else { return }
            onAction(.releaseRequested(roundId: model.roundId, method: model.selectedMethod,
                                       bedCount: model.bedCount, requestedLitres: p.required,
                                       remainingLitres: p.remaining, reserveUsedLitres: p.reserveNeeded))
        }) {
            HStack(spacing: 8) {
                if model.isEnabled && model.isSubmitting {
                    ProgressView().progressViewStyle(CircularProgressViewStyle(tint: palette.disabledText))
                        .accessibilityIdentifier("waterRound.progress")
                }
                Text(verbatim: label).font(.system(size: controlSize, weight: .semibold))
                    .fixedSize(horizontal: false, vertical: true)
            }
            .foregroundColor(p.releaseEnabled ? palette.accentOn : palette.disabledText)
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 48)
            .background(p.releaseEnabled ? palette.accent : palette.disabledSurface)
            .cornerRadius(12)
            .contentShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!p.releaseEnabled)
        .accessibilityLabel(Text(verbatim: label))
        .accessibilityIdentifier("waterRound.submit")
    }
}
