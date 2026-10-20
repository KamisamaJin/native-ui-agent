# Why additional evidence is not enough

The new tools address acquisition and declared plan coverage. They cannot
certify that an agent interpreted a design token correctly. In the sealed
source-a plans, `summary.font_sp` expects 14 and `balance.font_weight` expects
400. The independent frozen design requires summary 12 and semibold balance.
The actual native values match the builder's incorrect expectations, so its
original checks pass while the independent acceptance fails. Referencing the
whole brief as `source` does not establish that a particular expectation was
derived correctly. This is a shared implementation/test assumption, not a
missing native font inspector on Android.

The complete state matrix propagates the chosen expectation to declared states;
it cannot correct a wrong expectation. A future general improvement needs an
independently established typed design contract, with exact source anchors and
units, checked before implementation. The implementation agent should consume
that contract rather than independently invent both code and its own answers.
That capability was not added after seeing this task, and no frozen score or
source was repaired to make the new trial look better.

Original check noise remains separate from real defects. Native float equality,
near-threshold dimensions, JSON object formatting and TextLayout overflow flags
need their own semantics. An overflow flag is not automatically proof of
visible clipping. The original reports and model judgments remain intact; the
independent matching stage distinguishes confirmed, false, uncertain and
unmapped claims. The grader's pre-delivery precision/field corrections are
common infrastructure and cannot be credited as a treatment improvement.

The priority control illustrates a measurement limit. Its actual iOS AX height
changes from 28 to 48, but the frozen dimension uncertainty is ±2 pt. The latter
interval crosses the minimum48 threshold, so the literal transition is F→U,
not F→P. That records a real geometric change without claiming strict verified
compliance. It is not proof of a genuine OS physical hit region, which was not
measured. Report these boundary uncertainties apart from absent native facts
and unsupported style properties.

More target frames can improve evidence coverage while increasing native
navigation cost. Whole-content coverage, absence, successful activation and an
immediate callback interval remain separate obligations. More screenshots do
not create a SwiftUI computed-style inspector or establish unobserved physical
touch behavior. Same-source collector pairs are therefore the relevant evidence
for observer capability; two different generated implementations do not isolate
the effect of the Skill on code quality.

This task produced no assessed natural business callback/transition failure.
Its business miss denominator is N/A. A future independently preregistered
mutation evaluation could test generic boundary mistakes, but those would be
synthetic defects and could not replace this run's natural-development result.
One task per arm, related platforms, AI visual adjudication, shared hardware,
recognizable producer formats and shared filesystem also limit causal claims.

The trial tests new production components with a fixed public contract and
selectors through thin hosts. It does not establish the quality of arbitrary
unmodified legacy pages, vague-design interpretation, whole-app integration,
navigation or backend behavior.
