# Open demonstrated issues

## SC07 — PNG16 low-bit differences disappear during decoding

Both arms certify complete/exact and automatic absence passed although independent raw PNG16 decode proves one unequal original red channel sample. IHDR is bit depth16/color type2. Pillow exposes RGB and discards the low bits before the provider compares.

Expected: No full/absence credit from unequal originals or an unsupported original encoding. Lossy conversion cannot replace original pixels.

Reach: Direct certificate, bound state, execution coverage and automatic absence; no native/final delivery pass claimed.

`python3 -B validation/pooled-forward/qualification/review-6/checks/repro_existing.py --arm candidate-v13.5 --case A07-raster16-lowbit-admitted-host`

## SC08 — Later intersections invalidate an earlier independent witness clause

Both arms accept a3-frame coherent raster chain. Link0 has only A/B witnesses. Final exact rational domains force A=[201,211), B=[210,220), so no final joint assignment makes that link disjoint. The later link has C/D and is accepted while the earlier witness clause is not rechecked.

Expected: One assignment must satisfy every original link and global identity/order constraints jointly.

Reach: Direct certificate, bound state, execution coverage, routing and automatic absence.

`python3 -B validation/pooled-forward/qualification/review-6/checks/repro_existing.py --arm candidate-v13.5 --case A08-joint-witness-admitted-host`

## SC09 — Viewport-local presence/uniqueness values are treated as conflicting state values

With a valid coherent full sweep, a target missing in early lazy frames but present late produces U for present:true/unique:true, and U rather than F for present:false. An explicit duplicate in an early frame followed by one match later produces U for unique:true instead of decisive F. Seen-early/missing-later and nonunique expectation variants also remain U.

Expected: State presence is existential over coherent original frames; absence requires complete never-present evidence; a real duplicate witness cannot be cancelled by a later single match.

Reach: Automatic typed evaluator in both common arms. Absent-all full and mixed-epoch/incomplete-negative controls behave correctly.

`python3 -B validation/pooled-forward/qualification/review-6/checks/repro_existing.py --arm candidate-v13.5 --case A11-late-presence`

## SC10 — Coverage-domain verification omits approved runtime host shape

Prepared approval/request/source namespace/original component copy/mock compiled log/captured and compiled host bytes match the pinned neutral domain. Coherently halving logical app/viewport/content/leaf rectangles to195x300 while retaining390x600 original PNGs is still granted full_content and absence P by both arms. The fixed approval requires logical390x600 and verified runtime shape/mapping.

Expected: Wrong runtime host shape cannot authorize full-content or absence through the fallback.

Reach: Coverage/domain/absence misclassification only. Independent environment gate is F and blocks whole final delivery; no final acceptance bypass asserted.

`python3 -B validation/pooled-forward/qualification/review-6/checks/repro_existing.py --arm candidate-v13.5 --case A09-forged-runtime-shape`

## Preserved interpretation / harness records

The root-frame-disjoint-advisory F remains unresolved and is not a fifth confirmed bug. Initial ineligible offscreen mutation and allowed disjoint raster candidate Fs were expectation mistakes. The first390x600 fixture had one clipped anchor; corrected fresh run retains old17 rows. The first default run hit sandbox kern.boottime EPERM plus an incomplete inventory mock; its first failure remains. See raw adjudication files; no old outcomes were replaced.
