from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.validate_provenance import (
    CE_LICENSE_SHA256,
    EXPECTED_MATRIX,
    EXPECTED_SOURCES,
    validate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_REL = Path("plugins/nutworks")
PROVENANCE_REL = PLUGIN_REL / "third_party/compound-engineering/provenance.json"


class ProvenanceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        shutil.copytree(REPO_ROOT / PLUGIN_REL, self.root / PLUGIN_REL)

    def tearDown(self) -> None:
        self._temp.cleanup()

    @property
    def provenance_path(self) -> Path:
        return self.root / PROVENANCE_REL

    def load_provenance(self) -> dict:
        return json.loads(self.provenance_path.read_text(encoding="utf-8"))

    def save_provenance(self, data: dict) -> None:
        self.provenance_path.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )

    def assert_invalid(self, fragment: str) -> None:
        errors = validate(self.root)
        self.assertTrue(errors, "expected provenance validation to fail")
        self.assertIn(fragment, errors[0])

    def test_complete_mapping_is_valid_and_exact(self) -> None:
        self.assertEqual([], validate(self.root))
        data = self.load_provenance()
        self.assertEqual(6, len(data["adapted"]))
        self.assertEqual(8, len(data["sources"]))
        self.assertEqual(set(EXPECTED_MATRIX), {row["destination"] for row in data["adapted"]})
        self.assertEqual(set(EXPECTED_SOURCES), {row["path"] for row in data["sources"]})

    def test_packaged_ce_license_is_exact(self) -> None:
        license_path = self.root / PLUGIN_REL / "third_party/compound-engineering/LICENSE"
        self.assertEqual(CE_LICENSE_SHA256, hashlib.sha256(license_path.read_bytes()).hexdigest())

    def test_validation_is_read_only(self) -> None:
        before = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual([], validate(self.root))
        after = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_missing_and_duplicate_adapted_records_fail(self) -> None:
        data = self.load_provenance()
        removed = data["adapted"].pop()
        self.save_provenance(data)
        self.assert_invalid("six-destination")

        data["adapted"].append(removed)
        data["adapted"].append(dict(removed))
        self.save_provenance(data)
        self.assert_invalid("duplicate destination")

    def test_source_count_and_identity_are_frozen(self) -> None:
        data = self.load_provenance()
        data["sources"][0]["sha256"] = "0" * 64
        self.save_provenance(data)
        self.assert_invalid("exact eight frozen CE sources")

    def test_destination_digest_drift_fails(self) -> None:
        data = self.load_provenance()
        destination = self.root / PLUGIN_REL / data["adapted"][0]["destination"]
        destination.write_text(destination.read_text(encoding="utf-8") + "\ndrift\n", encoding="utf-8")
        self.assert_invalid("destination digest drift")

    def test_unexplained_or_style_only_adaptation_fails(self) -> None:
        data = self.load_provenance()
        data["adapted"][0]["diff_review"]["modifications"] = []
        self.save_provenance(data)
        self.assert_invalid("unexplained")

        data = json.loads((REPO_ROOT / PROVENANCE_REL).read_text(encoding="utf-8"))
        data["adapted"][0]["diff_review"]["style_only_rewrite"] = True
        self.save_provenance(data)
        self.assert_invalid("style-only")

    def test_removed_structure_and_invalid_reason_fail(self) -> None:
        data = self.load_provenance()
        data["adapted"][0]["diff_review"]["retained"] = []
        self.save_provenance(data)
        self.assert_invalid("substantive structure")

        data = json.loads((REPO_ROOT / PROVENANCE_REL).read_text(encoding="utf-8"))
        data["adapted"][0]["diff_review"]["modifications"][0]["reason"] = "style"
        self.save_provenance(data)
        self.assert_invalid("modification reason")

    def test_absolute_and_traversal_paths_fail(self) -> None:
        data = self.load_provenance()
        data["adapted"][0]["destination"] = "/tmp/plan.md"
        self.save_provenance(data)
        self.assert_invalid("six-destination")

        data = json.loads((REPO_ROOT / PROVENANCE_REL).read_text(encoding="utf-8"))
        data["sources"][0]["path"] = "../outside.md"
        self.save_provenance(data)
        self.assert_invalid("traverse")

    def test_symlink_destination_fails(self) -> None:
        data = self.load_provenance()
        destination = self.root / PLUGIN_REL / data["adapted"][0]["destination"]
        replacement = destination.with_name("replacement.md")
        destination.rename(replacement)
        destination.symlink_to(replacement.name)
        self.assert_invalid("symbolic link")

    def test_hard_link_destination_fails(self) -> None:
        data = self.load_provenance()
        destination = self.root / PLUGIN_REL / data["adapted"][0]["destination"]
        os.link(destination, destination.with_name("second-link.md"))
        self.assert_invalid("exactly one hard link")

    def test_wrong_type_destination_fails(self) -> None:
        data = self.load_provenance()
        destination = self.root / PLUGIN_REL / data["adapted"][0]["destination"]
        destination.unlink()
        destination.mkdir()
        self.assert_invalid("regular file")

    def test_path_swap_in_mapping_fails(self) -> None:
        data = self.load_provenance()
        first = data["adapted"][0]["destination"]
        second = data["adapted"][1]["destination"]
        data["adapted"][0]["destination"] = second
        data["adapted"][1]["destination"] = first
        self.save_provenance(data)
        self.assert_invalid("destination digest drift")

    def test_missing_or_altered_third_party_notice_fails(self) -> None:
        notice = self.root / PLUGIN_REL / "THIRD_PARTY_NOTICES.md"
        notice.unlink()
        self.assert_invalid("No such file")

        shutil.copy2(REPO_ROOT / PLUGIN_REL / "THIRD_PARTY_NOTICES.md", notice)
        notice.write_text("Copyright (c) 2025 Every\n", encoding="utf-8")
        self.assert_invalid("third-party notice is missing")

    def test_linked_third_party_notice_fails(self) -> None:
        notice = self.root / PLUGIN_REL / "THIRD_PARTY_NOTICES.md"
        replacement = notice.with_name("notice-copy.md")
        notice.rename(replacement)
        notice.symlink_to(replacement.name)
        self.assert_invalid("symbolic link")

    def test_duplicate_json_key_fails(self) -> None:
        text = self.provenance_path.read_text(encoding="utf-8")
        self.provenance_path.write_text(
            text.replace('"schema_version": 1,', '"schema_version": 1,\n  "schema_version": 1,', 1),
            encoding="utf-8",
        )
        self.assert_invalid("duplicate JSON key")

    def test_merged_or_altered_license_ownership_fails(self) -> None:
        ce_license = self.root / PLUGIN_REL / "third_party/compound-engineering/LICENSE"
        ce_license.write_text(
            ce_license.read_text(encoding="utf-8") + "Copyright (c) 2026 Andrew Gomel\n",
            encoding="utf-8",
        )
        self.assert_invalid("frozen Every MIT license")

        shutil.copy2(REPO_ROOT / PLUGIN_REL / "third_party/compound-engineering/LICENSE", ce_license)
        nutworks_license = self.root / PLUGIN_REL / "LICENSE"
        nutworks_license.write_text(
            nutworks_license.read_text(encoding="utf-8") + "Copyright (c) 2025 Every\n",
            encoding="utf-8",
        )
        self.assert_invalid("settled MIT notice")

    def test_informed_and_original_classifications_are_required(self) -> None:
        data = self.load_provenance()
        data["informed_by"] = []
        self.save_provenance(data)
        self.assert_invalid("sole informed_by")

        data = json.loads((REPO_ROOT / PROVENANCE_REL).read_text(encoding="utf-8"))
        data["original"].pop()
        self.save_provenance(data)
        self.assert_invalid("original reviewer classifications")


if __name__ == "__main__":
    unittest.main()
