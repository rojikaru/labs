import pytest
import torch

from decide.encode import InputTooLongError, collate, encode, piece


def test_option_spans_cover_exactly_each_option(tokenizer):
    options = ["red", "blue green", "the cat sat"]
    encoded = encode(tokenizer, "the cat sat on a mat", "is it red", options)
    for (start, end), text in zip(encoded.spans, options, strict=True):
        assert encoded.input_ids[start:end] == piece(tokenizer, text)
        assert encoded.input_ids[end] == tokenizer.sep_token_id
    assert encoded.input_ids[0] == tokenizer.cls_token_id


def test_truncation_shortens_only_the_state_from_the_end(tokenizer):
    state = " ".join(["cat"] * 50 + ["mat"] * 50)
    options = ["red", "blue"]
    full = encode(tokenizer, state, "is it red", options)
    short = encode(tokenizer, state, "is it red", options, max_length=40)
    assert len(full.input_ids) == 1 + 100 + 1 + 3 + 1 + 4
    assert len(short.input_ids) == 40
    kept = short.input_ids[1 : 40 - 10]
    assert kept == piece(tokenizer, state)[: len(kept)]
    assert short.input_ids[-9:] == full.input_ids[-9:]


def test_instructions_and_options_are_never_cut(tokenizer):
    with pytest.raises(InputTooLongError):
        encode(tokenizer, "cat", "is it red " * 10, ["red"], max_length=20)


def test_collate_masks(tokenizer):
    batch = [
        encode(tokenizer, "cat", "is it", ["red", "blue"]),
        encode(tokenizer, "cat mat", "is it", []),
    ]
    tensors = collate(batch, tokenizer.pad_token_id)
    assert tensors["option_mask"].tolist() == [[True, True], [False, False]]
    assert tensors["span_mask"].sum(-1).tolist() == [[1.0, 1.0], [0.0, 0.0]]
    assert int(tensors["attention_mask"][0].sum()) == len(batch[0].input_ids)
    assert torch.all(tensors["input_ids"][0, len(batch[0].input_ids) :] == tokenizer.pad_token_id)
