#!/usr/bin/env python3
"""Adapt the sealed design guard to the controller's five-argument hook.

Profile identity comes from the actual platform, lock and exact plan path. The
caller cannot select a different profile or request the pure-placeholder mode.
No original design, expectation, guard or frozen native tool is modified.
"""
import hashlib
import importlib.util
from pathlib import Path


def verify(root, approval, approval_sha, platform, config):
    root = Path(root).resolve()
    actual_plan = Path(config['plan']).resolve()
    matches = [identity for identity, profile in approval['profiles'].items()
               if profile['intended_platform'] == platform
               and profile['design_sha256'] == config.get('design_sha256')
               and (root / profile['paths']['plan']).resolve() == actual_plan]
    if len(matches) != 1:
        raise ValueError('Actual platform/lock/plan must identify one sealed profile')
    guard = root / 'scripts/admit_profile.py'
    module_name = 'sealed_design_profile_' + hashlib.sha256(guard.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(module_name, guard)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify(root, approval, approval_sha, platform, matches[0], config, runtime=True)
    if result.get('status') != 'admitted_profile' or result.get('actual_platform') != platform or result.get('pure_only') is not False:
        raise ValueError('Sealed guard did not admit this actual runtime representation')
    return dict(result, platform=platform, controller_adapter='five_argument_actual_config_v1',
                source_approved=False, native_executed=False)
