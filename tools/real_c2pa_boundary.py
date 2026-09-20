from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from epm import (
    AssuranceContext,
    AssuranceState,
    AuthorityFailureCode,
    AuthorityRequest,
    Decision,
    EvidentiaryEnvelope,
    RuleBinding,
    State,
    assess_transition,
    evaluate_authority_request,
)

EPM_POST_RELEASE_PIN = "adb1c31cdb428816c95a3cf98c9a4427c13ec482"
C2PATOOL_RELEASE = "0.27.22"
C2PA_SPEC_VERSION = "2.4"
AT = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def _root_validation_status(document: dict[str, object]) -> list[object]:
    value = document.get("validation_status")
    return value if isinstance(value, list) else []


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: real_c2pa_boundary.py <c2pa-json> <receipt-json>")

    source_path = Path(sys.argv[1])
    receipt_path = Path(sys.argv[2])
    document = json.loads(source_path.read_text())

    active_manifest = document.get("active_manifest")
    manifests = document.get("manifests")
    if not isinstance(active_manifest, str) or not active_manifest:
        raise AssertionError("c2patool output did not identify an active manifest")
    if not isinstance(manifests, dict) or active_manifest not in manifests:
        raise AssertionError("active C2PA manifest is not present in the manifest store")

    validation_status = _root_validation_status(document)
    if validation_status:
        raise AssertionError(
            "baseline C2PA fixture produced validation status entries; "
            "do not promote it to the clean-provenance handoff"
        )

    source_context = AssuranceContext(
        identity="asset:c2pa-fixture",
        purpose="verification",
        scope="single-asset",
        jurisdiction="US",
        at=AT,
    )
    target_context = AssuranceContext(
        identity="asset:c2pa-fixture",
        purpose="publication",
        scope="single-asset",
        jurisdiction="US",
        at=AT,
    )
    rule = RuleBinding(
        rule_id="boundary-proof",
        version="1",
        authority="authority:boundary-proof",
        jurisdiction="US",
        effective_at=AT,
    )
    source = State(
        state_id=f"c2pa:{active_manifest}",
        properties={
            "applicability": AssuranceState.PRESERVED,
            "provenance": AssuranceState.PRESERVED,
        },
        context=source_context,
        rule=rule,
    )
    target = State(
        state_id="boundary:publication-request",
        properties={
            "applicability": AssuranceState.PRESERVED,
            "provenance": AssuranceState.PRESERVED,
        },
        context=target_context,
        rule=rule,
    )
    envelope = EvidentiaryEnvelope(
        transition_id="REAL-C2PA-BOUNDARY-01",
        source=source,
        target=target,
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    transition_result = assess_transition(envelope)
    assert transition_result["decision"] == "DENY"
    assert transition_result["failure"] == "MISAPPLICATION"
    assert transition_result["fail_closed"] is True

    authority_request = AuthorityRequest(
        transition_id="REAL-C2PA-AUTHORITY-01",
        actor="agent:c2pa-verifier",
        action="content.publish",
        resource="asset:c2pa-fixture",
        purpose="publication",
        scope="single-asset",
        jurisdiction="US",
        at=AT,
        authority="authority:boundary-proof",
        policy_id="boundary-proof",
        policy_version="1",
    )
    authority_result = evaluate_authority_request(authority_request, None)
    assert authority_result.decision is Decision.DEFER
    assert authority_result.failure is AuthorityFailureCode.AUTHORITY_UNESTABLISHED
    assert authority_result.permitted is False
    assert authority_result.fail_closed is True

    receipt = {
        "schema": "c2pa-epm-boundary-proof/receipt/1",
        "result": "PASS",
        "claim": "C2PA provenance does not manufacture EPM applicability or authority",
        "pins": {
            "c2pa_specification": C2PA_SPEC_VERSION,
            "c2patool": C2PATOOL_RELEASE,
            "epm_post_release": EPM_POST_RELEASE_PIN,
        },
        "c2pa": {
            "active_manifest": active_manifest,
            "manifest_count": len(manifests),
            "validation_status_count": len(validation_status),
        },
        "epm": {
            "changed_purpose": {
                "decision": transition_result["decision"],
                "failure": transition_result["failure"],
                "fail_closed": transition_result["fail_closed"],
            },
            "authority_without_basis": {
                "decision": authority_result.decision.value,
                "failure": authority_result.failure.value,
                "permitted": authority_result.permitted,
                "fail_closed": authority_result.fail_closed,
            },
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
