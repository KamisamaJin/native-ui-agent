import SwiftUI
import AlertToast

// Decode observer input only; state, controls and callbacks live in the component.
enum ObserverBridge {
    static func make(
        fixture: [String: Any],
        onEvent: @escaping (String) -> Void
    ) -> AnyView {
        guard let marker = fixture["marker"] as? String,
              let detail = fixture["detail"] as? String else {
            preconditionFailure("Qualification fixture requires marker and detail")
        }
        if #available(iOS 14.0, *) {
            return AnyView(NativeQualificationProbe(
                marker: marker,
                detail: detail,
                onEvent: onEvent
            ))
        }
        preconditionFailure("Qualification fixture requires the admitted iOS 14+ runtime")
    }
}
