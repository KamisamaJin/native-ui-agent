import Foundation
import Vision
import ImageIO

let input=URL(fileURLWithPath:CommandLine.arguments[1])
let output=URL(fileURLWithPath:CommandLine.arguments[2])
guard let source=CGImageSourceCreateWithURL(input as CFURL,nil),
      let image=CGImageSourceCreateImageAtIndex(source,0,nil) else {fatalError("Cannot decode image")}
let request=VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.automaticallyDetectsLanguage = true
try VNImageRequestHandler(cgImage:image).perform([request])
let rows=(request.results ?? []).compactMap { item -> [String:Any]? in
    guard let text=item.topCandidates(1).first else{return nil}
    let box=item.boundingBox
    return ["text":text.string,"confidence":text.confidence,
            "bounds_px":[box.minX*Double(image.width),(1-box.maxY)*Double(image.height),
                         box.maxX*Double(image.width),(1-box.minY)*Double(image.height)]]
}
try JSONSerialization.data(withJSONObject:["method":"Apple Vision OCR; glyph boxes, not layout/style properties",
    "width":image.width,"height":image.height,"rows":rows],options:[.prettyPrinted,.sortedKeys]).write(to:output)
