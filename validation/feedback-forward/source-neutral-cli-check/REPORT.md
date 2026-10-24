# CLI regression against the sealed neutral fixture

All 14 recorded checks passed: True. No original fixture, proposition, expected value, submission, or source was changed. Original folder inventory, every file SHA (including its seal), retained symlink identity, and the original seal map were checked before and after and remained exactly unchanged.

| Invocation | Exit | JSON inspection |
| --- | --- | --- |
| Honest source catalog | 0 | Exactly equal to the original catalog |
| Honest bind | 1 | `not_accepted`; 6 passed, 0 failed, 1 unknown; formatter-localization blocks |
| Bind without submission | 2 | No output created; concise usage error, no traceback |
| Existing all-unknown submission | 1 | `not_accepted`; 0 passed, 0 failed, 7 unknown; all seven block |

The two blocked commands wrote their gate JSON and exited nonzero. Their payloads exactly match the sealed earlier gates. This confirms the revised CLI boundary without inferring semantics from process exit alone. The missing-submission stderr is preserved verbatim in `commands/03-missing-submission.json` and `results.json`.

The current shared tool byte SHA256 is `04e9d7829c318c73ff86c41ee9b134bc66857a276256a19d66f3cfc4df6af3ca`. `tool-identity.json` also records the earlier tool SHA and the current size/time. Exact argv, cwd, Unix start/end times, stdout, stderr and exit codes are in `commands/`. `run_cli_regression.py` preserves the controller source. No SDK, device, business design, product implementation, source edits, subagents, commits, or agent-message tools were used.

The earlier dishonest-review limitation remains documented in the sealed original report and was not retested or reinterpreted. These CLI changes provide no additional source-semantic, rendered-style, or native-runtime proof. This follow-up observed no additional CLI error in the requested invocations.

`SEAL.json` is written last and hashes every other readable file in this new folder. Its own bytes are necessarily excluded. `controller-record.json` preserves the controller invocation and its complete stdout/stderr.
