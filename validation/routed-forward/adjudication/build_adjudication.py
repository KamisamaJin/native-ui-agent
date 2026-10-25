"""Derive anonymous adjudication artifacts without changing any original actuals."""
import collections
import datetime
import hashlib
import json
import pathlib
import time

BASE = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(__file__).resolve().parent
CANDIDATES = ["candidate-2cf4bb56", "candidate-e5677eae", "candidate-d1cbcd54"]
INITIAL = "candidate-d1cbcd54"
FINALS = CANDIDATES[:2]
PANELS = ["panel-one", "panel-two"]
CASES = [("public", "quiet-library"), ("private", "long-library")]
inputs = {}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def record(p):
    p = pathlib.Path(p)
    inputs[str(p.relative_to(BASE))] = sha(p)
    return p


def read(p):
    return json.loads(record(p).read_text())


def ref(p, pointer=None, detail=None):
    p = record(p)
    d = {"file": str(p.relative_to(BASE)), "sha256": sha(p)}
    if pointer is not None:
        d["pointer"] = pointer
    if detail is not None:
        d["details"] = detail
    return d


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


protocol = read(BASE / "ADJUDICATION-PROTOCOL.json")
schema = read(BASE / "ADJUDICATION-SCHEMA.json")
identity = read(BASE / "adjudication-input/initial-identity.json")
assert identity["initial_candidate"] == INITIAL
assert set(identity["candidates"]) == set(CANDIDATES)
for scope, _ in CASES:
    record(BASE / "design" / scope / "requirements.md")

seal_checks = {}
for pn in PANELS:
    p = BASE / "quality-panels" / pn
    s = read(p / "SEAL.json")
    bad = [f for f, h in s["files"].items() if not (p / f).is_file() or sha(p / f) != h]
    assert not bad, bad
    seal_checks[pn] = {"seal": ref(p / "SEAL.json"), "verified_file_count": len(s["files"]), "mismatch": bad}

observations = {}
native_extracts = []
sources = {}
for c in CANDIDATES:
    f = BASE / "quality-inputs" / c / "source/alerttoast/Sources/AlertToast/ListeningBreakPanel.swift"
    text = record(f).read_text()
    sources[c] = f
    source_lines = [{"line": i, "text": l.strip()} for i, l in enumerate(text.splitlines(), 1) if "accessibility" in l]
    for scope, case in CASES:
        p = BASE / "quality-inputs" / c / "native" / scope / "ios" / case / "native/observation.json"
        d = read(p)
        observations[(c, scope)] = d
        s = d["snapshots"][3]
        nodes = [{k: n.get(k) for k in ("index", "parent_index", "identifier", "role_raw", "label", "enabled", "selected", "value")} for n in s["nodes"] if n.get("identifier", "").startswith("listening.") or (n.get("role_raw") == 9 and n.get("parent_index") in (10, 14, 18))]
        steps = [{"step": i, "state_id": x.get("state_id"), "outcome": x.get("outcome"), "same_process": x.get("same_process"), "dispatch": x.get("dispatch"), "callback_delta": x.get("callback_delta")} for i, x in enumerate(d["steps"])]
        captures = [{k: x.get(k) for k in ("state_id", "after_action", "snapshot_indices", "complete", "stable_binding", "binding")} for x in d["state_captures"]]
        native_extracts.append({"candidate": c, "scope": scope, "platform": "ios", "source": ref(f), "accessibility_source_lines": source_lines, "original_observation": ref(p), "snapshot3_nodes": nodes, "steps": steps, "state_captures": captures})

# These four original pixels were opened by view_image. Their role is visual
# corroboration only; native identifiers/roles come from the observation JSON.
viewed = []
for c, state, idx in [(INITIAL, "validation", 8), (INITIAL, "started", 26), (FINALS[0], "started", 16), (FINALS[1], "started", 16)]:
    d = observations[(c, "public")]
    p = BASE / "quality-inputs" / c / "native/public/ios/quiet-library/native" / d["snapshots"][idx]["screenshot"]
    detail = "Unchanged empty editing: acknowledgement off, Start listening, no error or summary, observer callbacks 0." if c == INITIAL else "Started state visible: acknowledgement on, ready status and rain summary, Choose again, observer callbacks 1."
    viewed.append({"candidate": c, "state_label": state, "snapshot_index": idx, "evidence": ref(p), "observed": detail, "scope": "Original image visually inspected at display resolution; no computed-font, native-role or physical-hit inference."})

raw = {"version": 1, "scope": "Exact unchanged original status inventory. No F/U is rescored by adjudication.", "panels": {}, "automatic": []}
panel_sources = {}
panel_runtime = {}
dispositions = []
unresolved = {c: [] for c in CANDIDATES}
cause_ids = ["ios-canvas-child-identity", "ios-option-native-semantics"]
extra_refs = {i: [] for i in cause_ids}
all_extra = {}
alarms = {}
for pn in PANELS:
    rp = BASE / "quality-panels" / pn
    ep = BASE / "quality-evaluation" / pn
    alarms[pn] = read(rp / "alarm-judgments.json")
    all_extra[pn] = read(rp / "extra-findings.json")
    raw["panels"][pn] = {"source": [], "runtime": [], "manual": [], "visual": []}
    for j, a in enumerate(alarms[pn]):
        assert a["cause"] == "false_alarm"
        evidence = [ref(rp / "alarm-judgments.json", f"/{j}")] + a["evidence"]
        dispositions.append({"key": f"quality-panels/{pn}/alarm-judgments.json#/{j}", "candidate": a["candidate"], "scope": a["scope"], "platform": a["platform"], "assertion_id": a["assertion_id"], "original_cause": a["cause"], "original_status": "failed", "disposition": "false_alarm", "cause_id": None, "reason": "Both panels agree: the required native activation was unavailable (attempted=false, succeeded=false). Absence is an accurate observation of unchanged editing, but its conditional business-state oracle is unqualified. Preserve the original strict F; do not claim either a business defect or successful validation/start behavior.", "evidence": evidence})
    for j, x in enumerate(all_extra[pn]):
        key = f"quality-panels/{pn}/extra-findings.json#/{j}"
        ev = [ref(rp / "extra-findings.json", f"/{j}")] + x["evidence"]
        if x["cause"] == "product":
            cid = cause_ids[0] if x["obligation_id"] == "A-identifiers" else cause_ids[1]
            assert x["obligation_id"] in ("A-identifiers", "O-semantics")
            disposition = "confirmed_product"
            reason = "Jointly confirmed accessibility/testability manifestation, matched once across public/private routes and states to " + cid + ". It does not establish an unexecuted business transition failure."
            extra_refs[cid].append(ev[0])
        elif x["cause"] == "oracle":
            cid = None
            disposition = "non_product_host_or_collector"
            reason = "Evidence/oracle qualification problem, mapped to the two failed presence alarms in this candidate/scope. Automatic strict Fs remain unchanged; no separate product business cause is added."
        elif x["obligation_id"] == "O-control-size":
            cid = None
            disposition = "uncertain"
            reason = "Native rectangle coverage is unavailable. Panel one attributes this to collector coverage; panel two preserves uncertain attribution. These labels are retained without forced agreement. A long control not fitting fully in one viewport is not proof that its minimum rectangle is too small. Source minHeight and readable sweeps do not replace the required native box; U remains U."
        else:
            assert x["cause"] == "uncertain" and x["obligation_id"] == "O-route-behavior"
            cid = None
            disposition = "uncertain"
            reason = "Panel two explicitly reports an unexercised dirty-state prerequisite; panel one has no corresponding standalone extra finding. Both original visual records leave dependent checkpoints unknown. Successful caller replacement of already-empty editing cannot establish dirty-state reset. No confirmed product cause is inferred."
        dispositions.append({"key": key, "candidate": x["candidate"], "scope": x["scope"], "platform": x["platform"], "obligation_id": x["obligation_id"], "original_cause": x["cause"], "disposition": disposition, "cause_id": cid, "reason": reason, "evidence": ev})
    for scope, case in CASES:
        for c in CANDIDATES:
            f = ep / "source" / scope / (c + ".json")
            d = read(f)
            panel_sources[(pn, scope, c)] = d
            rows = d["rows"]
            assert not [r for r in rows if r["status"] == "failed"]
            raw["panels"][pn]["source"].append({"candidate": c, "scope": scope, "evidence": ref(f), "counts": dict(collections.Counter(r["status"] for r in rows)), "nonpassed": [{k: r.get(k) for k in ("id", "review_id", "status", "actual", "reason")} for r in rows if r["status"] != "passed"]})
            for j, r in enumerate(rows):
                if r["status"] == "passed":
                    continue
                reason = "The original component-only source proposition cannot establish the external bridge/review/observer obligation. This is an evidence-scope boundary, not an observed product defect; no outside evidence is used to turn the original source U into P."
                if r["id"] == "A-identifiers":
                    reason = "Source-only U is retained: declarations do not prove runtime exposure. The separate original native manifestation is confirmed under ios-canvas-child-identity; this does not retroactively change the source row."
                dispositions.append({"key": str(f.relative_to(BASE)) + f"#/rows/{j}", "candidate": c, "scope": scope, "platform": "source-both-platforms", "obligation_id": r["id"], "original_status": r["status"], "disposition": "uncertain", "cause_id": None, "related_confirmed_cause_id": cause_ids[0] if r["id"] == "A-identifiers" else None, "reason": reason, "evidence": [ref(f, f"/rows/{j}")]})
            if pn == PANELS[0]:
                unresolved[c].append(f"source/{scope}: original U for " + ", ".join(r["id"] for r in rows if r["status"] != "passed") + "; complete mandatory source audit is not established in the original scope.")
            for platform in ("ios", "android"):
                p = ep / "runtime" / c / scope / platform / case
                e = read(p / "evaluated.json")
                m = read(p / "manual.json")
                v = read(rp / "visual" / c / scope / platform / case / "submission.json")
                panel_runtime[(pn, c, scope, platform)] = e
                assert not [r for r in m["decisions"] if r["status"] == "failed"]
                raw["panels"][pn]["runtime"].append({"candidate": c, "scope": scope, "platform": platform, "evidence": ref(p / "evaluated.json"), "counts": e["counts"], "nonpassed": [{k: r.get(k) for k in ("id", "status", "reason")} for r in e["assertions"] if r["status"] != "passed"]})
                raw["panels"][pn]["manual"].append({"candidate": c, "scope": scope, "platform": platform, "evidence": ref(p / "manual.json"), "counts": dict(collections.Counter(r["status"] for r in m["decisions"])), "nonpassed": [{k: r.get(k) for k in ("id", "status", "reason")} for r in m["decisions"] if r["status"] != "passed"]})
                raw["panels"][pn]["visual"].append({"candidate": c, "scope": scope, "platform": platform, "evidence": ref(rp / "visual" / c / scope / platform / case / "submission.json"), "counts": dict(collections.Counter(str(r["actual"]) for r in v["decisions"])), "nonpassed": [{k: r.get(k) for k in ("review_id", "actual", "reason", "snapshot_indices")} for r in v["decisions"] if r["actual"] is not True]})
                if pn == PANELS[0]:
                    ap = BASE / "quality-inputs" / c / "native" / scope / platform / case / "automatic.json"
                    a = read(ap)
                    raw["automatic"].append({"candidate": c, "scope": scope, "platform": platform, "evidence": ref(ap), "counts": a["counts"], "nonpassed": [{k: r.get(k) for k in ("id", "status", "reason")} for r in a["assertions"] if r["status"] != "passed"]})
                    us = [r for r in e["assertions"] if r["status"] == "unassessed"]
                    if us:
                        unresolved[c].append(f"runtime/{scope}/{platform}: {len(us)} original U; exact IDs/reasons retained in raw-status-inventory.json. " + ("Unavailable selectors leave native properties, geometry and action results unestablished; callback qualification and dirty-state reset remain unknown." if c == INITIAL and platform == "ios" else "Long-content control geometry lacks a unique fully visible native rectangle in one coherent frame; no size failure inferred."))

# Compare original judgments, not reason prose. Any disagreement must be visible.
value_disagreements = []
for scope, case in CASES:
    for c in CANDIDATES:
        a = {r["id"]: (r["status"], r["actual"]) for r in panel_sources[(PANELS[0], scope, c)]["rows"]}
        z = {r["id"]: (r["status"], r["actual"]) for r in panel_sources[(PANELS[1], scope, c)]["rows"]}
        if a != z:
            value_disagreements.append({"candidate": c, "scope": scope, "type": "source"})
        for platform in ("ios", "android"):
            a = {r["id"]: r["status"] for r in panel_runtime[(PANELS[0], c, scope, platform)]["assertions"]}
            z = {r["id"]: r["status"] for r in panel_runtime[(PANELS[1], c, scope, platform)]["assertions"]}
            if a != z:
                value_disagreements.append({"candidate": c, "scope": scope, "platform": platform, "type": "runtime"})
assert not value_disagreements

causes = []
reasons = [
    "Initial iOS source applies listening.canvas to a VStack without an explicit containing accessibility element (lines 165–168). Original ready native snapshots in both independent input routes expose eleven descendants as listening.canvas and none of the required stable child IDs; source declarations alone are not the proof. Both panels independently confirm A-identifiers. Final anonymous sources add .accessibilityElement(children: .contain); both original final native trees expose one canvas plus distinct title, text, switch, action and option IDs, and their approved route dispatches succeed. This matches one iOS canvas identity cause across states and routes. Separate from option-native-semantics: canvas containment and option wrapping are different modifier sites and satisfy different native propositions; fixing either alone does not logically establish the other.",
    "Initial iOS option source inserts .accessibilityElement(children: .ignore) outside each native Button before its label/selected trait/identifier modifiers (lines 207–212). In both original ready native trees the outer role-1 wrapper has title + em dash + detail, while the unnamed role-9 button child has the automatic comma label. Both panels independently confirm O-semantics. Final sources remove that synthetic ignored-children element, and both final native trees expose exactly the required ID and em-dash label directly on role-9 option buttons with observed native dispatch. This is one iOS option semantic composition cause across all options/states/routes, requiring an option-specific correction independent of the root canvas containment correction. It establishes accessibility/testability, not an unexecuted business/callback defect."
]
for i, cid in enumerate(cause_ids):
    ev = list(extra_refs[cid])
    ev += [ref(sources[c], detail="Original sealed iOS production source; modifier lines recorded in evidence-review.json") for c in CANDIDATES]
    for c in CANDIDATES:
        for scope, case in CASES:
            ev.append(ref(BASE / "quality-inputs" / c / "native" / scope / "ios" / case / "native/observation.json", "/snapshots/3/nodes", "Original native ancestry/identifier/role/label facts; dispatch steps retained in evidence-review.json"))
    ev += [ref(BASE / "design" / scope / "requirements.md", detail="R05 distinct stable identifiers; R06 native option button label/selected semantics; R24 successful-dispatch qualification") for scope, _ in CASES]
    causes.append({"id": cid, "category": "accessibility_testability", "platform": "ios", "initial_present": True, "panel_consensus": True, "present_by_candidate": {c: c == INITIAL for c in CANDIDATES}, "reason": reasons[i], "evidence": ev})

participant_claims = {}
for c in CANDIDATES:
    f = BASE / "adjudication-input/participant-claims" / (c + ".json")
    if not f.is_file():
        participant_claims[c] = {"product": 0, "false_alarm": 0, "uncertain": 0, "evidence": [], "available": False, "counts": {"positive_product_statements": 0, "confirmed_distinct_causes": 0, "missed_confirmed_initial_causes": None}, "mapping": [], "reason": "No participant claim capsule was supplied for the initial candidate; discovery/miss/FDR metrics are N/A, not zero-error performance."}
        continue
    d = read(f)
    mapping = []
    for j, x in enumerate(d["findings"]):
        ev = [ref(f, f"/findings/{j}")]
        if x["classification"] == "product":
            ids = cause_ids if c == "candidate-e5677eae" else ([cause_ids[0]] if x["id"] == "IOS-IDENTIFIERS-D0" else [cause_ids[1]])
            mapping.append({"claim_id": x["id"], "original_classification": x["classification"], "disposition": "confirmed_product_discovery", "cause_ids": ids, "positive_product_statement": True, "reason": "Original anonymous initial source/native facts and both panels support the claimed cause(s). Current final anonymous evidence supports absence of those causes. External claim citations were not opened. Intermediate request chronology and exact historical retest counts are not independently verified by the supplied final capsule.", "evidence": ev + [e for ca in causes if ca["id"] in ids for e in ca["evidence"][:4]]})
        else:
            historical = x["id"] == "IOS-REQUEST1-DEPENDENT-START"
            mapping.append({"claim_id": x["id"], "original_classification": x["classification"], "disposition": "unverified_intermediate_history" if historical else "supported_evidence_limitation", "cause_ids": [], "positive_product_statement": False, "reason": "The intermediate request-1 capture is outside the permitted anonymous evidence. Preserve this limited statement without verifying its chronology or inferring a product cause." if historical else "The claim limits inference rather than asserting a product defect/pass. Original undispatched iOS actions, scoped source review, and sampled native evidence support retaining those limits; no full-domain or computed-style acceptance follows.", "evidence": ev})
    participant_claims[c] = {"product": 2, "false_alarm": 0, "uncertain": 0, "available": True, "evidence": [ref(f)], "count_unit": "Distinct independently confirmed product causes discovered, not number of statements, screenshots, strict alarms, options or routes.", "counts": {"positive_product_statements": sum(x["classification"] == "product" for x in d["findings"]), "confirmed_distinct_causes": 2, "false_positive_distinct_product_claims": 0, "uncertain_distinct_product_claims": 0, "confirmed_initial_causes_in_scope": 2, "detected_confirmed_initial_cause_ids": cause_ids, "missed_confirmed_initial_cause_ids": [], "missed_confirmed_initial_causes": 0, "nonpositive_limit_or_unassessed_statements": sum(x["classification"] != "product" for x in d["findings"]), "independent_sample_count": 1}, "mapping": mapping, "verification_limits": ["Do not treat a compound statement covering both causes as two independent samples.", "Historical request-1/request-2 verification claims are not separately established from forbidden controller/workspace paths. Anonymous final captures support the current repaired native condition only.", "The original participant does not assert complete delivery or computed fonts/padding; no unsupported full-pass claim is manufactured."]}

limits = [
    "Independent AI adjudication against two sealed independent AI panels; no human gold or condition map. Only initial identity is known. No source, expectations, threshold, tool, SDK run or original panel judgment was changed.",
    "Both confirmed causes are iOS accessibility_testability. Zero confirmed business_behavior, style or api causes means no jointly established cause in this supplied evidence, not proof those domains are defect-free.",
    "Four unique raw strict F rows (two per initial iOS scope) are jointly false alarms as conditional presence oracles after unexecuted stimuli. Raw Fs are preserved; original business behavior remains unknown. Joint product-attributed raw alarms: zero. Joint product extras: four scope manifestations matching two causes, not zero causes.",
    "All original source/manual judgments are preserved. Source Fs: zero; manual Fs: zero. Initial source U: four per scope; each final source U: three per scope. These U rows block a complete mandatory source-audit pass under the original protocol.",
    "A-bridge-boundary, A-evidence-boundary and A-callback-evidence are component-only source evidence-scope mismatches for external bridge/evaluator/observer propositions. They are evidence/method boundaries, not observed product contradictions. Design bridges or raw native receipts may support limited aspects in a different scope; this adjudication does not import them into original source rows, rescore U, or assert universal policy compliance.",
    "Final original public runtime counts are 224 P / 0 F / 0 U per platform. Each final private runtime has 217 P / 0 F / 7 U on iOS and 218 P / 0 F / 6 U on Android. Original large-copy geometry U remains an observation-method boundary: no unique fully visible native box in one coherent frame. Readable overlapping pixel sweeps and source minHeight declarations do not prove that particular native rectangle assertion, nor does missing geometry prove a product size defect.",
    "Initial iOS native route steps 1–10 were unavailable. Validation/start/renew/cancel and dirty replacement prerequisites are unexecuted; no business cause or business pass is inferred. Spatial sweep completion is independent of action qualification. Panel-two dirty-reset extra remains unresolved; it is not upgraded to consensus.",
    "Panel one collector vs panel two uncertain attribution for five private geometry extras is explicitly retained. Original source Boolean judgments and runtime statuses agree, while visual frame lists/rationale metadata may differ. Differing attribution labels are not forced into a product consensus.",
    "Source font/frame/color declarations are source-only. Native rectangles and labels do not establish computed font/padding/color or physical hit regions. Four directly inspected PNGs corroborate sampled visible state only. Native semantics require JSON ancestry/role/identifier evidence.",
    "Final false mappings refer to these two matched causes in supplied final sources and observed routes. No confirmed residual or new consensus regression is found; this does not remove unrelated U or establish complete delivery.",
    "Claim discovery uses original affirmative product findings and distinct causes. Nonassertive uncertainty/coverage statements are not counted as false-positive product findings. Unsupported intermediate verification history is explicitly unverified. No original evidence behind nonanonymous claim paths was opened.",
    "Zero denominators are N/A. Classic FPR is N/A without a true-negative population; alarm FDR uses the four unique jointly judged alarms, whereas claim FDR uses cause-matched affirmative product claims. Neither panel repetition nor a combined claim creates independent participant samples.",
    "Recorded timing-start follows the initial directory inventory and protocol/schema/identity read. Its measured interval is not a complete author-cost estimate; that initial uninstrumented intake must not be silently treated as zero."
]

result = {"candidates": CANDIDATES, "causes": causes, "unresolved_by_candidate": unresolved, "manifestation_dispositions": dispositions, "participant_claims": participant_claims, "limits": limits, "initial_candidate": INITIAL, "panel_consensus_accounting": {"confirmed_distinct_product_causes": 2, "confirmed_by_category": {"business_behavior": 0, "style": 0, "accessibility_testability": 2, "api": 0}, "unique_raw_strict_F": 4, "unique_jointly_judged_false_alarms": 4, "unique_joint_product_attributed_raw_alarms": 0, "unique_uncertain_raw_F_alarm_attribution": 0, "agreed_source_F": 0, "agreed_manual_F": 0, "product_extra_rows_per_panel": 4, "product_extra_manifestations_deduplicated_across_panels": 4, "product_extra_causes_after_route_matching": 2, "source_runtime_status_disagreements": value_disagreements, "scope": "Original F/U statuses remain in raw-status-inventory.json; no acceptance regrading."}, "panel_attribution_disagreements": {"private_geometry": "Five candidate/platform manifestations: panel-one collector vs panel-two uncertain; retained as uncertain native-geometry requirement outcome, no established product defect.", "dirty_replacement": "Two initial iOS scope extras appear only in panel two. Preserved unresolved; original dependent visual actuals in both panels remain null."}}

write("causes.json", result)
write("raw-status-inventory.json", raw)
write("evidence-review.json", {"version": 1, "scope": "Derived exact native/source excerpts and image inspection notes; not new measurements or regraded original actuals.", "panel_seal_checks": seal_checks, "native": native_extracts, "direct_original_image_inspections": viewed})
write("input-file-sha256.json", dict(sorted(inputs.items())))

coverage = {"version": 1, "alarm_rows": {pn: len(alarms[pn]) for pn in PANELS}, "extra_rows": {pn: len(all_extra[pn]) for pn in PANELS}, "mapped_alarm_rows": sum("alarm-judgments.json#/" in x["key"] for x in dispositions), "mapped_extra_rows": sum("extra-findings.json#/" in x["key"] for x in dispositions), "mapped_source_U_rows": sum("#/rows/" in x["key"] for x in dispositions), "all_joint_product_extra_rows_mapped": all(x["cause_id"] in cause_ids for x in dispositions if x.get("original_cause") == "product"), "original_source_manual_failed_rows": 0, "source_runtime_status_disagreements": value_disagreements}
assert coverage["mapped_alarm_rows"] == 8
assert coverage["mapped_extra_rows"] == 24
assert coverage["mapped_source_U_rows"] == 40
assert coverage["all_joint_product_extra_rows_mapped"]
assert all(set(x["present_by_candidate"]) == set(CANDIDATES) for x in causes)
write("coverage-check.json", coverage)
print(json.dumps(coverage, ensure_ascii=False, indent=2))
