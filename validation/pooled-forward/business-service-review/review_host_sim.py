#!/usr/bin/env python3
"""Independent, bounded HOST/SIM review of the original frozen helper.

No native/service forwarding. Every synthetic fixture is a five-pair study.
The original suite is executed in memory with only its ARTIFACTS destination
redirected here; its source and original outcomes remain unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import types
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
HELPER = ROOT / "business-tools/blind_study.py"
EXPECTED = "f9495569e2ae23a6511f47918d5ae79617243ed6efbd1bd0860ce6a22d626d8a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n")
    return str(path)


def replace(path, value):
    path = Path(path)
    path.chmod(0o644)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n")


assert sha(HELPER) == EXPECTED
suite_source = ROOT / "business-tools/test_blind_study.py"
suite_text = suite_source.read_text()
old = 'ARTIFACTS = HERE / "HOST-SIM"'
assert suite_text.count(old) == 1
original = types.ModuleType("independently_redirected_original_tests")
original.__file__ = str(suite_source)
exec(compile(suite_text.replace(old, 'ARTIFACTS = Path(' + repr(str(OUT / "original-suite-scratch")) + ')'),
             str(suite_source), "exec"), original.__dict__)
b = original.b


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


def run_suite(cls, basename):
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResult).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    put(OUT / (basename + ".log"), stream.getvalue())
    summary = {"kind": "HOST/SIM", "native_execution": False, "sdk_forwarding": False,
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "passed": result.wasSuccessful(), "tests": result.records}
    put(OUT / (basename + ".json"), summary)
    return summary


DETAILS = {}


class IndependentTests(unittest.TestCase):
    def setUp(self):
        self.folder = OUT / "fixtures" / self._testMethodName
        self.f = original.Fixture(self.folder)
        self.patches = [patch.object(b.Study, "execute", side_effect=AssertionError("Independent review forbids helper.execute forwarding")),
                        patch.object(b.subprocess, "run", side_effect=AssertionError("Independent review forbids subprocess.run")),
                        patch.object(b.subprocess, "Popen", side_effect=AssertionError("Independent review forbids subprocess.Popen")),
                        patch.object(b, "guard_live", return_value=True)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def start(self):
        s = self.f.init()
        s.admit("T1")
        return s

    def ready(self, alias="A"):
        self.f.d0(alias=alias)
        self.f.study.feedback_ready("T1", alias)

    def final(self, receiver=None):
        s = self.f.study
        s.lock_source("T1", "A")
        s.enqueue("T1", "A", "final")
        return s.serve(receiver or self.f.execute)

    def claim(self):
        return put(self.folder / "claim.json", {"statement": "HOST/SIM self claim; no business quality conclusion"})

    def test_initial_cohort_and_readonly_sources_before_any_d0(self):
        s = self.start()
        cohort = b.load(s.root / "INITIAL-COHORT.json")
        self.assertEqual(sum(len(v) for v in cohort.values()), 10)
        self.assertEqual(len(s.history(kind="request_enqueued")), 0)
        self.assertEqual(self.f.calls, [])
        for alias in ("A", "B"):
            for path, mode in b.modes(s.arm("T1", alias)["source_roots"]).items():
                self.assertFalse(mode & 0o222, path)
        changed = Path(s.arm("T1", "B")["source_roots"][0]) / "Opaque.txt"
        changed.chmod(0o644)
        changed.write_text("HOST/SIM forbidden initial drift")
        with self.assertRaisesRegex(ValueError, "initial/final"):
            s.enqueue("T1", "B", "diagnostic")

    def test_d0_clock_starts_at_readiness_and_review_and_queue_wait_are_charged(self):
        s = self.start()
        first = s.enqueue("T1", "A", "diagnostic")
        with patch.object(b.time, "clock_gettime", return_value=first["at_clock"] + 12), patch.object(b.time, "time", return_value=first["at_unix"] + 12):
            result = s.serve(self.f.execute)
        anchor = s.one("T1", "A", "repair_started")
        self.assertEqual(anchor["at_clock"], result["finished_at_clock"])
        self.assertEqual(anchor["deadline_clock"] - anchor["at_clock"], 1200)
        self.assertEqual(result["queue_wait_seconds"], 12)
        self.assertIsNone(s.one("T1", "B", "repair_started"))
        with patch.object(b.time, "clock_gettime", return_value=anchor["at_clock"] + 81), patch.object(b.time, "time", return_value=anchor["at_unix"] + 81):
            ack = s.feedback_ready("T1", "A")
        self.assertEqual(ack["deadline_clock"], anchor["deadline_clock"])
        self.assertEqual(ack["deadline_clock"] - ack["at_clock"], 1119)
        observation = put(self.folder / "observations.json", {"scope": "HOST/SIM explicit image observations"})
        s.enqueue("T1", "A", "review-native", "ios", observation)
        s.serve(self.f.execute)
        self.assertEqual(s.one("T1", "A", "repair_started"), anchor)
        self.assertEqual(len([e for e in s.history("T1", "A", "request_enqueued") if e["action"] == "diagnostic"]), 1)

    def test_guard_expiry_iteration_freezes_and_late_ack_cannot_unlock(self):
        s = self.start()
        self.f.d0()
        anchor = s.one("T1", "A", "repair_started")
        with patch.object(b.time, "clock_gettime", return_value=anchor["deadline_clock"] + .25), patch.object(b.time, "time", return_value=anchor["deadline_at_unix"] + .25), patch.object(b.time, "sleep", side_effect=RuntimeError("HOST/SIM stop after one watch iteration")):
            with self.assertRaisesRegex(RuntimeError, "one watch"):
                b.watch(s.root)
            with self.assertRaisesRegex(ValueError, "sealed"):
                s.feedback_ready("T1", "A")
        sealed = s.one("T1", "A", "source_locked")
        self.assertEqual(sealed["reason"], "repair_deadline")
        self.assertAlmostEqual(sealed["deadline_enforcement_lateness_seconds"], .25)
        self.assertIsNone(s.one("T1", "A", "repair_unlocked"))
        self.assertTrue((s.root / "guard-heartbeat.json").is_file())

    def test_two_failed_diagnostics_stay_charged_and_partial_evidence_retained(self):
        s = self.start()
        def fail(request, profile, argv, record):
            original.put(Path(record) / "service/partial.json", {"scope": "HOST/SIM failure packet"})
            raise ValueError("HOST/SIM collection failed")
        ids = []
        for _ in range(2):
            ids.append(s.enqueue("T1", "A", "diagnostic")["request_id"])
            result = s.serve(fail)
            self.assertTrue(all(o.get("error") for o in result["outcomes"]))
            self.assertTrue(all(Path(o["inventory"]["path"]).is_file() for o in result["outcomes"]))
        with self.assertRaisesRegex(ValueError, "cap"):
            s.enqueue("T1", "A", "diagnostic")
        self.assertEqual([e["request_id"] for e in s.history("T1", "A", "request_finished")], ids)
        self.assertIsNone(s.one("T1", "A", "repair_started"))
        self.assertEqual(s.serve(fail)["status"], "queue_empty")

    def test_started_unfinished_ticket_blocks_fifo_without_retry(self):
        s = self.start()
        first = s.enqueue("T1", "A", "diagnostic")
        second = s.enqueue("T1", "B", "diagnostic")
        s.append("request_started", task="T1", arm="A", request_id=first["request_id"], scope="HOST/SIM interrupted ticket")
        with self.assertRaisesRegex(ValueError, "Interrupted/in-flight"):
            s.serve(self.f.execute)
        self.assertEqual([e["request_id"] for e in s.pending()], [first["request_id"], second["request_id"]])
        self.assertEqual(self.f.calls, [])

    def test_public_config_and_declared_inputs_and_frozen_tools_detect_drift(self):
        arm = self.f.manifest["tasks"][0]["arms"]["A"]
        cpath = arm["public_configs"]["ios"]
        c = b.load(cpath)
        for key in ["plan", "design_lock", "routes", "fixtures", "bridge", "policy", "environment"]:
            p = original.put(self.folder / "public" / (key + ".json"), {"scope": "HOST/SIM immutable " + key})
            arm["public_readset"].append(p)
            c[key] = p
        original.put(cpath, c)
        s = self.start()
        tested = []
        tool = self.f.manifest["tools"][arm["tool"]]
        paths = [cpath, *arm["public_readset"], str(Path(tool["skill_root"]) / "scripts/ui_loop.py"),
                 self.f.manifest["envelope"]["path"], self.f.manifest["envelope"]["meter_path"],
                 self.f.manifest["envelope"]["meter_spec_path"], self.f.manifest["protocol"]["path"],
                 self.f.manifest["speed_gate"]["path"], self.f.manifest["design_approval"]["path"]]
        for raw in paths:
            path = Path(raw)
            before = path.read_bytes()
            path.chmod(0o644)
            path.write_bytes(before + b"\nHOST_SIM_DRIFT")
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                s.enqueue("T1", "A", "diagnostic")
            path.write_bytes(before)
            tested.append(raw)
        s.verify_pins("T1", "A")
        self.assertEqual(self.f.calls, [])
        DETAILS["immutability_inputs_exercised"] = tested

    def test_final_original_and_self_claim_tampering_blocks_progress(self):
        s = self.start()
        self.ready()
        self.final()
        claim = self.claim()
        source = Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt"
        before = source.read_bytes()
        source.chmod(0o644)
        source.write_bytes(before + b"drift")
        with self.assertRaisesRegex(ValueError, "initial/final"):
            s.seal_self("T1", "A", claim)
        source.write_bytes(before)
        source.chmod(0o444)
        original_file = Path(s.outcomes("T1", "A", "ios")[0]["capture"]["path"]).parent / "native.log"
        old_bytes = original_file.read_bytes()
        original_file.chmod(0o644)
        original_file.write_bytes(old_bytes + b"drift")
        with self.assertRaisesRegex(ValueError, "original service packet"):
            s.seal_self("T1", "A", claim)
        original_file.write_bytes(old_bytes)
        original_file.chmod(0o444)
        seal = s.seal_self("T1", "A", claim)
        with self.assertRaisesRegex(ValueError, "irrevocably"):
            s.seal_self("T1", "A", claim)
        replace(seal["claim_path"], {"statement": "HOST/SIM altered self claim"})
        with self.assertRaisesRegex(ValueError, "self-claim/seal"):
            s.cohort()
        self.assertEqual(s.history(kind="hidden_authorized"), [])

    def test_final_status_and_retirement_are_both_required(self):
        s = self.start()
        self.ready()
        def unresolved(request, profile, argv, record):
            self.f.execute(request, profile, argv, record)
            p = Path(record) / "service/cycle.json"
            v = b.load(p)
            v["status"] = "review_images"
            original.put(p, v)
            original.put(Path(record) / "service/resources.json", {"cleanup_errors": [], "remaining_devices": ["HOST_SIM_not_retired"], "remaining_directories": []})
            return 0
        self.final(unresolved)
        claim = self.claim()
        with self.assertRaisesRegex(ValueError, "retirement proof"):
            s.seal_self("T1", "A", claim)
        s.enqueue("T1", "A", "retire")
        s.serve(self.f.execute)
        seal = s.seal_self("T1", "A", claim)
        self.assertFalse(seal["public_service_accepted"])
        self.assertTrue(all(o["service_status"] == "review_images" for o in seal["final_outcomes"].values()))
        self.assertEqual(len(s.history("T1", "A", "request_finished")), 3)

    def test_full_five_pair_barrier_hidden_open_order_and_unique_record_basenames(self):
        s = self.f.init()
        hidden = {Path(p) for t in self.f.manifest["tasks"] for a in t["arms"].values() for p in a["hidden_configs"].values()}
        opened = []
        original_open = Path.open
        def observed_open(path, *args, **kwargs):
            mode = args[0] if args else kwargs.get("mode", "r")
            if path in hidden and "r" in mode:
                self.assertEqual(len(s.history(kind="self_sealed")), 10)
                self.assertEqual(len(s.history(kind="hidden_authorized")), 1)
                opened.append(str(path))
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", observed_open):
            for n in range(1, 6):
                if n > 1:
                    self.assertEqual(len(s.history(kind="self_sealed")), 2 * (n - 1))
                with self.assertRaisesRegex(ValueError, "All ten"):
                    s.authorize_hidden()
                self.assertEqual(opened, [])
                self.f.finish_task("T" + str(n))
            s.seal_cohort()
            self.f.create_hidden()
            s.authorize_hidden()
        self.assertEqual(len(set(opened)), 20)
        outcomes = [o for t in self.f.manifest["tasks"] for a in t["arms"] for p in t["arms"][a]["public_configs"] for o in s.outcomes(t["id"], a, p)]
        names = [Path(o["envelope_record"]).name for o in outcomes]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 40)
        for call in self.f.calls:
            if call["action"] == "final" and call["arm"] == "A":
                for flag in ["--previous", "--previous-sha256", "--history"]:
                    self.assertIn(flag, call["argv"])
            if call["arm"] == "B":
                for flag in ["--previous", "--history", "--fresh"]:
                    self.assertNotIn(flag, call["argv"])
        DETAILS["all_five_pair_integration"] = {"envelope_record_basenames": names, "hidden_configs_opened_after_authorization": sorted(set(opened)), "self_seals": 10}

    def test_source_domain_revision_transport_blocker_is_reproduced_without_waiver(self):
        domain_path = ROOT / "candidate-v13.9/scripts/coverage_domain.py"
        d = types.ModuleType("design_contract")
        d.canonical = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
        d.digest = lambda value: hashlib.sha256(d.canonical(value)).hexdigest()
        d.load = lambda path: json.loads(path.read_text())
        spec = importlib.util.spec_from_file_location("independent_synthetic_coverage_domain", domain_path)
        domain = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"design_contract": d}):
            spec.loader.exec_module(domain)
        # Only module location is redirected to a wholly synthetic provider tree.
        # The exact frozen prepare(), pinned(), policy() source is unchanged.
        synthetic_tool = self.folder / "synthetic-provider"
        domain.__file__ = str(synthetic_tool / "scripts/coverage_domain.py")
        host = {rel: put(synthetic_tool / rel, "HOST/SIM provider identity fixture\n") for rel in ["assets/ios-observer/ObserverApp.swift", "assets/ios-observer/ObserverTests.swift"]}
        arm = self.f.manifest["tasks"][0]["arms"]["A"]
        component = Path(arm["source_roots"][0]) / "Opaque.txt"
        bridge = put(self.folder / "public/bridge.json", {"scope": "HOST/SIM unchanged bridge"})
        fixtures = put(self.folder / "public/fixtures.json", {"scope": "HOST/SIM unchanged fixtures"})
        lock = {"scope": "HOST/SIM independent unchanged expectations"}
        plan = {"design_contract": {"platform": "ios"}, "assertions": ["SIM"], "states": [{"id": "SIM", "coverage": "full_content"}]}
        approval = {"version": 1, "binds": {"design_lock_sha256": d.digest(lock), "required_native_assertions": 1, "selected_state_ids": ["SIM"], "full_content_state_ids": ["SIM"], "environment_ios_canonical_sha256": "SIM-environment"},
                    "common_host_shape": {"scope": "HOST/SIM unchanged shape"}, "geometry_encoding": {"scope": "HOST/SIM encoding identity only"},
                    "actual_subject_binding": {"component_subject": "component", "bridge_subject": "bridge"},
                    "approved_inputs": {"SIM": {"platform": "ios", "fixture_canonical_sha256": d.digest(b.load(fixtures)), "fixture_file_sha256": sha(fixtures), "launch_bridge_sha256": sha(bridge)}},
                    "platforms": {"ios": {"exact_bridge": {"sha256": sha(bridge)}, "component_install_path": "Sources/Opaque.txt", "product": "SIM", "approved_component_revisions": {"initial": {"sha256": sha(component), "bytes": component.stat().st_size}}}}}
        approval["common_host_shape_sha256"] = d.digest(approval["common_host_shape"])
        approval["geometry_encoding_sha256"] = d.digest(approval["geometry_encoding"])
        # Encoding is synthetic; its fixed identity is a fixture parameter, not a source approval bypass.
        domain.SUPPORTED_ENCODING_SHA256 = approval["geometry_encoding_sha256"]
        provider = {"version": 1, "status": "conforming", "common_host_shape_sha256": approval["common_host_shape_sha256"], "files": {rel: sha(path) for rel, path in host.items()}}
        approval_path = put(self.folder / "public/approval-v1.json", approval)
        provider_path = put(self.folder / "public/provider.json", provider)
        cpath = arm["public_configs"]["ios"]
        config = b.load(cpath)
        config.update(design_sha256=d.digest(lock), environment_sha256="SIM-environment", fixtures=fixtures, bridge=bridge,
                      coverage_domain_ref={"path": approval_path, "sha256": d.digest(approval)}, coverage_provider_ref={"path": provider_path, "sha256": d.digest(provider)},
                      evidence_subjects={"component": [str(component)], "bridge": [bridge]})
        config["native_options"].update(package=arm["workspace"], product="SIM")
        original.put(cpath, config)
        arm["public_readset"] += [bridge, fixtures, approval_path, provider_path]
        s = self.start()
        initial = domain.prepare(config, plan, lock)
        self.assertEqual(initial["revision"], "initial")
        self.ready()
        component.write_text("HOST/SIM repaired component; unchanged finite scope\n")
        with self.assertRaises(domain.DomainReviewRequired) as missing:
            domain.prepare(config, plan, lock)
        approval2 = copy.deepcopy(approval)
        approval2["platforms"]["ios"]["approved_component_revisions"]["separately-reviewed"] = {"sha256": sha(component), "bytes": component.stat().st_size}
        self.assertEqual(d.digest(domain.policy(approval2)), initial["policy_sha256"])
        approval2_path = put(self.folder / "public/approval-v2.json", approval2)
        next_config = copy.deepcopy(config)
        next_config["coverage_domain_ref"] = {"path": approval2_path, "sha256": d.digest(approval2)}
        admitted = domain.prepare(next_config, plan, lock)
        self.assertEqual(admitted["revision"], "separately-reviewed")
        # The helper has no active version channel: unchanged original config is what it transports.
        ticket = s.enqueue("T1", "A", "diagnostic")
        record = self.folder / "command-preview"
        record.mkdir()
        argv, _, _ = s.build_command(ticket, "ios", record)
        self.assertEqual(argv[argv.index("--config") + 1], cpath)
        with self.assertRaises(domain.DomainReviewRequired):
            domain.prepare(b.load(cpath), plan, lock)
        original.put(cpath, next_config)
        with self.assertRaisesRegex(ValueError, "public input/config changed") as frozen:
            s.verify_pins("T1", "A")
        original.put(cpath, config)
        # A separate approval alone leaves original config/readset unchanged and cannot select v2.
        s.verify_pins("T1", "A")
        self.assertEqual(sha(approval_path), sha(approval_path))
        DETAILS["source_domain_transport_blocker"] = {"status": "reproduced", "source_gate_rejection": str(missing.exception), "controller_rejection_when_reference_updated": str(frozen.exception),
            "initial_policy_sha256": initial["policy_sha256"], "approved_repaired_policy_sha256": admitted["policy_sha256"],
            "original_config_path": cpath, "original_config_sha256": sha(cpath), "original_approval_path": approval_path, "new_separately_sealed_approval_path": approval2_path,
            "generated_transport": argv, "repair_source_sha256": sha(component), "revision_bytes": component.stat().st_size,
            "scope": "Synthetic source-shape only. No business design, behavior verdict, native execution, or source-gate waiver. Source and config policy gates executed from original frozen public functions."}


def main():
    original_summary = run_suite(original.ControllerTests, "original-15-tests")
    independent_summary = run_suite(IndependentTests, "independent-edge-tests")
    put(OUT / "observations.json", DETAILS)
    result = {"kind": "independent-HOST/SIM-controller-forward-review", "candidate_helper_sha256": EXPECTED,
              "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False,
              "original_suite": original_summary, "independent_suite": independent_summary,
              "source_domain_transport_blocker_reproduced": DETAILS.get("source_domain_transport_blocker", {}).get("status") == "reproduced",
              "study_admission": "blocked_pending_new_helper_candidate", "business_quality_or_performance_claim": False}
    put(OUT / "RESULT.json", result)
    print(json.dumps({"original": {k: original_summary[k] for k in ["tests_run", "failures", "errors", "passed"]}, "independent": {k: independent_summary[k] for k in ["tests_run", "failures", "errors", "passed"]}, "study_admission": result["study_admission"]}))
    return 0 if original_summary["passed"] and independent_summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
