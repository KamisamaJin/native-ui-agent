import Foundation
let input = FileHandle.standardInput.readDataToEndOfFile()
let object = try JSONSerialization.jsonObject(with: input) as! [String: Any]
let vectors = object["vectors"] as! [[String: Any]]
var results: [[String: Any]] = []
for vector in vectors {
    let data = try JSONSerialization.data(withJSONObject: vector["model"]!, options: [.sortedKeys])
    results.append(["id": vector["id"]!, "utf8_base64": data.base64EncodedString()])
}
let output = try JSONSerialization.data(withJSONObject: ["version": 1, "producer": "Foundation.JSONSerialization.sortedKeys", "results": results], options: [.sortedKeys])
FileHandle.standardOutput.write(output)
