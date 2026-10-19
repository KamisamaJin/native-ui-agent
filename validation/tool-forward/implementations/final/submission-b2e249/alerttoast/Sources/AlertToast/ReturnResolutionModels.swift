import SwiftUI

public struct ReturnResolutionModel {
    public var caseId: String
    public var merchant: String
    public var heading: String
    public var orderReference: String
    public var intro: String
    public var status: ReturnResolutionStatus
    public var statusLabel: String
    public var item: ReturnResolutionItem
    public var deadline: ReturnResolutionDeadline?
    public var contextMessage: String
    public var optionsTitle: String
    public var options: [ReturnResolutionOption]
    public var selectedOptionId: String?
    public var sizesTitle: String
    public var sizes: [ReturnResolutionSize]
    public var selectedSizeId: String?
    public var acknowledgementAccepted: Bool
    public var notes: ReturnResolutionNotes
    public var notesExpanded: Bool
    public var amountRows: [ReturnResolutionAmountRow]
    public var totalLabel: String
    public var totalValue: String
    public var totalFootnote: String
    public var idlePrimaryLabel: String
    public var keepLabel: String
    public var progressTitle: String
    public var progressBody: String
    public var resultTitle: String
    public var resultBody: String
    public var resultReference: String
    public var doneLabel: String
    public var strings: ReturnResolutionStrings
    public init(caseId: String, merchant: String, heading: String, orderReference: String, intro: String, status: ReturnResolutionStatus, statusLabel: String, item: ReturnResolutionItem, deadline: ReturnResolutionDeadline?, contextMessage: String, optionsTitle: String, options: [ReturnResolutionOption], selectedOptionId: String?, sizesTitle: String, sizes: [ReturnResolutionSize], selectedSizeId: String?, acknowledgementAccepted: Bool, notes: ReturnResolutionNotes, notesExpanded: Bool, amountRows: [ReturnResolutionAmountRow], totalLabel: String, totalValue: String, totalFootnote: String, idlePrimaryLabel: String, keepLabel: String, progressTitle: String, progressBody: String, resultTitle: String, resultBody: String, resultReference: String, doneLabel: String, strings: ReturnResolutionStrings) {
        self.caseId = caseId
        self.merchant = merchant
        self.heading = heading
        self.orderReference = orderReference
        self.intro = intro
        self.status = status
        self.statusLabel = statusLabel
        self.item = item
        self.deadline = deadline
        self.contextMessage = contextMessage
        self.optionsTitle = optionsTitle
        self.options = options
        self.selectedOptionId = selectedOptionId
        self.sizesTitle = sizesTitle
        self.sizes = sizes
        self.selectedSizeId = selectedSizeId
        self.acknowledgementAccepted = acknowledgementAccepted
        self.notes = notes
        self.notesExpanded = notesExpanded
        self.amountRows = amountRows
        self.totalLabel = totalLabel
        self.totalValue = totalValue
        self.totalFootnote = totalFootnote
        self.idlePrimaryLabel = idlePrimaryLabel
        self.keepLabel = keepLabel
        self.progressTitle = progressTitle
        self.progressBody = progressBody
        self.resultTitle = resultTitle
        self.resultBody = resultBody
        self.resultReference = resultReference
        self.doneLabel = doneLabel
        self.strings = strings
    }
}

public struct ReturnResolutionItem {
    public var title: String
    public var variant: String
    public var quantityLabel: String
    public var paidLabel: String
    public var accent: ReturnResolutionAccent
    public init(title: String, variant: String, quantityLabel: String, paidLabel: String, accent: ReturnResolutionAccent) {
        self.title = title
        self.variant = variant
        self.quantityLabel = quantityLabel
        self.paidLabel = paidLabel
        self.accent = accent
    }
}

public struct ReturnResolutionDeadline {
    public var text: String
    public var urgent: Bool
    public init(text: String, urgent: Bool) {
        self.text = text
        self.urgent = urgent
    }
}

public struct ReturnResolutionOption {
    public var id: String
    public var kind: ReturnResolutionKind
    public var title: String
    public var description: String
    public var amountLabel: String
    public var tag: String?
    public var disabledReason: String?
    public var detailTitle: String
    public var detailBody: String
    public var acknowledgementLabel: String?
    public var primaryLabel: String
    public init(id: String, kind: ReturnResolutionKind, title: String, description: String, amountLabel: String, tag: String?, disabledReason: String?, detailTitle: String, detailBody: String, acknowledgementLabel: String?, primaryLabel: String) {
        self.id = id
        self.kind = kind
        self.title = title
        self.description = description
        self.amountLabel = amountLabel
        self.tag = tag
        self.disabledReason = disabledReason
        self.detailTitle = detailTitle
        self.detailBody = detailBody
        self.acknowledgementLabel = acknowledgementLabel
        self.primaryLabel = primaryLabel
    }
}

public struct ReturnResolutionSize {
    public var id: String
    public var label: String
    public var unavailableReason: String?
    public init(id: String, label: String, unavailableReason: String?) {
        self.id = id
        self.label = label
        self.unavailableReason = unavailableReason
    }
}

public struct ReturnResolutionNotes {
    public var title: String
    public var body: String
    public var bullets: [String]
    public init(title: String, body: String, bullets: [String]) {
        self.title = title
        self.body = body
        self.bullets = bullets
    }
}

public struct ReturnResolutionAmountRow {
    public var id: String
    public var label: String
    public var value: String
    public var emphasized: Bool
    public init(id: String, label: String, value: String, emphasized: Bool) {
        self.id = id
        self.label = label
        self.value = value
        self.emphasized = emphasized
    }
}

public struct ReturnResolutionStrings {
    public var chooseOption: String
    public var chooseSize: String
    public var acceptTerms: String
    public var ready: String
    public var noOptions: String
    public var checkedValue: String
    public var uncheckedValue: String
    public var expandedValue: String
    public var collapsedValue: String
    public var busyValue: String
    public init(chooseOption: String, chooseSize: String, acceptTerms: String, ready: String, noOptions: String, checkedValue: String, uncheckedValue: String, expandedValue: String, collapsedValue: String, busyValue: String) {
        self.chooseOption = chooseOption
        self.chooseSize = chooseSize
        self.acceptTerms = acceptTerms
        self.ready = ready
        self.noOptions = noOptions
        self.checkedValue = checkedValue
        self.uncheckedValue = uncheckedValue
        self.expandedValue = expandedValue
        self.collapsedValue = collapsedValue
        self.busyValue = busyValue
    }
}

public enum ReturnResolutionStatus { case editing, submitting, complete }
public enum ReturnResolutionKind { case refund, credit, exchange }
public enum ReturnResolutionAccent { case teal, coral, indigo }

public enum ReturnResolutionAction {
    case selectOption(optionId: String)
    case selectSize(sizeId: String)
    case setAcknowledgement(accepted: Bool)
    case setNotesExpanded(expanded: Bool)
    case submit(optionId: String, sizeId: String?, acknowledgementAccepted: Bool)
    case keepPurchase
    case done
}
