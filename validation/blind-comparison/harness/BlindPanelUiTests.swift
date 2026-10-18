import XCTest
import SwiftUI
import UIKit
import SnapshotTesting
@testable import AlertToast

final class BlindPanelUiTests: XCTestCase {
    @MainActor func testCapture() throws {
        let env=ProcessInfo.processInfo.environment
        let output=URL(fileURLWithPath:try XCTUnwrap(env["NATIVE_UI_OUTPUT"]))
        let fixture=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:try XCTUnwrap(env["BENCH_FIXTURE"])))) as! [String:Any]
        let width=(fixture["width"] as? NSNumber)?.doubleValue ?? 390
        let height=(fixture["height"] as? NSNumber)?.doubleValue ?? 620
        let dark=fixture["dark"] as? Bool ?? false
        let rtl=fixture["rtl"] as? Bool ?? false
        let large=((fixture["font_scale"] as? NSNumber)?.doubleValue ?? 1) >= 1.6
        let items=(fixture["items"] as! [[String:Any]]).map { item -> TransferToastItem in
            let raw=item["progress"]
            let progress=(raw as? NSNumber)?.doubleValue ?? Double(raw as? String ?? "nan") ?? .nan
            return TransferToastItem(id:item["id"] as! String,name:item["name"] as! String,
                status:item["status"] as! String,progress:progress)
        }
        var events=[String]()
        let panel=TransferToastPanel(items:items,expanded:fixture["expanded"] as? Bool ?? false,
            onToggle:{events.append("toggle")},onRetry:{events.append("retry:"+$0)})
        let view=ZStack(alignment:.topLeading) {
            (dark ? Color(red:12/255,green:20/255,blue:36/255) : Color(red:237/255,green:242/255,blue:248/255))
            ScrollView(.vertical) {
                panel.frame(maxWidth:.infinity).padding(.horizontal,16).padding(.top,24).padding(.bottom,24)
            }
        }.environment(\.colorScheme,dark ? .dark:.light)
         .environment(\.layoutDirection,rtl ? .rightToLeft:.leftToRight)
         .environment(\.sizeCategory,large ? .accessibilityExtraExtraExtraLarge:.large)
         .frame(width:width,height:height)
        let hosting=UIHostingController(rootView:view)
        let traits=UITraitCollection(traitsFrom:[UITraitCollection(displayScale:2),
            UITraitCollection(userInterfaceStyle:dark ? .dark:.light),
            UITraitCollection(preferredContentSizeCategory:large ? .accessibilityExtraExtraExtraLarge:.large)])
        let strategy=Snapshotting<UIViewController,UIImage>.image(size:CGSize(width:width,height:height),traits:traits)
        let ready=expectation(description:"native render")
        var image:UIImage?
        strategy.snapshot(hosting).run {image=$0;ready.fulfill()}
        wait(for:[ready],timeout:10)
        try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
        try XCTUnwrap(image?.pngData()).write(to:output.appendingPathComponent("actual.png"))
        var ax=[[String:Any]]();var seen=Set<ObjectIdentifier>();var activated=false
        let wanted=fixture["activate_id"] as? String
        func walk(_ object:AnyObject,_ depth:Int) {
            guard depth<30 else{return}
            let identity=ObjectIdentifier(object);guard !seen.contains(identity) else{return};seen.insert(identity)
            if let element=object as? UIAccessibilityElement {
                let frame=element.accessibilityFrame
                let id=element.accessibilityIdentifier ?? ""
                ax.append(["identifier":id,"label":element.accessibilityLabel ?? "",
                    "value":element.accessibilityValue ?? "","traits":element.accessibilityTraits.rawValue,
                    "frame_screen_pt":[frame.minX,frame.minY,frame.maxX,frame.maxY].allSatisfy {$0.isFinite}
                        ? [frame.minX,frame.minY,frame.maxX,frame.maxY] : []])
                if id==wanted {activated=element.accessibilityActivate()}
            }
            if let ui=object as? UIView {
                if let elements=ui.accessibilityElements {for child in elements {walk(child as AnyObject,depth+1)}}
                let count=ui.accessibilityElementCount()
                if count>0 && count<300 {for i in 0..<count {if let child=ui.accessibilityElement(at:i) {walk(child as AnyObject,depth+1)}}}
                ui.subviews.forEach {walk($0,depth+1)}
            }
        }
        walk(hosting.view,0)
        let report:[String:Any]=["native_test":"BlindPanelUiTests.testCapture","ax_elements":ax,
            "activation_requested":wanted ?? "","activation_executed":activated,"events":events,
            "action_method":"UIAccessibilityElement.accessibilityActivate if an exposed element exists; otherwise not executed",
            "font_category":large ? "accessibilityExtraExtraExtraLarge":"large",
            "layout_scope":"Real simulator XCTest component host; no full business app navigation"]
        try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted]).write(to:output.appendingPathComponent("native-report.json"))
    }
}
