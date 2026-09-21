from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Literal

from datasets import load_dataset
from openai import AsyncOpenAI
from pydantic import BaseModel

from boundary_proof.hle_x import aggregate, receipt_hash, sanitize_official_judged_item

HLE_REPOSITORY_COMMIT = "73ae974b1844c3ffa64c3f4343d9f1f259575700"
FULL_RUN_CONFIRMATION = "RUN_HLE_FULL"


class Judgement(BaseModel):
    extracted_final_answer: str
    correct: Literal["yes", "no"]
    confidence: int


MODEL_INSTRUCTION = (
    "Respond in exactly this format:\n"
    "Explanation: {brief explanation}\n"
    "Answer: {final answer}\n"
    "Confidence: {integer from 0% to 100%}"
)

JUDGE_INSTRUCTION = (
    "Judge whether the model response matches the supplied reference answer. "
    "Extract the model's final answer and its stated confidence. "
    "Return correct='yes' only when the final answer matches the reference "
    "answer or is within a small numerical tolerance where appropriate."
)


def _require_exact_revision(value: str) -> None:
    if re.fullmatch(r"[0-9a-fA-F]{40}", value) is None:
        raise SystemExit(
            "dataset revision must be an exact 40-character commit SHA, not a moving ref"
        )


def _authorize_size(max_samples: int, confirmation: str) -> None:
    if max_samples <= 0:
        raise SystemExit("max_samples must be positive")
    if max_samples > 100 and confirmation != FULL_RUN_CONFIRMATION:
        raise SystemExit(
            f"runs above 100 items require --confirmation {FULL_RUN_CONFIRMATION}"
        )


def _messages(question: dict[str, object]) -> list[dict[str, object]]:
    text = question.get("question")
    if not isinstance(text, str) or not text:
        raise ValueError("HLE item is missing question text")

    content: list[dict[str, object]] = [{"type": "text", "text": text}]
    image = question.get("image")
    if isinstance(image, str) and image:
        content.append({"type": "image_url", "image_url": {"url": image}})

    return [
        {"role": "system", "content": MODEL_INSTRUCTION},
        {"role": "user", "content": content},
    ]


async def _evaluate_item(
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    question: dict[str, object],
    *,
    model: str,
    judge: str,
    max_completion_tokens: int,
):
    async with semaphore:
        response = await client.chat.completions.create(
            model=model,
            max_completion_tokens=max_completion_tokens,
            messages=_messages(question),
            stream=False,
        )
        model_response = response.choices[0].message.content
        if not isinstance(model_response, str) or not model_response:
            raise RuntimeError("model returned no textual response")

        reference = question.get("answer")
        if not isinstance(reference, str):
            raise ValueError("HLE item is missing reference answer")

        judge_prompt = (
            f"{JUDGE_INSTRUCTION}\n\n"
            f"Reference answer:\n{reference}\n\n"
            f"Model response:\n{model_response}"
        )
        judged = await client.beta.chat.completions.parse(
            model=judge,
            max_completion_tokens=4096,
            messages=[{"role": "user", "content": judge_prompt}],
            response_format=Judgement,
        )
        parsed = judged.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("judge returned no structured result")

        item_id = question.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("HLE item is missing id")

        transient = {
            "model": model,
            "response": model_response,
            "judge_response": {
                "correct_answer": reference,
                "model_answer": parsed.extracted_final_answer,
                "correct": parsed.correct,
                "confidence": parsed.confidence,
            },
        }

        # Sanitization occurs immediately. Raw HLE content and free-form model
        # output are not returned from this function and are never persisted.
        return sanitize_official_judged_item(item_id, transient)


async def _run(args) -> list:
    token = os.environ.get("HF_TOKEN")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not token:
        raise SystemExit("HF_TOKEN is required after authorized HLE dataset access")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required for the selected model endpoint")

    dataset = load_dataset(
        args.dataset,
        split="test",
        revision=args.dataset_revision,
        token=token,
    )
    count = min(args.max_samples, len(dataset))
    questions = [dict(dataset[index]) for index in range(count)]

    client = AsyncOpenAI(api_key=api_key, timeout=600.0, max_retries=1)
    semaphore = asyncio.Semaphore(args.num_workers)
    tasks = [
        _evaluate_item(
            client,
            semaphore,
            question,
            model=args.model,
            judge=args.judge,
            max_completion_tokens=args.max_completion_tokens,
        )
        for question in questions
    ]
    return await asyncio.gather(*tasks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="cais/hle")
    parser.add_argument("--dataset-revision", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--judge", required=True)
    parser.add_argument("--max-samples", type=int, default=25)
    parser.add_argument("--max-completion-tokens", type=int, default=8192)
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    _require_exact_revision(args.dataset_revision)
    _authorize_size(args.max_samples, args.confirmation)

    items = asyncio.run(_run(args))
    payload = {
        "schema": "c2pa-epm-boundary-proof/hle-x-live-receipt/1",
        "benchmark": {
            "name": "Humanity's Last Exam",
            "dataset": args.dataset,
            "dataset_revision": args.dataset_revision,
            "upstream_repository_commit": HLE_REPOSITORY_COMMIT,
        },
        "execution": {
            "model": args.model,
            "judge": args.judge,
            "requested_max_samples": args.max_samples,
            "evaluated_items": len(items),
            "max_completion_tokens": args.max_completion_tokens,
        },
        "claim_boundary": {
            "question_text_retained": False,
            "reference_answers_retained": False,
            "raw_model_responses_retained": False,
            "correctness_implies_provenance": False,
            "confidence_implies_provenance": False,
            "score_implies_authority": False,
        },
        "aggregate": aggregate(items),
        "items": [item.to_dict() for item in items],
    }
    payload["receipt_sha256"] = receipt_hash(payload)
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["aggregate"], indent=2, sort_keys=True))
    print(f"receipt_sha256={payload['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
