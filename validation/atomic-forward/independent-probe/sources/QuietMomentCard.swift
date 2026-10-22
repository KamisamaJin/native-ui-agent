import SwiftUI

public struct QuietMomentCard: View {
    public let title: String
    public let detail: String
    public let canvas: Color
    public let band: Color
    public let onAcknowledge: () -> Void
    public init(title: String, detail: String, canvas: Color, band: Color, onAcknowledge: @escaping () -> Void) {
        self.title = title; self.detail = detail; self.canvas = canvas; self.band = band; self.onAcknowledge = onAcknowledge
    }
    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Rectangle().fill(band).frame(height: 64)
                .accessibilityElement(children: .ignore).accessibilityLabel("Accent region")
                .accessibilityIdentifier("moment.band")
            Text(title).font(.title2).fontWeight(.semibold)
                .fixedSize(horizontal: false, vertical: true).accessibilityIdentifier("moment.title")
            Text(detail).font(.body).fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("moment.body")
            Button(action: onAcknowledge) {
                Text("Acknowledge").font(.body).fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, minHeight: 48, alignment: .leading)
                    .contentShape(Rectangle())
            }.buttonStyle(PlainButtonStyle()).accessibilityIdentifier("moment.action")
        }.foregroundColor(Color(red: 32/255, green: 33/255, blue: 36/255))
            .padding(20).frame(maxWidth: .infinity, alignment: .leading).background(canvas)
            .accessibilityElement(children: .contain).accessibilityIdentifier("moment.canvas")
    }
}
