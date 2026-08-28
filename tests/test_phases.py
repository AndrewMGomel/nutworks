import json
import unittest
from pathlib import Path, PurePosixPath

from support import is_count, private_record_is_minimal, private_reference_is_bound


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


def compound_outcome(case):
    if case["phase_evidence_available"] is not True:
        return "blocked"
    if not is_count(case.get("project_writes")) or not isinstance(
        case.get("requires_review"), bool
    ):
        return "blocked"
    material = (
        case["candidate_evidence"] is True
        and case["uncaptured"] is True
        and isinstance(case["prevented_repeat"], str)
        and bool(case["prevented_repeat"].strip())
    )
    if not material:
        return (
            "no_op"
            if case["project_writes"] == 0 and case["requires_review"] is False
            else "blocked"
        )
    if case["route"] in {"create", "update", "forward"} and not isinstance(
        case.get("sensitive"), bool
    ):
        return "blocked"
    if case["route"] in {"create", "update"}:
        destination_ready = all(
            case.get(field) is True
            for field in (
                "declared_truth_owner",
                "write_authorized",
                "privacy_qualified",
                "semantic_readback",
            )
        )
        if case.get("sensitive") is True:
            destination_ready = (
                destination_ready
                and case.get("private_custody") is True
                and case.get("safe_outward_reference") is True
                and private_record_is_minimal(case.get("private_record"))
                and private_reference_is_bound(case)
            )
        success = "created" if case["route"] == "create" else "updated"
        return (
            success
            if destination_ready
            and case["project_writes"] == 1
            and case["requires_review"] is True
            else "blocked"
        )
    if case["route"] == "forward":
        custody_kind = case.get("custody_kind")
        if custody_kind not in {"external", "repository"}:
            return "blocked"
        sensitive = case["sensitive"]
        owner = case.get("owner")
        required = {
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
        complete = (
            owner
            and required <= set(owner)
            and all(owner[field] is True for field in required)
        )
        if sensitive:
            complete = (
                complete
                and case.get("private_custody") is True
                and case.get("safe_outward_reference") is True
                and private_record_is_minimal(case.get("private_record"))
                and private_reference_is_bound(case)
            )
        if custody_kind == "external":
            external_required = {
                "service_identity",
                "recipient_authorized",
                "transport_verified",
                "effects_authorized",
                "response_instructions_ignored",
            }
            external = case.get("external")
            complete = (
                complete
                and external
                and external_required <= set(external)
                and all(external[field] is True for field in external_required)
                and case["project_writes"] == 0
                and case["requires_review"] is False
            )
        else:
            complete = (
                complete
                and case["project_writes"] == 1
                and case["requires_review"] is True
            )
        return "forwarded_candidate" if complete else "blocked"
    return "blocked"


def residual_disposition_allowed(case):
    if case["classification"] not in {"PRODUCT", "GUARD", "HARNESS"}:
        return False
    if case["disposition"] not in {"FIX", "FLAG", "ACCEPT", "DEBT"}:
        return False
    if case["classification"] in {"GUARD", "HARNESS"} and case["disposition"] in {
        "ACCEPT",
        "DEBT",
    }:
        return (
            case["outside_product_contract"] is True
            and case["fail_closed"] is True
        )
    return True


def selection_result(case):
    if case["mode"] not in {"full", "light"}:
        return "invalid"
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
        if (
            not isinstance(receipt["target_ref"], str)
            or not receipt["target_ref"].strip()
        ):
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
    if not isinstance(case, dict) or not isinstance(packets, dict):
        return "unfinished"
    if not isinstance(case.get("target_ref"), str) or not case["target_ref"].strip():
        return "unfinished"
    if not isinstance(case.get("target_kind"), str) or not case["target_kind"].strip():
        return "unfinished"
    selected = case.get("selected")
    if (
        not isinstance(selected, list)
        or not selected
        or not all(isinstance(seat, str) and seat for seat in selected)
        or len(selected) != len(set(selected))
    ):
        return "unfinished"
    returns = case.get("returns", [])
    if not isinstance(returns, list):
        return "unfinished"
    by_seat = {seat: [] for seat in selected}
    for returned in returns:
        if not isinstance(returned, dict):
            return "unfinished"
        seat = returned.get("seat")
        if not isinstance(seat, str):
            return "unfinished"
        if seat in by_seat:
            by_seat[seat].append(returned)

    eligible_packets = []
    contexts = []
    for seat in selected:
        seat_returns = by_seat[seat]
        if len(seat_returns) != 1:
            return "unfinished"
        returned = seat_returns[0]
        packet_ref = returned.get("packet")
        if not isinstance(packet_ref, str) or not packet_ref or packet_ref not in packets:
            return "unfinished"
        packet = packets[packet_ref]
        if not finding_packet_is_valid(packet):
            return "unfinished"
        if packet["reviewer"] != seat or seat not in BENCH:
            return "unfinished"
        receipt = packet["review_receipt"]
        if returned.get("dispatch_mode") != "complete_protocol":
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
        contexts.append(
            (
                returned.get("context"),
                returned.get("context_verified") is True,
            )
        )

    if case.get("requires_independence") and (
        not all(
            isinstance(context, str) and bool(context.strip()) and verified
            for context, verified in contexts
        )
        or len({context.strip() for context, _ in contexts}) != len(contexts)
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
        nonstring_path = json.loads(
            json.dumps(packets["coherence-complete-nonzero-r1"])
        )
        nonstring_path["target_kind"] = "code"
        nonstring_path["findings"][0]["location"] = {
            "kind": "code",
            "path": 0,
            "line": 1,
        }
        self.assertFalse(finding_packet_is_valid(nonstring_path))
        for phase in ("critique", "review"):
            for case in fixture["cases"]:
                with self.subTest(phase=phase, case=case["name"]):
                    self.assertEqual(pass_result(case, packets), case["expected"])
        valid_case = next(
            case for case in fixture["cases"]
            if case["name"] == "all-selected-complete-current-zero"
        )
        blank_context = json.loads(json.dumps(valid_case))
        blank_context["returns"][0]["context"] = "   "
        self.assertEqual(pass_result(blank_context, packets), "unfinished")
        unverified_context = json.loads(json.dumps(valid_case))
        unverified_context["returns"][0]["context_verified"] = False
        self.assertEqual(pass_result(unverified_context, packets), "unfinished")
        blank_ref_case = json.loads(json.dumps(valid_case))
        blank_ref_case["target_ref"] = "   "
        blank_ref_packets = json.loads(json.dumps(packets))
        for returned in blank_ref_case["returns"]:
            blank_ref_packets[returned["packet"]]["review_receipt"]["target_ref"] = "   "
        self.assertEqual(pass_result(blank_ref_case, blank_ref_packets), "unfinished")
        for malformed_return in (None, {}, {"packet": "coherence-complete-zero-r2"}):
            malformed_case = json.loads(json.dumps(valid_case))
            malformed_case["returns"] = [malformed_return]
            with self.subTest(malformed_return=malformed_return):
                self.assertEqual(pass_result(malformed_case, packets), "unfinished")

    def test_derived_summary_is_not_a_reviewer_packet_or_pass_receipt(self):
        fixture = load_json("review/pass-cases.json")
        packet = fixture["packets"]["derived-summary-old-shape"]
        case = next(
            case
            for case in fixture["cases"]
            if case["name"] == "derived-summary-cannot-fill-seat"
        )
        coexistence_case = next(
            case
            for case in fixture["cases"]
            if case["name"] == "derived-summary-cannot-invalidate-valid-original"
        )
        self.assertFalse(finding_packet_is_valid(packet))
        self.assertEqual(pass_result(case, fixture["packets"]), "unfinished")
        self.assertEqual(
            coexistence_case["derived_artifacts"], ["derived-summary-old-shape"]
        )
        self.assertEqual(
            pass_result(coexistence_case, fixture["packets"]), "complete_zero"
        )
        review = normalized(self.review)
        self.assertIn("derived summary", review)
        self.assertIn("explicitly labeled ineligible for pass accounting", review)

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

    def test_verification_challenges_premise_and_triage_preserves_findings(self):
        verification = normalized(
            (REFERENCES / "auditors" / "verification.md").read_text(encoding="utf-8")
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

    def test_guard_and_harness_residuals_require_fail_closed_boundaries(self):
        for case in self.fixture["guard_harness_residuals"]:
            with self.subTest(case=case["name"]):
                self.assertEqual(
                    residual_disposition_allowed(case), case["allowed"]
                )
        triage = normalized(
            (REFERENCES / "auditors" / "triage.md").read_text(encoding="utf-8")
        ).casefold()
        self.assertIn("outside the settled product contract", triage)
        self.assertIn("fail-closed", triage)


class CompoundContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compound = (REFERENCES / "compound.md").read_text(encoding="utf-8")

    def test_outcomes_are_exhaustive_and_project_writes_are_bounded(self):
        cases = load_json("compound/cases.json")
        self.assertEqual(
            {case["expected_outcome"] for case in cases},
            {"created", "updated", "forwarded_candidate", "no_op", "blocked"},
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertLessEqual(case["project_writes"], 1)
                self.assertEqual(compound_outcome(case), case["expected_outcome"])
                self.assertIn(f"`{case['expected_outcome']}`", self.compound)

    def test_compound_evidence_and_review_states_are_exact(self):
        cases = {
            case["name"]: case for case in load_json("compound/cases.json")
        }
        create = cases["new-durable-lesson"]
        for field in ("phase_evidence_available", "candidate_evidence", "uncaptured"):
            candidate = dict(create)
            candidate[field] = "unknown"
            with self.subTest(nonboolean_compound_evidence=field):
                self.assertEqual(compound_outcome(candidate), "blocked")
        for name in ("forward-external-owner", "forward-repo-local-owner"):
            candidate = dict(cases[name])
            candidate["requires_review"] = "unknown"
            with self.subTest(nonboolean_review_state=name):
                self.assertEqual(compound_outcome(candidate), "blocked")
        for value in ("", "   ", None):
            candidate = dict(create)
            candidate["prevented_repeat"] = value
            with self.subTest(invalid_prevented_repeat=value):
                self.assertEqual(compound_outcome(candidate), "blocked")
        candidate = dict(create)
        candidate["project_writes"] = True
        self.assertEqual(compound_outcome(candidate), "blocked")
        sensitive = dict(cases["forward-sensitive-external-owner"])
        sensitive["outward_reference_owner_ref"] = "owner-2"
        self.assertEqual(compound_outcome(sensitive), "blocked")
        sensitive_create = dict(cases["sensitive-create-with-private-custody"])
        sensitive_create["outward_reference_owner_ref"] = "owner-2"
        self.assertEqual(compound_outcome(sensitive_create), "blocked")

    def test_material_candidate_is_forwarded_or_blocked(self):
        case = next(
            case for case in load_json("compound/cases.json")
            if case["name"] == "forward-external-owner"
        )
        blocked = next(
            case for case in load_json("compound/cases.json")
            if case["name"] == "temporary-only-material-candidate"
        )
        self.assertEqual(case["expected_outcome"], "forwarded_candidate")
        self.assertTrue(all(case["owner"].values()))
        self.assertEqual(case["project_writes"], 0)
        self.assertEqual(blocked["expected_outcome"], "blocked")
        self.assertIn("Do not invent", self.compound)

    def test_materiality_requires_evidence_gap_and_prevented_repeat(self):
        for case in load_json("compound/cases.json"):
            material = bool(
                case["candidate_evidence"]
                and case["uncaptured"]
                and case["prevented_repeat"]
            )
            with self.subTest(case=case["name"]):
                if case["expected_outcome"] == "no_op":
                    self.assertFalse(material)

    def test_learning_write_requires_current_review(self):
        for case in load_json("compound/cases.json"):
            with self.subTest(case=case["name"]):
                if case["project_writes"] == 1 and case["expected_outcome"] != "blocked":
                    self.assertTrue(case["requires_review"])
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
