import json
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins" / "nutworks" / "skills" / "nuts"
REFERENCES = SKILL_ROOT / "references"
FIXTURES = ROOT / "tests" / "fixtures"
BENCH = {"coherence", "feasibility", "correctness", "testing", "change-risk", "simplicity"}


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
    top_required = {
        "reviewer",
        "target_kind",
        "findings",
        "residual_risks",
        "deferred_questions",
        "testing_gaps",
    }
    if set(packet) != top_required:
        return False
    if not packet["reviewer"] or packet["target_kind"] not in {"document", "code"}:
        return False
    if not all(isinstance(packet[name], list) for name in top_required - {"reviewer", "target_kind"}):
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
        if not finding_required <= set(finding):
            return False
        if finding["severity"] not in {"P0", "P1", "P2", "P3"}:
            return False
        if finding["finding_type"] not in {"error", "omission"}:
            return False
        if finding["confidence"] not in {0, 25, 50, 75, 100}:
            return False
        if not finding["evidence"] or not all(finding["evidence"]):
            return False
        location = finding["location"]
        if location.get("kind") != packet["target_kind"]:
            return False
        if packet["target_kind"] == "code":
            if not valid_relative_path(location.get("path", "")):
                return False
            if not isinstance(location.get("line"), int) or location["line"] < 1:
                return False
        elif not location.get("section"):
            return False
    return True


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
