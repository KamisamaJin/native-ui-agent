import SwiftUI
import AlertToast

// Caller adaptation only: every visible element and all local state belong to production.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let options = (fixture["options"] as! [[String: Any]]).map { item in
            ListeningBreakOption(id: item["id"] as! String,
                                 title: item["title"] as! String,
                                 detail: item["detail"] as! String,
                                 isAvailable: item["isAvailable"] as! Bool)
        }
        let input = ListeningBreakInput(sessionID: fixture["sessionID"] as! String,
                                        title: fixture["title"] as! String,
                                        introduction: fixture["introduction"] as! String,
                                        options: options,
                                        quietNote: fixture["quietNote"] as! String,
                                        footer: fixture["footer"] as! String)
        return AnyView(ListeningBreakPanel(input: input,
            onStart: { sessionID, optionID in onEvent("listening.started:\(sessionID):\(optionID)") },
            onCancel: { sessionID in onEvent("listening.canceled:\(sessionID)") }))
    }
}
