from __future__ import annotations

import json
from pathlib import Path

from boundary.runtime import run_case

OUT = Path("dist/proofs")
OUT.mkdir(parents=True, exist_ok=True)

for case_id in ("baseline", "purpose-change", "time-change"):
    proof = run_case(case_id)
    (OUT / f"{case_id}.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(case_id, proof["proof_sha256"])
