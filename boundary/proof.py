from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

PROOF_SCHEMA = "epm.c2pa-boundary-proof/0.1-experimental"
RECEIPT_SCHEMA = "epm.c2pa-validation-receipt/0.1-experimental"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def make_receipt(
    *,
    asset_source: Mapping[str, Any],
    asset_sha256: str,
    manifest_store: Mapping[str, Any],
    validation_state: Any,
    validation_results: Any,
    sdk_version: str,
) -> dict[str, Any]:
    # This wrapper is intentionally lossless: it retains the raw C2PA-derived
    # structures and adds only provenance about the handoff itself.
    manifest_hash = sha256_json(manifest_store)
    return {
        "schema": RECEIPT_SCHEMA,
        "source_system": "C2PA",
        "sdk": f"c2pa-python/{sdk_version}",
        "asset_source": dict(asset_source),
        "asset_sha256": asset_sha256,
        "manifest_store_sha256": manifest_hash,
        "active_manifest": manifest_store.get("active_manifest"),
        "validation_state": validation_state,
        "validation_results": validation_results,
        "manifest_store": manifest_store,
        "handoff_semantics": {
            "lossless_wrapper": True,
            "c2pa_output_rewritten": False,
            "value_judgment_added": False,
            "authority_imported": False,
        },
    }


def build_boundary_proof(
    *,
    case_id: str,
    c2pa_receipt: Mapping[str, Any],
    epm_input: Mapping[str, Any],
    epm_result: Mapping[str, Any],
    epm_engine_version: str,
    epm_release_commit: str,
) -> dict[str, Any]:
    authority = {
        "status": "OUTSIDE_EPM_SCOPE",
        "authorized": None,
        "reason": (
            "The EPM transition decision evaluates evidentiary preservation. "
            "It does not confer permission for an external real-world action."
        ),
    }
    invariant_view = {
        "c2pa_receipt_sha256": sha256_json(c2pa_receipt),
        "c2pa_semantics_mutated": False,
        "external_authority_from_epm": False,
        "context_change_declared": bool(epm_input.get("context_delta")),
    }
    core = {
        "schema": PROOF_SCHEMA,
        "case_id": case_id,
        "versions": {
            "epm_engine": epm_engine_version,
            "epm_release_commit": epm_release_commit,
        },
        "c2pa_receipt": dict(c2pa_receipt),
        "epm_input": dict(epm_input),
        "epm_transition_result": dict(epm_result),
        "external_action_authority": authority,
        "invariants": invariant_view,
    }
    core["proof_sha256"] = sha256_json(core)
    return core
