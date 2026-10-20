# Engineering attempts before the business design

These are infrastructure/developer failures, never new business defects or v5
treatment gains. All native attempt directories and original command records are
retained separately.

- The first new unit-test run raised two errors because `deepcopy` of an aliased
  Python action list preserved shared element identity. Copying each action fixed
  state assignment. The subsequent full suite passed 79 tests. This occurred before
  native validation and tool freeze; the original console was not archived.
- The default system Python lacked `yaml` for the skill-creator validator
  (`ModuleNotFoundError: No module named 'yaml'`). An isolated ignored validation
  venv with PyYAML 6.0.3 and Pillow 11.3.0 passed validation; no global install.
- An initial ad-hoc contact-sheet command assumed every step had
  `immediate_after`. Full-sweep steps legitimately do not; the command raised
  `KeyError: 'immediate_after'` before producing an image. The saved generic image
  indexer now includes that field only when present. Raw native evidence unchanged.
- A follow-up ad-hoc console summary assumed every Android sweep step had
  `state_id` and raised `KeyError: 'state_id'` after its image was saved. The summary
  uses optional fields; the typed checker had already evaluated all declared states
  successfully. Neither display-command failure changed any native capture.
