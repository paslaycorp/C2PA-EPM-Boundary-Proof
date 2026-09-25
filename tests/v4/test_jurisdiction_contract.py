from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from epm import (
    AuthorityGrant,
    AuthorityRequest,
    Decision,
    establish_authority_basis,
    evaluate_authority_request,
)

from boundary_proof.c2pa_adapter import C2PATrustState, parse_c2patool_report

DECISION_AT = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)


@dataclass(frozen=True)
class PolicyEnvelope:
    policy_id: str
    policy_version: str
    action: str
    resource: str
    purpose: str
    permitted: bool


@dataclass(frozen=True)
class MaterialityReceipt:
    material_fields: frozenset[str]


@dataclass(frozen=True)
class Act:
    action: str
    resource: str
    purpose: str
    beneficiary: str
    amount: int


@dataclass(frozen=True)
class EffectuationResult:
    permitted: bool
    code: str


def _trusted_report(**extra: object) -> dict[str, object]:
    report: dict[str, object] = {
        "active_manifest": "contentauth:urn:uuid:jurisdiction-contract",
        "validation_state": "Trusted",
        "validation_status": [],
        "manifests": {"contentauth:urn:uuid:jurisdiction-contract": {}},
    }
    report.update(extra)
    return report


def _request(*, at: datetime = DECISION_AT) -> AuthorityRequest:
    return AuthorityRequest(
        transition_id="V4-JURISDICTION-001",
        actor="agent:executor",
        action="payment.execute",
        resource="payment:invoice-42",
        purpose="settlement",
        scope="single-transaction",
        jurisdiction="US",
        at=at,
        authority="authority:treasury",
        policy_id="odrl-like-policy",
        policy_version="1",
    )


def _grant(*, evidence_ref: str) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="V4-GRANT-001",
        subject="agent:executor",
        actions=frozenset({"payment.execute"}),
        resources=frozenset({"payment:invoice-42"}),
        purposes=frozenset({"settlement"}),
        scopes=frozenset({"single-transaction"}),
        jurisdictions=frozenset({"US"}),
        issuer="authority:treasury",
        policy_id="odrl-like-policy",
        policy_version="1",
        evidence_refs=(evidence_ref,),
        not_before=DECISION_AT - timedelta(minutes=5),
        not_after=DECISION_AT + timedelta(minutes=5),
    )


def _policy(*, permitted: bool = True) -> PolicyEnvelope:
    return PolicyEnvelope(
        policy_id="odrl-like-policy",
        policy_version="1",
        action="payment.execute",
        resource="payment:invoice-42",
        purpose="settlement",
        permitted=permitted,
    )


def _act(*, beneficiary: str = "vendor:A", amount: int = 100_000) -> Act:
    return Act(
        action="payment.execute",
        resource="payment:invoice-42",
        purpose="settlement",
        beneficiary=beneficiary,
        amount=amount,
    )


def _authorized_result(evidence_ref: str):
    basis = establish_authority_basis(
        _grant(evidence_ref=evidence_ref),
        validator_id="boundary-validator:v4",
        validation_method="external-policy-check",
        validation_evidence_refs=("validation:v4:on-time",),
        validated_at=DECISION_AT - timedelta(seconds=30),
    )
    return evaluate_authority_request(_request(), basis)


def _effectuation_gate(
    *,
    provenance,
    authority_result,
    policy: PolicyEnvelope,
    materiality: MaterialityReceipt,
    approved_act: Act,
    current_act: Act,
    approved_state: dict[str, object],
    current_state: dict[str, object],
) -> EffectuationResult:
    # C2PA lane: provenance validity only. It is necessary in this scenario,
    # but never sufficient to authorize the act.
    if provenance.trust_state is not C2PATrustState.TRUSTED:
        return EffectuationResult(False, "PROVENANCE_NOT_TRUSTED")

    # EPM lane: authority/evidentiary decision. Policy and provenance cannot
    # manufacture an AUTHORIZED result here.
    if authority_result.decision is not Decision.AUTHORIZED or not authority_result.permitted:
        return EffectuationResult(False, "AUTHORITY_NOT_ESTABLISHED")

    # Policy lane: synthetic contract only. This is intentionally not an
    # ODRL processor or conformance claim.
    if not policy.permitted:
        return EffectuationResult(False, "POLICY_DENY")
    if (
        policy.action != current_act.action
        or policy.resource != current_act.resource
        or policy.purpose != current_act.purpose
    ):
        return EffectuationResult(False, "POLICY_SCOPE_MISMATCH")

    # Effectuation lane: exact-act binding belongs at the final boundary.
    if current_act != approved_act:
        return EffectuationResult(False, "EXACT_ACT_MISMATCH")

    # TVC-like lane: materiality identifies which mutable facts require
    # revalidation. It does not itself grant or revoke authority.
    changed_material = {
        field
        for field in materiality.material_fields
        if approved_state.get(field) != current_state.get(field)
    }
    if changed_material:
        return EffectuationResult(False, "MATERIAL_STATE_CHANGED")

    return EffectuationResult(True, "EFFECTUATION_PERMITTED")


def test_trusted_provenance_and_permissive_policy_cannot_create_authority():
    provenance = parse_c2patool_report(_trusted_report())
    assert provenance.evidence_ref is not None

    missing_authority = evaluate_authority_request(_request(), None)
    result = _effectuation_gate(
        provenance=provenance,
        authority_result=missing_authority,
        policy=_policy(permitted=True),
        materiality=MaterialityReceipt(frozenset({"beneficiary_verified", "policy_epoch"})),
        approved_act=_act(),
        current_act=_act(),
        approved_state={"beneficiary_verified": True, "policy_epoch": 7},
        current_state={"beneficiary_verified": True, "policy_epoch": 7},
    )

    assert result == EffectuationResult(False, "AUTHORITY_NOT_ESTABLISHED")


def test_policy_decision_does_not_rewrite_c2pa_provenance_state():
    clean = parse_c2patool_report(_trusted_report())
    permissive = _policy(permitted=True)
    denying = _policy(permitted=False)

    assert permissive != denying
    assert clean.trust_state is C2PATrustState.TRUSTED
    assert parse_c2patool_report(_trusted_report()).trust_state is clean.trust_state


def test_materiality_receipt_cannot_authorize_without_epm_authority():
    provenance = parse_c2patool_report(_trusted_report())
    missing_authority = evaluate_authority_request(_request(), None)

    result = _effectuation_gate(
        provenance=provenance,
        authority_result=missing_authority,
        policy=_policy(),
        materiality=MaterialityReceipt(
            frozenset({"beneficiary_verified", "policy_epoch", "delegation_active"})
        ),
        approved_act=_act(),
        current_act=_act(),
        approved_state={
            "beneficiary_verified": True,
            "policy_epoch": 7,
            "delegation_active": True,
        },
        current_state={
            "beneficiary_verified": True,
            "policy_epoch": 7,
            "delegation_active": True,
        },
    )

    assert result.permitted is False
    assert result.code == "AUTHORITY_NOT_ESTABLISHED"


def test_exact_act_mutation_is_rejected_at_effectuation_boundary():
    provenance = parse_c2patool_report(_trusted_report())
    assert provenance.evidence_ref is not None
    authority = _authorized_result(provenance.evidence_ref)
    assert authority.decision is Decision.AUTHORIZED

    result = _effectuation_gate(
        provenance=provenance,
        authority_result=authority,
        policy=_policy(),
        materiality=MaterialityReceipt(frozenset({"beneficiary_verified", "policy_epoch"})),
        approved_act=_act(beneficiary="vendor:A"),
        current_act=_act(beneficiary="vendor:B"),
        approved_state={"beneficiary_verified": True, "policy_epoch": 7},
        current_state={"beneficiary_verified": True, "policy_epoch": 7},
    )

    assert result == EffectuationResult(False, "EXACT_ACT_MISMATCH")


def test_material_state_change_revokes_effectuation_but_preserves_prior_authorization():
    provenance = parse_c2patool_report(_trusted_report())
    assert provenance.evidence_ref is not None
    authority = _authorized_result(provenance.evidence_ref)
    assert authority.decision is Decision.AUTHORIZED
    assert authority.permitted is True

    result = _effectuation_gate(
        provenance=provenance,
        authority_result=authority,
        policy=_policy(),
        materiality=MaterialityReceipt(frozenset({"beneficiary_verified", "policy_epoch"})),
        approved_act=_act(),
        current_act=_act(),
        approved_state={"beneficiary_verified": True, "policy_epoch": 7, "ui_theme": "dark"},
        current_state={"beneficiary_verified": False, "policy_epoch": 7, "ui_theme": "dark"},
    )

    assert authority.decision is Decision.AUTHORIZED
    assert result == EffectuationResult(False, "MATERIAL_STATE_CHANGED")


def test_non_material_state_change_does_not_cause_spurious_denial():
    provenance = parse_c2patool_report(_trusted_report())
    assert provenance.evidence_ref is not None
    authority = _authorized_result(provenance.evidence_ref)

    result = _effectuation_gate(
        provenance=provenance,
        authority_result=authority,
        policy=_policy(),
        materiality=MaterialityReceipt(frozenset({"beneficiary_verified", "policy_epoch"})),
        approved_act=_act(),
        current_act=_act(),
        approved_state={"beneficiary_verified": True, "policy_epoch": 7, "ui_theme": "dark"},
        current_state={"beneficiary_verified": True, "policy_epoch": 7, "ui_theme": "light"},
    )

    assert result == EffectuationResult(True, "EFFECTUATION_PERMITTED")


def test_policy_denial_blocks_effectuation_without_rewriting_authority_history():
    provenance = parse_c2patool_report(_trusted_report())
    assert provenance.evidence_ref is not None
    authority = _authorized_result(provenance.evidence_ref)
    assert authority.decision is Decision.AUTHORIZED

    result = _effectuation_gate(
        provenance=provenance,
        authority_result=authority,
        policy=_policy(permitted=False),
        materiality=MaterialityReceipt(frozenset({"beneficiary_verified", "policy_epoch"})),
        approved_act=_act(),
        current_act=_act(),
        approved_state={"beneficiary_verified": True, "policy_epoch": 7},
        current_state={"beneficiary_verified": True, "policy_epoch": 7},
    )

    assert authority.decision is Decision.AUTHORIZED
    assert result == EffectuationResult(False, "POLICY_DENY")
