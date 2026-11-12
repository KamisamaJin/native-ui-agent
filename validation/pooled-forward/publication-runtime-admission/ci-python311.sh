#!/usr/bin/env bash
set -euo pipefail
runtime_tool_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$runtime_tool_root/HOST"
runtime_admission_parent="$(mktemp -d "$runtime_tool_root/HOST/ci-python311.XXXXXX")"
exec python3.11 -B "$runtime_tool_root/admit_runtime.py" \
  --target linux-py311 \
  --output "$runtime_admission_parent/admission"
