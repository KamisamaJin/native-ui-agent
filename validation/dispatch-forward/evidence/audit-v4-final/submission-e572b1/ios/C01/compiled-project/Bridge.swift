import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        // Deliberately strict: malformed input is an integration failure.
        let model = WaterRoundModel(
            roundId: fixture["roundId"] as! String,
            title: fixture["title"] as! String,
            description: fixture["description"] as! String,
            notice: fixture["notice"] as! String,
            bedCount: fixture["bedCount"] as! Int,
            dripLitresPerBed: fixture["dripLitresPerBed"] as! Int,
            soakLitresPerBed: fixture["soakLitresPerBed"] as! Int,
            dripPrimeLitres: fixture["dripPrimeLitres"] as! Int,
            tankLitres: fixture["tankLitres"] as! Int,
            reserveLitres: fixture["reserveLitres"] as! Int,
            soakAllowed: fixture["soakAllowed"] as! Bool,
            selectedMethod: WateringMethod(rawValue: fixture["selectedMethod"] as! String)!,
            reserveAcknowledged: fixture["reserveAcknowledged"] as! Bool,
            isEnabled: fixture["isEnabled"] as! Bool,
            isSubmitting: fixture["isSubmitting"] as! Bool)
        return AnyView(WaterRoundReleaseView(model: model) { action in
            switch action {
            case let .methodRequested(roundId, method):
                onEvent("methodRequested|roundId=\(roundId)|method=\(method.rawValue)")
            case let .reserveAcknowledgementRequested(roundId, acknowledged):
                onEvent("reserveAcknowledgementRequested|roundId=\(roundId)|acknowledged=\(acknowledged ? "true" : "false")")
            case let .releaseRequested(roundId, method, bedCount, requestedLitres, remainingLitres, reserveUsedLitres):
                onEvent("releaseRequested|roundId=\(roundId)|method=\(method.rawValue)|bedCount=\(bedCount)|requestedLitres=\(requestedLitres)|remainingLitres=\(remainingLitres)|reserveUsedLitres=\(reserveUsedLitres)")
            }
        })
    }
}
