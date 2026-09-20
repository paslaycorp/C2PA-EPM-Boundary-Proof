from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from epm import (
    AssuranceContext,
    AssuranceState,
    EvidentiaryEnvelope,
    PreservationProof,
    RuleBinding,
    State,
    assess_transition,
)

NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def _context(*, purpose: str = "verify", at: datetime = NOW) -> AssuranceContext:
    return AssuranceContext(
        identity="asset:example",
        purpose=purpose,
        scope="asset",
        jurisdiction="US",
        at=at,
    )


def _rule(*, effective_at: datetime = NOW) -> RuleBinding:
    return RuleBinding(
        rule_id="boundary-rule",
        version="1",
        authority="authority:boundary",
        jurisdiction="US",
        effective_at=effective_at,
    )


def _state(
    state_id: str,
    *,
    applicability: AssuranceState = AssuranceState.PRESERVED,
    provenance: AssuranceState = AssuranceState.PRESERVED,
    context: AssuranceContext | None = None,
    rule: RuleBinding | None = None,
) -> State:
    return State(
        state_id=state_id,
        properties={
            "applicability": applicability,
            "provenance": provenance,
        },
        context=context or _context(),
        rule=rule or _rule(),
    )


def test_verified_provenance_does_not_authorize_changed_purpose():
    envelope = EvidentiaryEnvelope(
        transition_id="FROZEN-01",
        source=_state("asset:source"),
        target=_state("asset:target", context=_context(purpose="publish")),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "DENY"
    assert result["failure"] == "MISAPPLICATION"
    assert result["fail_closed"] is True


def test_unknown_applicability_cannot_be_promoted_to_authorized():
    envelope = EvidentiaryEnvelope(
        transition_id="FROZEN-02",
        source=_state("asset:source", applicability=AssuranceState.UNKNOWN),
        target=_state("asset:target"),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] != "AUTHORIZED"
    assert result["state"] == "UNKNOWN"


def test_wrong_authority_preservation_proof_fails_closed():
    proof = PreservationProof(
        property_name="applicability",
        transition_id="FROZEN-03",
        rule_id="boundary-rule",
        rule_version="1",
        authority="authority:wrong",
        evidence_refs=("c2pa:manifest:verified",),
    )
    envelope = EvidentiaryEnvelope(
        transition_id="FROZEN-03",
        source=_state("asset:source"),
        target=_state("asset:target", context=_context(purpose="publish")),
        material_properties=frozenset({"applicability"}),
        preservation={"applicability": proof},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "DENY"
    assert result["failure"] == "AUTHORITY_MISMATCH"
    assert result["fail_closed"] is True


def test_future_effective_rule_cannot_preserve_present_transition():
    future_rule = _rule(effective_at=NOW + timedelta(hours=1))
    proof = PreservationProof(
        property_name="applicability",
        transition_id="FROZEN-04",
        rule_id=future_rule.rule_id,
        rule_version=future_rule.version,
        authority=future_rule.authority,
        evidence_refs=("c2pa:manifest:verified",),
    )
    envelope = EvidentiaryEnvelope(
        transition_id="FROZEN-04",
        source=_state("asset:source", rule=future_rule),
        target=_state("asset:target", rule=future_rule),
        material_properties=frozenset({"applicability"}),
        preservation={"applicability": proof},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "DENY"
    assert result["failure"] == "PRESERVATION_UNESTABLISHED"


@pytest.mark.xfail(
    strict=True,
    reason="Known frozen v0.1.2 gap: unsupported envelope schemas were not rejected at this boundary.",
)
def test_known_gap_unsupported_schema_must_not_authorize():
    envelope = EvidentiaryEnvelope(
        transition_id="FROZEN-X01",
        source=_state("asset:source"),
        target=_state("asset:target"),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
        schema_version="epm.evidentiary-envelope/999.0",
    )

    result = assess_transition(envelope)

    assert result["decision"] != "AUTHORIZED"


@pytest.mark.xfail(
    strict=True,
    reason="Known frozen v0.1.2 gap: CONTRADICTED collapsed to UNKNOWN in transition evaluation.",
)
def test_known_gap_contradiction_must_remain_typed():
    envelope = EvidentiaryEnvelope(
        transition_id="FROZEN-X02",
        source=_state("asset:source", applicability=AssuranceState.CONTRADICTED),
        target=_state("asset:target"),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["state"] == "CONTRADICTED"
