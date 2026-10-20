import SwiftUI
#if canImport(AlertToast)
import AlertToast
#endif

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        do {
            let data = try JSONSerialization.data(withJSONObject: fixture, options: [.sortedKeys])
            let catalog = try JSONDecoder().decode(WorkshopCatalog.self, from: data)
            return AnyView(WorkshopEnrollmentCard(catalog: catalog) { reservation in
                onEvent("reserve:\(reservation.courseID):\(reservation.mode.rawValue):\(reservation.seats):\(reservation.workbook ? "true" : "false")")
            })
        } catch {
            return AnyView(Text("Fixture decoding failed: \(error.localizedDescription)"))
        }
    }
}
