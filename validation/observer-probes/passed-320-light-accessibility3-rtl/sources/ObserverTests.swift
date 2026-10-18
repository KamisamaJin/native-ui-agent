import XCTest
import UIKit

final class ObserverTests: XCTestCase {
    var app: XCUIApplication!
    var records: [[String: Any]] = []
    var steps: [[String: Any]] = []
    var issues: [String] = []
    var seen = Set<String>()
    var bottomReached = false
    var counter = 0
    var viewportFrame = CGRect.zero

    func decode(_ value: String) -> Any? { guard let data = value.data(using: .utf8) else { return nil }; return try? JSONSerialization.jsonObject(with: data) }
    func rect(_ frame: CGRect) -> [String: Double] { ["x": frame.origin.x, "y": frame.origin.y, "width": frame.width, "height": frame.height] }
    func receipt() -> [[String: Any]] { decode(app.staticTexts["__observer.receipt"].label) as? [[String: Any]] ?? [] }
    func runtime() -> [String: Any] { decode(app.staticTexts["__observer.runtime"].label) as? [String: Any] ?? [:] }
    func visible(_ e: XCUIElement) -> Bool {
        let intersection = e.frame.intersection(viewportFrame)
        return e.exists && !intersection.isNull && intersection.width > 0 && intersection.height > 0 && e.frame.width > 0 && e.frame.height > 0
    }
    func fullyVisible(_ e: XCUIElement) -> Bool {
        e.exists && e.frame.width > 0 && e.frame.height > 0 && viewportFrame.insetBy(dx: -0.5, dy: -0.5).contains(e.frame)
    }
    func capture(_ name: String) -> [String: Any] {
        let shot = app.screenshot()
        let attachment = XCTAttachment(screenshot: shot)
        attachment.name = String(format: "%03d-", counter) + name + ".png"; attachment.lifetime = .keepAlways; add(attachment)
        let viewport = viewportFrame
        let elements = app.descendants(matching: .any).allElementsBoundByIndex
        var nodes: [[String: Any]] = []
        for (i, e) in elements.enumerated() where e.exists {
            let isVisible = visible(e)
            let hittable = e.isHittable
            let enabled = e.isEnabled
            let full = fullyVisible(e)
            if full && (hittable || !enabled) && !e.identifier.isEmpty { seen.insert(e.identifier) }
            nodes.append(["index": i, "identifier": e.identifier, "label": e.label, "value": e.value.map { String(describing: $0) } ?? NSNull(),
                "role": String(describing: e.elementType), "role_raw": e.elementType.rawValue, "frame": rect(e.frame),
                "enabled": enabled, "selected": e.isSelected, "hittable": hittable, "intersects_viewport": isVisible, "fully_within_viewport": full])
        }
        let sentinel = app.staticTexts["__observer.bottom"]
        let reached = sentinel.exists && sentinel.isHittable && fullyVisible(sentinel)
        bottomReached = bottomReached || reached
        let cg = UIImage(data: shot.pngRepresentation)?.cgImage
        let record: [String: Any] = ["index": counter, "name": name, "screenshot_attachment": attachment.name!, "nodes": nodes,
            "runtime": runtime(), "callbacks": receipt(), "viewport": rect(viewport), "app_frame": rect(app.frame),
            "native_scroll_ax_frame": rect(app.scrollViews["__observer.scroll"].frame),
            "screenshot_pixels": ["width": cg?.width ?? 0, "height": cg?.height ?? 0],
            "bottom_sentinel_visible": reached]
        records.append(record); counter += 1; return record
    }
    func scroll(_ direction: String) {
        let down = direction != "up"
        let origin = app.coordinate(withNormalizedOffset: .zero)
        let start = origin.withOffset(CGVector(dx: viewportFrame.midX, dy: viewportFrame.minY + viewportFrame.height * (down ? 0.78 : 0.25)))
        let end = origin.withOffset(CGVector(dx: viewportFrame.midX, dy: viewportFrame.minY + viewportFrame.height * (down ? 0.28 : 0.75)))
        start.press(forDuration: 0.05, thenDragTo: end, withVelocity: .slow, thenHoldForDuration: 0.1)
        Thread.sleep(forTimeInterval: 0.2)
    }
    func select(_ identifier: String, allowMissing: Bool = false) -> XCUIElement? {
        let values = app.descendants(matching: .any).matching(identifier: identifier).allElementsBoundByIndex.filter { $0.exists }
        if allowMissing && values.isEmpty { return nil }
        guard values.count == 1 else { issues.append("identifier \(identifier) matched \(values.count) nodes; expected exactly one"); return nil }
        return values[0]
    }
    func reveal(_ identifier: String, maxSteps: Int, initialDirection: String, prefix: String) -> XCUIElement? {
        let limit = min(max(maxSteps, 1), 24)
        for n in 0...limit {
            let previousIssues = issues.count
            let target = select(identifier, allowMissing: true)
            if issues.count > previousIssues { return nil }
            if let target, fullyVisible(target) && (target.isHittable || !target.isEnabled) { return target }
            if let target, target.frame.height > viewportFrame.height + 0.5 || target.frame.width > viewportFrame.width + 0.5 {
                issues.append("reveal target \(identifier) is larger than the measured viewport"); return nil
            }
            if n == limit { break }
            var direction = initialDirection == "up" ? "up" : "down"
            if let target {
                if target.frame.minY < viewportFrame.minY { direction = "up" }
                else if target.frame.maxY > viewportFrame.maxY { direction = "down" }
            }
            scroll(direction); _ = capture("\(prefix)-reveal-\(n)-\(direction)")
        }
        issues.append("reveal target \(identifier) not fully visible/hittable after \(limit) native scroll steps")
        return nil
    }
    func testObserve() throws {
        continueAfterFailure = false
        let env = ProcessInfo.processInfo.environment
        guard let raw = env["OBSERVER_CONFIG_BASE64"], let data = Data(base64Encoded: raw),
              let config = try JSONSerialization.jsonObject(with: data) as? [String: Any] else { XCTFail("Missing fixture transport"); return }
        let actionData = Data(base64Encoded: env["OBSERVER_ACTIONS_BASE64"] ?? "") ?? Data("[]".utf8)
        let actions = try JSONSerialization.jsonObject(with: actionData) as? [[String: Any]] ?? []
        app = XCUIApplication(); app.launchEnvironment["OBSERVER_CONFIG_BASE64"] = raw; app.launch()
        XCTAssertTrue(app.scrollViews["__observer.scroll"].waitForExistence(timeout: 15))
        let originalRuntime = runtime()
        guard let viewport = originalRuntime["viewport"] as? [String: Double],
              let x = viewport["x"], let y = viewport["y"], let width = viewport["width"], let height = viewport["height"],
              width > 0 && height > 0 else { XCTFail("Native viewport geometry unavailable"); return }
        viewportFrame = CGRect(x: x, y: y, width: width, height: height)
        XCTAssertEqual(height, 600, accuracy: 0.5, "Native measured viewport must be 600 points")
        _ = capture("top")
        for (i, action) in actions.enumerated() {
            let before = capture("action-\(i)-before")
            let callbacksBefore = receipt().count
            let oldIndex = runtime()["fixture_index"] as? Int ?? -1
            let kind = action["type"] as? String ?? ""
            var outcome = "completed"
            var targetState: [String: Any] = [:]
            switch kind {
            case "tap":
                if let id = action["identifier"] as? String {
                    let target = action["reveal"] as? Bool == true
                        ? reveal(id, maxSteps: action["max_steps"] as? Int ?? 18, initialDirection: action["direction"] as? String ?? "down", prefix: "action-\(i)")
                        : select(id)
                    if let target {
                        targetState = ["identifier": id, "enabled": target.isEnabled, "selected": target.isSelected,
                                       "hittable": target.isHittable, "frame": rect(target.frame), "fully_within_viewport": fullyVisible(target)]
                        if !target.isEnabled && action["allow_disabled"] as? Bool == true && fullyVisible(target) {
                            outcome = "blocked_disabled"
                        } else if target.isEnabled && target.isHittable && fullyVisible(target) {
                            target.tap(); outcome = "tapped"
                        } else {
                            outcome = "unavailable"; issues.append("tap target \(id) is disabled, not hittable, or not fully within the viewport")
                        }
                    } else { outcome = "unavailable" }
                } else { outcome = "unavailable"; issues.append("tap missing identifier") }
            case "apply_next_fixture":
                let button = app.buttons["__observer.next"]
                if button.isEnabled && button.isHittable { button.tap() } else { issues.append("next fixture control unavailable") }
            case "scroll":
                if action["direction"] as? String == "auto", let id = action["until_identifier"] as? String {
                    _ = reveal(id, maxSteps: action["max_steps"] as? Int ?? 18, initialDirection: "down", prefix: "action-\(i)")
                    break
                }
                let maxSteps = min(max(action["max_steps"] as? Int ?? 1, 1), 24)
                for n in 0..<maxSteps {
                    if let id = action["until_identifier"] as? String,
                       let target = select(id, allowMissing: true), fullyVisible(target) && target.isHittable { break }
                    scroll(action["direction"] as? String ?? "down")
                    _ = capture("action-\(i)-scroll-\(n)")
                }
                if let id = action["until_identifier"] as? String,
                   let target = select(id), !(fullyVisible(target) && target.isHittable) { issues.append("scroll target \(id) not reached") }
            case "capture", "checkpoint": break
            default: issues.append("unsupported action \(kind)")
            }
            Thread.sleep(forTimeInterval: 0.15)
            let after = capture(action["name"] as? String ?? "action-\(i)-after")
            let now = runtime()
            let sameProcess = (now["pid"] as? Int == originalRuntime["pid"] as? Int) && (now["instance"] as? String == originalRuntime["instance"] as? String)
            if !sameProcess { issues.append("app process identity changed") }
            if kind == "apply_next_fixture" && now["fixture_index"] as? Int != oldIndex + 1 { issues.append("fixture index did not advance explicitly") }
            let delta = Array(receipt().dropFirst(callbacksBefore))
            if outcome == "blocked_disabled" && !delta.isEmpty { issues.append("disabled target unexpectedly emitted callbacks") }
            if let expected = action["expect_callback"] as? String, !delta.contains(where: { $0["event"] as? String == expected }) {
                issues.append("expected real callback \(expected) was not received")
            }
            steps.append(["action": action, "outcome": outcome, "target": targetState, "before": before["index"]!, "after": after["index"]!, "callback_delta": delta, "same_process": sameProcess])
        }
        let maxScrolls = min(max(config["max_scrolls"] as? Int ?? 18, 1), 40)
        for n in 0..<maxScrolls {
            let sentinel = app.staticTexts["__observer.bottom"]
            if sentinel.exists && sentinel.isHittable && fullyVisible(sentinel) { bottomReached = true; break }
            scroll("down"); _ = capture("coverage-scroll-\(n)")
        }
        _ = capture("bottom")
        let required = config["required_identifiers"] as? [String] ?? []
        let missing = required.filter { !seen.contains($0) }
        if !bottomReached { issues.append("bottom sentinel not reached; lower content coverage incomplete") }
        if !missing.isEmpty { issues.append("required identifiers never visible: \(missing.joined(separator: ", "))") }
        let result: [String: Any] = ["schema_version": 1, "measurement_kind": "XCUIElement runtime accessibility; frames in logical screen points",
            "snapshots": records, "steps": steps, "coverage": ["bottom_reached": bottomReached, "required_identifiers": required, "missing_identifiers": missing, "observed_identifiers": seen.sorted()],
            "issues": issues, "status": issues.isEmpty ? "passed" : "failed", "original_runtime": originalRuntime]
        let resultAttachment = XCTAttachment(data: try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]), uniformTypeIdentifier: "public.json")
        resultAttachment.name = "observer-result.json"; resultAttachment.lifetime = .keepAlways; add(resultAttachment)
        XCTAssertTrue(issues.isEmpty, issues.joined(separator: "; "))
    }
}
