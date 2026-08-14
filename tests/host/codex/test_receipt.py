from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.validate_official_codex import run_official_validator


SCHEMA = json.loads((Path(__file__).parent / "receipt.schema.json").read_text(encoding="utf-8"))


class CodexReceiptContractTests(unittest.TestCase):
    def test_schema_forbids_semantic_and_custody_claims(self) -> None:
        claim_properties = SCHEMA["properties"]["claims"]["properties"]
        self.assertEqual({value["const"] for value in claim_properties.values()}, {False})
        self.assertEqual(
            SCHEMA["properties"]["status"]["enum"],
            ["passed", "failed", "not-tested"],
        )

    def test_not_tested_is_only_for_an_unstarted_smoke(self) -> None:
        rules = SCHEMA["allOf"]
        self.assertEqual(rules[0]["then"]["properties"]["status"]["const"], "not-tested")
        self.assertNotIn("not-tested", rules[1]["then"]["properties"]["status"]["enum"])


class OfficialCodexWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "plugins/nutworks").mkdir(parents=True)
        (self.root / "requirements-dev.lock").write_text("PyYAML==6.0.2\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def validator(self, exit_code: int) -> Path:
        path = self.root / "official" / "validate_plugin.py"
        path.parent.mkdir()
        path.write_text(
            "import sys\nprint('official fixture')\nraise SystemExit(%d)\n" % exit_code,
            encoding="utf-8",
        )
        return path

    @mock.patch("scripts.validate_official_codex.importlib.metadata.version", return_value="6.0.2")
    def test_runs_explicit_validator_without_installing_dependencies(self, _version: object) -> None:
        result, exit_code = run_official_validator(self.root, validator_path=self.validator(0))
        self.assertEqual((result["status"], exit_code), ("passed", 0))
        self.assertIn("official fixture", result["stdout"])

    @mock.patch("scripts.validate_official_codex.importlib.metadata.version", return_value="6.0.2")
    def test_failed_official_validation_is_not_relabelled_unavailable(self, _version: object) -> None:
        result, exit_code = run_official_validator(self.root, validator_path=self.validator(1))
        self.assertEqual((result["status"], exit_code), ("failed", 1))

    @mock.patch("scripts.validate_official_codex.importlib.metadata.version", return_value="6.0.1")
    def test_dependency_mismatch_reports_unavailable(self, _version: object) -> None:
        result, exit_code = run_official_validator(self.root, validator_path=self.validator(0))
        self.assertEqual((result["status"], exit_code), ("unavailable", 2))
        self.assertIn("does not match", result["reason"])


if __name__ == "__main__":
    unittest.main()
