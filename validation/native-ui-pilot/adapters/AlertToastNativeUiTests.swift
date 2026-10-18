import XCTest
import SwiftUI
import UIKit
import SnapshotTesting
@testable import AlertToast

final class AlertToastNativeUiTests: XCTestCase {
    @MainActor
    func testCaptureHUD() throws {
        let environment = ProcessInfo.processInfo.environment
        let outputValue = environment["NATIVE_UI_OUTPUT"]
            ?? environment["TEST_RUNNER_NATIVE_UI_OUTPUT"]
        let output = URL(fileURLWithPath: try XCTUnwrap(outputValue))
        let scenario = environment["NATIVE_UI_SCENARIO"]
            ?? environment["TEST_RUNNER_NATIVE_UI_SCENARIO"] ?? "normal"
        let isDark = scenario == "dark"
        let title = scenario == "long"
            ? "Your order is ready. Please review the delivery instructions."
            : "Order updated"
        let toast = AlertToast(
            displayMode: .hud,
            type: .systemImage("shippingbox.fill", .blue),
            title: title,
            subTitle: "The package is on its way",
            style: .style(
                backgroundColor: isDark ? Color(white: 0.16) : .white,
                titleColor: isDark ? .white : .black,
                subTitleColor: isDark ? .white : .black
            )
        )
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
        .frame(width: 390, height: 240)

        let hosting = UIHostingController(rootView: view)
        hosting.view.frame = CGRect(x: 0, y: 0, width: 390, height: 240)
        let traits = UITraitCollection(traitsFrom: [
            UITraitCollection(displayScale: 2),
            UITraitCollection(userInterfaceStyle: isDark ? .dark : .light),
            UITraitCollection(preferredContentSizeCategory: .large)
        ])
        let strategy = Snapshotting<UIViewController, UIImage>.image(
            size: CGSize(width: 390, height: 240),
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
            "executed_test": "AlertToastNativeUiTests.testCaptureHUD",
            "scenario": scenario,
            "production_component": "AlertToast.hud",
            "output_environment_received": true,
            "png_bytes": png.count
        ]
        try JSONSerialization.data(withJSONObject: nativeReport, options: [.prettyPrinted])
            .write(to: output.appendingPathComponent("native-test.json"))
    }
}
