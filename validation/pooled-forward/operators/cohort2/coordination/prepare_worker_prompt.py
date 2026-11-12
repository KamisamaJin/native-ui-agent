#!/usr/bin/env python3
"""Create the same public-only repair instruction for one ready arm."""
import argparse
import json
from pathlib import Path


TASKS = {
    "T1": ("catering-package", "CateringPackagePlanner"),
    "T2": ("training-pathway", "TrainingPathwayEnrollment"),
    "T3": ("subscription-capacity", "SubscriptionCapacityChange"),
    "T4": ("visitor-preclearance", "VisitorAccessPreclearance"),
    "T5": ("candidate-disposition", "CandidateDispositionReview"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--task", choices=TASKS, required=True)
    ap.add_argument("--arm", choices=("A", "B"), required=True)
    ap.add_argument("--d0", required=True)
    ap.add_argument("--ack", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    r = a.root.resolve()
    run = r / "cache/business/run-cohort2"
    assignment_path = run / "arms" / a.task / a.arm / "assignment.json"
    assignment = json.loads(assignment_path.read_text())
    result_path = run / "requests" / a.d0 / "result.json"
    result = json.loads(result_path.read_text())
    assert result["task"] == a.task and result["arm"] == a.arm
    assert a.ack.is_file()
    anchors = []
    for p in sorted((run / "events").glob("*.json")):
        e = json.loads(p.read_text())
        if e.get("kind") == "repair_started" and (e.get("task"), e.get("arm")) == (a.task, a.arm):
            anchors.append(e)
    assert len(anchors) == 1
    anchor = anchors[0]
    task_name, component = TASKS[a.task]
    tool = assignment.get("tool", {})
    tool_root = tool.get("skill_root") if isinstance(tool, dict) else None
    if tool_root is None:
        tool_root = assignment["skill_root"]
    workspace = r / "cache/business" / a.task / a.arm / "workspace"
    records = workspace.parent / "worker-records"
    prompt = f"""Independently complete your own repair, current-source public evidence reviews, final collection, positive resource closure and self-seal for one real dual-platform business PR. Use the frozen skill at {tool_root}/SKILL.md and its public API docs. This is an independent forward evaluation: decide from your own raw source, public approved requirements and actual original images; no intended answer or prior findings are provided.

Your sole assignment: {assignment_path}
Your public task root: {r}/business-design-cohort2-v2/public/tasks/{task_name}
Your complete terminal D0 result: {result_path}
Your workspace: {workspace}
Your own records directory: {records}
Frozen controller: {r}/business-tools-v4/blind_study.py
Shared mandatory repair rules: {r}/operators/cohort2/REPAIR-AUTHOR-RULES.md

Read and follow those rules. The coordinator has ALREADY run process-visible feedback-ready and unlocked this arm (receipt {a.ack.resolve()}); do not re-acknowledge. The original automatically anchored deadline is {anchor.get('deadline_unix', anchor.get('deadline_at_unix', 'recorded in your original repair_started event'))}; it never resets. Analysis and review consume the existing window. You have at most TWO diagnostic bundles TOTAL including this D0; D1 is optional. Early source lock is irrevocable. Read-only final reviews and source-shape approval may finish after source lock/deadline.

Only these two production files are editable:
{workspace}/alerttoast/Sources/AlertToast/{component}.swift
{workspace}/reply/Reply/app/src/main/java/com/example/reply/ui/components/business/{component}.kt
Write your own submissions/logs/claim only under your own records directory. Every other source, configuration, design, expected value, bridge, tool, build input and resource policy is frozen. No injected defects, fixture-specific substitutions, permission bypass, extra native tests, manual screenshots or direct SDK/ui_loop calls.

The common FIFO pump already serves requests. ONLY enqueue actions using the frozen controller and poll your own original result files; NEVER call serve. Redirect verbose JSON to own records. Inspect D0 and actually view its original PNGs before making source changes. Keep product issues distinct from infrastructure, binding and incomplete evidence. Bind all mandatory generated source-review claims (the default three) and relevant actual image observations through review-source/review-native requests. Honest F/U/unassessed is required where evidence is unavailable; never infer an unseen image from expected text/source.

If iOS source changes, finish the intended patch, ensure no native ticket is pending, then request-domain-review --assignment ... --profile ios. Send the returned exact request ID/path to /root/v13_business_ops. Do not change source while its exact-source review is pending; the registered independent reviewer and coordinator handle same-policy admission. Android-only source changes do not require iOS source approval. Do not inspect other arms/cases, controller manifest/events, private inputs, prior experiments, costs, other judgments or hidden data.

When ready, lock-source, enqueue final, inspect and bind current final source and original native images, and finish-review for each profile. Positive retirement must be proved; if missing, explicitly request retire and retain failed final. Source/native/image evidence and service acceptance remain separate. No hidden quality conclusion is available to you. Complete a truthful self-claim with statement, deduplicated evidence-based alerts/classification, attempted_repairs, known_unresolved, actual public final statuses. Then seal-self. Return the exact SELF-SEAL.json path and a concise actual outcome. Do not stop at a plan; carry your authorized own arm through final self-sealing.\n"""
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x") as fp:
        fp.write(prompt)
    print(prompt)


if __name__ == "__main__":
    main()
