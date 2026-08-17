#!/usr/bin/env python3
"""Validate and stage the bounded Nutworks runtime package.

This validator proves source and temporary-stage closure only. Native hosts own
installation, placement, loading, and activation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


PLUGIN_NAME = "nutworks"
CATALOG_SOURCE = "./plugins/nutworks"
RUNTIME_ALLOWLIST = "runtime-files.json"
REQUIRED_RUNTIME_FILES = {
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "runtime-files.json",
    "skills/nuts/SKILL.md",
    "third_party/compound-engineering/LICENSE",
    "third_party/compound-engineering/provenance.json",
}
MIT_LICENSE = """MIT License

Copyright (c) 2026 Andrew Gomel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
RUNTIME_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])((?:references|scripts|assets|third_party)/[A-Za-z0-9_.\-/]+)"
)
PRIVATE_CONTENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private user path", re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\\\Users\\\\)")),
    ("private attachment path", re.compile(r"(?:/Library/Messages/Attachments|/var/folders/)")),
    (
        "absolute filesystem path",
        re.compile(r"(?<![A-Za-z0-9:])(?:/(?:etc|opt|private|tmp|usr|var|Volumes)/|~/|\$HOME/|\$\{HOME\}/)"),
    ),
    ("Protocol Workbench reference", re.compile(r"protocol-workbench", re.IGNORECASE)),
    ("field-report reference", re.compile(r"nuts-field-report", re.IGNORECASE)),
    ("Topsight reference", re.compile(r"\bTopsight\b", re.IGNORECASE)),
    ("recipient name", re.compile(r"\b(?:Matt|Matthew|Mr\.?\s+Pencil)\b", re.IGNORECASE)),
    (
        "raw conversation marker",
        re.compile(r"(?:<codex_delegation>|source_thread_id|Response annotations:|Message Type:)", re.IGNORECASE),
    ),
    ("personal NUTS skill reference", re.compile(r"(?:\bag:nuts\b|\$CODEX_HOME|\.codex/skills/)", re.IGNORECASE)),
    ("CE runtime invocation", re.compile(r"(?:compound-engineering:ce-|\$ce-)", re.IGNORECASE)),
    ("path traversal", re.compile(r"(?:^|[\s`'\"(])\.\.[/\\]", re.MULTILINE)),
    ("control character", re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")),
)
SECRET_CONTENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b")),
    ("OpenAI-style token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    (
        "assigned secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*"
            r"['\"]?[A-Za-z0-9_./+=-]{12,}"
        ),
    ),
)
SECRET_NAMES = {
    ".env",
    ".env.local",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "secrets.json",
}
DEVELOPMENT_PATH_PARTS = {
    ".nuts",
    "__pycache__",
    "fixtures",
    "run-evidence",
    "runs",
    "test",
    "tests",
}
GOVERNANCE_FILENAMES = {"AGENTS.md", "CLAUDE.md"}


class PackageValidationError(Exception):
    """Raised with every package validation failure found in one pass."""

    def __init__(self, errors: Iterable[str]):
        self.errors = sorted(set(errors))
        super().__init__("; ".join(self.errors))


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not require_regular_non_link(path, str(path), errors):
        return None
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_no_duplicate_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{path}: invalid JSON ({exc})")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path}: JSON root must be an object")
        return None
    return value


def safe_relative_path(raw: Any) -> str | None:
    if (
        not isinstance(raw, str)
        or not raw
        or "\\" in raw
        or ":" in raw
        or any(ord(character) < 32 for character in raw)
    ):
        return None
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        return None
    return candidate.as_posix()


def inspect_regular_tree(root: Path, label: str, errors: list[str]) -> list[str]:
    """Return regular files without following any directory entry links."""
    files: list[str] = []
    try:
        root_stat = root.lstat()
    except OSError as exc:
        errors.append(f"{label}: unavailable ({exc})")
        return files
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        errors.append(f"{label}: root must be a real directory")
        return files

    def walk(directory: Path) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            errors.append(f"{label}: cannot inspect {directory} ({exc})")
            return
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            try:
                entry_stat = entry.stat(follow_symlinks=False)
            except OSError as exc:
                errors.append(f"{label}: cannot inspect {relative} ({exc})")
                continue
            mode = entry_stat.st_mode
            if stat.S_ISLNK(mode):
                errors.append(f"{label}: link is forbidden: {relative}")
            elif stat.S_ISDIR(mode):
                walk(path)
            elif stat.S_ISREG(mode):
                files.append(relative)
            else:
                errors.append(f"{label}: special file is forbidden: {relative}")

    walk(root)
    return sorted(files)


def require_regular_non_link(path: Path, label: str, errors: list[str]) -> bool:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        errors.append(f"{label}: unavailable ({exc})")
        return False
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        errors.append(f"{label}: must be a regular non-link file")
        return False
    return True


def reject_linked_path_components(repo_root: Path, errors: list[str]) -> None:
    checked: set[Path] = set()
    for relative in (
        Path("plugins/nutworks"),
        Path(".agents/plugins/marketplace.json"),
        Path(".claude-plugin/marketplace.json"),
        Path("LICENSE"),
    ):
        current = repo_root
        for part in relative.parts:
            current = current / part
            if current in checked:
                continue
            checked.add(current)
            try:
                mode = current.lstat().st_mode
            except OSError:
                continue
            if stat.S_ISLNK(mode):
                errors.append(f"linked package/catalog path component is forbidden: {relative}")


def load_runtime_allowlist(plugin_root: Path, errors: list[str]) -> list[str]:
    payload = load_json(plugin_root / RUNTIME_ALLOWLIST, errors)
    if payload is None:
        return []
    if set(payload) != {"schema_version", "files"}:
        errors.append("runtime-files.json must contain only schema_version and files")
    if payload.get("schema_version") != 1:
        errors.append("runtime-files.json schema_version must be 1")
    raw_files = payload.get("files")
    if not isinstance(raw_files, list):
        errors.append("runtime-files.json files must be an array")
        return []
    paths: list[str] = []
    for raw_path in raw_files:
        normalized = safe_relative_path(raw_path)
        if normalized is None:
            errors.append(f"runtime-files.json has unsafe path: {raw_path!r}")
        else:
            paths.append(normalized)
            parts = {part.lower() for part in PurePosixPath(normalized).parts}
            if parts & DEVELOPMENT_PATH_PARTS:
                errors.append(f"development-only runtime path is forbidden: {normalized}")
            if PurePosixPath(normalized).name in GOVERNANCE_FILENAMES:
                errors.append(f"project governance file is forbidden in runtime payload: {normalized}")
    if len(paths) != len(set(paths)):
        errors.append("runtime-files.json contains duplicate paths")
    if paths != sorted(paths):
        errors.append("runtime-files.json paths must be sorted")
    missing_required = sorted(REQUIRED_RUNTIME_FILES - set(paths))
    if missing_required:
        errors.append(f"runtime allowlist omits required files: {missing_required}")
    return paths


def validate_catalogs_and_manifests(repo_root: Path, errors: list[str]) -> str | None:
    plugin_root = repo_root / "plugins" / PLUGIN_NAME
    paths = {
        "Codex manifest": plugin_root / ".codex-plugin" / "plugin.json",
        "Claude manifest": plugin_root / ".claude-plugin" / "plugin.json",
        "Codex catalog": repo_root / ".agents" / "plugins" / "marketplace.json",
        "Claude catalog": repo_root / ".claude-plugin" / "marketplace.json",
    }
    codex_manifest = load_json(paths["Codex manifest"], errors)
    claude_manifest = load_json(paths["Claude manifest"], errors)
    codex_catalog = load_json(paths["Codex catalog"], errors)
    claude_catalog = load_json(paths["Claude catalog"], errors)
    if None in (codex_manifest, claude_manifest, codex_catalog, claude_catalog):
        return None
    assert codex_manifest is not None
    assert claude_manifest is not None
    assert codex_catalog is not None
    assert claude_catalog is not None

    for field in ("name", "version", "description", "license"):
        if codex_manifest.get(field) != claude_manifest.get(field):
            errors.append(f"host manifests disagree on {field}")
    version = codex_manifest.get("version")
    if codex_manifest.get("name") != PLUGIN_NAME:
        errors.append(f"manifest name must be {PLUGIN_NAME}")
    if not isinstance(version, str) or SEMVER_RE.fullmatch(version) is None:
        errors.append("manifest version must be strict semver")
    if codex_manifest.get("license") != "MIT":
        errors.append("both manifests must use the MIT SPDX identifier")
    if codex_manifest.get("skills") != "./skills/":
        errors.append("Codex manifest skills path must be ./skills/")

    codex_plugins = codex_catalog.get("plugins")
    if not isinstance(codex_plugins, list) or len(codex_plugins) != 1:
        errors.append("Codex catalog must contain exactly one plugin")
    else:
        entry = codex_plugins[0]
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(entry, dict) or entry.get("name") != PLUGIN_NAME:
            errors.append("Codex catalog plugin name must be nutworks")
        if source != {"source": "local", "path": CATALOG_SOURCE}:
            errors.append("Codex catalog must use the exact relative local source ./plugins/nutworks")

    claude_plugins = claude_catalog.get("plugins")
    if not isinstance(claude_plugins, list) or len(claude_plugins) != 1:
        errors.append("Claude catalog must contain exactly one plugin")
    else:
        entry = claude_plugins[0]
        if not isinstance(entry, dict) or entry.get("name") != PLUGIN_NAME:
            errors.append("Claude catalog plugin name must be nutworks")
        if not isinstance(entry, dict) or entry.get("source") != CATALOG_SOURCE:
            errors.append("Claude catalog must use the exact relative source ./plugins/nutworks")
    metadata = claude_catalog.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("version") != version:
        errors.append("Claude catalog metadata version must match both manifests")
    return version if isinstance(version, str) else None


def validate_license_and_provenance(repo_root: Path, errors: list[str]) -> None:
    plugin_root = repo_root / "plugins" / PLUGIN_NAME
    repo_license_path = repo_root / "LICENSE"
    plugin_license_path = plugin_root / "LICENSE"
    if not all(
        (
            require_regular_non_link(repo_license_path, "repository license", errors),
            require_regular_non_link(plugin_license_path, "payload license", errors),
        )
    ):
        return
    try:
        repo_license = repo_license_path.read_text(encoding="utf-8")
        plugin_license = plugin_license_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"unable to read Nutworks licenses ({exc})")
        return
    if repo_license != MIT_LICENSE or plugin_license != MIT_LICENSE:
        errors.append("repository and payload Nutworks licenses must match the exact approved MIT text")
    third_party_license = plugin_root / "third_party" / "compound-engineering" / "LICENSE"
    notices = plugin_root / "THIRD_PARTY_NOTICES.md"
    provenance = plugin_root / "third_party" / "compound-engineering" / "provenance.json"
    third_party_safe = require_regular_non_link(third_party_license, "CE license", errors)
    notices_safe = require_regular_non_link(notices, "third-party notices", errors)
    if not (third_party_safe and notices_safe):
        load_json(provenance, errors)
        return
    try:
        third_party_text = third_party_license.read_text(encoding="utf-8")
        notices_text = notices.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"unable to read separate CE notice material ({exc})")
    else:
        if "Copyright (c) 2025 Every" not in third_party_text:
            errors.append("CE license must retain Every's copyright notice")
        if "Every" not in notices_text or "Compound Engineering" not in notices_text:
            errors.append("THIRD_PARTY_NOTICES.md must identify Every and Compound Engineering")
        if "Every" in repo_license or "Every" in plugin_license:
            errors.append("CE notice must remain separate from the Nutworks license")
    load_json(provenance, errors)


def validate_runtime_content(plugin_root: Path, files: list[str], errors: list[str]) -> None:
    allowed = set(files)
    for relative in files:
        path = plugin_root / relative
        if path.name.lower() in SECRET_NAMES or path.name.lower().startswith(".env."):
            errors.append(f"secret-like filename is forbidden: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"runtime file must be UTF-8 text: {relative}")
            continue
        except OSError:
            continue
        for label, pattern in PRIVATE_CONTENT_PATTERNS + SECRET_CONTENT_PATTERNS:
            if pattern.search(text):
                errors.append(f"{relative}: contains forbidden {label}")
        for target in referenced_paths(relative, text):
            resolved = resolve_runtime_reference(relative, target)
            if resolved is None:
                errors.append(f"{relative}: unsafe or absolute reference: {target}")
            elif resolved not in allowed and not any(
                candidate.startswith(resolved.rstrip("/") + "/") for candidate in allowed
            ):
                errors.append(f"{relative}: broken or undeclared reference: {target}")


def referenced_paths(relative: str, text: str) -> set[str]:
    targets: set[str] = set()
    if relative.endswith(".md"):
        for match in MARKDOWN_LINK_RE.finditer(text):
            raw = match.group(1).strip().split()[0].strip("<>")
            if not raw.startswith(("#", "https://", "http://", "mailto:")):
                targets.add(raw.split("#", 1)[0])
        targets.update(match.group(1) for match in RUNTIME_PATH_RE.finditer(text))
    if relative.endswith(".json"):
        try:
            payload = json.loads(text, object_pairs_hook=_no_duplicate_object)
        except (json.JSONDecodeError, ValueError):
            return targets
        collect_json_references(payload, targets)
    return targets


def collect_json_references(value: Any, targets: set[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"$ref", "destination", "license_path"} and isinstance(item, str) and not item.startswith(("#", "https://", "http://")):
                targets.add(item.split("#", 1)[0])
            else:
                collect_json_references(item, targets)
    elif isinstance(value, list):
        for item in value:
            collect_json_references(item, targets)


def resolve_runtime_reference(source_relative: str, target: str) -> str | None:
    if not target or "\\" in target:
        return None
    candidate = PurePosixPath(target)
    if candidate.is_absolute() or any(part in {"", ".."} for part in candidate.parts):
        return None
    source = PurePosixPath(source_relative)
    if target.startswith(("references/", "scripts/", "assets/")):
        parts = source.parts
        try:
            skill_index = parts.index("skills")
            skill_root = PurePosixPath(*parts[: skill_index + 2])
        except (ValueError, IndexError):
            resolved = source.parent / candidate
        else:
            resolved = skill_root / candidate
    elif target.startswith("third_party/"):
        resolved = candidate
    elif target.startswith("skills/"):
        resolved = candidate
    else:
        resolved = source.parent / candidate
    return resolved.as_posix()


def _copy_regular(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with source.open("rb") as input_file, destination.open("xb") as output_file:
        shutil.copyfileobj(input_file, output_file)
    destination.chmod(0o600)


def stage_package(repo_root: Path, files: list[str], stage_root: Path) -> None:
    stage_root.chmod(0o700)
    for catalog in (
        Path(".agents/plugins/marketplace.json"),
        Path(".claude-plugin/marketplace.json"),
    ):
        _copy_regular(repo_root / catalog, stage_root / catalog)
    for relative in files:
        _copy_regular(
            repo_root / "plugins" / PLUGIN_NAME / relative,
            stage_root / "plugins" / PLUGIN_NAME / relative,
        )


def validate_package(repo_root: Path, *, stage_parent: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    reject_linked_path_components(repo_root, errors)
    plugin_root = repo_root / "plugins" / PLUGIN_NAME
    runtime_files = inspect_regular_tree(plugin_root, "plugin source", errors)
    allowlist = load_runtime_allowlist(plugin_root, errors)
    if runtime_files != allowlist:
        undeclared = sorted(set(runtime_files) - set(allowlist))
        missing = sorted(set(allowlist) - set(runtime_files))
        if undeclared:
            errors.append(f"runtime files not declared by allowlist: {undeclared}")
        if missing:
            errors.append(f"allowlisted runtime files are missing: {missing}")
    version = validate_catalogs_and_manifests(repo_root, errors)
    validate_license_and_provenance(repo_root, errors)
    validate_runtime_content(plugin_root, allowlist, errors)
    if errors:
        raise PackageValidationError(errors)

    parent = stage_parent.resolve() if stage_parent is not None else None
    with tempfile.TemporaryDirectory(prefix="nutworks-package-stage-", dir=parent) as raw_stage:
        stage_root = Path(raw_stage)
        stage_package(repo_root, allowlist, stage_root)
        stage_errors: list[str] = []
        if stat.S_IMODE(stage_root.stat().st_mode) & 0o077:
            stage_errors.append("temporary marketplace stage must be owner-only")
        staged_files = inspect_regular_tree(stage_root / "plugins" / PLUGIN_NAME, "staged plugin", stage_errors)
        if staged_files != allowlist:
            stage_errors.append("staged runtime inventory differs from the source allowlist")
        staged_version = validate_catalogs_and_manifests(stage_root, stage_errors)
        validate_runtime_content(stage_root / "plugins" / PLUGIN_NAME, staged_files, stage_errors)
        if stage_errors:
            raise PackageValidationError(stage_errors)
        inventory = [
            {
                "path": path,
                "bytes": (stage_root / "plugins" / PLUGIN_NAME / path).stat().st_size,
            }
            for path in staged_files
        ]
        return {
            "schema_version": 1,
            "status": "passed",
            "claim": "source-and-stage-validation-only",
            "plugin": PLUGIN_NAME,
            "source_version": staged_version or version,
            "inventory": inventory,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Nutworks repository root",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        receipt = validate_package(args.repo_root)
    except PackageValidationError as exc:
        print(json.dumps({"schema_version": 1, "status": "failed", "errors": exc.errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
