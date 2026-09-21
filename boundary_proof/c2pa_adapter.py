from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from epm import AssuranceState


class C2PATrustState(str, Enum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    INVALID = "INVALID"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class C2PAHandoff:
    active_manifest: str | None
    validation_state: str | None
    validation_status_codes: tuple[str, ...]
    trust_state: C2PATrustState
    provenance_state: AssuranceState
    reason: str

    @property
    def evidence_ref(self) -> str | None:
        if not self.active_manifest:
            return None
        return f"c2pa:{self.active_manifest}"


def _validation_status_entries(value: object) -> list[Mapping[str, object]]:
    found: list[Mapping[str, object]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key == "validation_status" and isinstance(child, list):
                for entry in child:
                    if isinstance(entry, Mapping):
                        found.append(entry)
            found.extend(_validation_status_entries(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_validation_status_entries(child))
    return found


def _status_codes(document: Mapping[str, object]) -> tuple[str, ...]:
    codes: set[str] = set()
    for entry in _validation_status_entries(document):
        code = entry.get("code")
        if isinstance(code, str) and code:
            codes.add(code)
    return tuple(sorted(codes))


def parse_c2patool_report(document: Mapping[str, object]) -> C2PAHandoff:
    """Convert c2patool output into a deliberately narrow provenance handoff.

    The mapping is intentionally conservative: trusted clean reports may become
    PRESERVED provenance; an untrusted signer becomes UNKNOWN rather than false;
    invalid reports become INVALIDATED; incomplete or unfamiliar reports remain
    UNKNOWN. Friendly caller fields such as trusted=true are ignored.
    """

    active_manifest = document.get("active_manifest")
    if not isinstance(active_manifest, str) or not active_manifest:
        active_manifest = None

    raw_validation_state = document.get("validation_state")
    validation_state = (
        raw_validation_state if isinstance(raw_validation_state, str) else None
    )
    codes = _status_codes(document)

    if validation_state == "Invalid":
        return C2PAHandoff(
            active_manifest=active_manifest,
            validation_state=validation_state,
            validation_status_codes=codes,
            trust_state=C2PATrustState.INVALID,
            provenance_state=AssuranceState.INVALIDATED,
            reason="c2patool reports the manifest as invalid.",
        )

    if active_manifest is None:
        return C2PAHandoff(
            active_manifest=None,
            validation_state=validation_state,
            validation_status_codes=codes,
            trust_state=C2PATrustState.INDETERMINATE,
            provenance_state=AssuranceState.UNKNOWN,
            reason="No active manifest was established.",
        )

    if "signingCredential.untrusted" in codes:
        return C2PAHandoff(
            active_manifest=active_manifest,
            validation_state=validation_state,
            validation_status_codes=codes,
            trust_state=C2PATrustState.UNTRUSTED,
            provenance_state=AssuranceState.UNKNOWN,
            reason=(
                "Manifest structure may validate, but signer trust is not "
                "established under the supplied trust basis."
            ),
        )

    if validation_state == "Valid" and not codes:
        return C2PAHandoff(
            active_manifest=active_manifest,
            validation_state=validation_state,
            validation_status_codes=(),
            trust_state=C2PATrustState.TRUSTED,
            provenance_state=AssuranceState.PRESERVED,
            reason="Manifest validated without reported status exceptions.",
        )

    return C2PAHandoff(
        active_manifest=active_manifest,
        validation_state=validation_state,
        validation_status_codes=codes,
        trust_state=C2PATrustState.INDETERMINATE,
        provenance_state=AssuranceState.UNKNOWN,
        reason="Report does not satisfy the harness's narrow trusted handoff rule.",
    )
