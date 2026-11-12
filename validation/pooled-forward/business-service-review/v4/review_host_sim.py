#!/usr/bin/env python3
"""Independent bounded FIRST-D0 recovery cut matrix; no SDK forwarding."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
TOOLS = ROOT / "business-tools-v4"
base = types.ModuleType("test_blind_study")
base.__file__ = str(TOOLS / "test_blind_study.py")
text = Path(base.__file__).read_text()
old = 'ARTIFACTS = HERE / "HOST-SIM"'
assert text.count(old) == 1
exec(compile(text.replace(old, 'ARTIFACTS = Path(' + repr(str(OUT / "existing-suite-scratch")) + ')'), base.__file__, "exec"), base.__dict__)
sys.modules["test_blind_study"] = base
b = base.b
for name in ["test_domain_admission", "test_terminal_d0", "test_anchor_recovery"]:
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
original = sys.modules["test_anchor_recovery"]
DETAILS = {}


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n")
    return str(path)


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.records = []
    def addSuccess(self, test):
        super().addSuccess(test); self.records.append({"test": test.id(), "status": "passed"})
    def addFailure(self, test, err):
        super().addFailure(test, err); self.records.append({"test": test.id(), "status": "failed", "detail": self._exc_info_to_string(err, test)})
    def addError(self, test, err):
        super().addError(test, err); self.records.append({"test": test.id(), "status": "error", "detail": self._exc_info_to_string(err, test)})


def run_suite(cls, name):
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    summary = {"kind": "HOST/SIM", "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful(),
               "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False, "tests": result.records}
    put(OUT / (name + ".json"), summary); put(OUT / (name + ".log"), stream.getvalue())
    return summary


class IndependentRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.folder = OUT / "fixtures" / self._testMethodName
        self.patches = [patch.object(b.Study, "execute", side_effect=AssertionError("NO helper forwarding")), patch.object(b.subprocess, "run", side_effect=AssertionError("NO subprocess forwarding")),
                        patch.object(b.subprocess, "Popen", side_effect=AssertionError("NO subprocess forwarding")), patch.object(b, "guard_live", return_value=True)]
        for p in self.patches: p.start()
    def tearDown(self):
        for p in reversed(self.patches): p.stop()
    def begin(self, label="fixture", alias="A"):
        f = base.Fixture(self.folder / label)
        s = f.init(); s.admit("T1")
        ticket = s.enqueue("T1", alias, "diagnostic")
        return f, s, ticket
    def failed(self, request, profile, argv, folder):
        put(Path(folder) / "service/failure.log", "HOST/SIM failed initial collector; no SDK or native execution\n")
        raise RuntimeError("HOST/SIM legitimate terminal initial failure")
    def cut_append(self, s, kind):
        append = s.append
        def stop(event, **values):
            if event == kind: raise OSError("HOST/SIM exact stop before " + kind)
            return append(event, **values)
        return patch.object(s, "append", side_effect=stop)
    def at(self, result, seconds):
        return patch.multiple(b.time, clock_gettime=lambda *args: result["finished_at_clock"] + seconds, time=lambda: result["finished_at_unix"] + seconds)
    def result(self, s, ticket):
        path = s.root / "requests" / ticket["request_id"] / "result.json"
        return path, b.load(path)
    def assert_anchor(self, s, ticket, result, alias="A"):
        anchor = s.one("T1", alias, "repair_started")
        self.assertIsNotNone(anchor)
        self.assertEqual(anchor["d0_request_id"], ticket["request_id"])
        self.assertEqual(anchor["deadline_clock"], result["finished_at_clock"] + 1200)
        self.assertEqual(anchor["deadline_at_unix"], result["finished_at_unix"] + 1200)
        self.assertEqual(len(s.history("T1", alias, "repair_started")), 1)
        return anchor

    def test_original_v3_plus1301_counterexample_is_closed_for_both_arms(self):
        records = []
        for alias in ["A", "B"]:
            f, s, ticket = self.begin(alias, alias)
            component = Path(s.arm("T1", alias)["source_roots"][0]) / "Opaque.txt"
            initial_sha = b.sha(component)
            with self.cut_append(s, "repair_started"):
                with self.assertRaisesRegex(ValueError, "recovery proof"):
                    s.serve(self.failed)
            path, result = self.result(s, ticket)
            self.assertTrue(s.d0_complete("T1", alias))
            self.assertIsNone(s.one("T1", alias, "repair_started"))
            fresh = b.Study(s.root)
            with self.at(result, 1301):
                with self.assertRaisesRegex(ValueError, "sealed"):
                    fresh.enqueue("T1", alias, "diagnostic")
                with self.assertRaisesRegex(ValueError, "sealed"):
                    fresh.feedback_ready("T1", alias)
            anchor = self.assert_anchor(fresh, ticket, result, alias)
            self.assertEqual(anchor["d0_result"], {"path": str(path), "sha256": b.sha(path)})
            self.assertIsNotNone(fresh.one("T1", alias, "source_locked"))
            self.assertIsNone(fresh.one("T1", alias, "repair_unlocked"))
            self.assertFalse(component.stat().st_mode & 0o222)
            self.assertEqual(b.sha(component), initial_sha)
            self.assertEqual(len([e for e in fresh.history("T1", alias, "request_enqueued") if e["action"] == "diagnostic"]), 1)
            other = "B" if alias == "A" else "A"
            self.assertIsNone(fresh.one("T1", other, "repair_started"))
            records.append({"arm": alias, "first_ticket": ticket["request_id"], "original_result": {"path": str(path), "sha256": b.sha(path)}, "recovered_anchor": anchor,
                            "source_frozen_before_D1_and_unlock": True, "source_sha256": initial_sha})
        DETAILS["original_v3_counterexample_closed"] = records

    def test_result_before_finish_recovery_keeps_remaining_window_patch_D1_final(self):
        records = []
        for alias in ["A", "B"]:
            f, s, ticket = self.begin(alias, alias)
            save = b.save
            def stop_after_result(path, value):
                save(path, value)
                if Path(path).name == "result.json": raise OSError("HOST/SIM complete result, no finished event")
            with patch.object(b, "save", side_effect=stop_after_result):
                with self.assertRaises(OSError): s.serve(self.failed)
            path, result = self.result(s, ticket)
            self.assertEqual(s.history("T1", alias, "request_finished"), [])
            fresh = b.Study(s.root)
            f.study = fresh
            with self.at(result, 275):
                ack = fresh.feedback_ready("T1", alias)
            anchor = self.assert_anchor(fresh, ticket, result, alias)
            self.assertEqual(ack["deadline_clock"] - ack["at_clock"], 925)
            self.assertTrue(fresh.history("T1", alias, "request_finished")[0]["recovered_from_prepared_result"])
            component = Path(fresh.arm("T1", alias)["source_roots"][0]) / "Opaque.txt"
            component.write_text("HOST/SIM repair after original-clock recovery " + alias)
            with self.at(result, 400):
                fresh.enqueue("T1", alias, "diagnostic")
                d1 = fresh.serve(f.execute)
                fresh.lock_source("T1", alias)
                fresh.enqueue("T1", alias, "final")
                final = fresh.serve(f.execute)
            self.assertTrue(all(not o.get("error") for o in d1["outcomes"]))
            self.assertTrue(all(o["accepted"] for o in final["outcomes"]))
            self.assertEqual(fresh.one("T1", alias, "repair_started"), anchor)
            for call in [c for c in f.calls if c["action"] == "final"]:
                self.assertEqual("--previous" in call["argv"], alias == "A")
                self.assertEqual("--history" in call["argv"], alias == "A")
                self.assertNotIn("--fresh", call["argv"])
            with self.assertRaisesRegex(ValueError, "sealed"):
                fresh.feedback_ready("T1", alias)
            records.append({"arm": alias, "ack": ack, "anchor": anchor, "remaining_seconds": 925, "original_result_sha256": b.sha(path)})
        DETAILS["original_remaining_window_repair_D1_final"] = records

    def test_before_preparation_missing_and_truncated_results_never_rewrite_or_retry(self):
        for kind in ["before_preparation", "prepared_missing", "prepared_truncated"]:
            f, s, ticket = self.begin(kind)
            save = b.save
            def cut_result(path, value):
                if Path(path).name == "result.json":
                    if kind == "prepared_truncated": Path(path).write_text('{"HOST_SIM":"partial')
                    raise OSError("HOST/SIM aggregate cut")
                return save(path, value)
            hook = self.cut_append(s, "d0_result_prepared") if kind == "before_preparation" else patch.object(b, "save", side_effect=cut_result)
            with hook:
                with self.assertRaises(OSError): s.serve(self.failed)
            path = s.root / "requests" / ticket["request_id"] / "result.json"
            original_bytes = path.read_bytes() if path.exists() else None
            fresh = b.Study(s.root)
            with self.assertRaises(ValueError): fresh.feedback_ready("T1", "A")
            with self.assertRaises(ValueError): fresh.enqueue("T1", "A", "diagnostic")
            with self.assertRaises(ValueError): fresh.serve(self.failed)
            self.assertEqual(path.read_bytes() if path.exists() else None, original_bytes)
            self.assertIsNone(fresh.one("T1", "A", "repair_started"))
            self.assertEqual(len(fresh.pending("T1", "A")), 1)
            self.assertFalse((Path(fresh.arm("T1", "A")["source_roots"][0]) / "Opaque.txt").stat().st_mode & 0o222)

    def test_missing_original_outcome_cannot_be_added_later_to_upgrade_D0(self):
        f, s, ticket = self.begin()
        save = b.save
        omitted = {}
        def omit(path, value):
            if Path(path).name == "outcome.json" and Path(path).parent.name == "ios":
                omitted["path"], omitted["value"] = Path(path), copy.deepcopy(value)
                return
            return save(path, value)
        with patch.object(b, "save", side_effect=omit): s.serve(self.failed)
        prepared = s.history("T1", "A", "d0_result_prepared")[0]
        self.assertIsNone(prepared["outcome_files"]["ios"])
        self.assertFalse(s.d0_complete("T1", "A"))
        save(omitted["path"], omitted["value"])
        fresh = b.Study(s.root)
        with b.lock(fresh.root / "state.lock"): fresh.expire()
        self.assertFalse(fresh.d0_complete("T1", "A"))
        fresh.enqueue("T1", "A", "diagnostic"); fresh.serve(f.execute)
        self.assertIsNone(fresh.one("T1", "A", "repair_started"))
        with self.assertRaisesRegex(ValueError, "D0 is pending"): fresh.feedback_ready("T1", "A")

    def test_existing_anchor_hash_corruption_rejects_foreground_and_restart_watchdog(self):
        f, s, ticket = self.begin()
        s.serve(self.failed)
        anchor = s.one("T1", "A", "repair_started")
        path = s.root / "events" / (f"{anchor['sequence']:06d}.json")
        value = b.load(path); value["d0_result"]["sha256"] = "0" * 64
        path.chmod(0o644); base.put(path, value)
        fresh = b.Study(s.root)
        with self.assertRaisesRegex(ValueError, "immutable FIRST D0"): fresh.feedback_ready("T1", "A")
        with self.assertRaisesRegex(ValueError, "immutable FIRST D0"): b.watch(s.root)
        self.assertIsNone(fresh.one("T1", "A", "repair_unlocked"))
        self.assertFalse((Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt").stat().st_mode & 0o222)

    def test_stable_cached_watchdog_expires_original_deadline(self):
        f, s, ticket = self.begin()
        s.serve(self.failed)
        _, result = self.result(s, ticket)
        anchor = copy.deepcopy(s.one("T1", "A", "repair_started"))
        elapsed = [100]
        calls = [0]
        def next_iteration(seconds):
            calls[0] += 1
            if calls[0] == 1: elapsed[0] = 1301
            else: raise RuntimeError("HOST/SIM stop after cached expiry iteration")
        with patch.object(b.time, "clock_gettime", side_effect=lambda *args: result["finished_at_clock"] + elapsed[0]), patch.object(b.time, "time", side_effect=lambda: result["finished_at_unix"] + elapsed[0]), patch.object(b.time, "sleep", side_effect=next_iteration):
            with self.assertRaisesRegex(RuntimeError, "cached expiry"): b.watch(s.root)
        self.assertEqual(s.one("T1", "A", "repair_started"), anchor)
        self.assertEqual(s.one("T1", "A", "source_locked")["reason"], "repair_deadline")
        self.assertFalse((Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt").stat().st_mode & 0o222)
        self.assertEqual(calls[0], 2)
        DETAILS["watchdog_cached_original_deadline"] = {"anchor": anchor, "source_lock": s.one("T1", "A", "source_locked"), "iterations": calls[0]}


if __name__ == "__main__":
    frozen = run_suite(original.AnchorRecoveryTests, "frozen-anchor-13-tests")
    independent = run_suite(IndependentRecoveryTests, "independent-recovery-tests")
    put(OUT / "observations.json", DETAILS)
    passed = frozen["passed"] and independent["passed"]
    put(OUT / "RESULT.json", {"kind": "independent-v4-bounded-anchor-recovery-review", "passed": passed, "suites": {"frozen_anchor": frozen, "independent": independent},
                              "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False, "business_data_access": False})
    print(json.dumps({"frozen_anchor": {k: frozen[k] for k in ["tests_run", "failures", "errors", "passed"]}, "independent": {k: independent[k] for k in ["tests_run", "failures", "errors", "passed"]}}))
    raise SystemExit(0 if passed else 1)
