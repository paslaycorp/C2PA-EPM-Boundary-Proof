# Exam v1 — Evidence Record

This record preserves the first complete green C2PA–EPM boundary exam.

## Tested head

`4725bf0b55e3fafb64ce65d26ae6c3b65ce01bde`

GitHub Actions run: **35542651303** — conclusion **success**.

## Result

The frozen EPM v0.1.2 lane produced **4 passes + 2 expected historical falsifications** on Python 3.12 and again on Python 3.13. The post-release constitutional/authority lane produced **11/11 passes** on each Python version.

The real C2PA lane used c2patool **0.27.22**, a checksum-pinned binary, a pinned signed fixture, and explicit fixture-provided trust material. The fixture produced one active manifest and zero validation-status entries after trust binding.

That provenance result was then handed to EPM. A purpose change from verification to publication produced:

- decision: `DENY`
- failure: `MISAPPLICATION`
- fail-closed: `true`

The same C2PA-derived provenance did not manufacture action authority. A publication request without a validated authority basis produced:

- decision: `DEFER`
- failure: `AUTHORITY_UNESTABLISHED`
- permitted: `false`
- fail-closed: `true`

A byte was then mutated inside the signed JPEG scan data. c2patool returned JSON with `validation_state: Invalid` and `assertion.dataHash.mismatch`. Its process exit code remained zero, so the harness deliberately evaluates the machine-readable validation result rather than equating process success with evidentiary validity.

## Falsification retained

The first real-C2PA attempt, run **35542568099**, failed because the signed sample's test certificate was untrusted under c2patool's default trust configuration. The asset itself showed valid signature/hash/timestamp evidence.

That failure was preserved. The correction did not relax the assertion and did not alter EPM. The harness instead bound the sample repository's pinned `allowed_list.pem` and `store.cfg` explicitly, making the trust basis part of the test evidence.

## Claim boundary

This demonstrates a tested architectural separation between a C2PA provenance result and EPM applicability/authority decisions for the pinned implementations and fixture. It is **not** a C2PA conformance, certification, or endorsement claim.

Machine-readable details are in [receipts/EXAM-v1.json](receipts/EXAM-v1.json).
