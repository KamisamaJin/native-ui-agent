import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let chapters = (fixture["chapters"] as! [[String: Any]]).map {
            AudioTourChapter(id: $0["id"] as! String, title: $0["title"] as! String, body: $0["body"] as! String)
        }
        let tour = OfflineAudioTour(id: fixture["id"] as! String,
            title: fixture["title"] as! String, language: fixture["language"] as! String,
            downloadSizeMB: fixture["downloadSizeMB"] as! Int, availableMB: fixture["availableMB"] as! Int,
            meteredConnection: fixture["meteredConnection"] as! Bool, chapters: chapters)
        return AnyView(OfflineAudioTourPanel(tour: tour,
            onWifiOnlyChange: { wifiOnly in onEvent("audio.wifiOnly:\(tour.id):\(wifiOnly ? "true" : "false")") },
            onDownload: { id, wifiOnly in onEvent("audio.download:\(id):\(wifiOnly ? "wifi" : "mobile")") }))
    }
}
