from __future__ import annotations

import json
import sys
from pathlib import Path

from epm import AssuranceState

from boundary_proof.c2pa_adapter import C2PATrustState, parse_c2patool_report


def _load(path: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise AssertionError(f"{path} did not contain a JSON object")
    return value


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: exam_v2_trust.py "
            "<trusted.json> <default-trust.json> <tampered.json> <receipt.json>"
        )

    trusted = parse_c2patool_report(_load(sys.argv[1]))
    default = parse_c2patool_report(_load(sys.argv[2]))
    tampered = parse_c2patool_report(_load(sys.argv[3]))

    assert trusted.trust_state is C2PATrustState.TRUSTED
    assert trusted.provenance_state is AssuranceState.PRESERVED

    assert default.trust_state is C2PATrustState.UNTRUSTED
    assert default.provenance_state is AssuranceState.UNKNOWN
    assert "signingCredential.untrusted" in default.validation_status_codes

    assert tampered.trust_state is C2PATrustState.INVALID
    assert tampered.provenance_state is AssuranceState.INVALIDATED
    assert "assertion.dataHash.mismatch" in tampered.validation_status_codes

    receipt = {
        "schema": "c2pa-epm-boundary-proof/exam-v2-trust/1",
        "result": "PASS",
        "invariant": (
            "cryptographic validity, signer trust, provenance assurance, "
            "applicability, and authority remain separate states"
        ),
        "trusted_fixture": {
            "trust_state": trusted.trust_state.value,
            "provenance_state": trusted.provenance_state.value,
            "validation_status_codes": list(trusted.validation_status_codes),
        },
        "default_trust": {
            "trust_state": default.trust_state.value,
            "provenance_state": default.provenance_state.value,
            "validation_status_codes": list(default.validation_status_codes),
        },
        "tampered": {
            "trust_state": tampered.trust_state.value,
            "provenance_state": tampered.provenance_state.value,
            "validation_status_codes": list(tampered.validation_status_codes),
        },
        "claim_boundary": {
            "c2pa_conformance_claim": False,
            "c2pa_endorsement_claim": False,
            "upstream_epm_modified": False,
        },
    }
    Path(sys.argv[4]).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
