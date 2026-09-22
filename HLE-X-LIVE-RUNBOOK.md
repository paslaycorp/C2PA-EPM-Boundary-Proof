# HLE-X Live Runbook

The live HLE-X workflow is deliberately manual.

## Preconditions

Before a live run:

1. The user must personally obtain legitimate access to the gated `cais/hle` dataset and accept its access conditions.
2. Record the **exact 40-character dataset commit SHA**. HLE-X rejects moving refs such as `main`.
3. Configure the repository secret `HF_TOKEN` with access to the authorized dataset.
4. Configure `OPENAI_API_KEY` for the chosen model and judge endpoints.
5. Select the model and judge explicitly.

## Pilot first

The workflow defaults to **25 items**.

Runs above 100 items require the exact confirmation:

`RUN_HLE_FULL`

This prevents an accidental high-cost benchmark execution.

## Data handling

During a live run, question text, images, reference answers, model free-form responses, and judge reasoning exist only in the ephemeral runner process.

The only uploaded artifact is the sanitized HLE-X receipt containing:

- hashed HLE item identifiers;
- model identifier;
- judged correctness;
- extracted confidence;
- calibration class;
- UNKNOWN evidence state;
- EPM authority decision/failure;
- aggregate calibration metrics;
- deterministic receipt SHA-256.

Raw benchmark content is not committed or uploaded by this workflow.

## Interpretation

A high HLE accuracy score does not establish provenance or authority. HLE-X evaluates whether the architecture preserves those distinctions while also measuring outcome accuracy and calibration.
