import json
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins" / "nutworks" / "skills" / "nuts"
REFERENCES = SKILL_ROOT / "references"
FIXTURES = ROOT / "tests" / "fixtures"
BENCH = {"coherence", "feasibility", "correctness", "testing", "change-risk", "simplicity"}
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


def selection_result(case):
    selected = case["selected"]
    required = set(case["required"])
    sticky = set(case["sticky"])
    if "novelty" in case["rationale"].casefold():
        return "invalid"
    if len(selected) != len(set(selected)) or not set(selected) <= BENCH:
        return "invalid"
    if not sticky <= set(selected):
        return "invalid"
    if case["mode"] == "light" and len(required | sticky) > 2:
        return "incomplete"
    if case["mode"] == "light" and len(selected) != 2:
        return "invalid"
    if case["mode"] == "full" and len(selected) < 2:
        return "invalid"
    if not required <= set(selected):
        return "invalid"
    return "valid"


def valid_relative_path(value):
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts


def finding_packet_is_valid(packet):
    reviewer = packet.get("reviewer")
    if reviewer not in PRODUCERS:
        return False
    expected_keys = PACKET_REQUIRED | ({"review_receipt"} if reviewer in BENCH else set())
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
        if not isinstance(receipt["target_ref"], str) or not receipt["target_ref"]:
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
        if not finding_required <= set(finding) or not set(finding) <= finding_required | {"suggested_fix"}:
            return False
        if not isinstance(finding["title"], str) or not 1 <= len(finding["title"]) <= 100:
            return False
        if not isinstance(finding["why_it_matters"], str) or not finding["why_it_matters"]:
            return False
        if finding["severity"] not in {"P0", "P1", "P2", "P3"}:
            return False
        if finding["finding_type"] not in {"error", "omission"}:
            return False
        if finding["confidence"] not in {0, 25, 50, 75, 100}:
            return False
        if not isinstance(finding["evidence"], list) or not finding["evidence"] or not all(
            isinstance(item, str) and item for item in finding["evidence"]
        ):
            return False
        if not isinstance(finding["requires_verification"], bool) or not isinstance(
            finding["pre_existing"], bool
        ):
            return False
        if "suggested_fix" in finding and finding["suggested_fix"] is not None and not isinstance(
            finding["suggested_fix"], str
        ):
            return False
        location = finding["location"]
        if not isinstance(location, dict):
            return False
        if location.get("kind") != packet["target_kind"]:
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
        else:
            if (
                set(location) != {"kind", "section"}
                or not isinstance(location.get("section"), str)
                or not location["section"]
            ):
                return False
    return True


def pass_result(case, packets):
    selected = case["selected"]
    returns = case.get("returns", [])
    by_seat = {seat: [] for seat in selected}
    for returned in returns:
        if returned["seat"] in by_seat:
            by_seat[returned["seat"]].append(returned)

    eligible_packets = []
    contexts = []
    for seat in selected:
        seat_returns = by_seat[seat]
        if len(seat_returns) != 1:
            return "unfinished"
        returned = seat_returns[0]
        packet = packets[returned["packet"]]
        if not finding_packet_is_valid(packet):
            return "unfinished"
        if packet["reviewer"] != seat or seat not in BENCH:
            return "unfinished"
        receipt = packet["review_receipt"]
        if returned["dispatch_mode"] != "complete_protocol":
            return "unfinished"
        if receipt["mode"] != "complete_protocol":
            return "unfinished"
        if packet["target_kind"] != case["target_kind"]:
            return "unfinished"
        if receipt["target_ref"] != case["target_ref"]:
            return "unfinished"
        if receipt["protocol_complete"] is not True or receipt["limitations"]:
            return "unfinished"
        eligible_packets.append(packet)
        contexts.append(returned.get("context"))

    if case.get("requires_independence") and (
        not all(contexts) or len(contexts) != len(set(contexts))
    ):
        return "unfinished"
    return (
        "complete_nonzero"
        if any(packet["findings"] for packet in eligible_packets)
        else "complete_zero"
    )


class ReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = (REFERENCES / "review.md").read_text(encoding="utf-8")

    def test_all_and_only_bounded_bench_files_exist(self):
        reviewer_dir = REFERENCES / "reviewers"
        self.assertEqual({path.stem for path in reviewer_dir.glob("*.md")}, BENCH)

    def test_fresh_selection_cases(self):
        for case in load_json("review/selection-cases.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(selection_result(case), case["expected"])

    def test_review_contract_states_capacity_stickiness_and_no_novelty(self):
        required = [
            "Full selects at least two protocols",
            "Light selects exactly two",
            "unresolved actionable finding remains selected",
            "never rotate merely for novelty",
            "simplicity is never a mandatory third reviewer",
        ]
        review = normalized(self.review)
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, review)

    def test_finding_fixtures_enforce_schema_shape_and_relative_locations(self):
        for case in load_json("review/finding-cases.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(finding_packet_is_valid(case["packet"]), case["valid"])

    def test_published_schema_and_handwritten_oracle_have_structural_parity(self):
        schema = json.loads(
            (REFERENCES / "schemas" / "finding.schema.json").read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), PACKET_REQUIRED)
        self.assertEqual(set(schema["properties"]["reviewer"]["enum"]), PRODUCERS)

        receipt = schema["properties"]["review_receipt"]
        self.assertFalse(receipt["additionalProperties"])
        self.assertEqual(set(receipt["required"]), RECEIPT_REQUIRED)
        self.assertEqual(
            set(receipt["properties"]["mode"]["enum"]),
            {"complete_protocol", "targeted_verification"},
        )
        receipt_rules = {
            rule["if"]["properties"]["mode"]["const"]: rule["then"]["properties"]
            for rule in receipt["allOf"]
        }
        self.assertEqual(receipt_rules["complete_protocol"]["protocol_complete"], {"const": True})
        self.assertEqual(receipt_rules["complete_protocol"]["limitations"], {"maxItems": 0})
        self.assertEqual(receipt_rules["targeted_verification"]["protocol_complete"], {"const": False})
        self.assertEqual(receipt_rules["targeted_verification"]["limitations"], {"minItems": 1})

        producer_rules = schema["allOf"]
        self.assertEqual(
            set(producer_rules[0]["if"]["properties"]["reviewer"]["enum"]), BENCH
        )
        self.assertEqual(producer_rules[0]["then"], {"required": ["review_receipt"]})
        self.assertEqual(
            set(producer_rules[1]["if"]["properties"]["reviewer"]["enum"]),
            AUDIT_PRODUCERS,
        )
        self.assertEqual(
            producer_rules[1]["then"], {"not": {"required": ["review_receipt"]}}
        )
        self.assertIn(
            "does not satisfy a pass seat or establish convergence",
            schema["properties"]["findings"]["description"],
        )

    def test_pass_accounting_matrix_is_symmetric(self):
        fixture = load_json("review/pass-cases.json")
        packets = fixture["packets"]
        for name, packet in packets.items():
            with self.subTest(packet=name):
                self.assertEqual(
                    finding_packet_is_valid(packet), fixture["packet_validity"][name]
                )
        for phase in ("critique", "review"):
            for case in fixture["cases"]:
                with self.subTest(phase=phase, case=case["name"]):
                    self.assertEqual(pass_result(case, packets), case["expected"])

    def test_mutation_targeted_zero_and_fresh_complete_zero_trace(self):
        fixture = load_json("review/pass-cases.json")
        packets = fixture["packets"]
        trace = fixture["temporal_trace"]
        self.assertEqual(trace["mutation"], {"from": "plan-r1", "to": "plan-r2"})
        for phase in ("critique", "review"):
            actual = [
                pass_result(
                    next(case for case in fixture["cases"] if case["name"] == name),
                    packets,
                )
                for name in trace["cases"]
            ]
            with self.subTest(phase=phase):
                self.assertEqual(actual, trace["expected"])

    def test_original_specialists_remain_distinct(self):
        change_risk = (REFERENCES / "reviewers" / "change-risk.md").read_text(encoding="utf-8")
        simplicity = (REFERENCES / "reviewers" / "simplicity.md").read_text(encoding="utf-8")
        self.assertIn("concrete domain or integration risk", change_risk)
        self.assertIn("one-use", simplicity)
        self.assertIn("not a replacement for change-risk", simplicity)
        self.assertNotEqual(change_risk, simplicity)


class AuditContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = (REFERENCES / "audit.md").read_text(encoding="utf-8")
        cls.fixture = load_json("audit/cases.json")

    def test_required_parts_questions_and_triage_values(self):
        for value in self.fixture["required_parts"] + self.fixture["required_questions"]:
            with self.subTest(value=value):
                self.assertIn(value, self.audit)
        triage = (REFERENCES / "auditors" / "triage.md").read_text(encoding="utf-8")
        for value in self.fixture["triage_values"]:
            self.assertIn(f"`{value}`", triage)

    def test_each_auditor_protocol_exists_and_forbids_mutation(self):
        for name in ("concerns", "verification", "triage"):
            with self.subTest(name=name):
                text = (REFERENCES / "auditors" / f"{name}.md").read_text(encoding="utf-8")
                self.assertIn("Do not edit the target", normalized(text))

    def test_triage_covers_every_source_finding(self):
        for case in self.fixture["cases"]:
            all_findings = set(
                case["main_findings"]
                + case["concern_findings"]
                + case["verification_findings"]
            )
            actual = "complete" if all_findings == set(case["triaged"]) else "incomplete"
            with self.subTest(case=case["name"]):
                self.assertEqual(actual, case["expected"])

    def test_audit_producers_use_exact_receipt_free_shared_packet_mapping(self):
        concerns = (REFERENCES / "auditors" / "concerns.md").read_text(encoding="utf-8")
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


class CompoundContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compound = (REFERENCES / "compound.md").read_text(encoding="utf-8")

    def test_outcomes_are_exhaustive_and_project_writes_are_bounded(self):
        cases = load_json("compound/cases.json")
        self.assertEqual(
            {case["outcome"] for case in cases},
            {"created", "updated", "candidate", "no_op", "blocked"},
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertLessEqual(case["project_writes"], 1)
                self.assertIn(f"`{case['outcome']}`", self.compound)

    def test_no_store_becomes_candidate_without_inventing_a_convention(self):
        case = next(
            case for case in load_json("compound/cases.json") if case["name"] == "no-declared-store"
        )
        self.assertEqual(case["outcome"], "candidate")
        self.assertEqual(case["project_writes"], 0)
        self.assertIn("Do not invent", self.compound)

    def test_learning_write_requires_current_review(self):
        for case in load_json("compound/cases.json"):
            expected = case["outcome"] in {"created", "updated"}
            with self.subTest(case=case["name"]):
                self.assertEqual(case["requires_review"], expected)
        self.assertIn("Full must", self.compound)
        self.assertIn("Light must", self.compound)


class IntegratedFixtureTests(unittest.TestCase):
    def test_full_and_light_happy_paths_preserve_mode_orders(self):
        full = load_json("semantic-project/full-run.json")
        light = load_json("semantic-project/light-learning-run.json")
        self.assertEqual(full["expected_claim"], "Full")
        self.assertIn("Audit pre clear", full["events"])
        self.assertIn("Audit post clear", full["events"])
        self.assertEqual(light["expected_claim"], "Light")
        self.assertNotIn("Audit pre clear", light["events"])
        self.assertLess(
            light["events"].index("Compound updated"),
            light["events"].index("Review zero after learning"),
        )

    def test_running_worker_prevents_completion(self):
        interrupted = load_json("semantic-project/interrupted-run.json")
        self.assertGreater(interrupted["workers_running_at_summary"], 0)
        self.assertEqual(interrupted["expected_claim"], "incomplete")


if __name__ == "__main__":
    unittest.main()
