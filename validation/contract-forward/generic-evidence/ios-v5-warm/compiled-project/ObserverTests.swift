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
    var revealDiagnostics: [[String: Any]] = []
    var observationTargets: [[String: Any]] = []
    var stateCaptures: [[String: Any]] = []
    var activeState = "initial"
    var stateCaptureEnabled = false
    var currentActionIndex = -1
    var sweepLimit = 40
    var traceRevealImages = false
    func key(_ value: [String: Any]) -> String {
        String(data: (try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])) ?? Data(), encoding: .utf8) ?? ""
    }
    func binding() -> [String: Any] {
        let r = runtime()
        return ["pid": r["pid"] ?? NSNull(), "instance": r["instance"] ?? NSNull(),
                "fixture_index": r["fixture_index"] ?? NSNull(), "input_sha256": r["input_sha256"] ?? NSNull(),
                "event_revision": r["event_revision"] ?? NSNull()]
    }
    func frame(_ value: Any?) -> CGRect {
        guard let d = value as? [String: Double] else { return .zero }
        return CGRect(x: d["x"] ?? 0, y: d["y"] ?? 0, width: d["width"] ?? 0, height: d["height"] ?? 0)
    }
    func role(_ name: String) -> XCUIElement.ElementType? {
        switch name.lowercased() {
        case "button": return .button
        case "switch": return .switch
        case "other": return .other
        case "statictext", "text": return .staticText
        default: return nil
        }
    }
    func matches(_ selector: [String: Any]) -> [XCUIElement] {
        let type = (selector["role"] as? String).flatMap { role($0) } ?? .any
        let query = app.descendants(matching: type)
        if let id = selector["identifier"] as? String, !id.isEmpty { return query.matching(identifier: id).allElementsBoundByIndex.filter { $0.exists } }
        if let label = selector["label"] as? String, !label.isEmpty { return query.matching(NSPredicate(format: "label == %@", label)).allElementsBoundByIndex.filter { $0.exists } }
        return []
    }
    func selectTarget(_ selector: [String: Any], allowMissing: Bool = false) -> XCUIElement? {
        let values = matches(selector)
        if allowMissing && values.isEmpty { return nil }
        guard values.count == 1 else { issues.append("selector \(key(selector)) matched \(values.count) nodes; expected exactly one"); return nil }
        return values[0]
    }
    func selector(_ action: [String: Any]) -> [String: Any] {
        action["target"] as? [String: Any] ?? ["identifier": action["identifier"] as? String ?? ""]
    }
    func controls(_ semantic: XCUIElement) -> [(XCUIElement, [String: Any])] {
        var candidates: [(XCUIElement, [String: Any])] = []
        // A nested Button can have its own action. Only a Switch's native
        // wrapper/leaf duplication is collapsed; never discard an activatable
        // Button merely because another control occurs below it.
        if semantic.elementType == .button {
            candidates.append((semantic, ["relation": "self_native_control", "role_raw": semantic.elementType.rawValue]))
        }
        for t: XCUIElement.ElementType in [.button, .switch] {
            for (i, e) in semantic.descendants(matching: t).allElementsBoundByIndex.enumerated() where e.exists {
                if t == .button || (e.descendants(matching: .button).count == 0 && e.descendants(matching: .switch).count == 0) {
                    candidates.append((e, ["relation": "native_descendant", "role_raw": t.rawValue, "index": i]))
                }
            }
        }
        if candidates.isEmpty && semantic.elementType == .switch {
            return [(semantic, ["relation": "self_native_control", "role_raw": semantic.elementType.rawValue])]
        }
        return candidates
    }
    func group(_ selector: [String: Any]) -> [String: Any] {
        let found = matches(selector)
        guard found.count == 1 else { return ["selector": selector, "match_count": found.count, "resolution": found.isEmpty ? "missing" : "ambiguous_semantic"] }
        let semantic = found[0]
        if !visible(semantic) { return ["selector": selector, "match_count": 1, "resolution": "offscreen_not_resolved", "semantic": ["identifier": semantic.identifier, "intersects_viewport": false]] }
        let leaves = controls(semantic)
        var out: [String: Any] = ["selector": selector, "match_count": 1, "semantic": nativeState(semantic, path: ["selector": selector]),
          "resolution": leaves.count == 1 ? "unique_native_control" : leaves.isEmpty ? "no_native_control" : "ambiguous_native_controls",
          "native_control_count": leaves.count, "candidates": leaves.map { nativeState($0.0, path: $0.1) }]
        if leaves.count == 1 { out["control"] = nativeState(leaves[0].0, path: leaves[0].1) }
        return out
    }
    func usablePoint(_ target: XCUIElement) -> CGPoint? {
        let intersection = target.frame.intersection(viewportFrame.insetBy(dx: 1, dy: 1))
        guard target.exists && target.isHittable && !intersection.isNull && intersection.width >= 4 && intersection.height >= 4 else { return nil }
        return CGPoint(x: intersection.midX, y: intersection.midY)
    }
    func actionable(_ semantic: XCUIElement) -> Bool {
        let leaves = controls(semantic)
        guard leaves.count == 1 else { return false }
        let actual = leaves[0].0
        return revealed(actual) && (usablePoint(actual) != nil || (!actual.isEnabled && visible(actual)))
    }
    func revealed(_ target: XCUIElement) -> Bool {
        let fits = target.frame.height <= viewportFrame.height && target.frame.width <= viewportFrame.width
        return fits ? fullyVisible(target) : visible(target)
    }
    func sweep(_ state: String, maxSteps: Int? = nil) {
        let limit = min(max(maxSteps ?? sweepLimit, 1), 80)
        activeState = state
        guard frame(runtime()["content_frame"]).height > 0 else { issues.append("native content geometry unavailable for state \(state)"); return }
        let original = binding(), first = records.count
        var trace: [[String: Any]] = []
        for n in 0..<limit {
            let content = frame(runtime()["content_frame"]), offset = viewportFrame.minY - content.minY
            if offset <= 0.5 { break }
            trace.append(["direction": "up", "offset_before": offset, "step": n])
            scroll("up", fraction: 0.65)
        }
        var intervals: [[Double]] = [], heights: [Double] = [], drift = false
        var sawTop = false, sawBottom = false
        var seenTargets = Set<String>()
        for n in 0...limit {
            let snap = capture("state-\(state)-scroll-\(n)")
            let content = frame((snap["runtime"] as? [String: Any])?["content_frame"])
            let offset = Double(viewportFrame.minY - content.minY), h = Double(content.height)
            heights.append(h); intervals.append([max(0, offset), min(h, offset + Double(viewportFrame.height))])
            sawTop = sawTop || offset <= 0.5
            sawBottom = sawBottom || (snap["bottom_sentinel_visible"] as? Bool == true)
            if key(binding()) != key(original) { drift = true }
            for target in observationTargets {
                let values = matches(target)
                if values.count == 1 && visible(values[0]) { seenTargets.insert(key(target)) }
            }
            if sawBottom { break }
            if n < limit { scroll("down", fraction: 0.45) }
        }
        let sorted = intervals.sorted { $0[0] < $1[0] }
        var end = 0.0, maxGap = 0.0
        for interval in sorted { maxGap = max(maxGap, interval[0] - end); end = max(end, interval[1]) }
        let height = heights.max() ?? 0
        let stableHeight = (heights.max() ?? 0) - (heights.min() ?? 0) <= 1
        let complete = sawTop && sawBottom && !drift && stableHeight && height > 0 && maxGap <= 1 && end >= height - 1
        stateCaptures.append(["state_id": state, "after_action": currentActionIndex, "binding": original, "snapshot_indices": Array(first..<records.count),
            "intervals": intervals, "content_height": height, "top_reached": sawTop, "bottom_reached": sawBottom,
            "max_gap": maxGap, "stable_binding": !drift, "stable_height": stableHeight, "complete": complete,
            "observed_targets": observationTargets.filter { seenTargets.contains(key($0)) }, "return_trace": trace,
            "scope": "Actual overlapping pixels for this input/event epoch; not a style or business pass."])
        if !complete { issues.append("state \(state) incomplete overlapping full-content coverage") }
    }

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
        let started = ProcessInfo.processInfo.systemUptime
        // One public native snapshot carries real AX ancestry and attributes.
        // Do not turn every exported property into another remote XCUI query.
        let tree: XCUIElementSnapshot?
        do { tree = try app.snapshot() }
        catch { issues.append("native snapshot unavailable: \(error)"); tree = nil }
        var native: [XCUIElementSnapshot] = [], parents: [Int] = []
        func visit(_ node: XCUIElementSnapshot, parent: Int) {
            let index = native.count; native.append(node); parents.append(parent)
            for child in node.children { visit(child, parent: index) }
        }
        if let tree { visit(tree, parent: -1) }
        let treeFinished = ProcessInfo.processInfo.systemUptime
        let shot = app.screenshot()
        let attachment = XCTAttachment(screenshot: shot)
        attachment.name = String(format: "%03d-", counter) + name + ".png"; attachment.lifetime = .keepAlways; add(attachment)
        let viewport = viewportFrame
        var nodes: [[String: Any]] = []
        for (i, e) in native.enumerated() {
            let intersection = e.frame.intersection(viewport)
            let isVisible = !intersection.isNull && intersection.width > 0 && intersection.height > 0 && e.frame.width > 0 && e.frame.height > 0
            let full = e.frame.width > 0 && e.frame.height > 0 && viewport.insetBy(dx: -0.5, dy: -0.5).contains(e.frame)
            if isVisible && !e.identifier.isEmpty { seen.insert(e.identifier) }
            nodes.append(["index": i, "parent_index": parents[i], "identifier": e.identifier, "label": e.label, "value": e.value.map { String(describing: $0) } ?? NSNull(),
                "role": String(describing: e.elementType), "role_raw": e.elementType.rawValue, "frame": rect(e.frame),
                "enabled": e.isEnabled, "selected": e.isSelected, "hittable": NSNull(), "hittable_measured": false, "intersects_viewport": isVisible, "fully_within_viewport": full])
        }
        let r = nodes.first { $0["identifier"] as? String == "__observer.runtime" }.flatMap { decode($0["label"] as? String ?? "") as? [String: Any] } ?? [:]
        let callbacks = nodes.first { $0["identifier"] as? String == "__observer.receipt" }.flatMap { decode($0["label"] as? String ?? "") as? [[String: Any]] } ?? []
        let b: [String: Any] = ["pid": r["pid"] ?? NSNull(), "instance": r["instance"] ?? NSNull(), "fixture_index": r["fixture_index"] ?? NSNull(), "input_sha256": r["input_sha256"] ?? NSNull(), "event_revision": r["event_revision"] ?? NSNull()]
        let reached = nodes.contains { $0["identifier"] as? String == "__observer.bottom" && $0["fully_within_viewport"] as? Bool == true }
        bottomReached = bottomReached || reached
        let cg = UIImage(data: shot.pngRepresentation)?.cgImage
        // Keep the image tied to the snapshot's native epoch. A fast tree must
        // not relabel an older hierarchy with a newer caller input or event.
        let afterImage = runtime()
        let afterImageBinding: [String: Any] = ["pid": afterImage["pid"] ?? NSNull(), "instance": afterImage["instance"] ?? NSNull(),
            "fixture_index": afterImage["fixture_index"] ?? NSNull(), "input_sha256": afterImage["input_sha256"] ?? NSNull(), "event_revision": afterImage["event_revision"] ?? NSNull()]
        let beforeGeometry = frame(r["content_frame"]), afterGeometry = frame(afterImage["content_frame"])
        let consistent = key(b) == key(afterImageBinding) && beforeGeometry.height > 0
            && abs(beforeGeometry.minY - afterGeometry.minY) <= 0.5 && abs(beforeGeometry.height - afterGeometry.height) <= 0.5
        func snapshotGroup(_ wanted: [String: Any]) -> [String: Any] {
            let found = nodes.indices.filter { index in
                let n = nodes[index]
                let identity = wanted["identifier"] as? String
                let label = wanted["label"] as? String
                return (identity != nil ? n["identifier"] as? String == identity : label != nil && n["label"] as? String == label)
                    && ((wanted["role"] as? String).flatMap { role($0) }.map { $0 == native[index].elementType } ?? true)
            }
            guard found.count == 1 else { return ["selector": wanted, "match_count": found.count, "resolution": found.isEmpty ? "missing" : "ambiguous_semantic"] }
            let index = found[0], semantic = nodes[index]
            guard semantic["intersects_viewport"] as? Bool == true else { return ["selector": wanted, "match_count": 1, "semantic": semantic, "resolution": "offscreen_not_resolved"] }
            func descendants(_ n: Int) -> [Int] {
                nodes.indices.filter { child in
                    var cursor = parents[child]
                    while cursor >= 0 { if cursor == n { return true }; cursor = parents[cursor] }
                    return false
                }
            }
            var candidates: [Int] = native[index].elementType == .button ? [index] : []
            for child in descendants(index) {
                if native[child].elementType == .button { candidates.append(child) }
                else if native[child].elementType == .switch && !descendants(child).contains(where: { native[$0].elementType == .button || native[$0].elementType == .switch }) { candidates.append(child) }
            }
            if candidates.isEmpty && native[index].elementType == .switch { candidates = [index] }
            var value: [String: Any] = ["selector": wanted, "match_count": 1, "semantic": semantic, "native_control_count": candidates.count,
                "candidates": candidates.map { nodes[$0] }, "resolution": candidates.count == 1 ? "unique_native_control" : candidates.isEmpty ? "no_native_control" : "ambiguous_native_controls"]
            if candidates.count == 1 { value["control"] = nodes[candidates[0]] }
            return value
        }
        let record: [String: Any] = ["index": counter, "name": name, "screenshot_attachment": attachment.name!, "nodes": nodes,
            "runtime": r, "callbacks": callbacks, "viewport": rect(viewport), "app_frame": rect(tree?.frame ?? app.frame),
            "native_scroll_ax_frame": nodes.first { $0["identifier"] as? String == "__observer.scroll" }?["frame"] ?? NSNull(),
            "screenshot_pixels": ["width": cg?.width ?? 0, "height": cg?.height ?? 0],
            "state_id": activeState, "binding": b, "control_groups": observationTargets.map { snapshotGroup($0) },
            "binding_after_capture": afterImageBinding, "capture_consistent": consistent,
            "performance": ["ax_snapshot_seconds": treeFinished - started, "capture_seconds": ProcessInfo.processInfo.systemUptime - started, "native_query_mode": "single_public_snapshot", "hittable_scope": "actual_dispatch_target_only"] as [String: Any],
            "bottom_sentinel_visible": reached]
        records.append(record); counter += 1; return record
    }
    func scroll(_ direction: String, fraction: Double = 0.5) {
        let down = direction != "up"
        let origin = app.coordinate(withNormalizedOffset: .zero)
        let distance = min(max(fraction, 0.025), 0.7)
        let startY = down ? 0.85 : 0.15
        let endY = down ? startY - distance : startY + distance
        let start = origin.withOffset(CGVector(dx: viewportFrame.midX - app.frame.minX, dy: viewportFrame.minY - app.frame.minY + viewportFrame.height * startY))
        let end = origin.withOffset(CGVector(dx: viewportFrame.midX - app.frame.minX, dy: viewportFrame.minY - app.frame.minY + viewportFrame.height * endY))
        start.press(forDuration: 0.05, thenDragTo: end, withVelocity: .slow, thenHoldForDuration: 0.1)
        Thread.sleep(forTimeInterval: 0.2)
    }
    func select(_ identifier: String, allowMissing: Bool = false) -> XCUIElement? {
        let values = app.descendants(matching: .any).matching(identifier: identifier).allElementsBoundByIndex.filter { $0.exists }
        if allowMissing && values.isEmpty { return nil }
        guard values.count == 1 else { issues.append("identifier \(identifier) matched \(values.count) nodes; expected exactly one"); return nil }
        return values[0]
    }
    func nativeState(_ target: XCUIElement, path: [String: Any]) -> [String: Any] {
        ["identifier": target.identifier, "label": target.label, "value": target.value.map { String(describing: $0) } ?? NSNull(),
         "role": String(describing: target.elementType), "role_raw": target.elementType.rawValue,
         "enabled": target.isEnabled, "selected": target.isSelected, "hittable": target.isHittable,
         "frame": rect(target.frame), "intersects_viewport": visible(target), "fully_within_viewport": fullyVisible(target), "path": path]
    }
    func activation(_ semantic: XCUIElement) -> (XCUIElement, [String: Any])? {
        let leaves = controls(semantic)
        guard leaves.count == 1 else { issues.append("activation requires one native control; found \(leaves.count)"); return nil }
        return leaves[0]
    }
    func unavailable(_ identifier: String, reason: String, direction: String, scrolls: Int, present: Bool, sentinel: XCUIElement? = nil, recordIssue: Bool = true) {
        var diagnostic: [String: Any] = ["identifier": identifier, "classification": present ? "unavailable" : "unobserved",
            "reason": reason, "direction": direction, "scroll_steps": scrolls, "native_target_present": present,
            "evidence_snapshot_index": records.last?["index"] ?? NSNull(),
            "scope": "bounded observer search; not proof of product absence"]
        if let sentinel {
            diagnostic["native_boundary"] = nativeState(sentinel, path: ["selector": "application.staticTexts", "identifier": "__observer.bottom"])
        }
        revealDiagnostics.append(diagnostic)
        if recordIssue { issues.append("observer target \(identifier) \(present ? "unavailable" : "unobserved"): \(reason), after \(scrolls) native scroll steps") }
    }
    func revealTarget(_ selector: [String: Any], maxSteps: Int, initialDirection: String, prefix: String, requireControl: Bool = true, centerOversized: Bool = false, recordFailure: Bool = true) -> XCUIElement? {
        let limit = min(max(maxSteps, 1), 40)
        var fraction = 0.45, lastDirection = "", lastOffset: Double? = nil, stationary = 0
        for n in 0...limit {
            let found = matches(selector)
            if found.count > 1 { if recordFailure { issues.append("ambiguous semantic selector \(key(selector))") }; return nil }
            let target = found.first
            if let target {
                let f = target.frame
                let fits = f.height <= viewportFrame.height && f.width <= viewportFrame.width
                let observed = !centerOversized || fits ? revealed(target) : visible(target) && viewportFrame.contains(CGPoint(x: f.midX, y: f.midY))
                if requireControl ? actionable(target) : observed { return target }
            }
            var direction = initialDirection == "up" ? "up" : "down"
            if let target {
                let leaves = requireControl ? controls(target) : [], f = leaves.count == 1 ? leaves[0].0.frame : target.frame
                if f.midY < viewportFrame.midY { direction = "up" } else { direction = "down" }
            }
            if !lastDirection.isEmpty && direction != lastDirection { fraction = max(0.025, fraction / 2) }
            let content = frame(runtime()["content_frame"]), offset = Double(viewportFrame.minY - content.minY)
            if let previous = lastOffset, abs(offset - previous) < 0.5 { stationary += 1 } else { stationary = 0 }
            let atBottom = app.staticTexts["__observer.bottom"].exists && fullyVisible(app.staticTexts["__observer.bottom"])
            if n == limit || stationary >= 3 || (target == nil && direction == "down" && atBottom) {
                unavailable(key(selector), reason: n == limit ? "reveal_step_limit_reached" : stationary >= 3 ? "native_scroll_stationary" : "native_bottom_boundary_target_unobserved", direction: direction, scrolls: n, present: target != nil, recordIssue: recordFailure)
                return nil
            }
            revealDiagnostics.append(["selector": selector, "step": n, "direction": direction, "fraction": fraction, "offset_before": offset, "target_present": target != nil])
            lastDirection = direction; lastOffset = offset
            scroll(direction, fraction: fraction)
            if traceRevealImages { _ = capture("\(prefix)-reveal-\(n)-\(direction)") }
        }
        return nil
    }
    func reveal(_ identifier: String, maxSteps: Int, initialDirection: String, prefix: String) -> XCUIElement? {
        revealTarget(["identifier": identifier], maxSteps: maxSteps, initialDirection: initialDirection, prefix: prefix, requireControl: false)
    }
    func targetEvidence(_ wanted: [String: Any], indices: [Int], epoch: [String: Any]) -> [String: Any] {
        var observed: [Int] = [], full: [Int] = [], ambiguous = false
        for index in indices {
            let snapshot = records[index]
            guard key(snapshot["binding"] as? [String: Any] ?? [:]) == key(epoch), snapshot["capture_consistent"] as? Bool == true else { continue }
            let groups = snapshot["control_groups"] as? [[String: Any]] ?? []
            guard let group = groups.first(where: { key($0["selector"] as? [String: Any] ?? [:]) == key(wanted) }) else { continue }
            if group["match_count"] as? Int != 1 { ambiguous = ambiguous || (group["match_count"] as? Int ?? 0) > 1; continue }
            guard let node = group["semantic"] as? [String: Any], node["intersects_viewport"] as? Bool == true else { continue }
            let f = frame(node["frame"])
            if node["fully_within_viewport"] as? Bool == true { observed.append(index); full.append(index) }
            else if (f.height > viewportFrame.height || f.width > viewportFrame.width) && viewportFrame.contains(CGPoint(x: f.midX, y: f.midY)) { observed.append(index) }
        }
        return ["selector": wanted, "status": observed.isEmpty ? "unavailable" : "observed", "snapshot_indices": observed,
                "fully_visible": !full.isEmpty, "fully_visible_snapshot_indices": full,
                "reason": observed.isEmpty ? (ambiguous ? "ambiguous_native_target" : "no_unique_visible_target_frame") : "original_native_target_frames"]
    }
    func observeTargets(_ targets: [[String: Any]], immediate: [String: Any], action: Int, maxScrolls: Int) -> [String: Any] {
        let epoch = immediate["binding"] as? [String: Any] ?? [:]
        var indices = [immediate["index"] as! Int], remaining = min(max(maxScrolls, 0), 40)
        let diagnosticsStart = revealDiagnostics.count
        for (number, wanted) in targets.enumerated() {
            if key(binding()) != key(epoch) { break }
            if targetEvidence(wanted, indices: indices, epoch: epoch)["status"] as? String == "observed" { continue }
            if remaining == 0 { continue }
            let native = frame(runtime()["content_frame"])
            let initialDirection = viewportFrame.minY - native.minY > 0.5 ? "up" : "down"
            for direction in [initialDirection, initialDirection == "up" ? "down" : "up"] {
                if remaining == 0 || key(binding()) != key(epoch) { break }
                let beforeOffset = frame(runtime()["content_frame"]).minY
                let start = revealDiagnostics.count
                let target = revealTarget(wanted, maxSteps: remaining, initialDirection: direction, prefix: "action-\(action)-target-\(number)", requireControl: false, centerOversized: true, recordFailure: false)
                remaining -= Array(revealDiagnostics.dropFirst(start)).filter { $0["fraction"] != nil }.count
                let afterOffset = frame(runtime()["content_frame"]).minY
                if abs(beforeOffset - afterOffset) > 0.5 {
                    let sample = capture("action-\(action)-target-\(number)")
                    indices.append(sample["index"] as! Int)
                }
                if target != nil || targetEvidence(wanted, indices: indices, epoch: epoch)["status"] as? String == "observed" { break }
                if matches(wanted).count > 1 { break }
            }
        }
        // trace_reveal_images may have produced extra original frames; retain
        // the whole exact interval rather than silently dropping those samples.
        let first = immediate["index"] as! Int
        indices = Array(first..<records.count)
        let ending = binding()
        let stable = key(ending) == key(epoch) && indices.allSatisfy { key(records[$0]["binding"] as? [String: Any] ?? [:]) == key(epoch) && records[$0]["capture_consistent"] as? Bool == true }
        let results = targets.map { targetEvidence($0, indices: indices, epoch: epoch) }
        return ["state_id": activeState, "after_action": action, "binding": epoch, "binding_after_observation": ending,
                "binding_stable": stable, "snapshot_indices": indices, "requested_targets": targets, "targets": results,
                "all_targets_observed": stable && results.allSatisfy { $0["status"] as? String == "observed" },
                "scroll_budget": min(max(maxScrolls, 0), 40), "scrolls_used": min(max(maxScrolls, 0), 40) - remaining,
                "trace": Array(revealDiagnostics.dropFirst(diagnosticsStart)), "scope": "targets_only; never full-content or absence proof"]
    }
    var nonFiniteNumbers: [[String: String]] = []
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
        if let values = value as? [Any] { return values.enumerated().map { jsonSafe($0.element, path: path + "[\($0.offset)]") } }
        return value
    }
    func testObserve() throws {
        continueAfterFailure = false
        let env = ProcessInfo.processInfo.environment
        guard let raw = env["OBSERVER_CONFIG_BASE64"], let data = Data(base64Encoded: raw),
              let config = try JSONSerialization.jsonObject(with: data) as? [String: Any] else { XCTFail("Missing fixture transport"); return }
        let actionData = Data(base64Encoded: env["OBSERVER_ACTIONS_BASE64"] ?? "") ?? Data("[]".utf8)
        let actions = try JSONSerialization.jsonObject(with: actionData) as? [[String: Any]] ?? []
        stateCaptureEnabled = config["state_capture"] as? Bool ?? false
        traceRevealImages = config["trace_reveal_images"] as? Bool ?? false
        sweepLimit = min(max(config["max_scrolls"] as? Int ?? 40, 1), 80)
        observationTargets = config["observation_targets"] as? [[String: Any]] ?? []
        for action in actions where action["type"] as? String == "tap" {
            let target = selector(action)
            if !observationTargets.contains(where: { key($0) == key(target) }) { observationTargets.append(target) }
        }
        for action in actions {
            let extra = action["after_targets"] as? [[String: Any]] ?? (action["after_target"] as? [String: Any]).map { [$0] } ?? []
            for target in extra where !observationTargets.contains(where: { key($0) == key(target) }) { observationTargets.append(target) }
        }
        app = XCUIApplication(); app.launchEnvironment["OBSERVER_CONFIG_BASE64"] = raw; app.launch()
        XCTAssertTrue(app.scrollViews["__observer.scroll"].waitForExistence(timeout: 15))
        let originalRuntime = runtime()
        guard let viewport = originalRuntime["viewport"] as? [String: Double],
              let x = viewport["x"], let y = viewport["y"], let width = viewport["width"], let height = viewport["height"],
              width > 0 && height > 0 else { XCTFail("Native viewport geometry unavailable"); return }
        viewportFrame = CGRect(x: x, y: y, width: width, height: height)
        XCTAssertEqual(height, 600, accuracy: 0.5, "Native measured viewport must be 600 points")
        _ = capture("top")
        if stateCaptureEnabled { sweep("initial") }
        for (i, action) in actions.enumerated() {
            if stateCaptureEnabled && action["type"] as? String == "apply_next_fixture" { sweep("before-update-\(i)") }
            currentActionIndex = i
            activeState = action["state_id"] as? String ?? "action-\(i)"
            let before = capture("action-\(i)-before")
            var callbacksBefore = receipt().count
            let oldIndex = runtime()["fixture_index"] as? Int ?? -1
            let diagnosticsBefore = revealDiagnostics.count
            let kind = action["type"] as? String ?? ""
            var outcome = "completed"
            var targetState: [String: Any] = [:]
            var activationState: [String: Any] = [:]
            var dispatch: [String: Any] = ["attempted": false, "succeeded": false, "binding_before": binding(),
                "event_start": callbacksBefore, "method": kind == "tap" ? "xcui_tap" : kind == "apply_next_fixture" ? "caller_fixture_update" : "observation_only",
                "stimulus": kind == "apply_next_fixture" ? "caller_update" : "activation"]
            switch kind {
            case "tap":
                let wanted = selector(action)
                let target = action["reveal"] as? Bool == true
                    ? revealTarget(wanted, maxSteps: action["max_steps"] as? Int ?? 24, initialDirection: action["direction"] as? String ?? "down", prefix: "action-\(i)")
                    : selectTarget(wanted)
                if let target {
                    targetState = nativeState(target, path: ["selector": wanted])
                    if let (actual, path) = activation(target) {
                        activationState = nativeState(actual, path: path)
                        dispatch["matches"] = 1; dispatch["native_controls"] = 1; dispatch["enabled"] = actual.isEnabled
                        if !actual.isEnabled && action["allow_disabled"] as? Bool == true && visible(actual) {
                            outcome = "blocked_disabled"
                        } else if actual.isEnabled, let point = usablePoint(actual) {
                            let startBinding = binding()
                            callbacksBefore = receipt().count
                            dispatch = ["attempted": true, "succeeded": false, "method": "xcui_tap", "stimulus": "activation",
                                        "binding_before": startBinding, "event_start": callbacksBefore,
                                        "matches": 1, "native_controls": 1, "enabled": actual.isEnabled]
                            if fullyVisible(actual) { actual.tap() }
                            else {
                                let origin = app.coordinate(withNormalizedOffset: .zero)
                                origin.withOffset(CGVector(dx: point.x - app.frame.minX, dy: point.y - app.frame.minY)).tap()
                            }
                            activationState["activation_point"] = ["x": point.x, "y": point.y]
                            activationState["activation_method"] = fullyVisible(actual) ? "native_control_tap" : "visible_intersection_coordinate"
                            outcome = "tapped"
                            dispatch["succeeded"] = true
                        } else { outcome = "unavailable"; issues.append("native control not enabled or no usable visible point") }
                    } else { outcome = "unavailable" }
                } else { outcome = "unavailable" }
            case "apply_next_fixture":
                let button = app.buttons["__observer.next"]
                if button.isEnabled && button.isHittable {
                    dispatch = ["attempted": true, "succeeded": false, "method": "caller_fixture_update", "stimulus": "caller_update",
                                "binding_before": binding(), "event_start": receipt().count]
                    callbacksBefore = receipt().count
                    button.tap()
                    dispatch["succeeded"] = runtime()["fixture_index"] as? Int == oldIndex + 1
                    outcome = dispatch["succeeded"] as? Bool == true ? "updated" : "unavailable"
                } else { outcome = "unavailable"; issues.append("next fixture control unavailable") }
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
            case "sweep": sweep(action["state_id"] as? String ?? "action-\(i)", maxSteps: action["max_steps"] as? Int)
            case "capture", "checkpoint": break
            default: issues.append("unsupported action \(kind)")
            }
            Thread.sleep(forTimeInterval: 0.15)
            let immediateAfter = capture(action["name"] as? String ?? "action-\(i)-after")
            var after = immediateAfter
            let actionBinding = after["binding"] as? [String: Any] ?? [:]
            let actionReceipts = after["callbacks"] as? [[String: Any]] ?? []
            let delta = Array(actionReceipts.dropFirst(callbacksBefore))
            dispatch["event_end"] = actionBinding["event_revision"] ?? NSNull()
            var postViewport: [String: Any] = ["status": "not_requested"]
            var observationSet: [String: Any] = [:]
            let requested = action["after_targets"] as? [[String: Any]] ?? (kind == "tap" ? [action["after_target"] as? [String: Any] ?? selector(action)] : [])
            if !requested.isEmpty, action["observe_after"] as? Bool != false {
                observationSet = observeTargets(requested, immediate: immediateAfter, action: i, maxScrolls: action["observation_max_scrolls"] as? Int ?? 24)
                after = records.last ?? immediateAfter
                if var first = (observationSet["targets"] as? [[String: Any]])?.first {
                    if let sample = (first["snapshot_indices"] as? [Int])?.first { first["snapshot"] = sample }
                    else { first["snapshot"] = after["index"] ?? NSNull() }
                    first["binding_stable"] = observationSet["binding_stable"]
                    postViewport = first
                }
            }
            if stateCaptureEnabled, let state = action["state_id"] as? String, kind != "sweep" { sweep(state) }
            let now = after["runtime"] as? [String: Any] ?? [:]
            let sameProcess = (now["pid"] as? Int == originalRuntime["pid"] as? Int) && (now["instance"] as? String == originalRuntime["instance"] as? String)
            if !sameProcess { issues.append("app process identity changed") }
            if kind == "apply_next_fixture" && now["fixture_index"] as? Int != oldIndex + 1 { issues.append("fixture index did not advance explicitly") }
            if dispatch["succeeded"] as? Bool == true, let expected = action["expect_callback"] as? String, !delta.contains(where: { $0["event"] as? String == expected }) {
                issues.append("expected real callback \(expected) was not received")
            }
            steps.append(["action": action, "outcome": outcome, "target": targetState, "semantic_target": targetState,
                          "activation_target": activationState, "reveal_diagnostics": Array(revealDiagnostics.dropFirst(diagnosticsBefore)),
                          "dispatch": dispatch,
                          "post_action_viewport": postViewport, "observation_set": observationSet, "immediate_after": immediateAfter["index"]!,
                          "before": before["index"]!, "after": after["index"]!, "callback_delta": delta, "same_process": sameProcess, "state_id": activeState, "binding_after": actionBinding])
        }
        if stateCaptureEnabled { sweep("final") }
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
        let result: [String: Any] = ["schema_version": 2, "state_captures": stateCaptures, "measurement_kind": "XCUIElement runtime accessibility; frames in logical screen points",
            "snapshots": records, "steps": steps, "coverage": ["bottom_reached": bottomReached, "required_identifiers": required, "missing_identifiers": missing, "observed_identifiers": seen.sorted()],
            "issues": issues, "reveal_diagnostics": revealDiagnostics, "status": issues.isEmpty ? "passed" : "failed", "original_runtime": originalRuntime]
        var export = jsonSafe(result) as! [String: Any]
        export["serialization_diagnostics"] = nonFiniteNumbers
        let resultAttachment = XCTAttachment(data: try JSONSerialization.data(withJSONObject: export, options: [.prettyPrinted, .sortedKeys]), uniformTypeIdentifier: "public.json")
        resultAttachment.name = "observer-result.json"; resultAttachment.lifetime = .keepAlways; add(resultAttachment)
        XCTAssertTrue(issues.isEmpty, issues.joined(separator: "; "))
    }
}
