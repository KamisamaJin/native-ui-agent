import SwiftUI
import AlertToast

public enum ObserverBridge {
    public static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let host = fixture["host"] as! [String: Any]
        let index = fixture["activeModelIndex"] as? Int ?? 0
        let raw = (fixture["model"] as? [String: Any]) ?? (fixture["models"] as! [[String: Any]])[index]
        let jobs = (raw["jobs"] as! [[String: Any]]).map { j in
            PrintBatchJob(id: j["id"] as! String, title: j["title"] as! String, pages: j["pages"] as! Int, copies: j["copies"] as! Int, isColor: j["isColor"] as! Bool, selected: j["selected"] as! Bool, locked: j["locked"] as! Bool)
        }
        let model = PrintBatchModel(modelID: raw["modelID"] as! String, budgetCredits: raw["budgetCredits"] as! Int, allowPriority: raw["allowPriority"] as! Bool, initialPaperMode: raw["initialPaperMode"] as! String, initialPriority: raw["initialPriority"] as! Bool, initialExpanded: raw["initialExpanded"] as! Bool, jobs: jobs)
        let presentation = PrintBatchPresentation(isDark: host["theme"] as! String == "dark", textScale: (host["textScale"] as! NSNumber).doubleValue, isRTL: host["direction"] as! String == "rtl")
        return AnyView(PrintBatchApprovalCard(model: model, presentation: presentation) { name, payload in
            let envelope: [String: Any] = ["name": name, "payload": payload]
            if let data = try? JSONSerialization.data(withJSONObject: envelope, options: [.sortedKeys]), let line = String(data: data, encoding: .utf8) { onEvent(line) }
        })
    }
}
