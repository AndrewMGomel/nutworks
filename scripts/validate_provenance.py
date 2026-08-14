#!/usr/bin/env python3
"""Validate Nutworks's static Compound Engineering provenance mapping."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from typing import Any


PLUGIN_REL = "plugins/nutworks"
PROVENANCE_REL = "third_party/compound-engineering/provenance.json"
CE_LICENSE_REL = "third_party/compound-engineering/LICENSE"
NOTICE_REL = "THIRD_PARTY_NOTICES.md"
NUTWORKS_LICENSE_REL = "LICENSE"

CE_REPOSITORY = "https://github.com/EveryInc/compound-engineering-plugin"
CE_VERSION = "3.20.0"
CE_COMMIT = "5c7cb347d0686663743b87cd7227246ba24f7fa7"
CE_LICENSE_SHA256 = "61d89de7646effdaba2d0a4ab7bd0eba60b4094b83efe5bc73c7940e43e93fc6"
NUTWORKS_LICENSE_SHA256 = "f425cdf9d14f01d7ec1b246e390b2ae9f0f1d6179c23b272d145586a9546e5f5"
GROUNDING_SOURCE = {
    "path": "skills/ce-compound/references/grounding-validation.md",
    "sha256": "0295ee3be2f19b22b95568cbf17b846d20ff75e358331077fd477da95aa5ad19",
}

EXPECTED_SOURCES = {
    "skills/ce-plan/references/plan-sections.md":
        "082219787c4df38138cae1da57dc763910a268dc59169065c9fa0242a49e0c42",
    "skills/ce-plan/references/settled-decisions.md":
        "e4fa8cecdccdb5d8a141b720c26a733fb143292a81671c21b144fac2584d5b22",
    "skills/ce-doc-review/references/personas/coherence-reviewer.md":
        "e84c8fa209e0b3f6126cb10c21c7e12fffb39952697e38fa14071303e2e14355",
    "skills/ce-doc-review/references/personas/feasibility-reviewer.md":
        "1e186dabf2b6cac325dbfe8466744f8f1b63cda0c15f69fa160e92c97810de36",
    "skills/ce-code-review/references/personas/correctness-reviewer.md":
        "36a5e5378753345688741a20faa3c19878a6a64e2b4d41c2c06695c15d6eaa81",
    "skills/ce-code-review/references/personas/testing-reviewer.md":
        "8b6e7fad8b4249bfdde96e89f6139b53ca08151407830bd0b2a8d3ed3c79b223",
    "skills/ce-doc-review/references/findings-schema.json":
        "d20a74985ed53841a717472783f44ded059aac0f4ceb78cedcf53437ed2fbfb7",
    "skills/ce-code-review/references/findings-schema.json":
        "14f484b5e32cfc51a432ffee4a89b38ee56fb4619d2604a6db3ed71567f43e76",
}

EXPECTED_MATRIX = {
    "skills/nuts/references/plan.md": (
        "skills/ce-plan/references/plan-sections.md",
        "skills/ce-plan/references/settled-decisions.md",
    ),
    "skills/nuts/references/reviewers/coherence.md": (
        "skills/ce-doc-review/references/personas/coherence-reviewer.md",
    ),
    "skills/nuts/references/reviewers/feasibility.md": (
        "skills/ce-doc-review/references/personas/feasibility-reviewer.md",
    ),
    "skills/nuts/references/reviewers/correctness.md": (
        "skills/ce-code-review/references/personas/correctness-reviewer.md",
    ),
    "skills/nuts/references/reviewers/testing.md": (
        "skills/ce-code-review/references/personas/testing-reviewer.md",
    ),
    "skills/nuts/references/schemas/finding.schema.json": (
        "skills/ce-doc-review/references/findings-schema.json",
        "skills/ce-code-review/references/findings-schema.json",
    ),
}

EXPECTED_INFORMED = "skills/nuts/references/compound.md"
EXPECTED_ORIGINAL = {
    "skills/nuts/references/reviewers/change-risk.md",
    "skills/nuts/references/reviewers/simplicity.md",
}
ALLOWED_REASONS = {
    "nuts_authority",
    "host_neutrality",
    "safety_boundary",
    "shared_evidence_contract",
}


class ValidationError(Exception):
    """Raised for one bounded provenance validation failure."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{label} must be a non-empty relative path")
    if "\\" in value or any(ord(char) < 32 for char in value):
        raise ValidationError(f"{label} contains a control or backslash")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise ValidationError(f"{label} must not be absolute or traverse")
    if pure.as_posix() != value:
        raise ValidationError(f"{label} is not canonical POSIX relative form")
    return value


def _read_regular(base: Path, relative: str, label: str) -> bytes:
    relative = _safe_relative(relative, label)
    current = base
    root_stat = os.lstat(base)
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise ValidationError(f"{label} base must be a real directory")

    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        item_stat = os.lstat(current)
        if stat.S_ISLNK(item_stat.st_mode):
            raise ValidationError(f"{label} must not traverse a symbolic link")
        if index < len(parts) - 1 and not stat.S_ISDIR(item_stat.st_mode):
            raise ValidationError(f"{label} parent is not a directory")

    before = os.lstat(current)
    if not stat.S_ISREG(before.st_mode):
        raise ValidationError(f"{label} must be a regular file")
    if before.st_nlink != 1:
        raise ValidationError(f"{label} must have exactly one hard link")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(current, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValidationError(f"{label} changed while being opened")
        chunks = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    return b"".join(chunks)


def _load_json(data: bytes, label: str) -> Any:
    try:
        text = data.decode("utf-8")
        return json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"{label} is not valid unique-key UTF-8 JSON: {error}") from error


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _records_by(records: Any, key: str, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        raise ValidationError(f"{label} must be an array")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get(key), str):
            raise ValidationError(f"{label} contains an invalid record")
        identity = record[key]
        if identity in indexed:
            raise ValidationError(f"{label} contains duplicate {key}: {identity}")
        indexed[identity] = record
    return indexed


def _validate_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValidationError(f"{label} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValidationError(f"{label} must be a SHA-256 hex digest") from error
    if value.lower() != value:
        raise ValidationError(f"{label} must use lowercase hex")
    return value


def _validate_destination(plugin_root: Path, record: dict[str, Any], label: str) -> None:
    destination = _safe_relative(record.get("destination"), f"{label}.destination")
    expected = _validate_digest(record.get("destination_sha256"), f"{label}.destination_sha256")
    actual = _sha256(_read_regular(plugin_root, destination, f"{label}.destination"))
    if actual != expected:
        raise ValidationError(f"{label} destination digest drift: {destination}")


def _validate_adapted(plugin_root: Path, data: dict[str, Any]) -> None:
    records = _records_by(data.get("adapted"), "destination", "adapted")
    if set(records) != set(EXPECTED_MATRIX):
        raise ValidationError("adapted destinations must match the exact six-destination allowlist")

    used_sources: list[str] = []
    for destination, expected_sources in EXPECTED_MATRIX.items():
        record = records[destination]
        _validate_destination(plugin_root, record, f"adapted[{destination}]")
        if record.get("treatment") != "substantially_adapted":
            raise ValidationError(f"adapted treatment is wrong for {destination}")
        sources = record.get("sources")
        if not isinstance(sources, list) or tuple(sources) != expected_sources:
            raise ValidationError(f"adapted sources are wrong for {destination}")
        for source in sources:
            _safe_relative(source, f"adapted[{destination}].source")
        used_sources.extend(sources)

        review = record.get("diff_review")
        if not isinstance(review, dict):
            raise ValidationError(f"missing diff review for {destination}")
        if review.get("completed") is not True:
            raise ValidationError(f"diff review is incomplete for {destination}")
        if review.get("result") != "source_faithful_minimal_adaptation":
            raise ValidationError(f"diff review result is invalid for {destination}")
        if review.get("style_only_rewrite") is not False:
            raise ValidationError(f"style-only rewrite is not allowed for {destination}")
        retained = review.get("retained")
        if not isinstance(retained, list) or not retained or not all(
            isinstance(item, str) and item.strip() for item in retained
        ):
            raise ValidationError(f"retained substantive structure is missing for {destination}")
        modifications = review.get("modifications")
        if not isinstance(modifications, list) or not modifications:
            raise ValidationError(f"material modifications are unexplained for {destination}")
        for modification in modifications:
            if not isinstance(modification, dict):
                raise ValidationError(f"invalid modification record for {destination}")
            if not isinstance(modification.get("change"), str) or not modification["change"].strip():
                raise ValidationError(f"empty modification explanation for {destination}")
            if modification.get("reason") not in ALLOWED_REASONS:
                raise ValidationError(f"invalid modification reason for {destination}")

    if len(used_sources) != 8 or set(used_sources) != set(EXPECTED_SOURCES):
        raise ValidationError("adapted mapping must resolve to exactly eight frozen sources")


def _validate_classifications(plugin_root: Path, data: dict[str, Any]) -> None:
    informed = _records_by(data.get("informed_by"), "destination", "informed_by")
    if set(informed) != {EXPECTED_INFORMED}:
        raise ValidationError("compound.md must be the sole informed_by destination")
    compound = informed[EXPECTED_INFORMED]
    _validate_destination(plugin_root, compound, "informed_by[compound]")
    if compound.get("treatment") != "original_informed_by":
        raise ValidationError("compound.md treatment must be original_informed_by")
    if compound.get("sources") != [GROUNDING_SOURCE]:
        raise ValidationError("compound.md grounding source identity is wrong")
    if not isinstance(compound.get("influence"), str) or not compound["influence"].strip():
        raise ValidationError("compound.md influence must be recorded")
    review = compound.get("classification_review")
    if not isinstance(review, str) or not review.strip():
        raise ValidationError("compound.md originality review must be recorded")

    originals = _records_by(data.get("original"), "destination", "original")
    if set(originals) != EXPECTED_ORIGINAL:
        raise ValidationError("original reviewer classifications must be exact")
    for destination, record in originals.items():
        _validate_destination(plugin_root, record, f"original[{destination}]")
        if record.get("treatment") != "original":
            raise ValidationError(f"original treatment is wrong for {destination}")
        if not isinstance(record.get("basis"), str) or not record["basis"].strip():
            raise ValidationError(f"original basis is missing for {destination}")

    all_destinations = set(EXPECTED_MATRIX) | set(informed) | set(originals)
    if len(all_destinations) != 9:
        raise ValidationError("provenance classifications overlap")


def _validate_notices(plugin_root: Path, data: dict[str, Any]) -> None:
    ce_license = _read_regular(plugin_root, CE_LICENSE_REL, "CE license")
    if _sha256(ce_license) != CE_LICENSE_SHA256:
        raise ValidationError("packaged CE license does not match the frozen Every MIT license")
    if b"Copyright (c) 2025 Every" not in ce_license or b"Andrew Gomel" in ce_license:
        raise ValidationError("packaged CE license has merged or altered ownership")

    nutworks_license = _read_regular(plugin_root, NUTWORKS_LICENSE_REL, "Nutworks license")
    if _sha256(nutworks_license) != NUTWORKS_LICENSE_SHA256:
        raise ValidationError("packaged Nutworks license does not match the settled MIT notice")
    if b"Copyright (c) 2026 Andrew Gomel" not in nutworks_license or b"2025 Every" in nutworks_license:
        raise ValidationError("Nutworks license has merged or altered ownership")

    notice = _read_regular(plugin_root, NOTICE_REL, "third-party notice").decode("utf-8")
    required_notice_text = (
        "Copyright (c) 2025 Every",
        CE_REPOSITORY,
        CE_VERSION,
        CE_COMMIT,
        CE_LICENSE_REL,
        PROVENANCE_REL,
        "does not imply endorsement",
    )
    for required in required_notice_text:
        if required not in notice:
            raise ValidationError(f"third-party notice is missing: {required}")

    upstream = data.get("upstream")
    if not isinstance(upstream, dict):
        raise ValidationError("upstream identity is missing")
    expected = {
        "name": "Compound Engineering",
        "repository": CE_REPOSITORY,
        "version": CE_VERSION,
        "commit": CE_COMMIT,
        "license_path": CE_LICENSE_REL,
        "license_sha256": CE_LICENSE_SHA256,
    }
    if upstream != expected:
        raise ValidationError("upstream identity or license record is wrong")


def validate(repo_root: Path | str) -> list[str]:
    """Return validation errors without modifying the repository."""

    errors: list[str] = []
    try:
        root = Path(repo_root)
        root_stat = os.lstat(root)
        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
            raise ValidationError("repository root must be a real directory")
        plugin_root = root / PLUGIN_REL
        provenance_bytes = _read_regular(plugin_root, PROVENANCE_REL, "provenance")
        data = _load_json(provenance_bytes, "provenance")
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ValidationError("provenance schema_version must be 1")

        sources = _records_by(data.get("sources"), "path", "sources")
        actual_sources: dict[str, str] = {}
        for source_path, source in sources.items():
            _safe_relative(source_path, "source path")
            actual_sources[source_path] = _validate_digest(
                source.get("sha256"), f"source digest {source_path}"
            )
        if actual_sources != EXPECTED_SOURCES:
            raise ValidationError("source records must match the exact eight frozen CE sources")

        _validate_notices(plugin_root, data)
        _validate_adapted(plugin_root, data)
        _validate_classifications(plugin_root, data)
    except (OSError, ValidationError) as error:
        errors.append(str(error))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Nutworks repository root (defaults to the script's repository)",
    )
    args = parser.parse_args(argv)
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Provenance valid: 6 adapted destinations, 8 frozen CE sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
