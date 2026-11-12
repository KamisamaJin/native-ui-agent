// Thin fixture decoder only; this file contains no business UI or local state.
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let input = TrainingPathwayInput(
            entityID: fixture["entityID"] as! String,
            revision: fixture["revision"] as! Int,
            title: fixture["title"] as! String,
            context: fixture["context"] as! String,
            notes: fixture["notes"] as! [String],
            completedHours: fixture["completedHours"] as! Int,
            completedModules: fixture["completedModules"] as! [String],
            cohortSeats: fixture["cohortSeats"] as! Int,
            deviceCredits: fixture["deviceCredits"] as! Int,
            assessmentSlots: fixture["assessmentSlots"] as! Int,
            practiceSeats: fixture["practiceSeats"] as! Int
        )
        return AnyView(TrainingPathwayEnrollment(input: input, onEvent: onEvent))
    }
}
