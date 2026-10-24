protocol LabelFormatting {
    func string(for count: Int) -> String
}

struct BadgeModel {
    let count: Int
    let formatter: any LabelFormatting
    static let accessibilityIdentifier = "neutral.badge.count"

    var displayCount: Int { max(0, count) }
    var label: String { formatter.string(for: displayCount) }
}
