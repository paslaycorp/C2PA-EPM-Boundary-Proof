# C2PA → EPM Boundary Proof v0.1

**Experimental interoperability proof. Non-normative. No C2PA conformance or endorsement claim.**

This small demonstrator tests one proposition:

> Verifiable provenance can remain unchanged while downstream evidentiary applicability changes, and neither layer needs to silently manufacture external authority.

## What it does

1. Fetches a pinned public C2PA example asset from `contentauth/example-assets` at commit `c37f93e115289ac1ef00f899a860e6e08ab9886f`.
2. Parses and validates it with `c2pa-python==0.37.10`.
3. Wraps the C2PA result losslessly into an experimental validation receipt and hashes the manifest-store report.
4. Sends the stable evidence identifier into the exact released EPM v0.1.2 engine at commit `bb0559ddb8eff7f78acc432c0334ce7596c1045c`.
5. Runs three deterministic transitions: baseline, purpose change, and time change.
6. Emits a downloadable proof JSON containing the untouched C2PA receipt, explicit context delta, exact EPM result, and an external-authority boundary.

## Core distinction

```text
C2PA provenance validation
          !=
EPM evidentiary applicability
          !=
external action permission
```

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000`.

## Proof cases

- **baseline** — unchanged context; EPM should preserve applicability.
- **purpose-change** — same C2PA evidence, changed downstream purpose, no preservation proof; EPM should fail closed with a misapplication boundary result.
- **time-change** — same C2PA evidence, changed temporal context, no preservation proof; EPM should expose a temporal boundary failure.

## Design discipline

See `BOUNDARY.md` and `NON_CONFORMANCE_NOTICE.md`.

## Meeting use

The UI is deliberately one screen. The intended sequence is:

1. show the real C2PA validation;
2. click **Change purpose**;
3. show that the C2PA receipt hash is identical;
4. show that EPM's transition result changes;
5. point to **External action authority: OUTSIDE_EPM_SCOPE**;
6. download the proof JSON if deeper inspection is requested.

## Verifiable build provenance

On non-PR workflow runs, CI generates the three deterministic proof JSON files, packages them as `c2pa-epm-boundary-proofs.zip`, and creates a GitHub artifact attestation using Sigstore-backed GitHub attestations. This attests **where and how the proof bundle was built**; it does not assert that the C2PA provenance is trustworthy, that EPM authorizes an external action, or that this demonstrator is C2PA conforming.

The workflow pins all first-party GitHub Actions to immutable commit SHAs.
