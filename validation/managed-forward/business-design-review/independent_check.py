#!/usr/bin/env python3
"""Read-only contract recomputation, independent of frozen tool implementations.

Inputs are only the sealed fresh business-design directory. No SDK, collector,
product source, historical business artifact, screenshot, or process control.
The model below is a transcription of the PUBLIC README/API rules, not a reuse
of reference.expected or the preparer's business calculations.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "business-design"
OUT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def money(cents):
    assert isinstance(cents, int) and cents >= 0
    return f"${cents // 100}.{cents % 100:02d}"


class PublicRulesModel:
    def __init__(self, dto):
        self.dto = copy.deepcopy(dto)
        self.selected = None
        self.count = dto["requestedServings"]
        self.credit = self.accepted = self.sent = False

    def option(self):
        return next((o for o in self.dto["options"]
                     if o["id"] == self.selected and o["available"]), None)

    def clamp(self, option):
        self.count = min(option["maximumServings"],
                         max(option["minimumServings"], self.count))

    def update(self, dto):
        old = self.dto
        if dto["requestID"] != old["requestID"]:
            self.__init__(dto)
            return []
        if dto["revision"] == old["revision"]:
            assert dto == old, "Same immutable snapshot identity cannot mutate in place"
            return []
        self.dto = copy.deepcopy(dto)
        self.accepted = self.sent = False
        option = self.option()
        if option is None:
            self.selected = None
        else:
            self.clamp(option)
        self.credit = self.credit and dto["trayReturnCreditCents"] > 0
        return []

    def balance(self):
        option = self.option()
        if option is None:
            return None
        return (option["pricePerServingCents"] * self.count
                - self.dto["prepaidTotalCents"]
                - (self.dto["trayReturnCreditCents"] if self.credit else 0))

    def activate(self, identifier):
        if self.sent:
            return []
        option = self.option()
        if identifier.startswith("menu.option."):
            target = identifier[len("menu.option."):]
            selected = next((o for o in self.dto["options"]
                             if o["id"] == target and o["available"]), None)
            if selected is not None and self.selected != target:
                self.selected = target
                self.clamp(selected)
                self.accepted = False
        elif identifier in ("menu.increase", "menu.decrease"):
            if option is not None:
                old = self.count
                self.count += 1 if identifier == "menu.increase" else -1
                self.clamp(option)
                if self.count != old:
                    self.accepted = False
        elif identifier == "menu.credit":
            if self.dto["trayReturnCreditCents"] > 0:
                self.credit = not self.credit
                self.accepted = False
        elif identifier == "menu.ack":
            if option is not None:
                self.accepted = not self.accepted
        elif identifier == "menu.submit":
            if option is not None and self.accepted:
                d = self.dto
                event = (f"menu.submit|request={d['requestID']}|revision={d['revision']}"
                         f"|option={self.selected}|servings={self.count}"
                         f"|trayCredit={str(self.credit).lower()}|balanceCents={self.balance()}")
                self.sent = True
                return [event]
        else:
            raise AssertionError(identifier)
        return []

    def atoms(self, bindings, theme):
        d, o = self.dto, self.option()
        balance = self.balance()
        if self.sent:
            status = "Request sent. Waiting for the kitchen."
        elif o is None:
            status = "Choose a replacement to continue."
        elif self.accepted:
            status = "Ready to send to the kitchen."
        else:
            status = "Review the balance and accept the updated menu."
        balance_copy = ("Select a dish to calculate the balance" if balance is None
                        else f"Additional payment {money(balance)}" if balance > 0
                        else f"Refund {money(-balance)}" if balance < 0
                        else "No balance due")
        a = {
            "title-label": d["occasion"],
            "context-label": f"Order {d['orderReference']} · {d['venue']} · revision {d['revision']}",
            "original-label": f"Replacing: {d['originalDish']} · {d['requestedServings']} servings",
            "notice-label": d["notice"],
            "servings-label": f"{self.count} servings",
            "selection-label": o["title"] if o else "No replacement selected",
            "total-label": (f"Replacement total {money(o['pricePerServingCents'] * self.count)}"
                            if o else "Replacement total —"),
            "prepaid-label": f"Already paid {money(d['prepaidTotalCents'])}",
            "applied-label": f"Tray credit applied {money(d['trayReturnCreditCents'] if self.credit else 0)}",
            "balance-label": balance_copy,
            "status-label": status,
            "submit-label": "Request sent" if self.sent else "Send replacement request",
            "last-note-label": d["kitchenNotes"][-1],
            "submit-enabled": o is not None and self.accepted and not self.sent,
            "increase-enabled": o is not None and self.count < o["maximumServings"] and not self.sent,
            "decrease-enabled": o is not None and self.count > o["minimumServings"] and not self.sent,
            "credit-enabled": d["trayReturnCreditCents"] > 0 and not self.sent,
            "ack-enabled": o is not None and not self.sent,
            "credit-value": self.credit,
            "ack-value": self.accepted,
            "canvas-fill": "#FFF5F2EA" if theme == "light" else "#FF101A15",
            "summary-fill": "#FFFFFFFF" if theme == "light" else "#FF19291F",
            "send-fill": ("#FF216B4A" if theme == "light" else "#FF8DDBAF")
                         if o is not None and self.accepted and not self.sent
                         else ("#FFD9E2DC" if theme == "light" else "#FF344A3C"),
            # These are required propositions, never claimed actual observations.
            "title-wrapping": True, "option-clipping": True,
            "balance-overlap": True, "title-hierarchy": True,
        }
        for letter in "abc":
            identifier = bindings["choice" + letter.upper()]["identifier"]
            oid = identifier[len("menu.option."):]
            item = next(x for x in d["options"] if x["id"] == oid)
            a[f"option-{letter}-label"] = item["title"]
            a[f"option-{letter}-selected"] = self.selected == oid
            a[f"option-{letter}-enabled"] = item["available"] and not self.sent
        return a


def unit(rule, value, platform):
    if rule == "send-min-height":
        return "pt" if platform == "ios" else "dp"
    if rule.endswith("-event"):
        return "events"
    if rule.endswith("-fill"):
        return "argb"
    return "bool" if isinstance(value, bool) else "string"


def pointer(document, path):
    value = document
    for key in path.lstrip("/").split("/"):
        value = value[key.replace("~1", "/").replace("~0", "~")]
    return value


def check_scope(scope):
    root = ROOT / scope
    contract, reference = read(root / "contract.json"), read(root / "reference.json")
    case = next(iter(contract["scenarios"]))
    scenario = contract["scenarios"][case]
    fixtures = read(root / "cases" / case / "fixtures.json")
    bindings, routes = read(root / "bindings.json"), read(root / "routes.json")
    policy, lock = read(root / "policy.json"), read(root / "design-lock.json")
    model = PublicRulesModel(fixtures["initial"])
    states, rows, input_index = {}, [], 0
    selected = {s["after_action"]: s for s in scenario["states"]}
    for index, action in enumerate(scenario["actions"]):
        if action["type"] == "checkpoint":
            events = []
        elif action["type"] == "apply_next_fixture":
            model.update(fixtures["updates"][input_index])
            input_index += 1
            events = []
        else:
            assert action["type"] == "tap"
            events = model.activate(bindings[action["target"]]["identifier"])
        if index not in selected:
            continue
        state = selected[index]
        assert state["id"] == action["state_id"] and state["input_index"] == input_index
        assert state["coverage"] == "full_content"
        a = model.atoms(bindings, fixtures["theme"])
        if action["type"] == "tap":
            a["action-event"] = events
        elif action["type"] == "apply_next_fixture":
            a["update-event"] = events
        assert a == {k: v["value"] for k, v in reference["expected"][state["id"]].items()}, state["id"]
        states[state["id"]] = a
        rows.append({"state": state["id"], "input_index": input_index,
                     "after_action": index, "selected_option": model.selected,
                     "servings": model.count, "credit": model.credit,
                     "accepted": model.accepted, "sent": model.sent,
                     "balance_cents": model.balance(), "balance_display": a["balance-label"],
                     "events_in_immediate_action_interval": events})
    assert len(states) == 8 and len(contract["rules"]) == 39
    assert set(contract["required_rule_ids"]) == {r["id"] for r in contract["rules"]}
    assert set(scenario["values"]) == set(contract["required_rule_ids"])
    rules = {r["id"]: r for r in contract["rules"]}
    native_claims = [r for r in reference["responsibilities"] if r["method"] != "source"]
    source_claims = [r for r in reference["responsibilities"] if r["method"] == "source"]
    assert len(native_claims) == 39 and len(source_claims) == 17
    assert all(c["priority"] == "must" for c in reference["responsibilities"])
    assert {r for c in native_claims for r in c["rule_ids"]} == set(rules)
    assert all(len(c["rule_ids"]) == 1 for c in native_claims)
    compatible = {"control": "control", "geometry": "geometry", "callback": "event", "visual": "manual"}
    assert all(rules[c["rule_ids"][0]]["kind"] == compatible[c["method"]] for c in native_claims)
    assert all(c["owner"] == c["subject"] == "component" for c in native_claims)
    assert set(reference["source_obligation_routes"]) == {c["id"] for c in source_claims}
    obligations = {o["id"]: o for o in reference["obligations"]}
    assert set(obligations) == set(routes["routes"])
    assert all(o["priority"] == "must" for o in obligations.values())
    for c in source_claims:
        assert not c["rule_ids"] and c["owner"] == c["subject"]
        assert c["owner"] in ("component", "bridge")
        for oid in reference["source_obligation_routes"][c["id"]]:
            assert oid in obligations and c["id"] in routes["routes"][oid]["reason"]
    assert {r for v in routes["routes"].values() for r in v["rule_ids"]} == set(rules)
    assert {a["rule_id"] for a in policy["atoms"]} == {r for r,v in rules.items() if v["kind"] == "manual"}
    assert len(policy["atoms"]) == 7
    for atom in policy["atoms"]:
        assert atom["method"] in rules[atom["rule_id"]]["allowed_methods"]
        assert policy["ownership"][rules[atom["rule_id"]]["target"]] == "component"
        if atom["method"] == "visual":
            assert atom["question"]["source"] == "reference"
            assert pointer(reference, atom["question"]["pointer"])["unit"] == "string"
    plans = {}
    for platform in ("ios", "android"):
        plan = read(root / "compiled" / case / platform / "plan.json")
        assertions = {a["id"]: a for a in plan["assertions"]}
        matrix = {a["id"]: a for a in plan["matrix_contract"]["cells"]}
        independently_required, independently_na = set(), set()
        for sid, a in states.items():
            for rid in rules:
                aid = f"{sid}/{rid}"
                expected = 52 if rid == "send-min-height" else a.get(rid)
                applicable = rid == "send-min-height" or rid in a
                cell = scenario["values"][rid][sid]
                if not applicable:
                    independently_na.add(aid)
                    assert set(cell) == {"not_applicable"} and cell["not_applicable"]
                    assert matrix[aid]["disposition"] == "not_applicable"
                    assert aid not in assertions
                    continue
                independently_required.add(aid)
                assert set(cell) == {"ios", "android"}
                source = cell[platform]
                assert source["source"] == "reference" and set(source) == {"source", "pointer"}
                datum = pointer(reference, source["pointer"])
                assert datum == {"value": expected, "unit": unit(rid, expected, platform)}
                measured_expected = int(expected[1:], 16) if rid.endswith("-fill") else expected
                assert assertions[aid]["expected"] == measured_expected
                assert assertions[aid]["unit"] == unit(rid, expected, platform)
                assert matrix[aid]["disposition"] == "required"
                assert assertions[aid]["requirement_id"] == rid
                if "target" in rules[rid]:
                    assert assertions[aid]["target"] == bindings[rules[rid]["target"]]
                assert assertions[aid]["expectation_provenance"][0]["source_datum"] == datum
        assert len(independently_required) == 303 and len(independently_na) == 9
        assert set(assertions) == independently_required == set(plan["required_assertion_ids"])
        assert set(matrix) == independently_required | independently_na
        assert len(matrix) == 312
        assert plan["states"] == scenario["states"]
        env = read(root / "cases" / case / f"environment.{platform}.json")
        launch = reference["launch"][case][platform]
        bridge = root / ("Bridge.swift" if platform == "ios" else "ObserverBridge.kt")
        assert launch["fixtures_sha256"] == digest(fixtures)
        assert launch["bridge_sha256"] == file_sha(bridge)
        assert env["width"] == fixtures["width"] and env["height"] == fixtures["viewportHeight"]
        assert env["theme"] == fixtures["theme"] and env["direction"] == fixtures["direction"]
        assert (env["dynamic_type"] == fixtures["dynamic_type"] if platform == "ios"
                else env["font_scale"] == fixtures["fontScale"])
        assert digest(lock) == read(root / "seal.json")["design_lock_sha256"]
        plans[platform] = {"assertions": len(assertions), "cells": len(matrix),
                           "not_applicable": sorted(independently_na),
                           "environment": env, "launch": launch,
                           "plan_canonical_sha256": digest(plan)}
    return {"case": case, "independent_state_derivation": rows,
            "expected_value_comparison": "all independently derived business, theme, and proposition expectations match",
            "source_association_claims": len(source_claims), "native_responsibility_claims": len(native_claims),
            "source_route_execution": "not performed; independent textual association completeness only",
            "plans": plans}


def main():
    result = {scope: check_scope(scope) for scope in ("public", "private")}
    pub, priv = ROOT / "public", ROOT / "private"
    for name in ("API.md", "Bridge.swift", "ObserverBridge.kt", "integration.json", "routes.json", "reference.svg"):
        assert (pub / name).read_bytes() == (priv / name).read_bytes(), name
    for name in ("style", "questions", "obligations", "responsibilities", "source_obligation_routes"):
        assert read(pub / "reference.json")[name] == read(priv / "reference.json")[name], name
    assert read(pub / "contract.json")["rules"] == read(priv / "contract.json")["rules"]
    assert read(pub / "policy.json")["atoms"] == read(priv / "policy.json")["atoms"]
    assert (pub / "README.md").read_text().split("## Public continuous example")[0] == (priv / "README.md").read_text().split("## Private continuous case")[0]
    result["shared_product_contract"] = "identical public/private general prose, API, rules, styles, propositions, duties, routes, bridges and structural SVG"
    result["runtime_actuals"] = "not collected; no native, pixel, qualitative-image or SDK pass is claimed"
    data = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    (OUT / "independent-recomputation.json").write_text(data)
    print(json.dumps({"result": "consistent", "scopes": ["public", "private"],
                      "states_per_scope": 8, "assertions_per_plan": 303,
                      "matrix_cells_per_plan": 312, "source_claims_per_scope": 17,
                      "native_execution": "not_performed"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
