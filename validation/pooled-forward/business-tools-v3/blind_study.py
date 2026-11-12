#!/usr/bin/env python3
"""Case-agnostic, append-only paired-study controller. No oracle or source edits.

This is a procedural gate, not a sandbox against an operator bypassing this CLI.
Native execution is available only through serve(), behind both frozen common
supervisors. Importing this module, init, and HOST/SIM tests never forward SDKs.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import time
import traceback
import uuid

HERE = Path(__file__).resolve().parent
_domain_spec = importlib.util.spec_from_file_location('paired_source_domain', HERE / 'source_domain.py')
domain = importlib.util.module_from_spec(_domain_spec)
_domain_spec.loader.exec_module(domain)
LIMIT = 1200
DIAGNOSTICS = 2


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def absolute(raw):
    if not isinstance(raw, str) or not Path(raw).is_absolute():
        raise ValueError("Explicit absolute path required")
    return Path(os.path.abspath(raw))


def name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ValueError("Safe explicit identifier required")
    return value


def intersects(a, b):
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


def path_strings(value):
    if isinstance(value, dict):
        return [p for item in value.values() for p in path_strings(item)]
    if isinstance(value, list):
        return [p for item in value for p in path_strings(item)]
    return [absolute(value)] if isinstance(value, str) and value.startswith("/") else []


def source(roots):
    """All bytes, no ignore patterns and no symlink traversal; root identity too."""
    files = {}
    identities = []
    for i, raw in enumerate(roots):
        root = absolute(raw)
        if any(p.is_symlink() for p in [root, *root.parents]) or not root.is_dir():
            raise ValueError("Source root must be an existing directory without symlinks")
        st = root.stat()
        identities.append({"path": str(root), "device": st.st_dev, "inode": st.st_ino})
        for p in sorted(root.rglob("*")):
            if p.is_symlink() or not (p.is_file() or p.is_dir()):
                raise ValueError("Only regular source files/directories are admitted: " + str(p))
            if p.is_file():
                files[str(i) + "/" + p.relative_to(root).as_posix()] = {"sha256": sha(p), "bytes": p.stat().st_size}
    if not files:
        raise ValueError("Nonempty production source required")
    return {"roots": identities, "files": files, "content_sha256": digest(files)}


def modes(roots):
    return {str(p): stat.S_IMODE(p.stat().st_mode) for r in roots
            for p in [Path(r), *sorted(Path(r).rglob("*"))]}


def protect(roots):
    for r in roots:
        paths = [*sorted(Path(r).rglob("*")), Path(r)]
        for p in paths:
            p.chmod(stat.S_IMODE(p.stat().st_mode) & ~0o222)


def capsule(folder, roots, expected):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    for relative in expected["files"]:
        index, tail = relative.split("/", 1)
        destination = folder / "files" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(roots[int(index)]) / tail, destination)
        destination.chmod(0o444)
    if source(roots) != expected:
        raise ValueError("Source changed while sealing")
    save(folder / "source.json", expected)
    return str(folder / "source.json")


@contextmanager
def lock(path, blocking=True):
    with Path(path).open("a+") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def frozen_files(tool):
    root = absolute(tool["skill_root"])
    wanted = tool["files"]
    required = {"SKILL.md", *[p.relative_to(root).as_posix() for p in (root / "scripts").glob("*.py")],
                *[p.relative_to(root).as_posix() for p in (root / "references").glob("*.md")],
                *[p.relative_to(root).as_posix() for p in (root / "assets").rglob("*") if p.is_file()]}
    if not required <= set(wanted) or "scripts/ui_loop.py" not in wanted:
        raise ValueError("Pin SKILL.md, every public script, and all public references")
    found = {}
    for relative in wanted:
        p = root / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or p.is_symlink():
            raise ValueError("Unsafe frozen tool member")
        found[relative] = sha(p)
    if found != wanted:
        raise ValueError("Frozen tool identity changed")
    return found


class Study:
    def __init__(self, root):
        self.root = absolute(str(root))
        self.manifest = load(self.root / "manifest.json")
        self.check_manifest_binding()

    def events(self):
        result = []
        previous = None
        for i, path in enumerate(sorted((self.root / "events").glob("*.json"))):
            value = load(path)
            if path.name != f"{i:06d}.json" or value["sequence"] != i or value["previous_sha256"] != previous:
                raise ValueError("Append-only event chain changed")
            previous = sha(path)
            result.append(value)
        return result

    def append(self, kind, **value):
        events = self.events()
        item = {"sequence": len(events), "previous_sha256": sha(self.root / "events" / f"{len(events)-1:06d}.json") if events else None,
                "at_unix": time.time(), "at_clock": time.clock_gettime(time.CLOCK_MONOTONIC), "kind": kind, **value}
        save(self.root / "events" / f"{len(events):06d}.json", item)
        return item

    def check_manifest_binding(self):
        admission = load(self.root / "INIT.json")
        if sha(self.root / "manifest.json") != admission["manifest_sha256"] or sha(__file__) != admission["helper_sha256"]:
            raise ValueError("Manifest or controller changed after init")
        if sha(self.root / "INITIAL-COHORT.json") != admission["initial_cohort_sha256"]:
            raise ValueError("All-five initial cohort admission changed")
        if sha(HERE / 'source_domain.py') != admission['domain_transport_sha256']:
            raise ValueError('Frozen source-domain transport changed after init')
        if admission.get('domain_authority_sha256') and sha(self.root / 'DOMAIN-AUTHORITY.json') != admission['domain_authority_sha256']:
            raise ValueError('Source-domain reviewer authority changed')

    def verify_initial_cohort(self):
        cohort = load(self.root / "INITIAL-COHORT.json")
        if set(cohort) != {t["id"] for t in self.manifest["tasks"]}:
            raise ValueError("All five initial admissions required before any native request")
        for t in self.manifest["tasks"]:
            entries = cohort[t["id"]]
            if set(entries) != set(t["arms"]):
                raise ValueError("Every initial arm admission is required")
            values = []
            for alias, entry in entries.items():
                if sha(entry["path"]) != entry["sha256"]:
                    raise ValueError("Initial admission changed")
                snapshot = load(entry["path"])
                capsule_root = Path(entry["path"]).parent / "files"
                if any(sha(capsule_root / rel) != v["sha256"] for rel, v in snapshot["files"].items()):
                    raise ValueError("Original initial source capsule changed")
                values.append(snapshot["files"])
            if values[0] != values[1]:
                raise ValueError("Paired initial bytes differ")

    def arm(self, task, alias):
        for row in self.manifest["tasks"]:
            if row["id"] == task and alias in row["arms"]:
                return row["arms"][alias]
        raise ValueError("Unknown assignment")

    def folder(self, task, alias):
        return self.root / "arms" / name(task) / name(alias)

    def history(self, task=None, alias=None, kind=None):
        return [e for e in self.events() if (task is None or e.get("task") == task)
                and (alias is None or e.get("arm") == alias) and (kind is None or e["kind"] == kind)]

    def one(self, task, alias, kind):
        values = self.history(task, alias, kind)
        return values[-1] if values else None

    def domain_authority(self):
        settings = self.manifest.get('source_domain_reviews')
        if not settings:
            raise ValueError('No independently predeclared source-domain review authority')
        value, identities = domain.registry(settings['registry'])
        if load(self.root / 'DOMAIN-AUTHORITY.json') != {'registry': settings['registry'], 'identities': identities}:
            raise ValueError('Independent reviewer registry/root identity changed')
        return value, identities

    def active_configs(self, task, alias):
        a = self.arm(task, alias)
        active = {p: domain.reference(path) for p, path in a['public_configs'].items()}
        entries = self.history(task, alias, 'domain_review_admitted')
        if entries:
            authority, identities = self.domain_authority()
        for entry in entries:
            profile = entry['profile']
            if profile not in active or active[profile] != entry['parent_config']:
                raise ValueError('Active source-domain config chain is stale or foreign')
            inventory = entry['files']
            folder = Path(entry['config']['path']).parent
            if {p.name for p in folder.iterdir()} != set(inventory) or any(sha(folder / p) != h for p, h in inventory.items()):
                raise ValueError('Immutable source-domain config/review version changed')
            request = load(entry['request']['path'])
            if sha(entry['request']['path']) != entry['request']['sha256'] or sha(request['component_capsule']['path']) != request['component_capsule']['sha256']:
                raise ValueError('Original source-domain review request changed')
            verified = domain.response(authority, identities, entry['review_seal']['path'], entry['review_seal']['sha256'],
                                       entry['provenance']['path'], entry['provenance']['sha256'], request, entry['request']['sha256'])
            old = load(active[profile]['path']); new = load(entry['config']['path'])
            if {k: v for k, v in old.items() if k != 'coverage_domain_ref'} != {k: v for k, v in new.items() if k != 'coverage_domain_ref'}:
                raise ValueError('Active config may change ONLY coverage_domain_ref')
            proposed = load(new['coverage_domain_ref']['path'])
            if digest(proposed) != new['coverage_domain_ref']['sha256'] or proposed != verified['proposed']:
                raise ValueError('Active approval differs from independently sealed proposal')
            domain.validate_append(load(old['coverage_domain_ref']['path']), proposed, request['platform'], request['component'])
            if domain.reference(entry['config']['path']) != entry['config']:
                raise ValueError('Active config pin changed')
            active[profile] = entry['config']
        return active

    def profile_admission(self, task, alias, profile, config_path, output):
        hook = self.arm(task, alias).get('profile_admissions', {}).get(profile)
        if not hook:
            return None
        config = load(config_path); platform = domain.platform(config)
        approval = load(hook['approval'])
        if digest(approval) != hook['approval_sha256']:
            raise ValueError('Independent profile approval canonical pin changed')
        spec = importlib.util.spec_from_file_location('paired_public_profile_admission_' + uuid.uuid4().hex, hook['script'])
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        verdict = module.verify(Path(hook['root']), approval, hook['approval_sha256'], platform, config)
        if not isinstance(verdict, dict) or verdict.get('status') != 'admitted_profile' or verdict.get('platform') != platform:
            raise ValueError('Public profile admission did not admit the actual plan platform')
        inputs = {}
        for key in ['design_lock', 'plan', 'policy', 'routes', 'environment', 'fixtures']:
            path = config[key]; inputs[key] = {**domain.reference(path), 'canonical_sha256': digest(load(path))}
        inputs['bridge'] = domain.reference(config['bridge'])
        receipt = {'version': 1, 'config': {**domain.reference(config_path), 'canonical_sha256': digest(config)},
                   'script': domain.reference(hook['script']), 'approval': {**domain.reference(hook['approval']), 'canonical_sha256': digest(approval)},
                   'platform': platform, 'platform_source': 'actual config.plan.design_contract.platform', 'inputs': inputs, 'verdict': verdict}
        save(output, receipt)
        return receipt

    def request_domain_review(self, task, alias, profile):
        with lock(self.root / 'state.lock'):
            self.expire()
            if not self.history(task, kind='task_admitted') or not self.one(task, alias, 'repair_started') or self.one(task, alias, 'self_sealed') or self.history(kind='cohort_sealed'):
                raise ValueError('Source-domain review requires active D0 assignment before final self/cohort seal')
            if self.pending(task, alias):
                raise ValueError('No source-domain review/config switch during a pending native ticket')
            self.domain_authority(); pins = self.verify_pins(task, alias)
            settings = self.manifest['source_domain_reviews']
            if len(self.history(task, alias, 'domain_review_requested')) >= settings.get('max_requests_per_arm', 4):
                raise ValueError('Bounded source-domain review request cap reached')
            if profile not in self.arm(task, alias)['public_configs']:
                raise ValueError('Only assigned public profile may request source-domain review')
            active = pins['active_configs'][profile]; config = load(active['path'])
            material = domain.original(config); current = self.assert_source(task, alias)
            request_id = uuid.uuid4().hex
            folder = self.folder(task, alias) / 'domain-requests' / request_id; folder.mkdir(parents=True)
            raw = Path(material['component']['path']).read_bytes()
            with (folder / 'component.source').open('xb') as stream: stream.write(raw)
            (folder / 'component.source').chmod(0o444)
            if self.assert_source(task, alias) != current or hashlib.sha256(raw).hexdigest() != material['component']['sha256']:
                raise ValueError('Source changed while requesting independent shape review')
            request = {'version': 1, 'kind': 'source_shape_review_request', 'request_id': request_id, 'study_id': self.manifest['study_id'],
                       'task': task, 'arm': alias, 'profile': profile, 'platform': material['platform'], 'source': current,
                       'component': material['component'], 'component_capsule': domain.reference(folder / 'component.source'),
                       'active_config': active, 'parent_approval': material['approval_ref'], 'parent_approval_sha256': material['approval_sha256'],
                       'policy_sha256': material['policy_sha256'], 'readset': pins,
                       'scope': 'Independent finite source-shape review only; no oracle/behavioral verdict, source edit, source-window extension or delivery credit'}
            save(folder / 'request.json', request)
            return self.append('domain_review_requested', task=task, arm=alias, profile=profile, request_id=request_id,
                               request=domain.reference(folder / 'request.json'))

    def admit_domain_review(self, request_id, seal, seal_sha, provenance, provenance_sha):
        try:
            return self._admit_domain_review(request_id, seal, seal_sha, provenance, provenance_sha)
        except Exception as error:
            with lock(self.root / 'state.lock'):
                self.append('domain_review_rejected', request_id=request_id,
                            review_seal={'path': str(seal), 'sha256': seal_sha}, provenance={'path': str(provenance), 'sha256': provenance_sha},
                            error={'type': type(error).__name__, 'message': str(error)})
            raise

    def _admit_domain_review(self, request_id, seal, seal_sha, provenance, provenance_sha):
        with lock(self.root / 'state.lock'):
            self.expire()
            events = [e for e in self.history(kind='domain_review_requested') if e['request_id'] == request_id]
            if len(events) != 1:
                raise ValueError('Exact program-generated source-domain review request required')
            event = events[0]; task, alias = event['task'], event['arm']
            if self.one(task, alias, 'self_sealed') or self.history(kind='cohort_sealed') or self.pending(task, alias):
                raise ValueError('Source-domain admission forbidden after final self/cohort seal or during pending native ticket')
            if any(e['request_id'] == request_id for e in self.history(kind='domain_review_admitted')):
                raise ValueError('Independent source-domain review request already admitted')
            pins = self.verify_pins(task, alias); authority, identities = self.domain_authority()
            request = load(event['request']['path'])
            if sha(event['request']['path']) != event['request']['sha256'] or sha(request['component_capsule']['path']) != request['component_capsule']['sha256']:
                raise ValueError('Original source-domain request/capsule changed')
            if self.assert_source(task, alias) != request['source'] or pins['active_configs'][request['profile']] != request['active_config']:
                raise ValueError('Independent review is stale for current source/active config')
            material = domain.original(load(request['active_config']['path']))
            if material['component'] != request['component'] or material['policy_sha256'] != request['policy_sha256']:
                raise ValueError('Current component/policy differs from independently reviewed bytes')
            self.public_path(absolute(str(seal))); self.public_path(absolute(str(provenance)))
            response = domain.response(authority, identities, seal, seal_sha, provenance, provenance_sha, request, event['request']['sha256'])
            revision = domain.validate_append(material['approval'], response['proposed'], request['platform'], material['component'])
            folder = self.folder(task, alias) / 'config-versions' / request_id; folder.mkdir(parents=True, exist_ok=False)
            review_root = Path(seal).resolve().parent
            originals = {'approval.json': review_root / 'approval.json', 'review.json': review_root / 'review.json',
                         'review-seal.json': Path(seal).resolve(), 'provenance.json': Path(provenance).resolve(), 'component.source': Path(request['component_capsule']['path'])}
            for relative, p in originals.items():
                with (folder / relative).open('xb') as stream: stream.write(p.read_bytes())
                (folder / relative).chmod(0o444)
            config = load(request['active_config']['path'])
            config['coverage_domain_ref'] = {'path': str(folder / 'approval.json'), 'sha256': digest(response['proposed'])}
            save(folder / 'config.json', config)
            self.profile_admission(task, alias, request['profile'], folder / 'config.json', folder / 'profile-admission.json')
            self.expire()
            if self.assert_source(task, alias) != request['source']:
                raise ValueError('Source changed during independent approval admission')
            files = {p.name: sha(p) for p in sorted(folder.iterdir())}
            return self.append('domain_review_admitted', task=task, arm=alias, profile=request['profile'], request_id=request_id,
                               request=event['request'], parent_config=request['active_config'], config=domain.reference(folder / 'config.json'),
                               component=request['component'], platform=request['platform'], policy_sha256=request['policy_sha256'], revision=revision,
                               review_seal={'path': str(Path(seal).resolve()), 'sha256': seal_sha},
                               provenance={'path': str(Path(provenance).resolve()), 'sha256': provenance_sha}, files=files,
                               review_elapsed_seconds=time.clock_gettime(time.CLOCK_MONOTONIC) - event['at_clock'],
                               source_deadline_clock=self.one(task, alias, 'repair_started')['deadline_clock'],
                               attribution='Common independent source-shape approval transport; no treatment semantics or quality credit')

    def verify_pins(self, task, alias):
        self.check_manifest_binding()
        a = self.arm(task, alias)
        public = load(self.folder(task, alias) / "public-inputs.json")
        actual = {p: sha(p) for p in public}
        if public != actual:
            raise ValueError("Admitted public input/config changed")
        frozen_files(self.manifest["tools"][a["tool"]])
        for key, filekey in [("path", "sha256"), ("meter_path", "meter_sha256"), ("meter_spec_path", "meter_spec_sha256")]:
            if sha(self.manifest["envelope"][key]) != self.manifest["envelope"][filekey]:
                raise ValueError("Common frozen supervisor/spec changed")
        p = self.manifest["protocol"]
        if sha(p["path"]) != p["sha256"]:
            raise ValueError("Frozen study protocol changed")
        for key in ["speed_gate", "design_approval"]:
            ref = self.manifest[key]
            if sha(ref["path"]) != ref["sha256"]:
                raise ValueError("Prerequisite seal changed: " + key)
        if self.manifest.get('source_domain_reviews'):
            self.domain_authority()
        return {"public_inputs": actual, "tool_files": self.manifest["tools"][a["tool"]]["files"],
                "helper_sha256": sha(__file__), "speed_gate": self.manifest["speed_gate"], "design_approval": self.manifest["design_approval"],
                'domain_transport_sha256': sha(HERE / 'source_domain.py'),
                'source_domain_registry': self.manifest.get('source_domain_reviews', {}).get('registry'),
                'active_configs': self.active_configs(task, alias)}

    def assert_source(self, task, alias, expected=None):
        a = self.arm(task, alias)
        current = source(a["source_roots"])
        initial = load(self.folder(task, alias) / "initial" / "source.json")
        if current["roots"] != initial["roots"]:
            raise ValueError("Source root identity changed")
        frozen = self.one(task, alias, "source_locked")
        if frozen:
            if sha(frozen["source_manifest"]) != frozen["source_manifest_sha256"]:
                raise ValueError("Final source manifest changed")
            expected = load(frozen["source_manifest"])
            archive = Path(frozen["source_manifest"]).parent / "files"
            if any(sha(archive / rel) != row["sha256"] for rel, row in expected["files"].items()):
                raise ValueError("Original final source capsule changed")
        elif not self.one(task, alias, "repair_unlocked"):
            expected = initial
        if expected and current != expected:
            raise ValueError("Source differs from required initial/final seal")
        return current

    def freeze(self, task, alias, reason):
        if self.one(task, alias, "source_locked"):
            self.assert_source(task, alias)
            return self.one(task, alias, "source_locked")
        a = self.arm(task, alias)
        before = self.assert_source(task, alias)
        protect(a["source_roots"])
        sealed = capsule(self.folder(task, alias) / "final-source", a["source_roots"], before)
        start = self.one(task, alias, "repair_started")
        late_changes = [str(p) for r in a["source_roots"] for p in Path(r).rglob("*")
                        if p.is_file() and start and p.stat().st_mtime > start["deadline_at_unix"]]
        return self.append("source_locked", task=task, arm=alias, reason=reason,
                           source_manifest=sealed, source_manifest_sha256=sha(sealed), source_sha256=before["content_sha256"],
                           source_deadline_compliant=not late_changes, changed_after_deadline=late_changes,
                           deadline_enforcement_lateness_seconds=max(0, time.clock_gettime(time.CLOCK_MONOTONIC) - start["deadline_clock"]) if start else None)

    def expire(self, timeline=None):
        now = time.clock_gettime(time.CLOCK_MONOTONIC)
        events = self.events() if timeline is None else timeline
        for t in self.manifest["tasks"]:
            for alias in t["arms"]:
                own = [e for e in events if e.get("task") == t["id"] and e.get("arm") == alias]
                start = next((e for e in reversed(own) if e["kind"] == "repair_started"), None)
                frozen = any(e["kind"] == "source_locked" for e in own)
                if start and not frozen and (now >= start["deadline_clock"] or time.time() >= start["deadline_at_unix"] or now < start["at_clock"]):
                    self.freeze(t["id"], alias, "repair_deadline")

    def pending(self, task=None, alias=None):
        completed = {e["request_id"] for e in self.history(kind="request_finished")}
        return [e for e in self.history(task, alias, "request_enqueued") if e["request_id"] not in completed]

    def admit(self, task):
        with lock(self.root / "state.lock"):
            self.expire()
            rows = self.manifest["tasks"]
            self.verify_initial_cohort()
            index = next((i for i, t in enumerate(rows) if t["id"] == task), None)
            if index is None or self.history(task, kind="task_admitted"):
                raise ValueError("Unknown/already admitted task")
            for previous in rows[:index]:
                if any(not self.one(previous["id"], alias, "self_sealed") for alias in previous["arms"]):
                    raise ValueError("Tasks must finish sequentially, including retirement and self-claims")
            for alias, a in rows[index]["arms"].items():
                self.verify_pins(task, alias)
                self.assert_source(task, alias)
                protect(a["source_roots"])
            return self.append("task_admitted", task=task, arms=list(rows[index]["arms"]),
                               delivery_clock_start="Each arm's first D0 enqueue; includes all queue, SDK, review/check, retirement and self-claim time")

    def enqueue(self, task, alias, action, profile=None, submission=None, supersedes=(), revision_reason=None):
        with lock(self.root / "state.lock"):
            self.expire()
            a = self.arm(task, alias)
            if not self.history(task, kind="task_admitted") or self.one(task, alias, "self_sealed"):
                raise ValueError("Assignment is not active")
            if self.pending(task, alias):
                raise ValueError("Finish the arm's outstanding request first")
            pins = self.verify_pins(task, alias)
            current = self.assert_source(task, alias)
            if action == "diagnostic":
                self.verify_initial_cohort()
                requests = [e for e in self.history(task, alias, "request_enqueued") if e["action"] == "diagnostic"]
                if len(requests) >= DIAGNOSTICS or self.one(task, alias, "source_locked"):
                    raise ValueError("Diagnostic request cap reached or source already sealed")
            elif action == "final":
                if not self.one(task, alias, "source_locked"):
                    raise ValueError("Lock source before public final collection")
            elif action not in {"review-native", "review-source", "finish-review", "retire"}:
                raise ValueError("Unsupported action")
            profiles = a.get("profile_order", sorted(a["public_configs"])) if action in {"diagnostic", "final", "retire"} else [profile]
            if any(p not in a["public_configs"] for p in profiles):
                raise ValueError("Only assigned public profiles are available")
            request_id = uuid.uuid4().hex
            folder = self.root / "requests" / request_id
            folder.mkdir(parents=True)
            item = {"task": task, "arm": alias, "request_id": request_id, "action": action, "profiles": profiles,
                    "source": current, "readset": pins, 'active_configs': pins['active_configs'], "supersedes": list(supersedes), "revision_reason": revision_reason}
            if action.startswith("review-"):
                if not submission:
                    raise ValueError("Actual observation submission required")
                raw = absolute(str(submission))
                self.public_path(raw)
                data = raw.read_bytes()
                destination = folder / "original-submission.json"
                with destination.open("xb") as stream:
                    stream.write(data)
                destination.chmod(0o444)
                item["submission"] = {"path": str(destination), "sha256": sha(destination), "original_path": str(raw)}
            if supersedes and (action != "review-native" or not revision_reason):
                raise ValueError("Explicit native-review correction and reason required")
            save(folder / "request.json", item)
            return self.append("request_enqueued", **item)

    def public_path(self, path):
        for t in self.manifest["tasks"]:
            for a in t["arms"].values():
                if any(intersects(path, absolute(p)) or intersects(path.resolve(), absolute(p)) for p in a["hidden_configs"].values()):
                    raise ValueError("Hidden path cannot be opened before cohort authorization")

    def outcomes(self, task, alias, profile, action=None):
        out = []
        for e in self.history(task, alias, "request_finished"):
            request = load(self.root / "requests" / e["request_id"] / "request.json")
            if action and request["action"] != action:
                continue
            if sha(e["result_path"]) != e["result_sha256"]:
                raise ValueError("Append-only request result changed")
            value = load(e["result_path"])
            out.extend(o for o in value["outcomes"] if o["profile"] == profile)
        return out

    def latest(self, task, alias, profile, field, final_only=False):
        for o in reversed(self.outcomes(task, alias, profile)):
            if final_only and o["action"] != "final":
                continue
            value = o.get(field)
            if value:
                if sha(value["path"]) != value["sha256"]:
                    raise ValueError("Generated original receipt changed")
                return value
        raise ValueError("Required program-generated receipt is not available: " + field)

    def feedback_ready(self, task, alias):
        with lock(self.root / "state.lock"):
            self.expire()
            if not guard_live(self.root):
                raise ValueError("A live deadline guard is required before source repair; use the CLI feedback-ready command")
            anchor = self.one(task, alias, "repair_started")
            if not anchor or self.one(task, alias, "repair_unlocked") or self.one(task, alias, "source_locked") or self.pending(task, alias):
                raise ValueError("D0 is pending, repair already unlocked, or source already sealed")
            if not self.d0_complete(task, alias):
                raise ValueError('Complete terminal first-D0 result and intact initial integrity proof required')
            first = next(e for e in self.history(task, alias, 'request_enqueued') if e['action'] == 'diagnostic')
            self.check_request_integrity(first)
            a = self.arm(task, alias)
            self.assert_source(task, alias)
            original_modes = load(self.folder(task, alias) / "initial-modes.json")
            for p, mode in original_modes.items():
                Path(p).chmod(mode)
            return self.append("repair_unlocked", task=task, arm=alias, anchor_sequence=anchor["sequence"],
                               deadline_clock=anchor["deadline_clock"], deadline_at_unix=anchor["deadline_at_unix"],
                               scope="Acknowledgement only; original image/source review time is inside the automatic D0 repair window")

    def d0_complete(self, task, alias):
        diagnostics = [e for e in self.history(task, alias, 'request_enqueued') if e['action'] == 'diagnostic']
        if not diagnostics:
            return False
        first = diagnostics[0]
        finished = [e for e in self.history(task, alias, 'request_finished') if e['request_id'] == first['request_id']]
        if len(finished) != 1 or any(e['request_id'] == first['request_id'] for e in self.history(kind='request_interrupted')):
            return False
        end = finished[0]
        if not Path(end['result_path']).is_file() or sha(end['result_path']) != end['result_sha256']:
            return False
        result = load(end['result_path']); rows = result.get('outcomes', [])
        if any(result.get(k) != first[k] for k in ['task', 'arm', 'request_id']):
            return False
        expected = set(self.arm(task, alias)['public_configs'])
        if set(first['profiles']) != expected or len(first['profiles']) != len(expected) or len(rows) != len(expected) or {o.get('profile') for o in rows} != expected:
            return False
        if first['source'] != load(self.folder(task, alias) / 'initial/source.json'):
            return False
        for row in rows:
            path = self.root / 'requests' / first['request_id'] / row['profile'] / 'outcome.json'
            integrity = row.get('integrity', {})
            if not path.is_file() or load(path) != row or row.get('interrupted') or integrity.get('passed') is not True:
                return False
            if integrity.get('source_sha256') != first['source']['content_sha256'] or integrity.get('readset_sha256') != digest(first['readset']):
                return False
        return True

    def check_request_integrity(self, request):
        if request['action'] == 'diagnostic':
            self.verify_initial_cohort()
        pins = self.verify_pins(request['task'], request['arm'])
        if pins != request['readset'] or pins['active_configs'] != request['active_configs']:
            raise ValueError('Source/config/tool/readset integrity changed for this ticket')
        if self.assert_source(request['task'], request['arm']) != request['source']:
            raise ValueError('Source changed while queued or during request')
        return {'passed': True, 'source_sha256': request['source']['content_sha256'], 'readset_sha256': digest(pins)}

    def lock_source(self, task, alias):
        with lock(self.root / "state.lock"):
            self.expire()
            if not self.outcomes(task, alias, next(iter(self.arm(task, alias)["public_configs"])), "diagnostic"):
                raise ValueError("D0 outcome required before early source seal")
            return self.freeze(task, alias, "irrevocable_early_seal")

    def build_command(self, request, profile, record):
        task, alias = request["task"], request["arm"]
        a = self.arm(task, alias)
        tool = self.manifest["tools"][a["tool"]]
        config = request['active_configs'][profile]['path']
        action = request["action"]
        record = Path(record)
        service_output = record / "service"
        argv = [sys.executable, "-B", str(Path(tool["skill_root"]) / "scripts/ui_loop.py")]
        capture = None
        if action in {"diagnostic", "final"}:
            argv += ["native", "--config", config, "--output", str(service_output)]
            if action == "final":
                argv.append("--final")
            if tool["api"] == "baseline-explicit-prior":
                candidates = [o for o in self.outcomes(task, alias, profile) if o.get("capture")]
                if candidates:
                    capture = self.latest(task, alias, profile, "capture")
                if capture:
                    argv += ["--previous", capture["path"], "--previous-sha256", capture["sha256"]]
                cycles = [o["cycle"] for o in self.outcomes(task, alias, profile) if o.get("cycle")]
                if cycles:
                    save(record / "history.json", cycles)
                    argv += ["--history", str(record / "history.json")]
        elif action == "review-native":
            capture = self.latest(task, alias, profile, "capture")
            store = load(config).get("review_store")
            if not store:
                raise ValueError("Frozen public review_store is required")
            service_output = Path(store) / ("study-" + request["request_id"])
            argv += ["bind-native-review", "--config", config, "--capture-result", capture["path"],
                     "--capture-sha256", capture["sha256"], "--submission", request["submission"]["path"],
                     "--submission-sha256", request["submission"]["sha256"], "--output", str(service_output)]
            for previous in request["supersedes"]:
                argv += ["--supersedes-sha256", previous]
            if request["revision_reason"]:
                argv += ["--revision-reason", request["revision_reason"]]
        elif action == "review-source":
            service_output.mkdir()
            argv += ["bind-source-review", "--config", config, "--submission", request["submission"]["path"],
                     "--output", str(service_output / "source-review-ref.json")]
        elif action == "finish-review":
            cycle = self.latest(task, alias, profile, "cycle", final_only=True)
            argv += ["finish-native-review", "--config", config, "--cycle", cycle["path"],
                     "--cycle-sha256", cycle["sha256"], "--output", str(service_output)]
        elif action == "retire":
            argv += ["cleanup-native-resources", "--config", config, "--output", str(service_output)]
        return argv, service_output, capture

    def serve(self, executor=None):
        """Exactly one FIFO ticket. No retries; executor injection is HOST/SIM only."""
        with lock(self.root / "native-queue.lock"):
            with lock(self.root / "state.lock"):
                self.expire()
                pending = self.pending()
                if not pending:
                    return {"status": "queue_empty"}
                request = pending[0]
                if any(e.get("request_id") == request["request_id"] for e in self.history(kind="request_started")):
                    raise ValueError("Interrupted/in-flight ticket retained; do not retry invisibly")
                start = self.append("request_started", task=request["task"], arm=request["arm"], request_id=request["request_id"],
                                    queue_wait_seconds=time.clock_gettime(time.CLOCK_MONOTONIC) - request["at_clock"])
            outcomes = []
            for profile in request["profiles"]:
                folder = self.root / "requests" / request["request_id"] / profile
                folder.mkdir()
                at = time.time()
                clock = time.clock_gettime(time.CLOCK_MONOTONIC)
                outcome = {"profile": profile, "action": request["action"], "started_at_unix": at,
                           "envelope_record": str(folder / ("envelope-" + request["request_id"] + "-" + profile))}
                preflight = False
                interrupted = None
                try:
                    with lock(self.root / "state.lock"):
                        self.expire()
                        if request["action"] == "diagnostic":
                            self.verify_initial_cohort()
                        if self.verify_pins(request["task"], request["arm"])['active_configs'] != request['active_configs']:
                            raise ValueError('Active config changed while queued; ticket remains a failure')
                        if self.assert_source(request["task"], request["arm"]) != request["source"]:
                            raise ValueError("Source changed while queued; ticket failed and remains charged")
                        self.check_request_integrity(request)
                        preflight = True
                    self.profile_admission(request['task'], request['arm'], profile, request['active_configs'][profile]['path'], folder / 'profile-admission.json')
                    if self.verify_pins(request['task'], request['arm'])['active_configs'] != request['active_configs'] or self.assert_source(request['task'], request['arm']) != request['source']:
                        raise ValueError('Exact config/source changed during pure public profile admission')
                    argv, output, capture = self.build_command(request, profile, folder)
                    save(folder / "command.json", {"argv": argv, "config_sha256": sha(request['active_configs'][profile]['path']),
                                                 "source": request["source"], "readset": request["readset"], "prior_capture": capture})
                    outcome.update(service_output=str(output), capture=capture)
                    outcome["exit_code"] = (executor or self.execute)(request, profile, argv, folder)
                    envelope_result = Path(outcome['envelope_record']) / 'result.json'
                    external = load(envelope_result) if envelope_result.is_file() else {}
                    if outcome['exit_code'] < 0 or (external.get('error') or {}).get('type') in {'KeyboardInterrupt', 'SystemExit', 'InterruptedError'}:
                        raise InterruptedError('Native supervisor interrupted; ticket has no complete terminal bundle')
                    if external.get('source_unchanged') is False:
                        outcome['observed_integrity_violation'] = 'Common envelope reported source drift'
                    self.verify_pins(request["task"], request["arm"])
                    if self.assert_source(request["task"], request["arm"]) != request["source"]:
                        raise ValueError("Production source changed during request")
                    for field, filename in [("cycle", "cycle.json"), ("completion", "completion.json"), ("bound_review", "review-result.json")]:
                        p = output / filename
                        if p.is_file():
                            outcome[field] = {"path": str(p), "sha256": sha(p)}
                    if outcome.get("cycle"):
                        cycle = load(outcome["cycle"]["path"])
                        outcome["service_status"] = cycle.get("status")
                        outcome["new_ui_acquisition"] = cycle.get("native_executed")
                        outcome["capture_reused"] = cycle.get("capture_reused", False)
                        if cycle.get("capture_result"):
                            cp = Path(cycle["capture_result"])
                            if not cp.is_relative_to(self.root / "requests") or sha(cp) != cycle["capture_sha256"]:
                                raise ValueError("Only original program-generated capture receipts are allowed")
                            outcome["capture"] = {"path": str(cp), "sha256": cycle["capture_sha256"]}
                            if cycle.get("native_executed") is True:
                                receipt = load(cp)
                                drift = [k for k in ['source_unchanged', 'inputs_unchanged', 'tool_sources_unchanged'] if receipt.get(k) is False]
                                if drift:
                                    outcome['observed_integrity_violation'] = 'Original capture reported integrity drift: ' + ','.join(drift)
                                execution = cp.parent / "execution.json"
                                observation = cp.parent / "native/observation.json"
                                native_log = cp.parent / "native.log"
                                if not execution.is_file() or not native_log.is_file() or receipt.get("execution_sha256") != load(execution).get("execution_sha256"):
                                    raise ValueError("New-UI acquisition flag lacks original execution identity")
                                outcome["acquisition_evidence"] = {"capture_receipt": outcome["capture"], "execution": {"path": str(execution), "sha256": sha(execution)},
                                                                   "native_log": {"path": str(native_log), "sha256": sha(native_log)},
                                                                   "observation": {"path": str(observation), "sha256": sha(observation)} if observation.is_file() else None,
                                                                   "scope": "Frozen capture execution identity; absent/failed observation remains a failure or unknown, never acceptance"}
                                outcome["native_collection_success"] = receipt.get("native_exit_code") == 0 and observation.is_file() and not receipt.get("evidence_error")
                                if "nativeFinishedAtUnix" in receipt and "startedAtUnix" in receipt:
                                    outcome["native_observer_command_wall_seconds"] = receipt["nativeFinishedAtUnix"] - receipt["startedAtUnix"]
                    if outcome.get("completion"):
                        outcome["service_status"] = load(outcome["completion"]["path"]).get("status")
                    if request.get("submission"):
                        outcome["submission"] = request["submission"]
                    # Original outputs are never edited. Other requests may append
                    # separate registry entries, never write inside this packet.
                    if output.exists():
                        inventory = {str(p): sha(p) for p in sorted(output.rglob("*")) if p.is_file()}
                        save(folder / "original-inventory.json", inventory)
                        protect([str(output)])
                        outcome["inventory"] = {"path": str(folder / "original-inventory.json"), "sha256": sha(folder / "original-inventory.json")}
                except BaseException as error:
                    if isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit, InterruptedError)):
                        interrupted = error
                        outcome['interrupted'] = True
                    outcome["error"] = {"type": type(error).__name__, "message": str(error)}
                    save(folder / "failure.json", {"error": outcome["error"], "traceback": traceback.format_exc()})
                    # Partial original outputs and failures remain immutable too.
                    if outcome.get("service_output") and Path(outcome["service_output"]).exists() and not outcome.get("inventory"):
                        partial = Path(outcome["service_output"])
                        save(folder / "original-inventory.json", {str(p): sha(p) for p in sorted(partial.rglob("*")) if p.is_file()})
                        protect([str(partial)])
                        outcome["inventory"] = {"path": str(folder / "original-inventory.json"), "sha256": sha(folder / "original-inventory.json")}
                try:
                    # This check also runs after a legitimate SDK/collector/guard
                    # failure: failed observations may permit repair, drift may not.
                    outcome['integrity'] = self.check_request_integrity(request)
                    if not preflight or outcome.get('observed_integrity_violation'):
                        raise ValueError(outcome.get('observed_integrity_violation', 'Initial preflight integrity was not established'))
                except Exception as error:
                    outcome['integrity'] = {'passed': False, 'error': {'type': type(error).__name__, 'message': str(error)}}
                outcome.update(finished_at_unix=time.time(), wall_seconds=time.clock_gettime(time.CLOCK_MONOTONIC) - clock)
                outcome["accepted"] = outcome.get("exit_code") == 0 and not outcome.get("error") and outcome.get("service_status") == "accepted" and outcome['integrity']['passed']
                outcome.setdefault("new_ui_acquisition", None)  # failure/utility is never a false zero
                save(folder / "outcome.json", outcome)
                outcomes.append(outcome)
                if interrupted is not None:
                    with lock(self.root / 'state.lock'):
                        self.append('request_interrupted', task=request['task'], arm=request['arm'], request_id=request['request_id'], profile=profile,
                                    outcome=domain.reference(folder / 'outcome.json'), scope='Partial artifacts retained; no complete result, no source unlock, no automatic retry')
                    raise interrupted
            ready_clock = time.clock_gettime(time.CLOCK_MONOTONIC)
            result = {"task": request["task"], "arm": request["arm"], "request_id": request["request_id"], "outcomes": outcomes,
                      "queue_wait_seconds": start["queue_wait_seconds"], "finished_at_unix": time.time(),
                      "finished_at_clock": ready_clock,
                      "service_wall_seconds": time.clock_gettime(time.CLOCK_MONOTONIC) - start["at_clock"],
                      "native_execution_is_not_delivery_acceptance": True}
            result_path = self.root / "requests" / request["request_id"] / "result.json"
            save(result_path, result)
            anchored = False
            with lock(self.root / "state.lock"):
                self.append("request_finished", task=request["task"], arm=request["arm"], request_id=request["request_id"],
                            result_path=str(result_path), result_sha256=sha(result_path))
                if request["action"] == "diagnostic" and not self.one(request["task"], request["arm"], "repair_started") and self.d0_complete(request["task"], request["arm"]):
                    self.append("repair_started", task=request["task"], arm=request["arm"],
                                deadline_clock=ready_clock + LIMIT, deadline_at_unix=result["finished_at_unix"] + LIMIT,
                                repair_budget_seconds=LIMIT, d0_request_id=request["request_id"],
                                scope="Automatic FIRST terminal D0 bundle readiness, including honest failures; native success is not repair admission or delivery credit")
                    anchored = True
                    self.expire()
            if anchored:
                # The deadline is durable BEFORE guard startup. A startup failure
                # cannot delay/reset it; source stays read-only until a live guard.
                start_guard(self)
            return result

    def execute(self, request, profile, argv, folder):
        """The only forwarding boundary; never called by HOST/SIM verification."""
        a = self.arm(request["task"], request["arm"])
        spec = self.manifest["envelope"]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        command = [sys.executable, "-B", spec["meter_path"], "--spec", spec["meter_spec_path"], "--output", str(folder / "meter.jsonl"), "--",
                   sys.executable, "-B", spec["path"], "--config", request['active_configs'][profile]['path'], "--skill", self.manifest["tools"][a["tool"]]["skill_root"],
                   "--record", str(folder / ("envelope-" + request["request_id"] + "-" + profile)), "--timeout", "1200", "--", *argv]
        save(folder / "supervised-command.json", {"argv": command})
        journals = [Path(r) / "events.jsonl" for r in a["resource_roots"]]
        offsets = {str(p): p.stat().st_size if p.exists() else 0 for p in journals}
        with (folder / "supervisor.log").open("x") as stream:
            code = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT).returncode
        observed = []
        prefixes = []
        for p in journals:
            raw = p.read_bytes() if p.exists() else b""
            prefixes.append({"path": str(p), "start_byte": offsets[str(p)], "end_byte": len(raw), "prefix_sha256": hashlib.sha256(raw).hexdigest()})
            for row in raw[offsets[str(p)]:].splitlines():
                item = json.loads(row)
                if item.get("kind") in {"simctl_command", "process_started"}:
                    observed.append(item)
        save(folder / "sdk-observation.json", {"journal_prefixes": prefixes, "observed_command_records": observed,
                                               "scope": "EXPLICIT PARTIAL: owned resource journals only; SDK identity queries and internal descendants are unobserved. All execute inside enclosing request wall. Empty observed records do not mean zero SDK work."})
        return code

    def verify_originals(self, task, alias):
        for o in [o for p in self.arm(task, alias)["public_configs"] for o in self.outcomes(task, alias, p)]:
            if o.get("inventory"):
                inv = o["inventory"]
                if sha(inv["path"]) != inv["sha256"] or any(sha(p) != wanted for p, wanted in load(inv["path"]).items()):
                    raise ValueError("Immutable original service packet changed")

    def retirement(self, task, alias, profile):
        candidates = self.outcomes(task, alias, profile)
        for o in reversed(candidates):
            if o["action"] not in {"final", "retire"} or not o.get("service_output"):
                continue
            paths = [Path(o["service_output"]) / "resources.json"]
            # The common supervisor's explicit frozen cleanup API handles errors.
            p = Path(o["envelope_record"]) / "error-recovery" / "resources.json"
            paths.append(p)
            for path in paths:
                if path.is_file():
                    value = load(path)
                    if not value.get("cleanup_errors") and not value.get("remaining_devices") and not value.get("remaining_directories"):
                        if all(k in value for k in ["cleanup_errors", "remaining_devices", "remaining_directories"]):
                            return {"path": str(path), "sha256": sha(path)}
            break
        raise ValueError("Positive-owned retirement proof missing; enqueue retire, retain failure")

    def seal_self(self, task, alias, claim):
        with lock(self.root / "state.lock"):
            self.expire()
            if self.one(task, alias, "self_sealed") or self.pending(task, alias) or not self.one(task, alias, "source_locked"):
                raise ValueError("Source must be irrevocably locked and public queue completed before self-claim")
            self.verify_pins(task, alias)
            current = self.assert_source(task, alias)
            self.verify_originals(task, alias)
            final = {}
            retirement = {}
            for profile in self.arm(task, alias)["public_configs"]:
                values = self.outcomes(task, alias, profile, "final")
                if not values:
                    raise ValueError("Final public service outcome required for every profile")
                last = values[-1]
                later = self.outcomes(task, alias, profile, "finish-review")
                completion = [o for o in later if o["started_at_unix"] >= last["finished_at_unix"]]
                final[profile] = (completion[-1] if completion else last)
                retirement[profile] = self.retirement(task, alias, profile)
            claim_path = absolute(str(claim))
            self.public_path(claim_path)
            original_claim = load(claim_path)
            if not isinstance(original_claim, dict) or not isinstance(original_claim.get("statement"), str) or not original_claim["statement"].strip():
                raise ValueError("Final self-claim JSON needs a nonempty statement; no expected values are written")
            folder = self.folder(task, alias)
            save(folder / "self-claim.json", original_claim)
            admitted = next(e for e in self.history(task, alias, "request_enqueued") if e["action"] == "diagnostic")
            endpoint = self.append("self_sealed", task=task, arm=alias, source_sha256=current["content_sha256"],
                                   active_configs=self.active_configs(task, alias),
                                   claim_path=str(folder / "self-claim.json"), claim_sha256=sha(folder / "self-claim.json"),
                                   final_outcomes=final, retirement=retirement,
                                   public_service_accepted=all(o["accepted"] for o in final.values()) and self.one(task, alias, "source_locked")["source_deadline_compliant"],
                                   own_delivery_wall_seconds=time.clock_gettime(time.CLOCK_MONOTONIC) - admitted["at_clock"],
                                   delivery_scope="Own public service endpoint including review/check/retirement/self-claim; independent hidden quality is pending, F/U is not delivered")
            save(folder / "SELF-SEAL.json", endpoint)
            return endpoint

    def cohort(self):
        self.verify_initial_cohort()
        members = {}
        for t in self.manifest["tasks"]:
            for alias in t["arms"]:
                self.verify_pins(t["id"], alias)
                self.assert_source(t["id"], alias)
                self.verify_originals(t["id"], alias)
                seal = self.one(t["id"], alias, "self_sealed")
                if not seal or self.pending(t["id"], alias):
                    raise ValueError("All ten final sources, final service outcomes and self-claims must seal before any hidden access")
                if seal['active_configs'] != self.active_configs(t['id'], alias):
                    raise ValueError('Active public config changed after final self-seal')
                p = self.folder(t["id"], alias) / "SELF-SEAL.json"
                if load(p) != seal or sha(seal["claim_path"]) != seal["claim_sha256"]:
                    raise ValueError("Final self-claim/seal changed")
                members[t["id"] + "/" + alias] = {"path": str(p), "sha256": sha(p), "source_sha256": seal["source_sha256"]}
        return members

    def seal_cohort(self):
        with lock(self.root / "state.lock"):
            self.expire()
            members = self.cohort()
            value = self.append("cohort_sealed", members=members)
            save(self.root / "COHORT-SEAL.json", value)
            return value

    def authorize_hidden(self):
        with lock(self.root / "state.lock"):
            self.expire()
            members = self.cohort()  # no hidden path has been opened here
            seal = load(self.root / "COHORT-SEAL.json")
            if seal["members"] != members or seal != self.history(kind="cohort_sealed")[-1]:
                raise ValueError("Complete immutable cohort seal required")
            if self.history(kind="hidden_authorized"):
                raise ValueError("Hidden authorization is one-shot and append-only")
            authorization = self.append("hidden_authorized", cohort_sha256=sha(self.root / "COHORT-SEAL.json"),
                                        scope="Root may now open the declared hidden configurations and assemble anonymous evaluation packets. No grading or mapping reveal is performed.")
            # Authorization is durably recorded BEFORE the first hidden open.
            hidden = {}
            used_contexts = []
            public_contexts = [absolute(v) for t in self.manifest["tasks"] for a in t["arms"].values() for p in a["public_configs"].values()
                               for c in [load(p)] for v in [c.get("review_store"), c.get("source_review_store"), c.get("workflow", {}).get("root")] if v]
            for t in self.manifest["tasks"]:
                hidden[t["id"]] = {}
                for alias, a in t["arms"].items():
                    hidden[t["id"]][alias] = {}
                    for profile, p in a["hidden_configs"].items():
                        c = load(p)  # first hidden open is after durable all-ten authorization
                        if c["source_roots"] != a["source_roots"] or c["resources"]["root"] not in a["resource_roots"] or c["resources"].get("max_simulators", 1) != 1:
                            raise ValueError("Hidden evaluation must retain the final source identity and same arm's one-device resource bound")
                        roots = [absolute(v) for v in [c.get("review_store"), c.get("source_review_store"), c.get("workflow", {}).get("root")] if v]
                        if not c.get("review_store") or not c.get("source_review_store") or (self.manifest["tools"][a["tool"]]["api"] == "stateful-default" and not c.get("workflow", {}).get("root")):
                            raise ValueError("Hidden evaluation requires independently admitted fresh review/workflow roots")
                        if any(intersects(r, other) for r in roots for other in [*public_contexts, self.root, *map(absolute, a["source_roots"]), *map(absolute, a["resource_roots"])]):
                            raise ValueError("Public unresolved tasks/reviews cannot be cleared by swapping hidden context into public roots")
                        if any(r.exists() and any(r.iterdir()) for r in roots):
                            raise ValueError("Hidden evaluation context must be fresh and empty before authorization")
                        # Profiles may share a new workflow within one arm, as the
                        # frozen default supports per-platform contexts. Arms may not.
                        for r in roots:
                            if any(intersects(r, other) and owner != (t["id"], alias) for owner, other in used_contexts):
                                raise ValueError("Hidden contexts cannot overlap other arms")
                            used_contexts.append(((t["id"], alias), r))
                        hidden[t["id"]][alias][profile] = {"path": p, "sha256": sha(p), "context_roots": list(map(str, roots))}
            self.append("hidden_contexts_validated", authorization_sequence=authorization["sequence"],
                        scope="Fresh independent hidden contexts only; no public previous/history transport or public-task clearing is authorized")
            save(self.root / "HIDDEN-AUTHORIZATION.json", {"authorization": authorization, "hidden_configs": hidden,
                                                        "barrier_wait_seconds": {t["id"] + "/" + alias: authorization["at_unix"] - self.one(t["id"], alias, "self_sealed")["at_unix"]
                                                                                 for t in self.manifest["tasks"] for alias in t["arms"]}})
            return {"authorization_path": str(self.root / "HIDDEN-AUTHORIZATION.json"), "cohort_members": len(members)}


def initialize(manifest_path):
    m = load(manifest_path)
    if m.get("version") != 1 or len(m.get("tasks", [])) != 5:
        raise ValueError("Version1 manifest with exactly five sequential paired tasks required")
    name(m["study_id"])
    if len({t["id"] for t in m["tasks"]}) != 5:
        raise ValueError("Exactly five unique task identifiers required")
    root = absolute(m["run_root"])
    hidden = [absolute(p) for t in m["tasks"] for a in t["arms"].values() for p in a["hidden_configs"].values()]
    if any(intersects(root, h) for h in hidden):
        raise ValueError("Controller evidence root must be separate from hidden config paths")
    prerequisite_paths = [m["protocol"]["path"], m["speed_gate"]["path"], m["design_approval"]["path"],
                          *[m["envelope"][k] for k in ["path", "meter_path", "meter_spec_path"]],
                          *[t["skill_root"] for t in m["tools"].values()]]
    settings = m.get('source_domain_reviews')
    authority = None
    if settings:
        prerequisite_paths.append(settings['registry']['path'])
    if any(intersects(absolute(p), h) or intersects(absolute(p).resolve(), h) for p in prerequisite_paths for h in hidden):
        raise ValueError("Hidden paths cannot appear in the public prerequisite/tool readset")
    if settings:
        maximum = settings.get('max_requests_per_arm', 4)
        if type(maximum) is not int or not 1 <= maximum <= 8:
            raise ValueError('Predeclare 1..8 source-domain review requests per arm, identical for both APIs')
        _, identities = domain.registry(settings['registry'])
        authority = {'registry': settings['registry'], 'identities': identities}
    e = m["envelope"]
    for key, hashkey in [("path", "sha256"), ("meter_path", "meter_sha256"), ("meter_spec_path", "meter_spec_sha256")]:
        if sha(absolute(e[key])) != e[hashkey]:
            raise ValueError("Pinned common supervisor/spec mismatch")
    if absolute(e["meter_spec_path"]) != absolute(e["path"]).parent / "operators/whole-study-meter-spec-v2.json":
        raise ValueError("Existing envelope's frozen default meter spec must be used unchanged")
    p = m["protocol"]
    if sha(absolute(p["path"])) != p["sha256"]:
        raise ValueError("Pinned protocol mismatch")
    gate = m["speed_gate"]
    if absolute(gate["path"]) != absolute(p["path"]).parent / "qualification/benchmark-gate/RESULT.json" or sha(gate["path"]) != gate["sha256"]:
        raise ValueError("Pin the frozen benchmark-gate/RESULT.json prerequisite")
    verdict = load(gate["path"])
    if verdict.get("passed") is not True or verdict.get("business_tasks_may_start") is not True:
        raise ValueError("Passed measured gate must authorize business tasks before initial admission")
    approval = m["design_approval"]
    if sha(absolute(approval["path"])) != approval["sha256"]:
        raise ValueError("Pinned independent design approval seal required")
    protocol = load(p["path"])
    if protocol["business"]["tasks"] != 5 or protocol["business"]["repair_budget_minutes"] != 20 or protocol["business"]["diagnostic_requests_max"] != 2:
        raise ValueError("Predeclared five-task/20-minute/two-request protocol required")
    meter = load(e["meter_spec_path"])
    if meter["max_total_allocated_bytes"] > 32 * 2**30 or meter["min_free_bytes"] < 5 * 2**30:
        raise ValueError("Frozen common resource budget exceeds protocol")
    measured_paths = [absolute(p) for g in meter["groups"].values() for p in g["paths"]]
    journals = {str(absolute(p)) for g in meter["groups"].values() for p in g.get("resource_journals", [])}
    def covered(path):
        return any(path == p or path.is_relative_to(p) for p in measured_paths)
    all_sources = []
    all_resources = []
    prepared = []
    for tool in m["tools"].values():
        if tool["api"] not in {"stateful-default", "baseline-explicit-prior"}:
            raise ValueError("Only the two documented frozen APIs are supported")
        frozen_files(tool)
    if {tool["api"] for tool in m["tools"].values()} != {"stateful-default", "baseline-explicit-prior"}:
        raise ValueError("One frozen control and one frozen treatment API required")
    for t in m["tasks"]:
        name(t["id"])
        if len(t["arms"]) != 2:
            raise ValueError("Exactly two anonymous arms required per task")
        if len({bool(a.get('profile_admissions')) for a in t['arms'].values()}) != 1:
            raise ValueError('Pure profile admission must apply identically to both paired arms')
        pair = []
        apis = set()
        for alias, a in t["arms"].items():
            name(alias)
            apis.add(m["tools"][a["tool"]]["api"])
            workspace = absolute(a["workspace"])
            roots = [absolute(p) for p in a["source_roots"]]
            if not roots or any(not r.is_relative_to(workspace) for r in roots):
                raise ValueError("Private workspace must own all declared production source roots")
            for r in roots:
                if any(intersects(r, other) for other in all_sources) or intersects(r, root) or any(intersects(r, h) for h in hidden):
                    raise ValueError("Source roots must be disjoint from arms, output and hidden files")
                all_sources.append(r)
            if not covered(workspace) or not covered(root):
                raise ValueError("Predeclared common meter paths must cover private workspaces and study output")
            if set(a["public_configs"]) != set(a["hidden_configs"]) or not a["public_configs"]:
                raise ValueError("Public/hidden profile names must match; hidden values remain opaque")
            public_paths = {str(absolute(p)) for p in [*a["public_configs"].values(), *a["public_readset"]]}
            order = a.get("profile_order", sorted(a["public_configs"]))
            if len(order) != len(set(order)) or set(order) != set(a["public_configs"]):
                raise ValueError("Profile order must name every assigned public profile exactly once")
            if any(intersects(absolute(p), h) or intersects(absolute(p).resolve(), h) for p in public_paths for h in hidden):
                raise ValueError("Hidden file declared in public readset")
            public = {p: sha(p) for p in sorted(public_paths)}
            ios_roots = set()
            hooks = a.get('profile_admissions', {})
            if hooks and set(hooks) != set(a['public_configs']):
                raise ValueError('Configured pure profile admission must cover every assigned public profile')
            guarded_platforms = set()
            for profile, path in a["public_configs"].items():
                name(profile)
                config = load(path)
                if any(intersects(p, h) or intersects(p.resolve(), h) for p in path_strings(config) for h in hidden):
                    raise ValueError("Public config cannot route a service to hidden config paths")
                extra = []
                for key in ['coverage_domain_ref', 'coverage_provider_ref']:
                    if config.get(key):
                        extra.append(config[key]['path'])
                if config.get('coverage_domain_ref'):
                    if not settings:
                        raise ValueError('Source-domain configs require predeclared independent review transport')
                    domain.original(config)
                if hooks:
                    hook = hooks[profile]
                    extra += [hook['script'], hook['approval'], *hook.get('dependencies', [])]
                    if any(intersects(absolute(p), h) or intersects(absolute(p).resolve(), h) for p in [*extra, hook['root']] for h in hidden):
                        raise ValueError('Pure public profile admission cannot open hidden config paths')
                    if digest(load(hook['approval'])) != hook['approval_sha256']:
                        raise ValueError('Independent profile approval canonical pin differs')
                    guarded_platforms.add(domain.platform(config))
                for raw in extra:
                    p = str(absolute(raw)); public_paths.add(p); public[p] = sha(p)
                if config["source_roots"] != a["source_roots"]:
                    raise ValueError("Public config must declare the exact complete ordered source roots")
                resources = config["resources"]
                rr = absolute(resources["root"])
                managed_ios = config.get("native_options", {}).get("simulator") == "managed"
                if resources.get("max_simulators", 1) != 1 or not covered(rr) or (managed_ios and str(rr / "journal.json") not in journals):
                    raise ValueError("One owned simulator/root, allocation coverage and managed-iOS journal coverage required")
                if str(rr) not in a["resource_roots"]:
                    raise ValueError("Public config resource root must be explicitly owned by this arm")
                if managed_ios:
                    ios_roots.add(str(rr))
                for key in ["plan", "design_lock", "routes", "fixtures", "bridge", "policy", "environment"]:
                    if config.get(key) and str(absolute(config[key])) not in public_paths and not any(absolute(config[key]).is_relative_to(r) for r in roots):
                        raise ValueError("Public input missing from immutable readset: " + key)
                if m["tools"][a["tool"]]["api"] == "stateful-default" and not config.get("workflow", {}).get("root"):
                    raise ValueError("Treatment must use its frozen default workflow state machine")
                if m["tools"][a["tool"]]["api"] == "baseline-explicit-prior" and ("workflow" in config or "platform_source_roots" in config or "pool" in resources):
                    raise ValueError("Do not backport treatment state/pool/scoped-source config into baseline")
            if len(ios_roots) != 1:
                raise ValueError("Exactly one private iOS resource root per arm required")
            if hooks and guarded_platforms != {'ios', 'android'}:
                raise ValueError('Pure public admissions must include actual iOS AND Android plan namespaces')
            for raw in a["resource_roots"]:
                rr = absolute(raw)
                if any(intersects(rr, v) for v in [root, *all_sources, *all_resources, *hidden]) or not covered(rr):
                    raise ValueError("Private resource roots must be disjoint and metered; never shared SDK caches")
                all_resources.append(rr)
            snapshot = source(a["source_roots"])
            pair.append(snapshot["files"])
            prepared.append((t["id"], alias, a, public, snapshot, modes(a["source_roots"])))
        if len(apis) != 2 or pair[0] != pair[1]:
            raise ValueError("A/B initial source bytes must be exactly identical before any render")
    if any(intersects(s, r) for s in all_sources for r in all_resources):
        raise ValueError("Every source root must be disjoint from every private resource root")
    if authority and any(intersects(absolute(spec['path']), p) for spec in authority['identities'].values()
                         for p in [root, *all_sources, *all_resources, *[absolute(a['workspace']) for t in m['tasks'] for a in t['arms'].values()], *hidden]):
        raise ValueError('Independent reviewer roots must be separate from repair workspaces, evidence, resources and hidden configs')
    root.mkdir(parents=True, exist_ok=False)
    (root / "events").mkdir()
    save(root / "manifest.json", m)
    cohort = {}
    for task, alias, a, public, snapshot, original_modes in prepared:
        folder = root / "arms" / task / alias
        folder.mkdir(parents=True)
        capsule(folder / "initial", a["source_roots"], snapshot)
        cohort.setdefault(task, {})[alias] = {"path": str(folder / "initial" / "source.json"), "sha256": sha(folder / "initial" / "source.json")}
        save(folder / "initial-modes.json", original_modes)
        save(folder / "public-inputs.json", public)
        save(folder / "assignment.json", {"version": 1, "run_root": str(root), "task": task, "arm": alias,
                                          "workspace": a["workspace"], "source_roots": a["source_roots"],
                                          "public_configs": a["public_configs"], "skill_root": m["tools"][a["tool"]]["skill_root"]})
    save(root / "INITIAL-COHORT.json", cohort)
    if authority:
        save(root / 'DOMAIN-AUTHORITY.json', authority)
    save(root / "INIT.json", {"manifest_sha256": sha(root / "manifest.json"), "helper_sha256": sha(__file__),
                             'domain_transport_sha256': sha(HERE / 'source_domain.py'),
                             'domain_authority_sha256': sha(root / 'DOMAIN-AUTHORITY.json') if authority else None,
                             "initial_cohort_sha256": sha(root / "INITIAL-COHORT.json"), "at_unix": time.time(),
                             "scope": "All five pairs have exact nonempty initial byte identity; no native execution or hidden read"})
    study = Study(root)
    with lock(root / "state.lock"):
        study.append("initialized", cohort_members=10, no_native_execution=True, no_hidden_open=True)
    return {"run_root": str(root), "assignments_root": str(root / "arms"), "cohort_members": 10}


def assignment(path):
    path = absolute(str(path))
    value = load(path)
    study = Study(value["run_root"])
    expected = study.folder(value["task"], value["arm"]) / "assignment.json"
    if path != expected or load(expected) != value:
        raise ValueError("Use this arm's generated assignment file")
    return study, value["task"], value["arm"]


def guard_live(root):
    try:
        heartbeat = load(Path(root) / "guard-heartbeat.json")
        age = time.clock_gettime(time.CLOCK_MONOTONIC) - heartbeat["at_clock"]
        os.kill(heartbeat["pid"], 0)
        return 0 <= age < 1
    except (OSError, KeyError, ValueError):
        return False


def watch(root):
    study = Study(root)
    with lock(study.root / "deadline-guard.lock", blocking=False):
        signature = None
        timeline = []
        while True:
            with lock(study.root / "state.lock"):
                paths = sorted((study.root / "events").glob("*.json"))
                current = (len(paths), paths[-1].stat().st_mtime_ns if paths else None)
                if current != signature:
                    timeline = study.events()
                    signature = current
                study.expire(timeline)
                if any(e["kind"] == "cohort_sealed" for e in timeline):
                    return
                heartbeat = study.root / "guard-heartbeat.json"
                temporary = study.root / (".heartbeat-" + str(os.getpid()))
                temporary.write_text(json.dumps({"pid": os.getpid(), "at_clock": time.clock_gettime(time.CLOCK_MONOTONIC)}))
                temporary.replace(heartbeat)
            time.sleep(.1)


def start_guard(study):
    # Durable source deadline independent of repair-agent cooperation. Never a
    # native child; it only takes source snapshots/permissions under state.lock.
    if guard_live(study.root):
        return
    with (study.root / "guard.log").open("a") as stream:
        subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "_watch", "--run", str(study.root)],
                         stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if guard_live(study.root):
            return
        time.sleep(.02)
    raise ValueError("Deadline guard did not become ready; source stays locked")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("init"); q.add_argument("--manifest", type=Path, required=True)
    q = sub.add_parser("tool-identity"); q.add_argument("--skill-root", type=Path, required=True); q.add_argument("--api", choices=["stateful-default", "baseline-explicit-prior"], required=True)
    q = sub.add_parser("admit"); q.add_argument("--run", type=Path, required=True); q.add_argument("--task", required=True)
    q = sub.add_parser('admit-domain-review'); q.add_argument('--run', type=Path, required=True); q.add_argument('--request-id', required=True)
    for key in ['seal', 'provenance']:
        q.add_argument('--' + key, type=Path, required=True); q.add_argument('--' + key + '-sha256', required=True)
    for action in ["serve", "seal-cohort", "authorize-hidden", "status", "_watch"]:
        q = sub.add_parser(action); q.add_argument("--run", type=Path, required=True)
    for action in ["request", "feedback-ready", "lock-source", "seal-self", 'request-domain-review']:
        q = sub.add_parser(action); q.add_argument("--assignment", type=Path, required=True)
        if action == "request":
            q.add_argument("action", choices=["diagnostic", "final", "review-native", "review-source", "finish-review", "retire"])
            q.add_argument("--profile"); q.add_argument("--submission", type=Path)
            q.add_argument("--supersedes-sha256", action="append", default=[]); q.add_argument("--revision-reason")
        if action == "seal-self":
            q.add_argument("--claim", type=Path, required=True)
        if action == 'request-domain-review':
            q.add_argument('--profile', required=True)
    a = p.parse_args()
    if a.command == "tool-identity":
        root = a.skill_root.resolve()
        paths = [root / "SKILL.md", *(root / "scripts").glob("*.py"), *(root / "references").glob("*.md"),
                 *[p for p in (root / "assets").rglob("*") if p.is_file()]]
        result = {"skill_root": str(root), "api": a.api, "files": {str(p.relative_to(root)): sha(p) for p in sorted(paths)}}
    elif a.command == "init":
        result = initialize(a.manifest)
    elif a.command == "_watch":
        watch(a.run); return 0
    elif hasattr(a, "assignment"):
        study, task, alias = assignment(a.assignment)
        if a.command == "request":
            result = study.enqueue(task, alias, a.action, a.profile, a.submission, a.supersedes_sha256, a.revision_reason)
        elif a.command == "feedback-ready":
            # CLI always starts a guard BEFORE source write permissions return.
            start_guard(study)
            result = study.feedback_ready(task, alias)
        elif a.command == "lock-source":
            result = study.lock_source(task, alias)
        elif a.command == 'request-domain-review':
            result = study.request_domain_review(task, alias, a.profile)
        else:
            result = study.seal_self(task, alias, a.claim)
    else:
        study = Study(a.run)
        if a.command == "admit": result = study.admit(a.task)
        elif a.command == 'admit-domain-review': result = study.admit_domain_review(a.request_id, a.seal, a.seal_sha256, a.provenance, a.provenance_sha256)
        elif a.command == "serve": result = study.serve()
        elif a.command == "seal-cohort": result = study.seal_cohort()
        elif a.command == "authorize-hidden": result = study.authorize_hidden()
        else:
            result = {"pending_requests": [{"request_id": r["request_id"], "task": r["task"], "arm": r["arm"], "action": r["action"]} for r in study.pending()],
                      "final_self_seals": len(study.history(kind="self_sealed")), "cohort_sealed": bool(study.history(kind="cohort_sealed"))}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "rejected", "error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
