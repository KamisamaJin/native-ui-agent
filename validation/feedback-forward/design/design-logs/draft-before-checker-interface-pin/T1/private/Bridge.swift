import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let notes = (fixture["notes"] as! [[String: Any]]).map {
            TransferHandlingNote(id: $0["id"] as! String, title: $0["title"] as! String, body: $0["body"] as! String)
        }
        let transfer = ColdStorageTransfer(id: fixture["id"] as! String,
            title: fixture["title"] as! String, destination: fixture["destination"] as! String,
            temperatureRange: fixture["temperatureRange"] as! String,
            sealIntact: fixture["sealIntact"] as! Bool, coolantReady: fixture["coolantReady"] as! Bool, notes: notes)
        return AnyView(ColdStorageTransferPanel(transfer: transfer,
            onAcknowledgementChange: { checked in onEvent("transfer.ack:\(transfer.id):\(checked ? "true" : "false")") },
            onRelease: { id in onEvent("transfer.release:\(id)") }))
    }
}
