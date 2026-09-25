# Exam v4 — Jurisdiction Contract

Status: experimental draft. This document defines the claim boundary for a compositional jurisdiction test. It does not claim C2PA conformance, ODRL conformance, TVC production integration, FAP production validation, or standards-body endorsement.

## Question under test

Can provenance, evidentiary/authority evaluation, policy expression, material-dependency analysis, and final effectuation remain compositionally useful without any layer silently inheriting another layer's authority?

The intended architecture is:

```text
C2PA provenance result
        ↓
EPM evidentiary / authority evaluation
        ↓
policy envelope
        ↓
material-dependency receipt
        ↓
final effectuation gate
```

The proposition is not that these layers must always be ordered this way in every implementation. The proposition under test is narrower:

> Each layer may contribute evidence or constraints to a later decision, but no layer may manufacture a claim that belongs to another jurisdiction.

## Jurisdictions

### C2PA lane

Allowed to establish, for the pinned test inputs:

- provenance assertions associated with an asset;
- cryptographic binding and validation state;
- signer/trust information exposed by the C2PA validation result.

Not allowed to establish merely by being Trusted:

- truth of every assertion;
- evidentiary sufficiency;
- contextual applicability;
- authorization;
- permission to execute a consequential act.

This follows the C2PA 2.4 design boundary that provenance validation should not itself become a value judgment about whether provenance is good, bad, or sufficient for a downstream decision.

Primary source:
https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html

### EPM lane

Allowed to evaluate the evidentiary and authority basis supplied to the EPM interface.

Not allowed to:

- rewrite C2PA provenance state;
- treat policy syntax alone as evidence;
- allow later effectuation to erase the historical decision that existed at decision time.

The v4 harness uses the same immutable post-release EPM pin inherited from the existing workflow:

`adb1c31cdb428816c95a3cf98c9a4427c13ec482`

No EPM source is modified.

### Policy lane

Exam v4 uses a deliberately minimal synthetic `PolicyEnvelope`.

It represents only:

- policy identifier and version;
- action, resource, and purpose scope;
- permit/deny result.

It is **not an ODRL processor** and makes **no ODRL conformance claim**.

This boundary is intentional. W3C's 24 September 2026 Future of ODRL workshop report recommends stronger formal semantics, processor conformance, a comprehensive conformance test suite, modular conformance, and integration with identity and provenance. Exam v4 tests the composition seam without pretending those future processor requirements have already been implemented here.

Primary source:
https://www.w3.org/news/2026/w3c-workshop-report-the-future-of-odrl/

### Materiality lane

Exam v4 uses a synthetic `MaterialityReceipt` modeled on the narrow role TVC is intended to serve in this composition:

- identify which mutable conditions are material to the decision or consequence;
- determine which conditions require revalidation at effectuation.

It is not allowed to:

- grant authority;
- override policy;
- rewrite provenance;
- independently permit effectuation.

Exam v4 does not claim that this synthetic receipt is a complete TVC implementation.

### Effectuation lane

The final gate is allowed to decide only whether the already-proposed act may become effective under the currently supplied upstream constraints.

It checks:

- required provenance state;
- existing EPM authority result;
- current policy scope and policy decision;
- exact-act equality;
- current values of material mutable conditions.

It is not allowed to:

- rewrite the earlier EPM decision;
- retroactively change what C2PA validated;
- promote a non-material change into a denial.

This reflects the execution-finality problem described in the individual Internet-Draft `draft-das-agentic-effectuation-boundary-00`, which explicitly distinguishes final exact-act/current-state verification from ordinary identity, authorization, attestation, or provenance inputs. The draft has no IETF consensus status and is cited only as current architectural context.

Primary source:
https://datatracker.ietf.org/doc/draft-das-agentic-effectuation-boundary/

## Adversarial invariants

Exam v4 fails if any of the following becomes possible:

1. Trusted provenance plus a permissive policy creates authority when EPM has no authority basis.
2. Policy permit/deny rewrites C2PA provenance state.
3. A materiality receipt manufactures authorization.
4. The final beneficiary or other exact-act parameter changes after approval and still executes.
5. A material dependency changes after authorization and execution still proceeds.
6. A non-material state change causes a spurious denial.
7. A later policy denial erases or rewrites the fact that an earlier EPM authorization existed.

## Positive control

A trusted provenance result, time-valid EPM authority basis, permissive policy envelope, unchanged exact act, and unchanged material conditions must produce:

`EFFECTUATION_PERMITTED`

If the harness only fails closed and can never distinguish irrelevant change from material change, it is not demonstrating disciplined revalidation. It is merely demonstrating paranoia with unit tests.

## Claim boundary

A green Exam v4 supports only this claim:

> In the tested composition harness and exact pinned EPM/C2PA-adapter environment, the tested layer contracts remain separated across the specified adversarial cases, including exact-act mutation, post-authorization material-state change, policy denial, and non-material change.

A green result does **not** establish:

- C2PA conformance or endorsement;
- ODRL 3.0 conformance;
- IETF adoption of the effectuation-boundary model;
- production FAP behavior;
- production TVC behavior;
- universal safety of autonomous agents;
- correctness outside the exact tested inputs and invariants.
