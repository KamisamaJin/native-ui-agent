// Thin fixture decoder only; this file contains no business UI or local state.
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let input = CateringPackageInput(
            entityID: fixture["entityID"] as! String,
            revision: fixture["revision"] as! Int,
            title: fixture["title"] as! String,
            context: fixture["context"] as! String,
            notes: fixture["notes"] as! [String],
            guestCount: fixture["guestCount"] as! Int,
            vegetarianGuests: fixture["vegetarianGuests"] as! Int,
            vegetarianMeals: fixture["vegetarianMeals"] as! Int,
            buffetCapacity: fixture["buffetCapacity"] as! Int,
            boxedCapacity: fixture["boxedCapacity"] as! Int,
            reusableSets: fixture["reusableSets"] as! Int,
            compostableSets: fixture["compostableSets"] as! Int
        )
        return AnyView(CateringPackagePlanner(input: input, onEvent: onEvent))
    }
}
