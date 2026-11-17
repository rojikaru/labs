import pytest
import torch
from tokenizers import Tokenizer, models, pre_tokenizers
from transformers import ModernBertConfig, ModernBertModel, PreTrainedTokenizerFast

from decide.model import DecisionModel

WORDS = [
    "[PAD]",
    "[UNK]",
    "[CLS]",
    "[SEP]",
    "the",
    "cat",
    "sat",
    "on",
    "a",
    "mat",
    "is",
    "it",
    "red",
    "blue",
    "green",
    "yes",
    "no",
]


@pytest.fixture
def tokenizer():
    vocab = {word: index for index, word in enumerate(WORDS)}
    core = Tokenizer(models.WordLevel(vocab, unk_token="[UNK]"))
    core.pre_tokenizer = pre_tokenizers.Whitespace()
    return PreTrainedTokenizerFast(
        tokenizer_object=core,
        cls_token="[CLS]",
        sep_token="[SEP]",
        pad_token="[PAD]",
        unk_token="[UNK]",
    )


@pytest.fixture
def toy_model():
    torch.manual_seed(0)
    config = ModernBertConfig(
        vocab_size=len(WORDS),
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        intermediate_size=128,
        pad_token_id=0,
        cls_token_id=2,
        sep_token_id=3,
        bos_token_id=2,
        eos_token_id=3,
    )
    return DecisionModel(ModernBertModel(config)).eval()
