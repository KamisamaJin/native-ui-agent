# Post-barrier operator runner guard review

The unexecuted pre-review source and its byte pin remain here. The corrected
runner changes no frozen SUT, controller, envelope, spec, fixture or oracle.
Thirteen author synthetic HOST controls passed without actual RUN/private access,
SDK calls or live forwarding. They do not establish operational/native success.

The runner uses only the frozen controller's read-only constructor/cohort/D0
proof methods, under a shared state lock. It verifies original full member/source/
claim/input/tool pins, event chronology, the first immutable D0 clock, and the
one-shot hidden authorization. It never invokes expire/status/serve or repairs.

The I preparation seal is pinned by `--initial-seal` and
`--initial-seal-sha256`, then registered once for all I operations. Its exact schema
is `{version:1,kind:"canonical-initial-reference-preparation",tasks:{Tn:{profile:
{config:{path,sha256},source_manifest:{path,sha256},resource_root,source_roots}}}}`.
The canonical source must match original initial bytes, retain its new readonly
root identity, and use distinct registered I resources. Final operations retain
their original final root identity and one-shot-authorized config pins.

Each task/arm/profile can reserve one native attempt. Its claim is durable before
forwarding; a failure/interruption cannot be replaced by a fresh record name.
Source/image binding and finish operations reference that scope's original
`--native-outcome` and `--native-outcome-sha256`, plus the original capture/cycle.
Native outcomes may be incomplete/failed: their original fresh facts remain
eligible for honest independent assessment, never automatically delivered.

I native collection requires a live supplemental monitor and all slots clear.
Readonly work can continue after positive monitor closure. Explicit owned cleanup
uses the frozen resource-manager cleanup API under the original meter, bypassing
new-collection halt/idle admission only; it cannot launch new UI. Cleanup remains
possible after a live production source error, with historical/config pins intact.

Every admitted invocation records entry-to-final wall including barrier/admission
checks and preflight failures. Output inventory/protection errors cannot suppress
the terminal outcome. Links are recorded with lstat/readlink, never chmod-followed.
Partial originals/errors are retained. All helper/profile-adapter dependency
bytes are checked before import and after operation.

Actual operation still requires the operator's independent checks: correct
profiles, live READY/preflight/close, fresh native facts, runtime outcomes, source/
image verdict replay, anonymous double review/cause/reveal barriers and cleanup.
The guard is procedural, not a sandbox against a privileged operator bypass.
