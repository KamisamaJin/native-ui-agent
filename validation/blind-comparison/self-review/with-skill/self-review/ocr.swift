import Foundation
import Vision
import AppKit
var records = [[String:Any]]()
for input in CommandLine.arguments.dropFirst() {
    let url = URL(fileURLWithPath: input)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    let handler = VNImageRequestHandler(url: url, options: [:])
    do {
        try handler.perform([request])
        let texts: [[String:Any]] = (request.results ?? []).compactMap { result in
            guard let candidate = result.topCandidates(1).first else { return nil }
            let b = result.boundingBox
            return ["text":candidate.string,"confidence":candidate.confidence,
                    "normalized_bounds_bottom_left":[b.minX,b.minY,b.maxX,b.maxY]]
        }
        records.append(["image":input,"method":"Apple Vision accurate text recognition on fresh native PNG; bounds are OCR glyph boxes, not SwiftUI frames","texts":texts])
    } catch { records.append(["image":input,"error":String(describing:error)]) }
}
let data = try JSONSerialization.data(withJSONObject: records, options: [.prettyPrinted,.sortedKeys])
FileHandle.standardOutput.write(data)
