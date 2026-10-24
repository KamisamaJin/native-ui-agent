interface LabelFormatting {
    fun stringFor(count: Int): String
}

data class BadgeModel(val count: Int, val formatter: LabelFormatting) {
    companion object {
        const val accessibilityIdentifier = "neutral.badge.count"
    }

    val displayCount: Int get() = count.coerceAtLeast(0)
    val label: String get() = formatter.stringFor(displayCount)
}
