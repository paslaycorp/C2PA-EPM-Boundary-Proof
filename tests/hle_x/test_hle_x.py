from __future__ import annotations

import json

import pytest

from epm import AssuranceState, AuthorityFailureCode, Decision

from boundary_proof.hle_x import (
    CalibrationClass,
    aggregate,
    classify,
    receipt_hash,
    sanitize_official_judged_item,
)


def _prediction(*, correct: str, confidence: int, model: str = "test-model"):
    return {
        "model": model,
        "response": "RAW MODEL RESPONSE MUST NEVER ENTER SANITIZED OUTPUT",
        "judge_response": {
            "correct_answer": "REFERENCE ANSWER MUST NEVER ENTER SANITIZED OUTPUT",
            "model_answer": "MODEL ANSWER MUST NEVER ENTER SANITIZED OUTPUT",
            "reasoning": "JUDGE REASONING MUST NEVER ENTER SANITIZED OUTPUT",
            "correct": correct,
            "confidence": confidence,
        },
    }


@pytest.mark.parametrize(
    ("correct", "confidence", "expected"),
    [
        (True, 95, CalibrationClass.CONFIDENT_CORRECT),
        (True, 20, CalibrationClass.UNDERCONFIDENT_CORRECT),
        (True, 60, CalibrationClass.UNCERTAIN_CORRECT),
        (False, 95, CalibrationClass.OVERCONFIDENT_FAILURE),
        (False, 20, CalibrationClass.LOW_CONFIDENCE_FAILURE),
        (False, 60, CalibrationClass.UNCERTAIN_FAILURE),
    ],
)
def test_calibration_classes_preserve_outcome_and_posture(correct, confidence, expected):
    assert classify(correct, confidence) is expected


def test_correct_answer_does_not_create_provenance_or_authority():
    item = sanitize_official_judged_item(
        "hle-item-1",
        _prediction(correct="yes", confidence=99),
    )

    assert item.correct is True
    assert item.evidence_state is AssuranceState.UNKNOWN
    assert item.authority_decision is Decision.DEFER
    assert item.authority_failure is AuthorityFailureCode.AUTHORITY_UNESTABLISHED
    assert item.authority_permitted is False


def test_overconfident_wrong_answer_remains_typed_failure():
    item = sanitize_official_judged_item(
        "hle-item-2",
        _prediction(correct="no", confidence=100),
    )

    assert item.correct is False
    assert item.calibration_class is CalibrationClass.OVERCONFIDENT_FAILURE
    assert item.evidence_state is AssuranceState.UNKNOWN


def test_sanitized_record_contains_no_benchmark_or_response_text():
    prediction = _prediction(correct="yes", confidence=80)
    item = sanitize_official_judged_item("hle-item-3", prediction)
    encoded = json.dumps(item.to_dict())

    assert "RAW MODEL RESPONSE" not in encoded
    assert "REFERENCE ANSWER" not in encoded
    assert "MODEL ANSWER" not in encoded
    assert "JUDGE REASONING" not in encoded
    assert "hle-item-3" not in encoded


def test_aggregate_exposes_calibration_without_upgrading_evidence():
    items = [
        sanitize_official_judged_item("a", _prediction(correct="yes", confidence=90)),
        sanitize_official_judged_item("b", _prediction(correct="no", confidence=90)),
        sanitize_official_judged_item("c", _prediction(correct="yes", confidence=30)),
        sanitize_official_judged_item("d", _prediction(correct="no", confidence=20)),
    ]

    result = aggregate(items)

    assert result["n"] == 4
    assert result["accuracy"] == 0.5
    assert result["all_evidence_states_unknown"] is True
    assert result["all_authority_unestablished"] is True
    assert result["classes"]["OVERCONFIDENT_FAILURE"] == 1
    assert result["classes"]["UNDERCONFIDENT_CORRECT"] == 1


def test_receipt_hash_is_canonical_and_order_independent_for_mapping_keys():
    first = {"b": 2, "a": {"y": 2, "x": 1}}
    second = {"a": {"x": 1, "y": 2}, "b": 2}

    assert receipt_hash(first) == receipt_hash(second)


@pytest.mark.parametrize("confidence", [-1, 101])
def test_out_of_range_confidence_is_rejected(confidence):
    with pytest.raises(ValueError):
        sanitize_official_judged_item(
            "bad-confidence",
            _prediction(correct="yes", confidence=confidence),
        )
