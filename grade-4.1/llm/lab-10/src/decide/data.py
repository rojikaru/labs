import argparse
import random
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from datasets import Dataset, load_dataset

SEED = 13
TRAIN_CAP, TEST_CAP, VAL_SHARE = 8000, 2000, 0.05
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
YELP_LEVELS = [
    "very dissatisfied",
    "dissatisfied",
    "neutral",
    "satisfied",
    "very satisfied",
]
SIB_TOPICS = [
    "entertainment",
    "geography",
    "health",
    "politics",
    "science/technology",
    "sports",
    "travel",
]


@dataclass
class Example:
    kind: str
    state: str
    instructions: str
    target: int
    keys: list[str] = field(default_factory=list)
    descriptions: list[str] = field(default_factory=list)

    @property
    def option_texts(self) -> list[str]:
        if self.kind == "score":
            return list(self.descriptions)
        pairs = zip(self.keys, self.descriptions, strict=True)
        return [f"{key}: {text}" if text else key for key, text in pairs]


def boolq(r, labels) -> Example:
    return Example("noul", r["passage"], r["question"] + "?", int(r["answer"]))


def mnli(r, labels) -> Example:
    question = f"Does it follow that: {r['hypothesis']}?"
    return Example("noul", r["premise"], question, int(r["label"] == 0))


def amazon(r, labels) -> Example:
    text = f"{r['title']}. {r['content']}"
    return Example("noul", text, "Is this review positive?", r["label"])


def ag_news(r, labels) -> Example:
    question = "What is this news article about?"
    return Example(
        "choice", r["text"], question, r["label"], labels, [""] * len(labels)
    )


def race(r, labels) -> Example:
    letters = list(LETTERS[: len(r["options"])])
    target = LETTERS.index(r["answer"])
    return Example("choice", r["article"], r["question"], target, letters, r["options"])


def belebele(r, labels) -> Example:
    answers = [r[f"mc_answer{number}"] for number in range(1, 5)]
    target = int(r["correct_answer_num"]) - 1
    return Example(
        "choice", r["flores_passage"], r["question"], target, list(LETTERS[:4]), answers
    )


def sib(r, labels) -> Example:
    target = SIB_TOPICS.index(r["category"])
    return Example(
        "choice", r["text"], "Про що це речення?", target, SIB_TOPICS, [""] * 7
    )


def banking(r, labels) -> Example:
    rng = random.Random(f"{SEED}-{r['text']}")
    others = rng.sample([i for i in range(len(labels)) if i != r["label"]], 4)
    order = rng.sample([r["label"], *others], 5)
    keys = [labels[i].replace("_", " ") for i in order]
    question = "What does the customer want?"
    return Example(
        "choice", r["text"], question, order.index(r["label"]), keys, [""] * 5
    )


def yelp(r, labels) -> Example:
    keys = [str(level) for level in range(len(YELP_LEVELS))]
    question = "How satisfied is the reviewer?"
    return Example("score", r["text"], question, r["label"], keys, YELP_LEVELS)


def not_neutral(label: int) -> bool:
    return label != 1


@dataclass
class Source:
    hub: str
    config: str | None
    split: str
    recast: Callable[..., Example]
    keep: Callable | None = None


TRAIN_SOURCES = {
    "boolq": Source("google/boolq", None, "train", boolq),
    "mnli": Source("nyu-mll/glue", "mnli", "train", mnli, not_neutral),
    "ag_news": Source("fancyzhx/ag_news", None, "train", ag_news),
    "race": Source("ehovy/race", "all", "train", race),
    "yelp": Source("Yelp/yelp_review_full", None, "train", yelp),
}
TEST_SOURCES = {
    "boolq_val": Source("google/boolq", None, "validation", boolq),
    "amazon_polarity": Source("fancyzhx/amazon_polarity", None, "test", amazon),
    "banking77": Source("PolyAI/banking77", None, "test", banking),
    "belebele_uk": Source("facebook/belebele", "ukr_Cyrl", "test", belebele),
    "sib200_uk": Source("Davlan/sib200", "ukr_Cyrl", "test", sib),
    "yelp_test": Source("Yelp/yelp_review_full", None, "test", yelp),
}


def load(source: Source, cap: int) -> Dataset:
    rows = load_dataset(source.hub, source.config, split=source.split)
    if source.keep is not None:
        rows = rows.filter(source.keep, input_columns="label")
    rows = rows.shuffle(seed=SEED)
    return rows.select(range(min(cap, len(rows))))


def recast(source: Source, rows: Dataset) -> list[Example]:
    label = rows.features.get("label")
    labels = getattr(label, "names", None)
    return [source.recast(row, labels) for row in rows]


def load_training(
    names=None,
) -> tuple[dict[str, list[Example]], dict[str, list[Example]]]:
    train, val = {}, {}
    for name in names or TRAIN_SOURCES:
        source = TRAIN_SOURCES[name]
        rows = load(source, TRAIN_CAP)
        cut = round(len(rows) * VAL_SHARE)
        val[name] = recast(source, rows.select(range(cut)))
        train[name] = recast(source, rows.select(range(cut, len(rows))))
    return train, val


def load_tests(names=None) -> dict[str, list[Example]]:
    return {
        name: recast(TEST_SOURCES[name], load(TEST_SOURCES[name], TEST_CAP))
        for name in names or TEST_SOURCES
    }


def majority_share(examples: list[Example]) -> float:
    return Counter(e.target for e in examples).most_common(1)[0][1] / len(examples)


def print_stats() -> None:
    train, val = load_training()
    print(f"{'source':18} {'type':7} {'split':6} {'rows':>6} {'majority':>9}")
    for split, groups in (("train", train), ("val", val), ("test", load_tests())):
        for name, examples in groups.items():
            share = f"{majority_share(examples):9.3f}" if split == "test" else ""
            print(f"{name:18} {examples[0].kind:7} {split:6} {len(examples):6} {share}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stats", action="store_true", help="print rows per source/type/split"
    )
    if parser.parse_args().stats:
        print_stats()
