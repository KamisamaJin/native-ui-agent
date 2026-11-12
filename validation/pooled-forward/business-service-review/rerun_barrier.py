#!/usr/bin/env python3
"""Rerun only the hidden-open observer corrected to honor keyword mode='w'."""
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
review.OUT = HERE / "barrier-observer-correction"
stream = io.StringIO()
test = review.IndependentTests("test_full_five_pair_barrier_hidden_open_order_and_unique_record_basenames")
result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=review.RecordedResult).run(unittest.TestSuite([test]))
summary = {"kind": "HOST/SIM", "native_execution": False, "sdk_forwarding": False, "tests_run": result.testsRun,
           "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful(), "tests": result.records,
           "corrects": "independent-edge-tests.json hidden-open observer only; Path.open keyword mode='w' was initially misclassified as read",
           "candidate_changed": False, "initial_outcome_retained": True}
review.put(review.OUT / "RESULT.json", summary)
review.put(review.OUT / "test.log", stream.getvalue())
review.put(review.OUT / "observations.json", review.DETAILS)
print(json.dumps({k: summary[k] for k in ["tests_run", "failures", "errors", "passed"]}))
raise SystemExit(0 if result.wasSuccessful() else 1)
