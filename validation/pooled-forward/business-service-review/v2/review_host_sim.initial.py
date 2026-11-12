#!/usr/bin/env python3
"""Independent bounded v2 delta review. Every service boundary is synthetic."""
import ast
import copy
import hashlib
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
TOOLS = ROOT / "business-tools-v2"
HELPER_SHA = "cd2ab17f43426096c2ac4c322c5a09310d2d7d2fa9d51c453f3b52cd7083aaf8"
DOMAIN_SHA = "fd82356e7b76a8b3099351d6de4d19259eeb241dd99e06b1c4efad3668ba7c8c"
FREEZE_SHA = "258edc5d22c538587d1b3ff4b950b8c34239ff666325bedbe520d520743929be"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, sort_keys=True, indent=2) + "\n")
    return str(path)


assert sha(TOOLS / "blind_study.py") == HELPER_SHA
assert sha(TOOLS / "source_domain.py") == DOMAIN_SHA
assert sha(TOOLS / "FREEZE.json") == FREEZE_SHA
base = types.ModuleType("test_blind_study")
base.__file__ = str(TOOLS / "test_blind_study.py")
source = Path(base.__file__).read_text()
old = 'ARTIFACTS = HERE / "HOST-SIM"'
assert source.count(old) == 1
exec(compile(source.replace(old, 'ARTIFACTS = Path(' + repr(str(OUT / "existing-suite-scratch")) + ')'), base.__file__, "exec"), base.__dict__)
spec = importlib.util.spec_from_file_location("independent_original_domain_tests", TOOLS / "test_domain_admission.py")
existing_domain = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"test_blind_study": base}):
    spec.loader.exec_module(existing_domain)
b = base.b
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
    summary = {"kind": "HOST/SIM", "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "passed": result.wasSuccessful(), "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False, "tests": result.records}
    put(OUT / (name + ".json"), summary)
    put(OUT / (name + ".log"), stream.getvalue())
    return summary


class IndependentDeltaTests(unittest.TestCase):
    def setUp(self):
        self.temp = str(OUT / "fixtures" / self._testMethodName)
        self.fixture = base.Fixture(self.temp)
        existing_domain.enable_domain(self.fixture)
        # Additional ordinary context identity fields required by the frozen
        # treatment's pure context() function; never business expectations.
        for task in self.fixture.manifest["tasks"]:
            for arm in task["arms"].values():
                for path in arm["public_configs"].values():
                    config = b.load(path)
                    config.update(routes_sha256=b.digest(b.load(config["routes"])), environment_sha256=b.digest(b.load(config["environment"])), launch_ref={"kind": "HOST_SIM_fixture"})
                    base.put(path, config)
        self.patches = [patch.object(b.Study, "execute", side_effect=AssertionError("NO helper forwarding in independent review")),
                        patch.object(b.subprocess, "run", side_effect=AssertionError("NO subprocess forwarding in independent review")),
                        patch.object(b.subprocess, "Popen", side_effect=AssertionError("NO subprocess forwarding in independent review")),
                        patch.object(b, "guard_live", return_value=True)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def start(self):
        s = self.fixture.init()
        s.admit("T1")
        return s

    def ready(self, alias="A", change=True):
        f = self.fixture
        if not hasattr(f, "study"):
            self.start()
        f.d0(alias=alias)
        f.study.feedback_ready("T1", alias)
        if change:
            (Path(f.study.arm("T1", alias)["source_roots"][0]) / "Opaque.txt").write_text("HOST/SIM exact actual repaired component " + alias + "\n")
        return f.study

    def review(self, event, mutate=None):
        return existing_domain.DomainTests.review(self, event, mutate)

    def admit(self, alias="A", profile="ios"):
        s = self.fixture.study
        event = s.request_domain_review("T1", alias, profile)
        return event, s.admit_domain_review(**self.review(event))

    def test_both_apis_two_platform_active_config_transport_and_final_lock(self):
        f = self.fixture
        observations = []
        for alias in ["A", "B"]:
            s = self.ready(alias)
            initial_config_hashes = {p: sha(path) for p, path in s.arm("T1", alias)["public_configs"].items()}
            anchor = s.one("T1", alias, "repair_started")
            for profile in ["ios", "android"]:
                original = copy.deepcopy(s.active_configs("T1", alias)[profile])
                event, admitted = self.admit(alias, profile)
                request = b.load(event["request"]["path"])
                actual = s.assert_source("T1", alias)
                self.assertEqual(actual, request["source"])
                self.assertEqual(Path(request["component_capsule"]["path"]).read_bytes(), Path(request["component"]["path"]).read_bytes())
                old, new = b.load(original["path"]), b.load(admitted["config"]["path"])
                self.assertEqual({k: v for k, v in old.items() if k != "coverage_domain_ref"}, {k: v for k, v in new.items() if k != "coverage_domain_ref"})
                self.assertEqual(b.domain.digest(b.domain.policy(b.load(old["coverage_domain_ref"]["path"]))), b.domain.digest(b.domain.policy(b.load(new["coverage_domain_ref"]["path"]))))
                self.assertEqual(s.one("T1", alias, "repair_started"), anchor)
                observations.append({"arm": alias, "profile": profile, "request": event["request"], "config": admitted["config"], "policy_sha256": admitted["policy_sha256"]})
            s.lock_source("T1", alias)
            s.enqueue("T1", alias, "final")
            result = s.serve(f.execute)
            self.assertTrue(all(not o.get("error") for o in result["outcomes"]))
            for profile, original_path in s.arm("T1", alias)["public_configs"].items():
                self.assertEqual(sha(original_path), initial_config_hashes[profile])
                call = [c for c in f.calls if c["arm"] == alias and c["profile"] == profile][-1]
                active = s.active_configs("T1", alias)[profile]
                self.assertEqual(call["argv"][call["argv"].index("--config") + 1], active["path"])
                self.assertEqual("--previous" in call["argv"], alias == "A")
                self.assertEqual("--history" in call["argv"], alias == "A")
                self.assertNotIn("--fresh", call["argv"])
                receipt = b.load(Path(next(o for o in result["outcomes"] if o["profile"] == profile)["service_output"]).parent / "profile-admission.json")
                self.assertEqual(receipt["config"]["sha256"], active["sha256"])
                self.assertEqual(receipt["platform"], profile)
            claim = put(Path(self.temp) / (alias + "-claim.json"), {"statement": "HOST/SIM final endpoint"})
            self.assertTrue(s.seal_self("T1", alias, claim)["public_service_accepted"])
        DETAILS["both_api_active_config_transport"] = observations

    def test_frozen_default_context_and_pending_measured_repair_are_preserved(self):
        s = self.ready("B", change=False)
        config = b.load(s.active_configs("T1", "B")["ios"]["path"])
        d = types.ModuleType("design_contract")
        d.digest, d.load = b.digest, lambda p: b.load(p)
        source_identity = types.ModuleType("source_identity")
        source_identity.model = lambda c, p: {"platform": p, "source_roots": c["source_roots"]}
        source_identity.fingerprint = lambda c, p: {str(q): sha(q) for raw in c["source_roots"] for q in sorted(Path(raw).rglob("*")) if q.is_file()}
        domain_spec = importlib.util.spec_from_file_location("coverage_domain", ROOT / "candidate-v13.9/scripts/coverage_domain.py")
        frozen_domain = importlib.util.module_from_spec(domain_spec)
        with patch.dict(sys.modules, {"design_contract": d}):
            domain_spec.loader.exec_module(frozen_domain)
        validity = types.ModuleType("capture_validity")
        validity.sha = sha
        validity.__file__ = str(Path(self.temp) / "synthetic-tool/scripts/capture_validity.py")
        validity.__dict__.update(Path=Path, d=d, source_identity=source_identity, host_identity=lambda c, p: {"scope": "HOST/SIM no SDK identity query"}, build_dependencies=lambda c, p: {}, dependency_environment=lambda c, p: {})
        tree = ast.parse((ROOT / "candidate-v13.9/scripts/capture_validity.py").read_text())
        context_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "context")
        exec(compile(ast.Module(body=[context_node], type_ignores=[]), str(ROOT / "candidate-v13.9/scripts/capture_validity.py"), "exec"), validity.__dict__)
        resource = types.ModuleType("resource_manager")
        resource.no_symlinks = lambda p: Path(p).resolve()
        resource.lease_clock = lambda: 12345.0
        resource.boot_identity = lambda: "HOST_SIM_NOT_A_REAL_BOOT"
        wf_spec = importlib.util.spec_from_file_location("independent_frozen_workflow", ROOT / "candidate-v13.9/scripts/workflow_state.py")
        workflow = importlib.util.module_from_spec(wf_spec)
        modules = {"capture_validity": validity, "design_contract": d, "source_identity": source_identity, "execution_plan": types.ModuleType("execution_plan"), "resource_manager": resource, "coverage_domain": frozen_domain}
        with patch.dict(sys.modules, modules):
            wf_spec.loader.exec_module(workflow)
            with workflow.Session(config, Path(self.temp) / "context-before") as session:
                before_sha = session.context_sha
                capture = put(Path(self.temp) / "original-capture.json", {"scope": "HOST/SIM original task anchor"})
                task_path = put(Path(self.temp) / "repair-task.json", {"capture": workflow.reference(capture), "context_sha256": before_sha, "source_map": source_identity.fingerprint(config, "ios")})
                task_ref = workflow.reference(task_path)
                session.state["task"] = task_ref
                session.checkpoint()
            (Path(config["source_roots"][0]) / "Opaque.txt").write_text("HOST/SIM measured current repair after source review\n")
            _, admitted = self.admit("B", "ios")
            active = b.load(admitted["config"]["path"])
            self.assertEqual(validity.context(config, "ios"), validity.context(active, "ios"))
            self.assertEqual(frozen_domain.policy(b.load(config["coverage_domain_ref"]["path"])), b.domain.policy(b.load(active["coverage_domain_ref"]["path"])))
            with workflow.Session(active, Path(self.temp) / "context-after") as session:
                self.assertEqual(session.context_sha, before_sha)
                self.assertEqual(session.state["task"], task_ref)
                pending = session.complete(task_ref)
                completion = copy.deepcopy(session.state["completion"])
                self.assertEqual(pending["status"], "patched_needs_native_retest")
                self.assertEqual(session.state["task"], task_ref)
                self.assertTrue(pending["measured_changed_files"])
            with workflow.Session(active, Path(self.temp) / "context-reopen") as session:
                self.assertEqual(session.state["task"], task_ref)
                self.assertEqual(session.state["completion"], completion)
                self.assertEqual(session.context_sha, before_sha)
        DETAILS["frozen_default_context_and_pending_repair"] = {"context_sha256": before_sha, "task": task_ref, "completion": completion, "config": admitted["config"], "sdk_and_host_observers_stubbed": True, "frozen_context_and_Session_methods_unchanged": True}

    def test_source_lock_after_deadline_admits_readonly_review_without_unlock_or_reset(self):
        s = self.ready()
        anchor = s.one("T1", "A", "repair_started")
        component = Path(s.arm("T1", "A")["source_roots"][0]) / "Opaque.txt"
        with patch.object(b.time, "clock_gettime", return_value=anchor["deadline_clock"] + 10), patch.object(b.time, "time", return_value=anchor["deadline_at_unix"] + 10):
            with b.lock(s.root / "state.lock"):
                s.expire()
            locked = copy.deepcopy(s.one("T1", "A", "source_locked"))
            event = s.request_domain_review("T1", "A", "ios")
            response = self.review(event)
        with patch.object(b.time, "clock_gettime", return_value=anchor["deadline_clock"] + 110), patch.object(b.time, "time", return_value=anchor["deadline_at_unix"] + 110):
            admitted = s.admit_domain_review(**response)
        self.assertEqual(admitted["review_elapsed_seconds"], 100)
        self.assertEqual(admitted["source_deadline_clock"], anchor["deadline_clock"])
        self.assertEqual(s.one("T1", "A", "source_locked"), locked)
        self.assertFalse(component.stat().st_mode & 0o222)
        self.assertEqual(len(s.history("T1", "A", "repair_unlocked")), 1)
        self.assertEqual(s.one("T1", "A", "repair_started"), anchor)
        with self.assertRaisesRegex(ValueError, "sealed"):
            s.feedback_ready("T1", "A")

    def test_tampered_independent_capsule_cannot_be_resealed_as_actual_source(self):
        s = self.ready()
        event = s.request_domain_review("T1", "A", "ios")
        response = self.review(event)
        folder = Path(response["seal"]).parent
        base.put(folder / "component.source", "HOST/SIM foreign independent capsule")
        seal = b.load(response["seal"])
        seal["files"]["component.source"] = sha(folder / "component.source")
        base.put(response["seal"], seal)
        response["seal_sha"] = sha(response["seal"])
        provenance = b.load(response["provenance"])
        provenance["review_seal_sha256"] = response["seal_sha"]
        base.put(response["provenance"], provenance)
        response["provenance_sha"] = sha(response["provenance"])
        with self.assertRaisesRegex(ValueError, "component capsule differs"):
            s.admit_domain_review(**response)
        self.assertEqual(s.history(kind="domain_review_admitted"), [])

    def test_authority_and_full_active_chain_originals_rechecked_before_queue(self):
        s = self.ready()
        event = s.request_domain_review("T1", "A", "ios")
        response = self.review(event)
        admitted = s.admit_domain_review(**response)
        request = b.load(event["request"]["path"])
        paths = [response["seal"], response["provenance"], str(Path(response["seal"]).parent / "review.json"),
                 str(Path(response["seal"]).parent / "approval.json"), str(Path(response["seal"]).parent / "component.source"),
                 admitted["config"]["path"], str(Path(admitted["config"]["path"]).parent / "approval.json"), event["request"]["path"], request["component_capsule"]["path"],
                 self.fixture.manifest["source_domain_reviews"]["registry"]["path"]]
        for raw in paths:
            path = Path(raw)
            before = path.read_bytes()
            mode = path.stat().st_mode & 0o777
            path.chmod(0o644)
            path.write_bytes(before + b"HOST_SIM_DRIFT")
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                s.enqueue("T1", "A", "diagnostic")
            path.write_bytes(before)
            path.chmod(mode)
        _, identities = s.domain_authority()
        reviewer = Path(identities["shape-reviewer"]["path"])
        previous = reviewer.with_name("shape-reviewer-original")
        reviewer.rename(previous)
        reviewer.mkdir()
        try:
            with self.assertRaisesRegex(ValueError, "root identity changed"):
                s.verify_pins("T1", "A")
        finally:
            reviewer.rmdir()
            previous.rename(reviewer)
        s.verify_pins("T1", "A")
        self.assertEqual(len(s.history("T1", "A", "request_enqueued")), 1)
        DETAILS["chain_drift_inputs_tested"] = paths

    def test_exact_active_config_cannot_change_ownership_or_platform_or_oracle(self):
        s = self.ready()
        _, admitted = self.admit()
        path = Path(admitted["config"]["path"])
        before = path.read_bytes()
        active = b.load(path)
        for key, value in [("resources", {**active["resources"], "root": "/foreign/owned-root"}), ("source_roots", ["/foreign/source"]),
                           ("platform", "android"), ("fixtures", "/foreign/fixtures.json"), ("bridge", "/foreign/bridge"), ("design_sha256", "0" * 64),
                           ("workflow", {"root": "/foreign/workflow"})]:
            path.chmod(0o644)
            base.put(path, {**active, key: value})
            with self.assertRaisesRegex(ValueError, "version changed"):
                s.enqueue("T1", "A", "diagnostic")
            path.write_bytes(before)
            path.chmod(0o444)
        self.assertEqual(s.active_configs("T1", "A")["ios"], admitted["config"])

    def test_actual_plan_platform_drives_guard_despite_opaque_profile_names(self):
        f = self.fixture
        for task in f.manifest["tasks"]:
            for arm in task["arms"].values():
                for key in ["public_configs", "hidden_configs", "profile_admissions"]:
                    arm[key] = {"opaque_red": arm[key]["android"], "opaque_blue": arm[key]["ios"]}
        s = self.start()
        s.enqueue("T1", "A", "diagnostic")
        result = s.serve(f.execute)
        self.assertTrue(all(not o.get("error") for o in result["outcomes"]))
        receipts = []
        for outcome in result["outcomes"]:
            receipt = b.load(Path(outcome["service_output"]).parent / "profile-admission.json")
            expected = "android" if outcome["profile"] == "opaque_red" else "ios"
            self.assertEqual(receipt["platform"], expected)
            self.assertEqual(receipt["platform"], b.load(b.load(receipt["config"]["path"])["plan"])["design_contract"]["platform"])
            receipts.append(receipt)
        DETAILS["opaque_profile_plan_platform_receipts"] = receipts

    def test_inconsistent_explicit_platform_rejects_before_any_forward(self):
        arm = self.fixture.manifest["tasks"][0]["arms"]["A"]
        path = arm["public_configs"]["ios"]
        config = b.load(path)
        config["platform"] = "android"
        base.put(path, config)
        with self.assertRaisesRegex(ValueError, "Actual plan platform"):
            self.fixture.init()
        self.assertEqual(self.fixture.calls, [])

    def test_guard_pin_and_declared_dependency_drift_never_forward(self):
        arm = self.fixture.manifest["tasks"][0]["arms"]["A"]
        dependency = put(Path(self.temp) / "guard-dependency.json", {"scope": "HOST/SIM pinned verifier dependency"})
        for hook in arm["profile_admissions"].values():
            hook["dependencies"] = [dependency]
        s = self.start()
        s.enqueue("T1", "A", "diagnostic")
        base.put(dependency, {"scope": "HOST/SIM swapped verifier dependency"})
        result = s.serve(self.fixture.execute)
        self.assertTrue(all(o.get("error") for o in result["outcomes"]))
        self.assertEqual(self.fixture.calls, [])
        self.assertEqual(len(s.history("T1", "A", "request_finished")), 1)

    def test_guard_mutation_after_verdict_is_caught_before_forward(self):
        arm = self.fixture.manifest["tasks"][0]["arms"]["A"]
        script = arm["profile_admissions"]["ios"]["script"]
        base.put(script, Path(script).read_text() + "\noriginal_verify = verify\ndef verify(root, approval, approval_sha, platform, config):\n    verdict = original_verify(root, approval, approval_sha, platform, config)\n    Path(config['bridge']).write_text('HOST/SIM deliberate guard side effect')\n    return verdict\n")
        s = self.start()
        s.enqueue("T1", "A", "diagnostic")
        result = s.serve(self.fixture.execute)
        self.assertTrue(all(o.get("error") for o in result["outcomes"]))
        self.assertEqual(self.fixture.calls, [])
        self.assertIsNone(s.one("T1", "A", "repair_started"))
        DETAILS["guard_mutation_failure_outcomes"] = result


def main():
    summaries = {"original_phase": run_suite(base.ControllerTests, "original-15-tests"),
                 "frozen_v2_domain": run_suite(existing_domain.DomainTests, "frozen-v2-13-tests"),
                 "independent_delta": run_suite(IndependentDeltaTests, "independent-delta-tests")}
    put(OUT / "observations.json", DETAILS)
    passed = all(v["passed"] for v in summaries.values())
    result = {"kind": "independent-v2-HOST/SIM-forward-review", "passed": passed, "suites": summaries,
              "candidate_helper_sha256": HELPER_SHA, "source_domain_sha256": DOMAIN_SHA,
              "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False,
              "business_quality_or_performance_claim": False}
    put(OUT / "RESULT.json", result)
    print(json.dumps({key: {k: value[k] for k in ["tests_run", "failures", "errors", "passed"]} for key, value in summaries.items()}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
