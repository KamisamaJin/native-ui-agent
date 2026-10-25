import SwiftUI
import AlertToast

// Data conversion only; the production component owns presentation and interaction.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        func string(_ key: String) -> String { fixture[key] as! String }
        let data = CollectionAuthorizationData(
            requestID: string("requestID"),
            title: string("title"),
            jobSummary: string("jobSummary"),
            pickupWindow: string("pickupWindow"),
            notesClosedTitle: string("notesClosedTitle"),
            notesOpenTitle: string("notesOpenTitle"),
            notesBody: string("notesBody"),
            selfTitle: string("selfTitle"),
            selfDetail: string("selfDetail"),
            delegateTitle: string("delegateTitle"),
            delegateDetail: string("delegateDetail"),
            acknowledgement: string("acknowledgement"),
            confirmTitle: string("confirmTitle"),
            sentTitle: string("sentTitle"),
            readyMessage: string("readyMessage"),
            needsAcknowledgementMessage: string("needsAcknowledgementMessage"),
            sentMessage: string("sentMessage"),
            delegateUnavailableMessage: string("delegateUnavailableMessage"),
            delegateAvailable: fixture["delegateAvailable"] as! Bool
        )
        return AnyView(CollectionAuthorizationCard(data: data, onEvent: onEvent))
    }
}
