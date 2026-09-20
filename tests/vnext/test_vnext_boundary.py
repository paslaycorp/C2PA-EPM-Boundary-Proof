from __future__ import annotations

from datetime import UTC, datetime, timedelta

from epm import (
    AssuranceContext,
    AssuranceState,
    AuthorityFailureCode,
    AuthorityGrant,
    AuthorityRequest,
    Decision,
    EvidentiaryEnvelope,
    PreservationProof,
    RuleBinding,
    State,
    assess_transition,
    establish_authority_basis,
    evaluate_authority_request,
)

NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def _context() -> AssuranceContext:
    return AssuranceContext(
        identity="asset:example",
        purpose="verify",
        scope="asset",
        jurisdiction="US",
        at=NOW,
    )


def _rule() -> RuleBinding:
    return RuleBinding(
        rule_id="boundary-rule",
        version="1",
        authority="authority:boundary",
        jurisdiction="US",
        effective_at=NOW,
    )


def _state(
    state_id: str,
    *,
    applicability: AssuranceState = AssuranceState.PRESERVED,
    provenance: AssuranceState | None = AssuranceState.PRESERVED,
    integrity: AssuranceState | None = None,
) -> State:
    properties = {"applicability": applicability}
    if provenance is not None:
        properties["provenance"] = provenance
    if integrity is not None:
        properties["integrity"] = integrity
    return State(state_id, properties, _context(), _rule())


def _request(**overrides) -> AuthorityRequest:
    values = {
        "transition_id": "AUTH-001",
        "actor": "agent:verifier",
        "action": "record.write",
        "resource": "ledger:boundary-proof",
        "purpose": "verification",
        "scope": "single-asset",
        "jurisdiction": "US",
        "at": NOW,
        "authority": "authority:boundary",
        "policy_id": "boundary-policy",
        "policy_version": "1",
    }
    values.update(overrides)
    return AuthorityRequest(**values)


def _grant(**overrides) -> AuthorityGrant:
    values = {
        "grant_id": "GRANT-001",
        "subject": "agent:verifier",
        "actions": frozenset({"record.write"}),
        "resources": frozenset({"ledger:boundary-proof"}),
        "purposes": frozenset({"verification"}),
        "scopes": frozenset({"single-asset"}),
        "jurisdictions": frozenset({"US"}),
        "issuer": "authority:boundary",
        "policy_id": "boundary-policy",
        "policy_version": "1",
        "evidence_refs": ("grant:001",),
        "not_before": NOW - timedelta(hours=1),
        "not_after": NOW + timedelta(hours=2),
    }
    values.update(overrides)
    return AuthorityGrant(**values)


def _basis(grant: AuthorityGrant | None = None, *, validated_at: datetime | None = None):
    return establish_authority_basis(
        grant or _grant(),
        validator_id="boundary-validator:1",
        validation_method="external-policy-check",
        validation_evidence_refs=("validation:001",),
        validated_at=validated_at or NOW - timedelta(minutes=1),
    )


def _proof(property_name: str, transition_id: str) -> PreservationProof:
    return PreservationProof(
        property_name=property_name,
        transition_id=transition_id,
        rule_id="boundary-rule",
        rule_version="1",
        authority="authority:boundary",
        evidence_refs=(f"evidence:{property_name}",),
    )


def test_unsupported_envelope_schema_cannot_authorize():
    envelope = EvidentiaryEnvelope(
        transition_id="VNEXT-01",
        source=_state("asset:source"),
        target=_state("asset:target"),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
        schema_version="epm.evidentiary-envelope/999.0",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "DENY"
    assert result["failure"] == "PRESERVATION_UNESTABLISHED"
    assert result["fail_closed"] is True


def test_contradiction_survives_composition_as_typed_blocker():
    envelope = EvidentiaryEnvelope(
        transition_id="VNEXT-02",
        source=_state("asset:source", provenance=AssuranceState.CONTRADICTED),
        target=_state("asset:target"),
        material_properties=frozenset({"provenance"}),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["state"] == "CONTRADICTED"
    assert result["failure"] == "CONTRADICTORY_EVIDENCE"
    assert result["decision"] == "DENY"


def test_caller_omission_cannot_hide_explicit_property_state_change():
    envelope = EvidentiaryEnvelope(
        transition_id="VNEXT-03",
        source=_state("asset:source", provenance=AssuranceState.UNKNOWN),
        target=_state("asset:target", provenance=AssuranceState.PRESERVED),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "DENY"
    assert result["failure"] == "COMPOSITION_UNRESOLVED"
    assert result["fail_closed"] is True


def test_structural_omission_is_not_rewritten_as_explicit_unknown():
    envelope = EvidentiaryEnvelope(
        transition_id="VNEXT-04",
        source=_state("asset:source", provenance=AssuranceState.PRESERVED),
        target=_state("asset:target", provenance=None),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "AUTHORIZED"
    assert result["failure"] == "NONE"


def test_explicit_unknown_target_is_material_and_blocks_composition():
    envelope = EvidentiaryEnvelope(
        transition_id="VNEXT-05",
        source=_state("asset:source", provenance=AssuranceState.PRESERVED),
        target=_state("asset:target", provenance=AssuranceState.UNKNOWN),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "DENY"
    assert result["failure"] == "COMPOSITION_UNRESOLVED"


def test_capability_without_validated_authority_cannot_permit_action():
    result = evaluate_authority_request(_request(), None)

    assert result.decision is Decision.DEFER
    assert result.failure is AuthorityFailureCode.AUTHORITY_UNESTABLISHED
    assert result.permitted is False
    assert result.fail_closed is True


def test_caller_asserted_authority_cannot_self_validate():
    hostile = {
        "grant_id": "GRANT-001",
        "validated": True,
        "boundary_validated": True,
        "authority": "authority:boundary",
    }

    result = evaluate_authority_request(_request(), hostile)

    assert result.decision is Decision.QUARANTINE
    assert result.failure is AuthorityFailureCode.BOUNDARY_UNVALIDATED
    assert result.permitted is False


def test_later_validation_cannot_retroactively_authorize():
    result = evaluate_authority_request(
        _request(at=NOW),
        _basis(validated_at=NOW + timedelta(minutes=1)),
    )

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.TEMPORAL_MISMATCH
    assert result.permitted is False


def test_revocation_blocks_future_use_without_rewriting_prior_result():
    revoked_at = NOW + timedelta(minutes=10)
    grant = _grant(
        revoked_at=revoked_at,
        revocation_evidence_refs=("revocation:001",),
    )
    basis = _basis(grant, validated_at=NOW - timedelta(minutes=5))

    before = evaluate_authority_request(_request(at=NOW), basis)
    after = evaluate_authority_request(
        _request(transition_id="AUTH-002", at=NOW + timedelta(minutes=11)),
        basis,
    )

    assert before.decision is Decision.AUTHORIZED
    assert before.permitted is True
    assert after.decision is Decision.DENY
    assert after.failure is AuthorityFailureCode.AUTHORITY_REVOKED
    assert after.permitted is False


def test_network_reachability_does_not_become_network_authority():
    result = evaluate_authority_request(
        _request(
            action="network.connect",
            resource="tcp:203.0.113.7:22",
            purpose="reverse-tunnel",
        ),
        _basis(),
    )

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.ACTION_MISMATCH
    assert result.permitted is False


def test_equivalent_component_orders_produce_identical_receipts():
    transition_id = "VNEXT-ORDER"
    preservation_a = {
        "provenance": _proof("provenance", transition_id),
        "integrity": _proof("integrity", transition_id),
    }
    preservation_b = {
        "integrity": _proof("integrity", transition_id),
        "provenance": _proof("provenance", transition_id),
    }

    first = EvidentiaryEnvelope(
        transition_id=transition_id,
        source=_state(
            "asset:source",
            provenance=AssuranceState.PRESERVED,
            integrity=AssuranceState.PRESERVED,
        ),
        target=_state(
            "asset:target",
            provenance=AssuranceState.PRESERVED,
            integrity=AssuranceState.PRESERVED,
        ),
        material_properties=frozenset(["provenance", "integrity"]),
        preservation=preservation_a,
        consequence="critical",
    )
    second = EvidentiaryEnvelope(
        transition_id=transition_id,
        source=first.source,
        target=first.target,
        material_properties=frozenset(["integrity", "provenance"]),
        preservation=preservation_b,
        consequence="critical",
    )

    first_result = assess_transition(first)
    second_result = assess_transition(second)

    assert first_result == second_result
    assert first_result["decision"] == "AUTHORIZED"
    assert [c["property"] for c in first_result["component_results"]] == [
        "integrity",
        "provenance",
    ]
