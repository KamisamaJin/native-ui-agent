# State evidence planning

Use this when selected business states require several independent native facts,
especially after a caller replacement or when related targets are far apart.
The caller agent chooses relevant states and translates the independent design.
The compiler checks that declared matrix; it cannot establish that prose has
been translated completely or that a supplied expectation/source is correct.

## Compile before feedback

Write a matrix with `version:1`, `states`, `requirements`, `required_state_ids`
and `required_requirement_ids`. Every selected state × requirement becomes a
cell. A requirement names its source and an atomic native check. A constant
`check.expected` applies across selected states; `by_state` can override expected,
target, action_index, stimulus, required_method or op. Without a default, every
applicable state needs its own expected value. `not_applicable` maps state IDs to
nonempty reasons; those cells remain in the ledger for independent review.

```json
{
  "version":1,
  "required_state_ids":["after-request","after-replacement"],
  "required_requirement_ids":["status","action-enabled"],
  "states":[
    {"id":"after-request","input_index":0,"after_action":0,"coverage":"targets"},
    {"id":"after-replacement","input_index":1,"after_action":1,"coverage":"targets"}
  ],
  "requirements":[
    {"id":"status","source":"Independent public status contract",
     "check":{"kind":"control","target":{"identifier":"actual.status"},
              "property":"label","expected":"Ready"},
     "by_state":{"after-replacement":{"expected":"Paused"}}},
    {"id":"action-enabled","source":"Independent enablement contract",
     "check":{"kind":"control","target":{"identifier":"actual.action"},
              "property":"enabled","expected":true},
     "by_state":{"after-replacement":{"expected":false}}}
  ]
}
```

```sh
python3 scripts/state_plan.py --matrix matrix.json --actions original-actions.json \
  --output fresh-plan
```

`plan.json` contains every applicable atomic check and required ID, plus a
SHA-bound declared matrix/disposition ledger. `actions.json` adds exact state
names and deduplicated `after_targets` from relevant checks. It preserves action
routes and callback requests; it adds no business expectation to the observer.
The output directory must be fresh. Original action names that disagree with
the matrix are rejected. A state can use `stimulus_action` to identify an earlier
requested stimulus separately from its explicit full-sweep observation action.

Choose actual producer state IDs and action indices. Initial and explicit sweep
states may use `coverage:"full_content"`. Other actions use `coverage:"targets"`.
Compilation does not insert full sweeps or establish missing native capabilities.
Preserve the matrix and plan before reviewing rendered feedback; changing an
expectation later needs a separate requirement reason, not a better test score.

## Collect and judge

Run the native observer with the generated actions, then `native_checks.py` with
the generated plan. The observer records the immediate action result and original
callback interval, then observes each target. Native frames can jointly establish
facts for targets that cannot fit in one viewport. All frames must have the exact
same native input/process/event binding. Input drift, wrong state/action, torn
image/hierarchy captures and conflicting values remain U.

Only actual matching native facts earn a verdict. The producer's
`all_targets_observed:true` flag alone is not evidence. Unseen targets cannot prove
absence without complete native full-content coverage. An oversized target may
have its center observed while full visibility remains false. Joint target frames
never establish complete content, effective padding/fonts or physical hit areas.

Callbacks still require demonstrated requested dispatch. Current labels and
enabled/selected native facts are separate observations; a label after a blocked
action is not proof that its handler executed or that zero callbacks passed.

The check report retains all failed and unassessed IDs and exports
`machine_findings` for failed typed-native checks, one record per actual state and
aspect. Preserve this report with its observation hash in the agent's review.
Keep manual visual findings separate; duplicate root causes can be grouped for
repair while their distinct state checks remain visible. A later shared repair
does not retroactively establish that another state was reviewed or detected.

Multi-target navigation costs additional work. Limit targets to the independently
planned aspects relevant to that state and retain the shared scroll budget,
unavailable targets, full-state coverage and command wall time. Do not shrink
content, bypass required states or drop U rows to improve coverage or speed.
