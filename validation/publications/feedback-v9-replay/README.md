# Immutable v9 replay with later live tools

The v10 skill adds live modules and updates the root README/workflow. verify.py materializes the original v9 inventory in a temporary source view, uses the exact original mutable publication aliases, restores the old live skill from validation/default-forward/baseline-v9, and restores the final v9 root README/workflow from historical-root.

It builds a temporary metadata-only Git index from archived literal bytes so the original verifier can check its original blob identities and scope. The real index, objects, commits, original v9 data, manifests, scores and failure records are not changed. Original file symlinks are archived as raw link bytes; active relative directory namespaces remain intact.

Run from repository root: python3 -B validation/publications/feedback-v9-replay/verify.py . This is a historical publication replay, with no SDK rerun and no new component acceptance claim.
