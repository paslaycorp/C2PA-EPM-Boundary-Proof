from boundary.runtime import run_case


def test_baseline_and_context_change_preserve_c2pa_receipt():
    baseline = run_case("baseline")
    changed = run_case("purpose-change")
    assert baseline["c2pa_receipt"]["manifest_store_sha256"] == changed["c2pa_receipt"]["manifest_store_sha256"]
    assert baseline["epm_transition_result"]["decision"] == "AUTHORIZED"
    assert changed["epm_transition_result"]["decision"] in {"QUARANTINE", "DENY"}
    assert changed["epm_transition_result"]["failure"] == "MISAPPLICATION"
    assert changed["external_action_authority"]["status"] == "OUTSIDE_EPM_SCOPE"
