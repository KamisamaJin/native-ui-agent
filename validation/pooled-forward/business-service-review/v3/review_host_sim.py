#!/usr/bin/env python3
"""Bounded v3 terminal-D0 HOST/SIM checks; original counterexample retained."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
TOOLS = ROOT / "business-tools-v3"
spec = importlib.util.spec_from_file_location("independent_lost_anchor", OUT / "reproduce_lost_anchor.py")
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)
b, base, put = repro.b, repro.base, repro.put
for name, path in [("test_domain_admission", "test_domain_admission.py"), ("test_terminal_d0", "test_terminal_d0.py")]:
    spec = importlib.util.spec_from_file_location(name, TOOLS / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
terminal = sys.modules["test_terminal_d0"]
DETAILS = {}


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({"test": test.id(), "status": "passed"})
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({"test": test.id(), "status": "failed", "detail": self._exc_info_to_string(err, test)})
    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({"test": test.id(), "status": "error", "detail": self._exc_info_to_string(err, test)})


def run_suite(cls, name):
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    summary = {"kind": "HOST/SIM", "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful(),
               "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False, "tests": result.records}
    put(OUT / (name + ".json"), summary)
    put(OUT / (name + ".log"), stream.getvalue())
    return summary


class IndependentTests(unittest.TestCase):
    def setUp(self):
        self.folder = OUT / "fixtures" / self._testMethodName
        self.f = base.Fixture(self.folder)
        self.patches = [patch.object(b.Study, "execute", side_effect=AssertionError("NO helper forwarding")), patch.object(b.subprocess, "run", side_effect=AssertionError("NO subprocess forwarding")),
                        patch.object(b.subprocess, "Popen", side_effect=AssertionError("NO subprocess forwarding")), patch.object(b, "guard_live", return_value=True)]
        for p in self.patches: p.start()
    def tearDown(self):
        for p in reversed(self.patches): p.stop()
    def start(self, fixture=None):
        fixture = fixture or self.f
        s = fixture.init(); s.admit("T1")
        return s
    def crash(self, request, profile, argv, folder):
        put(Path(folder) / "service/failure.log", "HOST/SIM initial runtime crash, no SDK or native execution\n")
        raise RuntimeError("HOST/SIM runtime crash")
    def blocked(self, request, profile, argv, folder):
        put(Path(folder) / "service/cycle.json", {"status": "review_source_domain", "native_executed": False, "scope": "HOST/SIM blocked before native"})
        put(Path(folder) / "service/blocked.log", "HOST/SIM source-shape precondition blocked\n")
        return 1

    def test_runtime_crash_A_and_blocked_B_repair_D1_final_default_transport(self):
        f, s = self.f, self.start()
        cohort_sha = b.sha(s.root / "INITIAL-COHORT.json")
        records = []
        for alias, receiver in [("A", self.crash), ("B", self.blocked)]:
            ticket = s.enqueue("T1", alias, "diagnostic")
            d0 = s.serve(receiver)
            anchor = s.one("T1", alias, "repair_started")
            self.assertTrue(s.d0_complete("T1", alias))
            self.assertEqual(anchor["d0_request_id"], ticket["request_id"])
            self.assertEqual(anchor["deadline_clock"], d0["finished_at_clock"] + 1200)
            self.assertTrue(all(not row["accepted"] and row["integrity"]["passed"] for row in d0["outcomes"]))
            self.assertTrue(all(row["new_ui_acquisition"] is (None if alias == "A" else False) for row in d0["outcomes"]))
            source = Path(s.arm("T1", alias)["source_roots"][0]) / "Opaque.txt"
            self.assertFalse(source.stat().st_mode & 0o222)
            self.assertIsNone(s.one("T1", alias, "repair_unlocked"))
            s.feedback_ready("T1", alias)
            source.write_text("HOST/SIM source-only repair from failure logs " + alias)
            s.enqueue("T1", alias, "diagnostic")
            d1 = s.serve(f.execute)
            self.assertTrue(all(not row.get("error") for row in d1["outcomes"]))
            self.assertEqual(s.one("T1", alias, "repair_started"), anchor)
            with self.assertRaisesRegex(ValueError, "cap"):
                s.enqueue("T1", alias, "diagnostic")
            s.lock_source("T1", alias)
            s.enqueue("T1", alias, "final")
            final = s.serve(f.execute)
            self.assertTrue(all(row["accepted"] for row in final["outcomes"]))
            for call in [c for c in f.calls if c["arm"] == alias and c["action"] == "final"]:
                self.assertEqual("--previous" in call["argv"], alias == "A")
                self.assertEqual("--history" in call["argv"], alias == "A")
                self.assertNotIn("--fresh", call["argv"])
            claim = put(self.folder / (alias + "-claim.json"), {"statement": "HOST/SIM final self claim"})
            sealed = s.seal_self("T1", alias, claim)
            self.assertTrue(sealed["public_service_accepted"])
            with self.assertRaisesRegex(ValueError, "sealed"):
                s.feedback_ready("T1", alias)
            if alias == "A": self.assertIsNone(s.one("T1", "B", "repair_started"))
            records.append({"arm": alias, "first_ticket": ticket["request_id"], "anchor": anchor, "final_self_seal": sealed})
        self.assertEqual(b.sha(s.root / "INITIAL-COHORT.json"), cohort_sha)
        s.verify_initial_cohort()
        DETAILS["failed_D0_to_patch_D1_final_both_APIs"] = records

    def test_late_ack_failed_D0_freezes_original_source_without_unlock(self):
        s = self.start()
        s.enqueue("T1", "A", "diagnostic"); s.serve(self.crash)
        anchor = s.one("T1", "A", "repair_started")
        before = s.assert_source("T1", "A")
        with patch.object(b.time, "clock_gettime", return_value=anchor["deadline_clock"] + 1), patch.object(b.time, "time", return_value=anchor["deadline_at_unix"] + 1):
            with self.assertRaisesRegex(ValueError, "sealed"):
                s.feedback_ready("T1", "A")
        self.assertIsNone(s.one("T1", "A", "repair_unlocked"))
        self.assertEqual(s.assert_source("T1", "A"), before)
        self.assertEqual(s.one("T1", "A", "source_locked")["reason"], "repair_deadline")
        self.assertEqual(s.one("T1", "A", "repair_started"), anchor)
        self.assertIsNone(s.one("T1", "B", "repair_started"))

    def test_system_exit_negative_return_and_envelope_interrupt_stay_pending(self):
        recorded = []
        for kind in ["system_exit", "negative_return", "envelope_interrupt"]:
            f = base.Fixture(self.folder / kind)
            s = self.start(f)
            ticket = s.enqueue("T1", "A", "diagnostic")
            calls = []
            def interrupted(request, profile, argv, folder):
                calls.append(profile)
                put(Path(folder) / "service/interrupted.log", "HOST/SIM partial interrupted operation")
                if kind == "system_exit": raise SystemExit("HOST/SIM stop")
                if kind == "negative_return": return -9
                put(Path(folder) / ("envelope-" + request["request_id"] + "-" + profile) / "result.json", {"error": {"type": "InterruptedError"}})
                return 1
            with self.assertRaises((SystemExit, InterruptedError)):
                s.serve(interrupted)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(s.history(kind="request_interrupted")), 1)
            self.assertEqual(len(s.pending()), 1)
            self.assertFalse((s.root / "requests" / ticket["request_id"] / "result.json").exists())
            self.assertFalse(s.d0_complete("T1", "A"))
            self.assertIsNone(s.one("T1", "A", "repair_started"))
            with self.assertRaisesRegex(ValueError, "in-flight"):
                s.serve(interrupted)
            with self.assertRaisesRegex(ValueError, "D0 is pending"):
                s.feedback_ready("T1", "A")
            recorded.append({"kind": kind, "request": ticket["request_id"], "interrupted": s.history(kind="request_interrupted")[0]})
        DETAILS["independent_interruption_variants"] = recorded

    def test_explicit_drift_reports_and_remote_initial_capsule_drift_cannot_anchor(self):
        for kind in ["envelope_source_drift", "capture_input_drift", "other_pair_capsule_drift"]:
            f = base.Fixture(self.folder / kind)
            s = self.start(f)
            s.enqueue("T1", "A", "diagnostic")
            tampered = None
            if kind == "other_pair_capsule_drift":
                tampered = s.folder("T5", "B") / "initial/files/0/Opaque.txt"
                original = tampered.read_bytes(); tampered.chmod(0o644); tampered.write_text("HOST/SIM initial cohort capsule drift")
            calls = []
            def observed(request, profile, argv, folder):
                calls.append(profile)
                f.execute(request, profile, argv, folder)
                if kind == "envelope_source_drift":
                    base.put(Path(folder) / ("envelope-" + request["request_id"] + "-" + profile) / "result.json", {"source_unchanged": False})
                elif kind == "capture_input_drift":
                    capture = Path(folder) / "service/capture/result.json"
                    value = b.load(capture); value["inputs_unchanged"] = False; base.put(capture, value)
                    cycle = Path(folder) / "service/cycle.json"; value = b.load(cycle); value["capture_sha256"] = b.sha(capture); base.put(cycle, value)
                return 0
            first = s.serve(observed)
            self.assertTrue(all(not row["integrity"]["passed"] for row in first["outcomes"]))
            self.assertIsNone(s.one("T1", "A", "repair_started"))
            if tampered:
                self.assertEqual(calls, [])
                tampered.write_bytes(original); tampered.chmod(0o444)
            s.enqueue("T1", "A", "diagnostic"); s.serve(f.execute)
            self.assertIsNone(s.one("T1", "A", "repair_started"))
            self.assertFalse(s.d0_complete("T1", "A"))


if __name__ == "__main__":
    frozen = run_suite(terminal.TerminalD0Tests, "frozen-terminal-12-tests")
    independent = run_suite(IndependentTests, "independent-focused-tests")
    put(OUT / "observations.json", DETAILS)
    counterexample = b.load(OUT / "LOST-ANCHOR-COUNTEREXAMPLE.json")
    put(OUT / "RESULT.json", {"kind": "independent-v3-terminal-D0-delta-review", "verdict": "changes_required", "positive_suites": {"frozen_terminal": frozen, "independent": independent},
                              "protocol_counterexample_reproduced": counterexample["protocol_conforming"] is False, "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False})
    print(json.dumps({"frozen_terminal": {k: frozen[k] for k in ["tests_run", "failures", "errors", "passed"]}, "independent": {k: independent[k] for k in ["tests_run", "failures", "errors", "passed"]}, "protocol_counterexample_reproduced": True, "verdict": "changes_required"}))
    raise SystemExit(0 if frozen["passed"] and independent["passed"] else 1)
