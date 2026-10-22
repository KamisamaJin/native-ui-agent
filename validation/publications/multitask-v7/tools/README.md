# Shared native environment adapters

`native_environment.py` converts only explicitly known native wire identifiers.
The first encoding is Compose `LayoutDirection` (`Ltr`/`Rtl`) to contract identifiers
(`ltr`/`rtl`). It preserves the original value, canonical value, encoding and
recognition flag. It does not rewrite an observation or infer a locale/direction.

```python
from tools.native_environment import direction, ENCODING

proof = direction(observation['configuration']['direction'], encoding=ENCODING)
actual_direction = proof['canonical']
# Compare actual_direction with the independent contract; retain proof alongside
# the environment input check. Unknown values remain unchanged, never a pass.
```

The separately sealed adoption in `validation/multitask-forward/shared-environment-v1`
fixes a shared independent-oracle integration error. The original frozen v7 Skill
bundle and primary scores are unchanged. The posthoc rescore is reported separately
from treatment benefit. Regression coverage includes actual predesign native wire
recordings; RTL equivalence has unit coverage, not a new native RTL trial.

Run `python3 -B validation/multitask-forward/test_shared_environment.py` from the
repository root. These helpers use the repository MIT license.
