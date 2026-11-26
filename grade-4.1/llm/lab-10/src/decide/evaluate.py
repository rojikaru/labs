import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from transformers import pipeline

from decide.calibrate import (
    confidence_and_correct,
    expected_calibration_error,
    fit_temperature,
    reliability_plot,
    stack_logits,
)
from decide.data import load_tests, load_training, majority_share
from decide.encode import encode
from decide.model import (
    TYPES,
    infer_logits,
    load_checkpoint,
    save_checkpoint,
    to_probabilities,
)
from decide.schema import Request
from decide.service import Predictor, model_name
from decide.train import SOURCES_BY_KIND, keep_fitting, update_metrics

CANONICAL = Path(__file__).parents[2] / "canonical_request.json"
ZERO_SHOT_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"


def predict(model, tokenizer, examples, device: str, batch_size: int = 32):
    rows = []
    for start in range(0, len(examples), batch_size):
        chunk = examples[start : start + batch_size]
        encoded = [
            encode(tokenizer, e.state, e.instructions, e.option_texts) for e in chunk
        ]
        rows += infer_logits(model, encoded, tokenizer.pad_token_id, device)
    return stack_logits(rows), torch.tensor([e.target for e in examples])


def fit_temperatures(model, tokenizer, kinds, device: str) -> dict[str, float]:
    _, val = load_training([name for kind in kinds for name in SOURCES_BY_KIND[kind]])
    fitted = {}
    for kind in kinds:
        examples = [e for name in SOURCES_BY_KIND[kind] for e in val[name]]
        fitted[kind] = fit_temperature(
            *predict(model, tokenizer, examples, device), kind
        )
        model.temperature[TYPES.index(kind)] = fitted[kind]
    return fitted


def f1_score(predicted: torch.Tensor, targets: torch.Tensor) -> float:
    true_positive = int((predicted & (targets == 1)).sum())
    return 2 * true_positive / max(1, int(predicted.sum()) + int((targets == 1).sum()))


def score_set(logits, targets, kind: str, temperature: float):
    row, curves = {"type": kind, "rows": len(targets)}, {}
    for label, value in (("before", 1.0), ("after", temperature)):
        confidence, correct = confidence_and_correct(
            to_probabilities(logits, kind, value), targets, kind
        )
        curves[label] = (confidence, correct)
        row[f"ece_{label}"] = expected_calibration_error(confidence, correct)
    row["accuracy"] = float(correct.mean())
    if kind == "noul":
        row["f1"] = f1_score(logits > 0, targets)
    return row, curves


def pool(curves: dict, names: list[str], label: str) -> tuple[np.ndarray, np.ndarray]:
    confidence = np.concatenate([curves[name][label][0] for name in names])
    correct = np.concatenate([curves[name][label][1] for name in names])
    return confidence, correct


def pooled_reliability(
    results: dict, curves: dict, temperatures: dict, suffix: str
) -> dict:
    by_type = {}
    for kind, fitted in temperatures.items():
        names = [name for name, row in results.items() if row["type"] == kind]
        merged = {
            f"T = {value:g}": pool(curves, names, label)
            for label, value in (("before", 1.0), ("after", fitted))
        }
        reliability_plot(
            merged,
            f"{kind}: held-out test sets",
            f"reports/reliability_{kind}{suffix}.png",
        )
        by_type[kind] = {
            label: expected_calibration_error(*pair) for label, pair in merged.items()
        }
    return by_type


def zero_shot_hit(classifier, example) -> bool:
    sequence = f"{example.state}\n{example.instructions}"
    out = classifier(sequence, example.option_texts, hypothesis_template="{}")
    return out["labels"][0] == example.option_texts[example.target]


def zero_shot(tests: dict, device: str, cap: int = 1000) -> dict[str, float]:
    classifier = pipeline(
        "zero-shot-classification", model=ZERO_SHOT_MODEL, device=device
    )
    accuracy = {}
    for name, examples in tests.items():
        if examples[0].kind != "choice":
            continue
        hits = [zero_shot_hit(classifier, e) for e in examples[:cap]]
        accuracy[name] = sum(hits) / len(hits)
    return accuracy


def timed(predictor: Predictor, request: Request) -> float:
    torch.cuda.synchronize()
    started = time.perf_counter()
    predictor(request)
    torch.cuda.synchronize()
    return time.perf_counter() - started


def service_metrics(checkpoint: Path) -> dict:
    request = Request.model_validate(json.loads(CANONICAL.read_text()))
    found = {}
    for device in ("cuda", "cpu"):
        model, tokenizer = load_checkpoint(checkpoint, device)
        predictor = Predictor(model, tokenizer, model_name(model.base_name), device)
        response = predictor(request)
        for _ in range(2):
            predictor(request)
        timings = [timed(predictor, request) for _ in range(20)]
        found[f"latency_ms_{device}"] = round(1000 * sum(timings) / len(timings), 2)
        found[f"response_{device}"] = response.model_dump()
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoints/best.pt"))
    parser.add_argument("--kinds", nargs="+", default=list(TYPES), choices=TYPES)
    parser.add_argument("--section", default="results")
    parser.add_argument("--baselines", action="store_true")
    parser.add_argument("--latency", action="store_true")
    args = parser.parse_args()
    model, tokenizer = load_checkpoint(args.checkpoint, "cuda")
    temperatures = fit_temperatures(model, tokenizer, args.kinds, "cuda")
    save_checkpoint(model, args.checkpoint)
    tests = {n: rows for n, rows in load_tests().items() if rows[0].kind in args.kinds}
    tests = keep_fitting(tokenizer, tests)
    results, curves = {}, {}
    for name, examples in tests.items():
        logits, targets = predict(model, tokenizer, examples, "cuda")
        kind = examples[0].kind
        results[name], curves[name] = score_set(
            logits, targets, kind, temperatures[kind]
        )
        results[name]["majority"] = majority_share(examples)
    suffix = "" if args.section == "results" else f"_{args.section}"
    by_type = pooled_reliability(results, curves, temperatures, suffix)
    for name, accuracy in (zero_shot(tests, "cuda") if args.baselines else {}).items():
        results[name]["zero_shot"] = accuracy
    section = {"temperature": temperatures, "tests": results, "ece_by_type": by_type}
    update_metrics(args.section, section)
    if args.latency:
        update_metrics("service", service_metrics(args.checkpoint))


if __name__ == "__main__":
    main()
