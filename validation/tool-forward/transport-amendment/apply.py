#!/usr/bin/env python3
"""Identical non-finite JSON transport repair for each frozen observer bundle."""
import argparse,shutil
from pathlib import Path
HELPER='''    var nonFiniteNumbers: [[String: String]] = []
    func jsonSafe(_ value: Any, path: String = "$" ) -> Any {
        if let number = value as? NSNumber, !number.doubleValue.isFinite {
            nonFiniteNumbers.append(["path": path, "native_value": String(describing: number), "status": "unavailable_non_finite"])
            return NSNull()
        }
        if let dictionary = value as? [String: Any] {
            return dictionary.mapValues { entry in entry } .reduce(into: [String: Any]()) { result, entry in
                result[entry.key] = jsonSafe(entry.value, path: path + "." + entry.key)
            }
        }
        if let values = value as? [Any] { return values.enumerated().map { jsonSafe($0.element, path: path + "[\\($0.offset)]") } }
        return value
    }
'''
def apply(bundle):
 p=bundle/'assets/ios-observer/ObserverTests.swift';s=p.read_text();assert 'func jsonSafe'not in s
 s=s.replace('    func testObserve() throws {',HELPER+'    func testObserve() throws {')
 old='let resultAttachment = XCTAttachment(data: try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]), uniformTypeIdentifier: "public.json")'
 new='var export = jsonSafe(result) as! [String: Any]\n        export["serialization_diagnostics"] = nonFiniteNumbers\n        let resultAttachment = XCTAttachment(data: try JSONSerialization.data(withJSONObject: export, options: [.prettyPrinted, .sortedKeys]), uniformTypeIdentifier: "public.json")'
 assert old in s;s=s.replace(old,new);p.write_text(s)
 p=bundle/'scripts/ios_observe.py';s=p.read_text();assert '\nimport math\n'not in s;s=s.replace('\nimport json\n','\nimport json\nimport math\n')
 marker='    if app_frame["width"] <= 0 or app_frame["height"] <= 0:'
 replacement='''    # Invalid native geometry is unavailable; never coerce it to zero pixels.
    if any(not isinstance(app_frame.get(k), (int, float)) or not math.isfinite(app_frame[k]) for k in ("x", "y", "width", "height")):
        raise ValueError("App frame must be finite")
    if any(not isinstance(frame.get(k), (int, float)) or not math.isfinite(frame[k]) for k in ("x", "y", "width", "height")):
        return None
'''+marker
 assert marker in s;s=s.replace(marker,replacement);p.write_text(s)
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();shutil.copytree(a.source,a.output,ignore=shutil.ignore_patterns('__pycache__','*.pyc'));apply(a.output)
if __name__=='__main__':main()
