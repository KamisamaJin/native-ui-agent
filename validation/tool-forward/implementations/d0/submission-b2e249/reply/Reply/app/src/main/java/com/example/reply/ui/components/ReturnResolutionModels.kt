package com.example.reply.ui.components

/** Caller-owned values for a return settlement. No presentation state is cached. */
data class ReturnResolutionModel(
    val caseId: String,
    val merchant: String,
    val heading: String,
    val orderReference: String,
    val intro: String,
    val status: ReturnResolutionStatus,
    val statusLabel: String,
    val item: ReturnResolutionItem,
    val deadline: ReturnResolutionDeadline?,
    val contextMessage: String,
    val optionsTitle: String,
    val options: List<ReturnResolutionOption>,
    val selectedOptionId: String?,
    val sizesTitle: String,
    val sizes: List<ReturnResolutionSize>,
    val selectedSizeId: String?,
    val acknowledgementAccepted: Boolean,
    val notes: ReturnResolutionNotes,
    val notesExpanded: Boolean,
    val amountRows: List<ReturnResolutionAmountRow>,
    val totalLabel: String,
    val totalValue: String,
    val totalFootnote: String,
    val idlePrimaryLabel: String,
    val keepLabel: String,
    val progressTitle: String,
    val progressBody: String,
    val resultTitle: String,
    val resultBody: String,
    val resultReference: String,
    val doneLabel: String,
    val strings: ReturnResolutionStrings
)

data class ReturnResolutionItem(
    val title: String,
    val variant: String,
    val quantityLabel: String,
    val paidLabel: String,
    val accent: ReturnResolutionAccent
)

data class ReturnResolutionDeadline(
    val text: String,
    val urgent: Boolean
)

data class ReturnResolutionOption(
    val id: String,
    val kind: ReturnResolutionKind,
    val title: String,
    val description: String,
    val amountLabel: String,
    val tag: String?,
    val disabledReason: String?,
    val detailTitle: String,
    val detailBody: String,
    val acknowledgementLabel: String?,
    val primaryLabel: String
)

data class ReturnResolutionSize(
    val id: String,
    val label: String,
    val unavailableReason: String?
)

data class ReturnResolutionNotes(
    val title: String,
    val body: String,
    val bullets: List<String>
)

data class ReturnResolutionAmountRow(
    val id: String,
    val label: String,
    val value: String,
    val emphasized: Boolean
)

data class ReturnResolutionStrings(
    val chooseOption: String,
    val chooseSize: String,
    val acceptTerms: String,
    val ready: String,
    val noOptions: String,
    val checkedValue: String,
    val uncheckedValue: String,
    val expandedValue: String,
    val collapsedValue: String,
    val busyValue: String
)

enum class ReturnResolutionStatus { EDITING, SUBMITTING, COMPLETE }
enum class ReturnResolutionKind { REFUND, CREDIT, EXCHANGE }
enum class ReturnResolutionAccent { TEAL, CORAL, INDIGO }

sealed class ReturnResolutionAction {
    data class SelectOption(val optionId: String) : ReturnResolutionAction()
    data class SelectSize(val sizeId: String) : ReturnResolutionAction()
    data class SetAcknowledgement(val accepted: Boolean) : ReturnResolutionAction()
    data class SetNotesExpanded(val expanded: Boolean) : ReturnResolutionAction()
    data class Submit(val optionId: String, val sizeId: String?, val acknowledgementAccepted: Boolean) : ReturnResolutionAction()
    object KeepPurchase : ReturnResolutionAction()
    object Done : ReturnResolutionAction()
}
