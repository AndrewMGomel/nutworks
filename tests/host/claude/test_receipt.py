from __future__ import annotations

import json
import unittest
from pathlib import Path


SCHEMA = json.loads((Path(__file__).parent / "receipt.schema.json").read_text(encoding="utf-8"))


class ClaudeReceiptContractTests(unittest.TestCase):
    def test_receipt_is_exact_build_and_observation_scoped(self) -> None:
        required = set(SCHEMA["required"])
        self.assertTrue({"build", "surface", "operation", "observed"} <= required)
        self.assertEqual(SCHEMA["properties"]["host"]["const"], "claude-code")

    def test_started_inconclusive_smoke_cannot_be_not_tested(self) -> None:
        started_statuses = SCHEMA["allOf"][1]["then"]["properties"]["status"]["enum"]
        self.assertEqual(started_statuses, ["passed", "failed"])

    def test_schema_forbids_semantic_and_custody_claims(self) -> None:
        claim_properties = SCHEMA["properties"]["claims"]["properties"]
        self.assertEqual({value["const"] for value in claim_properties.values()}, {False})


if __name__ == "__main__":
    unittest.main()
