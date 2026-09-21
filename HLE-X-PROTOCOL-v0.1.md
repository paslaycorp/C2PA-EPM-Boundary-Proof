# HLE-X Protocol v0.1 — Evidence Record

The HLE-X protocol layer is validated without using or reproducing gated Humanity's Last Exam benchmark content.

## Pinned upstream

- HLE repository: `centerforaisafety/hle`
- Commit: `73ae974b1844c3ffa64c3f4343d9f1f259575700`
- Dataset identifier: `cais/hle`
- Declared benchmark size: 2,500 questions

## Protocol validation

GitHub Actions run **35549792258** completed successfully at proof-harness head:

`21f388561867a2fd0c68d26a258c6354447c2c81`

Observed:

- **13/13** HLE-X synthetic falsification tests passed;
- correctness remained distinct from evidentiary provenance;
- high confidence could not manufacture authority;
- correct answers without an independent evidentiary basis remained `UNKNOWN`;
- every synthetic item without authority basis remained `DEFER / AUTHORITY_UNESTABLISHED`;
- sanitizer output omitted question text, reference answers, judge reasoning, and raw model responses;
- canonical sanitized synthetic receipt SHA-256:
  `22b933d296fff25e0ed05ed35093b159882e04eb3a5a01546494d9654c2b7d39`.

## Live benchmark status

The actual HLE benchmark has **not** been executed by this branch.

The official dataset is gated. Live execution is intentionally blocked until the user legitimately accepts the dataset access terms and supplies an authorized model endpoint. This protocol does not attempt to bypass that boundary.

Machine-readable evidence is in [receipts/HLE-X-PROTOCOL-v0.1.json](receipts/HLE-X-PROTOCOL-v0.1.json).
