import SwiftUI

public struct ReturnResolutionModel {
    public let caseId: String
    public let merchant: String
    public let heading: String
    public let orderReference: String
    public let intro: String
    public let status: ReturnResolutionStatus
    public let statusLabel: String
    public let item: ReturnResolutionItem
    public let deadline: ReturnResolutionDeadline?
    public let contextMessage: String
    public let optionsTitle: String
    public let options: [ReturnResolutionOption]
    public let selectedOptionId: String?
    public let sizesTitle: String
    public let sizes: [ReturnResolutionSize]
    public let selectedSizeId: String?
    public let acknowledgementAccepted: Bool
    public let notes: ReturnResolutionNotes
    public let notesExpanded: Bool
    public let amountRows: [ReturnResolutionAmountRow]
    public let totalLabel: String
    public let totalValue: String
    public let totalFootnote: String
    public let idlePrimaryLabel: String
    public let keepLabel: String
    public let progressTitle: String
    public let progressBody: String
    public let resultTitle: String
    public let resultBody: String
    public let resultReference: String
    public let doneLabel: String
    public let strings: ReturnResolutionStrings
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
    public let title: String
    public let variant: String
    public let quantityLabel: String
    public let paidLabel: String
    public let accent: ReturnResolutionAccent
    public init(title: String, variant: String, quantityLabel: String, paidLabel: String, accent: ReturnResolutionAccent) {
        self.title = title
        self.variant = variant
        self.quantityLabel = quantityLabel
        self.paidLabel = paidLabel
        self.accent = accent
    }
}

public struct ReturnResolutionDeadline {
    public let text: String
    public let urgent: Bool
    public init(text: String, urgent: Bool) {
        self.text = text
        self.urgent = urgent
    }
}

public struct ReturnResolutionOption {
    public let id: String
    public let kind: ReturnResolutionKind
    public let title: String
    public let description: String
    public let amountLabel: String
    public let tag: String?
    public let disabledReason: String?
    public let detailTitle: String
    public let detailBody: String
    public let acknowledgementLabel: String?
    public let primaryLabel: String
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
    public let id: String
    public let label: String
    public let unavailableReason: String?
    public init(id: String, label: String, unavailableReason: String?) {
        self.id = id
        self.label = label
        self.unavailableReason = unavailableReason
    }
}

public struct ReturnResolutionNotes {
    public let title: String
    public let body: String
    public let bullets: [String]
    public init(title: String, body: String, bullets: [String]) {
        self.title = title
        self.body = body
        self.bullets = bullets
    }
}

public struct ReturnResolutionAmountRow {
    public let id: String
    public let label: String
    public let value: String
    public let emphasized: Bool
    public init(id: String, label: String, value: String, emphasized: Bool) {
        self.id = id
        self.label = label
        self.value = value
        self.emphasized = emphasized
    }
}

public struct ReturnResolutionStrings {
    public let chooseOption: String
    public let chooseSize: String
    public let acceptTerms: String
    public let ready: String
    public let noOptions: String
    public let checkedValue: String
    public let uncheckedValue: String
    public let expandedValue: String
    public let collapsedValue: String
    public let busyValue: String
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
