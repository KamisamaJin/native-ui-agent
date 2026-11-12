V7 extends the compatible verification call with an optional keyword-only provenance_authorities argument. Empty v7 provenance proofs still support verify_derivation(reader, row). A nonempty provenance proof must fail without caller-bound context. Never obtain the allowed context from the proof row or from a worker claim.

After independently verifying the external all15 selection/spec pins, current root/cause/code/group bindings and original/derived document manifest, use the exact pinned batch module:

```python
spec = batch.pinned(reader, selected_row['spec'])
derivations = batch.pinned_value(reader, selected_row['derivations'])
authorities = batch.selected_provenance_authorities(reader, spec, derivations)
for derivation in derivations:
    batch.verify_derivation(
        reader, derivation, provenance_authorities=authorities)
```

package_selected already performs this handoff before any packet is written. A separate consumer such as the dispatcher must adopt and independently validate this call pattern with the new batch/schema pins. Its existing all15 packet/ledger/policy/actor/input/cause checks remain required. No consumer was modified or audited in this v7 task.

SPEC.provenance_authorities is operator-only selection data. It contains operation refs plus public result/event refs generated from the verified source protocol. The helper requires operation membership to match selected operation-result derivations and documents; it matches public outcomes by exact JSON values and checks pinned event scope/result binding. Provenance registry replay then pins original target bytes, including original inventory members. The helper assumes the externally pinned spec was produced/admitted through the gated selection protocol; it cannot bless an arbitrary attacker-authored spec or replace external authority.

The existing emitter_admission gains provenance_reference_changes and provenance_authorities. Raw/derived refs, fixed outer outcome selection, existing key-map admission and bounded projection proofs remain. ALL-SPECS/ALL-PACKETS index shapes and top-level code-pin keys remain unchanged; the SPEC gains the explicit private authority field. Prepare fresh all15 material under this admitted revision. Never retag old actual derivations or infer evidence validity from an opaque reference. Unsupported/dangling worker locators still fail and need separately reviewed presentation metadata responsibility.
