from dataclasses import dataclass

import torch

MAX_LENGTH = 512


class InputTooLongError(ValueError):
    pass


@dataclass
class Encoded:
    input_ids: list[int]
    spans: list[tuple[int, int]]


def piece(tokenizer, text: str) -> list[int]:
    return tokenizer(text, add_special_tokens=False)["input_ids"]


def encode(
    tokenizer,
    state: str,
    instructions: str,
    options: list[str],
    max_length: int = MAX_LENGTH,
) -> Encoded:
    cls_id, sep_id = tokenizer.cls_token_id, tokenizer.sep_token_id
    instruction_ids = piece(tokenizer, instructions)
    option_ids = [piece(tokenizer, text) for text in options]
    cls_and_two_seps = 3
    fixed = (
        cls_and_two_seps
        + len(instruction_ids)
        + sum(len(ids) + 1 for ids in option_ids)
    )
    if fixed > max_length:
        raise InputTooLongError(
            f"instructions and options need {fixed} > {max_length} tokens"
        )
    state_ids = piece(tokenizer, state)[: max_length - fixed]
    input_ids = [cls_id, *state_ids, sep_id, *instruction_ids, sep_id]
    spans = []
    for ids in option_ids:
        spans.append((len(input_ids), len(input_ids) + len(ids)))
        input_ids += [*ids, sep_id]
    return Encoded(input_ids, spans)


def collate(batch: list[Encoded], pad_id: int) -> dict[str, torch.Tensor]:
    length = max(len(item.input_ids) for item in batch)
    options = max(len(item.spans) for item in batch)
    input_ids = torch.full((len(batch), length), pad_id, dtype=torch.long)
    attention_mask = torch.zeros((len(batch), length), dtype=torch.long)
    span_mask = torch.zeros((len(batch), options, length))
    option_mask = torch.zeros((len(batch), options), dtype=torch.bool)
    for row, item in enumerate(batch):
        input_ids[row, : len(item.input_ids)] = torch.tensor(item.input_ids)
        attention_mask[row, : len(item.input_ids)] = 1
        for slot, (start, end) in enumerate(item.spans):
            span_mask[row, slot, start:end] = 1.0
            option_mask[row, slot] = True
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "span_mask": span_mask,
        "option_mask": option_mask,
    }
