# Minimum verifiable scope guard

Default to `outside_calibrated_scope` unless every measured source has native,
capture-bound evidence that it belongs to the profile's measured semantic scope.
An ordinary external XCUI frame has no proof that it is the probe's kind of
identity-transform UIKit leaf. Provider `xcui_cgrect`, matching OS/scale, a frame
inside the numerical domain, a source-code declaration, or an unverified boolean
cannot fill that gap.

For this profile, a positive scope check would need evidence of all of the following:

1. A trusted native producer measured the actual target view, its local bounds,
   public AX frame, affine transform, and ancestor transform identity. The view's
   AX behavior belongs to the observed default-UIView-leaf scope; generic SwiftUI,
   combined/custom AX, transformed nodes, and other unproved semantics remain out.
2. That runtime record is bound to the measurement's exact source target and native
   instance, snapshot/capture index, input hash, process/session, and event revision.
   Its frame agrees with the source frame under separately fixed coherence criteria.
   The consumer verifies the binding and payload integrity, rather than trusting
   a freestanding caller field asserting that calibration applies.
3. Source units are explicitly `pt`; native runtime context matches the profile;
   profile provenance resolves to the sealed probe, raw observation, extraction,
   and method/source version and verifies their hashes.
4. The numerical domain is actually supported for the requested axis/property.
   Signed coordinate ranges and lower/upper extents remain distinct. Width/height
   evidence does not automatically establish relational or semantic layout claims.

The current ordinary XCUI source proof does not provide item 1 or the full item 2.
The minimum safe implementation can therefore simply return
`outside_calibrated_scope` for it. There is no need to invent an attestation, infer
the native view class, instrument business components, or collect another SDK run
to avoid that result. The independently checked raw geometry assertion remains
unchanged and its original P/F threshold is retained.

Even when those scope checks exist, this dataset's zero residuals do not establish
a positive error law. Preserve that limitation in profile status and diagnostic
language. A model interval may describe an exploratory empirical hypothesis; it
must not become a passing waiver, a guaranteed layout-error bound, or a product
cause attribution. Freezing a later method is prospective and does not retroactively
make the current data a confirmatory positive-residual test.

This recommendation follows `ASSESSMENT-1-SEAL.json`. It proposes no change to
probe dimensions, sample membership, expectations, tolerances, or known-case inputs.
