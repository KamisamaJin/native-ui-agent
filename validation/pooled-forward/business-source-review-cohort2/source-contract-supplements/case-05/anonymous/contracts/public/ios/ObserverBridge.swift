// Thin fixture decoder only; this file contains no business UI or local state.
import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let input = CandidateDispositionInput(
            entityID: fixture["entityID"] as! String,
            revision: fixture["revision"] as! Int,
            title: fixture["title"] as! String,
            context: fixture["context"] as! String,
            notes: fixture["notes"] as! [String],
            portfolioScore: fixture["portfolioScore"] as! Int,
            reviewerCapacity: fixture["reviewerCapacity"] as! Int,
            technicalSlots: fixture["technicalSlots"] as! Int,
            recruiterSlots: fixture["recruiterSlots"] as! Int,
            legalHold: fixture["legalHold"] as! Bool,
            assessmentCount: fixture["assessmentCount"] as! Int,
            openRoleCount: fixture["openRoleCount"] as! Int
        )
        return AnyView(CandidateDispositionReview(input: input, onEvent: onEvent))
    }
}
