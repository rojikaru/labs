import numpy as np
import torch
from matplotlib.figure import Figure

from decide.model import loss_for

TEMPERATURE_GRID = np.round(np.arange(0.50, 5.0001, 0.05), 2)
BINS = 15


def stack_logits(rows: list[torch.Tensor]) -> torch.Tensor:
    if rows[0].dim() == 0:
        return torch.stack(rows)
    width = max(len(row) for row in rows)
    out = torch.full((len(rows), width), float("-inf"))
    for index, row in enumerate(rows):
        out[index, : len(row)] = row
    return out


def fit_temperature(logits: torch.Tensor, targets: torch.Tensor, kind: str) -> float:
    losses = [
        float(loss_for(logits / value, targets, kind)) for value in TEMPERATURE_GRID
    ]
    return float(TEMPERATURE_GRID[int(np.argmin(losses))])


def confidence_and_correct(probs: torch.Tensor, targets: torch.Tensor, kind: str):
    if kind == "noul":
        predicted = (probs >= 0.5).long()
        confidence = torch.maximum(probs, 1 - probs)
    else:
        confidence, predicted = probs.max(dim=-1)
    return confidence.numpy(), (predicted == targets).numpy().astype(float)


def bin_statistics(confidence: np.ndarray, correct: np.ndarray, bins: int = BINS):
    index = np.minimum((confidence * bins).astype(int), bins - 1)
    counts = np.bincount(index, minlength=bins)
    safe = np.maximum(counts, 1)
    mean_conf = np.bincount(index, weights=confidence, minlength=bins) / safe
    accuracy = np.bincount(index, weights=correct, minlength=bins) / safe
    return counts, mean_conf, accuracy


def expected_calibration_error(
    confidence: np.ndarray, correct: np.ndarray, bins: int = BINS
) -> float:
    counts, mean_conf, accuracy = bin_statistics(
        np.asarray(confidence), np.asarray(correct), bins
    )
    return float(np.sum(counts / counts.sum() * np.abs(accuracy - mean_conf)))


def reliability_plot(
    curves: dict[str, tuple[np.ndarray, np.ndarray]], title: str, path
) -> None:
    figure = Figure(figsize=(5, 5))
    axis = figure.add_subplot()
    axis.plot([0, 1], [0, 1], linestyle="--", color="grey", label="perfect")
    for label, (confidence, correct) in curves.items():
        counts, mean_conf, accuracy = bin_statistics(confidence, correct)
        filled = counts > 0
        ece = expected_calibration_error(confidence, correct)
        axis.plot(
            mean_conf[filled],
            accuracy[filled],
            marker="o",
            label=f"{label} (ECE {ece:.3f})",
        )
    axis.set(
        xlabel="confidence", ylabel="accuracy", title=title, xlim=(0, 1), ylim=(0, 1)
    )
    axis.legend(loc="upper left")
    figure.tight_layout()
    figure.savefig(path, dpi=120)
