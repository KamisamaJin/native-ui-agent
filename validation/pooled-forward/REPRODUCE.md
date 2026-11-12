# Replaying v13 without re-running a trial

The released implementation is `native-ui-agent/`; `candidate-v13.9/` is its
exact frozen study copy. The comparison is `baseline-v12.6-common-6/`, including
the separately listed common correctness floor. It is not an unmodified older
release or a no-skill control.

From the repository root:

```sh
python3 -B validation/pooled-forward/verify_sources.py
python3 -m pip install -r native-ui-agent/scripts/requirements.txt 'Pillow==11.3.0'
python3 -B -m unittest discover -s native-ui-agent/tests -v
```

Linux Python3.11 has a separate current-runtime qualification. It checks the
frozen mechanisms and golden evidence without claiming an iOS SDK run:

```sh
bash validation/pooled-forward/publication-runtime-admission/ci-python311-v2.sh
```

The final closed publication supplies `PUBLICATION.json` and its external
`PUBLICATION.sha256`. The manifest is produced after judgment and original live binding close;
its cleanup metadata is separate from product delivery. Choose a new disposable
output directory with enough disk for decoded archives and the readonly restore:

```sh
read -r publication_sha < validation/pooled-forward/PUBLICATION.sha256
python3 -B validation/pooled-forward/verify_publication.py \
  --manifest-sha256 "$publication_sha" --output /ABSOLUTE/NEW/pooled-v13-replay
```

The verifier decodes the lossless cold transports, checks every inner archive,
restores the original absolute **keys** into a separate readonly namespace,
and replays the recorded public controller, original native historical view,
both independent review barriers and fixed five-case metric arithmetic. Embedded
JSON and original evidence bytes are not rewritten. There is no original-path
fallback, SDK invocation, source editing, new UI sample or cleanup action.
Failures and partial restores remain in the requested output directory.

The map session hashes the complete externally pinned map at its boundaries and
requires unchanged no-follow POSIX file/namespace identities around every access.
Every payload still receives its original byte/hash/mode checks and a complete
final verification. This is common publication I/O, not either arm's native
collection improvement. The assumption is an ordinary local POSIX filesystem;
it is not an adversarial same-user filesystem sandbox.

Recorded provenance and metric replay do not independently establish a product
judgment. The original independent judgments, disagreements, unsupported
observations, source/image projections and live binding results remain sealed.
Portable **source-domain and source-responsibility grading is unsupported**:
those frozen backends require original production paths and parent proofs.
Archive replay never reports current-source delivery validity. Live binding must
complete before the original owned workspaces are cleaned.

The gallery uses a prospective deterministic selection: private snapshot0 of
each I/X/Y version and platform, or an explicit missing slot. Its PNG bytes are
unchanged. It is a preview, not a design oracle or complete state inspection.

To run a new study, create new device/resource/workflow roots, independently
freeze new requirements and inputs, produce a natural initial PR before any
render, and pair byte-identical copies. An immutable historical packet must not
be relabeled as a fresh observation of a current project. Use the production
integration guide at `native-ui-agent/references/pooled-workflow.md` for device
ownership, platform invalidation, finite independently authorized packet
validity and the default repair state machine.

Large raw SDK captures, logs and failed intermediate records are preserved in
the declared cold transports. Shared SDK/JDK/Gradle caches, runtime images,
signing material and full upstream Git object databases are not publication
obligations. Main-repository Git data and user resources are not cleanup targets.

The original main readonly replay was fully verified before its original selected
cache files were removed. Surviving benchmark/qualification/rejected-cohort files
have a separate lossless original-data supplement. Terminal records retain the
complete disk streams, exact-prefix public-window derivation, original maps,
cleanup intents/failures and common storage controls. Additional transports are
byte-verified but do not become current product evidence or a second main view.

CI disposes only its verified `$RUNNER_TEMP/pooled-v13-replay` decoded/payload
subtrees before legacy checks, with a manifest-bound exact inventory. Its cold
checkout and compact receipts remain unchanged; 34 small controls cover writable
Git inputs, readonly outputs, wrong roots, links, races and partial failure.
The helper is intentionally CI-only; do not simulate CI environment variables
to clean an unrelated local directory. Budget for roughly12GiB of main restored
payload plus metadata and cold/decoded storage on a fresh checkout.

To inspect a supplemental original namespace, use the corresponding verified
`<transport-id>/decoded` directory with `publication-tools/archive.py restore`,
its published `index_sha256`, a fresh destination and `--read-only`. Supplemental
transports are not merged into the main current-view resolver. Structural
symlink/FIFO records remain inert metadata and must not be activated.

The frozen historical `RECORDED-PROVENANCE.json` retains
`meter_terminal_and_postcleanup_control_supplement_pending: true` and
`cleanup_authorized: false` from that producer schema. Those original bytes are
not edited into a final closure claim. The final manifest separately verifies
the terminal transport and references the actual closed meter/cleanup receipts;
cleanup authorization comes from the explicit ownership/policy/operator guards.
A provenance replay alone never authorizes deletion.
