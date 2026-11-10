import Foundation
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let data = try! JSONSerialization.data(withJSONObject: fixture, options: [.sortedKeys])
        let model = try! JSONDecoder().decode(MenuChangeModel.self, from: data)
        return AnyView(MenuChangeReviewPanel(model: model) { submission in
            onEvent(submission.wireValue)
        })
    }
}
