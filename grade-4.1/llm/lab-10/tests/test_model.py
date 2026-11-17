import torch

from decide.encode import collate, encode
from decide.model import option_logits, to_probabilities


def test_option_probabilities_sum_to_one_and_padding_is_zero(tokenizer, toy_model):
    batch = [
        encode(tokenizer, "the cat", "is it", ["red", "blue", "green"]),
        encode(tokenizer, "a mat", "is it", ["yes", "no"]),
    ]
    with torch.no_grad():
        _, logits = toy_model(**collate(batch, tokenizer.pad_token_id))
    probs = to_probabilities(logits, "choice")
    assert torch.allclose(probs.sum(-1), torch.ones(2), atol=1e-6)
    assert probs[1, 2].item() == 0.0
    assert torch.isinf(logits[1, 2])


def test_option_head_is_equivariant(toy_model):
    torch.manual_seed(1)
    hidden = torch.randn(1, 12, 64)
    span_mask = torch.zeros(1, 4, 12)
    for slot, (start, end) in enumerate([(1, 3), (4, 5), (6, 9), (10, 12)]):
        span_mask[0, slot, start:end] = 1.0
    option_mask = torch.ones(1, 4, dtype=torch.bool)
    permutation = torch.tensor([2, 0, 3, 1])
    with torch.no_grad():
        base = option_logits(toy_model.option_head, hidden, span_mask, option_mask)
        moved = option_logits(toy_model.option_head, hidden, span_mask[:, permutation], option_mask)
    probs, moved_probs = torch.softmax(base, -1), torch.softmax(moved, -1)
    assert torch.allclose(moved_probs, probs[:, permutation], atol=1e-6)


def test_temperature_one_is_identity_and_larger_moves_to_uniform():
    logits = torch.tensor([[2.0, 0.5, -1.0]])
    assert torch.allclose(to_probabilities(logits, "choice", 1.0), torch.softmax(logits, -1))
    assert torch.allclose(to_probabilities(logits[0, 0], "noul", 1.0), torch.sigmoid(logits[0, 0]))
    uniform = torch.full((1, 3), 1 / 3)
    distances = [
        (to_probabilities(logits, "choice", t) - uniform).abs().sum() for t in (1.0, 2.0, 5.0)
    ]
    assert distances[0] > distances[1] > distances[2]
    noul = [
        abs(float(to_probabilities(torch.tensor(3.0), "noul", t)) - 0.5) for t in (1.0, 2.0, 5.0)
    ]
    assert noul[0] > noul[1] > noul[2]
