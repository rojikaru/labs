import argparse
import json
import math
import random
import time
from collections import defaultdict
from dataclasses import replace
from operator import itemgetter
from pathlib import Path

import torch
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

from decide.data import SEED, Example, load_training
from decide.encode import InputTooLongError, collate, encode
from decide.model import TYPES, build_model, loss_for, save_checkpoint

METRICS = Path("reports/metrics.json")
SOURCES_BY_KIND = {
    "noul": ["boolq", "mnli"],
    "choice": ["ag_news", "race"],
    "score": ["yelp"],
}


def update_metrics(section: str, value) -> None:
    data = json.loads(METRICS.read_text()) if METRICS.exists() else {}
    data[section] = value
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def shuffled(example: Example, rng: random.Random) -> Example:
    if not example.keys:
        return example
    order = list(range(len(example.keys)))
    rng.shuffle(order)
    return replace(
        example,
        keys=[example.keys[i] for i in order],
        descriptions=[example.descriptions[i] for i in order],
        target=order.index(example.target),
    )


def fits(tokenizer, example: Example) -> bool:
    try:
        encode(tokenizer, "", example.instructions, example.option_texts)
    except InputTooLongError:
        return False
    return True


def keep_fitting(tokenizer, groups: dict[str, list[Example]]) -> dict[str, list[Example]]:
    return {name: [e for e in rows if fits(tokenizer, e)] for name, rows in groups.items()}


def make_batches(groups: dict[str, list[Example]], size: int, rng: random.Random):
    by_kind = defaultdict(list)
    for examples in groups.values():
        by_kind[examples[0].kind].extend(examples)
    batches = []
    for examples in by_kind.values():
        order = rng.sample(examples, len(examples))
        batches += [order[start : start + size] for start in range(0, len(order), size)]
    rng.shuffle(batches)
    return batches


def batch_loss(model, tokenizer, batch: list[Example]) -> torch.Tensor:
    encoded = [encode(tokenizer, e.state, e.instructions, e.option_texts) for e in batch]
    tensors = {k: v.to("cuda") for k, v in collate(encoded, tokenizer.pad_token_id).items()}
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        noul, options = model(**tensors)
    kind = batch[0].kind
    targets = torch.tensor([e.target for e in batch], device="cuda")
    return loss_for(noul if kind == "noul" else options, targets, kind)


@torch.no_grad()
def validation_loss(model, tokenizer, groups, size: int) -> float:
    model.eval()
    total, count = 0.0, 0
    for batch in make_batches(groups, size, random.Random(SEED)):
        total += float(batch_loss(model, tokenizer, batch)) * len(batch)
        count += len(batch)
    model.train()
    return total / count


def train_epoch(model, batches, optimizer, scheduler, args) -> float:
    losses = []
    for step, batch in enumerate(batches, start=1):
        loss = batch_loss(model, args.tokenizer, [shuffled(e, args.rng) for e in batch])
        (loss / args.accumulate).backward()
        losses.append(loss.item())
        if step % args.accumulate == 0 or step == len(batches):
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
        if step % 200 == 0:
            print(
                f"  step {step}/{len(batches)} loss {sum(losses[-200:]) / 200:.4f}",
                flush=True,
            )
    return sum(losses) / len(losses)


def prepare(args):
    torch.manual_seed(SEED)
    args.tokenizer = AutoTokenizer.from_pretrained(args.model)
    sources = [name for kind in args.kinds for name in SOURCES_BY_KIND[kind]]
    train, val = load_training(sources)
    train, val = keep_fitting(args.tokenizer, train), keep_fitting(args.tokenizer, val)
    model = build_model(args.model).to("cuda").train()
    if args.freeze_embeddings:
        model.encoder.get_input_embeddings().requires_grad_(False)
    return train, val, model


def summary(args, model, train, history, started: float) -> dict:
    best = min(history, key=itemgetter("val_loss"))
    return {
        "base_model": args.model,
        "kinds": args.kinds,
        "history": history,
        "best_epoch": best["epoch"],
        "best_val_loss": best["val_loss"],
        "train_rows": {name: len(rows) for name, rows in train.items()},
        "batch_size": args.batch_size,
        "accumulate": args.accumulate,
        "freeze_embeddings": args.freeze_embeddings,
        "wall_time_s": round(time.time() - started, 1),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 2**30, 3),
        "gpu": torch.cuda.get_device_name(0),
        "parameters_m": round(sum(p.numel() for p in model.parameters()) / 1e6, 1),
    }


def run(args) -> dict:
    started = time.time()
    train, val, model = prepare(args)
    batches_per_epoch = len(make_batches(train, args.batch_size, random.Random(SEED)))
    steps = args.epochs * math.ceil(batches_per_epoch / args.accumulate)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=3e-5, weight_decay=0.01
    )
    scheduler = get_linear_schedule_with_warmup(optimizer, round(0.05 * steps), steps)
    history = []
    for epoch in range(1, args.epochs + 1):
        batches = make_batches(train, args.batch_size, args.rng)
        train_loss = train_epoch(model, batches, optimizer, scheduler, args)
        val_loss = validation_loss(model, args.tokenizer, val, args.batch_size)
        print(f"epoch {epoch}: train {train_loss:.4f} val {val_loss:.4f}", flush=True)
        if val_loss < min((row["val_loss"] for row in history), default=math.inf):
            save_checkpoint(model, args.out)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
    return summary(args, model, train, history, started)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="jhu-clsp/mmBERT-small")
    parser.add_argument("--out", type=Path, default=Path("checkpoints/best.pt"))
    parser.add_argument("--kinds", nargs="+", default=list(TYPES), choices=TYPES)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--accumulate", type=int, default=1)
    parser.add_argument("--freeze-embeddings", action="store_true")
    parser.add_argument("--tag", default="main")
    args = parser.parse_args()
    args.rng = random.Random(SEED)
    print("GPU:", torch.cuda.get_device_name(0), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    update_metrics(f"train_{args.tag}", run(args))


if __name__ == "__main__":
    main()
