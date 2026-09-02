import json
import re
import unittest
from pathlib import Path

from support import (
    private_record_is_minimal,
    private_reference_is_bound,
    summary_is_accepted,
)


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


class KernelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.evidence = (
            SKILL_ROOT / "references" / "evidence-and-claims.md"
        ).read_text(encoding="utf-8")
        cls.plan = (SKILL_ROOT / "references" / "plan.md").read_text(
            encoding="utf-8"
        )
        cls.review = (SKILL_ROOT / "references" / "review.md").read_text(
            encoding="utf-8"
        )

    def test_frontmatter_is_portable_and_activation_focused(self):
        self.assertTrue(self.skill.startswith("---\n"))
        frontmatter = self.skill.split("---", 2)[1].strip().splitlines()
        keys = [line.split(":", 1)[0] for line in frontmatter]
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("name: nuts", frontmatter)
        description = next(
            line for line in frontmatter if line.startswith("description:")
        )
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

    def test_plan_premises_and_durable_destination_are_explicit(self):
        text = normalized(self.plan).casefold()
        for phrase in [
            "object users actually run or receive",
            "command that could falsify the premise",
            "negative existence claim",
            "smaller no-build answer",
            "share a deeper cause",
            "resolve its durable destination before leaving plan",
            "write the exact reviewed bytes once",
            "require exact byte equality",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertIn(
            "zero-obligation run inspects no unused owner surface",
            normalized(self.evidence).casefold(),
        )

    def test_testing_contract_names_real_red_and_cleanup_evidence(self):
        testing = normalized(
            (SKILL_ROOT / "references" / "reviewers" / "testing.md").read_text(
                encoding="utf-8"
            )
        ).casefold()
        for phrase in [
            "environmental prerequisite",
            "observable behavior",
            "deliberate defect",
            "green no-op control",
            "isolated disposable tree",
            "cleanup failure",
        ]:
            self.assertIn(phrase, testing)

    def test_terminal_state_has_one_source_owner(self):
        runtime_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(SKILL_ROOT.rglob("*.md"))
            if path.is_file()
        )
        self.assertEqual(runtime_text.count("## Terminal Summary Contract"), 1)
        phase_floor = self.evidence.split(
            "## Phase Evidence Floor\n", 1
        )[1].split("\n## ", 1)[0]
        self.assertIn("sole owner of terminal-state derivation", phase_floor)
        self.assertIn(
            "Current after the last FLAG, owner, or reviewed-target change",
            phase_floor,
        )
        self.assertIn("It never supplies prior phase evidence", phase_floor)

    def test_temporary_evidence_and_conversation_fallback_are_explicit(self):
        fixture = load_json("runs/privacy-cases.json")
        combined = normalized(self.skill + self.evidence).casefold()
        for item in fixture["allowed"] + fixture["excluded"]:
            with self.subTest(item=item):
                self.assertIn(item.casefold(), combined)
        for item in fixture["sidecar_acceptance"] + fixture["fallback_cases"]:
            with self.subTest(item=item):
                self.assertIn(item.casefold(), combined)
        self.assertIn(fixture["fallback_disclosure"].casefold(), combined)
        self.assertIn(fixture["retained_default"].casefold(), combined)
        self.assertIn(fixture["sensitive_handling"].casefold(), combined)
        self.assertNotIn(fixture["seeded_sensitive_value"].casefold(), combined)

    def test_human_gate_and_late_user_direction_have_one_source_owner(self):
        runtime_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(SKILL_ROOT.rglob("*.md"))
            if path.is_file()
        )
        combined = normalized(runtime_text).casefold()
        self.assertEqual(self.evidence.count("### Human-gate admission"), 1)
        self.assertEqual(runtime_text.count("Still proceed?"), 1)
        for phrase in [
            "authoritative provenance",
            "material choice or risk delta",
            "already-authorized effects need no new human gate",
            "runner-owned `fix`",
            "cannot create human authority",
            "does not by itself show awareness of that hidden cost",
            "already acknowledged that restart or revalidation consequence",
            "agent-discovered correction follows existing authority",
            "genuinely new effect or authority remains independently gated",
        ]:
            with self.subTest(contract_phrase=phrase):
                self.assertIn(phrase.casefold(), combined)

    def test_completion_boundary_has_one_canonical_phase_route(self):
        runtime_files = [
            path for path in sorted(SKILL_ROOT.rglob("*.md")) if path.is_file()
        ]
        runtime_text = "\n".join(
            path.read_text(encoding="utf-8") for path in runtime_files
        )
        self.assertEqual(runtime_text.count("## Completion-Boundary Routing"), 1)

        route_section = self.evidence.split(
            "## Completion-Boundary Routing\n", 1
        )[1].split("\n## ", 1)[0]
        rows = [
            tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            for line in route_section.splitlines()
            if line.startswith("|") and "---" not in line
        ]
        self.assertTrue(rows)
        self.assertTrue(all(len(row) == 5 for row in rows))
        row_labels = [row[0] for row in rows[1:]]
        self.assertEqual(len(row_labels), len(set(row_labels)))
        self.assertEqual(
            row_labels,
            [
                "Before Critique",
                "During or after Critique and before Review",
                "After Review begins and before terminal closeout (Review, post-audit, Compound, Log Debt, or Summary)",
            ],
        )
        late_row = rows[-1]
        self.assertIn("Audit (post-implement) → Compound → Log Debt → derive terminal state → Summary", late_row[2])
        self.assertIn("Review until convergence → Compound → Log Debt → derive terminal state → Summary", late_row[4])
        self.assertIn("Every already-produced phase result after Plan", late_row[1])
        self.assertIn("Every already-produced phase result after Plan", late_row[3])

        folded_route = normalized(route_section).casefold()
        for phrase in (
            "actionable concern found during critique or any later phase",
            "a plan assertion is not authority by itself",
            "without provenance in user direction, governing policy, safety, or correctness necessary to the objective",
            "remove or narrow that guarantee instead of hardening machinery",
            "finding and current pass remain nonzero",
            "plan mutation requires fresh complete critique",
        ):
            with self.subTest(completion_boundary_contract=phrase):
                self.assertIn(phrase, folded_route)

        for relative in (
            "references/plan.md",
            "references/review.md",
            "references/audit.md",
            "references/auditors/triage.md",
        ):
            text = normalized((SKILL_ROOT / relative).read_text(encoding="utf-8"))
            self.assertIn(
                "canonical Completion-Boundary Routing in `evidence-and-claims.md`",
                text,
            )

        folded_runtime = runtime_text.casefold()
        for phrase in (
            "operating horizon",
            "current-tranche",
            "successful tranche",
            "required_now",
            "authorized_rescope",
            "separately_owned",
            "second-material-rescope",
            "gate_admitted",
            "scope-routing-cases",
            "material freeze",
            "`defer`",
        ):
            with self.subTest(forbidden_scope_engine=phrase):
                self.assertNotIn(phrase, folded_runtime)

    def test_runtime_and_public_instructions_have_no_project_local_run_path(self):
        public_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        combined = (self.skill + self.evidence + self.review + public_readme).casefold()
        self.assertNotIn(".nuts/runs", combined)
        self.assertNotIn(".nuts/", gitignore.casefold())
        self.assertIn("creates no project-local run-evidence directory by default", combined)
        self.assertIn("temporary working sidecar", combined)

    def test_flag_debt_summary_and_custody_contracts_are_structurally_distinct(self):
        text = normalized(self.evidence).casefold()
        for phrase in [
            "repeated reports of the same decision boundary reuse the same id",
            "undisposed` must be zero before successful closeout",
            "summary emission is not successful closeout",
            "beginner-facing paragraph",
            "compact technical receipt",
            "redacted notice without private custody is not a disposition",
            "zero-obligation run inspects no unused owner surface",
            "restricted closeout-only custody path",
        ]:
            self.assertIn(phrase, text)

        for case in load_json("runs/private-record-cases.json"):
            with self.subTest(private_record=case["name"]):
                self.assertEqual(
                    private_record_is_minimal(case["record"]), case["accepted"]
                )
        self.assertTrue(
            private_reference_is_bound(
                {
                    "private_owner_ref": "owner-1",
                    "outward_reference_owner_ref": "owner-1",
                }
            )
        )
        self.assertFalse(
            private_reference_is_bound(
                {
                    "private_owner_ref": "owner-1",
                    "outward_reference_owner_ref": "owner-2",
                }
            )
        )

        for case in load_json("runs/summary-cases.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(
                    summary_is_accepted(case, case["terminal_claim"]),
                    case["accepted"],
                )

    def test_runtime_instruction_tree_has_no_private_or_cut_mechanism_edges(self):
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(SKILL_ROOT.rglob("*"))
            if path.is_file()
        ).casefold()
        for term in (
            "checkpoint engine",
            "active-run marker",
            "replay system",
            "pass budget",
            "restart engine",
        ):
            self.assertNotIn(term, text)
        self.assertFalse(any(SKILL_ROOT.rglob("*.py")))

    def test_invalidation_routes_cover_post_zero_mutations(self):
        for phrase in [
            "Completion-Boundary Routing",
            "During or after Critique and before Review",
            "After Review begins and before terminal closeout",
            "post-audit FIX changes the target",
            "Full Compound creates or updates",
            "Light Compound creates or updates",
            "new material FLAG appears after Log Debt",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.evidence)

    def test_mixed_target_keeps_one_reference_and_one_convergence_decision(self):
        review = normalized(self.review)
        for phrase in [
            "One `target_ref` binds the whole current target",
            "Assign `target_kind` per selected protocol",
            "sharing the exact same whole-target reference",
            "one coordinated pass with one pass state and one convergence decision",
            "Do not add a `mixed` kind",
            "let a seat's kind hide the other parts",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, review)

        for phrase in [
            "entire selected named protocol against the whole current target",
            "canonical Completion-Boundary Routing in `evidence-and-claims.md`",
            "does not rewrite the boundary or grant mutation",
            "Inspection stays broad while mutation stays bounded by the recorded Plan",
        ]:
            self.assertIn(phrase, review)


if __name__ == "__main__":
    unittest.main()
