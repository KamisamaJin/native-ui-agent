"""Audit both frozen reviewers' records and exact original evidence bindings."""
from pathlib import Path
from collections import Counter, defaultdict
import json
import hashlib

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "cause-matching"

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def rows(path):
    d = read(path)
    return d.get("rows", d.get("actuals"))

source_rows = {r: rows(BASE / r / "source-actuals-final.json") for r in ("reviewer-1", "reviewer-2")}
source_lookup = {r: {(x["candidate"], x["platform"], x["scope"], x["claim_id"]): x for x in values} for r, values in source_rows.items()}
source_records = []
for key in sorted(set(source_lookup["reviewer-1"]) | set(source_lookup["reviewer-2"])):
    a, b = [source_lookup[r].get(key) for r in ("reviewer-1", "reviewer-2")]
    claim = next((x for x in read(BASE / f"packet-public/design/{key[2]}/reference.json")["responsibilities"] if x["id"] == key[3]), None)
    source_records.append({"candidate": key[0], "platform": key[1], "scope": key[2], "claim_id": key[3], "reviewer_1_observed": a.get("observed") if a else None, "reviewer_2_observed": b.get("observed") if b else None, "same_actual": bool(a and b and a["observed"] == b["observed"]), "independent_must_source_clause_exists": bool(claim and claim["priority"] == "must" and claim["method"] == "source"), "reviewer_1_row": source_rows["reviewer-1"].index(a) if a else None, "reviewer_2_row": source_rows["reviewer-2"].index(b) if b else None})

visual_rows = {"reviewer-1": [], "reviewer-2": rows(BASE / "reviewer-2/visual-actuals-final.json")}
for filename in ("visual-actuals-public.json", "visual-actuals-hidden-finals.json", "visual-actuals-initial-hidden.json"):
    for row in rows(BASE / "reviewer-1" / filename):
        visual_rows["reviewer-1"].append({**row, "origin_file": filename})
visual_lookup = {}
for reviewer, values in visual_rows.items():
    grouped = defaultdict(list)
    for row in values:
        key = (row["candidate"], row["platform"], row["scope"], row.get("id", row.get("claim_id")))
        grouped[key].append(row)
    visual_lookup[reviewer] = grouped

visual_records = []
observations = {}
source_index = read(BASE / "packet-public/SOURCE-INDEX.json")
for key in sorted(set(visual_lookup["reviewer-1"]) | set(visual_lookup["reviewer-2"])):
    a, b = [visual_lookup[r].get(key, []) for r in ("reviewer-1", "reviewer-2")]
    values = [x.get("observed", x.get("actual")) for x in a + b]
    errors = []
    candidate, platform, scope, atom = key
    prefix = "packet-public" if scope == "public" else "packet-initial-hidden" if candidate == "initial" else "packet-hidden-finals"
    case = "cedar-lunch" if scope == "public" else "evening-service"
    catalog = read(BASE / f"packet-public/design/{scope}/compiled/{case}/{platform}/catalog.json")
    frozen = next(x for x in catalog["rows"] if x["id"] == atom)
    image_checks = []
    for reviewer, collection in (("reviewer-1", a), ("reviewer-2", b)):
        for row in collection:
            if row["review_id"] != frozen["review_id"]:
                errors.append(f"{reviewer}: review ID differs from fixed catalog")
            source = row.get("source_identity", {})
            if sha(BASE / "packet-public" / source["packet"]) != source["sha256"]:
                errors.append(f"{reviewer}: source hash mismatch")
            expected_source = source_index[candidate][platform]
            if source["packet"] != expected_source["packet"] or source["sha256"] != expected_source["sha256"]:
                errors.append(f"{reviewer}: source belongs to a different candidate/platform")
            original_citations = []
            for cited in row["citations"]:
                original_citations.extend(cited["fragments"] if "fragments" in cited else [cited])
            for cite in original_citations:
                image = cite.get("current_original_path", cite.get("image", cite.get("path")))
                expected_sha = cite.get("current_original_sha256", cite.get("image_sha256", cite.get("sha256")))
                snapshot_index = cite.get("current_snapshot_index", cite.get("snapshot_index", cite.get("snapshot")))
                image_path = BASE / prefix / image
                if scope == "public":
                    allowed_prefixes = [f"native/{a}/public/D0/{platform}/native/" for a in ("A", "B")] if candidate == "initial" else [f"native/{candidate}/public/Final/{platform}/native/"]
                else:
                    allowed_prefixes = [f"{candidate}/{platform}/native/"]
                if not any(image.startswith(p) for p in allowed_prefixes):
                    errors.append(f"{reviewer}: PNG belongs to a different candidate/platform/scope: {image}")
                actual_sha = sha(image_path)
                observation_path = image_path.parent.parent / "observation.json" if image_path.parent.name == "attachments" else image_path.parent / "observation.json"
                if observation_path not in observations:
                    observations[observation_path] = read(observation_path)
                observation = observations[observation_path]
                snapshot = observation["snapshots"][snapshot_index]
                capture = next(x for x in observation["state_captures"] if x["state_id"] == atom.split("/")[0])
                raw_image = observation_path.parent / snapshot["screenshot"]
                okay = actual_sha == expected_sha and raw_image.resolve() == image_path.resolve() and snapshot_index in capture["snapshot_indices"] and capture["complete"] is True and capture["stable_binding"] is True
                if not okay:
                    errors.append(f"{reviewer}: original PNG/state binding mismatch: {image}")
                image_checks.append({"reviewer": reviewer, "image": str(image_path.relative_to(BASE)), "sha256": actual_sha, "snapshot_index": snapshot_index, "valid_original_state_binding": okay})
    visual_records.append({"candidate": candidate, "platform": platform, "scope": scope, "id": atom, "reviewer_1_original_rows": len(a), "reviewer_2_original_rows": len(b), "reviewer_1_observed": [x["observed"] for x in a], "reviewer_2_observed": [x["observed"] for x in b], "same_actual": bool(a and b and all(x == values[0] for x in values)), "all_actuals_explicit_boolean": all(type(x) is bool for x in values), "errors": errors, "image_checks": image_checks})

submission_records = []
for candidate in ("initial", "A", "B"):
    for platform in ("ios", "android"):
        prefix = "packet-initial-hidden" if candidate == "initial" else "packet-hidden-finals"
        root = BASE / prefix / candidate / platform
        request = read(root / "review-request.json")
        template = request["submission_template"]
        fixed_catalog = read(BASE / f"packet-public/design/private/compiled/evening-service/{platform}/catalog.json")
        catalog_body = {k:v for k,v in fixed_catalog.items() if k != "catalog_sha256"}
        original_observation = read(root / "native/observation.json")
        fixed_by_id = {x["review_id"]: x for x in fixed_catalog["rows"]}
        original_ids = [x["review_id"] for x in template["decisions"]]
        for reviewer in ("reviewer-1", "reviewer-2"):
            name = f"hidden-{candidate}-{platform}-submission.json"
            if candidate == "initial":
                name = f"initial-hidden-{platform}-submission.json" if reviewer == "reviewer-1" else f"hidden-initial-{platform}-submission.json"
            submitted = read(BASE / reviewer / name)
            actual_ids = [x["review_id"] for x in submitted["decisions"]]
            errors = []
            if submitted["catalog_sha256"] != fixed_catalog["catalog_sha256"] or submitted["catalog_sha256"] != template["catalog_sha256"]:
                errors.append("Catalog header mismatch")
            if request["catalog"] != catalog_body:
                errors.append("Request catalog body differs from fixed design")
            if submitted["observation_sha256"] != sha(root / "native/observation.json") or submitted["observation_sha256"] != template["observation_sha256"]:
                errors.append("Observation digest mismatch")
            if actual_ids != original_ids or len(set(actual_ids)) != len(original_ids):
                errors.append("Original decision ID sequence changed or duplicated")
            for decision in submitted["decisions"]:
                frozen = fixed_by_id[decision["review_id"]]
                state = frozen["state"]
                capture = next(x for x in original_observation["state_captures"] if x["state_id"] == state)
                if type(decision["actual"]) is not bool or not decision.get("snapshot_indices") or not set(decision["snapshot_indices"]) <= set(capture["snapshot_indices"]):
                    errors.append(f"Decision lacks explicit actual or current state images: {frozen['id']}")
            submission_records.append({"reviewer": reviewer, "candidate": candidate, "platform": platform, "submission": f"{reviewer}/{name}", "decisions": len(actual_ids), "catalog_header": submitted["catalog_sha256"], "observation_header": submitted["observation_sha256"], "request_omitted_only_redundant_catalog_sha256": request["catalog"] == catalog_body, "errors": errors, "read_only_binding_preconditions_satisfied": not errors, "acceptance_CLI_executed_here": False})

save("cross-review-source-actuals.json", {"rows": source_records, "summary": {"canonical_rows": len(source_records), "semantic_disagreements": sum(not x["same_actual"] for x in source_records), "required_clause_gaps": sum(not x["independent_must_source_clause_exists"] for x in source_records)}})
save("cross-review-visual-actuals.json", {"rows": visual_records, "summary": {"reviewer_1_raw_rows": len(visual_rows["reviewer-1"]), "reviewer_2_final_rows": len(visual_rows["reviewer-2"]), "canonical_rows": len(visual_records), "semantic_disagreements": sum(not x["same_actual"] for x in visual_records), "non_boolean_actuals": sum(not x["all_actuals_explicit_boolean"] for x in visual_records), "evidence_binding_errors": sum(len(x["errors"]) for x in visual_records)}})
save("submission-binding-independent-checks.json", submission_records)
print("source",len(source_records),"disagreements",sum(not x["same_actual"] for x in source_records))
print("visual",len(visual_records),"disagreements",sum(not x["same_actual"] for x in visual_records),"binding errors",sum(len(x["errors"]) for x in visual_records))
print("submissions",len(submission_records),"errors",[(x["reviewer"],x["candidate"],x["platform"],x["errors"]) for x in submission_records if x["errors"]])
