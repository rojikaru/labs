import numpy as np
import torch

from decide.calibrate import expected_calibration_error, fit_temperature


def test_ece_is_small_when_calibrated_and_large_when_overconfident():
    rng = np.random.default_rng(13)
    confidence = rng.uniform(0.0, 1.0, 200_000)
    calibrated = (rng.uniform(0.0, 1.0, confidence.size) < confidence).astype(float)
    assert expected_calibration_error(confidence, calibrated) < 0.01
    overconfident = np.full(10_000, 0.99)
    correct = (rng.uniform(0.0, 1.0, overconfident.size) < 0.6).astype(float)
    assert expected_calibration_error(overconfident, correct) > 0.3


def test_fit_temperature_recovers_scale():
    torch.manual_seed(13)
    true_logits = torch.randn(20_000, 4) * 2
    targets = torch.multinomial(torch.softmax(true_logits, -1), 1).squeeze(-1)
    assert abs(fit_temperature(true_logits * 3, targets, "choice") - 3.0) <= 0.15
    assert abs(fit_temperature(true_logits, targets, "choice") - 1.0) <= 0.1
