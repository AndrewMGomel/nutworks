#!/usr/bin/env python3
"""Run OpenAI's plugin validator from a pinned maintainer environment.

This wrapper never installs dependencies or mutates a Codex profile. It reports
`unavailable` when the pinned dependency or official validator cannot be used.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


LOCK_PATTERN = re.compile(r"^PyYAML==([^\s]+)$", re.MULTILINE)


def receipt(status: str, **details: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "codex-official-static-validator",
        "status": status,
        **details,
    }


def find_validator(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit.expanduser()
    configured = os.environ.get("NUTWORKS_CODEX_PLUGIN_VALIDATOR")
    if configured:
        return Path(configured).expanduser()
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    candidate = codex_home / "skills" / ".system" / "plugin-creator" / "scripts" / "validate_plugin.py"
    return candidate if candidate.is_file() else None


def run_official_validator(
    repo_root: Path,
    *,
    validator_path: Path | None = None,
) -> tuple[dict[str, Any], int]:
    repo_root = repo_root.resolve()
    lock_path = repo_root / "requirements-dev.lock"
    try:
        lock_text = lock_path.read_text(encoding="utf-8")
    except OSError as exc:
        return receipt("unavailable", reason=f"cannot read requirements-dev.lock: {exc}"), 2
    match = LOCK_PATTERN.search(lock_text)
    if match is None:
        return receipt("unavailable", reason="requirements-dev.lock does not pin PyYAML"), 2
    required_pyyaml = match.group(1)
    try:
        installed_pyyaml = importlib.metadata.version("PyYAML")
    except importlib.metadata.PackageNotFoundError:
        return receipt(
            "unavailable",
            reason="pinned maintainer dependency PyYAML is not installed",
            required_pyyaml=required_pyyaml,
        ), 2
    if installed_pyyaml != required_pyyaml:
        return receipt(
            "unavailable",
            reason="installed PyYAML does not match requirements-dev.lock",
            required_pyyaml=required_pyyaml,
            installed_pyyaml=installed_pyyaml,
        ), 2

    validator = find_validator(validator_path)
    if validator is None:
        return receipt(
            "unavailable",
            reason=(
                "official Codex validator not found; set "
                "NUTWORKS_CODEX_PLUGIN_VALIDATOR or pass --validator"
            ),
            required_pyyaml=required_pyyaml,
        ), 2
    try:
        validator.lstat()
    except OSError as exc:
        return receipt("unavailable", reason=f"cannot inspect validator: {exc}"), 2
    if validator.is_symlink() or not validator.is_file():
        return receipt("unavailable", reason="validator must be a regular non-link file"), 2
    if validator.name != "validate_plugin.py":
        return receipt("unavailable", reason="validator filename must be validate_plugin.py"), 2
    plugin_root = repo_root / "plugins" / "nutworks"
    try:
        completed = subprocess.run(
            [sys.executable, str(validator), str(plugin_root)],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
            env=dict(os.environ),
        )
    except OSError as exc:
        return receipt("unavailable", reason=f"cannot run validator: {exc}"), 2
    status = "passed" if completed.returncode == 0 else "failed"
    result = receipt(
        status,
        required_pyyaml=required_pyyaml,
        installed_pyyaml=installed_pyyaml,
        exit_code=completed.returncode,
        stdout=completed.stdout[-8000:],
        stderr=completed.stderr[-8000:],
    )
    return result, 0 if status == "passed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--validator", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result, exit_code = run_official_validator(args.repo_root, validator_path=args.validator)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
