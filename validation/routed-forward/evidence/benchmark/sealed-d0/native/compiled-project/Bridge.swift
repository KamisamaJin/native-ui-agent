import SwiftUI
import UIKit

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        AnyView(FoldGuideHost(fixture: fixture, onEvent: onEvent).frame(height: 314))
    }
}

private struct FoldGuideHost: UIViewRepresentable {
    let fixture: [String: Any]
    let onEvent: (String) -> Void
    func makeUIView(context: Context) -> FoldGuideView {
        let view = FoldGuideView()
        view.apply(fixture, onEvent: onEvent)
        return view
    }
    func updateUIView(_ uiView: FoldGuideView, context: Context) { uiView.apply(fixture, onEvent: onEvent) }
}

private final class FoldDiagram: UIView {
    var reverse = false { didSet { setNeedsDisplay() } }
    override func draw(_ rect: CGRect) {
        let paper = CGRect(x: 12, y: 8, width: 156, height: 84)
        UIColor(red: 0.93, green: 0.95, blue: 0.97, alpha: 1).setFill()
        UIBezierPath(rect: paper).fill()
        UIColor(red: 0.2, green: 0.29, blue: 0.36, alpha: 1).setStroke()
        let outline = UIBezierPath(rect: paper); outline.lineWidth = 2; outline.stroke()
        let crease = UIBezierPath()
        crease.move(to: CGPoint(x: reverse ? 168 : 12, y: 8))
        crease.addLine(to: CGPoint(x: reverse ? 12 : 168, y: 92))
        crease.lineWidth = 2; crease.setLineDash([5, 4], count: 2, phase: 0); crease.stroke()
    }
}

private final class FoldGuideView: UIView {
    private let heading = UILabel()
    private let diagram = FoldDiagram()
    private let instruction = UILabel()
    private let status = UILabel()
    private let action = UIButton(type: .system)
    private var side: String?
    private var marked = false
    private var onEvent: (String) -> Void = { _ in }
    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .white
        heading.text = "Fold guide"
        heading.font = .systemFont(ofSize: 22, weight: .semibold)
        heading.textColor = .black
        heading.accessibilityIdentifier = "fold.heading"
        diagram.isAccessibilityElement = true
        diagram.accessibilityIdentifier = "fold.diagram"
        diagram.accessibilityLabel = "Fold diagram"
        instruction.font = .systemFont(ofSize: 15)
        instruction.textColor = .darkGray
        instruction.numberOfLines = 2
        instruction.accessibilityIdentifier = "fold.instruction"
        status.font = .systemFont(ofSize: 15, weight: .medium)
        status.textColor = .black
        status.accessibilityIdentifier = "fold.status"
        action.setTitle("Mark crease", for: .normal)
        action.titleLabel?.font = .systemFont(ofSize: 17, weight: .semibold)
        action.accessibilityIdentifier = "fold.action"
        action.backgroundColor = UIColor(red: 0.89, green: 0.94, blue: 0.97, alpha: 1)
        action.layer.cornerRadius = 8
        action.addTarget(self, action: #selector(mark), for: .touchUpInside)
        [heading, diagram, instruction, status, action].forEach(addSubview)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) unavailable") }
    override func layoutSubviews() {
        super.layoutSubviews()
        heading.frame = CGRect(x: 16, y: 8, width: bounds.width - 32, height: 28)
        diagram.frame = CGRect(x: 16, y: 50, width: 180, height: 100)
        instruction.frame = CGRect(x: 16, y: 160, width: bounds.width - 32, height: 44)
        status.frame = CGRect(x: 16, y: 214, width: bounds.width - 32, height: 22)
        action.frame = CGRect(x: 16, y: 250, width: 200, height: 44)
    }
    func apply(_ fixture: [String: Any], onEvent: @escaping (String) -> Void) {
        self.onEvent = onEvent
        let incoming = fixture["side"] as? String ?? "front"
        if incoming != side { side = incoming; marked = false }
        diagram.reverse = incoming == "reverse"
        instruction.text = incoming == "reverse" ? "Turn the sheet. Fold along the reverse diagonal." : "Fold the front sheet along the dashed diagonal."
        refresh()
    }
    private func refresh() {
        status.text = marked ? "Crease marked" : side == "reverse" ? "Reverse side" : "Sheet ready"
        action.isEnabled = !marked
    }
    @objc private func mark() {
        marked = true
        refresh()
        onEvent("crease.marked")
    }
}
