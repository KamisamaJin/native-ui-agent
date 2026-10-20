# Neutral native images

The root reviewer opened `ios-v5-v1-contact.png` and
`android-v5-v1-contact.png`, derived from original PNGs with frame labels. The
surfaces visibly contain the top disclosure/disabled action and distant footer
action; expanding adds the long detail, and caller replacement displays token B
at both ends. Raw full-size frames remain in `../generic-evidence`.

This is a capability sanity check, not a human gold standard or a business style
score. Native label/callback checks remain separate. iOS buttons in this neutral
probe deliberately use default SwiftUI styling; their size is not a design defect
because this probe does not impose a button-style specification.

All four target-set states retain `complete:false`. The missing-target action
uses zero search steps and remains unavailable. The disabled action emits no
callback and remains unassessed for handler behavior. The two intentional
negative-plan replays alter expectations only: they are evaluator controls,
not naturally occurring implementation defects or repair evidence.
