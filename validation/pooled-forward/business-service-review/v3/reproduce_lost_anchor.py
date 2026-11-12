#!/usr/bin/env python3
"""Independent first-D0 durability-boundary reproduction; no SDK forwarding."""
import importlib.util
import json
from pathlib import Path
import sys
import types
from unittest.mock import patch

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
TOOLS = ROOT / "business-tools-v3"
base = types.ModuleType("test_blind_study")
base.__file__ = str(TOOLS / "test_blind_study.py")
source = Path(base.__file__).read_text()
old = 'ARTIFACTS = HERE / "HOST-SIM"'
assert source.count(old) == 1
exec(compile(source.replace(old, 'ARTIFACTS = Path(' + repr(str(OUT / "suite-scratch")) + ')'), base.__file__, "exec"), base.__dict__)
b = base.b
sys.modules["test_blind_study"] = base


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n")
    return str(path)


def reproduce():
    f = base.Fixture(OUT / "lost-anchor-fixture")
    with patch.object(b.Study, "execute", side_effect=AssertionError("NO helper execute forwarding")), patch.object(b.subprocess, "run", side_effect=AssertionError("NO subprocess forwarding")), patch.object(b.subprocess, "Popen", side_effect=AssertionError("NO subprocess forwarding")), patch.object(b, "guard_live", return_value=True):
        s = f.init()
        s.admit("T1")
        d0 = s.enqueue("T1", "A", "diagnostic")
        append = s.append
        def stop_before_anchor(kind, **value):
            if kind == "repair_started":
                raise OSError("HOST/SIM process stops after durable D0 result/event before anchor write")
            return append(kind, **value)
        def runtime_crash(request, profile, argv, folder):
            put(Path(folder) / "service/initial-crash.log", "HOST/SIM initial crash log; no native execution\n")
            raise RuntimeError("HOST/SIM initial runtime failure")
        with patch.object(s, "append", side_effect=stop_before_anchor):
            try:
                s.serve(runtime_crash)
            except OSError as error:
                initial_error = str(error)
            else:
                raise AssertionError("Failure injection did not reach anchor durability boundary")
        d0_result = b.load(s.root / "requests" / d0["request_id"] / "result.json")
        assert s.d0_complete("T1", "A") is True
        assert s.one("T1", "A", "repair_started") is None
        assert s.pending("T1", "A") == []
        component = Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt"
        assert not component.stat().st_mode & 0o222
        # The original fixed D0 deadline has already elapsed. A new process
        # still has only durable original D0 records, not a valid new budget.
        with patch.object(b.time, "clock_gettime", return_value=d0_result["finished_at_clock"] + 1301), patch.object(b.time, "time", return_value=d0_result["finished_at_unix"] + 1301):
            restarted = b.Study(s.root)
            d1 = restarted.enqueue("T1", "A", "diagnostic")
            restarted.serve(f.execute)
            late_anchor = restarted.one("T1", "A", "repair_started")
            unlocked = restarted.feedback_ready("T1", "A")
        observed = {"kind": "independent-HOST/SIM-first-D0-anchor-durability-counterexample", "protocol_conforming": False,
                    "candidate_helper_sha256": b.sha(TOOLS / "blind_study.py"), "injected_boundary": initial_error,
                    "first_d0_request_id": d0["request_id"], "d0_finished_at_clock": d0_result["finished_at_clock"],
                    "required_original_deadline_clock": d0_result["finished_at_clock"] + 1200,
                    "first_result_path": str(s.root / "requests" / d0["request_id"] / "result.json"),
                    "first_result_sha256": b.sha(s.root / "requests" / d0["request_id"] / "result.json"),
                    "d0_durably_complete_before_restart": True, "d1_request_id": d1["request_id"], "observed_late_anchor": late_anchor,
                    "observed_unlock": unlocked, "source_writable_after_original_deadline": bool(component.stat().st_mode & 0o222),
                    "deadline_extension_seconds": late_anchor["deadline_clock"] - (d0_result["finished_at_clock"] + 1200),
                    "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False}
        assert observed["deadline_extension_seconds"] == 1301
        assert observed["source_writable_after_original_deadline"] is True
        assert late_anchor["d0_request_id"] == d1["request_id"] != d0["request_id"]
        put(OUT / "LOST-ANCHOR-COUNTEREXAMPLE.json", observed)
        print(json.dumps({"counterexample_reproduced": True, "deadline_extension_seconds": observed["deadline_extension_seconds"], "source_unlocked_after_original_deadline": True}))
        return observed


if __name__ == "__main__":
    reproduce()
