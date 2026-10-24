import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location("coverage_audit",Path(__file__).resolve().parents[1]/"scripts/coverage.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/"native.json").write_text('{"events":["selected:x"]}')
        self.plan={"version":1,"requirements":[{"id":"choice","source":"brief","description":"Selection callback","cases":["normal"],"related":[],"aspects":[{"id":"event","methods":["native_action","source_review"],"runtime":"action"}]}]}
        self.row={"requirement":"choice","case":"normal","aspect":"event","status":"passed","execution":"observed","method":"native_action","observation":"Native tap produced one selection event","evidence":[{"path":"native.json","sha256":hashlib.sha256((self.root/"native.json").read_bytes()).hexdigest()}]}
    def test_missing_cell_is_not_pass(self):
        r=module.evaluate(self.plan,{"records":[]},self.root);self.assertEqual(r["status"],"needs_review");self.assertEqual(r["observed_decisions"],0)
    def test_observed_native_event_can_pass(self):
        self.assertEqual(module.evaluate(self.plan,{"records":[self.row]},self.root)["status"],"passed")
    def test_source_cannot_replace_executed_action(self):
        self.row["method"]="source_review"
        with self.assertRaises(ValueError):module.evaluate(self.plan,{"records":[self.row]},self.root)
    def test_tampering_rejected(self):
        (self.root/"native.json").write_text('{}')
        with self.assertRaises(ValueError):module.evaluate(self.plan,{"records":[self.row]},self.root)
    def test_duplicate_or_unplanned_cell_rejected(self):
        with self.assertRaises(ValueError):module.evaluate(self.plan,{"records":[self.row,self.row]},self.root)
        self.row["case"]="different"
        with self.assertRaises(ValueError):module.evaluate(self.plan,{"records":[self.row]},self.root)
    def test_missing_aspect_keeps_requirement_incomplete(self):
        self.plan["requirements"][0]["aspects"].append({"id":"state","methods":["native_ax"],"runtime":"state"})
        r=module.evaluate(self.plan,{"records":[self.row]},self.root);self.assertEqual(r["status"],"needs_review");self.assertFalse(r["requirements"][0]["complete"])
    def test_related_rules_never_auto_fail_or_pass(self):
        other=copy.deepcopy(self.plan["requirements"][0]);other["id"]="related";self.plan["requirements"].append(other)
        self.plan["requirements"][0]["related"]=["related"];self.row["status"]="failed"
        r=module.evaluate(self.plan,{"records":[self.row]},self.root)
        self.assertEqual(r["requirements"][1]["status"],"needs_review");self.assertEqual(len(r["related_review_queue"]),1)
    def test_outside_or_unobserved_evidence_rejected(self):
        self.row["evidence"][0]["path"]="../outside.json"
        with self.assertRaises(ValueError):module.evaluate(self.plan,{"records":[self.row]},self.root)
        self.row["execution"]="not_executed"
        with self.assertRaises(ValueError):module.evaluate(self.plan,{"records":[self.row]},self.root)


if __name__=="__main__":unittest.main()
