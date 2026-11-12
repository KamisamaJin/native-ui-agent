// Thin fixture decoder only; this file contains no business UI or local state.
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let input = SubscriptionCapacityInput(
            entityID: fixture["entityID"] as! String,
            revision: fixture["revision"] as! Int,
            title: fixture["title"] as! String,
            context: fixture["context"] as! String,
            notes: fixture["notes"] as! [String],
            seatCount: fixture["seatCount"] as! Int,
            teamQuota: fixture["teamQuota"] as! Int,
            scaleQuota: fixture["scaleQuota"] as! Int,
            prepaidMonths: fixture["prepaidMonths"] as! Int,
            accountBalanceCents: fixture["accountBalanceCents"] as! Int
        )
        return AnyView(SubscriptionCapacityChange(input: input, onEvent: onEvent))
    }
}
