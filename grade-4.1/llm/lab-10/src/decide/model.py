import torch
import torch.nn.functional as F
from torch import nn
from transformers import AutoConfig, AutoModel, AutoTokenizer, PreTrainedModel

from decide.encode import Encoded, collate

TYPES = ("noul", "choice", "score")


def noul_logits(head: nn.Linear, hidden: torch.Tensor) -> torch.Tensor:
    return head(hidden[:, 0]).squeeze(-1)


def option_logits(
    head: nn.Linear,
    hidden: torch.Tensor,
    span_mask: torch.Tensor,
    option_mask: torch.Tensor,
) -> torch.Tensor:
    counts = span_mask.sum(-1, keepdim=True).clamp(min=1.0)
    pooled = span_mask.to(hidden.dtype) @ hidden / counts.to(hidden.dtype)
    logits = head(pooled).squeeze(-1)
    return logits.masked_fill(~option_mask, float("-inf"))


def to_probabilities(
    logits: torch.Tensor, kind: str, temperature: float = 1.0
) -> torch.Tensor:
    scaled = logits.float() / temperature
    return torch.sigmoid(scaled) if kind == "noul" else torch.softmax(scaled, dim=-1)


def loss_for(logits: torch.Tensor, targets: torch.Tensor, kind: str) -> torch.Tensor:
    if kind == "noul":
        return F.binary_cross_entropy_with_logits(logits.float(), targets.float())
    return F.cross_entropy(logits.float(), targets)


class DecisionModel(nn.Module):
    encoder: PreTrainedModel
    temperature: torch.Tensor

    def __init__(self, encoder: PreTrainedModel, base_name: str = "toy"):
        super().__init__()
        self.encoder = encoder
        self.base_name = base_name
        hidden = encoder.config.hidden_size
        self.noul_head = nn.Linear(hidden, 1)
        self.option_head = nn.Linear(hidden, 1)
        self.register_buffer("temperature", torch.ones(len(TYPES)))

    def forward(self, input_ids, attention_mask, span_mask, option_mask):
        hidden = self.encoder(
            input_ids=input_ids, attention_mask=attention_mask
        ).last_hidden_state
        options = option_logits(self.option_head, hidden, span_mask, option_mask)
        return noul_logits(self.noul_head, hidden), options

    def temperature_of(self, kind: str) -> float:
        return float(self.temperature[TYPES.index(kind)])


def build_model(base_name: str) -> DecisionModel:
    return DecisionModel(AutoModel.from_pretrained(base_name), base_name)


def save_checkpoint(model: DecisionModel, path) -> None:
    torch.save({"base_name": model.base_name, "state": model.state_dict()}, path)


def load_checkpoint(path, device: str = "cpu"):
    saved = torch.load(path, map_location="cpu", weights_only=True)
    encoder = AutoModel.from_config(AutoConfig.from_pretrained(saved["base_name"]))
    model = DecisionModel(encoder, saved["base_name"])
    model.load_state_dict(saved["state"])
    return model.to(device).eval(), AutoTokenizer.from_pretrained(saved["base_name"])


@torch.no_grad()
def infer_logits(
    model: DecisionModel, batch: list[Encoded], pad_id: int, device: str
) -> list[torch.Tensor]:
    tensors = {name: value.to(device) for name, value in collate(batch, pad_id).items()}
    with torch.autocast(
        device_type=device.split(":")[0], dtype=torch.bfloat16, enabled=device != "cpu"
    ):
        noul, options = model(**tensors)
    noul, options = noul.float().cpu(), options.float().cpu()
    return [
        noul[row] if not item.spans else options[row, : len(item.spans)]
        for row, item in enumerate(batch)
    ]
