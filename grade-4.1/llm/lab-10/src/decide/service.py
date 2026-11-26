import os
import subprocess
from functools import lru_cache
from operator import itemgetter
from typing import Annotated

import torch
from fastapi import Depends, FastAPI, HTTPException

from decide.data import Example
from decide.encode import InputTooLongError, encode
from decide.model import DecisionModel, infer_logits, load_checkpoint, to_probabilities
from decide.schema import (
    ChoiceAnswer,
    NoulAnswer,
    Request,
    Response,
    ScoreAnswer,
    Usage,
)


def to_example(question) -> Example:
    if question.type == "choice":
        keys = list(question.criteria)
        return Example(
            "choice",
            "",
            question.instructions,
            0,
            keys,
            list(question.criteria.values()),
        )
    if question.type == "score":
        keys = [str(level) for level in range(len(question.criteria))]
        return Example(
            "score", "", question.instructions, 0, keys, list(question.criteria)
        )
    return Example("noul", "", question.instructions, 0)


def confidence(top: float, options: int) -> float:
    return (top - 1 / options) / (1 - 1 / options)


def build_answer(example: Example, probs: torch.Tensor):
    if example.kind == "noul":
        return NoulAnswer(noul=round(float(probs), 4))
    values = [float(p) for p in probs]
    top = max(values)
    if example.kind == "choice":
        ranked = sorted(
            zip(example.keys, values, strict=True), key=itemgetter(1), reverse=True
        )
        return ChoiceAnswer(
            choice=ranked[0][0],
            probabilities={k: round(p, 4) for k, p in ranked},
            confidence=round(confidence(top, len(values)), 4),
        )
    return ScoreAnswer(
        score=round(sum(level * p for level, p in enumerate(values)), 4),
        confidence=round(confidence(top, len(values)), 4),
        probabilities={
            key: round(p, 4) for key, p in zip(example.keys, values, strict=True)
        },
        legend=dict(zip(example.keys, example.descriptions, strict=True)),
    )


class Predictor:
    def __init__(self, model: DecisionModel, tokenizer, name: str, device: str = "cpu"):
        self.model, self.tokenizer, self.name, self.device = (
            model,
            tokenizer,
            name,
            device,
        )

    def __call__(self, request: Request) -> Response:
        examples = [to_example(question) for question in request.questions.values()]
        batch = [
            encode(self.tokenizer, request.state, e.instructions, e.option_texts)
            for e in examples
        ]
        logits = infer_logits(
            self.model, batch, self.tokenizer.pad_token_id, self.device
        )
        answers = {
            key: build_answer(
                e, to_probabilities(row, e.kind, self.model.temperature_of(e.kind))
            )
            for key, e, row in zip(request.questions, examples, logits, strict=True)
        }
        tokens = sum(len(item.input_ids) for item in batch)
        return Response(
            model=self.name, answers=answers, usage=Usage(input_tokens=tokens)
        )


def model_name(base_name: str) -> str:
    found = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    sha = found.stdout.strip() or "nogit"
    return f"decide-{base_name.split('/')[-1].lower()}-{sha}"


@lru_cache(maxsize=1)
def get_predictor() -> Predictor:
    device = os.environ.get(
        "DECIDE_DEVICE", "cuda" if torch.cuda.is_available() else "cpu"
    )
    model, tokenizer = load_checkpoint(
        os.environ.get("DECIDE_CHECKPOINT", "checkpoints/best.pt"), device
    )
    return Predictor(model, tokenizer, model_name(model.base_name), device)


app = FastAPI(title="decide")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/systemone")
def systemone(
    request: Request, predictor: Annotated[Predictor, Depends(get_predictor)]
) -> Response:
    try:
        return predictor(request)
    except InputTooLongError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
