from __future__ import annotations

import hashlib
import io
import json
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import c2pa
import requests
from epm import (
    EPM_ENGINE_VERSION,
    AssuranceContext,
    AssuranceState,
    EvidentiaryEnvelope,
    RuleBinding,
    State,
    assess_transition,
)

from .proof import build_boundary_proof, make_receipt

EPM_RELEASE_COMMIT = "bb0559ddb8eff7f78acc432c0334ce7596c1045c"
C2PA_PYTHON_VERSION = "0.37.10"
ASSET_REPO_COMMIT = "c37f93e115289ac1ef00f899a860e6e08ab9886f"
ASSET_PATH = "images/Firefly_tabby_cat.jpg"
ASSET_URL = (
    "https://raw.githubusercontent.com/contentauth/example-assets/"
    f"{ASSET_REPO_COMMIT}/{ASSET_PATH}"
)
MAX_ASSET_BYTES = 5 * 1024 * 1024
FIXED_AT = datetime(2026, 9, 28, 18, 30, tzinfo=UTC)


def _enumish(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _enumish(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_enumish(v) for v in value]
    if hasattr(value, "value"):
        return _enumish(value.value)
    for method in ("to_json", "json"):
        fn = getattr(value, method, None)
        if callable(fn):
            try:
                data = fn()
                return json.loads(data) if isinstance(data, str) else _enumish(data)
            except Exception:
                pass
    if hasattr(value, "__dict__"):
        return {k: _enumish(v) for k, v in vars(value).items() if not k.startswith("_")}
    return str(value)


@lru_cache(maxsize=1)
def load_c2pa_receipt() -> dict[str, Any]:
    response = requests.get(ASSET_URL, timeout=20)
    response.raise_for_status()
    asset = response.content
    if len(asset) > MAX_ASSET_BYTES:
        raise RuntimeError("Pinned demonstration asset exceeds safety size limit")

    asset_hash = hashlib.sha256(asset).hexdigest()
    ctx = c2pa.Context.from_dict({
        "verify": {
            "remote_manifest_fetch": True,
            "verify_trust": True,
            "verify_timestamp_trust": True,
        }
    })
    with io.BytesIO(asset) as stream:
        with c2pa.Reader("image/jpeg", stream, context=ctx) as reader:
            manifest_store = json.loads(reader.json())
            state = _enumish(reader.get_validation_state())
            results = _enumish(reader.get_validation_results())

    return make_receipt(
        asset_source={
            "repository": "contentauth/example-assets",
            "repository_commit": ASSET_REPO_COMMIT,
            "path": ASSET_PATH,
            "url": ASSET_URL,
            "declared_example": "Adobe Firefly Content Credentials example asset",
        },
        asset_sha256=asset_hash,
        manifest_store=manifest_store,
        validation_state=state,
        validation_results=results,
        sdk_version=C2PA_PYTHON_VERSION,
    )


def _case_context(case_id: str) -> tuple[AssuranceContext, dict[str, Any]]:
    base = {
        "identity": "c2pa-validation-receipt",
        "purpose": "provenance-review",
        "scope": "content-provenance",
        "jurisdiction": "DEMO",
        "at": FIXED_AT,
    }
    target = dict(base)
    delta: dict[str, Any] = {}
    if case_id == "purpose-change":
        target["purpose"] = "public-disclosure"
        delta = {"purpose": {"from": base["purpose"], "to": target["purpose"]}}
    elif case_id == "time-change":
        target["at"] = FIXED_AT + timedelta(hours=1)
        delta = {
            "at": {
                "from": FIXED_AT.isoformat(),
                "to": target["at"].isoformat(),
            }
        }
    elif case_id != "baseline":
        raise ValueError(f"Unknown case: {case_id}")
    return AssuranceContext(**target), delta


def run_case(case_id: str) -> dict[str, Any]:
    receipt = load_c2pa_receipt()
    source_context = AssuranceContext(
        identity="c2pa-validation-receipt",
        purpose="provenance-review",
        scope="content-provenance",
        jurisdiction="DEMO",
        at=FIXED_AT,
    )
    target_context, delta = _case_context(case_id)
    rule = RuleBinding(
        "c2pa-epm-boundary-demo",
        "0.1",
        "demo-boundary-only",
        "DEMO",
        FIXED_AT,
    )
    evidence_id = f"c2pa:{receipt['manifest_store_sha256']}"
    source = State(
        evidence_id,
        {"applicability": AssuranceState.PRESERVED},
        source_context,
        rule,
    )
    target = State(
        f"{evidence_id}:{case_id}",
        {"applicability": AssuranceState.PRESERVED},
        target_context,
        rule,
    )
    envelope = EvidentiaryEnvelope(
        transition_id=f"c2pa-boundary:{case_id}",
        source=source,
        target=target,
        material_properties=frozenset(),
    )
    result = dict(assess_transition(envelope))
    epm_input = {
        "transition_id": envelope.transition_id,
        "source_evidence_id": evidence_id,
        "source_context": {
            "identity": source_context.identity,
            "purpose": source_context.purpose,
            "scope": source_context.scope,
            "jurisdiction": source_context.jurisdiction,
            "at": source_context.at.isoformat(),
        },
        "target_context": {
            "identity": target_context.identity,
            "purpose": target_context.purpose,
            "scope": target_context.scope,
            "jurisdiction": target_context.jurisdiction,
            "at": target_context.at.isoformat() if target_context.at else None,
        },
        "context_delta": delta,
        "declared_material_properties": [],
        "note": (
            "EPM v0.1.2 derives applicability materiality from an actual "
            "context/rule change even when the caller under-declares it."
        ),
    }
    return build_boundary_proof(
        case_id=case_id,
        c2pa_receipt=receipt,
        epm_input=epm_input,
        epm_result=result,
        epm_engine_version=EPM_ENGINE_VERSION,
        epm_release_commit=EPM_RELEASE_COMMIT,
    )
