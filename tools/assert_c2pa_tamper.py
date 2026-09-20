from __future__ import annotations

import json
import sys
from pathlib import Path


def _validation_statuses(value: object) -> list[object]:
    found: list[object] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "validation_status" and isinstance(child, list):
                found.extend(child)
            found.extend(_validation_statuses(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_validation_statuses(child))
    return found


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: assert_c2pa_tamper.py <c2pa-json>")

    path = Path(sys.argv[1])
    if not path.exists() or path.stat().st_size == 0:
        raise AssertionError(
            "c2patool returned success for the tampered asset without a JSON validation report"
        )

    document = json.loads(path.read_text())
    statuses = _validation_statuses(document)
    if not statuses:
        raise AssertionError(
            "tampered asset was accepted without any visible validation_status entry"
        )

    print(json.dumps({"tamper_detected": True, "validation_status_count": len(statuses)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
