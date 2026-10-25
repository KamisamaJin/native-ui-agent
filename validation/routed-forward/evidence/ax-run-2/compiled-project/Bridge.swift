import SwiftUI
import UIKit

// Neutral calibration only. This bridge has no business component or callbacks.
enum ObserverBridge {
    static func make(fixture: [String: Any],
                     onEvent: @escaping (String) -> Void) -> AnyView {
        let specification = AXProbeSpecification(fixture)
        return AnyView(AXProbeRepresentable(specification: specification)
            .frame(width: specification.width, height: specification.height,
                   alignment: .topLeading))
    }
}

private struct AXProbeItem {
    let identifier: String
    let placement: CGRect
    let referenceBounds: CGRect

    init(_ input: [String: Any]) {
        identifier = input["id"] as! String
        let p = input["placement"] as! [String: Any]
        let b = input["bounds"] as! [String: Any]
        func n(_ d: [String: Any], _ k: String) -> CGFloat {
            CGFloat((d[k] as! NSNumber).doubleValue)
        }
        placement = CGRect(x: n(p, "x"), y: n(p, "y"),
                           width: n(b, "width"), height: n(b, "height"))
        referenceBounds = CGRect(x: n(b, "x"), y: n(b, "y"),
                                 width: n(b, "width"), height: n(b, "height"))
    }
}

private struct AXProbeSpecification {
    let width: CGFloat
    let height: CGFloat
    let items: [AXProbeItem]

    init(_ fixture: [String: Any]) {
        let canvas = fixture["canvas"] as! [String: Any]
        width = CGFloat((canvas["width"] as! NSNumber).doubleValue)
        height = CGFloat((canvas["height"] as! NSNumber).doubleValue)
        items = (fixture["probes"] as! [[String: Any]]).map(AXProbeItem.init)
        precondition(width.isFinite && width > 0 && height.isFinite && height > 0)
        precondition(Set(items.map(\.identifier)).count == items.count)
    }
}

private struct AXProbeRepresentable: UIViewRepresentable {
    let specification: AXProbeSpecification

    func makeUIView(context: Context) -> AXProbeCanvas {
        AXProbeCanvas(specification: specification)
    }

    func updateUIView(_ view: AXProbeCanvas, context: Context) {
        view.configure(specification)
    }

    func sizeThatFits(_ proposal: ProposedViewSize, uiView: AXProbeCanvas,
                     context: Context) -> CGSize? {
        CGSize(width: specification.width, height: specification.height)
    }
}

private final class AXProbeCanvas: UIView {
    private var specification: AXProbeSpecification
    private var leaves: [AXProbeLeaf] = []

    init(specification: AXProbeSpecification) {
        self.specification = specification
        super.init(frame: CGRect(x: 0, y: 0, width: specification.width,
                                 height: specification.height))
        isAccessibilityElement = false
        shouldGroupAccessibilityChildren = false
        backgroundColor = .white
        clipsToBounds = false
        configure(specification)
    }

    required init?(coder: NSCoder) { fatalError("Programmatic calibration view") }

    override var intrinsicContentSize: CGSize {
        CGSize(width: specification.width, height: specification.height)
    }

    func configure(_ specification: AXProbeSpecification) {
        self.specification = specification
        if leaves.map(\.referenceIdentifier) != specification.items.map(\.identifier) {
            leaves.forEach { $0.removeFromSuperview() }
            leaves = specification.items.enumerated().map { index, item in
                let leaf = AXProbeLeaf(identifier: item.identifier, ordinal: index)
                addSubview(leaf)
                return leaf
            }
            accessibilityElements = leaves
        }
        applyGeometry()
        invalidateIntrinsicContentSize()
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        applyGeometry()
    }

    private func applyGeometry() {
        for (leaf, item) in zip(leaves, specification.items) {
            leaf.transform = .identity
            leaf.bounds = item.referenceBounds
            leaf.center = CGPoint(x: item.placement.midX, y: item.placement.midY)
        }
    }
}

private final class AXProbeLeaf: UIView {
    let referenceIdentifier: String
    private let nativeInstanceIdentity = UUID().uuidString.replacingOccurrences(of: "-", with: "")
    private var cachedGeometryKey: String?
    private var cachedValue: String?
    private var geometryRevision = 0

    init(identifier: String, ordinal: Int) {
        referenceIdentifier = identifier
        super.init(frame: .zero)
        isAccessibilityElement = true
        accessibilityIdentifier = identifier
        accessibilityLabel = "Calibration sample \(ordinal)"
        accessibilityTraits = .staticText
        backgroundColor = UIColor(hue: CGFloat(ordinal) / 23.0,
                                  saturation: 0.18, brightness: 0.94, alpha: 1)
        layer.borderColor = UIColor.darkGray.cgColor
        layer.borderWidth = 0.5
    }

    required init?(coder: NSCoder) { fatalError("Programmatic calibration leaf") }

    private func rect(_ value: CGRect) -> [Double] {
        [Double(value.origin.x), Double(value.origin.y),
         Double(value.size.width), Double(value.size.height)]
    }

    private func encode(_ object: [String: Any]) -> String {
        guard JSONSerialization.isValidJSONObject(object),
              let data = try? JSONSerialization.data(withJSONObject: object,
                                                     options: [.sortedKeys]),
              let text = String(data: data, encoding: .utf8) else {
            return "{\"v\":2,\"m\":false,\"e\":\"non_finite\"}"
        }
        return text
    }

    // Query-time public UIKit measurements include ancestor scroll translations.
    // The cached property changes only when native geometry/attachment changes;
    // it never calls onEvent and never mutates the observer's event revision.
    override var accessibilityValue: String? {
        get {
            let w = window
            var ancestorsIdentity = true
            var parent = superview
            while let ancestor = parent {
                ancestorsIdentity = ancestorsIdentity && ancestor.transform.isIdentity
                parent = ancestor.superview
            }
            let t = transform
            var geometry: [String: Any] = [
                "v": 2,
                "m": w != nil,
                "i": referenceIdentifier,
                "u": nativeInstanceIdentity,
                "o": String(UInt(bitPattern: ObjectIdentifier(self)), radix: 16),
                "b": rect(bounds),
                "a": rect(accessibilityFrame),
                "t": [Double(t.a), Double(t.b), Double(t.c), Double(t.d),
                      Double(t.tx), Double(t.ty)],
                "p": ancestorsIdentity,
                "s": Double(w?.screen.scale ?? UIScreen.main.scale),
                "w": w.map { rect(convert(bounds, to: $0)) as Any } ?? NSNull(),
                "os": UIDevice.current.systemVersion
            ]
            let key = encode(geometry)
            if cachedGeometryKey != key {
                geometryRevision += 1
                geometry["r"] = geometryRevision
                let wire = encode(geometry)
                // Public XCUI value transport truncated the v1 payload at 512
                // ASCII characters. Never round native metrics to fit that limit.
                cachedValue = wire.utf8.count < 480 ? wire
                    : "{\"v\":2,\"m\":false,\"e\":\"wire_overflow\",\"n\":\(wire.utf8.count)}"
                cachedGeometryKey = key
            }
            return cachedValue
        }
        set { /* The value is owned by actual native geometry. */ }
    }

    override func draw(_ rect: CGRect) {
        super.draw(rect)
        let text = referenceIdentifier as NSString
        text.draw(at: CGPoint(x: bounds.minX + 3, y: bounds.minY + 3),
                  withAttributes: [.font: UIFont.monospacedSystemFont(ofSize: 9,
                                                                    weight: .regular),
                                   .foregroundColor: UIColor.black])
    }
}
