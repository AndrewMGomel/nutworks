import json
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins" / "nutworks" / "skills" / "nuts"
REFERENCES = SKILL_ROOT / "references"
FIXTURES = ROOT / "tests" / "fixtures"
BENCH = {
    "coherence",
    "feasibility",
    "correctness",
    "testing",
    "change-risk",
    "simplicity",
}
AUDIT_PRODUCERS = {"audit-concerns", "audit-verification"}
PRODUCERS = BENCH | AUDIT_PRODUCERS
PACKET_REQUIRED = {
    "reviewer",
    "target_kind",
    "findings",
    "residual_risks",
    "deferred_questions",
    "testing_gaps",
}
RECEIPT_REQUIRED = {"mode", "target_ref", "protocol_complete", "limitations"}


def load_json(relative_path):
    return json.loads((FIXTURES / relative_path).read_text(encoding="utf-8"))


def normalized(text):
    return " ".join(text.split())


def valid_relative_path(value):
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def finding_packet_is_valid(packet):
    if not isinstance(packet, dict):
        return False
    reviewer = packet.get("reviewer")
    if reviewer not in PRODUCERS:
        return False
    expected_keys = PACKET_REQUIRED | (
        {"review_receipt"} if reviewer in BENCH else set()
    )
    if set(packet) != expected_keys:
        return False
    if packet["target_kind"] not in {"document", "code"}:
        return False
    if not all(
        isinstance(packet[name], list)
        for name in PACKET_REQUIRED - {"reviewer", "target_kind"}
    ):
        return False
    if not all(
        all(isinstance(item, str) for item in packet[name])
        for name in {"residual_risks", "deferred_questions", "testing_gaps"}
    ):
        return False
    if reviewer in BENCH:
        receipt = packet["review_receipt"]
        if not isinstance(receipt, dict) or set(receipt) != RECEIPT_REQUIRED:
            return False
        if not isinstance(receipt["target_ref"], str) or not receipt[
            "target_ref"
        ].strip():
            return False
        if not isinstance(receipt["protocol_complete"], bool):
            return False
        limitations = receipt["limitations"]
        if not isinstance(limitations, list) or not all(
            isinstance(item, str) and item for item in limitations
        ):
            return False
        if receipt["mode"] == "complete_protocol":
            if receipt["protocol_complete"] is not True or limitations:
                return False
        elif receipt["mode"] == "targeted_verification":
            if receipt["protocol_complete"] is not False or not limitations:
                return False
        else:
            return False

    finding_required = {
        "title",
        "severity",
        "location",
        "why_it_matters",
        "finding_type",
        "confidence",
        "evidence",
        "requires_verification",
        "pre_existing",
    }
    for finding in packet["findings"]:
        if not isinstance(finding, dict):
            return False
        if not finding_required <= set(finding) or not set(finding) <= (
            finding_required | {"suggested_fix"}
        ):
            return False
        if not isinstance(finding["title"], str) or not 1 <= len(
            finding["title"]
        ) <= 100:
            return False
        if not isinstance(finding["why_it_matters"], str) or not finding[
            "why_it_matters"
        ]:
            return False
        if finding["severity"] not in {"P0", "P1", "P2", "P3"}:
            return False
        if finding["finding_type"] not in {"error", "omission"}:
            return False
        if finding["confidence"] not in {0, 25, 50, 75, 100}:
            return False
        if not isinstance(finding["evidence"], list) or not finding[
            "evidence"
        ] or not all(isinstance(item, str) and item for item in finding["evidence"]):
            return False
        if not isinstance(finding["requires_verification"], bool) or not isinstance(
            finding["pre_existing"], bool
        ):
            return False
        if (
            "suggested_fix" in finding
            and finding["suggested_fix"] is not None
            and not isinstance(finding["suggested_fix"], str)
        ):
            return False
        location = finding["location"]
        if not isinstance(location, dict) or location.get("kind") != packet[
            "target_kind"
        ]:
            return False
        if packet["target_kind"] == "code":
            if set(location) != {"kind", "path", "line"}:
                return False
            if not valid_relative_path(location.get("path", "")):
                return False
            if (
                not isinstance(location.get("line"), int)
                or isinstance(location["line"], bool)
                or location["line"] < 1
            ):
                return False
        elif set(location) != {"kind", "section"} or not isinstance(
            location.get("section"), str
        ) or not location["section"]:
            return False
    return True


class ReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = (REFERENCES / "review.md").read_text(encoding="utf-8")

    def test_all_and_only_bounded_bench_files_exist(self):
        reviewer_dir = REFERENCES / "reviewers"
        self.assertEqual({path.stem for path in reviewer_dir.glob("*.md")}, BENCH)

    def test_review_contract_states_capacity_stickiness_and_no_novelty(self):
        review = normalized(self.review)
        for phrase in [
            "Full selects at least two protocols",
            "Light selects exactly two",
            "unresolved actionable finding remains selected",
            "never rotate merely for novelty",
            "simplicity is never a mandatory third reviewer",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, review)

    def test_finding_fixtures_enforce_schema_shape_and_relative_locations(self):
        for case in load_json("review/finding-cases.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(
                    finding_packet_is_valid(case["packet"]), case["valid"]
                )

    def test_published_schema_and_validator_have_structural_parity(self):
        schema = json.loads(
            (REFERENCES / "schemas" / "finding.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), PACKET_REQUIRED)
        self.assertEqual(set(schema["properties"]["reviewer"]["enum"]), PRODUCERS)
        self.assertEqual(
            set(schema["properties"]["target_kind"]["enum"]),
            {"document", "code"},
        )
        self.assertEqual(
            schema["properties"]["target_kind"]["description"],
            "Assignment-level kind for this producer or seat; the runner's target_ref separately binds the shared whole target",
        )
        receipt = schema["properties"]["review_receipt"]
        self.assertFalse(receipt["additionalProperties"])
        self.assertEqual(set(receipt["required"]), RECEIPT_REQUIRED)
        self.assertEqual(
            set(receipt["properties"]["mode"]["enum"]),
            {"complete_protocol", "targeted_verification"},
        )

    def test_mixed_target_uses_assignment_kinds_under_one_pass(self):
        review = normalized(self.review)
        for phrase in [
            "assignment-level expected `target_kind`",
            "One `target_ref` binds the whole current target",
            "Assign `target_kind` per selected protocol",
            "different `code` or `document` kinds",
            "one coordinated pass with one pass state and one convergence decision",
            "Do not add a `mixed` kind",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, review)

    def test_original_specialists_remain_distinct(self):
        change_risk = (REFERENCES / "reviewers" / "change-risk.md").read_text(
            encoding="utf-8"
        )
        simplicity = (REFERENCES / "reviewers" / "simplicity.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("concrete domain or integration risk", change_risk)
        self.assertIn("one-use", simplicity)
        self.assertIn("not a replacement for change-risk", simplicity)
        self.assertNotEqual(change_risk, simplicity)

    def test_runner_classification_cannot_forge_convergence(self):
        text = normalized(self.review)
        for label in ("`PRODUCT`", "`GUARD`", "`HARNESS`"):
            self.assertIn(label, text)
        self.assertIn("never suppresses a valid finding", text)
        self.assertIn("converts a nonzero pass to zero", text)


class AuditContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = (REFERENCES / "audit.md").read_text(encoding="utf-8")

    def test_required_parts_questions_and_triage_values(self):
        for value in [
            "Main Context",
            "Concerns",
            "Verification",
            "Triage",
            "What worries you?",
            "What breaks if this runs for a week unattended?",
        ]:
            self.assertIn(value, self.audit)
        triage = (REFERENCES / "auditors" / "triage.md").read_text(
            encoding="utf-8"
        )
        for value in ("FIX", "FLAG", "ACCEPT"):
            self.assertIn(f"`{value}`", triage)

    def test_each_auditor_protocol_exists_and_forbids_mutation(self):
        for name in ("concerns", "verification", "triage"):
            with self.subTest(name=name):
                text = (REFERENCES / "auditors" / f"{name}.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn("Do not edit the target", normalized(text))

    def test_audit_producers_use_receipt_free_shared_packets(self):
        concerns = (REFERENCES / "auditors" / "concerns.md").read_text(
            encoding="utf-8"
        )
        verification = (REFERENCES / "auditors" / "verification.md").read_text(
            encoding="utf-8"
        )
        for text, identity in (
            (self.audit + concerns, "audit-concerns"),
            (self.audit + verification, "audit-verification"),
        ):
            normalized_text = normalized(text)
            with self.subTest(identity=identity):
                self.assertIn(f"reviewer: {identity}", normalized_text)
                self.assertIn("runner-supplied current `target_kind`", normalized_text)
                self.assertIn("no `review_receipt`", normalized_text)

    def test_verification_and_triage_boundaries_are_explicit(self):
        verification = normalized(
            (REFERENCES / "auditors" / "verification.md").read_text(
                encoding="utf-8"
            )
        )
        triage = normalized(
            (REFERENCES / "auditors" / "triage.md").read_text(encoding="utf-8")
        )
        for phrase in [
            "shipped/runtime object",
            "could falsify the premise",
            "negative existence claims",
            "smaller or no-build answer",
            "shared lower-level cause",
        ]:
            self.assertIn(phrase, verification)
        self.assertIn("classification never suppresses a finding", triage.casefold())
        self.assertIn("outside the settled product contract", triage.casefold())
        self.assertIn("fail-closed", triage.casefold())


class CompoundContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compound = (REFERENCES / "compound.md").read_text(encoding="utf-8")

    def test_outcomes_and_write_boundary_are_explicit(self):
        for outcome in ("created", "updated", "forwarded_candidate", "no_op", "blocked"):
            self.assertIn(f"`{outcome}`", self.compound)
        self.assertIn("Write at most one project learning", self.compound)

    def test_materiality_and_owner_requirements_are_explicit(self):
        text = normalized(self.compound)
        for phrase in [
            "verified current-run evidence",
            "the repeat failure its retention would prevent",
            "Do not invent",
            "canonical Invalidation Routes",
            "sole owner of the resulting phase route",
        ]:
            self.assertIn(phrase, text)
        self.assertNotIn("Full must return", text)
        self.assertNotIn("Light must return", text)


if __name__ == "__main__":
    unittest.main()
