#!/usr/bin/env python3
"""HOST/SIM controller tests. Synthetic receipts; no SDK/native forwarding."""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("blind_study", HERE / "blind_study.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
ARTIFACTS = HERE / "HOST-SIM"
ARTIFACTS.mkdir(exist_ok=True)


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n" if not isinstance(value, str) else value)
    return str(path)


class Fixture:
    """Entirely synthetic public ABI fixtures, never real native evidence."""
    def __init__(self, folder):
        self.folder = Path(folder)
        root = self.folder / "SIM-root"
        protocol = put(root / "PROTOCOL.json", {"business": {"tasks": 5, "repair_budget_minutes": 20, "diagnostic_requests_max": 2}})
        speed = put(root / "qualification/benchmark-gate/RESULT.json", {"passed": True, "business_tasks_may_start": True, "scope": "HOST/SIM, no performance claim"})
        approval = put(root / "design-approval.json", {"independent_approval": "HOST/SIM opaque fixture, no case design"})
        envelope = put(root / "native_envelope.py", "# HOST/SIM: must never execute\n")
        meter = put(root / "measure.py", "# HOST/SIM: must never execute\n")
        tools = {}
        for alias, api in [("old", "baseline-explicit-prior"), ("new", "stateful-default")]:
            skill = root / alias
            paths = [put(skill / "SKILL.md", "HOST/SIM public interface fixture\n"),
                     put(skill / "scripts/ui_loop.py", "raise AssertionError('HOST/SIM must never forward')\n")]
            tools[alias] = {"skill_root": str(skill), "api": api,
                            "files": {str(Path(p).relative_to(skill)): b.sha(p) for p in paths}}
        tasks = []
        journals = []
        for n in range(1, 6):
            task = {"id": "T" + str(n), "arms": {}}
            for alias, tool in [("A", "old"), ("B", "new")]:
                folder = root / "business" / task["id"] / alias
                workspace = folder / "workspace"
                src = workspace / "Sources"
                put(src / "Opaque.txt", "HOST/SIM identical initial source\n")
                resources = [str(folder / "resources" / p) for p in ["ios", "android"]]
                journals.append(str(Path(resources[0]) / "journal.json"))  # frozen meter lists managed iOS only
                public = {}
                for i, profile in enumerate(["ios", "android"]):
                    config = {"source_roots": [str(src)], "resources": {"root": resources[i], "max_simulators": 1},
                              "review_store": str(folder / "public-images" / profile), "source_review_store": str(folder / "public-source" / profile),
                              "native_options": {"simulator": "managed"} if profile == "ios" else {}}
                    if tool == "new":
                        config["workflow"] = {"root": str(folder / "public-workflow")}
                    public[profile] = put(folder / "profiles" / (profile + ".json"), config)
                task["arms"][alias] = {"tool": tool, "workspace": str(workspace), "source_roots": [str(src)],
                                      "resource_roots": resources, "public_configs": public, "public_readset": [],
                                      "hidden_configs": {p: str(folder / "hidden" / (p + ".json")) for p in public}}
            tasks.append(task)
        meterspec = put(root / "operators/whole-study-meter-spec-v2.json", {"sample_seconds": .1, "filesystem_root": str(root),
                         "max_total_allocated_bytes": 32 * 2**30, "min_free_bytes": 5 * 2**30,
                         "groups": {"synthetic": {"paths": [str(root)], "resource_journals": journals}}})
        self.manifest = {"version": 1, "study_id": "HOST_SIM", "run_root": str(root / "run"),
                         "protocol": {"path": protocol, "sha256": b.sha(protocol)},
                         "speed_gate": {"path": speed, "sha256": b.sha(speed)},
                         "design_approval": {"path": approval, "sha256": b.sha(approval)},
                         "envelope": {"path": envelope, "sha256": b.sha(envelope), "meter_path": meter, "meter_sha256": b.sha(meter),
                                      "meter_spec_path": meterspec, "meter_spec_sha256": b.sha(meterspec)}, "tools": tools, "tasks": tasks}
        self.path = put(root / "manifest-input.json", self.manifest)
        self.calls = []

    def init(self):
        put(self.path, self.manifest)
        b.initialize(self.path)
        self.study = b.Study(self.manifest["run_root"])
        return self.study

    def execute(self, request, profile, argv, record):
        """Synthetic transport receiver; creates only labeled SIM JSON artifacts."""
        self.calls.append({"task": request["task"], "arm": request["arm"], "profile": profile, "action": request["action"], "argv": argv})
        output = Path(argv[argv.index("--output") + 1])
        action = request["action"]
        marker = {"scope": "HOST/SIM synthetic receipt, NO native execution"}
        if action in {"diagnostic", "final"}:
            output.mkdir(parents=True)
            previous = self.study.outcomes(request["task"], request["arm"], profile)
            prior = next((o["capture"] for o in reversed(previous) if o.get("capture")), None)
            reused = action == "final" and request["arm"] == "B" and prior is not None
            if reused:
                capture = prior
            else:
                c = output / "capture"
                execution = {**marker, "execution_sha256": "SIM-not-native-identity"}
                put(c / "execution.json", execution)
                put(c / "native/observation.json", marker)
                put(c / "native.log", "HOST/SIM synthetic log: NO SDK or native execution\n")
                p = put(c / "result.json", {**marker, "execution_sha256": execution["execution_sha256"], "native_exit_code": 0})
                capture = {"path": p, "sha256": b.sha(p)}
            put(output / "cycle.json", {**marker, "final": action == "final", "status": "accepted" if action == "final" else "feedback_complete",
                                        "native_executed": not reused, "capture_reused": reused, "capture_result": capture["path"], "capture_sha256": capture["sha256"]})
            put(output / "resources.json", {**marker, "cleanup_errors": [], "remaining_devices": [], "remaining_directories": []})
        elif action == "review-native":
            put(output / "review-result.json", marker)
        elif action == "review-source":
            put(output, marker)
        elif action == "finish-review":
            put(output / "completion.json", {**marker, "status": "accepted", "native_executed": False})
        elif action == "retire":
            put(output / "resources.json", {**marker, "cleanup_errors": [], "remaining_devices": [], "remaining_directories": []})
        return 0

    def d0(self, task="T1", alias="A"):
        self.study.enqueue(task, alias, "diagnostic")
        self.study.serve(self.execute)

    def finish_task(self, task):
        s = self.study
        s.admit(task)
        for alias in ["A", "B"]:
            self.d0(task, alias)
            s.feedback_ready(task, alias)
            s.lock_source(task, alias)
            s.enqueue(task, alias, "final")
            s.serve(self.execute)
            claim = put(self.folder / (task + alias + "-claim.json"), {"statement": "HOST/SIM final self-observation, no quality claim"})
            s.seal_self(task, alias, claim)

    def create_hidden(self):
        for task in self.manifest["tasks"]:
            for alias, arm in task["arms"].items():
                folder = Path(arm["workspace"]).parent
                for profile, path in arm["hidden_configs"].items():
                    c = b.load(arm["public_configs"][profile])
                    c["review_store"] = str(folder / "hidden-images" / profile)
                    c["source_review_store"] = str(folder / "hidden-source" / profile)
                    if "workflow" in c:
                        c["workflow"] = {"root": str(folder / "hidden-workflow")}
                    put(path, c)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.mkdtemp(prefix="host-sim-", dir=ARTIFACTS)
        self.fixture = Fixture(self.temp)
        self.no_forward = patch.object(b.Study, "execute", side_effect=AssertionError("NO SDK forwarding permitted in HOST/SIM"))
        self.no_run = patch.object(b.subprocess, "run", side_effect=AssertionError("NO process forwarding permitted in HOST/SIM"))
        self.no_popen = patch.object(b.subprocess, "Popen", side_effect=AssertionError("NO process forwarding permitted in HOST/SIM"))
        self.guard = patch.object(b, "guard_live", return_value=True)  # simulate the separate host-only deadline process
        for p in [self.no_forward, self.no_run, self.no_popen, self.guard]: p.start()

    def tearDown(self):
        for p in [self.guard, self.no_popen, self.no_run, self.no_forward]: p.stop()
        for base, dirs, files in os.walk(self.temp):
            Path(base).chmod(0o755)
            for file in files: (Path(base) / file).chmod(0o644)
        shutil.rmtree(self.temp)

    def test_initial_identity_and_all_five_pre_native_barrier(self):
        f = self.fixture
        p = Path(f.manifest["tasks"][4]["arms"]["B"]["source_roots"][0]) / "Opaque.txt"
        p.write_text("different fifth initial")
        with self.assertRaisesRegex(ValueError, "exactly identical"):
            f.init()
        self.assertFalse(Path(f.manifest["run_root"]).exists())
        p.write_text("HOST/SIM identical initial source\n")
        s = f.init()
        s.admit("T1")
        missing = s.folder("T5", "B") / "initial/source.json"
        missing.unlink()
        with self.assertRaises(OSError): s.enqueue("T1", "A", "diagnostic")
        self.assertEqual(f.calls, [])

    def test_speed_and_design_prerequisites(self):
        f = self.fixture
        gate = f.manifest["speed_gate"]
        put(gate["path"], {"passed": True, "business_tasks_may_start": False})
        gate["sha256"] = b.sha(gate["path"])
        with self.assertRaisesRegex(ValueError, "must authorize"):
            f.init()
        put(gate["path"], {"passed": True, "business_tasks_may_start": True})
        gate["sha256"] = b.sha(gate["path"])
        f.manifest["design_approval"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "approval"):
            f.init()

    def test_android_allocation_coverage_does_not_require_simulator_journal(self):
        f = self.fixture
        spec_path = f.manifest["envelope"]["meter_spec_path"]
        meter = b.load(spec_path)
        arm = f.manifest["tasks"][0]["arms"]["A"]
        self.assertIn(str(Path(arm["resource_roots"][0]) / "journal.json"), meter["groups"]["synthetic"]["resource_journals"])
        self.assertNotIn(str(Path(arm["resource_roots"][1]) / "journal.json"), meter["groups"]["synthetic"]["resource_journals"])
        s = f.init()
        self.assertEqual(s.manifest["study_id"], "HOST_SIM")
        # The equivalent omission for managed iOS must still fail before any run.
        other = Fixture(Path(self.temp) / "missing-ios-journal")
        p = other.manifest["envelope"]["meter_spec_path"]
        value = b.load(p); value["groups"]["synthetic"]["resource_journals"].pop(0); put(p, value)
        other.manifest["envelope"]["meter_spec_sha256"] = b.sha(p)
        with self.assertRaisesRegex(ValueError, "managed-iOS journal"):
            other.init()

    def test_initial_patch_is_rejected_and_repair_clock_starts_after_feedback(self):
        f = self.fixture; s = f.init(); s.admit("T1")
        self.assertIsNone(s.one("T1", "A", "repair_started"))
        root = Path(s.arm("T1", "A")["source_roots"][0]); file = root / "Opaque.txt"
        file.chmod(0o644); file.write_text("premature edit")
        with self.assertRaisesRegex(ValueError, "initial/final"):
            s.enqueue("T1", "A", "diagnostic")
        file.write_text("HOST/SIM identical initial source\n")
        f.d0(); automatic = s.one("T1", "A", "repair_started")
        self.assertIsNotNone(automatic)
        with patch.object(b.time, "clock_gettime", return_value=automatic["at_clock"] + 30), patch.object(b.time, "time", return_value=automatic["at_unix"] + 30):
            ready = s.feedback_ready("T1", "A")
        self.assertEqual(ready["deadline_clock"], automatic["deadline_clock"])
        self.assertAlmostEqual(ready["deadline_clock"] - ready["at_clock"], 1170, delta=.1)
        self.assertTrue(file.stat().st_mode & 0o200)

    def test_queued_d0_rechecks_entire_initial_cohort_before_forwarding(self):
        f = self.fixture; s = f.init(); s.admit("T1")
        s.enqueue("T1", "A", "diagnostic")
        (s.folder("T5", "B") / "initial/source.json").unlink()
        result = s.serve(f.execute)
        self.assertEqual(f.calls, [])
        self.assertTrue(all(o.get("error") for o in result["outcomes"]))

    def test_guard_required_and_late_ack_does_not_extend_window(self):
        f = self.fixture; s = f.init(); s.admit("T1"); f.d0()
        anchor = s.one("T1", "A", "repair_started")
        with patch.object(b, "guard_live", return_value=False):
            with self.assertRaisesRegex(ValueError, "live deadline guard"):
                s.feedback_ready("T1", "A")
        with patch.object(b.time, "clock_gettime", return_value=anchor["deadline_clock"] + .01), patch.object(b.time, "time", return_value=anchor["deadline_at_unix"] + .01):
            with self.assertRaisesRegex(ValueError, "sealed"):
                s.feedback_ready("T1", "A")
        self.assertIsNotNone(s.one("T1", "A", "source_locked"))
        self.assertIsNone(s.one("T1", "A", "repair_unlocked"))

    def test_after_deadline_bytes_never_get_public_accepted_credit(self):
        f = self.fixture; s = f.init(); s.admit("T1"); f.d0(); s.feedback_ready("T1", "A")
        anchor = s.one("T1", "A", "repair_started")
        p = Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt"
        p.write_text("HOST/SIM deliberately late source")
        os.utime(p, (anchor["deadline_at_unix"] + .01, anchor["deadline_at_unix"] + .01))
        with patch.object(b.time, "clock_gettime", return_value=anchor["deadline_clock"] + .02), patch.object(b.time, "time", return_value=anchor["deadline_at_unix"] + .02):
            with b.lock(s.root / "state.lock"): s.expire()
        self.assertFalse(s.one("T1", "A", "source_locked")["source_deadline_compliant"])
        s.enqueue("T1", "A", "final"); s.serve(f.execute)
        claim = put(Path(self.temp) / "claim.json", {"statement": "HOST/SIM late source must stay a failure"})
        self.assertFalse(s.seal_self("T1", "A", claim)["public_service_accepted"])

    def test_two_diagnostic_bundles_deadline_and_irrevocable_early_seal(self):
        f = self.fixture; s = f.init(); s.admit("T1"); f.d0(); ready = s.feedback_ready("T1", "A")
        s.enqueue("T1", "A", "diagnostic"); s.serve(f.execute)
        self.assertEqual(len([c for c in f.calls if c["action"] == "diagnostic"]), 4)
        with self.assertRaisesRegex(ValueError, "cap"):
            s.enqueue("T1", "A", "diagnostic")
        with patch.object(b.time, "clock_gettime", return_value=ready["deadline_clock"] + .01), patch.object(b.time, "time", return_value=ready["deadline_at_unix"] + .01):
            with b.lock(s.root / "state.lock"): s.expire()
        self.assertEqual(s.one("T1", "A", "source_locked")["reason"], "repair_deadline")
        with self.assertRaisesRegex(ValueError, "already"):
            s.feedback_ready("T1", "A")
        self.assertFalse((Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt").stat().st_mode & 0o222)
        f.d0(alias="B"); s.feedback_ready("T1", "B")
        first = s.lock_source("T1", "B")
        self.assertEqual(first, s.lock_source("T1", "B"))
        with self.assertRaisesRegex(ValueError, "sealed"):
            s.enqueue("T1", "B", "diagnostic")

    def test_control_explicit_prior_treatment_default_and_final_reuse(self):
        f = self.fixture; s = f.init(); s.admit("T1")
        for alias in ["A", "B"]:
            f.d0(alias=alias); s.feedback_ready("T1", alias)
            s.enqueue("T1", alias, "diagnostic"); s.serve(f.execute)
            s.lock_source("T1", alias); s.enqueue("T1", alias, "final"); s.serve(f.execute)
        old = [c["argv"] for c in f.calls if c["arm"] == "A"]
        self.assertNotIn("--previous", old[0])
        self.assertIn("--previous", old[2]); self.assertIn("--previous-sha256", old[2]); self.assertIn("--history", old[2])
        for c in [c for c in f.calls if c["arm"] == "B"]:
            self.assertNotIn("--previous", c["argv"]); self.assertNotIn("--history", c["argv"])
            self.assertNotIn("--fresh", c["argv"])
        candidate_final = s.outcomes("T1", "B", "ios", "final")[-1]
        self.assertTrue(candidate_final["capture_reused"])
        self.assertFalse(candidate_final["new_ui_acquisition"])

    def test_failures_retained_fifo_and_exclusive_execution(self):
        f = self.fixture; s = f.init(); s.admit("T1")
        ids = [s.enqueue("T1", alias, "diagnostic")["request_id"] for alias in ["A", "B"]]
        active = 0; peak = 0; mutex = threading.Lock()
        def receiver(request, profile, argv, record):
            nonlocal active, peak
            with mutex: active += 1; peak = max(peak, active)
            try:
                time.sleep(.01)
                if request["arm"] == "A" and profile == "ios":
                    put(Path(record) / "service/partial-failure.json", {"scope": "HOST/SIM retained failure"})
                    raise RuntimeError("HOST/SIM explicit failure")
                return f.execute(request, profile, argv, record)
            finally:
                with mutex: active -= 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = [v.result() for v in [pool.submit(s.serve, receiver), pool.submit(s.serve, receiver)]]
        self.assertEqual(peak, 1)
        finished = s.history(kind="request_finished")
        self.assertEqual([e["request_id"] for e in finished], ids)
        failure = next(o for o in b.load(finished[0]["result_path"])["outcomes"] if o["profile"] == "ios")
        self.assertIn("explicit failure", failure["error"]["message"])
        self.assertTrue(Path(failure["inventory"]["path"]).is_file())
        self.assertIsNone(failure["new_ui_acquisition"])
        self.assertFalse(failure["accepted"])
        self.assertEqual(s.serve(receiver)["status"], "queue_empty")
        self.assertEqual(len(results), 2)

    def test_changed_queued_source_consumes_request_and_is_not_retried(self):
        f = self.fixture; s = f.init(); s.admit("T1"); f.d0(); s.feedback_ready("T1", "A")
        s.enqueue("T1", "A", "diagnostic")
        file = Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt"; file.write_text("new bytes while queued")
        result = s.serve(f.execute)
        self.assertEqual(len(f.calls), 2)  # only original D0 profiles reached receiver
        self.assertTrue(all("while queued" in o["error"]["message"] for o in result["outcomes"]))
        self.assertEqual(s.serve(f.execute)["status"], "queue_empty")

    def test_final_source_cannot_change_even_after_repair_deadline(self):
        f = self.fixture; s = f.init(); s.admit("T1"); f.d0(); s.feedback_ready("T1", "A"); s.lock_source("T1", "A")
        s.enqueue("T1", "A", "final"); s.serve(f.execute)
        file = Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt"; file.chmod(0o644); file.write_text("late edit")
        claim = put(Path(self.temp) / "claim.json", {"statement": "HOST/SIM final claim"})
        with self.assertRaisesRegex(ValueError, "initial/final"):
            s.seal_self("T1", "A", claim)
        self.assertIsNone(s.one("T1", "A", "self_sealed"))

    def test_sequential_tasks_all_ten_barrier_and_hidden_contexts(self):
        f = self.fixture; s = f.init()
        with self.assertRaisesRegex(ValueError, "sequential"):
            s.admit("T2")
        with self.assertRaisesRegex(ValueError, "All ten"):
            s.authorize_hidden()
        self.assertTrue(all(not Path(p).exists() for t in f.manifest["tasks"] for a in t["arms"].values() for p in a["hidden_configs"].values()))
        for n in range(1, 6):
            f.finish_task("T" + str(n))
            if n < 5:
                with self.assertRaisesRegex(ValueError, "All ten"):
                    s.seal_cohort()
        self.assertEqual(len(s.history(kind="self_sealed")), 10)
        s.seal_cohort()
        f.create_hidden()
        grant = s.authorize_hidden()
        self.assertEqual(grant["cohort_members"], 10)
        own_endpoint = s.one("T1", "A", "self_sealed")["own_delivery_wall_seconds"]
        self.assertGreaterEqual(own_endpoint, 0)
        self.assertEqual(s.one("T1", "A", "self_sealed")["own_delivery_wall_seconds"], own_endpoint)
        with self.assertRaisesRegex(ValueError, "one-shot"):
            s.authorize_hidden()

    def test_hidden_files_are_never_opened_before_cohort(self):
        f = self.fixture
        hidden = {Path(p) for t in f.manifest["tasks"] for a in t["arms"].values() for p in a["hidden_configs"].values()}
        original_open = Path.open
        def reject_hidden(path, *args, **kwargs):
            if path in hidden:
                raise AssertionError("HOST/SIM premature hidden open")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", reject_hidden):
            s = f.init(); s.admit("T1"); f.d0()
            with self.assertRaisesRegex(ValueError, "All ten"):
                s.authorize_hidden()

    def test_zero_exit_or_native_executed_is_not_delivery_acceptance(self):
        f = self.fixture; s = f.init(); s.admit("T1"); f.d0(); s.feedback_ready("T1", "A"); s.lock_source("T1", "A")
        def waiting(request, profile, argv, record):
            f.execute(request, profile, argv, record)
            p = Path(record) / "service/cycle.json"; v = b.load(p); v["status"] = "review_images"; put(p, v)
            return 0
        s.enqueue("T1", "A", "final"); s.serve(waiting)
        claim = put(Path(self.temp) / "claim.json", {"statement": "HOST/SIM selfclaim cannot override service F/U"})
        seal = s.seal_self("T1", "A", claim)
        self.assertFalse(seal["public_service_accepted"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ControllerTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {"kind": "HOST/SIM", "native_execution": False, "sdk_forwarding": False,
               "scope": "Controller state/transport/barrier tests only. Synthetic service receipts are not native evidence or study outcomes.",
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful()}
    put(ARTIFACTS / "RESULT.json", summary)
    raise SystemExit(0 if result.wasSuccessful() else 1)
