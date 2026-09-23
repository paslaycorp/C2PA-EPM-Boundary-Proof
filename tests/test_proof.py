from boundary.proof import build_boundary_proof, make_receipt


def fixture_receipt():
    return make_receipt(
        asset_source={"repository": "contentauth/example-assets", "commit": "abc"},
        asset_sha256="a" * 64,
        manifest_store={"active_manifest": "urn:test", "manifests": {"urn:test": {}}},
        validation_state="Trusted",
        validation_results={"success": [{"code": "claimSignature.validated"}], "informational": [], "failure": []},
        sdk_version="0.37.10",
    )


def test_proof_is_deterministic():
    receipt = fixture_receipt()
    args = dict(
        case_id="baseline",
        c2pa_receipt=receipt,
        epm_input={"context_delta": {}},
        epm_result={"decision": "AUTHORIZED", "state": "PRESERVED"},
        epm_engine_version="epm-engine/0.1.2",
        epm_release_commit="b" * 40,
    )
    assert build_boundary_proof(**args)["proof_sha256"] == build_boundary_proof(**args)["proof_sha256"]


def test_authority_never_imported():
    proof = build_boundary_proof(
        case_id="purpose-change",
        c2pa_receipt=fixture_receipt(),
        epm_input={"context_delta": {"purpose": {"from": "a", "to": "b"}}},
        epm_result={"decision": "QUARANTINE", "state": "INVALIDATED"},
        epm_engine_version="epm-engine/0.1.2",
        epm_release_commit="b" * 40,
    )
    assert proof["external_action_authority"]["status"] == "OUTSIDE_EPM_SCOPE"
    assert proof["external_action_authority"]["authorized"] is None
    assert proof["invariants"]["external_authority_from_epm"] is False
    assert proof["invariants"]["c2pa_semantics_mutated"] is False
