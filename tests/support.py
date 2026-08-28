def private_record_is_minimal(record):
    allowed_fields = {"minimum_actionable_detail", "content_classes"}
    required_content_classes = {
        "safe_id",
        "state",
        "next_action",
        "closure_condition",
    }
    return (
        isinstance(record, dict)
        and set(record) <= allowed_fields
        and record.get("minimum_actionable_detail") is True
        and isinstance(record.get("content_classes"), list)
        and bool(record["content_classes"])
        and len(record["content_classes"]) == len(set(record["content_classes"]))
        and set(record["content_classes"]) == required_content_classes
    )


def is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def private_reference_is_bound(case):
    private_owner_ref = case.get("private_owner_ref")
    outward_owner_ref = case.get("outward_reference_owner_ref")
    return (
        isinstance(private_owner_ref, str)
        and bool(private_owner_ref.strip())
        and outward_owner_ref == private_owner_ref
    )


def summary_is_accepted(case, terminal_claim):
    terminal_status = (
        "complete" if terminal_claim in {"Full", "Light"} else "incomplete"
    )
    failure_state = case.get("failure_state")
    failure_evidence_valid = (
        (failure_state == "none" and case.get("no_failure_stated") is True)
        or (
            failure_state == "uncorrected"
            and case.get("run_status") == "incomplete"
        )
        or (
            failure_state == "corrected"
            and case.get("correcting_evidence") is True
        )
    )
    return (
        case["facts_agree"] is True
        and case["self_contained"] is True
        and case["receipt_ids"] is True
        and case["sensitive_metadata_exposed"] is False
        and case["run_status"] in {"complete", "incomplete"}
        and case["run_status"] == terminal_status
        and case["beginner_first"] == case["run_status"]
        and failure_evidence_valid
    )
