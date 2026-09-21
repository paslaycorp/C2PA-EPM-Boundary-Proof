# Exam v3 — Temporal Boundary Result

Status: **PASS**

Evidence commit: `521f63ac017ab4992164251daf363295d2ad58fe`  
Inherited Exam v2 boundary: `32f8a6d2c63a36cd90d44d45e6ad1711fbe9754b`  
Workflow: **C2PA-EPM Boundary Proof** run **#56**  
Run result: **5/5 jobs passed**

## Immutable upstream references exercised

- Frozen EPM v0.1.2 pin: `bb0559ddb8eff7f78acc432c0334ce7596c1045c`
- Post-release EPM pin: `adb1c31cdb428816c95a3cf98c9a4427c13ec482`
- C2PA specifications metadata pin: `4eb2c67f49bd21f188e7842afa16dfa642bb578c`
- c2patool fixture pin: `e96d7c396f91848dd55bbfd56a5aec6cbe9352f2`
- c2patool release exercised by the live lane: `0.27.22`

## Test matrix

| Case | Expected boundary | Observed |
| --- | --- | --- |
| Trusted C2PA report plus caller-supplied repository-presence fields | Extra fields must not alter the narrow provenance handoff | PASS — handoff identical to clean trusted report |
| Trusted C2PA report plus caller-supplied actor-access / permission fields | Extra fields must not create authority semantics | PASS — handoff identical to clean trusted report |
| Trusted provenance with no authority basis | Provenance must not permit action | PASS — `DEFER / AUTHORITY_UNESTABLISHED` |
| Authority basis validated after the decision time | Later validation must not retroactively authorize | PASS — `DENY / TEMPORAL_MISMATCH` |
| Properly validated authority basis before the decision time | Temporal separation must not create a permanent false denial | PASS — `AUTHORIZED` |

## Boundary demonstrated

The harness preserves separate state for:

1. C2PA validation / signer trust;
2. provenance assurance;
3. historical repository-presence claims;
4. actor-access claims;
5. authority validation; and
6. the decision time at which authority must already be established.

A trusted provenance handoff is therefore insufficient, by itself, to establish that a manifest was present in a repository by an earlier time, that a particular actor could access it at that time, or that the actor was permitted to act.

## Explicit non-claims

This exam does **not** claim:

- C2PA conformance or C2PA endorsement;
- that the synthetic `repository_present_by` field is a C2PA Manifest Repository receipt;
- that C2PA itself proves historical repository presence in this harness;
- that repository presence proves earlier actor access;
- that actor access proves permission or authority;
- that the live c2patool validation result is a repository receipt;
- that EPM was modified by this exam.

The repository-presence and actor-access fields in the adversarial cases are deliberately untyped caller metadata. The test establishes that such metadata cannot silently enter the narrow C2PA-to-EPM handoff. A real historical-presence claim still requires the repository's own proof and trust model.

## Meeting-use statement

**Verified provenance, historical repository presence, earlier actor access, and permission to act are distinct claims. Evidence for one must not silently manufacture the others.**
