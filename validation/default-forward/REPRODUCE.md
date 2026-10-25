# Reproduce

Portable replay requires Python 3.11 and Pillow (requirements under native-ui-agent/scripts). From repository root:

```sh
python3 -B -m unittest discover -s native-ui-agent/tests -v
python3 -B validation/default-forward/test_metrics.py
python3 -B validation/default-forward/probe-design/verify_manifest.py
python3 -B validation/default-forward/probe-review/replay_after.py --output validation/default-forward/cache/replay-new
python3 -B validation/default-forward/design/verify_design.py
python3 -B validation/default-forward/verify.py
python3 -B validation/default-forward/execution_audit.py > validation/default-forward/cache/execution-recomputed.json
python3 -B validation/default-forward/costs.py > validation/default-forward/cache/costs-recomputed.json
python3 -B validation/default-forward/derive_results.py > validation/default-forward/cache/results-recomputed.json
python3 -B validation/default-forward/build_docs.py --check
python3 -B validation/default-forward/artifacts.py --tracked
```

Output paths must be fresh. The replay asserts original F/U, rather than requiring the component to pass. JSON outputs must equal their original published counterparts. Neutral replay replaces native transport with a disclosed synthetic fixture. Portable CI performs no SDK rerender.

For a fresh actual native run, use a Mac with the recorded toolchain/runtime and create a new owned simulator. Bootstrap pinned upstreams with validation/dispatch-forward/bootstrap.py, supplying actual --java-home and --android-sdk (omit --local-upstreams to fetch pinned sources). Copy the selected source capsule's two production roots into that workspace and verify its entire source map. Use the unchanged design/public or design/private plan/lock/routes/fixture/bridge plus actual native options to construct the config described in native-ui-agent/references/default-feedback.md. Then use ui_loop.py native --config CONFIG --output NEW_DIR; final uses --final. Do not reuse historical process/fixtures/images or original simulator IDs. SDK products must be rebuilt from pinned inputs; build-cache hashes in recorded manifests are observed cache identities, not a promise to publish SDK binaries.

All stage/member file hashes and source/image identities are recorded. Original participant sources, first actuals, independent panels and strict numeric alarm remain unchanged. Root tools and metric algorithms were released before business design. Two design revisions are preserved; v2 completeness review preceded initial code. The post-source scripts only normalize evidence, bind original actuals, conservatively combine frozen judgments and format results. Nonempty confirmed-defect/extra-finding cases require explicit independent common-cause matching, not automatic zeroing.

Source/API module outputs already included in explicit seals are retained as compiler evidence. Simulator/SDK/runtime/build caches and full upstream checkouts are excluded. See NOTICE.md and repository THIRD_PARTY_NOTICES.md. Three owned study simulators were deleted after actual captures; no user devices were touched.
