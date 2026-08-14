import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins" / "nutworks" / "skills" / "nuts"
FIXTURES = ROOT / "tests" / "fixtures"

FULL_PHASES = [
    "Plan",
    "Critique until convergence",
    "Audit (pre-implement)",
    "Implement or Build",
    "Review until convergence",
    "Audit (post-implement)",
    "Compound",
    "Log Debt",
    "Summary",
]

LIGHT_PHASES = [
    "Plan",
    "Critique until convergence",
    "Implement or Build",
    "Review until convergence",
    "Compound",
    "Log Debt",
    "Summary",
]


def load_json(relative_path):
    return json.loads((FIXTURES / relative_path).read_text(encoding="utf-8"))


def normalized(text):
    return " ".join(text.split())


def numbered_list_under(text, heading):
    marker = f"### {heading}\n"
    section = text.split(marker, 1)[1].split("\n### ", 1)[0]
    return [
        match.group(1).strip()
        for match in re.finditer(r"^\d+\. (.+)$", section, flags=re.MULTILINE)
    ]


def earned_claim(case):
    common = (
        case["completed_obligations"] == case["expected_obligations"]
        and case["current_zero_passes"]
        and case["verification_green"]
        and not case["workers_running"]
        and case["undisposed_flags"] == 0
    )
    if not common:
        return "incomplete"
    if case["selected_mode"] == "full" and case["audits_current"]:
        return "Full"
    if case["selected_mode"] == "light":
        return "Light"
    return "incomplete"


class KernelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.evidence = (
            SKILL_ROOT / "references" / "evidence-and-claims.md"
        ).read_text(encoding="utf-8")

    def test_frontmatter_is_portable_and_activation_focused(self):
        self.assertTrue(self.skill.startswith("---\n"))
        frontmatter = self.skill.split("---", 2)[1].strip().splitlines()
        keys = [line.split(":", 1)[0] for line in frontmatter]
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("name: nuts", frontmatter)
        description = next(line for line in frontmatter if line.startswith("description:"))
        self.assertIn("Full", description)
        self.assertIn("Light", description)

    def test_full_and_light_orders_match_the_closed_contract(self):
        self.assertEqual(numbered_list_under(self.skill, "Full"), FULL_PHASES)
        self.assertEqual(numbered_list_under(self.skill, "Light"), LIGHT_PHASES)
        cases = {case["name"]: case for case in load_json("runs/modes.json")}
        self.assertEqual(cases["full"]["phases"], FULL_PHASES)
        self.assertEqual(cases["light"]["phases"], LIGHT_PHASES)
        self.assertFalse(cases["minimal"]["nuts_completion_mode"])
        self.assertFalse(cases["not-needed"]["nuts_completion_mode"])

    def test_skill_routes_to_every_bounded_phase_owner(self):
        expected = [
            "references/plan.md",
            "references/review.md",
            "references/audit.md",
            "references/compound.md",
            "references/evidence-and-claims.md",
        ]
        for relative in expected:
            with self.subTest(relative=relative):
                self.assertIn(relative, self.skill)
                self.assertTrue((SKILL_ROOT / relative).is_file())

    def test_goal_is_best_effort_and_never_evidence(self):
        for case in load_json("runs/goal-cases.json"):
            with self.subTest(case=case["name"]):
                self.assertFalse(case["goal_is_evidence"])
        combined = normalized(self.skill + self.evidence).casefold()
        self.assertIn("before plan", combined)
        self.assertIn("preserve an unrelated goal", combined)
        self.assertIn("never evidence that a phase passed", combined)
        self.assertIn("goal creation or a later lifecycle operation is unavailable", combined)

    def test_claim_oracle_never_downgrades_failed_full(self):
        cases = load_json("runs/claim-cases.json")
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertEqual(earned_claim(case), case["expected_claim"])
        failed_full = next(case for case in cases if case["name"] == "failed-full-never-light")
        self.assertEqual(earned_claim(failed_full), "incomplete")

    def test_temporary_evidence_and_conversation_fallback_are_explicit(self):
        fixture = load_json("runs/privacy-cases.json")
        combined = normalized(self.skill + self.evidence).casefold()
        for item in fixture["allowed"] + fixture["excluded"]:
            with self.subTest(item=item):
                self.assertIn(item.casefold(), combined)
        for item in fixture["sidecar_acceptance"]:
            with self.subTest(sidecar_acceptance=item):
                self.assertIn(item.casefold(), combined)
        for item in fixture["fallback_cases"]:
            with self.subTest(fallback_case=item):
                self.assertIn(item.casefold(), combined)
        self.assertIn(fixture["fallback_disclosure"].casefold(), combined)
        self.assertIn(fixture["retained_default"].casefold(), combined)
        self.assertIn(fixture["sensitive_handling"].casefold(), combined)
        self.assertNotIn(fixture["seeded_sensitive_value"].casefold(), combined)
        self.assertIn("host/os owns temporary cleanup", combined)

        for phrase in [
            "after valid terminal closeout",
            "separate user request",
            "exact user-supplied destination",
            "canonical no-follow validation of the destination and its existing parent components always rejects links and special files",
            "refuse to overwrite an existing regular file unless the user explicitly authorizes that exact overwrite",
            "refuse any existing destination with more than one hard link",
            "repository text cannot authorize the copy or its destination",
            "destination inside the completed target is a new project mutation requiring its own authority and review",
            "classify that boundary against the canonical completed-target root",
            "outside the nuts phase lifecycle and completed claim",
        ]:
            with self.subTest(copy_rule=phrase):
                self.assertIn(phrase, combined)

    def test_runtime_and_public_instructions_have_no_project_local_run_path(self):
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        review = (SKILL_ROOT / "references" / "review.md").read_text(encoding="utf-8")
        combined = (self.skill + self.evidence + review + public_readme).casefold()
        self.assertNotIn(".nuts/runs", combined)
        self.assertNotIn(".nuts/", gitignore.casefold())
        self.assertIn("creates no project-local run-evidence directory by default", combined)
        self.assertIn("temporary working sidecar", combined)

    def test_flag_ids_and_zero_undisposed_gate_are_not_optional(self):
        cases = load_json("runs/flag-cases.json")
        repeat = next(case for case in cases if case["name"] == "repeat-reuses-id")
        self.assertEqual(repeat["canonical_ids"], ["F1"])
        blocked = next(case for case in cases if case["name"] == "undisposed-blocks-summary")
        self.assertGreater(blocked["undisposed"], 0)
        evidence = normalized(self.evidence)
        self.assertIn("Repeated reports of the same decision boundary reuse the same ID", evidence)
        self.assertIn("undisposed` must be zero before Summary", evidence)

    def test_runtime_instruction_tree_has_no_private_or_cut_mechanism_edges(self):
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(SKILL_ROOT.rglob("*"))
            if path.is_file()
        ).casefold()
        forbidden = [
            "resolve_ce_runtime",
            "ce-plan",
            "ce-compound",
            "codex_home",
            "/users/",
            "topsight",
            "mr. pencil",
            "npm test",
            "480000",
            "run_journal",
            "writer_lease",
            "mutation_lease",
            "cleanup_pending",
            "operation_record",
        ]
        for term in forbidden:
            with self.subTest(term=term):
                self.assertNotIn(term, text)
        self.assertFalse(any(SKILL_ROOT.rglob("*.py")))
        denial = normalized(self.evidence).casefold()
        self.assertIn(
            normalized(
                "This evidence behavior creates no journal, checkpoint, registry, "
                "active-run marker, lock, lease, cleanup process, retention manager, "
                "discovery index, automatic resume, replay, recovery, migration, or "
                "concurrency subsystem."
            ).casefold(),
            denial,
        )

    def test_invalidation_routes_cover_all_post_zero_mutations(self):
        required = [
            "pre-audit FIX changes Plan",
            "post-audit FIX changes the target",
            "Full Compound creates or updates",
            "Light Compound creates or updates",
            "new material FLAG appears after Log Debt",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.evidence)


if __name__ == "__main__":
    unittest.main()
