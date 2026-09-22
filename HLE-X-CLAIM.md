# HLE-X — Epistemic Calibration & Provenance Trial

HLE-X is an external stress track for the C2PA–EPM Boundary Proof project.

It does **not** modify Humanity's Last Exam, reproduce its question corpus, train on it, or claim endorsement by the Center for AI Safety or Scale AI.

## Claim under attack

A model's answer can be correct or incorrect and can carry high or low self-reported confidence. Neither correctness nor confidence is, by itself, evidence provenance or authority.

HLE-X therefore tests:

1. **Correctness is not provenance.** A correct answer without an explicit evidentiary basis remains epistemically distinct from a provenance-established answer.
2. **Confidence is not evidence.** High confidence cannot manufacture support, applicability, or authority.
3. **Wrong + high confidence is preserved as an overconfident failure.** It may not be normalized into generic uncertainty.
4. **Correct + low confidence remains underconfident correctness.** The outcome and the model's epistemic posture remain distinct.
5. **Unknown basis remains UNKNOWN.** Evaluation against a reference answer may establish outcome correctness while leaving the answer's evidence basis unknown.
6. **Authority is never inferred from benchmark performance.** Every HLE-X item is evaluated with no authority basis unless an independent authority artifact is supplied.
7. **Benchmark content is non-persistent here.** Question text, reference answers, rationale, images, and raw model responses are excluded from committed HLE-X receipts.

## Sanitized per-item record

HLE-X may persist only bounded metadata such as:

- SHA-256 of the HLE item identifier;
- model identifier;
- judged correctness;
- extracted confidence;
- calibration class;
- evidence-basis state;
- EPM authority decision/failure;
- deterministic receipt hash.

The benchmark question, reference answer, and free-form model response are deliberately omitted.

## Scope

A green HLE-X run demonstrates that the external evaluation harness preserved these distinctions for the exact benchmark revision, model outputs, judge outputs, and evaluator version used.

It is not an HLE score certification, model endorsement, C2PA conformance result, or universal proof of epistemic correctness.
