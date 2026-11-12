# Additive geometry encoding and neutral-domain admission

This is a pre-next-SDK clarification of `observed-strip-chain-1`. Its original
document/seal and original failed packet remain unchanged. No implementation,
candidate result, new native sample or performance material was read. The data
artifacts here define a fixed admissible representation and a neutral-only domain
approval; they do not claim actual provider conformance or a native pass.

## Pixel-cell geometry compatibility

Use encoding ID `native-rect-pixel-cell-enclosure-v1`. The provider must declare
its numeric representation, native coordinate space, original rectangle fields,
verified native-to-PNG mapping and provenance. The following are admissible:

* Native CGRect/CGFloat values transported as finite, losslessly round-trippable
  IEEE-754 binary64 numbers, with original x/y/width/height retained. An explicitly
  declared lossless promotion of a native binary32/integer value is also valid;
  record that original precision and do not infer extra measurement precision.
* Exact native integer-pixel rectangles with an explicitly verified raster map.

Unknown encoding, truncated decimal transport, null/non-finite geometry, guessed
coordinate origins or unsupported mapping stays U. Do not infer the encoding by
fitting this failure or its best matching displacement. Existing independently
specified native encodings may be supported only by an explicit fixed adapter;
this approval does not silently convert arbitrary floats, densities or endpoints.

Decode a declared binary64 value to its exact represented rational value (the
lossless floating-point bit value, not a rounded decimal display). Perform all
projection/enclosure arithmetic exactly over those rationals. Let the provider's
verified axis-aligned map to the PNG viewport be `(u,v)=(sx*x+ox,sy*y+oy)` with
positive scale, fixed provenance and no rotation/shear. The original viewport
crop must map to an integral pixel rectangle with unchanged W/H across the link.
No fitted scale, arbitrary crop, interpolation or image warp is permitted.

For any projected scalar q, define the closed pixel-boundary enclosure
`Q(q)=[floor(q),ceil(q)]`. Integral q has a singleton enclosure. The interval is
the deterministic pixel-cell enclosure of the recorded value; it is not an
estimated measurement error or a new design tolerance. It never changes the raw
native number. In particular, do not calculate an observed maximum error and
add it to q, subtract a fitted epsilon before floor/ceil, or reuse a rounded
endpoint difference as the source width/height.

For a native rectangle `(x,y,w,h)`, compute projected origin `(u,v)` and DIRECT
projected size `(a,b)=(sx*w,sy*h)`. Its admissible positive integer-pixel rectangles
are all half-open boxes `[L,R)×[T,B)` satisfying:

```
L ∈ Q(u)       R ∈ Q(u+a)       R-L ∈ Q(a)       R > L
T ∈ Q(v)       B ∈ Q(v+b)       B-T ∈ Q(b)       B > T
```

This couples edges to the original size fields. Every set is finite; each scalar
enclosure has at most two integer endpoints. Empty sets are unavailable. The
raw native rectangle must itself be strictly inside the native viewport, as
well as inside the image mapping; a producer's tolerant `fully_visible` flag
alone cannot admit a clipped anchor. Retain original native/raw/image records.

For a proposed integer down-translation D, a repeated leaf must admit one common
pixel rectangle in frame i and that SAME rectangle translated by `(0,-D)` in
frame i+1. Equivalently the complete rectangle candidate sets must intersect
after translation. All corresponding projected edge displacement intervals AND
directly projected width/height constraints must hold. Horizontal translation
is zero. Do not check only a center, top edge or median displacement.

Apply this to ALL eligible common leaf/control identities. Require a jointly
consistent assignment preserving their actual order and independent disjoint
vertical witness boxes. The at-least-two-leaves condition still applies; repeated
wrappers or two overlapping support boxes cannot satisfy it. All repeated
identities across the whole state must admit the SAME registered world rectangle
after applying the accumulated verified translations, with stable attributes and
root membership. An empty global intersection or incompatible order is U, even
if individual adjacent pairs look convenient.

The unique D is established by EXACT full-width raster overlap among all
geometry-admissible integer candidates. Do not accept `round(653.0000000000002)`
as proof of D=653. Scalar subtraction may propose search candidates but cannot
approve a link. If zero or multiple candidates satisfy the exact raster and all
native constraints, the link is U. RGBA comparisons, source images, crop/mapping,
candidate sets and rejection reasons must be retained and recomputable.

Why this handles numeric noise: a serialized CGRect may straddle an integer
pixel boundary even when its source arithmetic has a tiny cancellation residual.
The fixed enclosure records its pixel-boundary possibilities without pretending
the native float was exact-integer motion. The actual integer raster comparison
then supplies the unique observed translation. No value is learned from this
sample and no nonzero pixel mismatch is accepted.

This proves only pixel-registration compatibility. It does NOT prove exact native
rectangle equality, effective padding, font or physical hit geometry. Those
assertions keep their original raw values and design tolerances. A subpixel
native/style issue may remain a separate F/U while rendered coverage is proven;
coverage cannot vote it away. The closed immutable-domain and boundary premises
remain required, and observed-strip scope is unchanged.

## Executable neutral-only domain approval

`DOMAIN-APPROVAL.json` binds the unchanged supported neutral design lock, the exact
normal and controlled-repair production component hashes, exact thin bridge
hashes, fixed fixture/action/environment identities and a normative common host
shape. It authorizes only the finite input-driven 18-row, single-outer-vertical-
scroll neutral domain. It approves no business app or arbitrary source/project.

The shape is specified from the existing public observer ABI, not an unseen
implementation: the actual production component is called once inside the
observed main scroll; host receipt/update controls are outside it; the terminal
sentinel follows all component content; requested viewport/environment are fixed;
host-owned indicators are deterministically hidden. No nested/off-axis scroll,
sticky/occluding layer, live data or asynchronous content mutation is authorized.

The general service must load the externally pinned approval and independently
rebuild actual current subject binding. Match ONE exact approved production
revision for that platform plus its exact bridge, actual imported module/entry,
current source/build/fixture/plan/environment identity and verified host shape.
Hashing a conveniently placed unused file or accepting a caller-declared hash is
not binding. Existing measured source roots/import/build receipts and the source
responsibility boundaries must establish the actual component used by the host.
The common host's current code/template hashes and runtime shape/mapping records
must be pinned and independently checked against the normative shape before
fallback acceptance. A self-entered shape name or matching schema is not proof.

This artifact approves the expected semantic host shape, not unseen host bytes.
Provider conformance and exact shared-foundation bytes in BOTH arms remain an
admission condition. If that binding is absent, wrong or stale, mandatory full
coverage via this fallback remains U/error. No wildcard, path-prefix, normal/
repair source substitution or declaration that an arbitrary project is finite
can satisfy the approval.

Both authored component revisions are enumerated because either is still finite
and input-driven. The repair-control increment-by-two behavior keeps the original
count-one oracle and can correctly FAIL it. Domain approval is not behavioral
approval, source-change evidence reuse, a repair completion or permission to
change expectations. A change between those sources still invalidates old native
credit and requires the normal fresh source-repair recheck. Any other source
bytes need a new independent domain approval before fallback, even if a repair
seems plausible. The artifact does not authorize blanket capture reuse.

`CONFIG-REFERENCE.json` supplies an additive independently pinned external
`coverage_domain_ref`; the original design lock and all 104 values remain intact.
The admission owner resolves the actual component/bridge/host subjects using the
existing execution/source configuration, retains the approval digest outside the
implementation's editable evidence and verifies the provider. No actual current
source/host conformance receipt or SDK result is supplied by this author.
