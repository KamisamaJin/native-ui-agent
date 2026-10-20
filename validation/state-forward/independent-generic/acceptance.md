# Independent generic forward test

Frozen before implementation and native commands: 2026-10-20T07:36:51.889267+00:00

This is a new neutral reading checklist, invented for this evaluation without reading earlier trials, design folders, or business components. One public controlled component is implemented in SwiftUI and Compose; a caller bridge owns selection and applies input replacement without explicitly changing the view identity.

Independent design reference: a light neutral vertical sheet, with a 24-point/dp semibold dark title, 16-point/dp status, twelve numbered content sections, a teal full-width minimum 48-point/dp action immediately after section 6, and a footer after section 12. Content uses 18-point/dp section titles and 15-point/dp body. The sheet has no fixed text heights: the long paragraph wraps. Ordinary spacing is 16, section internal spacing 8, and a pale neutral section surface with 12 internal padding. The action uses white text; selected status stays dark. The offered native host width is 390 (358 child width after shell padding), LTR, light, ordinary size. This is a structural/style reference, not a pixel golden.

State A: title “Field notes, set A”; initial top status “Nothing marked”; footer “Selection: none”. Action label is “Mark section six”, enabled. Activating once emits exactly [“toggle-mark”] and the same component displays top “Section six marked”, action “Clear mark” selected=true, footer “Selection: section six”.

Caller replacement B: title “Field notes, set B”; clears caller selection, top “Nothing marked”, footer “Selection: none”, action “Mark section six” selected=false and disabled. Replacement emits zero callbacks. This checks retained process and native input advancement, not arbitrary view lifecycle.

The declared matrix includes separate title/top/action label/action enabled/action selected/footer/event/visual aspects. Visual review is limited to the acquired target frames, and cannot pass whole-content or numeric SwiftUI style claims. Initial/final state sweeps separately retain scroll coverage. Android may supply native text layout, but the common matrix deliberately makes no cross-platform font claim.

Before the component run, each observer gets a separate minimal probe: a title, active button and last label separated by tall fixed rows, one actual button callback, then explicit caller replacement. No production test depends on silent event intervals or blocked dispatch.

Run limit: at most two native invocations per platform (one probe, one component). Preserve compile or observation failure and stop that platform; report root before retry. No baseline updates, no external writes, no commits.
