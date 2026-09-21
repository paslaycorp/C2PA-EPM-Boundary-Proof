from __future__ import annotations

from copy import deepcopy

from epm import AssuranceState

from boundary_proof.c2pa_adapter import C2PATrustState, parse_c2patool_report


def _report(*, state: str = "Valid", statuses: list[dict[str, object]] | None = None):
    return {
        "active_manifest": "contentauth:urn:uuid:test",
        "validation_state": state,
        "validation_status": statuses or [],
        "manifests": {"contentauth:urn:uuid:test": {}},
    }


def test_clean_explicitly_trusted_report_can_preserve_provenance():
    handoff = parse_c2patool_report(_report())

    assert handoff.trust_state is C2PATrustState.TRUSTED
    assert handoff.provenance_state is AssuranceState.PRESERVED


def test_untrusted_signer_is_unknown_not_preserved_and_not_fabricated_invalid():
    handoff = parse_c2patool_report(
        _report(
            statuses=[
                {
                    "code": "signingCredential.untrusted",
                    "explanation": "certificate not in supplied trust basis",
                }
            ]
        )
    )

    assert handoff.trust_state is C2PATrustState.UNTRUSTED
    assert handoff.provenance_state is AssuranceState.UNKNOWN


def test_invalid_manifest_is_typed_invalidated():
    handoff = parse_c2patool_report(
        _report(
            state="Invalid",
            statuses=[{"code": "assertion.dataHash.mismatch"}],
        )
    )

    assert handoff.trust_state is C2PATrustState.INVALID
    assert handoff.provenance_state is AssuranceState.INVALIDATED


def test_caller_cannot_inject_trust_with_friendly_metadata():
    report = _report(statuses=[{"code": "signingCredential.untrusted"}])
    report["trusted"] = True
    report["authorized"] = True
    report["boundary_validated"] = True

    handoff = parse_c2patool_report(report)

    assert handoff.trust_state is C2PATrustState.UNTRUSTED
    assert handoff.provenance_state is AssuranceState.UNKNOWN


def test_missing_active_manifest_remains_indeterminate():
    report = _report()
    report.pop("active_manifest")

    handoff = parse_c2patool_report(report)

    assert handoff.trust_state is C2PATrustState.INDETERMINATE
    assert handoff.provenance_state is AssuranceState.UNKNOWN
    assert handoff.evidence_ref is None


def test_status_order_and_duplicates_do_not_change_handoff():
    first = _report(
        statuses=[
            {"code": "signingCredential.untrusted"},
            {"code": "example.notice"},
            {"code": "signingCredential.untrusted"},
        ]
    )
    second = deepcopy(first)
    second["validation_status"] = list(reversed(first["validation_status"]))

    a = parse_c2patool_report(first)
    b = parse_c2patool_report(second)

    assert a == b
    assert a.validation_status_codes == (
        "example.notice",
        "signingCredential.untrusted",
    )


def test_unknown_status_never_upgrades_to_trusted():
    handoff = parse_c2patool_report(
        _report(statuses=[{"code": "future.validation.status"}])
    )

    assert handoff.trust_state is C2PATrustState.INDETERMINATE
    assert handoff.provenance_state is AssuranceState.UNKNOWN
