# Independent fresh design artifact contract

This is a format/resource contract, not a business example or an expected answer.
The designer independently chooses the feature, API, content and requirements.
Public material must not expose private cases or expected per-case answers.

Public: brief.md, reference.svg (marked design intention, not native pixel golden),
public-example.json and api.md with Swift/Kotlin production types, entry point and
deterministic callback serialization. A thin bridge may only decode inputs, invoke
the production component, and serialize actual typed callbacks. It supplies no UI,
business validation, amount calculation or default branch that could hide a bug.

Private oracle.json:

```json
{
  "version":1,
  "cases":[{
    "id":"C01", "split":"initial",
    "environment":{"width":390,"theme":"light","direction":"ltr",
      "font_scale":1,"dynamic_type":"large"},
    "models":{"initial":{},"replacement":{}},
    "checkpoints":[{
      "id":"initial", "model":"initial", "full_content":true,
      "trigger":{"type":"initial"},
      "assertions":[{
        "id":"independently-chosen-cell",
        "category":"visual", "method":"visual",
        "target":{"identifier":"public.local.identifier"},
        "expected":"independently frozen requirement",
        "requires_stimulus":false
      }]
    }]
  }],
  "source_assertions":[]
}
```

Names C01–C04 are initial; H01–H02 are held out. At most two models, eight
activate/replaceModel actions and two full-content visual checkpoints per case.
Triggers: initial; activate with exact target selector and optional requested method;
replaceModel with model name. Names/opaque input IDs belong to the designer.
Each checkpoint is an immutable input/event epoch. Full-content checkpoints require
native overlapping interval coverage; target checkpoints require the actual target
image/native fields. Actions can be followed by a full sweep without changing the
original callback interval or attributing navigation callbacks to activation.

Atomic category: business, visual, integration, source_api or capability. Method:
callback, native_control, native_text, native_bounds, native_typography, pixels,
visual or source_api. Freeze every parameter member as its own assertion ID.
Platform-specific source assertions are separately enumerated. Include platform
and case/checkpoint in expanded keys, not in free-form reasons alone.

Callback expected is an exact list of serialized typed events. It requires an
actual successful activation with the requested native method, or a successful
explicit caller replacement for quietness. A control the observer refuses to
activate leaves activation behavior U; its independently observed disabled state
may be checked separately. An observed empty event interval is not handler proof.
All post-stimulus business behavior/assertions must set requires_stimulus:true;
visual/integration checks at a named post-action state also need a demonstrated
state transition when they claim that state. Native facts and original raw pixels
must support outcomes. A source declaration is never actual styling evidence.

Actual routes available: iOS XCUI tap, Android Compose semantic OnClick; neither
claims iOS AX performAction or Android OS physical touch. Missing native typography,
physical hit regions or internal padding must stay U if explicitly required. Do not
omit a required unsupported aspect merely to obtain a lower U ratio. Keep those
capability cells separate from business-behavior miss metrics.

Private expanded-plan.json lists every platform/case/checkpoint/member row with
expected/category/method/target/source-only and stimulus requirements; validate it
before candidate source or evidence is read. Also freeze the independent evaluator's
source-independent algorithm and exact evidence-locator/grade format before builders
start. The independent evaluator must import the common callback gate; the archival
validator rejects callback P/F if that gate says U, and rejects post-stimulus P/F
without established stimulus. No discretionary override using a literal count.

The private concrete holdouts are not given to builders. Root may translate triggers
and models into inputs without printing expectations. Generate held-out native input
files only after both final source seals. Do not change requirements from observed
source or results; source-specific provenance links can be attached during grading.
