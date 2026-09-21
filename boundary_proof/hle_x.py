from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Mapping

from epm import (
    AssuranceState,
    AuthorityFailureCode,
    AuthorityRequest,
    Decision,
    evaluate_authority_request,
)


class CalibrationClass(str, Enum):
    CONFIDENT_CORRECT = "CONFIDENT_CORRECT"
    UNDERCONFIDENT_CORRECT = "UNDERCONFIDENT_CORRECT"
    UNCERTAIN_CORRECT = "UNCERTAIN_CORRECT"
    OVERCONFIDENT_FAILURE = "OVERCONFIDENT_FAILURE"
    LOW_CONFIDENCE_FAILURE = "LOW_CONFIDENCE_FAILURE"
    UNCERTAIN_FAILURE = "UNCERTAIN_FAILURE"


@dataclass(frozen=True)
class SanitizedHLEItem:
    item_hash: str
    model: str
    correct: bool
    confidence: int
    calibration_class: CalibrationClass
    evidence_state: AssuranceState
    authority_decision: Decision
    authority_failure: AuthorityFailureCode
    authority_permitted: bool

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["calibration_class"] = self.calibration_class.value
        value["evidence_state"] = self.evidence_state.value
        value["authority_decision"] = self.authority_decision.value
        value["authority_failure"] = self.authority_failure.value
        return value


def hash_item_id(item_id: str) -> str:
    return hashlib.sha256(item_id.encode("utf-8")).hexdigest()


def classify(correct: bool, confidence: int) -> CalibrationClass:
    if not 0 <= confidence <= 100:
        raise ValueError("confidence must be between 0 and 100")

    if correct:
        if confidence >= 80:
            return CalibrationClass.CONFIDENT_CORRECT
        if confidence <= 40:
            return CalibrationClass.UNDERCONFIDENT_CORRECT
        return CalibrationClass.UNCERTAIN_CORRECT

    if confidence >= 80:
        return CalibrationClass.OVERCONFIDENT_FAILURE
    if confidence <= 40:
        return CalibrationClass.LOW_CONFIDENCE_FAILURE
    return CalibrationClass.UNCERTAIN_FAILURE


def sanitize_official_judged_item(
    item_id: str,
    prediction: Mapping[str, object],
) -> SanitizedHLEItem:
    judge = prediction.get("judge_response")
    if not isinstance(judge, Mapping):
        raise ValueError("prediction is missing judge_response")

    raw_correct = judge.get("correct")
    if raw_correct not in {"yes", "no"}:
        raise ValueError("judge_response.correct must be yes or no")
    correct = raw_correct == "yes"

    confidence = judge.get("confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool):
        raise ValueError("judge_response.confidence must be an integer")
    if not 0 <= confidence <= 100:
        raise ValueError("judge_response.confidence must be in [0, 100]")

    model = prediction.get("model")
    if not isinstance(model, str) or not model.strip():
        model = "UNSPECIFIED_MODEL"

    # HLE outcome grading establishes correctness against the benchmark key.
    # It does not establish provenance for the model's reasoning or answer.
    evidence_state = AssuranceState.UNKNOWN

    request = AuthorityRequest(
        transition_id=f"hle-x:{hash_item_id(item_id)[:16]}",
        actor=f"model:{model}",
        action="answer.use",
        resource="hle:item",
        purpose="benchmark-evaluation",
        scope="single-item",
        jurisdiction="benchmark",
        at=datetime(2026, 9, 20, 12, 0, tzinfo=UTC),
        authority="hle-x",
        policy_id="hle-x-no-authority-from-score",
        policy_version="1",
    )
    authority = evaluate_authority_request(request, None)

    if authority.decision is not Decision.DEFER:
        raise AssertionError("benchmark outcome unexpectedly manufactured authority")
    if authority.failure is not AuthorityFailureCode.AUTHORITY_UNESTABLISHED:
        raise AssertionError("missing authority basis did not remain explicit")
    if authority.permitted:
        raise AssertionError("benchmark outcome unexpectedly permitted an action")

    return SanitizedHLEItem(
        item_hash=hash_item_id(item_id),
        model=model,
        correct=correct,
        confidence=confidence,
        calibration_class=classify(correct, confidence),
        evidence_state=evidence_state,
        authority_decision=authority.decision,
        authority_failure=authority.failure,
        authority_permitted=authority.permitted,
    )


def brier_score(items: list[SanitizedHLEItem]) -> float:
    if not items:
        raise ValueError("at least one item is required")
    return sum(
        ((item.confidence / 100.0) - (1.0 if item.correct else 0.0)) ** 2
        for item in items
    ) / len(items)


def expected_calibration_error(
    items: list[SanitizedHLEItem],
    *,
    bins: int = 10,
) -> float:
    if not items:
        raise ValueError("at least one item is required")
    if bins <= 0:
        raise ValueError("bins must be positive")

    total = len(items)
    error = 0.0
    for index in range(bins):
        low = 100 * index / bins
        high = 100 * (index + 1) / bins
        bucket = [
            item
            for item in items
            if low <= item.confidence < high
            or (index == bins - 1 and item.confidence == 100)
        ]
        if not bucket:
            continue
        avg_conf = sum(item.confidence / 100.0 for item in bucket) / len(bucket)
        accuracy = sum(item.correct for item in bucket) / len(bucket)
        error += (len(bucket) / total) * abs(avg_conf - accuracy)
    return error


def aggregate(items: list[SanitizedHLEItem]) -> dict[str, object]:
    if not items:
        raise ValueError("at least one item is required")

    counts = {kind.value: 0 for kind in CalibrationClass}
    for item in items:
        counts[item.calibration_class.value] += 1

    accuracy = sum(item.correct for item in items) / len(items)
    mean_confidence = sum(item.confidence for item in items) / len(items) / 100.0

    return {
        "n": len(items),
        "accuracy": accuracy,
        "mean_confidence": mean_confidence,
        "brier_score": brier_score(items),
        "expected_calibration_error_10_bin": expected_calibration_error(items),
        "classes": counts,
        "all_evidence_states_unknown": all(
            item.evidence_state is AssuranceState.UNKNOWN for item in items
        ),
        "all_authority_unestablished": all(
            item.authority_failure is AuthorityFailureCode.AUTHORITY_UNESTABLISHED
            and item.authority_decision is Decision.DEFER
            and not item.authority_permitted
            for item in items
        ),
    }


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def receipt_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
