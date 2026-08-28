import json
import re
import unittest
from collections import Counter
from pathlib import Path

from support import (
    is_count,
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


def earned_claim(case, ledgers, custody_cases):
    required_obligations = {"full": 9, "light": 7}.get(case["selected_mode"])
    ledger = ledgers[case["debt_case"]]
    common = (
        required_obligations is not None
        and case["expected_obligations"] == required_obligations
        and case["completed_obligations"] == required_obligations
        and case["current_zero_passes"] is True
        and case["verification_green"] is True
        and case["workers_running"] is False
        and ledger_reconciles(ledger, custody_cases)
        and ledger["undisposed"] == 0
        and (
            case["planning_run"] is False
            or (
                case["planning_run"] is True
                and case.get("plan_durable") is True
            )
        )
        and case["compound_blocked"] is False
        and case["summary_reconciled"] is True
    )
    if not common:
        return "incomplete"
    if case["selected_mode"] == "full" and case["audits_current"] is True:
        return "Full"
    if case["selected_mode"] == "light":
        return "Light"
    return "incomplete"


def ledger_reconciles(case, custody_cases):
    canonical_ids = case["canonical_ids"]
    disposed = case["dispositions"]
    undisposed_ids = case["undisposed_ids"]
    declared_counts = case["declared_counts"]
    if (
        not isinstance(canonical_ids, list)
        or not isinstance(disposed, list)
        or not isinstance(undisposed_ids, list)
        or not isinstance(declared_counts, dict)
        or not all(isinstance(flag_id, str) for flag_id in canonical_ids)
        or not all(isinstance(flag_id, str) for flag_id in undisposed_ids)
        or not all(
            isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and isinstance(item.get("disposition"), str)
            for item in disposed
        )
    ):
        return False
    all_ids = [item["id"] for item in disposed] + undisposed_ids
    actual_counts = Counter(item["disposition"] for item in disposed)
    exact_dispositions = {"RESOLVED_IN_RUN", "IMPLEMENTED", "ACCEPTED_BOUNDARY"}
    parameterized_prefixes = ("DEBT:", "BACKLOG:", "GATE:", "DROPPED:")

    def valid_disposition(value):
        if not isinstance(value, str):
            return False
        if value in exact_dispositions:
            return True
        return any(
            value.startswith(prefix) and bool(value[len(prefix) :].strip())
            for prefix in parameterized_prefixes
        )

    def required_true(record, fields):
        return (
            isinstance(record, dict)
            and fields <= set(record)
            and all(record[field] is True for field in fields)
        )

    def valid_receipt(item):
        disposition = item["disposition"]
        evidence = item.get("evidence")
        if disposition == "RESOLVED_IN_RUN":
            return (
                required_true(evidence, {"decision_recorded", "settles_boundary"})
                and evidence.get("mapped_id") == item["id"]
            )
        if disposition == "IMPLEMENTED":
            return (
                required_true(evidence, {"changed", "verified", "complete_requirement"})
                and evidence.get("mapped_id") == item["id"]
            )
        if disposition == "ACCEPTED_BOUNDARY":
            return (
                required_true(evidence, {"explicit_acceptance"})
                and evidence.get("mapped_id") == item["id"]
            )
        if disposition.startswith(("DEBT:", "BACKLOG:", "GATE:")):
            disposition_ref = disposition.split(":", 1)[1].strip()
            custody = custody_cases.get(evidence.get("custody_case"), {}) if isinstance(evidence, dict) else {}
            return (
                isinstance(evidence, dict)
                and evidence.get("mapped_id") == item["id"]
                and evidence.get("disposition_ref") == disposition_ref
                and evidence.get("custody_case") in custody_cases
                and item["id"] in custody.get("canonical_ids", [])
                and custody.get("custody_id") == item["id"]
                and custody.get("destination_ref") == disposition_ref
                and not custody.get("resolved_in_run", False)
                and "classification" in custody
                and flag_is_disposed(custody)
            )
        if disposition.startswith("DROPPED:"):
            reason = disposition.split(":", 1)[1].strip()
            return (
                required_true(evidence, {"authorized_removal", "supporting_evidence"})
                and evidence.get("mapped_id") == item["id"]
                and evidence.get("reason") == reason
            )
        return False

    declared_counts_valid = all(
        valid_disposition(disposition)
        and isinstance(count, int)
        and not isinstance(count, bool)
        and count > 0
        for disposition, count in declared_counts.items()
    )
    custody_links = [
        item.get("evidence", {}).get("custody_case")
        for item in disposed
        if item["disposition"].startswith(("DEBT:", "BACKLOG:", "GATE:"))
    ]

    return (
        is_count(case["raised"])
        and is_count(case["undisposed"])
        and case["raised"] == len(canonical_ids)
        and canonical_ids == [f"F{index}" for index in range(1, case["raised"] + 1)]
        and len(set(canonical_ids)) == len(canonical_ids)
        and Counter(all_ids) == Counter(canonical_ids)
        and all(valid_disposition(item["disposition"]) for item in disposed)
        and all(valid_receipt(item) for item in disposed)
        and len(custody_links) == len(set(custody_links))
        and declared_counts_valid
        and actual_counts == Counter(declared_counts)
        and case["undisposed"] == len(undisposed_ids)
        and sum(declared_counts.values()) + case["undisposed"] == case["raised"]
    )


def goal_actions(case):
    effect = case["effect"]
    finish_effect = case["finish_effect"]
    update_effect = case["update_effect"]
    if effect not in {"certain", "rejected", "uncertain"}:
        effect = "uncertain"
    if finish_effect not in {"certain", "rejected", "uncertain"}:
        finish_effect = "uncertain"
    if update_effect not in {"not_attempted", "certain", "rejected", "uncertain"}:
        update_effect = "uncertain"
    if case["nuts_invoked"] is not True:
        start = "none"
    elif case["host"] not in {"available", "accepts_invocation"}:
        start = "report_once_continue"
    elif effect == "uncertain":
        start = "freeze_after_effect"
    elif case["existing"] in {"stable_same_run", "exact_user_designation"}:
        start = "bind"
    elif case["existing"] in {"similar_text", "ambiguous", "unrelated"}:
        start = "preserve_continue"
    elif case["host"] == "accepts_invocation" and case["existing"] == "none":
        start = "create_once"
    else:
        start = "report_once_continue"
    start_attempted = start in {"create_once", "bind", "freeze_after_effect"}
    bound = start in {"create_once", "bind"} and effect == "certain"
    update_attempted = bound and update_effect != "not_attempted"
    update_blocks_close = update_attempted and update_effect != "certain"
    close_attempted = (
        bound and not update_blocks_close and case["closeout"] == "complete"
    )
    finish = "close" if close_attempted and finish_effect == "certain" else "none"
    uncertain_effect = (
        (start_attempted and effect == "uncertain")
        or (update_attempted and update_effect == "uncertain")
    ) or (
        close_attempted and finish_effect == "uncertain"
    )
    known_rejection = (
        (start_attempted and effect == "rejected")
        or (update_attempted and update_effect == "rejected")
        or (close_attempted and finish_effect == "rejected")
    )
    report = (
        "report_once"
        if start == "report_once_continue" or known_rejection or uncertain_effect
        else "none"
    )
    if uncertain_effect:
        later_mutation = "frozen"
    elif bound and finish != "close":
        later_mutation = "bound"
    else:
        later_mutation = "none"
    return start, finish, report, later_mutation


def destination_result(case):
    if case["stage"] not in {"owner_discovery", "selection", "write"}:
        return "invalid"
    if case["stage"] == "owner_discovery":
        no_effect = not any(case[name] for name in ("contacts", "transmissions", "mutations"))
        return "ambiguous_no_effect" if not case["declared_precedence"] and no_effect else "invalid"
    if case["stage"] == "selection":
        source = case["source"]
        if source == "explicit":
            return "explicit" if case["eligible"] is True else "rejected_no_fallback"
        if source == "incidental":
            return "ignored"
        if source == "explicit_handoff":
            return "handoff" if case["eligible"] is True else "rejected_no_fallback"
        if source == "host":
            qualified = case["eligible"] is True and all(
                case[name] is True
                for name in (
                    "retained",
                    "retrievable",
                    "collision_safe",
                    "exact_readback",
                    "privacy_known",
                    "sharing_authorized",
                    "stable_nonsecret_locator",
                )
            )
            return "host" if qualified else "rejected_no_fallback"
        if source == "automatic_fallback":
            return "next_qualified" if case["eligible"] is True else "fail_before_critique"
        if source == "automatic":
            available = case["available"]
            priority = ("plan", "handoff", "nearby_plan", "host")
            if (
                case["eligible"] is not True
                or not isinstance(available, list)
                or not available
                or len(available) != len(set(available))
                or not set(available) <= set(priority)
            ):
                return "fail_before_critique"
            return next(candidate for candidate in priority if candidate in available)
        return "invalid"
    if case.get("after_effect"):
        effect = case.get("effect")
        if effect in {"failed", "partial", "mismatched", "uncertain"}:
            return "preserve_first_incomplete"
        if effect != "success":
            return "invalid"
    if not isinstance(case.get("after_effect"), bool):
        return "incomplete"
    if case.get("destination_kind") not in {"repository", "external_user_path"}:
        return "incomplete"
    if not isinstance(case.get("exists"), bool):
        return "incomplete"
    repository_safe = (
        case["destination_kind"] != "repository"
        or case.get("single_writer") is True
    )
    if not case["exists"]:
        safe = (
            case["parent_safe"] is True
            and case["exclusive_create"] is True
            and case["collision"] is False
            and case["identity_stable"] is True
            and case["exact_readback"] is True
            and case["post_write_parent_stable"] is True
            and case["post_write_access_safe"] is True
            and repository_safe
        )
        return "eligible_write" if safe else "incomplete"
    write_method_safe = case.get("identity_bound") is True or (
        case.get("destination_kind") == "repository"
        and case.get("atomic_replacement") is True
    )
    safe_existing = (
        case["parent_safe"] is True
        and case["authorized"] is True
        and case["file_type"] == "regular"
        and is_count(case["links"])
        and case["links"] == 1
        and write_method_safe
        and case["identity_stable"] is True
        and case["exact_readback"] is True
        and case["post_write_parent_stable"] is True
        and case["post_write_access_safe"] is True
        and repository_safe
    )
    return "eligible_write" if safe_existing else "incomplete"


def flag_is_disposed(case):
    owner_fields = {
        "authorized",
        "routinely_checked",
        "authoritative_surface",
        "operator_ingestion",
        "stable_locator",
        "responsible_owner",
        "next_gate",
        "closure",
        "retention",
        "write_certain",
        "readback",
    }
    plan_gate_fields = {
        "authorized",
        "routinely_checked",
        "authoritative_surface",
        "operator_ingestion",
        "reviewed_locator",
        "responsible_owner",
        "next_action",
        "closure",
        "retention",
        "write_certain",
        "readback",
    }
    if (
        not is_count(case.get("raised"))
        or not is_count(case.get("writes"))
        or not isinstance(case.get("discovery"), bool)
        or case["raised"] != len(case.get("canonical_ids", []))
    ):
        return False
    if case["raised"] == 0:
        return case["discovery"] is False and case["writes"] == 0
    if case.get("resolved_in_run") is True:
        return (
            case.get("resolution_recorded") is True
            and case.get("settles_boundary") is True
            and case["discovery"] is False
            and case["writes"] == 0
        )
    classification = case.get("classification")
    classification_fields = {"sensitive", "custody_kind"}
    if (
        not classification
        or not classification_fields <= set(classification)
        or not isinstance(classification["sensitive"], bool)
        or classification["custody_kind"] not in {"native", "external", "reviewed_plan"}
    ):
        return False
    if "multiple_candidates" in case and not isinstance(
        case["multiple_candidates"], bool
    ):
        return False
    if case.get("multiple_candidates") is True and case.get("declared_precedence") is not True:
        return False
    if "plan_gate" in case:
        if case["discovery"] is not True or case["writes"] != 0:
            return False
        if classification["custody_kind"] != "reviewed_plan":
            return False
        gate = case["plan_gate"]
        gate_valid = plan_gate_fields <= set(gate) and all(
            gate[field] is True for field in plan_gate_fields
        )
        if classification["sensitive"]:
            gate_valid = (
                gate_valid
                and case.get("private_custody") is True
                and case.get("safe_outward_reference") is True
                and private_record_is_minimal(case.get("private_record"))
                and private_reference_is_bound(case)
            )
        return gate_valid
    if case["discovery"] is not True or case["writes"] != 1:
        return False
    if "candidate_failed_prewrite" in case and not isinstance(
        case["candidate_failed_prewrite"], bool
    ):
        return False
    if (
        case.get("candidate_failed_prewrite") is True
        and case.get("fallback_before_write") is not True
    ):
        return False
    owner = case.get("owner")
    if (
        not owner
        or not owner_fields <= set(owner)
        or not all(owner[field] is True for field in owner_fields)
    ):
        return False
    if classification["sensitive"] and not (
        case.get("private_custody") is True
        and case.get("safe_outward_reference") is True
        and private_record_is_minimal(case.get("private_record"))
        and private_reference_is_bound(case)
    ):
        return False
    if classification["custody_kind"] == "external":
        if "external" not in case:
            return False
        external_fields = {
            "service_identity",
            "recipient_authorized",
            "transport_verified",
            "effects_authorized",
            "response_instructions_ignored",
        }
        external = case["external"]
        if not external_fields <= set(external) or not all(
            external[field] is True for field in external_fields
        ):
            return False
    elif classification["custody_kind"] != "native" or "external" in case:
        return False
    return True


def gate_admission(case):
    effect_fields = {
        "non_secret",
        "local_only",
        "minimized",
        "owner_private",
        "ephemeral",
        "sensitive",
        "external_sharing",
        "durable_truth",
        "provider_or_account",
        "activation",
        "publication",
        "destructive",
    }
    effect = case.get("effect")
    if (
        case.get("gate_source") not in {
            "none",
            "plan",
            "reviewer",
            "repository",
            "user",
            "governing_policy",
            "observed_effect",
        }
        or not isinstance(case.get("gate_proposed"), bool)
        or not isinstance(case.get("material_choice"), bool)
        or not isinstance(case.get("established_default_covers"), bool)
        or not isinstance(case.get("current_step_depends"), bool)
        or not isinstance(case.get("fully_informed"), bool)
        or not isinstance(effect, dict)
        or set(effect) != effect_fields
        or not all(isinstance(value, bool) for value in effect.values())
    ):
        return "blocked"
    safe_evidence = (
        all(
            effect[field]
            for field in (
                "non_secret",
                "local_only",
                "minimized",
                "owner_private",
                "ephemeral",
            )
        )
        and not any(
            effect[field]
            for field in (
                "sensitive",
                "external_sharing",
                "durable_truth",
                "provider_or_account",
                "activation",
                "publication",
                "destructive",
            )
        )
    )
    material_effect = not safe_evidence
    if (
        not case["gate_proposed"]
        and safe_evidence
        and case["established_default_covers"]
    ):
        return "proceed"
    authoritative = case["gate_source"] in {"user", "governing_policy"} or material_effect
    admissible = (
        authoritative
        and case["material_choice"]
        and not case["established_default_covers"]
        and case["current_step_depends"]
    )
    if material_effect and case["material_choice"] and case["current_step_depends"]:
        admissible = True
    if not admissible:
        return "fix"
    return "flag" if case["fully_informed"] else "disclose"


def harness_case_is_accepted(case):
    if case["trigger"] == "ordinary":
        return True
    if case["trigger"] == "skip":
        return case["skip_environment_only"] is True
    if case["trigger"] == "guard":
        return (
            case["observable_assertion"] is True
            and case["red_path"] is True
        )
    if case["trigger"] == "mutation":
        return all(
            case[name] is True
            for name in ("observable_assertion", "red_path", "no_op_green", "isolated", "cleanup")
        )
    return False


class KernelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.evidence = (
            SKILL_ROOT / "references" / "evidence-and-claims.md"
        ).read_text(encoding="utf-8")
        cls.plan = (SKILL_ROOT / "references" / "plan.md").read_text(encoding="utf-8")
        cls.testing = (
            SKILL_ROOT / "references" / "reviewers" / "testing.md"
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

    def test_goal_matrix_is_bounded_and_never_evidence(self):
        cases = load_json("runs/goal-cases.json")
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertFalse(case["goal_is_evidence"])
                self.assertFalse(case["prompt"])
                self.assertEqual(
                    goal_actions(case),
                    (
                        case["expected_start"],
                        case["expected_finish"],
                        case["expected_report"],
                        case["expected_later_mutation"],
                    ),
                )
        unauthorized = dict(
            next(case for case in cases if case["name"] == "authorized-create")
        )
        unauthorized["nuts_invoked"] = "false"
        self.assertEqual(goal_actions(unauthorized)[0], "none")
        unknown_effect = dict(
            next(case for case in cases if case["name"] == "authorized-create")
        )
        unknown_effect["effect"] = "unknown"
        self.assertEqual(
            goal_actions(unknown_effect),
            ("freeze_after_effect", "none", "report_once", "frozen"),
        )
        unknown_finish = dict(
            next(case for case in cases if case["name"] == "authorized-create")
        )
        unknown_finish["finish_effect"] = "unknown"
        self.assertEqual(
            goal_actions(unknown_finish),
            ("create_once", "none", "report_once", "frozen"),
        )
        unknown_update = dict(
            next(case for case in cases if case["name"] == "resume-no-duplicate")
        )
        unknown_update["update_effect"] = "unknown"
        self.assertEqual(
            goal_actions(unknown_update),
            ("bind", "none", "report_once", "frozen"),
        )
        combined = normalized(self.skill + self.evidence).casefold()
        self.assertIn("before plan", combined)
        self.assertIn("unrelated goal", combined)
        self.assertIn("never phase evidence", combined)
        self.assertIn("separately explicit goal request", combined)
        self.assertIn("make no later goal mutation", combined)

    def test_plan_premises_and_durable_destination_are_operational(self):
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
        for case in load_json("runs/plan-destination-cases.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(destination_result(case), case["expected"])
        destinations = {
            case["name"]: case
            for case in load_json("runs/plan-destination-cases.json")
        }
        for invalid_kind in (None, "reposotory"):
            candidate = dict(destinations["authorized-existing-plan-update"])
            if invalid_kind is None:
                candidate.pop("destination_kind")
            else:
                candidate["destination_kind"] = invalid_kind
            with self.subTest(destination_kind=invalid_kind):
                self.assertEqual(destination_result(candidate), "incomplete")
        candidate = dict(destinations["ordinary-plan-prefers-plan-path"])
        candidate["available"] = "plan"
        self.assertEqual(destination_result(candidate), "fail_before_critique")
        for field in ("after_effect", "exists"):
            candidate = dict(destinations["authorized-existing-plan-update"])
            candidate[field] = "unknown"
            with self.subTest(unknown_destination_lifecycle=field):
                self.assertNotEqual(destination_result(candidate), "eligible_write")
        candidate = dict(destinations["authorized-existing-plan-update"])
        candidate["links"] = True
        self.assertEqual(destination_result(candidate), "incomplete")
        for field in (
            "parent_safe",
            "exclusive_create",
            "identity_stable",
            "exact_readback",
            "post_write_parent_stable",
            "post_write_access_safe",
            "single_writer",
        ):
            candidate = dict(destinations["exclusive-new-file"])
            candidate[field] = "unknown"
            with self.subTest(nonboolean_destination_evidence=field):
                self.assertEqual(destination_result(candidate), "incomplete")
        self.assertIn("zero-obligation run inspects no unused owner surface", normalized(self.evidence).casefold())

    def test_conditional_harness_rules_reject_false_green(self):
        cases = {case["name"]: case for case in load_json("runs/testing-cases.json")}
        for case in cases.values():
            with self.subTest(case=case["name"]):
                self.assertEqual(harness_case_is_accepted(case), case["accepted"])
        for field in (
            "observable_assertion",
            "red_path",
            "no_op_green",
            "isolated",
            "cleanup",
        ):
            candidate = dict(cases["isolated-complete-harness"])
            candidate[field] = "unknown"
            with self.subTest(nonboolean_harness_evidence=field):
                self.assertFalse(harness_case_is_accepted(candidate))
        text = normalized(self.testing).casefold()
        for phrase in [
            "environmental prerequisite",
            "observable behavior",
            "deliberate defect",
            "green no-op control",
            "isolated disposable tree",
            "cleanup failure",
        ]:
            self.assertIn(phrase, text)

    def test_claim_oracle_never_downgrades_failed_full(self):
        cases = load_json("runs/claim-cases.json")
        ledgers = {
            case["name"]: case for case in load_json("runs/debt-cases.json")
        }
        custody_cases = {
            case["name"]: case for case in load_json("runs/flag-cases.json")
        }
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertEqual(
                    earned_claim(case, ledgers, custody_cases), case["expected_claim"]
                )
        failed_full = next(case for case in cases if case["name"] == "failed-full-never-light")
        self.assertEqual(
            earned_claim(failed_full, ledgers, custody_cases), "incomplete"
        )
        earned_full = next(case for case in cases if case["name"] == "earned-full")
        for field in (
            "current_zero_passes",
            "audits_current",
            "verification_green",
            "workers_running",
            "planning_run",
            "compound_blocked",
            "summary_reconciled",
        ):
            candidate = dict(earned_full)
            candidate[field] = "unknown"
            with self.subTest(nonboolean_closeout_evidence=field):
                self.assertEqual(
                    earned_claim(candidate, ledgers, custody_cases), "incomplete"
                )
        planning = next(case for case in cases if case["name"] == "planning-plan-durable")
        candidate = dict(planning)
        candidate["plan_durable"] = "unknown"
        self.assertEqual(earned_claim(candidate, ledgers, custody_cases), "incomplete")
        for field in ("workers_running", "planning_run", "compound_blocked"):
            candidate = dict(earned_full)
            candidate[field] = 0
            with self.subTest(falsey_nonboolean_closeout=field):
                self.assertEqual(
                    earned_claim(candidate, ledgers, custody_cases), "incomplete"
                )

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

    def test_human_gate_admission_preserves_autonomy_and_real_stops(self):
        cases = load_json("runs/gate-admission-cases.json")
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertEqual(gate_admission(case), case["expected"])
        combined = normalized(
            self.skill
            + self.plan
            + self.evidence
            + (SKILL_ROOT / "references" / "audit.md").read_text(encoding="utf-8")
            + (SKILL_ROOT / "references" / "auditors" / "triage.md").read_text(encoding="utf-8")
            + (SKILL_ROOT / "references" / "auditors" / "verification.md").read_text(encoding="utf-8")
        ).casefold()
        for phrase in [
            "authoritative provenance",
            "material choice or risk delta",
            "safe evidence envelope",
            "runner-owned `fix`",
            "earliest informed boundary",
            "cannot create human authority",
        ]:
            with self.subTest(contract_phrase=phrase):
                self.assertIn(phrase, combined)

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
        blocked = next(case for case in cases if case["name"] == "unordered-owners-block")
        self.assertFalse(flag_is_disposed(blocked))
        for ledger in load_json("runs/debt-cases.json"):
            with self.subTest(ledger=ledger["name"]):
                custody_cases = {
                    case["name"]: case
                    for case in load_json("runs/flag-cases.json")
                }
                self.assertEqual(
                    ledger_reconciles(ledger, custody_cases), ledger["reconciles"]
                )
        ledger = next(
            case for case in load_json("runs/debt-cases.json")
            if case["name"] == "one-undisposed"
        )
        for field in ("raised", "undisposed"):
            candidate = dict(ledger)
            candidate[field] = True
            with self.subTest(boolean_debt_count=field):
                self.assertFalse(ledger_reconciles(candidate, custody_cases))
        evidence = normalized(self.evidence)
        self.assertIn("Repeated reports of the same decision boundary reuse the same ID", evidence)
        self.assertIn("undisposed` must be zero before successful closeout", evidence)

    def test_closeout_summary_and_custody_are_distinct(self):
        text = normalized(self.evidence).casefold()
        for phrase in [
            "summary emission is not successful closeout",
            "beginner-facing paragraph",
            "compact technical receipt",
            "redacted notice without private custody is not a disposition",
            "zero-obligation run inspects no unused owner surface",
            "restricted closeout-only custody path",
            "newly enforced",
            "newly documented",
        ]:
            self.assertIn(phrase, text)
        flags = {case["name"]: case for case in load_json("runs/flag-cases.json")}
        for case in flags.values():
            with self.subTest(flag_case=case["name"]):
                self.assertEqual(flag_is_disposed(case), case["expected_disposed"])
                self.assertEqual(len(case["canonical_ids"]), case["raised"])
                self.assertEqual(len(set(case["canonical_ids"])), case["raised"])
                self.assertEqual(
                    case["canonical_ids"],
                    [f"F{index}" for index in range(1, case["raised"] + 1)],
                )
        candidate = dict(flags["reviewed-plan-gate-owner"])
        candidate["discovery"] = False
        self.assertFalse(flag_is_disposed(candidate))
        candidate = dict(flags["repeat-reuses-id"])
        candidate["writes"] = 1
        self.assertFalse(flag_is_disposed(candidate))
        for name in (
            "private-custody-with-safe-reference",
            "sensitive-private-reviewed-plan-gate",
        ):
            candidate = dict(flags[name])
            candidate["outward_reference_owner_ref"] = "owner-2"
            with self.subTest(mismatched_private_owner=name):
                self.assertFalse(flag_is_disposed(candidate))
        for case in load_json("runs/private-record-cases.json"):
            with self.subTest(private_record=case["name"]):
                self.assertEqual(
                    private_record_is_minimal(case["record"]), case["accepted"]
                )
                integrated = dict(flags["private-custody-with-safe-reference"])
                integrated["private_record"] = case["record"]
                self.assertEqual(flag_is_disposed(integrated), case["accepted"])
        self.assertFalse(flags["zero-flags-no-artifact"]["discovery"])
        self.assertEqual(flags["safety-stop-restricted-custody"]["affected_work_after_stop"], 0)
        self.assertFalse(flags["redacted-notice-without-custody"]["expected_disposed"])
        self.assertEqual(flags["uncertain-write-no-duplicate"]["duplicate_writes"], 0)
        claim_cases = {
            case["name"]: case for case in load_json("runs/claim-cases.json")
        }
        debt_cases = {
            case["name"]: case for case in load_json("runs/debt-cases.json")
        }
        custody_cases = {
            case["name"]: case for case in load_json("runs/flag-cases.json")
        }

        def summary_accepts(case):
            claim_case = case.get(
                "claim_case",
                "earned-full"
                if case["run_status"] == "complete"
                else "failed-full-never-light",
            )
            terminal_claim = earned_claim(
                claim_cases[claim_case], debt_cases, custody_cases
            )
            return summary_is_accepted(case, terminal_claim)

        for case in load_json("runs/summary-cases.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(summary_accepts(case), case["accepted"])
        accepted_summary = next(
            case for case in load_json("runs/summary-cases.json")
            if case["name"] == "complete-two-layer"
        )
        for field in (
            "facts_agree",
            "self_contained",
            "receipt_ids",
            "sensitive_metadata_exposed",
        ):
            candidate = dict(accepted_summary)
            candidate[field] = "unknown"
            with self.subTest(nonboolean_summary_evidence=field):
                self.assertFalse(summary_accepts(candidate))
        candidate = dict(accepted_summary)
        candidate["no_failure_stated"] = "unknown"
        self.assertFalse(summary_accepts(candidate))
        corrected_summary = next(
            case for case in load_json("runs/summary-cases.json")
            if case["name"] == "corrected-failure-with-evidence"
        )
        candidate = dict(corrected_summary)
        candidate["correcting_evidence"] = "unknown"
        self.assertFalse(summary_accepts(candidate))
        candidate = dict(accepted_summary)
        candidate["sensitive_metadata_exposed"] = 0
        self.assertFalse(summary_accepts(candidate))
        beginner_omits = next(
            case for case in load_json("runs/summary-cases.json")
            if case["name"] == "beginner-omits-technical-counts"
        )
        self.assertFalse(beginner_omits["beginner_ids"])
        self.assertTrue(beginner_omits["receipt_ids"])
        self.assertTrue(beginner_omits["accepted"])
        summary_contract = normalized(self.evidence).casefold()
        for phrase in (
            "derive one terminal state",
            "cannot upgrade or downgrade",
            "before summary wording",
        ):
            self.assertIn(phrase, summary_contract)

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

    def test_complete_review_scope_and_mutation_authority_remain_separate(self):
        review = normalized(
            (SKILL_ROOT / "references" / "review.md").read_text(encoding="utf-8")
        )
        for phrase in [
            "entire selected named protocol against the whole current target",
            "neither a whole-target assignment nor a finding grants",
            "violation of the settled boundary is actionable",
            "genuinely adjacent enhancement",
            "preserve it outside `findings`",
            "does not require a durable repository work item",
            "only a fresh complete pass may later report zero actionable findings",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, review)


if __name__ == "__main__":
    unittest.main()
