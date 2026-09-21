from __future__ import annotations

from datetime import UTC, datetime, timedelta

from epm import (
    AuthorityFailureCode,
    AuthorityGrant,
    AuthorityRequest,
    Decision,
    establish_authority_basis,
    evaluate_authority_request,
)

from boundary_proof.c2pa_adapter import C2PATrustState, parse_c2patool_report

DECISION_AT = datetime(2026, 9, 21, 15, 0, tzinfo=UTC)


def _trusted_report(**extra: object) -> dict[str, object]:
    report: dict[str, object] = {
        "active_manifest": "contentauth:urn:uuid:temporal-boundary",
        "validation_state": "Trusted",
        "validation_status": [],
        "manifests": {"contentauth:urn:uuid:temporal-boundary": {}},
    }
    report.update(extra)
    return report


def _request(*, at: datetime = DECISION_AT) -> AuthorityRequest:
    return AuthorityRequest(
        transition_id="V3-TEMPORAL-001",
        actor="agent:verifier",
        action="record.write",
        resource="ledger:boundary-proof",
        purpose="verification",
        scope="single-asset",
        jurisdiction="US",
        at=at,
        authority="authority:boundary",
        policy_id="boundary-policy",
        policy_version="1",
    )


def _grant(*, evidence_ref: str) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="V3-GRANT-001",
        subject="agent:verifier",
        actions=frozenset({"record.write"}),
        resources=frozenset({"ledger:boundary-proof"}),
        purposes=frozenset({"verification"}),
        scopes=frozenset({"single-asset"}),
        jurisdictions=frozenset({"US"}),
        issuer="authority:boundary",
        policy_id="boundary-policy",
        policy_version="1",
        evidence_refs=(evidence_ref,),
        not_before=DECISION_AT - timedelta(hours=1),
        not_after=DECISION_AT + timedelta(hours=1),
    )


def test_trusted_c2pa_does_not_absorb_untyped_repository_presence_claims():
    clean = parse_c2patool_report(_trusted_report())
    decorated = parse_c2patool_report(
        _trusted_report(
            repository_present_by="2026-09-20T00:00:00Z",
            repository_receipt_verified=True,
        )
    )

    assert clean == decorated
    assert decorated.trust_state is C2PATrustState.TRUSTED


def test_trusted_c2pa_does_not_absorb_untyped_actor_access_or_permission_claims():
    clean = parse_c2patool_report(_trusted_report())
    decorated = parse_c2patool_report(
        _trusted_report(
            actor_access_by="2026-09-20T00:00:00Z",
            authorized_at="2026-09-20T00:00:00Z",
            permitted=True,
        )
    )

    assert clean == decorated
    assert decorated.trust_state is C2PATrustState.TRUSTED


def test_trusted_provenance_without_authority_basis_cannot_permit_action():
    handoff = parse_c2patool_report(_trusted_report())
    assert handoff.evidence_ref is not None

    result = evaluate_authority_request(_request(), None)

    assert result.decision is Decision.DEFER
    assert result.failure is AuthorityFailureCode.AUTHORITY_UNESTABLISHED
    assert result.permitted is False
    assert result.fail_closed is True


def test_later_authority_validation_cannot_retroactively_authorize_trusted_provenance():
    handoff = parse_c2patool_report(_trusted_report())
    assert handoff.evidence_ref is not None

    basis = establish_authority_basis(
        _grant(evidence_ref=handoff.evidence_ref),
        validator_id="boundary-validator:1",
        validation_method="external-policy-check",
        validation_evidence_refs=("validation:v3:late",),
        validated_at=DECISION_AT + timedelta(minutes=1),
    )
    result = evaluate_authority_request(_request(), basis)

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.TEMPORAL_MISMATCH
    assert result.permitted is False


def test_time_valid_authority_is_a_separate_positive_control():
    handoff = parse_c2patool_report(_trusted_report())
    assert handoff.evidence_ref is not None

    basis = establish_authority_basis(
        _grant(evidence_ref=handoff.evidence_ref),
        validator_id="boundary-validator:1",
        validation_method="external-policy-check",
        validation_evidence_refs=("validation:v3:on-time",),
        validated_at=DECISION_AT - timedelta(minutes=1),
    )
    result = evaluate_authority_request(_request(), basis)

    assert result.decision is Decision.AUTHORIZED
    assert result.permitted is True
