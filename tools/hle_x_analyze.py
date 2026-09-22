from __future__ import annotations

import argparse
import json
from pathlib import Path

from boundary_proof.hle_x import aggregate, receipt_hash, sanitize_official_judged_item

HLE_REPOSITORY_COMMIT = "73ae974b1844c3ffa64c3f4343d9f1f259575700"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Sanitize official HLE judged predictions into an epistemic receipt "
            "without retaining benchmark questions, reference answers, rationale, "
            "images, or raw model responses."
        )
    )
    parser.add_argument("judged_predictions")
    parser.add_argument("output_receipt")
    parser.add_argument("--dataset", default="cais/hle")
    parser.add_argument("--dataset-revision", required=True)
    args = parser.parse_args()

    source = json.loads(Path(args.judged_predictions).read_text())
    if not isinstance(source, dict):
        raise SystemExit("judged predictions must be a JSON object keyed by HLE item id")

    sanitized = []
    for item_id in sorted(source):
        prediction = source[item_id]
        if not isinstance(prediction, dict):
            raise SystemExit(f"prediction {item_id!r} is not a JSON object")
        sanitized.append(sanitize_official_judged_item(item_id, prediction))

    payload = {
        "schema": "c2pa-epm-boundary-proof/hle-x-receipt/1",
        "benchmark": {
            "name": "Humanity's Last Exam",
            "dataset": args.dataset,
            "dataset_revision": args.dataset_revision,
            "upstream_repository_commit": HLE_REPOSITORY_COMMIT,
        },
        "claim_boundary": {
            "question_text_retained": False,
            "reference_answers_retained": False,
            "raw_model_responses_retained": False,
            "correctness_implies_provenance": False,
            "confidence_implies_provenance": False,
            "score_implies_authority": False,
        },
        "aggregate": aggregate(sanitized),
        "items": [item.to_dict() for item in sanitized],
    }
    payload["receipt_sha256"] = receipt_hash(payload)

    Path(args.output_receipt).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(payload["aggregate"], indent=2, sort_keys=True))
    print(f"receipt_sha256={payload['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
