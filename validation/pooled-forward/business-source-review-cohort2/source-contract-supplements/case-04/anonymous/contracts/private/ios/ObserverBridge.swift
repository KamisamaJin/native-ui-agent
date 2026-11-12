// Thin fixture decoder only; this file contains no business UI or local state.
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let input = VisitorAccessInput(
            entityID: fixture["entityID"] as! String,
            revision: fixture["revision"] as! Int,
            title: fixture["title"] as! String,
            context: fixture["context"] as! String,
            notes: fixture["notes"] as! [String],
            guestCount: fixture["guestCount"] as! Int,
            sponsorActive: fixture["sponsorActive"] as! Bool,
            badgeTrainingComplete: fixture["badgeTrainingComplete"] as! Bool,
            researchCapacity: fixture["researchCapacity"] as! Int,
            officeCapacity: fixture["officeCapacity"] as! Int,
            verifiedIDs: fixture["verifiedIDs"] as! Int,
            labInductions: fixture["labInductions"] as! Int,
            escortCount: fixture["escortCount"] as! Int
        )
        return AnyView(VisitorAccessPreclearance(input: input, onEvent: onEvent))
    }
}
