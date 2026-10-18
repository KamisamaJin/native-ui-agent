import Foundation
import Vision
import AppKit
var all: [[String:Any]] = []
for name in CommandLine.arguments.dropFirst() {
 let url=URL(fileURLWithPath:name)
 let req=VNRecognizeTextRequest()
 req.recognitionLevel = .accurate
 try VNImageRequestHandler(url:url).perform([req])
 let observations=(req.results ?? []).compactMap { item -> [String:Any]? in
  guard let text=item.topCandidates(1).first else {return nil}
  let box=item.boundingBox
  return ["text":text.string,"confidence":text.confidence,"bounds_normalized_bottom_origin":[box.minX,box.minY,box.width,box.height]]
 }
 all.append(["image":name,"observations":observations])
}
let data=try JSONSerialization.data(withJSONObject:all,options:[.prettyPrinted,.sortedKeys])
FileHandle.standardOutput.write(data)
