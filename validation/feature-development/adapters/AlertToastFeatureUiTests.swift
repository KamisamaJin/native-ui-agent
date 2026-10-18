import XCTest
import SwiftUI
import UIKit
import SnapshotTesting
@testable import AlertToast

final class AlertToastFeatureUiTests: XCTestCase {
    @MainActor
    func testCaptureProgress() throws {
        let environment = ProcessInfo.processInfo.environment
        let outputValue = environment["NATIVE_UI_OUTPUT"]
            ?? environment["TEST_RUNNER_NATIVE_UI_OUTPUT"]
        let output = URL(fileURLWithPath: try XCTUnwrap(outputValue))
        let scenario = environment["NATIVE_UI_SCENARIO"]
            ?? environment["TEST_RUNNER_NATIVE_UI_SCENARIO"] ?? "normal"
        let isDark = scenario == "dark"
        let legacy = scenario == "legacy"
        let width: CGFloat = scenario == "narrow" ? 320 : 390
        let height: CGFloat = legacy ? 240 : 300
        let progress: Double? = legacy ? nil : (scenario == "complete" ? 1.3 : (isDark ? 0.73 : 0.42))
        let title = legacy ? "Order updated" : ((scenario == "long" || scenario == "narrow")
            ? "Uploading your original holiday photographs to the shared family album"
            : "Uploading photos")
        let toast = AlertToast(
            displayMode: .hud,
            type: .systemImage("shippingbox.fill", .blue),
            title: title,
            subTitle: legacy ? "The package is on its way" : "Keep this window open",
            style: .style(
                backgroundColor: isDark ? Color(white: 0.16) : .white,
                titleColor: isDark ? .white : .black,
                subTitleColor: isDark ? .white : .black
            ),
            progress: progress
        )
        XCTAssertEqual(AlertToast(type: .regular, progress: -0.5).normalizedProgress, 0)
        XCTAssertEqual(AlertToast(type: .regular, progress: 1.5).normalizedProgress, 1)
        XCTAssertEqual(AlertToast(type: .regular, progress: .nan).normalizedProgress, 0)
        XCTAssertEqual(AlertToast(type: .regular, progress: .infinity).normalizedProgress, 0)
        XCTAssertNil(AlertToast(type: .regular).progress)
        let view = ZStack {
            (isDark ? Color(white: 0.06) : Color(white: 0.94))
            VStack {
                toast
                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.top, 20)
        }
        .environment(\.colorScheme, isDark ? .dark : .light)
        .environment(\.sizeCategory, .large)
        .frame(width: width, height: height)

        let hosting = UIHostingController(rootView: view)
        hosting.view.frame = CGRect(x: 0, y: 0, width: width, height: height)
        let traits = UITraitCollection(traitsFrom: [
            UITraitCollection(displayScale: 2),
            UITraitCollection(userInterfaceStyle: isDark ? .dark : .light),
            UITraitCollection(preferredContentSizeCategory: .large)
        ])
        let strategy = Snapshotting<UIViewController, UIImage>.image(
            size: CGSize(width: width, height: height),
            traits: traits
        )
        let captured = expectation(description: "SnapshotTesting produced the production HUD image")
        var image: UIImage?
        strategy.snapshot(hosting).run {
            image = $0
            captured.fulfill()
        }
        wait(for: [captured], timeout: 10)
        let png = try XCTUnwrap(image?.pngData())
        XCTAssertGreaterThan(png.count, 1000)
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        try png.write(to: output.appendingPathComponent("actual.png"))
        let nativeReport: [String: Any] = [
            "executed_test": "AlertToastFeatureUiTests.testCaptureProgress",
            "scenario": scenario,
            "production_component": "AlertToast.hud / progressHUD",
            "canvas_width_pt": width, "canvas_height_pt": height,
            "normalized_progress": toast.normalizedProgress, "has_progress": !legacy,
            "edge_case_assertions": "negative, >1, NaN, infinity, absent",
            "output_environment_received": true,
            "png_bytes": png.count
        ]
        try JSONSerialization.data(withJSONObject: nativeReport, options: [.prettyPrinted])
            .write(to: output.appendingPathComponent("native-test.json"))
    }
}
