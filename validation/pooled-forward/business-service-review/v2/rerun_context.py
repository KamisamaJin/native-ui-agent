#!/usr/bin/env python3
"""Only rerun the frozen-context check after correcting its host stub name."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("corrected_independent_review", HERE / "review_host_sim.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
review.OUT = HERE / "context-stub-correction"
stream = io.StringIO()
test = review.IndependentDeltaTests("test_frozen_default_context_and_pending_measured_repair_are_preserved")
result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=review.RecordedResult).run(unittest.TestSuite([test]))
summary = {"kind": "HOST/SIM", "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False,
           "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful(), "tests": result.records,
           "corrects": "independent-delta-tests.json context observer stub only: dependency_environment -> environment_dependencies",
           "candidate_changed": False, "initial_outcome_retained": True}
review.put(review.OUT / "RESULT.json", summary)
review.put(review.OUT / "test.log", stream.getvalue())
review.put(review.OUT / "observations.json", review.DETAILS)
print(json.dumps({k: summary[k] for k in ["tests_run", "failures", "errors", "passed"]}))
raise SystemExit(0 if result.wasSuccessful() else 1)
